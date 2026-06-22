# admin_panel/advanced_search_routes.py
# ثبت روت‌های مربوط به جستجوی پیشرفته در پنل مدیریت
# شامل: منوی اصلی، جستجوی سریع، فیلترها، نمایش نتایج و خروجی

from .router import route, extract_params
from .advanced_search import (
    handle_advanced_search,
    handle_search_quick,
    handle_search_date,
    handle_search_amount,
    handle_search_status,
    handle_search_status_toggle,
    handle_search_status_apply,
    handle_search_status_clear,
    handle_search_service,
    handle_search_service_toggle,
    handle_search_service_page,
    handle_search_service_apply,
    handle_search_service_clear,
    handle_search_user,
    handle_search_tracking,
    handle_search_has_file,
    handle_search_reset,
    handle_search_results,
    handle_search_page,
    handle_search_order_detail,
    handle_search_export,
)
from core import send_message
from logger_config import logger


# ========== روت‌های اصلی جستجوی پیشرفته ==========

@route("admin_adv_search")
async def admin_adv_search(update):
    """نمایش منوی اصلی جستجوی پیشرفته"""
    chat_id, user_id, data = extract_params(update)
    return await handle_advanced_search(chat_id, user_id)


@route("admin_adv_search_quick")
async def admin_adv_search_quick(update):
    """جستجوی سریع با کلمه کلیدی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_quick(chat_id, user_id)


@route("admin_adv_search_date")
async def admin_adv_search_date(update):
    """جستجو بر اساس تاریخ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_date(chat_id, user_id)


@route("admin_adv_search_amount")
async def admin_adv_search_amount(update):
    """جستجو بر اساس مبلغ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_amount(chat_id, user_id)


@route("admin_adv_search_status")
async def admin_adv_search_status(update):
    """جستجو بر اساس وضعیت"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_status(chat_id, user_id)


@route("admin_adv_search_status_toggle_")
async def admin_adv_search_status_toggle(update):
    """تغییر انتخاب یک وضعیت (admin_adv_search_status_toggle_<status>)"""
    chat_id, user_id, data = extract_params(update)
    status = data.split("_")[-1]
    return await handle_search_status_toggle(chat_id, user_id, status)


@route("admin_adv_search_status_apply")
async def admin_adv_search_status_apply(update):
    """اعمال فیلتر وضعیت"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_status_apply(chat_id, user_id)


@route("admin_adv_search_status_clear")
async def admin_adv_search_status_clear(update):
    """پاک کردن فیلتر وضعیت"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_status_clear(chat_id, user_id)


@route("admin_adv_search_service")
async def admin_adv_search_service(update):
    """جستجو بر اساس سرویس"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_service(chat_id, user_id, 0)


@route("admin_adv_search_service_toggle_")
async def admin_adv_search_service_toggle(update):
    """تغییر انتخاب یک سرویس (admin_adv_search_service_toggle_<service_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        service_id = int(data.split("_")[-1])
        return await handle_search_service_toggle(chat_id, user_id, service_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه سرویس نامعتبر.")
        return True


@route("admin_adv_search_service_page_")
async def admin_adv_search_service_page(update):
    """صفحه‌بندی سرویس‌ها (admin_adv_search_service_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        page = int(data.split("_")[-1])
        return await handle_search_service_page(chat_id, user_id, page)
    except ValueError:
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True


@route("admin_adv_search_service_apply")
async def admin_adv_search_service_apply(update):
    """اعمال فیلتر سرویس"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_service_apply(chat_id, user_id)


@route("admin_adv_search_service_clear")
async def admin_adv_search_service_clear(update):
    """پاک کردن فیلتر سرویس"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_service_clear(chat_id, user_id)


@route("admin_adv_search_user")
async def admin_adv_search_user(update):
    """جستجو بر اساس کاربر"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_user(chat_id, user_id)


@route("admin_adv_search_tracking")
async def admin_adv_search_tracking(update):
    """جستجو بر اساس کد رهگیری"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_tracking(chat_id, user_id)


@route("admin_adv_search_has_file")
async def admin_adv_search_has_file(update):
    """جستجوی سفارشات دارای فایل"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_has_file(chat_id, user_id)


@route("admin_adv_search_reset")
async def admin_adv_search_reset(update):
    """بازنشانی جستجو"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_reset(chat_id, user_id)


@route("admin_adv_search_results")
async def admin_adv_search_results(update):
    """نمایش نتایج جستجو"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_results(chat_id, user_id, 0)


@route("admin_adv_search_page_")
async def admin_adv_search_page(update):
    """صفحه‌بندی نتایج جستجو (admin_adv_search_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        page = int(data.split("_")[-1])
        return await handle_search_page(chat_id, user_id, page)
    except ValueError:
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True


@route("admin_adv_search_order_")
async def admin_adv_search_order(update):
    """نمایش جزئیات یک سفارش از نتایج جستجو (admin_adv_search_order_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        order_id = int(data.split("_")[-1])
        return await handle_search_order_detail(chat_id, user_id, order_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
        return True


@route("admin_adv_search_export")
async def admin_adv_search_export(update):
    """خروجی Excel از نتایج جستجو"""
    chat_id, user_id, data = extract_params(update)
    return await handle_search_export(chat_id, user_id)


# ========== صادر کردن ==========

__all__ = [
    'admin_adv_search',
    'admin_adv_search_quick',
    'admin_adv_search_date',
    'admin_adv_search_amount',
    'admin_adv_search_status',
    'admin_adv_search_status_toggle',
    'admin_adv_search_status_apply',
    'admin_adv_search_status_clear',
    'admin_adv_search_service',
    'admin_adv_search_service_toggle',
    'admin_adv_search_service_page',
    'admin_adv_search_service_apply',
    'admin_adv_search_service_clear',
    'admin_adv_search_user',
    'admin_adv_search_tracking',
    'admin_adv_search_has_file',
    'admin_adv_search_reset',
    'admin_adv_search_results',
    'admin_adv_search_page',
    'admin_adv_search_order',
    'admin_adv_search_export',
]