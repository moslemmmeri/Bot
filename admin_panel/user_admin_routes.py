# admin_panel/user_admin_routes.py
# ثبت روت‌های مربوط به مدیریت ادمین‌ها و کاربران در پنل مدیریت
# شامل: مدیریت ادمین‌ها (افزودن، حذف، تغییر نقش، تغییر وضعیت، جستجو، آمار)
# و مدیریت کاربران (لیست، جزئیات، جستجو، آمار)

from .router import route, extract_params
from .admin_management import (
    handle_admin_management,
    handle_admin_detail,
    handle_add_admin_start,
    handle_add_admin_role,
    handle_remove_admin,
    handle_remove_admin_confirm,
    handle_change_role,
    handle_change_role_select,
    handle_toggle_admin_status,
    handle_search_admin,
    handle_search_admin_result,
    handle_admin_stats,
    handle_admins_page,
)
from .user_management import (
    handle_user_management,
    handle_user_list,
    handle_user_list_page,
    handle_user_detail,
    handle_user_stats,
    handle_user_search,
    handle_user_search_result,
    # handle_user_orders,  <-- حذف شد
    handle_user_unblock_from_list,
)
from .user_actions import (
    handle_user_actions,
    handle_user_block_list,
    handle_user_block_list_page,
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


# ========== روت‌های مدیریت ادمین‌ها ==========

@route("admin_manage_admins")
async def admin_manage_admins(update):
    """نمایش لیست ادمین‌ها با صفحه‌بندی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_admin_management(chat_id, user_id, 0)


@route("admin_admin_detail_")
async def admin_admin_detail(update):
    """نمایش جزئیات یک ادمین خاص (admin_admin_detail_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_admin_detail(chat_id, user_id, data)


@route("admin_add_admin_start")
async def admin_add_admin_start(update):
    """شروع فرآیند افزودن ادمین جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_add_admin_start(chat_id, user_id)


@route("admin_add_admin_role_")
async def admin_add_admin_role(update):
    """انتخاب نقش برای ادمین جدید (admin_add_admin_role_<user_id>_<role>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_add_admin_role(chat_id, user_id, data)


@route("admin_remove_admin_")
async def admin_remove_admin(update):
    """نمایش تایید حذف ادمین (admin_remove_admin_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_remove_admin(chat_id, user_id, data)


@route("admin_remove_confirm_")
async def admin_remove_confirm(update):
    """تایید نهایی حذف ادمین (admin_remove_confirm_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_remove_admin_confirm(chat_id, user_id, data)


@route("admin_change_role_")
async def admin_change_role(update):
    """شروع فرآیند تغییر نقش ادمین (admin_change_role_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_change_role(chat_id, user_id, data)


@route("admin_change_role_select_")
async def admin_change_role_select(update):
    """انتخاب و اعمال نقش جدید (admin_change_role_select_<user_id>_<role>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_change_role_select(chat_id, user_id, data)


@route("admin_toggle_status_")
async def admin_toggle_status(update):
    """فعال/غیرفعال‌سازی ادمین (admin_toggle_status_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_admin_status(chat_id, user_id, data)


@route("admin_search_admin")
async def admin_search_admin(update):
    """شروع فرآیند جستجوی ادمین"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_admin(chat_id, user_id)


@route("admin_admins_stats")
async def admin_admins_stats(update):
    """نمایش آمار ادمین‌ها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_admin_stats(chat_id, user_id)


@route("admin_admins_page_")
async def admin_admins_page(update):
    """صفحه‌بندی لیست ادمین‌ها (admin_admins_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_admins_page(chat_id, user_id, data)


# ========== روت‌های مدیریت کاربران (اصلی) ==========

@route("admin_users")
async def admin_users(update):
    """نمایش منوی اصلی مدیریت کاربران"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_management(chat_id, user_id)


@route("admin_users_list")
async def admin_users_list(update):
    """نمایش لیست کاربران با صفحه‌بندی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_list(chat_id, user_id, 0)


@route("admin_users_list_page_")
async def admin_users_list_page(update):
    """صفحه‌بندی لیست کاربران (admin_users_list_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_list_page(chat_id, user_id, data)


@route("admin_user_detail_")
async def admin_user_detail(update):
    """نمایش جزئیات کامل یک کاربر (admin_user_detail_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_detail(chat_id, user_id, data)


@route("admin_users_stats")
async def admin_users_stats(update):
    """نمایش آمار کلی کاربران"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_stats(chat_id, user_id)


@route("admin_users_search")
async def admin_users_search(update):
    """شروع فرآیند جستجوی کاربران"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_search(chat_id, user_id)


# روت admin_orders_user_ حذف شد - این روت در order_routes.py تعریف شده است

@route("admin_user_unblock_")
async def admin_user_unblock_from_list(update):
    """رفع مسدودیت کاربر از لیست کاربران (admin_user_unblock_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_unblock_from_list(chat_id, user_id, data)


# ========== روت‌های مدیریت پیشرفته کاربران (مسدودیت، پیام انبوه، فعالیت) ==========

@route("admin_user_actions")
async def admin_user_actions(update):
    """نمایش منوی اصلی مدیریت پیشرفته کاربران"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_actions(chat_id, user_id)


@route("admin_user_block_list")
async def admin_user_block_list(update):
    """نمایش لیست کاربران مسدود شده"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_block_list(chat_id, user_id, 0)


@route("admin_user_block_list_page_")
async def admin_user_block_list_page(update):
    """صفحه‌بندی لیست کاربران مسدود شده"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_block_list_page(chat_id, user_id, data)


@route("admin_user_block_detail_")
async def admin_user_block_detail(update):
    """نمایش جزئیات یک کاربر مسدود شده (admin_user_block_detail_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_block_detail(chat_id, user_id, data)


@route("admin_user_block_")
async def admin_user_block(update):
    """مسدود کردن یک کاربر (admin_user_block_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_block(chat_id, user_id, data)


@route("admin_user_unblock_")
async def admin_user_unblock(update):
    """رفع مسدودیت کاربر (admin_user_unblock_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_unblock(chat_id, user_id, data)


@route("admin_user_activity_search")
async def admin_user_activity_search(update):
    """شروع جستجوی کاربر برای مشاهده فعالیت"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_activity_search(chat_id, user_id)


@route("admin_user_activity_")
async def admin_user_activity(update):
    """نمایش فعالیت کامل یک کاربر (admin_user_activity_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await show_user_activity(chat_id, user_id, data)


@route("admin_user_errors_")
async def admin_user_errors(update):
    """نمایش خطاهای یک کاربر (admin_user_errors_<user_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_errors(chat_id, user_id, data)


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
    return await handle_broadcast_send(chat_id, user_id, target_type)


@route("admin_user_actions_stats")
async def admin_user_actions_stats(update):
    """نمایش آمار کامل کاربران"""
    chat_id, user_id, data = extract_params(update)
    return await handle_user_actions_stats(chat_id, user_id)


# ========== صادر کردن ==========

__all__ = [
    # مدیریت ادمین‌ها
    'admin_manage_admins',
    'admin_admin_detail',
    'admin_add_admin_start',
    'admin_add_admin_role',
    'admin_remove_admin',
    'admin_remove_confirm',
    'admin_change_role',
    'admin_change_role_select',
    'admin_toggle_status',
    'admin_search_admin',
    'admin_admins_stats',
    'admin_admins_page',
    
    # مدیریت کاربران
    'admin_users',
    'admin_users_list',
    'admin_users_list_page',
    'admin_user_detail',
    'admin_users_stats',
    'admin_users_search',
    # 'admin_orders_user',  <-- حذف شد
    'admin_user_unblock_from_list',
    
    # مدیریت پیشرفته کاربران
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