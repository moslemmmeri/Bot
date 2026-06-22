# admin_panel/monitoring/reports.py
# مدیریت گزارش‌های دوره‌ای (Daily, Weekly, Monthly, Custom)
# شامل: تولید، مشاهده، حذف، تاریخچه و ارسال به OWNER

import json
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from logger_config import logger, ContextLogger
from core import send_message, OWNER_ID
from database import get_db_connection
from config import config
from utils.error_handler import log_callback_error, log_general_error, log_database_error


# ============================================================
# توابع پایه دیتابیس (با استفاده از ریپازیتوری)
# ============================================================

def save_report_to_db(
    report_type: str,
    title: str,
    content: Dict[str, Any],
    created_by: int,
    status: str = "pending"
) -> Optional[int]:
    """
    ذخیره یک گزارش جدید در دیتابیس

    پارامترها:
        report_type: نوع گزارش (daily, weekly, monthly, custom)
        title: عنوان گزارش
        content: محتوای گزارش (دیکشنری JSON)
        created_by: شناسه کاربر ایجادکننده
        status: وضعیت گزارش (pending, completed, failed)

    بازگشت: شناسه گزارش یا None
    """
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.save_report(report_type, title, content, created_by, status)
    except Exception as e:
        log_database_error(
            f"Error saving report: {str(e)}",
            traceback=traceback.format_exc()
        )
        return None


