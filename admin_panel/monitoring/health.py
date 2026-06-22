# admin_panel/monitoring/health.py
# بررسی سلامت سرویس‌ها (Health Check)
# شامل: بررسی دیتابیس، Redis، API بله، فضای دیسک، حجم دیتابیس و منابع سیستم

import os
import time
import traceback
from typing import Dict, Any, List, Tuple
from datetime import datetime

from logger_config import logger, ContextLogger
from core import send_message
from database import get_db_connection
from config import config
from utils.error_handler import log_callback_error, log_general_error, log_database_error

# تلاش برای import psutil (در صورت نصب نبودن، منابع سیستم نمایش داده نمی‌شوند)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# ============================================================
# کیبوردهای بخش سلامت
# ============================================================

def health_check_keyboard() -> Dict[str, Any]:
    """کیبورد اصلی بخش بررسی سلامت"""
    return {
        "inline_keyboard": [
            [{"text": "🔄 بررسی مجدد", "callback_data": "admin_monitoring_health"}],
            [{"text": "📊 بازگشت به داشبورد", "callback_data": "admin_monitoring"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


# ============================================================
# توابع بررسی سلامت سرویس‌ها
# ============================================================

async def check_db_health() -> Dict[str, Any]:
    """
    بررسی سلامت اتصال به دیتابیس و وضعیت آن.

    بازگشت: دیکشنری شامل status, message, details
    """
    ctx_logger = ContextLogger("monitoring.health.db")
    start_time = time.time()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # تست ساده با SELECT 1
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            # بررسی تعداد جدول‌ها برای اطمینان از سلامت ساختار
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            row = cursor.fetchone()
            table_count = row[0] if row else 0

            elapsed_ms = int((time.time() - start_time) * 1000)

            if result and table_count > 0:
                return {
                    'status': 'ok',
                    'message': 'اتصال به دیتابیس برقرار است',
                    'details': {
                        'response_time_ms': elapsed_ms,
                        'table_count': table_count,
                        'db_path': config.SQLITE_DB_PATH,
                        'db_size_mb': _get_db_size_mb(),
                    },
                    'status_text': '🟢 سالم',
                    'status_icon': '🟢'
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'دیتابیس در دسترس است اما ممکن است مشکل داشته باشد',
                    'details': {
                        'response_time_ms': elapsed_ms,
                        'table_count': table_count,
                        'db_path': config.SQLITE_DB_PATH,
                    },
                    'status_text': '🟡 هشدار',
                    'status_icon': '🟡'
                }

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        log_database_error(
            f"Database health check failed: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'status': 'error',
            'message': f'خطا در اتصال به دیتابیس: {str(e)}',
            'details': {
                'response_time_ms': elapsed_ms,
                'error': str(e),
            },
            'status_text': '🔴 مشکل',
            'status_icon': '🔴'
        }


async def check_redis_health() -> Dict[str, Any]:
    """
    بررسی سلامت اتصال به Redis.

    بازگشت: دیکشنری شامل status, message, details
    """
    ctx_logger = ContextLogger("monitoring.health.redis")
    start_time = time.time()

    try:
        if not config.REDIS_ENABLED:
            return {
                'status': 'disabled',
                'message': 'Redis غیرفعال است',
                'details': {'enabled': False},
                'status_text': '⚪ غیرفعال',
                'status_icon': '⚪'
            }

        from cache import get_cache_manager
        cache = get_cache_manager()

        # تست اتصال با یک عملیات ساده
        test_key = f"health_check_{int(time.time())}"
        await cache.set(test_key, "ok", ttl=10)
        value = await cache.get(test_key)
        await cache.delete(test_key)

        elapsed_ms = int((time.time() - start_time) * 1000)

        if value == "ok":
            return {
                'status': 'ok',
                'message': 'اتصال به Redis برقرار است',
                'details': {
                    'response_time_ms': elapsed_ms,
                    'host': config.REDIS_HOST,
                    'port': config.REDIS_PORT,
                    'db': config.REDIS_DB,
                },
                'status_text': '🟢 سالم',
                'status_icon': '🟢'
            }
        else:
            return {
                'status': 'warning',
                'message': 'Redis پاسخ نامعتبر برگرداند',
                'details': {'response_time_ms': elapsed_ms},
                'status_text': '🟡 هشدار',
                'status_icon': '🟡'
            }

    except ImportError:
        return {
            'status': 'error',
            'message': 'پکیج redis-py نصب نیست',
            'details': {'error': 'ImportError: redis not installed'},
            'status_text': '🔴 مشکل',
            'status_icon': '🔴'
        }
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        log_general_error(
            f"Redis health check failed: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'status': 'error',
            'message': f'خطا در اتصال به Redis: {str(e)}',
            'details': {
                'response_time_ms': elapsed_ms,
                'error': str(e),
            },
            'status_text': '🔴 مشکل',
            'status_icon': '🔴'
        }


async def check_bale_api() -> Dict[str, Any]:
    """
    بررسی سلامت اتصال به API بله با ارسال یک درخواست ساده (getMe).

    بازگشت: دیکشنری شامل status, message, details
    """
    ctx_logger = ContextLogger("monitoring.health.bale_api")
    start_time = time.time()

    try:
        import aiohttp
        import asyncio

        # استفاده از getMe برای بررسی اتصال به API
        url = f"https://tapi.bale.ai/bot{config.BOT_TOKEN}/getMe"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                elapsed_ms = int((time.time() - start_time) * 1000)

                if resp.status == 200:
                    data = await resp.json()
                    if data.get('ok'):
                        return {
                            'status': 'ok',
                            'message': f'اتصال به API بله برقرار است (ربات: {data.get("result", {}).get("username", "نامشخص")})',
                            'details': {
                                'response_time_ms': elapsed_ms,
                                'status_code': resp.status,
                                'bot_username': data.get('result', {}).get('username', 'نامشخص'),
                            },
                            'status_text': '🟢 سالم',
                            'status_icon': '🟢'
                        }
                    else:
                        return {
                            'status': 'warning',
                            'message': 'API بله پاسخ نامعتبر برگرداند',
                            'details': {
                                'response_time_ms': elapsed_ms,
                                'status_code': resp.status,
                                'response': data.get('description', 'نامشخص'),
                            },
                            'status_text': '🟡 هشدار',
                            'status_icon': '🟡'
                        }
                else:
                    return {
                        'status': 'error',
                        'message': f'API بله با کد {resp.status} پاسخ داد',
                        'details': {
                            'response_time_ms': elapsed_ms,
                            'status_code': resp.status,
                        },
                        'status_text': '🔴 مشکل',
                        'status_icon': '🔴'
                    }

    except asyncio.TimeoutError:
        elapsed_ms = int((time.time() - start_time) * 1000)
        log_general_error(
            "Bale API health check timeout",
            context_logger=ctx_logger
        )
        return {
            'status': 'error',
            'message': 'API بله پاسخ نداد (Timeout)',
            'details': {'response_time_ms': elapsed_ms},
            'status_text': '🔴 مشکل',
            'status_icon': '🔴'
        }
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        log_general_error(
            f"Bale API health check failed: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'status': 'error',
            'message': f'خطا در اتصال به API بله: {str(e)}',
            'details': {
                'response_time_ms': elapsed_ms,
                'error': str(e),
            },
            'status_text': '🔴 مشکل',
            'status_icon': '🔴'
        }


def check_disk_usage() -> Dict[str, Any]:
    """
    بررسی فضای خالی دیسک.

    بازگشت: دیکشنری شامل status, message, details
    """
    try:
        if not PSUTIL_AVAILABLE:
            return {
                'status': 'warning',
                'message': 'پکیج psutil نصب نیست، امکان بررسی فضای دیسک وجود ندارد',
                'details': {'available': False},
                'status_text': '🟡 هشدار',
                'status_icon': '🟡'
            }

        disk = psutil.disk_usage('/')
        total_gb = disk.total / (1024**3)
        used_gb = disk.used / (1024**3)
        free_gb = disk.free / (1024**3)
        percent = disk.percent

        # هشدار اگر فضای خالی کمتر از ۱۰٪ باشد
        if percent > 90:
            status = 'warning'
            message = f'فضای دیسک در حال اتمام است ({percent:.1f}% استفاده شده)'
            status_text = '🟡 هشدار'
            status_icon = '🟡'
        elif percent > 95:
            status = 'error'
            message = f'فضای دیسک بسیار کم است ({percent:.1f}% استفاده شده)'
            status_text = '🔴 مشکل'
            status_icon = '🔴'
        else:
            status = 'ok'
            message = f'فضای دیسک کافی است ({percent:.1f}% استفاده شده)'
            status_text = '🟢 سالم'
            status_icon = '🟢'

        return {
            'status': status,
            'message': message,
            'details': {
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'used_percent': percent,
            },
            'status_text': status_text,
            'status_icon': status_icon
        }

    except Exception as e:
        log_general_error(
            f"Disk usage check failed: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {
            'status': 'error',
            'message': f'خطا در بررسی فضای دیسک: {str(e)}',
            'details': {'error': str(e)},
            'status_text': '🔴 مشکل',
            'status_icon': '🔴'
        }


def get_db_size() -> int:
    """
    دریافت حجم فایل دیتابیس به بایت.

    بازگشت: حجم دیتابیس به بایت
    """
    try:
        db_path = config.SQLITE_DB_PATH
        if os.path.exists(db_path):
            return os.path.getsize(db_path)
        return 0
    except Exception as e:
        log_general_error(
            f"Error getting DB size: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0


def _get_db_size_mb() -> float:
    """
    دریافت حجم فایل دیتابیس به مگابایت.

    بازگشت: حجم دیتابیس به مگابایت (با دو رقم اعشار)
    """
    size_bytes = get_db_size()
    if size_bytes > 0:
        return round(size_bytes / (1024 * 1024), 2)
    return 0.0


def get_system_resources() -> Dict[str, Any]:
    """
    دریافت وضعیت منابع سیستم (CPU, Memory).

    بازگشت: دیکشنری شامل درصد مصرف CPU و Memory
    """
    try:
        if not PSUTIL_AVAILABLE:
            return {
                'available': False,
                'cpu_percent': 0,
                'memory_percent': 0,
                'message': 'پکیج psutil نصب نیست'
            }

        return {
            'available': True,
            'cpu_percent': psutil.cpu_percent(interval=0.5),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available_mb': round(psutil.virtual_memory().available / (1024 * 1024), 2),
            'memory_total_mb': round(psutil.virtual_memory().total / (1024 * 1024), 2),
        }
    except Exception as e:
        log_general_error(
            f"Error getting system resources: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {
            'available': False,
            'cpu_percent': 0,
            'memory_percent': 0,
            'error': str(e)
        }


# ============================================================
# تابع اصلی بررسی کامل سلامت
# ============================================================

async def run_health_check() -> Dict[str, Any]:
    """
    اجرای بررسی کامل سلامت تمام سرویس‌ها.

    بازگشت: دیکشنری جامع شامل نتایج تمام بررسی‌ها
    """
    ctx_logger = ContextLogger("monitoring.health.run_health_check")
    start_time = time.time()

    try:
        # اجرای همه بررسی‌ها به صورت موازی
        import asyncio
        db_result, redis_result, api_result = await asyncio.gather(
            check_db_health(),
            check_redis_health(),
            check_bale_api(),
        )

        disk_result = check_disk_usage()
        system_resources = get_system_resources()

        # محاسبه وضعیت کلی
        all_ok = all([
            db_result['status'] == 'ok',
            redis_result['status'] in ['ok', 'disabled'],
            api_result['status'] == 'ok',
            disk_result['status'] == 'ok',
        ])

        # شمارش مشکلات
        errors = []
        warnings = []
        for name, result in [
            ('database', db_result),
            ('redis', redis_result),
            ('bale_api', api_result),
            ('disk', disk_result),
        ]:
            if result['status'] == 'error':
                errors.append(name)
            elif result['status'] == 'warning':
                warnings.append(name)

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'overall_status': 'ok' if all_ok else ('warning' if warnings and not errors else 'error'),
            'overall_status_text': '🟢 همه سرویس‌ها سالم' if all_ok else ('🟡 برخی هشدارها' if warnings and not errors else '🔴 برخی سرویس‌ها مشکل دارند'),
            'overall_icon': '🟢' if all_ok else ('🟡' if warnings and not errors else '🔴'),
            'checks': {
                'database': db_result,
                'redis': redis_result,
                'bale_api': api_result,
                'disk': disk_result,
                'system_resources': system_resources,
            },
            'summary': {
                'total_checks': 4,  # db, redis, api, disk
                'ok_count': sum(1 for r in [db_result, redis_result, api_result, disk_result] if r['status'] == 'ok'),
                'warning_count': len(warnings),
                'error_count': len(errors),
                'errors': errors,
                'warnings': warnings,
            },
            'elapsed_ms': elapsed_ms,
        }

    except Exception as e:
        log_callback_error(
            f"Error in run_health_check: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'overall_status': 'error',
            'overall_status_text': '🔴 خطا در اجرای بررسی سلامت',
            'overall_icon': '🔴',
            'checks': {},
            'summary': {
                'total_checks': 0,
                'ok_count': 0,
                'warning_count': 0,
                'error_count': 1,
                'errors': ['health_check'],
                'warnings': [],
            },
            'elapsed_ms': 0,
            'error': str(e),
        }


# ============================================================
# توابع کمکی برای فرمت‌بندی پیام سلامت
# ============================================================

def _format_health_result(name: str, result: Dict[str, Any]) -> str:
    """فرمت‌بندی یک نتیجه بررسی سلامت برای نمایش در پیام"""
    status_icon = result.get('status_icon', '⚪')
    message = result.get('message', 'نامشخص')
    return f"  • {status_icon} **{name}:** {message}"


def _format_health_details(details: Dict[str, Any], indent: int = 4) -> str:
    """فرمت‌بندی جزئیات یک بررسی سلامت"""
    if not details:
        return ""

    lines = []
    for key, value in details.items():
        if value is not None and value != "":
            # تبدیل کلید به نام خوانا
            key_name = key.replace('_', ' ').title()
            if isinstance(value, bool):
                value_text = "✅ بله" if value else "❌ خیر"
            elif isinstance(value, float):
                value_text = f"{value:.2f}"
            else:
                value_text = str(value)
            lines.append(f"{' ' * indent}• {key_name}: {value_text}")

    return "\n".join(lines)


# ============================================================
# هندلر اصلی بخش سلامت
# ============================================================

async def handle_health_check(chat_id: int, user_id: int) -> bool:
    """
    نمایش وضعیت سلامت سرویس‌ها.

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    ctx_logger = ContextLogger("monitoring.health.handler", context={"user_id": user_id, "chat_id": chat_id})

    try:
        # ارسال پیام در حال بررسی
        await send_message(chat_id, "🔄 در حال بررسی سلامت سرویس‌ها... لطفاً صبر کنید.")

        # اجرای بررسی سلامت
        result = await run_health_check()

        # ========== ساخت پیام ==========
        msg = f"🏥 **بررسی سلامت سرویس‌ها**\n"
        msg += f"🕐 زمان: {result['timestamp']}\n"
        msg += f"📊 وضعیت کلی: {result['overall_status_text']}\n"
        msg += f"⏱️  زمان بررسی: {result['elapsed_ms']} ms\n"
        msg += "─" * 30 + "\n\n"

        # ========== خلاصه ==========
        summary = result.get('summary', {})
        msg += f"📊 **خلاصه:**\n"
        msg += f"  • بررسی‌های انجام‌شده: {summary.get('total_checks', 0)}\n"
        msg += f"  • ✅ سالم: {summary.get('ok_count', 0)}\n"
        msg += f"  • 🟡 هشدار: {summary.get('warning_count', 0)}\n"
        msg += f"  • 🔴 مشکل: {summary.get('error_count', 0)}\n\n"

        # ========== جزئیات بررسی‌ها ==========
        checks = result.get('checks', {})

        # دیتابیس
        if 'database' in checks:
            db = checks['database']
            msg += f"🗄️ **دیتابیس:**\n"
            msg += f"  • وضعیت: {db.get('status_text', 'نامشخص')}\n"
            msg += f"  • پیام: {db.get('message', 'نامشخص')}\n"
            details = db.get('details', {})
            if details:
                msg += f"  • جزئیات:\n"
                msg += f"    • زمان پاسخ: {details.get('response_time_ms', 'نامشخص')} ms\n"
                msg += f"    • تعداد جدول‌ها: {details.get('table_count', 'نامشخص')}\n"
                msg += f"    • حجم: {details.get('db_size_mb', 0)} MB\n"
            msg += "\n"

        # Redis
        if 'redis' in checks:
            redis = checks['redis']
            msg += f"⚡ **Redis:**\n"
            msg += f"  • وضعیت: {redis.get('status_text', 'نامشخص')}\n"
            msg += f"  • پیام: {redis.get('message', 'نامشخص')}\n"
            details = redis.get('details', {})
            if details and redis['status'] != 'disabled':
                msg += f"  • جزئیات:\n"
                msg += f"    • زمان پاسخ: {details.get('response_time_ms', 'نامشخص')} ms\n"
                msg += f"    • Host: {details.get('host', 'نامشخص')}\n"
                msg += f"    • Port: {details.get('port', 'نامشخص')}\n"
            msg += "\n"

        # API بله
        if 'bale_api' in checks:
            api = checks['bale_api']
            msg += f"🌐 **API بله:**\n"
            msg += f"  • وضعیت: {api.get('status_text', 'نامشخص')}\n"
            msg += f"  • پیام: {api.get('message', 'نامشخص')}\n"
            details = api.get('details', {})
            if details and api['status'] != 'error':
                msg += f"  • جزئیات:\n"
                msg += f"    • زمان پاسخ: {details.get('response_time_ms', 'نامشخص')} ms\n"
                msg += f"    • ربات: @{details.get('bot_username', 'نامشخص')}\n"
            msg += "\n"

        # فضای دیسک
        if 'disk' in checks:
            disk = checks['disk']
            msg += f"💾 **فضای دیسک:**\n"
            msg += f"  • وضعیت: {disk.get('status_text', 'نامشخص')}\n"
            msg += f"  • پیام: {disk.get('message', 'نامشخص')}\n"
            details = disk.get('details', {})
            if details and disk['status'] != 'warning':
                msg += f"  • جزئیات:\n"
                msg += f"    • کل: {details.get('total_gb', 0)} GB\n"
                msg += f"    • استفاده‌شده: {details.get('used_gb', 0)} GB\n"
                msg += f"    • خالی: {details.get('free_gb', 0)} GB\n"
                msg += f"    • درصد استفاده: {details.get('used_percent', 0)}%\n"
            msg += "\n"

        # منابع سیستم
        sys_res = checks.get('system_resources', {})
        if sys_res and sys_res.get('available', False):
            msg += f"🖥️ **منابع سیستم:**\n"
            msg += f"  • CPU: {sys_res.get('cpu_percent', 0):.1f}%\n"
            msg += f"  • RAM: {sys_res.get('memory_percent', 0):.1f}%\n"
            msg += f"  • RAM موجود: {sys_res.get('memory_available_mb', 0)} MB\n"
            msg += f"  • RAM کل: {sys_res.get('memory_total_mb', 0)} MB\n"
        elif sys_res and 'message' in sys_res:
            msg += f"ℹ️ {sys_res.get('message', '')}\n"

        # ========== در صورت وجود خطا ==========
        if result.get('error'):
            msg += f"\n⚠️ **خطا در اجرای بررسی:** {result['error']}\n"

        # ارسال پیام
        await send_message(chat_id, msg, health_check_keyboard())
        ctx_logger.info(f"Health check shown to user {user_id}")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_health_check: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(
            chat_id,
            "❌ خطا در بررسی سلامت سرویس‌ها. لطفاً دوباره تلاش کنید.",
            health_check_keyboard()
        )
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'handle_health_check',
    'run_health_check',
    'check_db_health',
    'check_redis_health',
    'check_bale_api',
    'check_disk_usage',
    'get_db_size',
    'get_system_resources',
    'health_check_keyboard',
]