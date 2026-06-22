# admin_panel/column_routes.py
# ثبت روت‌های مربوط به مدیریت پیشرفته ستون‌های منو در پنل مدیریت
# شامل: منوی اصلی، مدیریت دسته‌بندی‌ها، مدیریت دکمه‌ها، پیش‌نمایش، تنظیم سریع و بازنشانی

from .router import route, extract_params
from .column_management import (
    handle_column_management,
    handle_column_category_list,
    handle_column_category_edit,
    handle_column_category_set,
    handle_column_button_list,
    handle_column_button_edit,
    handle_column_button_set,
    handle_column_preview,
    handle_column_quick_set,
    handle_column_reset,
    handle_column_reset_confirm,
    handle_column_set_default,
)


# ========== روت‌های اصلی مدیریت ستون‌ها ==========

@route("admin_columns")
async def admin_columns(update):
    """نمایش منوی اصلی مدیریت پیشرفته ستون‌ها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_management(chat_id, user_id)


# ========== روت‌های مدیریت دسته‌بندی‌ها ==========

@route("admin_col_cat_list")
async def admin_col_cat_list(update):
    """نمایش لیست دسته‌بندی‌ها برای مدیریت ستون‌ها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_category_list(chat_id, user_id)


@route("admin_col_cat_edit_")
async def admin_col_cat_edit(update):
    """نمایش صفحه ویرایش ستون‌های یک دسته‌بندی (admin_col_cat_edit_<category_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_category_edit(chat_id, user_id, data)


@route("admin_col_cat_set_")
async def admin_col_cat_set(update):
    """تنظیم ستون‌های یک دسته‌بندی (admin_col_cat_set_<category_id>_<columns>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_category_set(chat_id, user_id, data)


# ========== روت‌های مدیریت دکمه‌ها ==========

@route("admin_col_btn_list")
async def admin_col_btn_list(update):
    """نمایش لیست دکمه‌ها برای مدیریت ستون‌ها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_button_list(chat_id, user_id)


@route("admin_col_btn_edit_")
async def admin_col_btn_edit(update):
    """نمایش صفحه ویرایش ستون‌های یک دکمه (admin_col_btn_edit_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_button_edit(chat_id, user_id, data)


@route("admin_col_btn_set_")
async def admin_col_btn_set(update):
    """تنظیم ستون‌های یک دکمه (admin_col_btn_set_<button_id>_<columns>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_button_set(chat_id, user_id, data)


# ========== روت‌های پیش‌نمایش ==========

@route("admin_col_preview_")
async def admin_col_preview(update):
    """نمایش پیش‌نمایش یک دسته‌بندی با تعداد ستون‌های مشخص (admin_col_preview_<category_id>_<columns>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_preview(chat_id, user_id, data)


# ========== روت‌های تنظیم سریع و بازنشانی ==========

@route("admin_col_quick_")
async def admin_col_quick(update):
    """تنظیم سریع ستون‌ها با یک کلیک (admin_col_quick_<columns>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_quick_set(chat_id, user_id, data)


@route("admin_col_reset")
async def admin_col_reset(update):
    """نمایش تاییدیه بازنشانی همه تنظیمات ستون‌ها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_reset(chat_id, user_id)


@route("admin_col_reset_confirm")
async def admin_col_reset_confirm(update):
    """اجرای بازنشانی همه تنظیمات ستون‌ها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_reset_confirm(chat_id, user_id)


@route("admin_col_set_default_")
async def admin_col_set_default(update):
    """تنظیم مستقیم پیش‌فرض عمومی (admin_col_set_default_<columns>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_column_set_default(chat_id, user_id, data)


# ========== صادر کردن ==========

__all__ = [
    'admin_columns',
    'admin_col_cat_list',
    'admin_col_cat_edit',
    'admin_col_cat_set',
    'admin_col_btn_list',
    'admin_col_btn_edit',
    'admin_col_btn_set',
    'admin_col_preview',
    'admin_col_quick',
    'admin_col_reset',
    'admin_col_reset_confirm',
    'admin_col_set_default',
]