def get_report_by_id_from_db(report_id: int) -> Optional[Dict[str, Any]]:
    """دریافت یک گزارش بر اساس شناسه"""
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.get_report_by_id(report_id)
    except Exception as e:
        log_database_error(
            f"Error getting report by id {report_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return None


def get_reports_from_db(
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """دریافت لیست گزارش‌ها"""
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.get_reports(report_type, status, limit, offset)
    except Exception as e:
        log_database_error(
            f"Error getting reports: {str(e)}",
            traceback=traceback.format_exc()
        )
        return []


def get_report_history(
    limit: int = 50,
    offset: int = 0,
    report_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    دریافت تاریخچه گزارش‌ها (Alias برای get_reports_from_db)

    پارامترها:
        limit: تعداد نتایج
        offset: موقعیت شروع
        report_type: نوع گزارش (اختیاری)

    بازگشت: لیست گزارش‌ها
    """
    return get_reports_from_db(report_type=report_type, limit=limit, offset=offset)


def update_report_status_in_db(report_id: int, status: str) -> bool:
    """به‌روزرسانی وضعیت یک گزارش"""
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.update_report_status(report_id, status)
    except Exception as e:
        log_database_error(
            f"Error updating report status {report_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


def delete_report_from_db(report_id: int) -> bool:
    """حذف یک گزارش"""
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.delete_report(report_id)
    except Exception as e:
        log_database_error(
            f"Error deleting report {report_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


# ============================================================
# تولید گزارش‌ها
# ============================================================

async def generate_daily_report() -> Dict[str, Any]:
    """
    تولید گزارش روزانه

    بازگشت: دیکشنری شامل نتایج تولید
    """
    ctx_logger = ContextLogger("monitoring.reports.daily")
    
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # جمع‌آوری آمار روزانه
        stats = await _collect_daily_stats()
        
        # تولید عنوان و محتوا
        title = f"گزارش روزانه - {today}"
        content = _build_daily_report_content(stats, now)
        
        # ذخیره گزارش
        report_id = save_report_to_db(
            report_type="daily",
            title=title,
            content=content,
            created_by=OWNER_ID,
            status="completed"
        )
        
        if report_id:
            logger.info(f"✅ Daily report generated: {report_id}")
            return {
                'success': True,
                'report_id': report_id,
                'title': title,
                'content': content
            }
        else:
            return {
                'success': False,
                'error': 'Failed to save report to database'
            }
            
    except Exception as e:
        log_general_error(
            f"Error generating daily report: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'success': False,
            'error': str(e)
        }


async def generate_weekly_report() -> Dict[str, Any]:
    """
    تولید گزارش هفتگی

    بازگشت: دیکشنری شامل نتایج تولید
    """
    ctx_logger = ContextLogger("monitoring.reports.weekly")
    
    try:
        now = datetime.now()
        week_number = now.isocalendar()[1]
        year = now.year
        week_range = _get_week_range(now)
        
        # جمع‌آوری آمار هفتگی
        stats = await _collect_weekly_stats(week_range)
        
        # تولید عنوان و محتوا
        title = f"گزارش هفتگی - هفته {week_number} ({year})"
        content = _build_weekly_report_content(stats, week_range, now)
        
        # ذخیره گزارش
        report_id = save_report_to_db(
            report_type="weekly",
            title=title,
            content=content,
            created_by=OWNER_ID,
            status="completed"
        )
        
        if report_id:
            logger.info(f"✅ Weekly report generated: {report_id}")
            return {
                'success': True,
                'report_id': report_id,
                'title': title,
                'content': content
            }
        else:
            return {
                'success': False,
                'error': 'Failed to save report to database'
            }
            
    except Exception as e:
        log_general_error(
            f"Error generating weekly report: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'success': False,
            'error': str(e)
        }


async def generate_monthly_report() -> Dict[str, Any]:
    """
    تولید گزارش ماهانه

    بازگشت: دیکشنری شامل نتایج تولید
    """
    ctx_logger = ContextLogger("monitoring.reports.monthly")
    
    try:
        now = datetime.now()
        month = now.month
        year = now.year
        month_name = _get_month_name(month)
        
        # جمع‌آوری آمار ماهانه
        stats = await _collect_monthly_stats(now)
        
        # تولید عنوان و محتوا
        title = f"گزارش ماهانه - {month_name} {year}"
        content = _build_monthly_report_content(stats, now)
        
        # ذخیره گزارش
        report_id = save_report_to_db(
            report_type="monthly",
            title=title,
            content=content,
            created_by=OWNER_ID,
            status="completed"
        )
        
        if report_id:
            logger.info(f"✅ Monthly report generated: {report_id}")
            return {
                'success': True,
                'report_id': report_id,
                'title': title,
                'content': content
            }
        else:
            return {
                'success': False,
                'error': 'Failed to save report to database'
            }
            
    except Exception as e:
        log_general_error(
            f"Error generating monthly report: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'success': False,
            'error': str(e)
        }


async def generate_custom_report(
    title: str,
    date_range: Dict[str, str],
    metrics: List[str]
) -> Dict[str, Any]:
    """
    تولید گزارش سفارشی

    پارامترها:
        title: عنوان گزارش
        date_range: بازه زمانی (start, end)
        metrics: لیست متریک‌های مورد نظر

    بازگشت: دیکشنری شامل نتایج تولید
    """
    ctx_logger = ContextLogger("monitoring.reports.custom")
    
    try:
        # جمع‌آوری آمار سفارشی
        stats = await _collect_custom_stats(date_range, metrics)
        
        # تولید محتوا
        content = _build_custom_report_content(stats, date_range, metrics)
        
        # ذخیره گزارش
        report_id = save_report_to_db(
            report_type="custom",
            title=title,
            content=content,
            created_by=OWNER_ID,
            status="completed"
        )
        
        if report_id:
            logger.info(f"✅ Custom report generated: {report_id}")
            return {
                'success': True,
                'report_id': report_id,
                'title': title,
                'content': content
            }
        else:
            return {
                'success': False,
                'error': 'Failed to save report to database'
            }
            
    except Exception as e:
        log_general_error(
            f"Error generating custom report: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================
# ارسال گزارش به ادمین
# ============================================================

async def send_report_to_admin(report_id: int) -> bool:
    """
    ارسال گزارش به OWNER

    پارامترها:
        report_id: شناسه گزارش

    بازگشت: True در صورت موفقیت
    """
    try:
        report = get_report_by_id_from_db(report_id)
        if not report:
            logger.warning(f"Report {report_id} not found")
            return False
        
        content = report.get('content', {})
        title = report.get('title', 'گزارش')
        report_type = report.get('report_type', 'unknown')
        created_at = report.get('created_at', '')
        
        # ساخت پیام گزارش
        msg = f"📄 **{title}**\n\n"
        msg += f"📌 نوع: {report_type}\n"
        msg += f"🕐 ایجاد: {created_at}\n"
        msg += "─" * 30 + "\n\n"
        
        # خلاصه گزارش
        summary = content.get('summary', {})
        if summary:
            msg += "📊 **خلاصه:**\n"
            for key, value in summary.items():
                if value is not None and value != "":
                    msg += f"  • {key}: {value}\n"
            msg += "\n"
        
        # جزئیات
        details = content.get('details', {})
        if details:
            msg += "📋 **جزئیات:**\n"
            for key, value in details.items():
                if value is not None and value != "":
                    if isinstance(value, dict):
                        msg += f"  • {key}:\n"
                        for sub_key, sub_value in value.items():
                            msg += f"      - {sub_key}: {sub_value}\n"
                    else:
                        msg += f"  • {key}: {value}\n"
        
        # اگر محتوا خیلی طولانی است، کوتاه کن
        if len(msg) > 4000:
            msg = msg[:3900] + "\n\n... (ادامه در دیتابیس)"
        
        await send_message(OWNER_ID, msg)
        logger.info(f"📨 Report {report_id} sent to OWNER")
        return True
        
    except Exception as e:
        log_general_error(
            f"Error sending report {report_id} to admin: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


# ============================================================
# توابع کمکی جمع‌آوری آمار
# ============================================================

async def _collect_daily_stats() -> Dict[str, Any]:
    """جمع‌آوری آمار روزانه"""
    stats = {}
    
    try:
        from database.db_stats import get_dashboard_stats
        from database.db_logs import get_error_stats
        
        # آمار کلی
        dashboard = get_dashboard_stats()
        stats['dashboard'] = dashboard
        
        # آمار خطاها
        errors = get_error_stats()
        stats['errors'] = errors
        
        # کاربران جدید امروز
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM users WHERE DATE(first_seen) = DATE('now')"
            )
            row = cursor.fetchone()
            stats['new_users_today'] = row['count'] if row else 0
            cursor.close()
        
        # سفارشات امروز
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count, COALESCE(SUM(payment_amount), 0) as total FROM dynamic_orders WHERE DATE(created_at) = DATE('now')"
            )
            row = cursor.fetchone()
            stats['orders_today'] = {
                'count': row['count'] if row else 0,
                'total': row['total'] if row else 0
            }
            cursor.close()
        
    except Exception as e:
        log_general_error(
            f"Error collecting daily stats: {str(e)}",
            traceback=traceback.format_exc()
        )
    
    return stats


async def _collect_weekly_stats(week_range: Dict[str, str]) -> Dict[str, Any]:
    """جمع‌آوری آمار هفتگی"""
    stats = {}
    
    try:
        start_date = week_range.get('start')
        end_date = week_range.get('end')
        
        from database.db_stats import get_dashboard_stats
        from database.db_logs import get_error_stats
        
        # آمار کلی
        dashboard = get_dashboard_stats()
        stats['dashboard'] = dashboard
        
        # آمار خطاها
        errors = get_error_stats()
        stats['errors'] = errors
        
        # کاربران جدید این هفته
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM users WHERE DATE(first_seen) BETWEEN ? AND ?",
                (start_date, end_date)
            )
            row = cursor.fetchone()
            stats['new_users_week'] = row['count'] if row else 0
            cursor.close()
        
        # سفارشات این هفته
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count, COALESCE(SUM(payment_amount), 0) as total FROM dynamic_orders WHERE DATE(created_at) BETWEEN ? AND ?",
                (start_date, end_date)
            )
            row = cursor.fetchone()
            stats['orders_week'] = {
                'count': row['count'] if row else 0,
                'total': row['total'] if row else 0
            }
            cursor.close()
        
        # آمار روزانه (برای نمودار)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count, COALESCE(SUM(payment_amount), 0) as total
                FROM dynamic_orders
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at)
            """, (start_date, end_date))
            rows = cursor.fetchall()
            stats['daily_breakdown'] = [dict(row) for row in rows]
            cursor.close()
        
    except Exception as e:
        log_general_error(
            f"Error collecting weekly stats: {str(e)}",
            traceback=traceback.format_exc()
        )
    
    return stats


async def _collect_monthly_stats(now: datetime) -> Dict[str, Any]:
    """جمع‌آوری آمار ماهانه"""
    stats = {}
    
    try:
        start_date = now.replace(day=1).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")
        
        from database.db_stats import get_dashboard_stats
        from database.db_logs import get_error_stats
        
        # آمار کلی
        dashboard = get_dashboard_stats()
        stats['dashboard'] = dashboard
        
        # آمار خطاها
        errors = get_error_stats()
        stats['errors'] = errors
        
        # کاربران جدید این ماه
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM users WHERE DATE(first_seen) BETWEEN ? AND ?",
                (start_date, end_date)
            )
            row = cursor.fetchone()
            stats['new_users_month'] = row['count'] if row else 0
            cursor.close()
        
        # سفارشات این ماه
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count, COALESCE(SUM(payment_amount), 0) as total FROM dynamic_orders WHERE DATE(created_at) BETWEEN ? AND ?",
                (start_date, end_date)
            )
            row = cursor.fetchone()
            stats['orders_month'] = {
                'count': row['count'] if row else 0,
                'total': row['total'] if row else 0
            }
            cursor.close()
        
        # آمار هفتگی (برای نمودار)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strftime('%W', created_at) as week, COUNT(*) as count, COALESCE(SUM(payment_amount), 0) as total
                FROM dynamic_orders
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY strftime('%W', created_at)
                ORDER BY week
            """, (start_date, end_date))
            rows = cursor.fetchall()
            stats['weekly_breakdown'] = [dict(row) for row in rows]
            cursor.close()
        
    except Exception as e:
        log_general_error(
            f"Error collecting monthly stats: {str(e)}",
            traceback=traceback.format_exc()
        )
    
    return stats


async def _collect_custom_stats(
    date_range: Dict[str, str],
    metrics: List[str]
) -> Dict[str, Any]:
    """جمع‌آوری آمار سفارشی"""
    stats = {}
    
    try:
        start_date = date_range.get('start')
        end_date = date_range.get('end')
        
        for metric in metrics:
            if metric == 'users':
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM users WHERE DATE(first_seen) BETWEEN ? AND ?",
                        (start_date, end_date)
                    )
                    row = cursor.fetchone()
                    stats['new_users'] = row['count'] if row else 0
                    cursor.close()
            
            elif metric == 'orders':
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) as count, COALESCE(SUM(payment_amount), 0) as total FROM dynamic_orders WHERE DATE(created_at) BETWEEN ? AND ?",
                        (start_date, end_date)
                    )
                    row = cursor.fetchone()
                    stats['orders'] = {
                        'count': row['count'] if row else 0,
                        'total': row['total'] if row else 0
                    }
                    cursor.close()
            
            elif metric == 'errors':
                from database.db_logs import get_error_stats
                stats['errors'] = get_error_stats()
            
            elif metric == 'revenue':
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COALESCE(SUM(payment_amount), 0) as total FROM dynamic_orders WHERE DATE(created_at) BETWEEN ? AND ? AND status IN ('paid', 'completed')",
                        (start_date, end_date)
                    )
                    row = cursor.fetchone()
                    stats['revenue'] = row['total'] if row else 0
                    cursor.close()
        
    except Exception as e:
        log_general_error(
            f"Error collecting custom stats: {str(e)}",
            traceback=traceback.format_exc()
        )
    
    return stats


# ============================================================
# توابع کمکی ساخت محتوای گزارش
# ============================================================

def _build_daily_report_content(stats: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    """ساخت محتوای گزارش روزانه"""
    return {
        'generated_at': now.isoformat(),
        'report_type': 'daily',
        'summary': {
            'کل کاربران': stats.get('dashboard', {}).get('total_users', 0),
            'کاربران جدید امروز': stats.get('new_users_today', 0),
            'سفارشات امروز': stats.get('orders_today', {}).get('count', 0),
            'درآمد امروز': stats.get('orders_today', {}).get('total', 0),
            'خطاهای حل‌نشده': stats.get('errors', {}).get('unresolved', 0),
        },
        'details': {
            'آمار کلی': stats.get('dashboard', {}),
            'خطاها': stats.get('errors', {}),
            'سفارشات امروز': stats.get('orders_today', {}),
        }
    }


def _build_weekly_report_content(
    stats: Dict[str, Any],
    week_range: Dict[str, str],
    now: datetime
) -> Dict[str, Any]:
    """ساخت محتوای گزارش هفتگی"""
    return {
        'generated_at': now.isoformat(),
        'report_type': 'weekly',
        'date_range': week_range,
        'summary': {
            'کل کاربران': stats.get('dashboard', {}).get('total_users', 0),
            'کاربران جدید این هفته': stats.get('new_users_week', 0),
            'سفارشات این هفته': stats.get('orders_week', {}).get('count', 0),
            'درآمد این هفته': stats.get('orders_week', {}).get('total', 0),
            'خطاهای حل‌نشده': stats.get('errors', {}).get('unresolved', 0),
        },
        'details': {
            'آمار کلی': stats.get('dashboard', {}),
            'خطاها': stats.get('errors', {}),
            'سفارشات این هفته': stats.get('orders_week', {}),
            'توزیع روزانه': stats.get('daily_breakdown', []),
        }
    }


def _build_monthly_report_content(stats: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    """ساخت محتوای گزارش ماهانه"""
    return {
        'generated_at': now.isoformat(),
        'report_type': 'monthly',
        'summary': {
            'کل کاربران': stats.get('dashboard', {}).get('total_users', 0),
            'کاربران جدید این ماه': stats.get('new_users_month', 0),
            'سفارشات این ماه': stats.get('orders_month', {}).get('count', 0),
            'درآمد این ماه': stats.get('orders_month', {}).get('total', 0),
            'خطاهای حل‌نشده': stats.get('errors', {}).get('unresolved', 0),
        },
        'details': {
            'آمار کلی': stats.get('dashboard', {}),
            'خطاها': stats.get('errors', {}),
            'سفارشات این ماه': stats.get('orders_month', {}),
            'توزیع هفتگی': stats.get('weekly_breakdown', []),
        }
    }


def _build_custom_report_content(
    stats: Dict[str, Any],
    date_range: Dict[str, str],
    metrics: List[str]
) -> Dict[str, Any]:
    """ساخت محتوای گزارش سفارشی"""
    return {
        'generated_at': datetime.now().isoformat(),
        'report_type': 'custom',
        'date_range': date_range,
        'metrics': metrics,
        'summary': stats,
    }


def _get_week_range(now: datetime) -> Dict[str, str]:
    """دریافت بازه هفته جاری"""
    start = now - timedelta(days=now.weekday())
    end = start + timedelta(days=6)
    return {
        'start': start.strftime("%Y-%m-%d"),
        'end': end.strftime("%Y-%m-%d")
    }


def _get_month_name(month: int) -> str:
    """دریافت نام ماه به فارسی"""
    months = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]
    return months[month - 1] if 1 <= month <= 12 else str(month)


# ============================================================
# هندلرهای پنل مدیریت
# ============================================================

async def handle_reports(chat_id: int, user_id: int) -> bool:
    """
    نمایش صفحه مدیریت گزارش‌ها

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        from keyboards.kb_monitoring import monitoring_reports_keyboard
        
        reports = get_reports_from_db(limit=10)
        has_reports = len(reports) > 0
        
        keyboard = monitoring_reports_keyboard(
            has_reports=has_reports,
            reports_count=len(reports)
        )
        
        msg = f"📄 **مدیریت گزارش‌های دوره‌ای**\n\n"
        
        if reports:
            msg += f"📌 **۱۰ گزارش اخیر:**\n\n"
            for report in reports[:10]:
                report_id = report.get('id')
                report_type = report.get('report_type', 'نامشخص')
                title = report.get('title', 'بدون عنوان')
                status = report.get('status', 'pending')
                created_at = report.get('created_at', '')[:16]
                
                status_icon = "✅" if status == 'completed' else "⏳" if status == 'pending' else "❌"
                type_labels = {
                    'daily': '📅 روزانه',
                    'weekly': '📆 هفتگی',
                    'monthly': '📊 ماهانه',
                    'custom': '📋 سفارشی'
                }
                type_label = type_labels.get(report_type, report_type)
                
                msg += f"  {status_icon} #{report_id} - {type_label} - {title[:30]}\n"
                msg += f"      🕐 {created_at}\n\n"
        else:
            msg += "✅ هیچ گزارشی یافت نشد.\n"
            msg += "برای تولید گزارش جدید، از دکمه‌های زیر استفاده کنید."
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_reports: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش گزارش‌ها.")
        return True


