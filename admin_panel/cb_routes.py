# admin_panel/cb_routes.py
# مسیریاب اصلی کالبک‌های پنل ادمین - نسخه کامل
# شامل روت‌های جدید مدیریت فایل لاگ (log_viewer)

import traceback
from .router import route, handle_admin_callback, extract_params
from core import send_message
from keyboards import admin_main_keyboard
from utils.error_handler import log_general_error

# ========== import فایل‌های روت برای ثبت خودکار روت‌ها ==========
# با import کردن این فایل‌ها، دکوراتور @route اجرا شده و روت‌ها در ROUTES ثبت می‌شوند
from . import btn_routes
from . import q_routes
from . import order_routes
from . import user_admin_routes
from . import analytics_routes
from . import backup_routes
from . import branding_routes
from . import versioning_routes
from . import error_routes
from . import settings_routes
from . import column_routes
from . import template_routes
from . import bulk_actions_routes
from . import advanced_search_routes

# ========== روت‌های جدید مدیریت فایل لاگ ==========
from .log_viewer import (
    handle_log_viewer,
    handle_log_view,
    handle_log_clear,
    handle_log_clear_confirm,
)


# ========== روت‌های اصلی ==========

@route("admin_panel")
async def show_admin_panel(update):
    """نمایش منوی اصلی پنل مدیریت"""
    chat_id, user_id, data = extract_params(update)
    admin_title = "🔐 **پنل مدیریت ربات**\nلطفاً یکی از گزینه‌ها را انتخاب کنید:"
    await send_message(chat_id, admin_title, admin_main_keyboard())
    return True


@route("admin_back")
async def admin_back(update):
    """بازگشت به منوی اصلی پنل مدیریت"""
    chat_id, user_id, data = extract_params(update)
    await send_message(chat_id, "🔐 **پنل مدیریت**", admin_main_keyboard())
    return True


@route("admin_none")
async def admin_none(update):
    """دکمه خالی برای مواردی که هیچ عملیاتی ندارند"""
    chat_id, user_id, data = extract_params(update)
    # فقط یک پاسخ ساده بدون تغییر وضعیت
    return True


# ========== روت‌های بخش مدیریت پیشرفته کاربران ==========
# این روت‌ها در user_admin_routes.py تعریف شده‌اند
# اما برای اطمینان از ثبت، مجدداً import می‌کنیم


# ========== روت‌های بخش Bulk Actions ==========

@route("admin_bulk_actions")
async def admin_bulk_actions(update):
    """نمایش منوی اصلی Bulk Actions"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_actions
    return await handle_bulk_actions(chat_id, user_id)


@route("admin_bulk_select")
async def admin_bulk_select(update):
    """نمایش صفحه انتخاب سفارشات برای عملیات گروهی"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_select
    return await handle_bulk_select(chat_id, user_id, 0)


@route("admin_bulk_toggle_")
async def admin_bulk_toggle(update):
    """تغییر انتخاب یک سفارش (admin_bulk_toggle_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_toggle
    try:
        order_id = int(data.split("_")[-1])
        return await handle_bulk_toggle(chat_id, user_id, order_id)
    except ValueError:
        log_general_error(
            f"Invalid order_id in admin_bulk_toggle: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
        return True


@route("admin_bulk_select_all")
async def admin_bulk_select_all(update):
    """انتخاب همه سفارشات"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_select_all
    return await handle_bulk_select_all(chat_id, user_id)


@route("admin_bulk_select_none")
async def admin_bulk_select_none(update):
    """لغو انتخاب همه سفارشات"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_select_none
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
        log_general_error(
            f"Invalid page in admin_bulk_select_page: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True


@route("admin_bulk_status")
async def admin_bulk_status(update):
    """نمایش صفحه انتخاب وضعیت برای تغییر گروهی"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_status
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
    from .bulk_actions import handle_bulk_delete
    return await handle_bulk_delete(chat_id, user_id)


@route("admin_bulk_delete_confirm")
async def admin_bulk_delete_confirm(update):
    """اجرای حذف گروهی سفارشات"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_delete_confirm
    return await handle_bulk_delete_confirm(chat_id, user_id)


@route("admin_bulk_export")
async def admin_bulk_export(update):
    """نمایش صفحه انتخاب نوع خروجی گروهی"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_export
    return await handle_bulk_export(chat_id, user_id)


