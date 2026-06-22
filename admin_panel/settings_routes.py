# admin_panel/settings_routes.py
# ثبت روت‌های مربوط به تنظیمات در پنل مدیریت
# شامل: تنظیم مبلغ پیش‌فرض، تنظیم تعداد ستون‌های پیش‌فرض منو و سایر تنظیمات عمومی

from .router import route, extract_params
from .settings import (
    handle_settings,
    handle_set_price,
    handle_set_default_columns,
)


# ========== روت‌های اصلی تنظیمات ==========

@route("admin_settings")
async def admin_settings(update):
    """
    نمایش صفحه تنظیمات با گزینه‌های مدیریت
    نمایش مبلغ پیش‌فرض فعلی و تعداد ستون‌های پیش‌فرض
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_settings(chat_id, user_id)


@route("admin_set_price")
async def admin_set_price(update):
    """
    شروع فرآیند تنظیم مبلغ پیش‌فرض
    وضعیت کاربر را به admin_set_price تغییر می‌دهد
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_set_price(chat_id, user_id)


@route("admin_set_default_columns")
async def admin_set_default_columns(update):
    """
    شروع فرآیند تنظیم تعداد ستون‌های پیش‌فرض منو
    وضعیت کاربر را به admin_set_default_columns تغییر می‌دهد
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_set_default_columns(chat_id, user_id)


# ========== صادر کردن ==========

__all__ = [
    'admin_settings',
    'admin_set_price',
    'admin_set_default_columns',
]