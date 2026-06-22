# admin_panel/branding_routes.py
# ثبت روت‌های مربوط به شخصی‌سازی ظاهر و برندینگ در پنل مدیریت
# شامل: مدیریت متون برندینگ، ویرایش، مشاهده، بازنشانی به پیش‌فرض

from .router import route, extract_params
from .branding import (
    handle_branding,
    handle_branding_view,
    handle_branding_edit,
    handle_branding_edit_field,
    handle_branding_reset,
    handle_branding_reset_confirm,
)


# ========== روت‌های اصلی برندینگ ==========

@route("admin_branding")
async def admin_branding(update):
    """نمایش منوی اصلی بخش برندینگ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_branding(chat_id, user_id)


@route("admin_branding_edit")
async def admin_branding_edit(update):
    """نمایش لیست بخش‌های قابل ویرایش برندینگ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_branding_edit(chat_id, user_id)


@route("admin_branding_edit_")
async def admin_branding_edit_field(update):
    """شروع ویرایش یک فیلد خاص برندینگ (admin_branding_edit_<field>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_branding_edit_field(chat_id, user_id, data)


@route("admin_branding_view")
async def admin_branding_view(update):
    """نمایش تمام متون برندینگ فعلی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_branding_view(chat_id, user_id)


@route("admin_branding_reset")
async def admin_branding_reset(update):
    """نمایش تاییدیه بازنشانی به پیش‌فرض"""
    chat_id, user_id, data = extract_params(update)
    return await handle_branding_reset(chat_id, user_id)


@route("admin_branding_reset_confirm")
async def admin_branding_reset_confirm(update):
    """اجرای بازنشانی متون به پیش‌فرض"""
    chat_id, user_id, data = extract_params(update)
    return await handle_branding_reset_confirm(chat_id, user_id)


# ========== صادر کردن ==========

__all__ = [
    'admin_branding',
    'admin_branding_edit',
    'admin_branding_edit_field',
    'admin_branding_view',
    'admin_branding_reset',
    'admin_branding_reset_confirm',
]