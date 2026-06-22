# admin_panel/monitoring/metrics.py
# جمع‌آوری و مدیریت متریک‌های عملکردی سیستم
# شامل: ذخیره‌سازی متریک‌ها، دریافت خلاصه، پاکسازی و تحلیل

import json
import time
import traceback
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum

from logger_config import logger, ContextLogger
from core import send_message
from database import get_db_connection
from config import config
from utils.error_handler import log_callback_error, log_general_error, log_database_error


# ============================================================
# تعریف انواع متریک‌ها
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
# کلاس متریک
# ============================================================

class Metric:
    """نمایش یک متریک با مقدار و زمان"""
    
    def __init__(self, metric_type: MetricType, value: Any, timestamp: Optional[datetime] = None):
        self.type = metric_type
        self.value = value
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value if isinstance(self.type, MetricType) else self.type,
            'value': self.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metric':
        return cls(
            metric_type=data.get('type'),
            value=data.get('value'),
            timestamp=datetime.fromisoformat(data.get('timestamp')) if data.get('timestamp') else None
        )


# ============================================================
# توابع ذخیره‌سازی متریک‌ها در دیتابیس
# ============================================================

def _create_metrics_table_if_not_exists():
    """ایجاد جدول metrics در صورت عدم وجود"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cursor.close()
            logger.debug("Table system_metrics created/checked successfully")
    except Exception as e:
        log_database_error(
            f"Error creating system_metrics table: {str(e)}",
            traceback=traceback.format_exc()
        )


def save_metric(metric_type: str, value: Any) -> bool:
    """
    ذخیره یک متریک در دیتابیس

    پارامترها:
        metric_type: نوع متریک
        value: مقدار متریک (JSON Serializable)

    بازگشت: True در صورت موفقیت
    """
    try:
        _create_metrics_table_if_not_exists()
        
        value_str = json.dumps(value, ensure_ascii=False, default=str)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO system_metrics (metric_type, value) VALUES (?, ?)",
                (metric_type, value_str)
            )
            conn.commit()
            cursor.close()
            return True
    except Exception as e:
        log_database_error(
            f"Error saving metric {metric_type}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


def save_metrics(metrics: List[Metric]) -> int:
    """
    ذخیره چندین متریک به صورت دسته‌ای

    پارامترها:
        metrics: لیست متریک‌ها

    بازگشت: تعداد متریک‌های ذخیره‌شده
    """
    try:
        _create_metrics_table_if_not_exists()
        
        saved_count = 0
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for metric in metrics:
                value_str = json.dumps(metric.value, ensure_ascii=False, default=str)
                cursor.execute(
                    "INSERT INTO system_metrics (metric_type, value, timestamp) VALUES (?, ?, ?)",
                    (metric.type.value if isinstance(metric.type, MetricType) else metric.type,
                     value_str,
                     metric.timestamp.isoformat() if metric.timestamp else None)
                )
                saved_count += 1
            conn.commit()
            cursor.close()
            return saved_count
    except Exception as e:
        log_database_error(
            f"Error saving metrics batch: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0


def get_metrics(
    metric_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    دریافت متریک‌ها از دیتابیس با فیلترهای اختیاری

    پارامترها:
        metric_type: نوع متریک (اختیاری)
        start_time: زمان شروع (اختیاری)
        end_time: زمان پایان (اختیاری)
        limit: تعداد نتایج
        offset: موقعیت شروع

    بازگشت: لیست متریک‌ها
    """
    try:
        conditions = []
        params = []
        
        if metric_type:
            conditions.append("metric_type = ?")
            params.append(metric_type)
        
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM system_metrics
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (*params, limit, offset))
            rows = cursor.fetchall()
            cursor.close()
            
            result = []
            for row in rows:
                item = dict(row)
                try:
                    item['value'] = json.loads(item['value'])
                except:
                    pass
                result.append(item)
            return result
    except Exception as e:
        log_database_error(
            f"Error getting metrics: {str(e)}",
            traceback=traceback.format_exc()
        )
        return []


