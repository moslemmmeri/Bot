# tasks/cleanup_task.py
# تسک پاکسازی خودکار لاگ‌ها، خطاها و فایل‌های قدیمی
# اصلاح شده با مدیریت خطا و لاگ‌گیری کامل در دیتابیس

import os
import asyncio
from datetime import datetime, timedelta
from logger_config import logger
from config import config
from database import get_db_connection
from database.db_logs import delete_error_logs
from utils.error_handler import (
    log_critical_error,
    log_general_error,
    log_database_error,
    log_api_error
)


async def run_cleanup_task():
    """
    اجرای تسک پاکسازی خودکار
    این تابع توسط Scheduler در زمان‌های مشخص فراخوانی می‌شود
    """
    try:
        logger.info("🔄 Starting automatic cleanup task...")
        start_time = datetime.now()
        
        results = {
            'deleted_errors': 0,
            'deleted_logs': 0,
            'deleted_charts': 0,
            'deleted_excel': 0,
            'deleted_temp': 0,
            'errors': []
        }
        
        # ۱. پاکسازی خطاهای قدیمی
        try:
            error_days = config.ERROR_RETENTION_DAYS
            deleted = delete_error_logs(error_days)
            results['deleted_errors'] = deleted
            logger.info(f"🗑️ Deleted {deleted} error logs older than {error_days} days")
        except Exception as e:
            log_database_error(
                f"Error cleaning error logs: {str(e)}",
                traceback=str(e)
            )
            results['errors'].append(f"Error logs: {str(e)}")
        
        # ۲. پاکسازی لاگ‌های سفارشات قدیمی
        try:
            log_days = config.LOG_RETENTION_DAYS
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM order_logs WHERE created_at < datetime('now', '-' || ? || ' days')",
                    (log_days,)
                )
                deleted = cursor.rowcount
                conn.commit()
            results['deleted_logs'] = deleted
            logger.info(f"🗑️ Deleted {deleted} order logs older than {log_days} days")
        except Exception as e:
            log_database_error(
                f"Error cleaning order logs: {str(e)}",
                traceback=str(e)
            )
            results['errors'].append(f"Order logs: {str(e)}")
        
        # ۳. پاکسازی نمودارهای قدیمی
        try:
            from admin_panel.charts import clean_old_charts
            clean_old_charts(days=7)
            results['deleted_charts'] = _count_chart_files()
            logger.info("🗑️ Old charts cleaned")
        except Exception as e:
            log_general_error(
                f"Error cleaning charts: {str(e)}",
                traceback=str(e)
            )
            results['errors'].append(f"Charts: {str(e)}")
        
        # ۴. پاکسازی فایل‌های Excel قدیمی
        try:
            from admin_panel.excel_export import ExcelExporter
            exporter = ExcelExporter()
            deleted = exporter.cleanup_old_exports(days=7)
            results['deleted_excel'] = deleted
            logger.info(f"🗑️ Deleted {deleted} old Excel files")
        except Exception as e:
            log_general_error(
                f"Error cleaning Excel files: {str(e)}",
                traceback=str(e)
            )
            results['errors'].append(f"Excel files: {str(e)}")
        
        # ۵. پاکسازی فایل‌های موقت (temp files)
        try:
            deleted_temp = _cleanup_temp_files()
            results['deleted_temp'] = deleted_temp
            if deleted_temp > 0:
                logger.info(f"🗑️ Deleted {deleted_temp} temporary files")
        except Exception as e:
            log_general_error(
                f"Error cleaning temp files: {str(e)}",
                traceback=str(e)
            )
            results['errors'].append(f"Temp files: {str(e)}")
        
        # ۶. بهینه‌سازی دیتابیس (VACUUM) در صورت نیاز
        try:
            if _should_vacuum():
                _vacuum_database()
                logger.info("🗑️ Database vacuum completed")
        except Exception as e:
            log_database_error(
                f"Error vacuuming database: {str(e)}",
                traceback=str(e)
            )
            results['errors'].append(f"Database vacuum: {str(e)}")
        
        # محاسبه زمان اجرا
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # ارسال گزارش به OWNER
        await _notify_owner(results, elapsed)
        
        logger.info(
            f"✅ Cleanup task completed\n"
            f"   🗑️ Errors: {results['deleted_errors']}\n"
            f"   🗑️ Logs: {results['deleted_logs']}\n"
            f"   🗑️ Charts: {results['deleted_charts']}\n"
            f"   🗑️ Excel: {results['deleted_excel']}\n"
            f"   🗑️ Temp: {results['deleted_temp']}\n"
            f"   ⏱️  Time: {elapsed:.2f} seconds"
        )
        
        return True
        
    except Exception as e:
        log_critical_error(
            f"Error in cleanup_task: {str(e)}",
            traceback=str(e)
        )
        return False


def _count_chart_files() -> int:
    """تعداد فایل‌های نمودار موجود"""
    try:
        from admin_panel.charts import CHARTS_DIR
        if os.path.exists(CHARTS_DIR):
            return len([f for f in os.listdir(CHARTS_DIR) if f.endswith('.png')])
        return 0
    except Exception as e:
        log_general_error(
            f"Error counting chart files: {str(e)}",
            traceback=str(e)
        )
        return 0


