# admin_panel/backup_routes.py
# ثبت روت‌های مربوط به پشتیبان‌گیری (Backup) در پنل مدیریت
# شامل: ایجاد پشتیبان جدید، لیست پشتیبان‌ها، دانلود، حذف، بازیابی و پاکسازی

from .router import route, extract_params
from .backup import (
    handle_backup,
    handle_backup_create,
    handle_backup_list,
    handle_backup_download,
    handle_backup_delete,
    handle_backup_restore_start,
    handle_backup_restore_confirm,
    handle_backup_cleanup,
    handle_backup_cleanup_confirm,
    handle_backup_list_page,
)
from core import send_message
from logger_config import logger


# ========== روت‌های اصلی پشتیبان‌گیری ==========

@route("admin_backup")
async def admin_backup(update):
    """نمایش منوی اصلی بخش پشتیبان‌گیری"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup(chat_id, user_id)


@route("admin_backup_create")
async def admin_backup_create(update):
    """ایجاد یک فایل پشتیبان جدید و ارسال آن به کاربر"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup_create(chat_id, user_id)


@route("admin_backup_list")
async def admin_backup_list(update):
    """نمایش لیست فایل‌های پشتیبان موجود"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup_list(chat_id, user_id, 0)


@route("admin_backup_list_page_")
async def admin_backup_list_page(update):
    """صفحه‌بندی لیست پشتیبان‌ها (admin_backup_list_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup_list_page(chat_id, user_id, data)


@route("admin_backup_download_")
async def admin_backup_download(update):
    """دانلود یک فایل پشتیبان خاص (admin_backup_download_<filename>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup_download(chat_id, user_id, data)


@route("admin_backup_delete_")
async def admin_backup_delete(update):
    """حذف یک فایل پشتیبان (admin_backup_delete_<filename>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup_delete(chat_id, user_id, data)


@route("admin_backup_restore")
async def admin_backup_restore(update):
    """شروع فرآیند بازیابی دیتابیس از فایل پشتیبان"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup_restore_start(chat_id, user_id)


@route("admin_backup_restore_confirm_")
async def admin_backup_restore_confirm(update):
    """تایید نهایی بازیابی از فایل پشتیبان (admin_backup_restore_confirm_<filename>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup_restore_confirm(chat_id, user_id, data)


@route("admin_backup_cleanup")
async def admin_backup_cleanup(update):
    """پاکسازی دستی پشتیبان‌های قدیمی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup_cleanup(chat_id, user_id)


@route("admin_backup_cleanup_confirm")
async def admin_backup_cleanup_confirm(update):
    """تایید و اجرای پاکسازی پشتیبان‌های قدیمی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_backup_cleanup_confirm(chat_id, user_id)


# ========== صادر کردن ==========

__all__ = [
    'admin_backup',
    'admin_backup_create',
    'admin_backup_list',
    'admin_backup_list_page',
    'admin_backup_download',
    'admin_backup_delete',
    'admin_backup_restore',
    'admin_backup_restore_confirm',
    'admin_backup_cleanup',
    'admin_backup_cleanup_confirm',
]