def get_latest_metric(metric_type: str) -> Optional[Dict[str, Any]]:
    """
    دریافت آخرین متریک از یک نوع خاص

    پارامترها:
        metric_type: نوع متریک

    بازگشت: آخرین متریک یا None
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM system_metrics
                WHERE metric_type = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (metric_type,))
            row = cursor.fetchone()
            cursor.close()
            if row:
                result = dict(row)
                try:
                    result['value'] = json.loads(result['value'])
                except:
                    pass
                return result
            return None
    except Exception as e:
        log_database_error(
            f"Error getting latest metric {metric_type}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return None


def get_metrics_by_type(metric_type: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    دریافت متریک‌های یک نوع خاص (برای نمایش در پنل)

    پارامترها:
        metric_type: نوع متریک
        limit: تعداد نتایج

    بازگشت: لیست متریک‌ها
    """
    return get_metrics(metric_type=metric_type, limit=limit)


def get_metrics_summary(
    metric_type: Optional[str] = None,
    hours: int = 24
) -> Dict[str, Any]:
    """
    دریافت خلاصه متریک‌ها در بازه زمانی مشخص

    پارامترها:
        metric_type: نوع متریک (اختیاری)
        hours: تعداد ساعت‌های اخیر

    بازگشت: دیکشنری شامل خلاصه
    """
    try:
        start_time = datetime.now() - timedelta(hours=hours)
        metrics = get_metrics(
            metric_type=metric_type,
            start_time=start_time,
            limit=1000
        )
        
        if not metrics:
            return {
                'count': 0,
                'types': [],
                'latest': None,
                'oldest': None,
            }
        
        types = list(set(m['metric_type'] for m in metrics))
        
        return {
            'count': len(metrics),
            'types': types,
            'latest': metrics[0] if metrics else None,
            'oldest': metrics[-1] if metrics else None,
            'hours': hours,
            'start_time': start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
        }
    except Exception as e:
        log_database_error(
            f"Error getting metrics summary: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {
            'count': 0,
            'types': [],
            'latest': None,
            'oldest': None,
            'error': str(e)
        }


