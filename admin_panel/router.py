# admin_panel/router.py
# هسته مسیریابی پنل مدیریت - شامل دیکشنری روت‌ها، دکوراتور route و تابع اصلی مسیریابی

import asyncio
import traceback
from logger_config import logger
from core import send_message, OWNER_ID
from database import is_admin
from keyboards import admin_main_keyboard
from utils.error_handler import log_general_error


# ========== دیکشنری مسیریابی ==========
ROUTES = {}

def route(prefix):
    """
    دکوراتور برای ثبت مسیرهای کالبک پنل مدیریت.
    
    استفاده:
        @route("admin_panel")
        async def show_admin_panel(update):
            ...
    
    پارامترها:
        prefix: پیشوند کالبک (مثلاً "admin_panel" یا "admin_orders_")
    
    بازگشت: دکوراتور
    """
    def decorator(func):
        ROUTES[prefix] = func
        logger.debug(f"Route registered: {prefix} -> {func.__name__}")
        return func
    return decorator


# ========== تابع کمکی برای استخراج پارامترها ==========
def extract_params(update):
    """
    استخراج chat_id, user_id, data از update کالبک.
    
    پارامترها:
        update: دیکشنری آپدیت دریافتی از بله
    
    بازگشت: (chat_id, user_id, data) یا (None, None, None) در صورت خطا
    """
    cb = update.get("callback_query")
    if not cb:
        return None, None, None
    data = cb.get("data")
    user_id = cb.get("from", {}).get("id")
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    return chat_id, user_id, data


# ========== تابع اصلی مسیریابی ==========
async def handle_admin_callback(update):
    """
    تابع اصلی مسیریابی کالبک‌های پنل مدیریت
    با استفاده از دیکشنری ROUTES و تطابق پیشوند
    
    پارامترها:
        update: دیکشنری آپدیت دریافتی از بله
    
    بازگشت: True اگر کالبک پردازش شد، False در غیر این صورت
    """
    try:
        cb = update.get("callback_query")
        if not cb:
            logger.warning("handle_admin_callback: callback_query وجود ندارد")
            return False

        data = cb.get("data")
        user_id = cb.get("from", {}).get("id")
        chat_id = cb.get("message", {}).get("chat", {}).get("id")

        # لاگ کامل کالبک دریافتی
        logger.info(f"📩 کالبک دریافتی: user_id={user_id}, data={data}")

        if not user_id or not chat_id:
            logger.warning("handle_admin_callback: user_id or chat_id missing")
            return False

        # بررسی دسترسی ادمین
        if user_id != OWNER_ID and not is_admin(user_id):
            await send_message(chat_id, "⛔ شما دسترسی به پنل مدیریت ندارید.")
            return True

        # جستجو در دیکشنری روت‌ها
        # مرتب‌سازی روت‌ها بر اساس طول پیشوند (نزولی) برای جلوگیری از تداخل
        sorted_routes = sorted(ROUTES.items(), key=lambda x: len(x[0]), reverse=True)

        for prefix, handler in sorted_routes:
            if data.startswith(prefix):
                logger.info(f"✅ Route matched: {prefix} -> {handler.__name__}")
                return await handler(update)

        # اگر هیچ تطابقی یافت نشد
        logger.warning(f"❌ Unhandled admin callback: {data}")
        await send_message(chat_id, "❌ گزینه نامعتبر است.", admin_main_keyboard())
        return True

    except Exception as e:
        # ✅ استفاده از log_general_error با traceback کامل
        log_general_error(
            f"Error in handle_admin_callback: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id if 'user_id' in locals() else None,
            chat_id=chat_id if 'chat_id' in locals() else None
        )
        try:
            await send_message(
                chat_id if 'chat_id' in locals() else None,
                f"❌ خطای سیستمی: {str(e)}"
            )
        except:
            pass
        return True


# ========== ایمپورت روت‌های مانیتورینگ ==========
# این ایمپورت باعث می‌شود که روت‌های تعریف‌شده در monitoring.routes
# به‌صورت خودکار در دیکشنری ROUTES ثبت شوند.
from .monitoring import routes as monitoring_routes  # noqa


__all__ = [
    'ROUTES',
    'route',
    'extract_params',
    'handle_admin_callback',
]