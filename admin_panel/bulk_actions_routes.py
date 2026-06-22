# admin_panel/bulk_actions_routes.py
# ثبت روت‌های مربوط به عملیات گروهی (Bulk Actions) در پنل مدیریت
# شامل: انتخاب سفارشات، تغییر وضعیت گروهی، حذف گروهی، خروجی گروهی

from .router import route, extract_params
from .bulk_actions import (
    handle_bulk_actions,
    handle_bulk_select,
    handle_bulk_toggle,
    handle_bulk_select_all,
    handle_bulk_select_none,
    handle_bulk_select_page,
    handle_bulk_status,
    handle_bulk_status_set,
    handle_bulk_delete,
    handle_bulk_delete_confirm,
    handle_bulk_export,
    handle_bulk_export_excel,
    handle_bulk_export_csv,
    handle_bulk_export_json,
)
from core import send_message
from logger_config import logger


# ========== روت‌های اصلی Bulk Actions ==========

@route("admin_bulk_actions")
async def admin_bulk_actions(update):
    """نمایش منوی اصلی Bulk Actions"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_actions(chat_id, user_id)


@route("admin_bulk_select")
async def admin_bulk_select(update):
    """نمایش صفحه انتخاب سفارشات برای عملیات گروهی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_select(chat_id, user_id, 0)


@route("admin_bulk_toggle_")
async def admin_bulk_toggle(update):
    """تغییر انتخاب یک سفارش (admin_bulk_toggle_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        order_id = int(data.split("_")[-1])
        return await handle_bulk_toggle(chat_id, user_id, order_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
        return True


@route("admin_bulk_select_all")
async def admin_bulk_select_all(update):
    """انتخاب همه سفارشات"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_select_all(chat_id, user_id)


@route("admin_bulk_select_none")
async def admin_bulk_select_none(update):
    """لغو انتخاب همه سفارشات"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_select_none(chat_id, user_id)


@route("admin_bulk_select_page_")
async def admin_bulk_select_page(update):
    """صفحه‌بندی انتخاب سفارشات (admin_bulk_select_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_select
    try:
        page = int(data.split("_")[-1])
        return await handle_bulk_select(chat_id, user_id, page)
    except ValueError:
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True


@route("admin_bulk_status")
async def admin_bulk_status(update):
    """نمایش صفحه انتخاب وضعیت برای تغییر گروهی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_status(chat_id, user_id)


@route("admin_bulk_status_set_")
async def admin_bulk_status_set(update):
    """اعمال تغییر وضعیت گروهی (admin_bulk_status_set_<status>)"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_status_set
    new_status = data.split("_")[-1]
    return await handle_bulk_status_set(chat_id, user_id, new_status)


@route("admin_bulk_delete")
async def admin_bulk_delete(update):
    """نمایش تاییدیه حذف گروهی سفارشات"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_delete(chat_id, user_id)


@route("admin_bulk_delete_confirm")
async def admin_bulk_delete_confirm(update):
    """اجرای حذف گروهی سفارشات"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_delete_confirm(chat_id, user_id)


@route("admin_bulk_export")
async def admin_bulk_export(update):
    """نمایش صفحه انتخاب نوع خروجی گروهی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_export(chat_id, user_id)


@route("admin_bulk_export_excel")
async def admin_bulk_export_excel(update):
    """خروجی Excel از سفارشات انتخاب‌شده"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_export_excel(chat_id, user_id)


@route("admin_bulk_export_csv")
async def admin_bulk_export_csv(update):
    """خروجی CSV از سفارشات انتخاب‌شده"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_export_csv(chat_id, user_id)


@route("admin_bulk_export_json")
async def admin_bulk_export_json(update):
    """خروجی JSON از سفارشات انتخاب‌شده"""
    chat_id, user_id, data = extract_params(update)
    return await handle_bulk_export_json(chat_id, user_id)


# ========== صادر کردن ==========

__all__ = [
    'admin_bulk_actions',
    'admin_bulk_select',
    'admin_bulk_toggle',
    'admin_bulk_select_all',
    'admin_bulk_select_none',
    'admin_bulk_select_page',
    'admin_bulk_status',
    'admin_bulk_status_set',
    'admin_bulk_delete',
    'admin_bulk_delete_confirm',
    'admin_bulk_export',
    'admin_bulk_export_excel',
    'admin_bulk_export_csv',
    'admin_bulk_export_json',
]