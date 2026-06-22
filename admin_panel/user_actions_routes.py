# admin_panel/user_actions_routes.py
# ثبت روت‌های مربوط به مدیریت پیشرفته کاربران در پنل مدیریت
# شامل: مسدود کردن/رفع مسدودیت، مشاهده فعالیت، ارسال پیام انبوه، آمار و ...

from .router import route, extract_params
from .user_actions import (
    handle_user_actions,
    handle_user_block_list,
    handle_user_block_detail,
    handle_user_block,
    handle_user_unblock,
    handle_user_activity_search,
    show_user_activity,
    handle_user_errors,
    handle_broadcast,
    handle_broadcast_target,
    handle_broadcast_send,
    handle_user_actions_stats,
)
from core import send_message, user_states
from logger_config import logger


# ============================================================
# تابع کمکی
# ============================================================

def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# ============================================================
# روت‌های اصلی مدیریت کاربران
# ============================================================

@route("admin_user_actions")
async def admin_user_actions(update):
    """نمایش منوی اصلی مدیریت پیشرفته کاربران"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_actions(chat_id, user_id)


# ============================================================
# روت‌های مدیریت کاربران مسدود شده
# ============================================================

@route("admin_user_block_list")
async def admin_user_block_list(update):
    """نمایش لیست کاربران مسدود شده"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_block_list(chat_id, user_id, 0)


@route("admin_user_block_list_page_")
async def admin_user_block_list_page(update):
    """صفحه‌بندی لیست کاربران مسدود شده"""
    chat_id, user_id, data = extract_params(update)
    try:
        page = int(data.split("_")[-1])
        return await handle_user_block_list(chat_id, user_id, page)
    except ValueError:
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True


@route("admin_user_block_detail_")
async def admin_user_block_detail(update):
    """نمایش جزئیات یک کاربر مسدود شده"""
    chat_id, user_id, data = extract_params(update)
    try:
        target_user_id = int(data.split("_")[-1])
        return await handle_user_block_detail(chat_id, user_id, target_user_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
        return True


@route("admin_user_block_")
async def admin_user_block(update):
    """مسدود کردن یک کاربر"""
    chat_id, user_id, data = extract_params(update)
    try:
        target_user_id = int(data.split("_")[-1])
        # اگر دلیل داده شده باشد
        if len(data.split("_")) > 4:
            reason = "_".join(data.split("_")[4:])
            return await handle_user_block(chat_id, user_id, target_user_id, reason)
        return await handle_user_block(chat_id, user_id, target_user_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
        return True


@route("admin_user_unblock_")
async def admin_user_unblock(update):
    """رفع مسدودیت کاربر"""
    chat_id, user_id, data = extract_params(update)
    try:
        target_user_id = int(data.split("_")[-1])
        return await handle_user_unblock(chat_id, user_id, target_user_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
        return True


# ============================================================
# روت‌های مشاهده فعالیت کاربر
# ============================================================

@route("admin_user_activity_search")
async def admin_user_activity_search(update):
    """شروع جستجوی کاربر برای مشاهده فعالیت"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_activity_search(chat_id, user_id)


@route("admin_user_activity_")
async def admin_user_activity(update):
    """نمایش فعالیت کامل یک کاربر (admin_user_activity_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        target_user_id = int(data.split("_")[-1])
        return await show_user_activity(chat_id, user_id, target_user_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
        return True


@route("admin_user_errors_")
async def admin_user_errors(update):
    """نمایش خطاهای یک کاربر (admin_user_errors_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        target_user_id = int(data.split("_")[-1])
        return await handle_user_errors(chat_id, user_id, target_user_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
        return True


# ============================================================
# روت‌های ارسال پیام انبوه
# ============================================================

@route("admin_user_broadcast")
async def admin_user_broadcast(update):
    """نمایش صفحه انتخاب مخاطبان برای پیام انبوه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_broadcast(chat_id, user_id)


@route("admin_broadcast_all")
@route("admin_broadcast_active")
@route("admin_broadcast_active_week")
@route("admin_broadcast_with_orders")
@route("admin_broadcast_blocked")
async def admin_broadcast_target(update):
    """انتخاب گروه مخاطبان برای ارسال پیام انبوه"""
    chat_id, user_id, data = extract_params(update)
    target_type = data.split("_")[-1]
    return await handle_broadcast_target(chat_id, user_id, target_type)


@route("admin_broadcast_send_")
async def admin_broadcast_send(update):
    """تایید و ارسال پیام انبوه (admin_broadcast_send_<target_type>)"""
    chat_id, user_id, data = extract_params(update)
    target_type = data.split("_")[-1]
    
    # دریافت پیام از user_states
    state_info = user_states.get(user_id, {})
    message = state_info.get("broadcast_message")
    
    if not message:
        # اگر پیام در user_states نبود، از کاربر می‌خواهیم پیام را وارد کند
        user_states[user_id]["broadcast_type"] = target_type
        user_states[user_id]["state"] = "admin_broadcast_message"
        await send_message(
            chat_id,
            f"📨 **ارسال پیام انبوه**\n\n"
            f"لطفاً متن پیام را وارد کنید:\n\n"
            f"📌 **نکته:** کاربران مسدود شده پیام دریافت نمی‌کنند.\n"
            f"برای انصراف، /cancel را ارسال کنید."
        )
        return True
    
    return await handle_broadcast_send(chat_id, user_id, target_type, message)


# ============================================================
# روت‌های آمار کاربران
# ============================================================

@route("admin_user_actions_stats")
async def admin_user_actions_stats(update):
    """نمایش آمار کامل کاربران"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_actions_stats(chat_id, user_id)


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'admin_user_actions',
    'admin_user_block_list',
    'admin_user_block_list_page',
    'admin_user_block_detail',
    'admin_user_block',
    'admin_user_unblock',
    'admin_user_activity_search',
    'admin_user_activity',
    'admin_user_errors',
    'admin_user_broadcast',
    'admin_broadcast_target',
    'admin_broadcast_send',
    'admin_user_actions_stats',
]