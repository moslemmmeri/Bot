# admin_panel/error_routes.py
# ثبت روت‌های مربوط به مدیریت خطاها و اعلان‌ها در پنل مدیریت
# شامل: لیست خطاها، جزئیات خطا، حل‌کردن، بازگشایی، حذف، آمار، پاکسازی و حذف همه

from .router import route, extract_params
from .error_management import (
    handle_error_management,
    handle_error_list,
    handle_error_detail,
    handle_error_resolve,
    handle_error_unresolve,
    handle_error_delete,
    handle_error_stats,
    handle_error_cleanup,
    handle_error_cleanup_confirm,
    handle_error_list_page,
    handle_error_clear_all,
    handle_error_clear_all_confirm,
)


# ========== روت‌های اصلی مدیریت خطاها ==========

@route("admin_errors")
async def admin_errors(update):
    """نمایش منوی اصلی مدیریت خطاها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_management(chat_id, user_id)


@route("admin_errors_list")
async def admin_errors_list(update):
    """نمایش لیست تمام خطاها با صفحه‌بندی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_list(chat_id, user_id, 0, False)


@route("admin_errors_list_unresolved")
async def admin_errors_list_unresolved(update):
    """نمایش لیست خطاهای حل‌نشده با صفحه‌بندی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_list(chat_id, user_id, 0, True)


@route("admin_errors_list_page_")
async def admin_errors_list_page(update):
    """صفحه‌بندی لیست خطاها (admin_errors_list_page_<page>_<type>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_list_page(chat_id, user_id, data)


# ========== روت‌های جزئیات و مدیریت خطا ==========

@route("admin_error_detail_")
async def admin_error_detail(update):
    """نمایش جزئیات کامل یک خطا (admin_error_detail_<error_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_detail(chat_id, user_id, data)


@route("admin_error_resolve_")
async def admin_error_resolve(update):
    """علامت‌گذاری خطا به عنوان حل‌شده (admin_error_resolve_<error_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_resolve(chat_id, user_id, data)


@route("admin_error_unresolve_")
async def admin_error_unresolve(update):
    """بازگشایی خطا (حل‌نشده) (admin_error_unresolve_<error_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_unresolve(chat_id, user_id, data)


@route("admin_error_delete_")
async def admin_error_delete(update):
    """حذف یک خطا (admin_error_delete_<error_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_delete(chat_id, user_id, data)


# ========== روت‌های آمار و پاکسازی خطاها ==========

@route("admin_errors_stats")
async def admin_errors_stats(update):
    """نمایش آمار خطاها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_stats(chat_id, user_id)


@route("admin_errors_cleanup")
async def admin_errors_cleanup(update):
    """نمایش تاییدیه پاکسازی خطاهای قدیمی (بیش از ۳۰ روز)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_cleanup(chat_id, user_id)


@route("admin_errors_cleanup_confirm")
async def admin_errors_cleanup_confirm(update):
    """اجرای پاکسازی خطاهای قدیمی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_cleanup_confirm(chat_id, user_id)


# ========== روت‌های حذف همه خطاها ==========

@route("admin_errors_clear_all")
async def admin_errors_clear_all(update):
    """نمایش تاییدیه برای حذف همه خطاها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_clear_all(chat_id, user_id)


@route("admin_errors_clear_all_confirm")
async def admin_errors_clear_all_confirm(update):
    """اجرای حذف همه خطاها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_error_clear_all_confirm(chat_id, user_id)


# ========== صادر کردن ==========

__all__ = [
    'admin_errors',
    'admin_errors_list',
    'admin_errors_list_unresolved',
    'admin_errors_list_page',
    'admin_error_detail',
    'admin_error_resolve',
    'admin_error_unresolve',
    'admin_error_delete',
    'admin_errors_stats',
    'admin_errors_cleanup',
    'admin_errors_cleanup_confirm',
    'admin_errors_clear_all',
    'admin_errors_clear_all_confirm',
]