def _cleanup_temp_files() -> int:
    """پاکسازی فایل‌های موقت"""
    deleted = 0
    temp_dirs = ['/tmp', '/var/tmp']
    patterns = ['bot_', 'chart_', 'backup_', 'export_']
    
    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            continue
        
        try:
            for filename in os.listdir(temp_dir):
                for pattern in patterns:
                    if filename.startswith(pattern) and any(filename.endswith(ext) for ext in ['.tmp', '.temp', '.log']):
                        filepath = os.path.join(temp_dir, filename)
                        try:
                            # بررسی سن فایل (بیش از ۱ روز)
                            if os.path.getmtime(filepath) < (datetime.now() - timedelta(days=1)).timestamp():
                                os.remove(filepath)
                                deleted += 1
                        except Exception as e:
                            log_general_error(
                                f"Error deleting temp file {filepath}: {str(e)}",
                                traceback=str(e)
                            )
                        break
        except Exception as e:
            log_general_error(
                f"Error cleaning temp dir {temp_dir}: {str(e)}",
                traceback=str(e)
            )
    
    return deleted


def _should_vacuum() -> bool:
    """
    بررسی نیاز به بهینه‌سازی دیتابیس
    اگر دیتابیس بزرگتر از ۱۰۰ مگابایت باشد، VACUUM انجام می‌شود
    """
    try:
        from config import config
        db_path = config.SQLITE_DB_PATH
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            return size > 100 * 1024 * 1024  # 100 MB
        return False
    except Exception as e:
        log_general_error(
            f"Error checking vacuum need: {str(e)}",
            traceback=str(e)
        )
        return False


def _vacuum_database():
    """اجرای VACUUM روی دیتابیس برای بهینه‌سازی"""
    try:
        from config import config
        import sqlite3
        
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        conn.execute("VACUUM")
        conn.close()
        logger.info("Database vacuum completed")
    except Exception as e:
        log_database_error(
            f"Error vacuuming database: {str(e)}",
            traceback=str(e)
        )
        raise


async def _notify_owner(results: dict, elapsed: float):
    """
    ارسال گزارش پاکسازی به OWNER
    
    پارامترها:
        results: دیکشنری نتایج پاکسازی
        elapsed: زمان اجرا (ثانیه)
    """
    try:
        from core import send_message, OWNER_ID
        
        msg = (
            f"🧹 **گزارش پاکسازی خودکار**\n\n"
            f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"⏱️  زمان اجرا: {elapsed:.2f} ثانیه\n\n"
            f"📊 **نتایج پاکسازی:**\n"
            f"  🗑️ خطاهای قدیمی: {results['deleted_errors']} مورد\n"
            f"  🗑️ لاگ‌های سفارشات: {results['deleted_logs']} مورد\n"
            f"  🗑️ نمودارهای قدیمی: {results['deleted_charts']} مورد\n"
            f"  🗑️ فایل‌های Excel قدیمی: {results['deleted_excel']} مورد\n"
            f"  🗑️ فایل‌های موقت: {results['deleted_temp']} مورد\n"
        )
        
        if results['errors']:
            msg += f"\n⚠️ **خطاها:**\n"
            for error in results['errors']:
                msg += f"  ❌ {error}\n"
        else:
            msg += "\n✅ همه عملیات با موفقیت انجام شد."
        
        await send_message(OWNER_ID, msg)
        
    except Exception as e:
        log_api_error(
            f"Error sending cleanup notification to owner: {str(e)}",
            traceback=str(e),
            user_id=OWNER_ID if 'OWNER_ID' in dir() else None
        )


def get_cleanup_status() -> dict:
    """
    دریافت وضعیت پاکسازی
    
    بازگشت: دیکشنری شامل اطلاعات پاکسازی
    """
    try:
        from admin_panel.charts import CHARTS_DIR
        from admin_panel.excel_export import EXPORT_DIR
        
        # تعداد فایل‌های نمودار
        chart_count = 0
        if os.path.exists(CHARTS_DIR):
            chart_count = len([f for f in os.listdir(CHARTS_DIR) if f.endswith('.png')])
        
        # تعداد فایل‌های Excel
        excel_count = 0
        if os.path.exists(EXPORT_DIR):
            excel_count = len([f for f in os.listdir(EXPORT_DIR) if f.endswith('.xlsx')])
        
        # تعداد خطاهای موجود
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM error_logs")
            error_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM order_logs")
            log_count = cursor.fetchone()['count']
        
        return {
            'error_count': error_count,
            'order_log_count': log_count,
            'chart_files': chart_count,
            'excel_files': excel_count,
            'error_retention_days': config.ERROR_RETENTION_DAYS,
            'log_retention_days': config.LOG_RETENTION_DAYS,
            'chart_retention_days': 7,
            'excel_retention_days': 7,
        }
        
    except Exception as e:
        log_general_error(
            f"Error getting cleanup status: {str(e)}",
            traceback=str(e)
        )
        return {
            'error_count': 0,
            'order_log_count': 0,
            'chart_files': 0,
            'excel_files': 0,
            'error_retention_days': config.ERROR_RETENTION_DAYS,
            'log_retention_days': config.LOG_RETENTION_DAYS,
            'chart_retention_days': 7,
            'excel_retention_days': 7,
            'error': str(e)
        }


__all__ = [
    'run_cleanup_task',
    'get_cleanup_status',
    '_notify_owner',
]