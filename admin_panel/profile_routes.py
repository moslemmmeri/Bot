# admin_panel/profile_routes.py
# ثبت روت‌های مربوط به پروفایل کاربری و تاریخچه سفارشات در پنل مدیریت
# نسخه اصلاح‌شده با مدیریت خطا و لاگ‌گیری کامل

from .router import route, extract_params
from profile import (
    show_profile,
    show_profile_orders,
    show_profile_order_detail,
    show_profile_stats,
    cancel_profile_order,
)
from core import send_message, OWNER_ID
from logger_config import logger
from utils.error_handler import log_error


# ============================================================
# تابع کمکی
# ============================================================

def _is_owner(user_id: int) -> bool:
    """بررسی آیا کاربر OWNER_ID است"""
    return user_id == OWNER_ID


# ============================================================
# روت‌های پروفایل کاربری
# ============================================================

@route("profile_main")
async def profile_main(update):
    """نمایش پروفایل کاربری (profile_main)"""
    chat_id, user_id, data = extract_params(update)
    
    if not chat_id or not user_id:
        return True
    
    try:
        await show_profile(chat_id, user_id)
    except Exception as e:
        logger.error(f"❌ خطا در profile_main برای کاربر {user_id}: {e}", exc_info=True)
        log_error('callback', f"profile_main: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش پروفایل. لطفاً دوباره تلاش کنید.")
    return True