@route("admin_bulk_export_excel")
async def admin_bulk_export_excel(update):
    """خروجی Excel از سفارشات انتخاب‌شده"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_export_excel
    return await handle_bulk_export_excel(chat_id, user_id)


@route("admin_bulk_export_csv")
async def admin_bulk_export_csv(update):
    """خروجی CSV از سفارشات انتخاب‌شده"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_export_csv
    return await handle_bulk_export_csv(chat_id, user_id)


@route("admin_bulk_export_json")
async def admin_bulk_export_json(update):
    """خروجی JSON از سفارشات انتخاب‌شده"""
    chat_id, user_id, data = extract_params(update)
    from .bulk_actions import handle_bulk_export_json
    return await handle_bulk_export_json(chat_id, user_id)


# ========== روت‌های بخش جستجوی پیشرفته ==========

@route("admin_adv_search")
async def admin_adv_search(update):
    """نمایش منوی اصلی جستجوی پیشرفته"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_advanced_search
    return await handle_advanced_search(chat_id, user_id)


@route("admin_adv_search_quick")
async def admin_adv_search_quick(update):
    """جستجوی سریع با کلمه کلیدی"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_quick
    return await handle_search_quick(chat_id, user_id)


@route("admin_adv_search_date")
async def admin_adv_search_date(update):
    """جستجو بر اساس تاریخ"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_date
    return await handle_search_date(chat_id, user_id)


@route("admin_adv_search_amount")
async def admin_adv_search_amount(update):
    """جستجو بر اساس مبلغ"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_amount
    return await handle_search_amount(chat_id, user_id)


@route("admin_adv_search_status")
async def admin_adv_search_status(update):
    """جستجو بر اساس وضعیت"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_status
    return await handle_search_status(chat_id, user_id)


@route("admin_adv_search_status_toggle_")
async def admin_adv_search_status_toggle(update):
    """تغییر انتخاب یک وضعیت (admin_adv_search_status_toggle_<status>)"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_status_toggle
    status = data.split("_")[-1]
    return await handle_search_status_toggle(chat_id, user_id, status)


@route("admin_adv_search_status_apply")
async def admin_adv_search_status_apply(update):
    """اعمال فیلتر وضعیت"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_status_apply
    return await handle_search_status_apply(chat_id, user_id)


@route("admin_adv_search_status_clear")
async def admin_adv_search_status_clear(update):
    """پاک کردن فیلتر وضعیت"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_status_clear
    return await handle_search_status_clear(chat_id, user_id)