def cleanup_old_metrics(days: int = 30) -> int:
    """
    پاکسازی متریک‌های قدیمی‌تر از تعداد روز مشخص

    پارامترها:
        days: تعداد روزهای نگهداری

    بازگشت: تعداد متریک‌های حذف‌شده
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM system_metrics WHERE timestamp < datetime('now', '-' || ? || ' days')",
                (days,)
            )
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            logger.info(f"🗑️ Deleted {deleted_count} old metrics older than {days} days")
            return deleted_count
    except Exception as e:
        log_database_error(
            f"Error cleaning up old metrics: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0


# ============================================================
# جمع‌آوری متریک‌ها
# ============================================================

async def collect_metrics() -> Dict[str, Any]:
    """
    جمع‌آوری متریک‌های لحظه‌ای از سیستم و ذخیره در دیتابیس

    بازگشت: دیکشنری شامل متریک‌های جمع‌آوری‌شده
    """
    ctx_logger = ContextLogger("monitoring.metrics.collect")
    
    try:
        metrics = []
        results = {}
        
        # ========== جمع‌آوری متریک‌های سیستمی ==========
        try:
            from admin_panel.monitoring.health import get_system_resources, check_disk_usage
            resources = get_system_resources()
            if resources.get('available', False):
                cpu_metric = Metric(MetricType.CPU_USAGE, resources.get('cpu_percent', 0))
                memory_metric = Metric(MetricType.MEMORY_USAGE, resources.get('memory_percent', 0))
                metrics.extend([cpu_metric, memory_metric])
                results['cpu'] = resources.get('cpu_percent', 0)
                results['memory'] = resources.get('memory_percent', 0)
            
            disk = check_disk_usage()
            if disk.get('status') != 'error':
                disk_details = disk.get('details', {})
                disk_metric = Metric(MetricType.DISK_USAGE, {
                    'used_percent': disk_details.get('used_percent', 0),
                    'free_gb': disk_details.get('free_gb', 0),
                    'used_gb': disk_details.get('used_gb', 0),
                    'total_gb': disk_details.get('total_gb', 0),
                })
                metrics.append(disk_metric)
                results['disk'] = disk_details
        except Exception as e:
            log_general_error(
                f"Error collecting system metrics: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )
        
        # ========== جمع‌آوری متریک‌های کاربران ==========
        try:
            from database import get_total_users, get_active_users
            from admin_panel.monitoring.dashboard import _get_active_users_since
            
            total_users = get_total_users()
            active_5min = _get_active_users_since(5)
            active_today = get_active_users(1)
            new_users = _get_new_users_count()
            
            metrics.append(Metric(MetricType.TOTAL_USERS, total_users))
            metrics.append(Metric(MetricType.ACTIVE_USERS, {
                '5min': active_5min,
                'today': active_today,
            }))
            metrics.append(Metric(MetricType.NEW_USERS, new_users))
            
            results['users'] = {
                'total': total_users,
                'active_5min': active_5min,
                'active_today': active_today,
                'new_users': new_users,
            }
        except Exception as e:
            log_general_error(
                f"Error collecting user metrics: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )
        
        # ========== جمع‌آوری متریک‌های سفارشات ==========
        try:
            from database.db_stats import get_dashboard_stats
            
            stats = get_dashboard_stats()
            orders_count = stats.get('total_orders', 0)
            revenue = stats.get('total_revenue', 0)
            conversion_rate = stats.get('overall_conversion', 0)
            
            metrics.append(Metric(MetricType.ORDERS_COUNT, orders_count))
            metrics.append(Metric(MetricType.REVENUE, revenue))
            metrics.append(Metric(MetricType.CONVERSION_RATE, conversion_rate))
            
            results['orders'] = {
                'count': orders_count,
                'revenue': revenue,
                'conversion_rate': conversion_rate,
            }
        except Exception as e:
            log_general_error(
                f"Error collecting order metrics: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )
        
        # ========== جمع‌آوری متریک‌های خطاها ==========
        try:
            from database.db_logs import get_error_stats
            
            error_stats = get_error_stats()
            total_errors = error_stats.get('total', 0)
            
            metrics.append(Metric(MetricType.ERROR_COUNT, {
                'total': total_errors,
                'unresolved': error_stats.get('unresolved', 0),
                'resolved': error_stats.get('resolved', 0),
            }))
            
            # نرخ خطا (تعداد خطاهای ۵ دقیقه اخیر)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM error_logs WHERE created_at >= datetime('now', '-5 minutes')"
                )
                row = cursor.fetchone()
                error_rate_5min = row['count'] if row else 0
                cursor.close()
            
            metrics.append(Metric(MetricType.ERROR_RATE, {
                '5min': error_rate_5min,
                'total': total_errors,
            }))
            
            results['errors'] = {
                'total': total_errors,
                'unresolved': error_stats.get('unresolved', 0),
                'rate_5min': error_rate_5min,
            }
        except Exception as e:
            log_general_error(
                f"Error collecting error metrics: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )
        
        # ========== جمع‌آوری متریک‌های درخواست‌ها ==========
        try:
            from admin_panel.monitoring.dashboard import _get_requests_per_minute
            
            rpm = _get_requests_per_minute()
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM button_stats")
                row = cursor.fetchone()
                total_requests = row['count'] if row else 0
                cursor.close()
            
            metrics.append(Metric(MetricType.REQUESTS_PER_MINUTE, rpm))
            metrics.append(Metric(MetricType.TOTAL_REQUESTS, total_requests))
            
            results['requests'] = {
                'rpm': rpm,
                'total': total_requests,
            }
        except Exception as e:
            log_general_error(
                f"Error collecting request metrics: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )
        
        # ========== جمع‌آوری متریک‌های دکمه‌ها ==========
        try:
            from database import get_top_buttons
            
            top_buttons = get_top_buttons(limit=5, sort_by='clicks')
            
            button_metrics = []
            for btn in top_buttons:
                button_metrics.append({
                    'button_id': btn.get('button_id'),
                    'name': btn.get('button_name'),
                    'clicks': btn.get('clicks', 0),
                    'orders': btn.get('orders', 0),
                    'conversion': btn.get('conversion_rate', 0),
                })
            
            metrics.append(Metric(MetricType.BUTTON_CLICKS, {
                'top_5': button_metrics,
            }))
            
            # نرخ تبدیل دکمه‌ها
            if top_buttons:
                total_clicks = sum(b.get('clicks', 0) for b in top_buttons)
                total_orders = sum(b.get('orders', 0) for b in top_buttons)
                avg_conversion = (total_orders / total_clicks * 100) if total_clicks > 0 else 0
                
                metrics.append(Metric(MetricType.BUTTON_CONVERSION, {
                    'avg_conversion': avg_conversion,
                    'top_5': button_metrics,
                }))
            
            results['buttons'] = {
                'top_5': button_metrics,
            }
        except Exception as e:
            log_general_error(
                f"Error collecting button metrics: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )
        
        # ========== ذخیره متریک‌ها در دیتابیس ==========
        saved_count = save_metrics(metrics)
        results['saved_count'] = saved_count
        results['timestamp'] = datetime.now().isoformat()
        
        logger.info(f"✅ Collected {len(metrics)} metrics, saved {saved_count} items")
        return results
        
    except Exception as e:
        log_callback_error(
            f"Error in collect_metrics: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'saved_count': 0,
        }


def _get_new_users_count(hours: int = 24) -> int:
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
            cursor.close()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(
            f"Error getting new users count: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0


# ============================================================
# کیبورد بخش متریک‌ها
# ============================================================

def metrics_main_keyboard() -> Dict[str, Any]:
    """کیبورد اصلی بخش متریک‌ها"""
    return {
        "inline_keyboard": [
            [{"text": "🔄 جمع‌آوری متریک‌های جدید", "callback_data": "admin_monitoring_metrics_collect"}],
            [{"text": "📊 خلاصه متریک‌ها", "callback_data": "admin_monitoring_metrics_summary"}],
            [{"text": "🗑️ پاکسازی متریک‌های قدیمی", "callback_data": "admin_monitoring_metrics_cleanup"}],
            [{"text": "🔙 بازگشت به مانیتورینگ", "callback_data": "admin_monitoring"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


# ============================================================
# هندلرهای بخش متریک‌ها
# ============================================================

async def handle_metrics(chat_id: int, user_id: int) -> bool:
    """
    نمایش صفحه اصلی مدیریت متریک‌ها

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    ctx_logger = ContextLogger("monitoring.metrics.handler", context={"user_id": user_id, "chat_id": chat_id})

    try:
        summary = get_metrics_summary(hours=24)
        
        msg = f"📊 **مدیریت متریک‌های سیستم**\n\n"
        
        if 'error' in summary:
            msg += f"⚠️ خطا در دریافت خلاصه: {summary['error']}\n\n"
        else:
            msg += f"📌 **خلاصه ۲۴ ساعت اخیر:**\n"
            msg += f"  • تعداد متریک‌ها: {summary.get('count', 0)}\n"
            msg += f"  • انواع متریک‌ها: {', '.join(summary.get('types', []))}\n\n"
            
            if summary.get('latest'):
                latest = summary['latest']
                msg += f"🕐 **آخرین متریک:**\n"
                msg += f"  • نوع: {latest.get('metric_type', 'نامشخص')}\n"
                msg += f"  • مقدار: {latest.get('value', 'نامشخص')}\n"
                msg += f"  • زمان: {latest.get('timestamp', 'نامشخص')}\n"
        
        await send_message(chat_id, msg, metrics_main_keyboard())
        ctx_logger.info(f"Metrics page shown to user {user_id}")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_metrics: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(
            chat_id,
            "❌ خطا در نمایش صفحه متریک‌ها. لطفاً دوباره تلاش کنید.",
            metrics_main_keyboard()
        )
        return True


