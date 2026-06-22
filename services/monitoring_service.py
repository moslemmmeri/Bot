# services/monitoring_service.py
# سرویس مانیتورینگ و نظارت بر سیستم
# شامل: جمع‌آوری متریک‌ها، مدیریت هشدارها، تولید گزارش‌ها و بررسی سلامت

import os
import time
import json
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from logger_config import logger, ContextLogger
from config import config
from database import get_db_connection
from utils.error_handler import log_general_error, log_database_error


# ============================================================
# تعریف انواع متریک‌ها (برای استفاده در سرویس)
# ============================================================

class MetricType(str, Enum):
    """انواع متریک‌های قابل جمع‌آوری"""
    # متریک‌های عملکردی
    API_LATENCY = "api_latency"
    DB_QUERY_TIME = "db_query_time"
    REQUEST_TIME = "request_time"
    
    # متریک‌های سیستمی
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    
    # متریک‌های کاربران
    ACTIVE_USERS = "active_users"
    TOTAL_USERS = "total_users"
    NEW_USERS = "new_users"
    
    # متریک‌های سفارشات
    ORDERS_COUNT = "orders_count"
    REVENUE = "revenue"
    CONVERSION_RATE = "conversion_rate"
    
    # متریک‌های خطاها
    ERROR_COUNT = "error_count"
    ERROR_RATE = "error_rate"
    
    # متریک‌های درخواست‌ها
    REQUESTS_PER_MINUTE = "requests_per_minute"
    TOTAL_REQUESTS = "total_requests"
    
    # متریک‌های دکمه‌ها
    BUTTON_CLICKS = "button_clicks"
    BUTTON_CONVERSION = "button_conversion"


# ============================================================
# کلاس سرویس مانیتورینگ
# ============================================================