@route("admin_adv_search_service")
async def admin_adv_search_service(update):
    """جستجو بر اساس سرویس"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_service
    return await handle_search_service(chat_id, user_id, 0)


@route("admin_adv_search_service_toggle_")
async def admin_adv_search_service_toggle(update):
    """تغییر انتخاب یک سرویس (admin_adv_search_service_toggle_<service_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_service_toggle
    try:
        service_id = int(data.split("_")[-1])
        return await handle_search_service_toggle(chat_id, user_id, service_id)
    except ValueError:
        log_general_error(
            f"Invalid service_id in admin_adv_search_service_toggle: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه سرویس نامعتبر.")
        return True


@route("admin_adv_search_service_page_")
async def admin_adv_search_service_page(update):
    """صفحه‌بندی سرویس‌ها (admin_adv_search_service_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_service_page
    try:
        page = int(data.split("_")[-1])
        return await handle_search_service_page(chat_id, user_id, page)
    except ValueError:
        log_general_error(
            f"Invalid page in admin_adv_search_service_page: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True


@route("admin_adv_search_service_apply")
async def admin_adv_search_service_apply(update):
    """اعمال فیلتر سرویس"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_service_apply
    return await handle_search_service_apply(chat_id, user_id)


@route("admin_adv_search_service_clear")
async def admin_adv_search_service_clear(update):
    """پاک کردن فیلتر سرویس"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_service_clear
    return await handle_search_service_clear(chat_id, user_id)


@route("admin_adv_search_user")
async def admin_adv_search_user(update):
    """جستجو بر اساس کاربر"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_user
    return await handle_search_user(chat_id, user_id)


@route("admin_adv_search_tracking")
async def admin_adv_search_tracking(update):
    """جستجو بر اساس کد رهگیری"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_tracking
    return await handle_search_tracking(chat_id, user_id)


@route("admin_adv_search_has_file")
async def admin_adv_search_has_file(update):
    """جستجوی سفارشات دارای فایل"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_has_file
    return await handle_search_has_file(chat_id, user_id)


@route("admin_adv_search_reset")
async def admin_adv_search_reset(update):
    """بازنشانی جستجو"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_reset
    return await handle_search_reset(chat_id, user_id)


@route("admin_adv_search_results")
async def admin_adv_search_results(update):
    """نمایش نتایج جستجو"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_results
    return await handle_search_results(chat_id, user_id, 0)


@route("admin_adv_search_page_")
async def admin_adv_search_page(update):
    """صفحه‌بندی نتایج جستجو (admin_adv_search_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_page
    try:
        page = int(data.split("_")[-1])
        return await handle_search_page(chat_id, user_id, page)
    except ValueError:
        log_general_error(
            f"Invalid page in admin_adv_search_page: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True


@route("admin_adv_search_order_")
async def admin_adv_search_order(update):
    """نمایش جزئیات یک سفارش از نتایج جستجو (admin_adv_search_order_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_order_detail
    try:
        order_id = int(data.split("_")[-1])
        return await handle_search_order_detail(chat_id, user_id, order_id)
    except ValueError:
        log_general_error(
            f"Invalid order_id in admin_adv_search_order: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
        return True


@route("admin_adv_search_export")
async def admin_adv_search_export(update):
    """خروجی Excel از نتایج جستجو"""
    chat_id, user_id, data = extract_params(update)
    from .advanced_search import handle_search_export
    return await handle_search_export(chat_id, user_id)


# ========== روت‌های بخش مدیریت الگوها (Templates) ==========

@route("admin_templates")
async def admin_templates(update):
    """نمایش منوی اصلی مدیریت الگوها"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_templates
    return await handle_templates(chat_id, user_id)


@route("admin_template_list")
async def admin_template_list(update):
    """نمایش لیست الگوها"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_list
    return await handle_template_list(chat_id, user_id, 0)


@route("admin_template_list_page_")
async def admin_template_list_page(update):
    """صفحه‌بندی لیست الگوها (admin_template_list_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_list_page
    try:
        page = int(data.split("_")[-1])
        return await handle_template_list_page(chat_id, user_id, page)
    except ValueError:
        log_general_error(
            f"Invalid page in admin_template_list_page: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True


@route("admin_template_detail_")
async def admin_template_detail(update):
    """نمایش جزئیات یک الگو (admin_template_detail_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_detail
    try:
        template_id = int(data.split("_")[-1])
        return await handle_template_detail(chat_id, user_id, template_id)
    except ValueError:
        log_general_error(
            f"Invalid template_id in admin_template_detail: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True


@route("admin_template_create")
async def admin_template_create(update):
    """شروع فرآیند ایجاد الگوی جدید"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_create
    return await handle_template_create(chat_id, user_id)


@route("admin_template_create_empty")
async def admin_template_create_empty(update):
    """ایجاد الگوی خالی جدید"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_create_empty
    return await handle_template_create_empty(chat_id, user_id)


@route("admin_template_copy")
async def admin_template_copy(update):
    """شروع فرآیند کپی از الگوی موجود"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_copy
    return await handle_template_copy(chat_id, user_id)


@route("admin_template_copy_select_")
async def admin_template_copy_select(update):
    """انتخاب الگو برای کپی (admin_template_copy_select_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_copy_select
    try:
        template_id = int(data.split("_")[-1])
        return await handle_template_copy_select(chat_id, user_id, template_id)
    except ValueError:
        log_general_error(
            f"Invalid template_id in admin_template_copy_select: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True


@route("admin_template_extract")
async def admin_template_extract(update):
    """شروع فرآیند استخراج الگو از دکمه"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_extract
    return await handle_template_extract(chat_id, user_id)


@route("admin_template_extract_btn_")
async def admin_template_extract_btn(update):
    """انتخاب دکمه برای استخراج الگو (admin_template_extract_btn_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_extract_btn
    try:
        button_id = int(data.split("_")[-1])
        return await handle_template_extract_btn(chat_id, user_id, button_id)
    except ValueError:
        log_general_error(
            f"Invalid button_id in admin_template_extract_btn: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True


@route("admin_template_save")
async def admin_template_save(update):
    """ذخیره الگوی در حال ساخت"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_save
    return await handle_template_save(chat_id, user_id)


@route("admin_template_edit_")
async def admin_template_edit(update):
    """شروع ویرایش الگو (admin_template_edit_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_edit
    try:
        template_id = int(data.split("_")[-1])
        return await handle_template_edit(chat_id, user_id, template_id)
    except ValueError:
        log_general_error(
            f"Invalid template_id in admin_template_edit: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True


@route("admin_template_delete_")
async def admin_template_delete(update):
    """شروع فرآیند حذف الگو (admin_template_delete_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_delete
    try:
        template_id = int(data.split("_")[-1])
        return await handle_template_delete(chat_id, user_id, template_id)
    except ValueError:
        log_general_error(
            f"Invalid template_id in admin_template_delete: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True


@route("admin_template_delete_confirm_")
async def admin_template_delete_confirm(update):
    """تایید نهایی حذف الگو (admin_template_delete_confirm_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_delete_confirm
    try:
        template_id = int(data.split("_")[-1])
        return await handle_template_delete_confirm(chat_id, user_id, template_id)
    except ValueError:
        log_general_error(
            f"Invalid template_id in admin_template_delete_confirm: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True


@route("admin_template_apply")
async def admin_template_apply(update):
    """نمایش لیست الگوها برای اعمال به دکمه"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_apply
    return await handle_template_apply(chat_id, user_id)


@route("admin_template_apply_select_")
async def admin_template_apply_select(update):
    """انتخاب الگو برای اعمال (admin_template_apply_select_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_apply_select
    try:
        template_id = int(data.split("_")[-1])
        return await handle_template_apply_select(chat_id, user_id, template_id)
    except ValueError:
        log_general_error(
            f"Invalid template_id in admin_template_apply_select: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True


@route("admin_template_apply_btn_")
async def admin_template_apply_btn(update):
    """انتخاب دکمه برای اعمال الگو (admin_template_apply_btn_<template_id>_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_apply_btn
    try:
        parts = data.split("_")
        template_id = int(parts[4])
        button_id = int(parts[5])
        return await handle_template_apply_btn(chat_id, user_id, template_id, button_id)
    except (ValueError, IndexError):
        log_general_error(
            f"Invalid template_id or button_id in admin_template_apply_btn: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True


@route("admin_template_apply_confirm_")
async def admin_template_apply_confirm(update):
    """تایید نهایی اعمال الگو به دکمه (admin_template_apply_confirm_<template_id>_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_apply_confirm
    try:
        parts = data.split("_")
        template_id = int(parts[5])
        button_id = int(parts[6])
        return await handle_template_apply_confirm(chat_id, user_id, template_id, button_id)
    except (ValueError, IndexError):
        log_general_error(
            f"Invalid template_id or button_id in admin_template_apply_confirm: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True


@route("admin_template_qtype_")
async def admin_template_qtype(update):
    """انتخاب نوع سوال برای الگو (admin_template_qtype_<type>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_qtype
    return await handle_template_qtype(chat_id, user_id, data)


@route("admin_template_qtype_back")
async def admin_template_qtype_back(update):
    """بازگشت به انتخاب نوع سوال"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_qtype_back
    return await handle_template_qtype_back(chat_id, user_id)


@route("admin_template_qsetting_")
async def admin_template_qsetting(update):
    """پردازش تنظیمات سوال (admin_template_qsetting_<action>)"""
    chat_id, user_id, data = extract_params(update)
    from .templates import handle_template_qsetting
    return await handle_template_qsetting(chat_id, user_id, data)


# ========== روت‌های مدیریت یادآوری سفارشات ==========

@route("admin_order_reminder")
async def admin_order_reminder(update):
    """نمایش لیست سفارشات نیازمند یادآوری"""
    chat_id, user_id, data = extract_params(update)
    from .orders import handle_order_reminder
    return await handle_order_reminder(chat_id, user_id)


@route("admin_order_remind_")
async def admin_order_remind_single(update):
    """ارسال یادآوری برای یک سفارش خاص (admin_order_remind_<order_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .orders import handle_order_remind_single
    try:
        order_id = int(data.split("_")[-1])
        return await handle_order_remind_single(chat_id, user_id, data)
    except ValueError:
        log_general_error(
            f"Invalid order_id in admin_order_remind_single: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
        return True


@route("admin_order_remind_all")
async def admin_order_remind_all(update):
    """ارسال یادآوری به همه سفارشات ناتمام"""
    chat_id, user_id, data = extract_params(update)
    from .orders import handle_order_remind_all
    return await handle_order_remind_all(chat_id, user_id)


# ========== روت‌های مدیریت قیمت متغیر ==========

@route("admin_btn_price_type_")
async def admin_btn_price_type(update):
    """تغییر نوع قیمت دکمه (admin_btn_price_type_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .btn_manage import handle_button_price_type
    try:
        btn_id = int(data.split("_")[-1])
        return await handle_button_price_type(chat_id, user_id, data)
    except ValueError:
        log_general_error(
            f"Invalid button_id in admin_btn_price_type: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True


@route("admin_btn_price_type_set_")
async def admin_btn_price_type_set(update):
    """اعمال نوع قیمت جدید (admin_btn_price_type_set_<button_id>_<type>)"""
    chat_id, user_id, data = extract_params(update)
    from .btn_manage import handle_button_price_type_set
    return await handle_button_price_type_set(chat_id, user_id, data)


@route("admin_btn_set_min_price_")
async def admin_btn_set_min_price(update):
    """تنظیم حداقل مبلغ قیمت متغیر (admin_btn_set_min_price_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .btn_manage import handle_button_set_min_price_start
    try:
        btn_id = int(data.split("_")[-1])
        return await handle_button_set_min_price_start(chat_id, user_id, btn_id)
    except ValueError:
        log_general_error(
            f"Invalid button_id in admin_btn_set_min_price: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True


@route("admin_btn_set_max_price_")
async def admin_btn_set_max_price(update):
    """تنظیم حداکثر مبلغ قیمت متغیر (admin_btn_set_max_price_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .btn_manage import handle_button_set_max_price_start
    try:
        btn_id = int(data.split("_")[-1])
        return await handle_button_set_max_price_start(chat_id, user_id, btn_id)
    except ValueError:
        log_general_error(
            f"Invalid button_id in admin_btn_set_max_price: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True


@route("admin_cat_price_")
async def admin_cat_price(update):
    """مدیریت قیمت‌های متغیر دکمه‌های یک دسته‌بندی (admin_cat_price_<category_id>)"""
    chat_id, user_id, data = extract_params(update)
    from .btn_manage import handle_category_price
    try:
        cat_id = int(data.split("_")[-1])
        return await handle_category_price(chat_id, user_id, cat_id)
    except ValueError:
        log_general_error(
            f"Invalid category_id in admin_cat_price: {data}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ شناسه دسته‌بندی نامعتبر.")
        return True


# ========== روت‌های جدید مدیریت فایل لاگ ==========

@route("admin_log_viewer")
async def admin_log_viewer(update):
    """نمایش منوی اصلی مدیریت فایل لاگ (bot.log)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_log_viewer(chat_id, user_id)


@route("admin_log_view")
async def admin_log_view(update):
    """نمایش خطاهای اخیر از فایل لاگ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_log_view(chat_id, user_id)


@route("admin_log_clear")
async def admin_log_clear(update):
    """نمایش تأییدیه پاک کردن فایل لاگ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_log_clear(chat_id, user_id)


@route("admin_log_clear_confirm")
async def admin_log_clear_confirm(update):
    """اجرای پاک کردن فایل لاگ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_log_clear_confirm(chat_id, user_id)


# ========== صادر کردن توابع اصلی برای استفاده در admin_panel/__init__.py ==========

__all__ = [
    'handle_admin_callback',
    'show_admin_panel',
    'admin_back',
    'admin_none',
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
    'admin_templates',
    'admin_template_list',
    'admin_template_list_page',
    'admin_template_detail',
    'admin_template_create',
    'admin_template_create_empty',
    'admin_template_copy',
    'admin_template_copy_select',
    'admin_template_extract',
    'admin_template_extract_btn',
    'admin_template_save',
    'admin_template_edit',
    'admin_template_delete',
    'admin_template_delete_confirm',
    'admin_template_apply',
    'admin_template_apply_select',
    'admin_template_apply_btn',
    'admin_template_apply_confirm',
    'admin_template_qtype',
    'admin_template_qtype_back',
    'admin_template_qsetting',
    'admin_order_reminder',
    'admin_order_remind_single',
    'admin_order_remind_all',
    'admin_btn_price_type',
    'admin_btn_price_type_set',
    'admin_btn_set_min_price',
    'admin_btn_set_max_price',
    'admin_cat_price',
    # روت‌های جدید مدیریت لاگ
    'admin_log_viewer',
    'admin_log_view',
    'admin_log_clear',
    'admin_log_clear_confirm',
]