async def handle_report_generate(chat_id: int, user_id: int, report_type: str) -> bool:
    """
    تولید یک گزارش جدید

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        report_type: نوع گزارش (daily, weekly, monthly)

    بازگشت: True در صورت موفقیت
    """
    try:
        await send_message(chat_id, f"🔄 در حال تولید گزارش {report_type}... لطفاً صبر کنید.")
        
        if report_type == 'daily':
            result = await generate_daily_report()
        elif report_type == 'weekly':
            result = await generate_weekly_report()
        elif report_type == 'monthly':
            result = await generate_monthly_report()
        else:
            await send_message(chat_id, f"❌ نوع گزارش نامعتبر: {report_type}")
            return True
        
        if result.get('success'):
            report_id = result.get('report_id')
            msg = f"✅ گزارش با موفقیت تولید شد.\n"
            msg += f"📌 شناسه: #{report_id}\n"
            msg += f"📄 عنوان: {result.get('title')}\n\n"
            msg += f"برای مشاهده گزارش، از لیست گزارش‌ها استفاده کنید."
            
            # ارسال گزارش به OWNER
            await send_report_to_admin(report_id)
            
        else:
            msg = f"❌ خطا در تولید گزارش: {result.get('error', 'خطای ناشناخته')}"
        
        await send_message(chat_id, msg)
        return await handle_reports(chat_id, user_id)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_report_generate: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در تولید گزارش: {str(e)}")
        return True


