# admin_panel/monitoring/dashboard.py
# داشبورد مانیتورینگ لحظه‌ای سیستم
# شامل: آمار کاربران، خطاها، وضعیت سرویس‌ها، منابع سیستم و تسک‌های زمان‌بندی‌شده

import os
import time
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from logger_config import logger, ContextLogger
from core import send_message
from database import get_db_connection, get_total_users, get_active_users
from database.db_logs import get_error_stats as db_get_error_stats
from database.db_stats import get_dashboard_stats as db_get_dashboard_stats
from config import config
from utils.error_handler import log_callback_error, log_general_error

# تلاش برای import psutil (در صورت نصب نبودن، منابع سیستم نمایش داده نمی‌شوند)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# ============================================================
# توابع کمکی برای دریافت آمار
# ============================================================

def _get_active_users_since(minutes: int = 5) -> int:
    """
    دریافت تعداد کاربران فعال در N دقیقه اخیر.

    پارامترها:
        minutes: تعداد دقیقه‌های اخیر (پیش‌فرض: ۵ دقیقه)

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
            f"Error in _get_active_users_since({minutes}): {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0


def _get_active_users_last_hour() -> int:
    """دریافت تعداد کاربران فعال در ۱ ساعت اخیر"""
    return _get_active_users_since(60)


def _get_requests_per_minute() -> float:
    """
    محاسبه میانگین درخواست‌ها در دقیقه بر اساس آمار کلیک‌های ۱۰ دقیقه اخیر.

    بازگشت: میانگین درخواست در دقیقه
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM button_stats 
                WHERE created_at >= datetime('now', '-10 minutes')
                """
            )
            row = cursor.fetchone()
            count = row['count'] if row else 0
            return round(count / 10, 2)  # تقسیم بر ۱۰ دقیقه
    except Exception as e:
        log_database_error(
            f"Error in _get_requests_per_minute: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0.0


def _get_api_latency_stats() -> Dict[str, Any]:
    """
    دریافت آمار میانگین زمان پاسخ‌گویی API.
    در حال حاضر، از آمار خطاها برای تخمین استفاده می‌شود.
    در آینده، با ذخیره‌سازی زمان‌های پاسخ در متریک‌ها، دقیق‌تر خواهد شد.

    بازگشت: دیکشنری شامل avg_ms, status
    """
    # در حال حاضر، یک مقدار تخمینی بر اساس تعداد خطاهای اخیر برمی‌گردانیم
    # در آینده می‌توان از متریک‌های ذخیره‌شده استفاده کرد
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # تعداد خطاهای ۵ دقیقه اخیر
            cursor.execute(
                "SELECT COUNT(*) as count FROM error_logs WHERE created_at >= datetime('now', '-5 minutes')"
            )
            row = cursor.fetchone()
            error_count = row['count'] if row else 0

            # تخمین ساده: اگر خطا زیاد باشد، تأخیر بیشتر است
            if error_count > 10:
                latency = 800  # میلی‌ثانیه
                status = "high"
            elif error_count > 3:
                latency = 300
                status = "medium"
            else:
                latency = 100
                status = "good"

            return {
                'avg_ms': latency,
                'status': status,
                'status_text': "🟢 خوب" if status == "good" else "🟡 متوسط" if status == "medium" else "🔴 بالا",
                'error_count_5min': error_count
            }
    except Exception as e:
        log_database_error(
            f"Error in _get_api_latency_stats: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {'avg_ms': 0, 'status': 'unknown', 'status_text': '⚪ نامشخص', 'error_count_5min': 0}


def _get_system_usage() -> Dict[str, Any]:
    """
    دریافت وضعیت مصرف منابع سیستم (CPU, Memory, Disk).

    بازگشت: دیکشنری شامل درصد مصرف
    """
    result = {
        'cpu_percent': 0,
        'memory_percent': 0,
        'disk_percent': 0,
        'available': False
    }

    if not PSUTIL_AVAILABLE:
        return result

    try:
        result['cpu_percent'] = psutil.cpu_percent(interval=0.5)
        result['memory_percent'] = psutil.virtual_memory().percent
        result['disk_percent'] = psutil.disk_usage('/').percent
        result['available'] = True
    except Exception as e:
        log_general_error(
            f"Error in _get_system_usage: {str(e)}",
            traceback=traceback.format_exc()
        )

    return result


def _get_scheduler_status_stats() -> Dict[str, Any]:
    """
    دریافت وضعیت تسک‌های زمان‌بندی‌شده (Scheduler).

    بازگشت: دیکشنری شامل وضعیت تسک‌ها
    """
    try:
        from scheduler import get_scheduler_status
        status = get_scheduler_status()
        return {
            'is_running': status.get('is_running', False),
            'total_jobs': status.get('total_jobs', 0),
            'jobs': status.get('jobs', []),
            'status_text': "🟢 فعال" if status.get('is_running', False) else "🔴 غیرفعال"
        }
    except ImportError:
        return {
            'is_running': False,
            'total_jobs': 0,
            'jobs': [],
            'status_text': "⚪ Scheduler فعال نیست"
        }
    except Exception as e:
        log_general_error(
            f"Error in _get_scheduler_status_stats: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {
            'is_running': False,
            'total_jobs': 0,
            'jobs': [],
            'status_text': "❌ خطا در دریافت وضعیت"
        }


def _get_db_size() -> int:
    """دریافت حجم فایل دیتابیس به مگابایت"""
    try:
        db_path = config.SQLITE_DB_PATH
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            return round(size_bytes / (1024 * 1024), 2)  # تبدیل به مگابایت
        return 0
    except Exception as e:
        log_general_error(
            f"Error in _get_db_size: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0


def _check_db_connection() -> bool:
    """بررسی اتصال به دیتابیس"""
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
            return True
    except Exception:
        return False


def _check_redis_connection() -> bool:
    """بررسی اتصال به Redis"""
    if not config.REDIS_ENABLED:
        return True  # اگر Redis غیرفعال است، وضعیت را OK در نظر می‌گیریم

    try:
        from cache import get_cache_manager
        import asyncio
        cache = get_cache_manager()
        # بررسی اتصال با یک عملیات ساده
        result = asyncio.run(cache.exists('health_check_key'))  # استفاده از asyncio.run() در تابع همزمان
        return True
    except Exception as e:
        log_general_error(
            f"Error in _check_redis_connection: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


# ============================================================
# تابع اصلی دریافت آمار جامع
# ============================================================

async def get_monitoring_stats() -> Dict[str, Any]:
    """
    جمع‌آوری و دریافت تمام آمارهای مورد نیاز برای داشبورد مانیتورینگ.

    بازگشت: دیکشنری جامع شامل تمام آمارها
    """
    ctx_logger = ContextLogger("monitoring.dashboard.get_stats")

    try:
        # آمار دیتابیس (کلی)
        db_stats = db_get_dashboard_stats()

        # آمار خطاها
        error_stats = db_get_error_stats()

        # آمار کاربران
        total_users = get_total_users()
        active_5min = _get_active_users_since(5)
        active_1hour = _get_active_users_last_hour()
        active_today = get_active_users(1)

        # آمار درخواست‌ها
        rpm = _get_requests_per_minute()

        # وضعیت API
        api_latency = _get_api_latency_stats()

        # وضعیت Scheduler
        scheduler_status = _get_scheduler_status_stats()

        # منابع سیستم
        system_usage = _get_system_usage()

        # وضعیت اتصال‌ها
        db_ok = _check_db_connection()
        redis_ok = _check_redis_connection()

        # حجم دیتابیس
        db_size_mb = _get_db_size()

        # آمار سفارشات (از db_stats)
        total_orders = db_stats.get('total_orders', 0)
        total_revenue = db_stats.get('total_revenue', 0)

        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'users': {
                'total': total_users,
                'active_5min': active_5min,
                'active_1hour': active_1hour,
                'active_today': active_today,
            },
            'orders': {
                'total': total_orders,
                'revenue': total_revenue,
                'avg_order_value': db_stats.get('avg_order_value', 0),
            },
            'errors': {
                'total': error_stats.get('total', 0),
                'unresolved': error_stats.get('unresolved', 0),
                'resolved': error_stats.get('resolved', 0),
                'by_type': error_stats.get('by_type', []),
            },
            'api': {
                'avg_latency_ms': api_latency.get('avg_ms', 0),
                'status': api_latency.get('status', 'unknown'),
                'status_text': api_latency.get('status_text', '⚪ نامشخص'),
                'error_count_5min': api_latency.get('error_count_5min', 0),
            },
            'requests': {
                'rpm': rpm,
                'total_clicks': db_stats.get('total_clicks', 0),
            },
            'infrastructure': {
                'database': {
                    'connected': db_ok,
                    'size_mb': db_size_mb,
                    'status': "🟢 متصل" if db_ok else "🔴 قطع",
                },
                'redis': {
                    'connected': redis_ok,
                    'enabled': config.REDIS_ENABLED,
                    'status': "🟢 متصل" if redis_ok else ("⚪ غیرفعال" if not config.REDIS_ENABLED else "🔴 قطع"),
                },
                'scheduler': scheduler_status,
                'system': system_usage,
            }
        }

    except Exception as e:
        log_callback_error(
            f"Error in get_monitoring_stats: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'error': str(e),
            'users': {'total': 0, 'active_5min': 0, 'active_1hour': 0, 'active_today': 0},
            'orders': {'total': 0, 'revenue': 0, 'avg_order_value': 0},
            'errors': {'total': 0, 'unresolved': 0, 'resolved': 0, 'by_type': []},
            'api': {'avg_latency_ms': 0, 'status': 'unknown', 'status_text': '⚪ نامشخص', 'error_count_5min': 0},
            'requests': {'rpm': 0, 'total_clicks': 0},
            'infrastructure': {
                'database': {'connected': False, 'size_mb': 0, 'status': '🔴 قطع'},
                'redis': {'connected': False, 'enabled': config.REDIS_ENABLED, 'status': '🔴 قطع'},
                'scheduler': {'is_running': False, 'total_jobs': 0, 'jobs': [], 'status_text': '❌ خطا'},
                'system': {'cpu_percent': 0, 'memory_percent': 0, 'disk_percent': 0, 'available': False},
            }
        }


# ============================================================
# کیبورد داشبورد (برای استفاده در پنل)
# ============================================================

def monitoring_main_keyboard() -> Dict[str, Any]:
    """کیبورد اصلی داشبورد مانیتورینگ"""
    return {
        "inline_keyboard": [
            [{"text": "🔄 به‌روزرسانی", "callback_data": "admin_monitoring"}],
            [{"text": "🏥 بررسی سلامت", "callback_data": "admin_monitoring_health"}],
            [{"text": "🚨 مدیریت هشدارها", "callback_data": "admin_monitoring_alerts"}],
            [{"text": "📊 آمار و متریک‌ها", "callback_data": "admin_monitoring_metrics"}],
            [{"text": "📄 گزارش‌ها", "callback_data": "admin_monitoring_reports"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


# ============================================================
# توابع کمکی برای فرمت‌بندی پیام
# ============================================================

def _format_status(status: bool, true_text: str = "🟢 سالم", false_text: str = "🔴 مشکل") -> str:
    """فرمت‌بندی وضعیت بولی به متن با آیکون"""
    return true_text if status else false_text


def _format_percent(value: float) -> str:
    """فرمت‌بندی درصد با یک رقم اعشار"""
    return f"{value:.1f}%"


def _format_number(num: int) -> str:
    """فرمت‌بندی اعداد با کاما"""
    return f"{num:,}"


# ============================================================
# هندلر اصلی داشبورد
# ============================================================

async def handle_monitoring(chat_id: int, user_id: int) -> bool:
    """
    نمایش داشبورد مانیتورینگ با آمار لحظه‌ای.

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    ctx_logger = ContextLogger("monitoring.dashboard.handler", context={"user_id": user_id, "chat_id": chat_id})

    try:
        # دریافت آمار
        stats = await get_monitoring_stats()

        if 'error' in stats:
            await send_message(
                chat_id,
                f"❌ خطا در دریافت آمار مانیتورینگ:\n{stats['error']}",
                monitoring_main_keyboard()
            )
            return True

        # ========== ساخت پیام ==========
        msg = f"📊 **داشبورد مانیتورینگ لحظه‌ای**\n"
        msg += f"🕐 **زمان:** {stats['timestamp']}\n"
        msg += "─" * 30 + "\n\n"

        # ========== وضعیت سرویس‌ها ==========
        msg += "🔌 **وضعیت سرویس‌ها:**\n"
        db_status = stats['infrastructure']['database']['status']
        redis_status = stats['infrastructure']['redis']['status']
        scheduler_status = stats['infrastructure']['scheduler']['status_text']
        msg += f"  • دیتابیس: {db_status}\n"
        msg += f"  • Redis: {redis_status}\n"
        msg += f"  • Scheduler: {scheduler_status}\n"
        msg += f"  • حجم دیتابیس: {stats['infrastructure']['database']['size_mb']} MB\n\n"

        # ========== کاربران ==========
        msg += "👥 **کاربران:**\n"
        msg += f"  • کل کاربران: {_format_number(stats['users']['total'])}\n"
        msg += f"  • فعال امروز: {_format_number(stats['users']['active_today'])}\n"
        msg += f"  • فعال ۱ ساعت: {_format_number(stats['users']['active_1hour'])}\n"
        msg += f"  • فعال ۵ دقیقه: {_format_number(stats['users']['active_5min'])}\n\n"

        # ========== سفارشات و درآمد ==========
        msg += "💰 **سفارشات و درآمد:**\n"
        msg += f"  • کل سفارشات: {_format_number(stats['orders']['total'])}\n"
        msg += f"  • کل درآمد: {_format_number(stats['orders']['revenue'])} ریال\n"
        msg += f"  • میانگین هر سفارش: {_format_number(stats['orders']['avg_order_value'])} ریال\n\n"

        # ========== خطاها ==========
        msg += "🚨 **خطاها:**\n"
        msg += f"  • کل خطاها: {_format_number(stats['errors']['total'])}\n"
        msg += f"  • حل‌شده: {_format_number(stats['errors']['resolved'])}\n"
        msg += f"  • حل‌نشده: {_format_number(stats['errors']['unresolved'])}\n"
        # نمایش ۳ نوع خطای پرتکرار
        if stats['errors']['by_type']:
            msg += "  • تفکیک (۳ نوع اصلی):\n"
            for item in stats['errors']['by_type'][:3]:
                error_type = item.get('error_type', 'نامشخص')
                count = item.get('count', 0)
                msg += f"      - {error_type}: {count}\n"
        msg += "\n"

        # ========== API و درخواست‌ها ==========
        msg += "🌐 **API و درخواست‌ها:**\n"
        msg += f"  • وضعیت API: {stats['api']['status_text']}\n"
        msg += f"  • میانگین تأخیر: {stats['api']['avg_latency_ms']} ms\n"
        msg += f"  • خطاهای ۵ دقیقه اخیر: {stats['api']['error_count_5min']}\n"
        msg += f"  • میانگین RPM: {stats['requests']['rpm']}\n\n"

        # ========== منابع سیستم ==========
        if stats['infrastructure']['system']['available']:
            sys = stats['infrastructure']['system']
            msg += "🖥️ **منابع سیستم:**\n"
            msg += f"  • CPU: {_format_percent(sys['cpu_percent'])}\n"
            msg += f"  • RAM: {_format_percent(sys['memory_percent'])}\n"
            msg += f"  • Disk: {_format_percent(sys['disk_percent'])}\n\n"
        else:
            msg += "ℹ️ برای مشاهده منابع سیستم، پکیج `psutil` را نصب کنید.\n\n"

        # ========== تسک‌های زمان‌بندی‌شده ==========
        scheduler = stats['infrastructure']['scheduler']
        msg += "⏰ **تسک‌های زمان‌بندی‌شده:**\n"
        msg += f"  • وضعیت: {scheduler['status_text']}\n"
        msg += f"  • تعداد تسک‌ها: {scheduler['total_jobs']}\n"
        if scheduler['jobs']:
            msg += "  • تسک‌های فعال:\n"
            for job in scheduler['jobs'][:3]:
                job_id = job.get('id', 'نامشخص')
                next_run = job.get('next_run_time', 'نامشخص')
                msg += f"      - {job_id} (بعدی: {next_run[:16] if next_run != 'نامشخص' else 'نامشخص'})\n"
            if len(scheduler['jobs']) > 3:
                msg += f"      ... و {len(scheduler['jobs']) - 3} تسک دیگر\n"

        # ارسال پیام
        await send_message(chat_id, msg, monitoring_main_keyboard())
        ctx_logger.info(f"Monitoring dashboard shown to user {user_id}")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_monitoring: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(
            chat_id,
            "❌ خطا در نمایش داشبورد مانیتورینگ. لطفاً دوباره تلاش کنید.",
            monitoring_main_keyboard()
        )
        return True


