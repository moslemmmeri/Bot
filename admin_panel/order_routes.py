# admin_panel/order_routes.py
# ثبت روت‌های مربوط به مدیریت سفارشات در پنل مدیریت
# شامل: گروه‌بندی سفارشات، فیلتر، جستجو، تغییر وضعیت، حذف، یادداشت، آمار و خروجی Excel
# همچنین یادآوری سفارشات ناتمام

from .router import route, extract_params
from .orders import (
    # توابع اصلی گروه‌بندی
    handle_orders_list,
    handle_orders_group_by_date,
    handle_orders_date_page,
    handle_orders_date,
    handle_orders_service_page,
    handle_orders_service_back,
    handle_orders_service,
    handle_orders_user_page,
    handle_orders_user,
    handle_order_by_id,
    # توابع فیلتر
    handle_orders_filter_start,
    handle_orders_filter_status,
    handle_orders_filter_service,
    handle_orders_filter_service_select,
    handle_orders_filter_apply,
    handle_orders_filter_clear,
    # توابع جستجو و آمار
    handle_orders_search,
    handle_orders_search_result,
    handle_orders_stats,
    handle_orders_export,
    # توابع تغییر وضعیت، حذف و یادداشت
    handle_order_status_change,
    handle_order_status_change_confirm,
    handle_order_delete,
    handle_order_delete_confirm,
    handle_order_note,
    handle_order_note_add,
    handle_order_detail,
    # توابع یادآوری
    handle_order_reminder,
    handle_order_remind_single,
    handle_order_remind_all,
)
from core import send_message
from logger_config import logger
from utils.error_handler import log_callback_error


# ========== روت‌های اصلی مدیریت سفارشات ==========

@route("admin_orders")
async def admin_orders(update):
    """منوی اصلی سفارشات"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_list(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_orders: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش منوی سفارشات.")
        return True


@route("admin_orders_group_by_date")
async def admin_orders_group_by_date(update):
    """گروه‌بندی سفارشات بر اساس تاریخ"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_group_by_date(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_group_by_date: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در گروه‌بندی سفارشات.")
        return True


# ========== روت‌های گروه‌بندی ==========

