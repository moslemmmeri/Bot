# admin_panel/versioning_routes.py
# ثبت روت‌های مربوط به نسخه‌سازی (Versioning) در پنل مدیریت
# شامل: منوی اصلی، لیست نسخه‌ها، ذخیره نسخه جدید، جزئیات نسخه، بازگردانی، حذف و پاکسازی

from .router import route, extract_params
from .versioning import (
    handle_versioning,
    handle_version_list,
    handle_version_list_btn,
    handle_version_list_page,
    handle_version_save,
    handle_version_save_btn,
    handle_version_save_skip,
    handle_version_detail,
    handle_version_restore,
    handle_version_restore_confirm,
    handle_version_delete,
    handle_version_cleanup,
    handle_version_cleanup_btn,
)


# ========== روت اصلی نسخه‌سازی ==========

@route("admin_version")
async def admin_version(update):
    """نمایش منوی اصلی نسخه‌سازی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_versioning(chat_id, user_id)


# ========== روت‌های لیست نسخه‌ها ==========

@route("admin_version_list")
async def admin_version_list(update):
    """نمایش لیست دکمه‌ها برای انتخاب و مشاهده‌ی نسخه‌ها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_list(chat_id, user_id)


@route("admin_version_list_btn_")
async def admin_version_list_btn(update):
    """نمایش لیست نسخه‌های یک دکمه خاص"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_list_btn(chat_id, user_id, data)


@route("admin_version_list_page_")
async def admin_version_list_page(update):
    """صفحه‌بندی لیست نسخه‌ها (admin_version_list_page_<button_id>_<page>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_list_page(chat_id, user_id, data)


# ========== روت‌های ذخیره نسخه جدید ==========

@route("admin_version_save")
async def admin_version_save(update):
    """شروع فرآیند ذخیره نسخه جدید - نمایش لیست دکمه‌ها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_save(chat_id, user_id)


@route("admin_version_save_btn_")
async def admin_version_save_btn(update):
    """انتخاب دکمه برای ذخیره نسخه (admin_version_save_btn_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_save_btn(chat_id, user_id, data)


@route("admin_version_save_skip_")
async def admin_version_save_skip(update):
    """ذخیره نسخه بدون یادداشت (admin_version_save_skip_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_save_skip(chat_id, user_id, data)


# ========== روت‌های جزئیات نسخه ==========

@route("admin_version_detail_")
async def admin_version_detail(update):
    """نمایش جزئیات یک نسخه (admin_version_detail_<button_id>_<version_number>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_detail(chat_id, user_id, data)


# ========== روت‌های بازگردانی (Rollback) ==========

@route("admin_version_restore_")
async def admin_version_restore(update):
    """نمایش تاییدیه بازگردانی به نسخه (admin_version_restore_<button_id>_<version_number>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_restore(chat_id, user_id, data)


@route("admin_version_restore_confirm_")
async def admin_version_restore_confirm(update):
    """اجرای بازگردانی به نسخه (admin_version_restore_confirm_<button_id>_<version_number>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_restore_confirm(chat_id, user_id, data)


# ========== روت‌های حذف نسخه ==========

@route("admin_version_delete_")
async def admin_version_delete(update):
    """حذف یک نسخه (admin_version_delete_<button_id>_<version_number>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_delete(chat_id, user_id, data)


# ========== روت‌های پاکسازی نسخه‌های قدیمی ==========

@route("admin_version_cleanup")
async def admin_version_cleanup(update):
    """نمایش لیست دکمه‌ها برای پاکسازی نسخه‌های قدیمی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_cleanup(chat_id, user_id)


@route("admin_version_cleanup_btn_")
async def admin_version_cleanup_btn(update):
    """اجرای پاکسازی نسخه‌های قدیمی یک دکمه (admin_version_cleanup_btn_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_version_cleanup_btn(chat_id, user_id, data)


# ========== صادر کردن ==========

__all__ = [
    'admin_version',
    'admin_version_list',
    'admin_version_list_btn',
    'admin_version_list_page',
    'admin_version_save',
    'admin_version_save_btn',
    'admin_version_save_skip',
    'admin_version_detail',
    'admin_version_restore',
    'admin_version_restore_confirm',
    'admin_version_delete',
    'admin_version_cleanup',
    'admin_version_cleanup_btn',
]