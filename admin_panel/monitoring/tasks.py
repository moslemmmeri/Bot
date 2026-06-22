# admin_panel/monitoring/tasks.py
# تسک‌های زمان‌بندی‌شده مربوط به مانیتورینگ
# شامل: بررسی دوره‌ای، تولید گزارش روزانه، بررسی هشدارها، پاکسازی متریک‌ها

import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from logger_config import logger, ContextLogger
from config import config
from core import send_message, OWNER_ID
from utils.error_handler import log_critical_error, log_general_error, log_database_error


# ============================================================
# تسک بررسی دوره‌ای مانیتورینگ
# ============================================================

async def run_monitoring_check() -> Dict[str, Any]:
    """
    اجرای بررسی دوره‌ای مانیتورینگ:
    - جمع‌آوری متریک‌های جدید
    - بررسی و ارسال هشدارها

    بازگشت: دیکشنری شامل نتایج بررسی
    """
    ctx_logger = ContextLogger("monitoring.tasks.check")
    start_time = datetime.now()

    try:
        logger.info("🔄 Running monitoring check task...")
        results = {
            'started_at': start_time.isoformat(),
            'metrics_collected': 0,
            'alerts_found': 0,
            'alerts_sent': 0,
            'errors': []
        }

        # ========== ۱. جمع‌آوری متریک‌ها ==========
        try:
            from .metrics import collect_metrics
            metrics_result = await collect_metrics()
            
            if 'error' in metrics_result:
                results['errors'].append(f"Metrics collection error: {metrics_result['error']}")
            else:
                results['metrics_collected'] = metrics_result.get('saved_count', 0)
                logger.info(f"📊 Metrics collected: {results['metrics_collected']} items")
                
        except Exception as e:
            error_msg = f"Error in collect_metrics: {str(e)}"
            results['errors'].append(error_msg)
            log_general_error(
                error_msg,
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        # ========== ۲. بررسی هشدارها ==========
        try:
            from .alerts import check_alerts
            alert_results = await check_alerts()
            
            results['alerts_found'] = alert_results.get('alerts_found', 0)
            results['alerts_sent'] = alert_results.get('alerts_sent', 0)
            
            if results['alerts_found'] > 0:
                logger.info(f"🚨 {results['alerts_found']} alerts found, {results['alerts_sent']} sent")
                
        except Exception as e:
            error_msg = f"Error in check_alerts: {str(e)}"
            results['errors'].append(error_msg)
            log_general_error(
                error_msg,
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        # ========== ۳. به‌روزرسانی وضعیت Scheduler ==========
        try:
            # ذخیره زمان آخرین بررسی در کش یا دیتابیس (اختیاری)
            # در اینجا فقط لاگ می‌کنیم
            pass
        except Exception as e:
            error_msg = f"Error updating scheduler status: {str(e)}"
            results['errors'].append(error_msg)
            log_general_error(
                error_msg,
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        elapsed = (datetime.now() - start_time).total_seconds()
        results['elapsed_seconds'] = round(elapsed, 2)

        logger.info(
            f"✅ Monitoring check completed: "
            f"metrics={results['metrics_collected']}, "
            f"alerts={results['alerts_found']}, "
            f"errors={len(results['errors'])}, "
            f"time={results['elapsed_seconds']}s"
        )

        return results

    except Exception as e:
        log_critical_error(
            f"Error in run_monitoring_check: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'started_at': start_time.isoformat(),
            'metrics_collected': 0,
            'alerts_found': 0,
            'alerts_sent': 0,
            'errors': [str(e)],
            'elapsed_seconds': 0
        }


# ============================================================
# تسک تولید گزارش روزانه
# ============================================================

async def run_daily_report() -> Dict[str, Any]:
    """
    تولید و ارسال گزارش روزانه به OWNER

    بازگشت: دیکشنری شامل نتایج تولید گزارش
    """
    ctx_logger = ContextLogger("monitoring.tasks.daily_report")
    start_time = datetime.now()

    try:
        logger.info("🔄 Running daily report task...")
        results = {
            'started_at': start_time.isoformat(),
            'success': False,
            'report_id': None,
            'error': None
        }

        # ========== تولید گزارش ==========
        try:
            from .reports import generate_daily_report
            report_result = await generate_daily_report()
            
            if report_result.get('success'):
                results['success'] = True
                results['report_id'] = report_result.get('report_id')
                logger.info(f"✅ Daily report generated: {results['report_id']}")
            else:
                results['error'] = report_result.get('error', 'Unknown error')
                logger.warning(f"⚠️ Daily report generation failed: {results['error']}")
                
        except Exception as e:
            error_msg = f"Error in generate_daily_report: {str(e)}"
            results['error'] = error_msg
            log_general_error(
                error_msg,
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        # ========== ارسال گزارش به OWNER ==========
        if results['success']:
            try:
                from .reports import send_report_to_admin
                sent = await send_report_to_admin(results['report_id'])
                
                if sent:
                    logger.info(f"📨 Daily report sent to OWNER")
                else:
                    logger.warning(f"⚠️ Failed to send daily report to OWNER")
                    
            except Exception as e:
                error_msg = f"Error sending report to OWNER: {str(e)}"
                results['error'] = error_msg
                log_general_error(
                    error_msg,
                    traceback=traceback.format_exc(),
                    context_logger=ctx_logger
                )

        elapsed = (datetime.now() - start_time).total_seconds()
        results['elapsed_seconds'] = round(elapsed, 2)

        logger.info(
            f"✅ Daily report task completed: "
            f"success={results['success']}, "
            f"report_id={results['report_id']}, "
            f"time={results['elapsed_seconds']}s"
        )

        return results

    except Exception as e:
        log_critical_error(
            f"Error in run_daily_report: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'started_at': start_time.isoformat(),
            'success': False,
            'report_id': None,
            'error': str(e),
            'elapsed_seconds': 0
        }


# ============================================================
# تسک بررسی و ارسال هشدارها
# ============================================================

async def run_alert_check() -> Dict[str, Any]:
    """
    بررسی و ارسال هشدارهای جدید (اجرای مستقل از بررسی دوره‌ای)

    بازگشت: دیکشنری شامل نتایج بررسی هشدارها
    """
    ctx_logger = ContextLogger("monitoring.tasks.alert_check")
    start_time = datetime.now()

    try:
        logger.info("🔄 Running alert check task...")
        results = {
            'started_at': start_time.isoformat(),
            'alerts_found': 0,
            'alerts_sent': 0,
            'errors': []
        }

        try:
            from .alerts import check_alerts
            alert_results = await check_alerts()
            
            results['alerts_found'] = alert_results.get('alerts_found', 0)
            results['alerts_sent'] = alert_results.get('alerts_sent', 0)
            
            logger.info(f"🚨 Alert check: {results['alerts_found']} alerts found, {results['alerts_sent']} sent")
            
        except Exception as e:
            error_msg = f"Error in check_alerts: {str(e)}"
            results['errors'].append(error_msg)
            log_general_error(
                error_msg,
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        elapsed = (datetime.now() - start_time).total_seconds()
        results['elapsed_seconds'] = round(elapsed, 2)

        logger.info(
            f"✅ Alert check completed: "
            f"alerts={results['alerts_found']}, "
            f"sent={results['alerts_sent']}, "
            f"time={results['elapsed_seconds']}s"
        )

        return results

    except Exception as e:
        log_critical_error(
            f"Error in run_alert_check: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'started_at': start_time.isoformat(),
            'alerts_found': 0,
            'alerts_sent': 0,
            'errors': [str(e)],
            'elapsed_seconds': 0
        }


# ============================================================
# تسک پاکسازی متریک‌ها و داده‌های مانیتورینگ
# ============================================================

async def run_metrics_cleanup() -> Dict[str, Any]:
    """
    پاکسازی متریک‌ها، هشدارها و گزارش‌های قدیمی

    بازگشت: دیکشنری شامل نتایج پاکسازی
    """
    ctx_logger = ContextLogger("monitoring.tasks.metrics_cleanup")
    start_time = datetime.now()

    try:
        logger.info("🔄 Running metrics cleanup task...")
        results = {
            'started_at': start_time.isoformat(),
            'deleted_metrics': 0,
            'deleted_alerts': 0,
            'deleted_reports': 0,
            'errors': []
        }

        try:
            from repositories.monitoring_repository import MonitoringRepository
            from database import get_db_connection
            
            with get_db_connection() as conn:
                repo = MonitoringRepository(conn)
                
                # پاکسازی متریک‌های قدیمی
                deleted_metrics = repo.cleanup_old_metrics(days=config.METRICS_RETENTION_DAYS)
                results['deleted_metrics'] = deleted_metrics
                logger.info(f"🗑️ Deleted {deleted_metrics} old metrics")
                
                # پاکسازی هشدارهای حل‌شده
                deleted_alerts = repo.cleanup_old_alerts(days=config.ALERTS_RETENTION_DAYS)
                results['deleted_alerts'] = deleted_alerts
                logger.info(f"🗑️ Deleted {deleted_alerts} old resolved alerts")
                
                # پاکسازی گزارش‌های قدیمی
                deleted_reports = repo.cleanup_old_reports(days=config.REPORTS_RETENTION_DAYS)
                results['deleted_reports'] = deleted_reports
                logger.info(f"🗑️ Deleted {deleted_reports} old reports")
                
        except Exception as e:
            error_msg = f"Error in cleanup: {str(e)}"
            results['errors'].append(error_msg)
            log_database_error(
                error_msg,
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        # ========== ارسال گزارش پاکسازی به OWNER ==========
        if results['deleted_metrics'] > 0 or results['deleted_alerts'] > 0 or results['deleted_reports'] > 0:
            try:
                msg = (
                    f"🧹 **گزارش پاکسازی مانیتورینگ**\n\n"
                    f"⏱️ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🗑️ متریک‌های حذف‌شده: {results['deleted_metrics']}\n"
                    f"🗑️ هشدارهای حذف‌شده: {results['deleted_alerts']}\n"
                    f"🗑️ گزارش‌های حذف‌شده: {results['deleted_reports']}\n"
                )
                await send_message(OWNER_ID, msg)
                logger.info("📨 Cleanup report sent to OWNER")
            except Exception as e:
                log_general_error(
                    f"Error sending cleanup report: {str(e)}",
                    traceback=traceback.format_exc(),
                    context_logger=ctx_logger
                )

        elapsed = (datetime.now() - start_time).total_seconds()
        results['elapsed_seconds'] = round(elapsed, 2)

        logger.info(
            f"✅ Metrics cleanup completed: "
            f"metrics={results['deleted_metrics']}, "
            f"alerts={results['deleted_alerts']}, "
            f"reports={results['deleted_reports']}, "
            f"time={results['elapsed_seconds']}s"
        )

        return results

    except Exception as e:
        log_critical_error(
            f"Error in run_metrics_cleanup: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'started_at': start_time.isoformat(),
            'deleted_metrics': 0,
            'deleted_alerts': 0,
            'deleted_reports': 0,
            'errors': [str(e)],
            'elapsed_seconds': 0
        }


# ============================================================
# تسک تولید گزارش هفتگی
# ============================================================

async def run_weekly_report() -> Dict[str, Any]:
    """
    تولید و ارسال گزارش هفتگی به OWNER

    بازگشت: دیکشنری شامل نتایج تولید گزارش
    """
    ctx_logger = ContextLogger("monitoring.tasks.weekly_report")
    start_time = datetime.now()

    try:
        logger.info("🔄 Running weekly report task...")
        results = {
            'started_at': start_time.isoformat(),
            'success': False,
            'report_id': None,
            'error': None
        }

        try:
            from .reports import generate_weekly_report
            report_result = await generate_weekly_report()
            
            if report_result.get('success'):
                results['success'] = True
                results['report_id'] = report_result.get('report_id')
                logger.info(f"✅ Weekly report generated: {results['report_id']}")
            else:
                results['error'] = report_result.get('error', 'Unknown error')
                logger.warning(f"⚠️ Weekly report generation failed: {results['error']}")
                
        except Exception as e:
            error_msg = f"Error in generate_weekly_report: {str(e)}"
            results['error'] = error_msg
            log_general_error(
                error_msg,
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        # ارسال به OWNER در صورت موفقیت
        if results['success']:
            try:
                from .reports import send_report_to_admin
                await send_report_to_admin(results['report_id'])
            except Exception as e:
                log_general_error(
                    f"Error sending weekly report: {str(e)}",
                    traceback=traceback.format_exc(),
                    context_logger=ctx_logger
                )

        elapsed = (datetime.now() - start_time).total_seconds()
        results['elapsed_seconds'] = round(elapsed, 2)

        return results

    except Exception as e:
        log_critical_error(
            f"Error in run_weekly_report: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'started_at': start_time.isoformat(),
            'success': False,
            'report_id': None,
            'error': str(e),
            'elapsed_seconds': 0
        }


# ============================================================
# تسک تولید گزارش ماهانه
# ============================================================

async def run_monthly_report() -> Dict[str, Any]:
    """
    تولید و ارسال گزارش ماهانه به OWNER

    بازگشت: دیکشنری شامل نتایج تولید گزارش
    """
    ctx_logger = ContextLogger("monitoring.tasks.monthly_report")
    start_time = datetime.now()

    try:
        logger.info("🔄 Running monthly report task...")
        results = {
            'started_at': start_time.isoformat(),
            'success': False,
            'report_id': None,
            'error': None
        }

        try:
            from .reports import generate_monthly_report
            report_result = await generate_monthly_report()
            
            if report_result.get('success'):
                results['success'] = True
                results['report_id'] = report_result.get('report_id')
                logger.info(f"✅ Monthly report generated: {results['report_id']}")
            else:
                results['error'] = report_result.get('error', 'Unknown error')
                logger.warning(f"⚠️ Monthly report generation failed: {results['error']}")
                
        except Exception as e:
            error_msg = f"Error in generate_monthly_report: {str(e)}"
            results['error'] = error_msg
            log_general_error(
                error_msg,
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        # ارسال به OWNER در صورت موفقیت
        if results['success']:
            try:
                from .reports import send_report_to_admin
                await send_report_to_admin(results['report_id'])
            except Exception as e:
                log_general_error(
                    f"Error sending monthly report: {str(e)}",
                    traceback=traceback.format_exc(),
                    context_logger=ctx_logger
                )

        elapsed = (datetime.now() - start_time).total_seconds()
        results['elapsed_seconds'] = round(elapsed, 2)

        return results

    except Exception as e:
        log_critical_error(
            f"Error in run_monthly_report: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'started_at': start_time.isoformat(),
            'success': False,
            'report_id': None,
            'error': str(e),
            'elapsed_seconds': 0
        }


# ============================================================
# راه‌اندازی تسک‌های مانیتورینگ
# ============================================================

def setup_monitoring_tasks(scheduler):
    """
    ثبت تسک‌های مانیتورینگ در Scheduler

    پارامترها:
        scheduler: آبجکت SchedulerManager
    """
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger

    if not config.MONITORING_ENABLED:
        logger.info("ℹ️ Monitoring is disabled, skipping monitoring tasks")
        return

    logger.info("🔧 Setting up monitoring tasks...")

    # ========== ۱. بررسی دوره‌ای مانیتورینگ ==========
    try:
        scheduler.add_job(
            run_monitoring_check,
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

    # ========== ۲. پاکسازی متریک‌ها ==========
    try:
        scheduler.add_job(
            run_metrics_cleanup,
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

    # ========== ۳. گزارش روزانه ==========
    try:
        report_schedule = config.MONITORING_REPORT_SCHEDULE
        scheduler.add_job(
            run_daily_report,
            CronTrigger.from_crontab(report_schedule),
            job_id="monitoring_daily_report",
            replace_existing=True
        )
        logger.info(f"✅ Daily report job scheduled: {report_schedule}")
    except Exception as e:
        log_critical_error(
            f"Error scheduling daily report job: {str(e)}",
            traceback=traceback.format_exc()
        )

    # ========== ۴. گزارش هفتگی (یکشنبه‌ها ساعت ۱۰ صبح) ==========
    try:
        scheduler.add_job(
            run_weekly_report,
            CronTrigger(day_of_week='sun', hour=10, minute=0),
            job_id="monitoring_weekly_report",
            replace_existing=True
        )
        logger.info("✅ Weekly report job scheduled: Sundays at 10:00 AM")
    except Exception as e:
        log_critical_error(
            f"Error scheduling weekly report job: {str(e)}",
            traceback=traceback.format_exc()
        )

    # ========== ۵. گزارش ماهانه (اول هر ماه ساعت ۱۰ صبح) ==========
    try:
        scheduler.add_job(
            run_monthly_report,
            CronTrigger(day=1, hour=10, minute=0),
            job_id="monitoring_monthly_report",
            replace_existing=True
        )
        logger.info("✅ Monthly report job scheduled: 1st of each month at 10:00 AM")
    except Exception as e:
        log_critical_error(
            f"Error scheduling monthly report job: {str(e)}",
            traceback=traceback.format_exc()
        )

    logger.info("✅ All monitoring tasks registered")


# ============================================================
# وضعیت تسک‌ها
# ============================================================

def get_monitoring_tasks_status() -> Dict[str, Any]:
    """
    دریافت وضعیت تسک‌های مانیتورینگ

    بازگشت: دیکشنری شامل وضعیت تسک‌ها
    """
    try:
        from scheduler import get_scheduler_status
        status = get_scheduler_status()
        
        monitoring_jobs = [
            'monitoring_check',
            'monitoring_cleanup',
            'monitoring_daily_report',
            'monitoring_weekly_report',
            'monitoring_monthly_report'
        ]
        
        jobs = []
        for job in status.get('jobs', []):
            if job.get('id') in monitoring_jobs:
                jobs.append(job)
        
        return {
            'total_monitoring_jobs': len(jobs),
            'jobs': jobs,
            'is_running': status.get('is_running', False)
        }
        
    except Exception as e:
        log_general_error(
            f"Error getting monitoring tasks status: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {
            'total_monitoring_jobs': 0,
            'jobs': [],
            'is_running': False,
            'error': str(e)
        }


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'run_monitoring_check',
    'run_daily_report',
    'run_weekly_report',
    'run_monthly_report',
    'run_alert_check',
    'run_metrics_cleanup',
    'setup_monitoring_tasks',
    'get_monitoring_tasks_status',
]