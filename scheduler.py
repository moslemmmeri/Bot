# scheduler.py
# مدیریت تسک‌های زمان‌بندی‌شده با استفاده از APScheduler
# شامل: پشتیبان‌گیری خودکار، یادآوری سفارشات، پاکسازی خطاها، و تسک‌های مانیتورینگ

import asyncio
import os
import traceback
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from logger_config import logger
from config import config
from utils.error_handler import (
    log_critical_error,
    log_general_error,
    log_database_error,
    log_api_error
)


# ============================================================
# تنظیمات
# ============================================================

# پیکربندی Scheduler
jobstores = {
    'default': MemoryJobStore()
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3,
    'misfire_grace_time': 60
}


# ============================================================
# کلاس SchedulerManager
# ============================================================

class SchedulerManager:
    """مدیریت تسک‌های زمان‌بندی‌شده"""
    
    def __init__(self):
        try:
            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults,
                timezone='Asia/Tehran'
            )
            self._is_running = False
            self._jobs = {}
            
            # تنظیم لاگ
            self.scheduler.add_listener(self._scheduler_listener)
        except Exception as e:
            log_critical_error(
                f"Error initializing SchedulerManager: {str(e)}",
                traceback=traceback.format_exc()
            )
            raise
    
    def _scheduler_listener(self, event):
        """شنونده رویدادهای Scheduler"""
        if event.exception:
            log_general_error(
                f"Scheduler event error: {event.exception}",
                traceback=traceback.format_exc() if event.exception else None
            )
        else:
            logger.debug(f"Scheduler event: {event.code} - {event.job_id}")
    
    def start(self):
        """راه‌اندازی Scheduler"""
        try:
            if not self._is_running:
                self.scheduler.start()
                self._is_running = True
                logger.info("✅ Scheduler started successfully")
        except Exception as e:
            log_critical_error(
                f"Error starting scheduler: {str(e)}",
                traceback=traceback.format_exc()
            )
            raise
    
    def shutdown(self, wait=True):
        """خاموش کردن Scheduler"""
        try:
            if self._is_running:
                self.scheduler.shutdown(wait=wait)
                self._is_running = False
                logger.info("Scheduler shut down")
        except Exception as e:
            log_general_error(
                f"Error shutting down scheduler: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    def add_job(self, func, trigger, job_id=None, **kwargs):
        """
        افزودن یک تسک جدید به Scheduler
        
        پارامترها:
            func: تابع async برای اجرا
            trigger: شیء Trigger (CronTrigger یا IntervalTrigger)
            job_id: شناسه یکتا برای تسک
            **kwargs: پارامترهای اضافی
        """
        try:
            if job_id and job_id in self._jobs:
                self.remove_job(job_id)
            
            job = self.scheduler.add_job(
                func,
                trigger,
                id=job_id,
                **kwargs
            )
            
            if job_id:
                self._jobs[job_id] = job
            
            logger.info(f"✅ Job added: {job_id or job.id}")
            return job
            
        except Exception as e:
            log_general_error(
                f"Error adding job {job_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def remove_job(self, job_id):
        """حذف یک تسک از Scheduler"""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self._jobs:
                del self._jobs[job_id]
            logger.info(f"Job removed: {job_id}")
            return True
        except Exception as e:
            log_general_error(
                f"Error removing job {job_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def get_job(self, job_id):
        """دریافت اطلاعات یک تسک"""
        try:
            return self.scheduler.get_job(job_id)
        except Exception as e:
            log_general_error(
                f"Error getting job {job_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_jobs(self):
        """دریافت لیست تمام تسک‌ها"""
        try:
            return self.scheduler.get_jobs()
        except Exception as e:
            log_general_error(
                f"Error getting jobs: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def pause_job(self, job_id):
        """متوقف کردن موقت یک تسک"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job paused: {job_id}")
            return True
        except Exception as e:
            log_general_error(
                f"Error pausing job {job_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def resume_job(self, job_id):
        """ادامه دادن یک تسک متوقف‌شده"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job resumed: {job_id}")
            return True
        except Exception as e:
            log_general_error(
                f"Error resuming job {job_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def is_running(self):
        """بررسی وضعیت Scheduler"""
        return self._is_running


# ============================================================
# آبجکت سراسری
# ============================================================

_scheduler_manager = None


def get_scheduler() -> SchedulerManager:
    """دریافت آبجکت سراسری SchedulerManager"""
    global _scheduler_manager
    if _scheduler_manager is None:
        try:
            _scheduler_manager = SchedulerManager()
        except Exception as e:
            log_critical_error(
                f"Error creating global scheduler: {str(e)}",
                traceback=traceback.format_exc()
            )
            raise
    return _scheduler_manager


# ============================================================
# توابع تسک‌ها (برای اجرا در Scheduler)
# ============================================================

async def backup_task():
    """تسک پشتیبان‌گیری خودکار از دیتابیس"""
    try:
        logger.info("🔄 Running automatic backup task...")
        
        from admin_panel.backup import (
            _ensure_backup_dir,
            _create_backup_file,
            _get_backup_filename,
            _cleanup_old_backups
        )
        from core import send_message, OWNER_ID
        
        start_time = datetime.now()
        backup_dir = _ensure_backup_dir()
        filename = _get_backup_filename("auto_backup")
        backup_path = os.path.join(backup_dir, filename)
        
        if _create_backup_file(backup_path):
            _cleanup_old_backups()
            
            # گزارش موفقیت
            elapsed = (datetime.now() - start_time).total_seconds()
            file_size = os.path.getsize(backup_path) // 1024
            
            msg = (
                f"✅ **پشتیبان‌گیری خودکار انجام شد**\n\n"
                f"📁 فایل: {filename}\n"
                f"📊 حجم: {file_size} KB\n"
                f"⏱️ زمان: {elapsed:.2f} ثانیه\n"
                f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await send_message(OWNER_ID, msg)
            logger.info(f"✅ Auto backup completed: {filename}")
        else:
            log_general_error(
                "❌ Auto backup failed",
                traceback=traceback.format_exc()
            )
            await send_message(OWNER_ID, "🚨 **خطا در پشتیبان‌گیری خودکار**\n\nلطفاً لاگ‌ها را بررسی کنید.")
            
    except Exception as e:
        log_critical_error(
            f"Error in backup_task: {str(e)}",
            traceback=traceback.format_exc()
        )


async def reminder_task():
    """تسک یادآوری سفارشات ناتمام"""
    try:
        logger.info("🔄 Running reminder task...")
        
        from database import get_dynamic_orders, get_user
        from core import send_message
        from datetime import datetime, timedelta
        from config import config
        
        orders = get_dynamic_orders()
        now = datetime.now()
        reminder_hours = config.REMINDER_AFTER_HOURS
        interval_hours = config.REMINDER_INTERVAL_HOURS
        
        # یافتن سفارشات در انتظار که نیاز به یادآوری دارند
        reminded_count = 0
        for order in orders:
            if order.get('status') != 'pending':
                continue
            
            created_at = order.get('created_at')
            if not created_at:
                continue
            
            # بررسی زمان ایجاد
            try:
                if isinstance(created_at, str):
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    created_time = created_at
            except Exception as e:
                log_database_error(
                    f"Error parsing created_at for order {order.get('id')}: {str(e)}",
                    traceback=traceback.format_exc()
                )
                continue
            
            # محاسبه زمان گذشته
            elapsed = now - created_time
            if elapsed.total_seconds() < reminder_hours * 3600:
                continue
            
            # بررسی اینکه آیا یادآوری قبلاً ارسال شده است
            last_reminder = order.get('last_reminder_sent')
            if last_reminder:
                try:
                    last_time = datetime.fromisoformat(last_reminder.replace('Z', '+00:00'))
                    if (now - last_time).total_seconds() < interval_hours * 3600:
                        continue
                except Exception as e:
                    log_database_error(
                        f"Error parsing last_reminder_sent for order {order.get('id')}: {str(e)}",
                        traceback=traceback.format_exc()
                    )
                    continue
            
            # ارسال یادآوری به کاربر
            user_id = order.get('user_id')
            if user_id:
                user = get_user(user_id)
                if user:
                    from admin_panel.common import get_service_name
                    name = user.get('first_name') or user.get('username') or 'کاربر گرامی'
                    service_name = get_service_name(order.get('button_id'))
                    amount = order.get('payment_amount', 0) or 0
                    
                    msg = (
                        f"⏰ **یادآوری سفارش ناتمام**\n\n"
                        f"سلام {name} عزیز،\n"
                        f"شما یک سفارش ثبت کرده‌اید که همچنان در انتظار پرداخت است.\n\n"
                        f"📌 **سرویس:** {service_name}\n"
                        f"💰 **مبلغ:** {amount:,} ریال\n"
                        f"📅 **تاریخ ثبت:** {created_at}\n\n"
                        f"لطفاً هرچه سریع‌تر اقدام به پرداخت کنید.\n"
                        f"در صورت نیاز به راهنمایی، با پشتیبانی تماس بگیرید."
                    )
                    
                    try:
                        from messenger import get_messenger
                        messenger = get_messenger()
                        result = await messenger.send_messages([
                            {'chat_id': user_id, 'text': msg}
                        ])
                        
                        if result and not isinstance(result[0], Exception):
                            # بروزرسانی last_reminder_sent
                            from database import get_db_connection
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE dynamic_orders SET last_reminder_sent = ? WHERE id = ?",
                                    (datetime.now().isoformat(), order.get('id'))
                                )
                                conn.commit()
                            reminded_count += 1
                            logger.info(f"✅ Reminder sent to user {user_id} for order {order.get('id')}")
                    except Exception as e:
                        log_api_error(
                            f"Error sending reminder to user {user_id}: {str(e)}",
                            traceback=traceback.format_exc(),
                            user_id=user_id
                        )
        
        logger.info(f"✅ Reminder task completed: {reminded_count} reminders sent")
        
    except Exception as e:
        log_critical_error(
            f"Error in reminder_task: {str(e)}",
            traceback=traceback.format_exc()
        )


async def cleanup_task():
    """تسک پاکسازی خودکار لاگ‌ها و خطاهای قدیمی"""
    try:
        logger.info("🔄 Running cleanup task...")
        
        from database import get_db_connection
        from database.db_logs import delete_error_logs
        from admin_panel.charts import clean_old_charts
        from admin_panel.excel_export import ExcelExporter
        from core import send_message, OWNER_ID
        
        start_time = datetime.now()
        results = {}
        
        # ۱. پاکسازی خطاهای قدیمی
        try:
            error_days = config.ERROR_RETENTION_DAYS
            deleted_errors = delete_error_logs(error_days)
            results['deleted_errors'] = deleted_errors
            logger.info(f"🗑️ Deleted {deleted_errors} error logs older than {error_days} days")
        except Exception as e:
            log_database_error(
                f"Error cleaning error logs: {str(e)}",
                traceback=traceback.format_exc()
            )
            results['deleted_errors'] = 0
        
        # ۲. پاکسازی لاگ‌های سفارشات قدیمی
        try:
            log_days = config.LOG_RETENTION_DAYS
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM order_logs WHERE created_at < datetime('now', '-' || ? || ' days')",
                    (log_days,)
                )
                deleted_logs = cursor.rowcount
                conn.commit()
            results['deleted_logs'] = deleted_logs
            logger.info(f"🗑️ Deleted {deleted_logs} order logs older than {log_days} days")
        except Exception as e:
            log_database_error(
                f"Error cleaning order logs: {str(e)}",
                traceback=traceback.format_exc()
            )
            results['deleted_logs'] = 0
        
        # ۳. پاکسازی نمودارهای قدیمی
        try:
            clean_old_charts(days=7)
            results['deleted_charts'] = 0  # تابع تعداد حذف شده را برنمی‌گرداند
            logger.info("🗑️ Old charts cleaned")
        except Exception as e:
            log_general_error(
                f"Error cleaning charts: {str(e)}",
                traceback=traceback.format_exc()
            )
            results['deleted_charts'] = 0
        
        # ۴. پاکسازی فایل‌های Excel قدیمی
        try:
            exporter = ExcelExporter()
            deleted_excel = exporter.cleanup_old_exports(days=7)
            results['deleted_excel'] = deleted_excel
            logger.info(f"🗑️ Deleted {deleted_excel} old Excel files")
        except Exception as e:
            log_general_error(
                f"Error cleaning Excel files: {str(e)}",
                traceback=traceback.format_exc()
            )
            results['deleted_excel'] = 0
        
        # ۵. پاکسازی فایل‌های موقت (temp files)
        try:
            deleted_temp = 0
            temp_dirs = ['/tmp', '/var/tmp']
            patterns = ['bot_', 'chart_', 'backup_', 'export_']
            
            for temp_dir in temp_dirs:
                if not os.path.exists(temp_dir):
                    continue
                for filename in os.listdir(temp_dir):
                    for pattern in patterns:
                        if filename.startswith(pattern) and any(filename.endswith(ext) for ext in ['.tmp', '.temp']):
                            filepath = os.path.join(temp_dir, filename)
                            try:
                                if os.path.getmtime(filepath) < (datetime.now() - timedelta(days=1)).timestamp():
                                    os.remove(filepath)
                                    deleted_temp += 1
                            except:
                                pass
                            break
            
            results['deleted_temp'] = deleted_temp
            logger.info(f"🗑️ Deleted {deleted_temp} temporary files")
        except Exception as e:
            log_general_error(
                f"Error cleaning temp files: {str(e)}",
                traceback=traceback.format_exc()
            )
            results['deleted_temp'] = 0
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # ارسال گزارش به OWNER
        msg = (
            f"🧹 **گزارش پاکسازی خودکار**\n\n"
            f"⏱️ زمان اجرا: {elapsed:.2f} ثانیه\n\n"
            f"📊 **نتایج:**\n"
            f"  • خطاهای قدیمی: {results.get('deleted_errors', 0)} مورد\n"
            f"  • لاگ‌های سفارشات: {results.get('deleted_logs', 0)} مورد\n"
            f"  • فایل‌های Excel: {results.get('deleted_excel', 0)} مورد\n"
            f"  • فایل‌های موقت: {results.get('deleted_temp', 0)} مورد\n"
        )
        await send_message(OWNER_ID, msg)
        
        logger.info("✅ Cleanup task completed")
        
    except Exception as e:
        log_critical_error(
            f"Error in cleanup_task: {str(e)}",
            traceback=traceback.format_exc()
        )


# ============================================================
# تسک‌های جدید مانیتورینگ
# ============================================================

async def monitoring_check_task():
    """
    تسک بررسی دوره‌ای مانیتورینگ
    جمع‌آوری متریک‌ها و بررسی هشدارها
    """
    try:
        logger.info("🔄 Running monitoring check task...")
        
        from admin_panel.monitoring.metrics import collect_metrics
        from admin_panel.monitoring.alerts import check_alerts
        
        # جمع‌آوری متریک‌ها
        metrics_result = await collect_metrics()
        logger.info(f"📊 Metrics collected: {metrics_result.get('saved_count', 0)} items")
        
        # بررسی هشدارها
        alert_results = await check_alerts()
        if alert_results.get('alerts_found', 0) > 0:
            logger.info(f"🚨 {alert_results.get('alerts_found')} alerts found")
        
        logger.info("✅ Monitoring check completed")
        
    except Exception as e:
        log_critical_error(
            f"Error in monitoring_check_task: {str(e)}",
            traceback=traceback.format_exc()
        )


async def monitoring_cleanup_task():
    """
    تسک پاکسازی متریک‌ها و هشدارهای قدیمی
    """
    try:
        logger.info("🔄 Running monitoring cleanup task...")
        
        from admin_panel.monitoring.metrics import cleanup_old_metrics
        from repositories.monitoring_repository import MonitoringRepository
        from database import get_db_connection
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            
            # پاکسازی متریک‌های قدیمی
            deleted_metrics = cleanup_old_metrics(days=config.METRICS_RETENTION_DAYS)
            logger.info(f"🗑️ Deleted {deleted_metrics} old metrics")
            
            # پاکسازی هشدارهای حل‌شده
            deleted_alerts = repo.cleanup_old_alerts(days=config.ALERTS_RETENTION_DAYS)
            logger.info(f"🗑️ Deleted {deleted_alerts} old resolved alerts")
            
            # پاکسازی گزارش‌های قدیمی
            deleted_reports = repo.cleanup_old_reports(days=config.REPORTS_RETENTION_DAYS)
            logger.info(f"🗑️ Deleted {deleted_reports} old reports")
        
        logger.info("✅ Monitoring cleanup completed")
        
    except Exception as e:
        log_critical_error(
            f"Error in monitoring_cleanup_task: {str(e)}",
            traceback=traceback.format_exc()
        )


async def monitoring_report_task():
    """
    تسک تولید گزارش روزانه
    """
    try:
        logger.info("🔄 Running daily report task...")
        
        from admin_panel.monitoring.reports import generate_daily_report
        
        # تولید گزارش روزانه
        result = await generate_daily_report()
        
        if result.get('success'):
            logger.info(f"✅ Daily report generated: {result.get('report_id')}")
        else:
            log_general_error(
                f"Failed to generate daily report: {result.get('error', 'Unknown error')}"
            )
        
    except Exception as e:
        log_critical_error(
            f"Error in monitoring_report_task: {str(e)}",
            traceback=traceback.format_exc()
        )


# ============================================================
# راه‌اندازی تسک‌های پیش‌فرض
# ============================================================

def setup_default_jobs():
    """تنظیم و راه‌اندازی تسک‌های پیش‌فرض"""
    scheduler = get_scheduler()
    
    # ۱. پشتیبان‌گیری خودکار (هر روز ساعت ۳ بامداد)
    try:
        cron_backup = CronTrigger.from_crontab(config.BACKUP_SCHEDULE)
        scheduler.add_job(
            backup_task,
            cron_backup,
            job_id="auto_backup",
            replace_existing=True
        )
        logger.info(f"✅ Backup job scheduled: {config.BACKUP_SCHEDULE}")
    except Exception as e:
        log_critical_error(
            f"Error scheduling backup job: {str(e)}",
            traceback=traceback.format_exc()
        )
    
    # ۲. یادآوری سفارشات (هر ۶ ساعت)
    try:
        interval_hours = config.REMINDER_INTERVAL_HOURS
        scheduler.add_job(
            reminder_task,
            IntervalTrigger(hours=interval_hours),
            job_id="auto_reminder",
            replace_existing=True
        )
        logger.info(f"✅ Reminder job scheduled: every {interval_hours} hours")
    except Exception as e:
        log_critical_error(
            f"Error scheduling reminder job: {str(e)}",
            traceback=traceback.format_exc()
        )
    
    # ۳. پاکسازی خودکار (هر روز ساعت ۴ بامداد)
    try:
        scheduler.add_job(
            cleanup_task,
            CronTrigger(hour=4, minute=0),
            job_id="auto_cleanup",
            replace_existing=True
        )
        logger.info("✅ Cleanup job scheduled: daily at 4:00 AM")
    except Exception as e:
        log_critical_error(
            f"Error scheduling cleanup job: {str(e)}",
            traceback=traceback.format_exc()
        )
    
    # ============================================
    # تسک‌های جدید مانیتورینگ
    # ============================================
    
    # ۴. بررسی دوره‌ای مانیتورینگ (هر ۵ دقیقه)
    if config.MONITORING_ENABLED:
        try:
            scheduler.add_job(
                monitoring_check_task,
                IntervalTrigger(seconds=config.MONITORING_CHECK_INTERVAL),
                job_id="monitoring_check",
                replace_existing=True
            )
            logger.info(f"✅ Monitoring check job scheduled: every {config.MONITORING_CHECK_INTERVAL} seconds")
        except Exception as e:
            log_critical_error(
                f"Error scheduling monitoring check job: {str(e)}",
                traceback=traceback.format_exc()
            )
        
        # ۵. پاکسازی متریک‌ها (هر روز ساعت ۲ بامداد)
        try:
            scheduler.add_job(
                monitoring_cleanup_task,
                CronTrigger(hour=2, minute=0),
                job_id="monitoring_cleanup",
                replace_existing=True
            )
            logger.info("✅ Monitoring cleanup job scheduled: daily at 2:00 AM")
        except Exception as e:
            log_critical_error(
                f"Error scheduling monitoring cleanup job: {str(e)}",
                traceback=traceback.format_exc()
            )
        
        # ۶. گزارش روزانه (هر روز ساعت ۹ صبح)
        try:
            cron_report = CronTrigger.from_crontab(config.MONITORING_REPORT_SCHEDULE)
            scheduler.add_job(
                monitoring_report_task,
                cron_report,
                job_id="monitoring_daily_report",
                replace_existing=True
            )
            logger.info(f"✅ Daily report job scheduled: {config.MONITORING_REPORT_SCHEDULE}")
        except Exception as e:
            log_critical_error(
                f"Error scheduling daily report job: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    # ۴. شروع Scheduler
    try:
        scheduler.start()
    except Exception as e:
        log_critical_error(
            f"Error starting scheduler: {str(e)}",
            traceback=traceback.format_exc()
        )


# ============================================================
# توابع کمکی برای مدیریت تسک‌ها از پنل مدیریت
# ============================================================

def get_scheduler_status() -> dict:
    """دریافت وضعیت Scheduler"""
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        return {
            'is_running': scheduler.is_running(),
            'total_jobs': len(jobs),
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name or job.id,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'pending': job.pending
                }
                for job in jobs
            ]
        }
    except Exception as e:
        log_general_error(
            f"Error getting scheduler status: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {
            'is_running': False,
            'total_jobs': 0,
            'jobs': [],
            'error': str(e)
        }


def trigger_job_manually(job_id: str) -> bool:
    """اجرای دستی یک تسک"""
    try:
        scheduler = get_scheduler()
        job = scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now())
            logger.info(f"Manual trigger for job: {job_id}")
            return True
        return False
    except Exception as e:
        log_general_error(
            f"Error triggering job {job_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


def pause_all_jobs() -> int:
    """متوقف کردن همه تسک‌ها"""
    try:
        scheduler = get_scheduler()
        count = 0
        for job in scheduler.get_jobs():
            if scheduler.pause_job(job.id):
                count += 1
        return count
    except Exception as e:
        log_general_error(
            f"Error pausing all jobs: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0


def resume_all_jobs() -> int:
    """ادامه دادن همه تسک‌ها"""
    try:
        scheduler = get_scheduler()
        count = 0
        for job in scheduler.get_jobs():
            if scheduler.resume_job(job.id):
                count += 1
        return count
    except Exception as e:
        log_general_error(
            f"Error resuming all jobs: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0


# ============================================================
# شروع خودکار در هنگام import
# ============================================================

def init_scheduler():
    """مقداردهی اولیه Scheduler"""
    try:
        setup_default_jobs()
        logger.info("✅ Scheduler initialized with default jobs")
    except Exception as e:
        log_critical_error(
            f"Error initializing scheduler: {str(e)}",
            traceback=traceback.format_exc()
        )


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'SchedulerManager',
    'get_scheduler',
    'setup_default_jobs',
    'get_scheduler_status',
    'trigger_job_manually',
    'pause_all_jobs',
    'resume_all_jobs',
    'init_scheduler',
    # توابع تسک‌ها
    'backup_task',
    'reminder_task',
    'cleanup_task',
    # تسک‌های مانیتورینگ
    'monitoring_check_task',
    'monitoring_cleanup_task',
    'monitoring_report_task',
]