@route("admin_orders_date_page_")
async def admin_orders_date_page(update):
    """صفحه‌بندی تاریخ‌ها (admin_orders_date_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_date_page(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_date_page: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در صفحه‌بندی تاریخ‌ها.")
        return True


@route("admin_orders_date_")
async def admin_orders_date(update):
    """انتخاب تاریخ و نمایش سرویس‌های آن (admin_orders_date_<date>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_date(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_date: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش سرویس‌های تاریخ.")
        return True


@route("admin_orders_service_page_")
async def admin_orders_service_page(update):
    """صفحه‌بندی سرویس‌ها (admin_orders_service_page_<date>_<page>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_service_page(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_service_page: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در صفحه‌بندی سرویس‌ها.")
        return True


@route("admin_orders_service_back_")
async def admin_orders_service_back(update):
    """بازگشت از مرحله سرویس به تاریخ‌ها (admin_orders_service_back_<date>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_service_back(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_service_back: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در بازگشت به تاریخ‌ها.")
        return True


@route("admin_orders_service_")
async def admin_orders_service(update):
    """انتخاب سرویس و نمایش کاربران آن (admin_orders_service_<date>_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_service(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_service: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش کاربران سرویس.")
        return True


@route("admin_orders_user_page_")
async def admin_orders_user_page(update):
    """صفحه‌بندی کاربران (admin_orders_user_page_<date>_<button_id>_<page>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_user_page(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_user_page: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در صفحه‌بندی کاربران.")
        return True


@route("admin_orders_user_")
async def admin_orders_user(update):
    """انتخاب کاربر و نمایش جزئیات سفارش (admin_orders_user_<date>_<button_id>_<fullname>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_user(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_user: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش کاربر.")
        return True


@route("admin_order_")
async def admin_order(update):
    """نمایش جزئیات سفارش با شناسه (admin_order_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_order_by_id(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_order: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
        return True


# ========== روت‌های فیلتر سفارشات ==========

@route("admin_orders_filter")
async def admin_orders_filter(update):
    """شروع فیلتر سفارشات"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_filter_start(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_filter: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در شروع فیلتر.")
        return True


@route("admin_orders_filter_status_")
async def admin_orders_filter_status(update):
    """انتخاب وضعیت برای فیلتر (admin_orders_filter_status_<status>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_filter_status(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_filter_status: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در انتخاب وضعیت.")
        return True


@route("admin_orders_filter_service")
async def admin_orders_filter_service(update):
    """نمایش لیست سرویس‌ها برای انتخاب فیلتر"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_filter_service(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_filter_service: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش سرویس‌ها.")
        return True


@route("admin_orders_filter_service_")
async def admin_orders_filter_service_select(update):
    """انتخاب سرویس برای فیلتر (admin_orders_filter_service_<service_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_filter_service_select(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_filter_service_select: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در انتخاب سرویس.")
        return True


@route("admin_orders_filter_apply")
async def admin_orders_filter_apply(update):
    """اعمال فیلترهای انتخاب‌شده و نمایش نتایج"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_filter_apply(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_filter_apply: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در اعمال فیلتر.")
        return True


@route("admin_orders_filter_clear")
async def admin_orders_filter_clear(update):
    """پاک کردن فیلترها"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_filter_clear(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_filter_clear: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در پاک کردن فیلتر.")
        return True


# ========== روت‌های جستجو و آمار ==========

@route("admin_orders_search")
async def admin_orders_search(update):
    """شروع جستجوی سفارشات"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_search(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_search: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در شروع جستجو.")
        return True


@route("admin_orders_stats")
async def admin_orders_stats(update):
    """نمایش آمار سفارشات"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_stats(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_stats: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش آمار.")
        return True


@route("admin_orders_export")
async def admin_orders_export(update):
    """خروجی Excel از همه سفارشات"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_export(chat_id, user_id, filtered=False)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_export: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در خروجی Excel.")
        return True


@route("admin_orders_export_filtered")
async def admin_orders_export_filtered(update):
    """خروجی Excel از سفارشات فیلتر شده"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_orders_export(chat_id, user_id, filtered=True)
    except Exception as e:
        log_callback_error(f"Error in admin_orders_export_filtered: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در خروجی Excel.")
        return True


# ========== روت‌های تغییر وضعیت، حذف و یادداشت سفارش ==========

@route("admin_order_status_")
async def admin_order_status(update):
    """شروع تغییر وضعیت سفارش (admin_order_status_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_order_status_change(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_order_status: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در شروع تغییر وضعیت.")
        return True


@route("admin_order_status_change_")
async def admin_order_status_change(update):
    """اعمال تغییر وضعیت سفارش (admin_order_status_change_<order_id>_<new_status>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_order_status_change_confirm(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_order_status_change: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در تغییر وضعیت.")
        return True


@route("admin_order_delete_")
async def admin_order_delete(update):
    """نمایش تایید حذف سفارش (admin_order_delete_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_order_delete(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_order_delete: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در شروع حذف.")
        return True


@route("admin_order_delete_yes_")
async def admin_order_delete_yes(update):
    """اجرای حذف سفارش (admin_order_delete_yes_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_order_delete_confirm(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_order_delete_yes: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در حذف سفارش.")
        return True


@route("admin_order_note_")
async def admin_order_note(update):
    """شروع افزودن یادداشت به سفارش (admin_order_note_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_order_note(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_order_note: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در شروع افزودن یادداشت.")
        return True


# ========== روت‌های یادآوری سفارشات ==========

@route("admin_order_reminder")
async def admin_order_reminder(update):
    """نمایش لیست سفارشات نیازمند یادآوری"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_order_reminder(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_order_reminder: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش یادآوری‌ها.")
        return True


@route("admin_order_remind_")
async def admin_order_remind_single(update):
    """ارسال یادآوری برای یک سفارش خاص (admin_order_remind_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_order_remind_single(chat_id, user_id, data)
    except Exception as e:
        log_callback_error(f"Error in admin_order_remind_single: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در ارسال یادآوری.")
        return True


@route("admin_order_remind_all")
async def admin_order_remind_all(update):
    """ارسال یادآوری به همه سفارشات ناتمام"""
    chat_id, user_id, data = extract_params(update)
    try:
        return await handle_order_remind_all(chat_id, user_id)
    except Exception as e:
        log_callback_error(f"Error in admin_order_remind_all: {e}", traceback=str(e), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در ارسال یادآوری گروهی.")
        return True


# ========== صادر کردن ==========

__all__ = [
    'admin_orders',
    'admin_orders_group_by_date',
    'admin_orders_date_page',
    'admin_orders_date',
    'admin_orders_service_page',
    'admin_orders_service_back',
    'admin_orders_service',
    'admin_orders_user_page',
    'admin_orders_user',
    'admin_order',
    'admin_orders_filter',
    'admin_orders_filter_status',
    'admin_orders_filter_service',
    'admin_orders_filter_service_select',
    'admin_orders_filter_apply',
    'admin_orders_filter_clear',
    'admin_orders_search',
    'admin_orders_stats',
    'admin_orders_export',
    'admin_orders_export_filtered',
    'admin_order_status',
    'admin_order_status_change',
    'admin_order_delete',
    'admin_order_delete_yes',
    'admin_order_note',
    'admin_order_reminder',
    'admin_order_remind_single',
    'admin_order_remind_all',
]