async def handle_metrics_collect(chat_id: int, user_id: int) -> bool:
    """
    اجرای جمع‌آوری متریک‌های جدید

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    ctx_logger = ContextLogger("monitoring.metrics.collect_handler", context={"user_id": user_id, "chat_id": chat_id})

    try:
        await send_message(chat_id, "🔄 در حال جمع‌آوری متریک‌ها... لطفاً صبر کنید.")
        
        results = await collect_metrics()
        
        if 'error' in results:
            msg = f"❌ خطا در جمع‌آوری متریک‌ها:\n{results['error']}"
        else:
            msg = f"✅ **جمع‌آوری متریک‌ها تکمیل شد**\n\n"
            msg += f"📊 تعداد متریک‌های ذخیره‌شده: {results.get('saved_count', 0)}\n"
            msg += f"🕐 زمان: {results.get('timestamp', 'نامشخص')}\n\n"
            
            if 'users' in results:
                users = results['users']
                msg += f"👥 کاربران:\n"
                msg += f"  • کل: {users.get('total', 0)}\n"
                msg += f"  • فعال ۵ دقیقه: {users.get('active_5min', 0)}\n"
                msg += f"  • فعال امروز: {users.get('active_today', 0)}\n"
                msg += f"  • کاربران جدید: {users.get('new_users', 0)}\n\n"
            
            if 'orders' in results:
                orders = results['orders']
                msg += f"💰 سفارشات:\n"
                msg += f"  • تعداد: {orders.get('count', 0)}\n"
                msg += f"  • درآمد: {orders.get('revenue', 0):,} ریال\n"
                msg += f"  • نرخ تبدیل: {orders.get('conversion_rate', 0):.2f}%\n\n"
            
            if 'requests' in results:
                requests = results['requests']
                msg += f"📨 درخواست‌ها:\n"
                msg += f"  • میانگین RPM: {requests.get('rpm', 0)}\n"
                msg += f"  • کل: {requests.get('total', 0):,}\n\n"
            
            if 'errors' in results:
                errors = results['errors']
                msg += f"🚨 خطاها:\n"
                msg += f"  • کل: {errors.get('total', 0)}\n"
                msg += f"  • حل‌نشده: {errors.get('unresolved', 0)}\n"
                msg += f"  • نرخ ۵ دقیقه: {errors.get('rate_5min', 0)}\n"
        
        await send_message(chat_id, msg, metrics_main_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_metrics_collect: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(
            chat_id,
            "❌ خطا در جمع‌آوری متریک‌ها.",
            metrics_main_keyboard()
        )
        return True


async def handle_metrics_summary(chat_id: int, user_id: int) -> bool:
    """
    نمایش خلاصه کامل متریک‌ها

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    ctx_logger = ContextLogger("monitoring.metrics.summary_handler", context={"user_id": user_id, "chat_id": chat_id})

    try:
        summary = get_metrics_summary(hours=24)
        
        if 'error' in summary:
            msg = f"❌ خطا در دریافت خلاصه متریک‌ها:\n{summary['error']}"
            await send_message(chat_id, msg, metrics_main_keyboard())
            return True
        
        msg = f"📊 **خلاصه متریک‌های سیستم**\n\n"
        msg += f"📌 **بازه زمانی:** ۲۴ ساعت اخیر\n"
        msg += f"📊 **تعداد متریک‌ها:** {summary.get('count', 0)}\n"
        
        types = summary.get('types', [])
        if types:
            msg += f"📋 **انواع:** {', '.join(types)}\n\n"
        else:
            msg += "\n"
        
        # دریافت متریک‌های خاص برای نمایش
        latest_cpu = get_latest_metric('cpu_usage')
        if latest_cpu:
            value = latest_cpu.get('value', {})
            msg += f"🖥️ **CPU:** {value}%\n"
        
        latest_memory = get_latest_metric('memory_usage')
        if latest_memory:
            value = latest_memory.get('value', {})
            msg += f"💾 **Memory:** {value}%\n"
        
        latest_users = get_latest_metric('total_users')
        if latest_users:
            value = latest_users.get('value', 0)
            msg += f"👥 **کل کاربران:** {value:,}\n"
        
        latest_orders = get_latest_metric('orders_count')
        if latest_orders:
            value = latest_orders.get('value', 0)
            msg += f"📦 **کل سفارشات:** {value:,}\n"
        
        latest_revenue = get_latest_metric('revenue')
        if latest_revenue:
            value = latest_revenue.get('value', 0)
            msg += f"💰 **کل درآمد:** {value:,} ریال\n"
        
        latest_errors = get_latest_metric('error_count')
        if latest_errors:
            value = latest_errors.get('value', {})
            total = value.get('total', 0)
            unresolved = value.get('unresolved', 0)
            msg += f"🚨 **خطاها:** {total} (حل‌نشده: {unresolved})\n"
        
        msg += "\n"
        msg += f"🕐 **آخرین به‌روزرسانی:** {summary.get('latest', {}).get('timestamp', 'نامشخص') if summary.get('latest') else 'نامشخص'}\n"
        msg += f"🕐 **قدیمی‌ترین:** {summary.get('oldest', {}).get('timestamp', 'نامشخص') if summary.get('oldest') else 'نامشخص'}"
        
        await send_message(chat_id, msg, metrics_main_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_metrics_summary: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(
            chat_id,
            "❌ خطا در نمایش خلاصه متریک‌ها.",
            metrics_main_keyboard()
        )
        return True


async def handle_metrics_cleanup(chat_id: int, user_id: int) -> bool:
    """
    پاکسازی متریک‌های قدیمی

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    ctx_logger = ContextLogger("monitoring.metrics.cleanup_handler", context={"user_id": user_id, "chat_id": chat_id})

    try:
        summary = get_metrics_summary()
        count = summary.get('count', 0)
        
        if count == 0:
            msg = "📊 هیچ متریکی برای پاکسازی وجود ندارد."
            await send_message(chat_id, msg, metrics_main_keyboard())
            return True
        
        deleted = cleanup_old_metrics(days=config.METRICS_RETENTION_DAYS)
        
        msg = f"🗑️ **پاکسازی متریک‌های قدیمی**\n\n"
        msg += f"📊 متریک‌های موجود: {count}\n"
        msg += f"🗑️ متریک‌های حذف‌شده: {deleted}\n"
        msg += f"📌 متریک‌های باقی‌مانده: {count - deleted}\n"
        msg += f"⏰ متریک‌های قدیمی‌تر از {config.METRICS_RETENTION_DAYS} روز حذف شدند."
        
        await send_message(chat_id, msg, metrics_main_keyboard())
        ctx_logger.info(f"Metrics cleanup: deleted {deleted} items")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_metrics_cleanup: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(
            chat_id,
            "❌ خطا در پاکسازی متریک‌ها.",
            metrics_main_keyboard()
        )
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'MetricType',
    'Metric',
    'save_metric',
    'save_metrics',
    'get_metrics',
    'get_latest_metric',
    'get_metrics_by_type',
    'get_metrics_summary',
    'cleanup_old_metrics',
    'collect_metrics',
    '_get_new_users_count',
    'handle_metrics',
    'handle_metrics_collect',
    'handle_metrics_summary',
    'handle_metrics_cleanup',
    'metrics_main_keyboard',
]