async def handle_report_view(chat_id: int, user_id: int, report_id: int) -> bool:
    """
    مشاهده یک گزارش

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        report_id: شناسه گزارش

    بازگشت: True در صورت موفقیت
    """
    try:
        report = get_report_by_id_from_db(report_id)
        if not report:
            await send_message(chat_id, f"❌ گزارش #{report_id} یافت نشد.")
            return True
        
        content = report.get('content', {})
        title = report.get('title', 'گزارش')
        report_type = report.get('report_type', 'unknown')
        status = report.get('status', 'pending')
        created_at = report.get('created_at', '')
        
        msg = f"📄 **{title}**\n\n"
        msg += f"📌 نوع: {report_type}\n"
        msg += f"📌 وضعیت: {status}\n"
        msg += f"🕐 ایجاد: {created_at}\n"
        msg += "─" * 30 + "\n\n"
        
        # نمایش خلاصه
        summary = content.get('summary', {})
        if summary:
            msg += "📊 **خلاصه:**\n"
            for key, value in summary.items():
                if value is not None and value != "":
                    msg += f"  • {key}: {value}\n"
            msg += "\n"
        
        # نمایش جزئیات
        details = content.get('details', {})
        if details:
            msg += "📋 **جزئیات:**\n"
            for key, value in details.items():
                if value is not None and value != "":
                    if isinstance(value, dict):
                        msg += f"  • {key}:\n"
                        for sub_key, sub_value in value.items():
                            msg += f"      - {sub_key}: {sub_value}\n"
                    else:
                        msg += f"  • {key}: {value}\n"
        
        # اگر محتوا خیلی طولانی است، کوتاه کن
        if len(msg) > 4000:
            msg = msg[:3900] + "\n\n... (ادامه در دیتابیس)"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "📨 ارسال مجدد به OWNER", "callback_data": f"admin_monitoring_reports_send_{report_id}"}],
                [{"text": "🗑️ حذف گزارش", "callback_data": f"admin_monitoring_reports_delete_{report_id}"}],
                [{"text": "🔙 بازگشت به لیست", "callback_data": "admin_monitoring_reports"}]
            ]
        }
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_report_view: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در مشاهده گزارش.")
        return True


async def handle_report_delete(chat_id: int, user_id: int, report_id: int) -> bool:
    """
    حذف یک گزارش

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        report_id: شناسه گزارش

    بازگشت: True در صورت موفقیت
    """
    try:
        success = delete_report_from_db(report_id)
        
        if success:
            await send_message(chat_id, f"✅ گزارش #{report_id} با موفقیت حذف شد.")
        else:
            await send_message(chat_id, f"❌ خطا در حذف گزارش #{report_id}.")
        
        return await handle_reports(chat_id, user_id)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_report_delete: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف گزارش.")
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # توابع دیتابیس
    'save_report_to_db',
    'get_report_by_id_from_db',
    'get_reports_from_db',
    'get_report_history',
    'update_report_status_in_db',
    'delete_report_from_db',
    
    # توابع تولید گزارش
    'generate_daily_report',
    'generate_weekly_report',
    'generate_monthly_report',
    'generate_custom_report',
    
    # ارسال به ادمین
    'send_report_to_admin',
    
    # هندلرهای پنل
    'handle_reports',
    'handle_report_generate',
    'handle_report_view',
    'handle_report_delete',
]