@route("profile_orders_")
async def profile_orders(update):
    """نمایش لیست سفارشات کاربر (profile_orders_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    
    if not chat_id or not user_id:
        return True
    
    try:
        parts = data.split("_")
        if len(parts) < 3:
            await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
            return True
        
        target_user_id = int(parts[-1])
        if target_user_id == user_id:
            await show_profile_orders(chat_id, user_id, 0)
        else:
            await send_message(chat_id, "⛔ دسترسی غیرمجاز.")
    except ValueError:
        logger.warning(f"شناسه کاربر نامعتبر در profile_orders: {data}")
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
    except Exception as e:
        logger.error(f"❌ خطا در profile_orders برای کاربر {user_id}: {e}", exc_info=True)
        log_error('callback', f"profile_orders: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش سفارشات. لطفاً دوباره تلاش کنید.")
    return True


@route("profile_orders_page_")
async def profile_orders_page(update):
    """صفحه‌بندی لیست سفارشات کاربر (profile_orders_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    
    if not chat_id or not user_id:
        return True
    
    try:
        page = int(data.split("_")[-1])
        if page < 0:
            page = 0
        await show_profile_orders(chat_id, user_id, page)
    except ValueError:
        logger.warning(f"شماره صفحه نامعتبر در profile_orders_page: {data}")
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
    except Exception as e:
        logger.error(f"❌ خطا در profile_orders_page برای کاربر {user_id}: {e}", exc_info=True)
        log_error('callback', f"profile_orders_page: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در صفحه‌بندی. لطفاً دوباره تلاش کنید.")
    return True


@route("profile_orders_back")
async def profile_orders_back(update):
    """
    بازگشت به لیست سفارشات (profile_orders_back)
    این روت بیشترین استفاده را دارد و باید خطاهای آن به‌خوبی لاگ شود
    """
    chat_id, user_id, data = extract_params(update)
    
    if not chat_id or not user_id:
        return True
    
    try:
        logger.info(f"🔄 بازگشت به لیست سفارشات برای کاربر {user_id}")
        await show_profile_orders(chat_id, user_id, 0)
        logger.info(f"✅ لیست سفارشات برای کاربر {user_id} نمایش داده شد.")
    except Exception as e:
        logger.error(f"❌❌❌ خطا در profile_orders_back برای کاربر {user_id}: {e}", exc_info=True)
        log_error('callback', f"profile_orders_back: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در بازگشت به لیست سفارشات. لطفاً دوباره تلاش کنید.")
    return True


@route("profile_order_detail_")
async def profile_order_detail(update):
    """نمایش جزئیات یک سفارش (profile_order_detail_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    
    if not chat_id or not user_id:
        return True
    
    try:
        order_id = int(data.split("_")[-1])
        if order_id <= 0:
            await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
            return True
        await show_profile_order_detail(chat_id, user_id, order_id)
    except ValueError:
        logger.warning(f"شناسه سفارش نامعتبر در profile_order_detail: {data}")
        await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
    except Exception as e:
        logger.error(f"❌ خطا در profile_order_detail برای کاربر {user_id}: {e}", exc_info=True)
        log_error('callback', f"profile_order_detail: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش. لطفاً دوباره تلاش کنید.")
    return True


@route("profile_order_cancel_")
async def profile_order_cancel(update):
    """لغو سفارش در انتظار پرداخت (profile_order_cancel_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    
    if not chat_id or not user_id:
        return True
    
    try:
        order_id = int(data.split("_")[-1])
        if order_id <= 0:
            await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
            return True
        await cancel_profile_order(chat_id, user_id, order_id)
    except ValueError:
        logger.warning(f"شناسه سفارش نامعتبر در profile_order_cancel: {data}")
        await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
    except Exception as e:
        logger.error(f"❌ خطا در profile_order_cancel برای کاربر {user_id}: {e}", exc_info=True)
        log_error('callback', f"profile_order_cancel: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در لغو سفارش. لطفاً دوباره تلاش کنید.")
    return True


@route("profile_stats_")
async def profile_stats(update):
    """نمایش آمار کاربر (profile_stats_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    
    if not chat_id or not user_id:
        return True
    
    try:
        parts = data.split("_")
        if len(parts) < 3:
            await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
            return True
        
        target_user_id = int(parts[-1])
        if target_user_id == user_id:
            await show_profile_stats(chat_id, user_id)
        else:
            await send_message(chat_id, "⛔ دسترسی غیرمجاز.")
    except ValueError:
        logger.warning(f"شناسه کاربر نامعتبر در profile_stats: {data}")
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
    except Exception as e:
        logger.error(f"❌ خطا در profile_stats برای کاربر {user_id}: {e}", exc_info=True)
        log_error('callback', f"profile_stats: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش آمار. لطفاً دوباره تلاش کنید.")
    return True


# ============================================================
# روت‌های مدیریت کاربران (دسترسی ادمین)
# ============================================================

@route("admin_user_profile_")
async def admin_user_profile(update):
    """مشاهده پروفایل یک کاربر توسط ادمین (admin_user_profile_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        target_user_id = int(data.split("_")[-1])
        if target_user_id <= 0:
            await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
            return True
        await show_profile(chat_id, target_user_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
    except Exception as e:
        logger.error(f"❌ خطا در admin_user_profile: {e}", exc_info=True)
        log_error('callback', f"admin_user_profile: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش پروفایل کاربر.")
    return True


@route("admin_user_orders_")
async def admin_user_orders(update):
    """مشاهده سفارشات یک کاربر توسط ادمین (admin_user_orders_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        target_user_id = int(data.split("_")[-1])
        if target_user_id <= 0:
            await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
            return True
        await show_profile_orders(chat_id, target_user_id, 0)
    except ValueError:
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
    except Exception as e:
        logger.error(f"❌ خطا در admin_user_orders: {e}", exc_info=True)
        log_error('callback', f"admin_user_orders: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش سفارشات کاربر.")
    return True


@route("admin_user_stats_")
async def admin_user_stats(update):
    """مشاهده آمار یک کاربر توسط ادمین (admin_user_stats_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        target_user_id = int(data.split("_")[-1])
        if target_user_id <= 0:
            await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
            return True
        await show_profile_stats(chat_id, target_user_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
    except Exception as e:
        logger.error(f"❌ خطا در admin_user_stats: {e}", exc_info=True)
        log_error('callback', f"admin_user_stats: {str(e)}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش آمار کاربر.")
    return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'profile_main',
    'profile_orders',
    'profile_orders_page',
    'profile_orders_back',
    'profile_order_detail',
    'profile_order_cancel',
    'profile_stats',
    'admin_user_profile',
    'admin_user_orders',
    'admin_user_stats',
]