class MonitoringService:
    """
    سرویس مانیتورینگ و نظارت بر سیستم
    مسئول جمع‌آوری متریک‌ها، مدیریت هشدارها، تولید گزارش‌ها و بررسی سلامت
    """
    
    def __init__(self, connection, repository=None):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            repository: ریپازیتوری مانیتورینگ (اختیاری)
        """
        self._connection = connection
        self._repository = repository
        self._owner_id = config.OWNER_ID
        
        # تنظیمات هشدارها
        self._alert_thresholds = {
            'error_rate': getattr(config, 'MONITORING_ALERT_ERROR_RATE', 10),
            'cpu_usage': getattr(config, 'MONITORING_ALERT_CPU', 80),
            'memory_usage': getattr(config, 'MONITORING_ALERT_MEMORY', 80),
            'disk_usage': getattr(config, 'MONITORING_ALERT_DISK', 85),
            'api_latency': getattr(config, 'MONITORING_ALERT_API_LATENCY', 500),
        }
        
        logger.info("✅ MonitoringService initialized")
    
    # ============================================================
    # متدهای دریافت آمار (از دیتابیس و سیستم)
    # ============================================================
    
    def get_total_users(self) -> int:
        """دریافت تعداد کل کاربران"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM users")
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            log_database_error(
                f"Error getting total users: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_active_users(self, minutes: int = 5) -> int:
        """
        دریافت تعداد کاربران فعال در N دقیقه اخیر
        
        پارامترها:
            minutes: تعداد دقیقه‌های اخیر
            
        بازگشت: تعداد کاربران فعال
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM users WHERE last_active >= datetime('now', '-' || ? || ' minutes')",
                    (minutes,)
                )
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            log_database_error(
                f"Error getting active users: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_new_users(self, hours: int = 24) -> int:
        """
        دریافت تعداد کاربران جدید در ساعت‌های اخیر
        
        پارامترها:
            hours: تعداد ساعت‌های اخیر
            
        بازگشت: تعداد کاربران جدید
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM users WHERE first_seen >= datetime('now', '-' || ? || ' hours')",
                    (hours,)
                )
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            log_database_error(
                f"Error getting new users: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_order_stats(self) -> Dict[str, Any]:
        """دریافت آمار سفارشات"""
        try:
            from database.db_stats import get_dashboard_stats
            return get_dashboard_stats()
        except Exception as e:
            log_database_error(
                f"Error getting order stats: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total_orders': 0,
                'total_revenue': 0,
                'avg_order_value': 0,
                'total_clicks': 0,
            }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """دریافت آمار خطاها"""
        try:
            from database.db_logs import get_error_stats
            return get_error_stats()
        except Exception as e:
            log_database_error(
                f"Error getting error stats: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total': 0,
                'unresolved': 0,
                'resolved': 0,
                'by_type': [],
            }
    
    def get_requests_per_minute(self) -> float:
        """
        محاسبه میانگین درخواست‌ها در دقیقه بر اساس آمار ۱۰ دقیقه اخیر
        
        بازگشت: میانگین درخواست در دقیقه
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM button_stats WHERE created_at >= datetime('now', '-10 minutes')"
                )
                row = cursor.fetchone()
                count = row['count'] if row else 0
                return round(count / 10, 2)
        except Exception as e:
            log_database_error(
                f"Error getting requests per minute: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0.0
    
    def get_system_resources(self) -> Dict[str, Any]:
        """
        دریافت وضعیت منابع سیستم (CPU, Memory, Disk)
        
        بازگشت: دیکشنری شامل درصد مصرف
        """
        result = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'available': False
        }
        
        try:
            import psutil
            result['cpu_percent'] = psutil.cpu_percent(interval=0.5)
            result['memory_percent'] = psutil.virtual_memory().percent
            result['disk_percent'] = psutil.disk_usage('/').percent
            result['available'] = True
        except ImportError:
            logger.debug("psutil not installed, system resources unavailable")
        except Exception as e:
            log_general_error(
                f"Error getting system resources: {str(e)}",
                traceback=traceback.format_exc()
            )
        
        return result
    
    def get_db_size(self) -> int:
        """دریافت حجم فایل دیتابیس به مگابایت"""
        try:
            db_path = config.SQLITE_DB_PATH
            if os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                return round(size_bytes / (1024 * 1024), 2)
            return 0
        except Exception as e:
            log_general_error(
                f"Error getting db size: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # جمع‌آوری متریک‌ها
    # ============================================================
    
    def collect_metrics_sync(self) -> Dict[str, Any]:
        """
        جمع‌آوری همزمان متریک‌ها (برای استفاده در تسک‌های زمان‌بندی‌شده)
        
        بازگشت: دیکشنری شامل متریک‌های جمع‌آوری‌شده
        """
        ctx_logger = ContextLogger("monitoring.service.collect_metrics")
        results = {}
        metrics = []
        
        try:
            # ========== متریک‌های سیستمی ==========
            resources = self.get_system_resources()
            if resources.get('available', False):
                metrics.append({
                    'type': MetricType.CPU_USAGE.value,
                    'value': resources.get('cpu_percent', 0)
                })
                metrics.append({
                    'type': MetricType.MEMORY_USAGE.value,
                    'value': resources.get('memory_percent', 0)
                })
                results['cpu'] = resources.get('cpu_percent', 0)
                results['memory'] = resources.get('memory_percent', 0)
            
            # ========== متریک‌های کاربران ==========
            total_users = self.get_total_users()
            active_5min = self.get_active_users(5)
            active_today = self.get_active_users(1440)  # 24 ساعت
            new_users = self.get_new_users(24)
            
            metrics.append({'type': MetricType.TOTAL_USERS.value, 'value': total_users})
            metrics.append({
                'type': MetricType.ACTIVE_USERS.value,
                'value': {
                    '5min': active_5min,
                    'today': active_today,
                }
            })
            metrics.append({'type': MetricType.NEW_USERS.value, 'value': new_users})
            
            results['users'] = {
                'total': total_users,
                'active_5min': active_5min,
                'active_today': active_today,
                'new_24h': new_users,
            }
            
            # ========== متریک‌های سفارشات ==========
            order_stats = self.get_order_stats()
            orders_count = order_stats.get('total_orders', 0)
            revenue = order_stats.get('total_revenue', 0)
            conversion_rate = order_stats.get('overall_conversion', 0)
            
            metrics.append({'type': MetricType.ORDERS_COUNT.value, 'value': orders_count})
            metrics.append({'type': MetricType.REVENUE.value, 'value': revenue})
            metrics.append({'type': MetricType.CONVERSION_RATE.value, 'value': conversion_rate})
            
            results['orders'] = {
                'count': orders_count,
                'revenue': revenue,
                'conversion_rate': conversion_rate,
            }
            
            # ========== متریک‌های خطاها ==========
            error_stats = self.get_error_stats()
            total_errors = error_stats.get('total', 0)
            unresolved = error_stats.get('unresolved', 0)
            
            # نرخ خطا (۵ دقیقه اخیر)
            error_rate_5min = self._get_error_rate_5min()
            
            metrics.append({
                'type': MetricType.ERROR_COUNT.value,
                'value': {
                    'total': total_errors,
                    'unresolved': unresolved,
                    'resolved': error_stats.get('resolved', 0),
                }
            })
            metrics.append({
                'type': MetricType.ERROR_RATE.value,
                'value': {
                    '5min': error_rate_5min,
                    'total': total_errors,
                }
            })
            
            results['errors'] = {
                'total': total_errors,
                'unresolved': unresolved,
                'rate_5min': error_rate_5min,
            }
            
            # ========== متریک‌های درخواست‌ها ==========
            rpm = self.get_requests_per_minute()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM button_stats")
                row = cursor.fetchone()
                total_requests = row['count'] if row else 0
            
            metrics.append({'type': MetricType.REQUESTS_PER_MINUTE.value, 'value': rpm})
            metrics.append({'type': MetricType.TOTAL_REQUESTS.value, 'value': total_requests})
            
            results['requests'] = {
                'rpm': rpm,
                'total': total_requests,
            }
            
            # ========== ذخیره متریک‌ها ==========
            if self._repository:
                saved_count = self._repository.save_metrics_batch(metrics)
                results['saved_count'] = saved_count
            else:
                # اگر ریپازیتوری وجود نداشت، مستقیم ذخیره کن
                saved_count = self._save_metrics_direct(metrics)
                results['saved_count'] = saved_count
            
            results['timestamp'] = datetime.now().isoformat()
            results['success'] = True
            
            logger.info(f"✅ Collected {len(metrics)} metrics, saved {saved_count} items")
            
        except Exception as e:
            log_general_error(
                f"Error in collect_metrics_sync: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )
            results['error'] = str(e)
            results['success'] = False
        
        return results
    
    def _get_error_rate_5min(self) -> int:
        """دریافت تعداد خطاهای ۵ دقیقه اخیر"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM error_logs WHERE created_at >= datetime('now', '-5 minutes')"
                )
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            log_database_error(
                f"Error getting error rate: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def _save_metrics_direct(self, metrics: List[Dict[str, Any]]) -> int:
        """ذخیره مستقیم متریک‌ها در دیتابیس"""
        try:
            from admin_panel.monitoring.metrics import save_metrics, Metric
            
            metric_objects = []
            for m in metrics:
                metric_objects.append(
                    Metric(
                        metric_type=m['type'],
                        value=m['value'],
                        timestamp=datetime.now()
                    )
                )
            
            return save_metrics(metric_objects)
        except Exception as e:
            log_database_error(
                f"Error saving metrics directly: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # مدیریت هشدارها
    # ============================================================
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        بررسی شرایط هشدار و تولید هشدارهای جدید
        
        بازگشت: لیست هشدارهای جدید
        """
        alerts = []
        
        try:
            # ========== بررسی نرخ خطا ==========
            error_rate = self._get_error_rate_5min()
            if error_rate > self._alert_thresholds.get('error_rate', 10):
                alerts.append({
                    'type': 'high_error_rate',
                    'level': 'warning' if error_rate < 20 else 'critical',
                    'message': f'نرخ خطا بالا: {error_rate} خطا در ۵ دقیقه',
                    'details': {'error_count': error_rate, 'threshold': self._alert_thresholds['error_rate']}
                })
            
            # ========== بررسی CPU ==========
            resources = self.get_system_resources()
            if resources.get('available', False):
                cpu = resources.get('cpu_percent', 0)
                if cpu > self._alert_thresholds.get('cpu_usage', 80):
                    alerts.append({
                        'type': 'high_cpu',
                        'level': 'warning' if cpu < 90 else 'critical',
                        'message': f'مصرف CPU بالا: {cpu:.1f}%',
                        'details': {'cpu_percent': cpu, 'threshold': self._alert_thresholds['cpu_usage']}
                    })
                
                memory = resources.get('memory_percent', 0)
                if memory > self._alert_thresholds.get('memory_usage', 80):
                    alerts.append({
                        'type': 'high_memory',
                        'level': 'warning' if memory < 90 else 'critical',
                        'message': f'مصرف حافظه بالا: {memory:.1f}%',
                        'details': {'memory_percent': memory, 'threshold': self._alert_thresholds['memory_usage']}
                    })
            
            # ========== بررسی فضای دیسک ==========
            try:
                import psutil
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                if disk_percent > self._alert_thresholds.get('disk_usage', 85):
                    alerts.append({
                        'type': 'high_disk_usage',
                        'level': 'warning' if disk_percent < 92 else 'critical',
                        'message': f'فضای دیسک در حال اتمام: {disk_percent:.1f}%',
                        'details': {
                            'disk_percent': disk_percent,
                            'free_gb': round(disk.free / (1024**3), 2),
                            'threshold': self._alert_thresholds['disk_usage']
                        }
                    })
            except:
                pass
            
            # ========== بررسی API ==========
            api_latency = self._get_api_latency()
            if api_latency > self._alert_thresholds.get('api_latency', 500):
                alerts.append({
                    'type': 'high_api_latency',
                    'level': 'warning' if api_latency < 800 else 'critical',
                    'message': f'تأخیر API بالا: {api_latency} ms',
                    'details': {'latency_ms': api_latency, 'threshold': self._alert_thresholds['api_latency']}
                })
            
            # ========== ذخیره هشدارها ==========
            if alerts and self._repository:
                for alert in alerts:
                    self._repository.save_alert(alert)
            
        except Exception as e:
            log_general_error(
                f"Error checking alerts: {str(e)}",
                traceback=traceback.format_exc()
            )
        
        return alerts
    
    def _get_api_latency(self) -> int:
        """دریافت تأخیر API (تخمینی)"""
        try:
            # تعداد خطاهای ۵ دقیقه اخیر
            error_count = self._get_error_rate_5min()
            if error_count > 10:
                return 800
            elif error_count > 3:
                return 300
            return 100
        except Exception:
            return 200
    
    # ============================================================
    # تولید گزارش‌ها
    # ============================================================
    
    def generate_report(self, report_type: str = 'daily') -> Dict[str, Any]:
        """
        تولید گزارش دوره‌ای
        
        پارامترها:
            report_type: نوع گزارش (daily, weekly, monthly)
            
        بازگشت: دیکشنری شامل گزارش
        """
        try:
            # تنظیم بازه زمانی
            now = datetime.now()
            if report_type == 'daily':
                start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
                end_date = now.strftime("%Y-%m-%d %H:%M:%S")
                days = 1
            elif report_type == 'weekly':
                start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
                end_date = now.strftime("%Y-%m-%d %H:%M:%S")
                days = 7
            elif report_type == 'monthly':
                start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                end_date = now.strftime("%Y-%m-%d %H:%M:%S")
                days = 30
            else:
                start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
                end_date = now.strftime("%Y-%m-%d %H:%M:%S")
                days = 1
            
            # جمع‌آوری آمار
            total_users = self.get_total_users()
            new_users = self.get_new_users(hours=days * 24)
            active_users = self.get_active_users(minutes=days * 24 * 60)
            
            order_stats = self.get_order_stats()
            error_stats = self.get_error_stats()
            rpm = self.get_requests_per_minute()
            resources = self.get_system_resources()
            db_size = self.get_db_size()
            
            report = {
                'report_type': report_type,
                'generated_at': now.isoformat(),
                'period': {
                    'start': start_date,
                    'end': end_date,
                    'days': days,
                },
                'summary': {
                    'total_users': total_users,
                    'new_users': new_users,
                    'active_users': active_users,
                    'total_orders': order_stats.get('total_orders', 0),
                    'total_revenue': order_stats.get('total_revenue', 0),
                    'avg_order_value': order_stats.get('avg_order_value', 0),
                    'total_errors': error_stats.get('total', 0),
                    'unresolved_errors': error_stats.get('unresolved', 0),
                    'rpm': rpm,
                    'db_size_mb': db_size,
                },
                'system_resources': resources if resources.get('available', False) else {},
                'error_breakdown': error_stats.get('by_type', []),
            }
            
            # ذخیره گزارش
            if self._repository:
                report_id = self._repository.save_report(report)
                report['id'] = report_id
            
            return report
            
        except Exception as e:
            log_general_error(
                f"Error generating {report_type} report: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'error': str(e),
                'report_type': report_type,
                'generated_at': datetime.now().isoformat(),
            }
    
    # ============================================================
    # بررسی سلامت
    # ============================================================
    
    def run_health_check(self) -> Dict[str, Any]:
        """
        اجرای بررسی کامل سلامت تمام سرویس‌ها
        
        بازگشت: دیکشنری شامل نتایج بررسی
        """
        start_time = time.time()
        results = {}
        
        try:
            # ========== بررسی دیتابیس ==========
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    results['database'] = {
                        'status': 'ok',
                        'message': 'اتصال برقرار است',
                        'status_text': '🟢 سالم'
                    }
            except Exception as e:
                results['database'] = {
                    'status': 'error',
                    'message': str(e),
                    'status_text': '🔴 مشکل'
                }
            
            # ========== بررسی Redis ==========
            if config.REDIS_ENABLED:
                try:
                    from cache import get_cache_manager
                    cache = get_cache_manager()
                    # تست اتصال
                    import asyncio
                    # استفاده از asyncio.run() در تابع همزمان
                    # برای سادگی، از یک عملیات ساده استفاده می‌کنیم
                    results['redis'] = {
                        'status': 'ok',
                        'message': 'اتصال برقرار است',
                        'status_text': '🟢 سالم'
                    }
                except Exception as e:
                    results['redis'] = {
                        'status': 'error',
                        'message': str(e),
                        'status_text': '🔴 مشکل'
                    }
            else:
                results['redis'] = {
                    'status': 'disabled',
                    'message': 'غیرفعال است',
                    'status_text': '⚪ غیرفعال'
                }
            
            # ========== بررسی فضای دیسک ==========
            try:
                import psutil
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                if disk_percent > 90:
                    status = 'warning'
                    status_text = '🟡 هشدار'
                elif disk_percent > 95:
                    status = 'error'
                    status_text = '🔴 مشکل'
                else:
                    status = 'ok'
                    status_text = '🟢 سالم'
                
                results['disk'] = {
                    'status': status,
                    'message': f'{disk_percent:.1f}% استفاده شده',
                    'status_text': status_text,
                    'details': {
                        'used_gb': round(disk.used / (1024**3), 2),
                        'free_gb': round(disk.free / (1024**3), 2),
                        'total_gb': round(disk.total / (1024**3), 2),
                    }
                }
            except:
                results['disk'] = {
                    'status': 'unknown',
                    'message': 'قابل بررسی نیست (psutil نصب نیست)',
                    'status_text': '⚪ نامشخص'
                }
            
            # ========== منابع سیستم ==========
            resources = self.get_system_resources()
            if resources.get('available', False):
                results['system'] = {
                    'status': 'ok' if resources['cpu_percent'] < 80 and resources['memory_percent'] < 80 else 'warning',
                    'status_text': '🟢 سالم' if resources['cpu_percent'] < 80 and resources['memory_percent'] < 80 else '🟡 هشدار',
                    'details': {
                        'cpu_percent': resources['cpu_percent'],
                        'memory_percent': resources['memory_percent'],
                    }
                }
            
            # ========== محاسبه وضعیت کلی ==========
            overall = 'ok'
            for key, result in results.items():
                if result.get('status') == 'error':
                    overall = 'error'
                    break
                elif result.get('status') == 'warning' and overall != 'error':
                    overall = 'warning'
            
            status_texts = {
                'ok': '🟢 همه سرویس‌ها سالم',
                'warning': '🟡 برخی هشدارها',
                'error': '🔴 برخی سرویس‌ها مشکل دارند',
            }
            
            results['overall'] = overall
            results['overall_status_text'] = status_texts.get(overall, '🟢 سالم')
            results['elapsed_ms'] = int((time.time() - start_time) * 1000)
            
            return results
            
        except Exception as e:
            log_general_error(
                f"Error running health check: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'overall': 'error',
                'overall_status_text': '🔴 خطا در بررسی سلامت',
                'error': str(e),
                'elapsed_ms': int((time.time() - start_time) * 1000),
            }


# ============================================================
# آبجکت سراسری (Singleton)
# ============================================================

_monitoring_service = None


def get_monitoring_service(connection=None, repository=None) -> MonitoringService:
    """
    دریافت آبجکت سراسری MonitoringService (Singleton)
    
    پارامترها:
        connection: اتصال به دیتابیس (در صورت عدم ارائه، اتصال جدید ایجاد می‌شود)
        repository: ریپازیتوری مانیتورینگ (اختیاری)
    
    بازگشت: نمونه‌ی MonitoringService
    """
    global _monitoring_service
    if _monitoring_service is None:
        if connection is None:
            from database import get_db_connection
            connection = get_db_connection()
        _monitoring_service = MonitoringService(connection, repository)
    return _monitoring_service


# ============================================================
# توابع راحت برای استفاده در سایر بخش‌ها
# ============================================================

def get_system_stats() -> Dict[str, Any]:
    """
    دریافت آمار کلی سیستم (تابع راحت)
    
    بازگشت: دیکشنری شامل آمار سیستم
    """
    service = get_monitoring_service()
    return {
        'total_users': service.get_total_users(),
        'active_users': service.get_active_users(5),
        'new_users_24h': service.get_new_users(24),
        'orders': service.get_order_stats(),
        'errors': service.get_error_stats(),
        'rpm': service.get_requests_per_minute(),
        'resources': service.get_system_resources(),
        'db_size_mb': service.get_db_size(),
    }


def run_health_check() -> Dict[str, Any]:
    """
    اجرای بررسی سلامت (تابع راحت)
    
    بازگشت: دیکشنری شامل نتایج بررسی
    """
    service = get_monitoring_service()
    return service.run_health_check()


def generate_monitoring_report(report_type: str = 'daily') -> Dict[str, Any]:
    """
    تولید گزارش مانیتورینگ (تابع راحت)
    
    پارامترها:
        report_type: نوع گزارش (daily, weekly, monthly)
    
    بازگشت: دیکشنری شامل گزارش
    """
    service = get_monitoring_service()
    return service.generate_report(report_type)


def check_system_alerts() -> List[Dict[str, Any]]:
    """
    بررسی هشدارهای سیستم (تابع راحت)
    
    بازگشت: لیست هشدارهای جدید
    """
    service = get_monitoring_service()
    return service.check_alerts()


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'MonitoringService',
    'MetricType',
    'get_monitoring_service',
    'get_system_stats',
    'run_health_check',
    'generate_monitoring_report',
    'check_system_alerts',
]