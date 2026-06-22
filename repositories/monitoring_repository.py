# repositories/monitoring_repository.py
# ریپازیتوری مانیتورینگ - مدیریت عملیات دیتابیس مربوط به متریک‌ها، هشدارها و گزارش‌ها
# اصلاح شده برای سازگاری با SQLite و رفع خطای get_cursor

import json
import traceback
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from logger_config import logger
from .base_repository import BaseRepository
from utils.error_handler import log_database_error, log_general_error


class MonitoringRepository(BaseRepository):
    """
    ریپازیتوری مانیتورینگ - مدیریت عملیات دیتابیس مربوط به:
    - متریک‌های سیستم (system_metrics)
    - هشدارها (alerts)
    - گزارش‌های دوره‌ای (reports)
    """
    
    def __init__(self, connection):
        super().__init__(connection, 'system_metrics', 'id')
        self._ensure_tables()
    
    # ============================================================
    # ایجاد جداول در صورت عدم وجود
    # ============================================================
    
    def _ensure_tables(self):
        """اطمینان از وجود جداول مورد نیاز مانیتورینگ"""
        try:
            # استفاده از cursor مستقیم (نه get_cursor)
            cursor = self._connection.cursor()
            
            # جدول متریک‌ها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # جدول هشدارها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_level TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    is_resolved INTEGER DEFAULT 0,
                    resolved_at TEXT,
                    resolved_by INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # جدول گزارش‌ها
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_by INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self._connection.commit()
            cursor.close()
            logger.debug("Monitoring tables created/checked successfully")
            
        except Exception as e:
            log_database_error(
                f"Error creating monitoring tables: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    # ============================================================
    # متدهای متریک‌ها (Metrics)
    # ============================================================
    
    def save_metric(self, metric_type: str, value: Any) -> bool:
        """
        ذخیره یک متریک در دیتابیس

        پارامترها:
            metric_type: نوع متریک
            value: مقدار متریک (JSON Serializable)

        بازگشت: True در صورت موفقیت
        """
        try:
            value_str = json.dumps(value, ensure_ascii=False, default=str)
            
            cursor = self._connection.cursor()
            cursor.execute(
                "INSERT INTO system_metrics (metric_type, value) VALUES (?, ?)",
                (metric_type, value_str)
            )
            self._connection.commit()
            cursor.close()
            return True
            
        except Exception as e:
            log_database_error(
                f"Error saving metric {metric_type}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def save_metrics_batch(self, metrics: List[Dict[str, Any]]) -> int:
        """
        ذخیره چندین متریک به صورت دسته‌ای

        پارامترها:
            metrics: لیست دیکشنری‌های شامل metric_type و value

        بازگشت: تعداد متریک‌های ذخیره‌شده
        """
        try:
            saved_count = 0
            cursor = self._connection.cursor()
            
            for metric in metrics:
                metric_type = metric.get('metric_type')
                value = metric.get('value')
                if metric_type is None:
                    continue
                
                value_str = json.dumps(value, ensure_ascii=False, default=str)
                cursor.execute(
                    "INSERT INTO system_metrics (metric_type, value) VALUES (?, ?)",
                    (metric_type, value_str)
                )
                saved_count += 1
            
            self._connection.commit()
            cursor.close()
            return saved_count
            
        except Exception as e:
            log_database_error(
                f"Error saving metrics batch: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return 0
    
    def get_metrics(
        self,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "timestamp DESC"
    ) -> List[Dict[str, Any]]:
        """
        دریافت متریک‌ها با فیلترهای اختیاری

        پارامترها:
            metric_type: نوع متریک (اختیاری)
            start_time: زمان شروع (اختیاری)
            end_time: زمان پایان (اختیاری)
            limit: تعداد نتایج
            offset: موقعیت شروع
            order_by: ترتیب مرتب‌سازی

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
            
            cursor = self._connection.cursor()
            cursor.execute(f"""
                SELECT * FROM system_metrics
                WHERE {where_clause}
                ORDER BY {order_by}
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
    
    def get_latest_metric(self, metric_type: str) -> Optional[Dict[str, Any]]:
        """
        دریافت آخرین متریک از یک نوع خاص

        پارامترها:
            metric_type: نوع متریک

        بازگشت: آخرین متریک یا None
        """
        try:
            cursor = self._connection.cursor()
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
    
    def get_metrics_summary(
        self,
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
            metrics = self.get_metrics(
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
    
    def cleanup_old_metrics(self, days: int = 30) -> int:
        """
        پاکسازی متریک‌های قدیمی‌تر از تعداد روز مشخص

        پارامترها:
            days: تعداد روزهای نگهداری

        بازگشت: تعداد متریک‌های حذف‌شده
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "DELETE FROM system_metrics WHERE timestamp < datetime('now', '-' || ? || ' days')",
                (days,)
            )
            deleted_count = cursor.rowcount
            self._connection.commit()
            cursor.close()
            return deleted_count
            
        except Exception as e:
            log_database_error(
                f"Error cleaning up old metrics: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_metrics_count(self, metric_type: Optional[str] = None) -> int:
        """
        دریافت تعداد متریک‌ها (با فیلتر اختیاری نوع)

        پارامترها:
            metric_type: نوع متریک (اختیاری)

        بازگشت: تعداد متریک‌ها
        """
        try:
            conditions = []
            params = []
            
            if metric_type:
                conditions.append("metric_type = ?")
                params.append(metric_type)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor = self._connection.cursor()
            cursor.execute(
                f"SELECT COUNT(*) as count FROM system_metrics WHERE {where_clause}",
                params
            )
            row = cursor.fetchone()
            cursor.close()
            return row['count'] if row else 0
            
        except Exception as e:
            log_database_error(
                f"Error getting metrics count: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # متدهای هشدارها (Alerts)
    # ============================================================
    
    def save_alert(
        self,
        alert_level: str,
        alert_type: str,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        ذخیره یک هشدار جدید

        پارامترها:
            alert_level: سطح هشدار (info, warning, error, critical)
            alert_type: نوع هشدار
            title: عنوان هشدار
            message: پیام هشدار
            details: جزئیات اضافی (اختیاری)

        بازگشت: شناسه هشدار یا None
        """
        try:
            details_str = json.dumps(details, ensure_ascii=False, default=str) if details else None
            
            cursor = self._connection.cursor()
            cursor.execute("""
                INSERT INTO alerts (alert_level, alert_type, title, message, details, is_resolved)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (alert_level, alert_type, title, message, details_str, 0))
            self._connection.commit()
            alert_id = cursor.lastrowid
            cursor.close()
            return alert_id
            
        except Exception as e:
            log_database_error(
                f"Error saving alert: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_active_alerts(
        self,
        alert_level: Optional[str] = None,
        alert_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        دریافت هشدارهای فعال (حل‌نشده)

        پارامترها:
            alert_level: سطح هشدار (اختیاری)
            alert_type: نوع هشدار (اختیاری)
            limit: تعداد نتایج

        بازگشت: لیست هشدارهای فعال
        """
        try:
            conditions = ["is_resolved = 0"]
            params = []
            
            if alert_level:
                conditions.append("alert_level = ?")
                params.append(alert_level)
            
            if alert_type:
                conditions.append("alert_type = ?")
                params.append(alert_type)
            
            where_clause = " AND ".join(conditions)
            
            cursor = self._connection.cursor()
            cursor.execute(f"""
                SELECT * FROM alerts
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, (*params, limit))
            rows = cursor.fetchall()
            cursor.close()
            
            result = []
            for row in rows:
                item = dict(row)
                if item.get('details'):
                    try:
                        item['details'] = json.loads(item['details'])
                    except:
                        pass
                result.append(item)
            return result
            
        except Exception as e:
            log_database_error(
                f"Error getting active alerts: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_all_alerts(
        self,
        is_resolved: Optional[bool] = None,
        alert_level: Optional[str] = None,
        alert_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        دریافت تمام هشدارها با فیلترهای اختیاری

        پارامترها:
            is_resolved: وضعیت حل شدن (اختیاری)
            alert_level: سطح هشدار (اختیاری)
            alert_type: نوع هشدار (اختیاری)
            limit: تعداد نتایج
            offset: موقعیت شروع

        بازگشت: لیست هشدارها
        """
        try:
            conditions = []
            params = []
            
            if is_resolved is not None:
                conditions.append("is_resolved = ?")
                params.append(1 if is_resolved else 0)
            
            if alert_level:
                conditions.append("alert_level = ?")
                params.append(alert_level)
            
            if alert_type:
                conditions.append("alert_type = ?")
                params.append(alert_type)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor = self._connection.cursor()
            cursor.execute(f"""
                SELECT * FROM alerts
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (*params, limit, offset))
            rows = cursor.fetchall()
            cursor.close()
            
            result = []
            for row in rows:
                item = dict(row)
                if item.get('details'):
                    try:
                        item['details'] = json.loads(item['details'])
                    except:
                        pass
                result.append(item)
            return result
            
        except Exception as e:
            log_database_error(
                f"Error getting all alerts: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_alert_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت یک هشدار بر اساس شناسه

        پارامترها:
            alert_id: شناسه هشدار

        بازگشت: دیکشنری هشدار یا None
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                result = dict(row)
                if result.get('details'):
                    try:
                        result['details'] = json.loads(result['details'])
                    except:
                        pass
                return result
            return None
            
        except Exception as e:
            log_database_error(
                f"Error getting alert by id {alert_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def resolve_alert(self, alert_id: int, resolved_by: int) -> bool:
        """
        حل کردن یک هشدار

        پارامترها:
            alert_id: شناسه هشدار
            resolved_by: شناسه کاربر حل‌کننده

        بازگشت: True در صورت موفقیت
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                UPDATE alerts
                SET is_resolved = 1, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                WHERE id = ?
            """, (resolved_by, alert_id))
            self._connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
            
        except Exception as e:
            log_database_error(
                f"Error resolving alert {alert_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def resolve_all_alerts(self, resolved_by: int) -> int:
        """
        حل کردن همه هشدارهای فعال

        پارامترها:
            resolved_by: شناسه کاربر حل‌کننده

        بازگشت: تعداد هشدارهای حل‌شده
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                UPDATE alerts
                SET is_resolved = 1, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                WHERE is_resolved = 0
            """, (resolved_by,))
            resolved_count = cursor.rowcount
            self._connection.commit()
            cursor.close()
            return resolved_count
            
        except Exception as e:
            log_database_error(
                f"Error resolving all alerts: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_alerts_count(
        self,
        is_resolved: Optional[bool] = None,
        alert_level: Optional[str] = None
    ) -> int:
        """
        دریافت تعداد هشدارها

        پارامترها:
            is_resolved: وضعیت حل شدن (اختیاری)
            alert_level: سطح هشدار (اختیاری)

        بازگشت: تعداد هشدارها
        """
        try:
            conditions = []
            params = []
            
            if is_resolved is not None:
                conditions.append("is_resolved = ?")
                params.append(1 if is_resolved else 0)
            
            if alert_level:
                conditions.append("alert_level = ?")
                params.append(alert_level)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor = self._connection.cursor()
            cursor.execute(
                f"SELECT COUNT(*) as count FROM alerts WHERE {where_clause}",
                params
            )
            row = cursor.fetchone()
            cursor.close()
            return row['count'] if row else 0
            
        except Exception as e:
            log_database_error(
                f"Error getting alerts count: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def delete_alert(self, alert_id: int) -> bool:
        """
        حذف یک هشدار

        پارامترها:
            alert_id: شناسه هشدار

        بازگشت: True در صورت موفقیت
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
            self._connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
            
        except Exception as e:
            log_database_error(
                f"Error deleting alert {alert_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def cleanup_old_alerts(self, days: int = 90) -> int:
        """
        پاکسازی هشدارهای قدیمی (حل‌شده)

        پارامترها:
            days: تعداد روزهای نگهداری

        بازگشت: تعداد هشدارهای حذف‌شده
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                DELETE FROM alerts
                WHERE is_resolved = 1
                AND created_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            deleted_count = cursor.rowcount
            self._connection.commit()
            cursor.close()
            return deleted_count
            
        except Exception as e:
            log_database_error(
                f"Error cleaning up old alerts: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # متدهای گزارش‌ها (Reports)
    # ============================================================
    
    def save_report(
        self,
        report_type: str,
        title: str,
        content: Dict[str, Any],
        created_by: int,
        status: str = "pending"
    ) -> Optional[int]:
        """
        ذخیره یک گزارش جدید

        پارامترها:
            report_type: نوع گزارش (daily, weekly, monthly, custom)
            title: عنوان گزارش
            content: محتوای گزارش (دیکشنری JSON)
            created_by: شناسه کاربر ایجادکننده
            status: وضعیت گزارش (pending, completed, failed)

        بازگشت: شناسه گزارش یا None
        """
        try:
            content_str = json.dumps(content, ensure_ascii=False, default=str)
            
            cursor = self._connection.cursor()
            cursor.execute("""
                INSERT INTO reports (report_type, title, content, status, created_by)
                VALUES (?, ?, ?, ?, ?)
            """, (report_type, title, content_str, status, created_by))
            self._connection.commit()
            report_id = cursor.lastrowid
            cursor.close()
            return report_id
            
        except Exception as e:
            log_database_error(
                f"Error saving report: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_report_by_id(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت یک گزارش بر اساس شناسه

        پارامترها:
            report_id: شناسه گزارش

        بازگشت: دیکشنری گزارش یا None
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                result = dict(row)
                if result.get('content'):
                    try:
                        result['content'] = json.loads(result['content'])
                    except:
                        pass
                return result
            return None
            
        except Exception as e:
            log_database_error(
                f"Error getting report by id {report_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_reports(
        self,
        report_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at DESC"
    ) -> List[Dict[str, Any]]:
        """
        دریافت لیست گزارش‌ها

        پارامترها:
            report_type: نوع گزارش (اختیاری)
            status: وضعیت گزارش (اختیاری)
            limit: تعداد نتایج
            offset: موقعیت شروع
            order_by: ترتیب مرتب‌سازی

        بازگشت: لیست گزارش‌ها
        """
        try:
            conditions = []
            params = []
            
            if report_type:
                conditions.append("report_type = ?")
                params.append(report_type)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor = self._connection.cursor()
            cursor.execute(f"""
                SELECT * FROM reports
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
            """, (*params, limit, offset))
            rows = cursor.fetchall()
            cursor.close()
            
            result = []
            for row in rows:
                item = dict(row)
                if item.get('content'):
                    try:
                        item['content'] = json.loads(item['content'])
                    except:
                        pass
                result.append(item)
            return result
            
        except Exception as e:
            log_database_error(
                f"Error getting reports: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_reports_count(
        self,
        report_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """
        دریافت تعداد گزارش‌ها

        پارامترها:
            report_type: نوع گزارش (اختیاری)
            status: وضعیت گزارش (اختیاری)

        بازگشت: تعداد گزارش‌ها
        """
        try:
            conditions = []
            params = []
            
            if report_type:
                conditions.append("report_type = ?")
                params.append(report_type)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            cursor = self._connection.cursor()
            cursor.execute(
                f"SELECT COUNT(*) as count FROM reports WHERE {where_clause}",
                params
            )
            row = cursor.fetchone()
            cursor.close()
            return row['count'] if row else 0
            
        except Exception as e:
            log_database_error(
                f"Error getting reports count: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def update_report_status(self, report_id: int, status: str) -> bool:
        """
        به‌روزرسانی وضعیت یک گزارش

        پارامترها:
            report_id: شناسه گزارش
            status: وضعیت جدید (pending, completed, failed)

        بازگشت: True در صورت موفقیت
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                UPDATE reports
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, report_id))
            self._connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
            
        except Exception as e:
            log_database_error(
                f"Error updating report status {report_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_report_content(self, report_id: int, content: Dict[str, Any]) -> bool:
        """
        به‌روزرسانی محتوای یک گزارش

        پارامترها:
            report_id: شناسه گزارش
            content: محتوای جدید

        بازگشت: True در صورت موفقیت
        """
        try:
            content_str = json.dumps(content, ensure_ascii=False, default=str)
            
            cursor = self._connection.cursor()
            cursor.execute("""
                UPDATE reports
                SET content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (content_str, report_id))
            self._connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
            
        except Exception as e:
            log_database_error(
                f"Error updating report content {report_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete_report(self, report_id: int) -> bool:
        """
        حذف یک گزارش

        پارامترها:
            report_id: شناسه گزارش

        بازگشت: True در صورت موفقیت
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            self._connection.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected > 0
            
        except Exception as e:
            log_database_error(
                f"Error deleting report {report_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def cleanup_old_reports(self, days: int = 30) -> int:
        """
        پاکسازی گزارش‌های قدیمی

        پارامترها:
            days: تعداد روزهای نگهداری

        بازگشت: تعداد گزارش‌های حذف‌شده
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute("""
                DELETE FROM reports
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            deleted_count = cursor.rowcount
            self._connection.commit()
            cursor.close()
            return deleted_count
            
        except Exception as e:
            log_database_error(
                f"Error cleaning up old reports: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # متدهای آماری
    # ============================================================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار خلاصه برای داشبورد مانیتورینگ

        بازگشت: دیکشنری شامل آمار
        """
        try:
            metrics_count = self.get_metrics_count()
            active_alerts_count = self.get_alerts_count(is_resolved=False)
            resolved_alerts_count = self.get_alerts_count(is_resolved=True)
            reports_count = self.get_reports_count()
            latest_metric = self.get_latest_metric('cpu_usage')
            
            return {
                'metrics_count': metrics_count,
                'active_alerts': active_alerts_count,
                'resolved_alerts': resolved_alerts_count,
                'total_alerts': active_alerts_count + resolved_alerts_count,
                'reports_count': reports_count,
                'latest_metric': latest_metric,
            }
            
        except Exception as e:
            log_database_error(
                f"Error getting dashboard stats: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'metrics_count': 0,
                'active_alerts': 0,
                'resolved_alerts': 0,
                'total_alerts': 0,
                'reports_count': 0,
                'latest_metric': None,
            }


__all__ = [
    'MonitoringRepository',
]