# ============================================================
# توابع کمکی برای سایر بخش‌ها (جهت استفاده در metrics, alerts, ...)
# ============================================================

async def get_dashboard_stats() -> Dict[str, Any]:
    """Alias برای get_monitoring_stats (برای سازگاری با سایر بخش‌ها)"""
    return await get_monitoring_stats()


async def get_active_users_stats() -> Dict[str, int]:
    """دریافت آمار کاربران فعال برای استفاده در سایر بخش‌ها"""
    return {
        'total': get_total_users(),
        'active_5min': _get_active_users_since(5),
        'active_1hour': _get_active_users_last_hour(),
        'active_today': get_active_users(1),
    }


async def get_api_latency_stats() -> Dict[str, Any]:
    """Alias برای _get_api_latency_stats"""
    return _get_api_latency_stats()


async def get_error_rate_stats() -> Dict[str, Any]:
    """دریافت آمار نرخ خطا"""
    return db_get_error_stats()


async def get_scheduler_status_stats() -> Dict[str, Any]:
    """Alias برای _get_scheduler_status_stats"""
    return _get_scheduler_status_stats()


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'handle_monitoring',
    'get_monitoring_stats',
    'get_dashboard_stats',
    'get_active_users_stats',
    'get_api_latency_stats',
    'get_error_rate_stats',
    'get_scheduler_status_stats',
    'monitoring_main_keyboard',
]