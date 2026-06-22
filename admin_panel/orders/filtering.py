# admin_panel/orders/filtering.py
# فیلترهای پیشرفته سفارشات
# شامل: فیلتر بر اساس وضعیت، سرویس، جستجوی کلمه کلیدی و اعمال فیلترها
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import List, Dict, Any, Optional
from logger_config import logger
from core import send_message, user_states
from database import (
    get_dynamic_orders,
    get_button_by_id,
    search_orders,
)
from keyboards.kb_admin_common import (
    admin_orders_filter_keyboard,
    admin_orders_filter_service_keyboard,
    admin_orders_search_keyboard,
)
from utils import get_service_name, format_number
from utils.error_handler import log_callback_error, log_general_error, log_database_error


# ============================================================
# توابع اصلی فیلتر
# ============================================================

async def handle_orders_filter_start(chat_id: int, user_id: int) -> bool:
    """
    شروع فیلتر سفارشات

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        current_filters = user_states.get(user_id, {}).get("orders_filters", {})
        current_status = current_filters.get('status')
        current_service = current_filters.get('button_id')

        keyboard = admin_orders_filter_keyboard(
            current_status=current_status,
            current_service=current_service
        )
        await send_message(
            chat_id,
            "🎯 **فیلتر سفارشات**\n\n"
            "وضعیت یا سرویس مورد نظر را انتخاب کنید:",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_filter_start: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش فیلتر.")
        return True


async def handle_orders_filter_status(chat_id: int, user_id: int, data: str) -> bool:
    """
    انتخاب وضعیت برای فیلتر

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک (admin_orders_filter_status_<status>)

    بازگشت: True در صورت موفقیت
    """
    try:
        status = data.split("_")[-1]
        logger.info(f"=== handle_orders_filter_status: وضعیت انتخاب شده: {status} ===")

        if user_id not in user_states:
            user_states[user_id] = {}
        if "orders_filters" not in user_states[user_id]:
            user_states[user_id]["orders_filters"] = {}

        if status == "all":
            user_states[user_id]["orders_filters"].pop("status", None)
        else:
            user_states[user_id]["orders_filters"]["status"] = status

        current_filters = user_states[user_id]["orders_filters"]
        keyboard = admin_orders_filter_keyboard(
            current_status=current_filters.get('status'),
            current_service=current_filters.get('button_id')
        )
        status_text = status if status != "all" else "همه"
        await send_message(
            chat_id,
            f"🎯 **فیلتر سفارشات**\n\nوضعیت انتخاب‌شده: {status_text}",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_filter_status: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب وضعیت.")
        return True


async def handle_orders_filter_service(chat_id: int, user_id: int) -> bool:
    """
    نمایش لیست سرویس‌ها برای انتخاب فیلتر

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_filter_service CALLED ===")

        orders = get_dynamic_orders()
        services = {}
        for order in orders:
            btn_id = order.get('button_id')
            if btn_id and btn_id not in services:
                btn = get_button_by_id(btn_id)
                if btn:
                    services[btn_id] = {'id': btn_id, 'name': btn['name']}

        if not services:
            await send_message(chat_id, "❌ هیچ سرویسی برای فیلتر یافت نشد.")
            return True

        service_list = list(services.values())
        keyboard = admin_orders_filter_service_keyboard(service_list)
        await send_message(chat_id, "🔘 **انتخاب سرویس برای فیلتر**", keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_filter_service: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش سرویس‌ها.")
        return True


async def handle_orders_filter_service_select(chat_id: int, user_id: int, data: str) -> bool:
    """
    انتخاب سرویس برای فیلتر

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک (admin_orders_filter_service_<service_id>)

    بازگشت: True در صورت موفقیت
    """
    try:
        service_id = int(data.split("_")[-1])
        logger.info(f"=== handle_orders_filter_service_select: سرویس انتخاب شده: {service_id} ===")

        if user_id not in user_states:
            user_states[user_id] = {}
        if "orders_filters" not in user_states[user_id]:
            user_states[user_id]["orders_filters"] = {}

        user_states[user_id]["orders_filters"]["button_id"] = service_id

        current_filters = user_states[user_id]["orders_filters"]
        btn = get_button_by_id(service_id)
        service_name = btn['name'] if btn else str(service_id)

        keyboard = admin_orders_filter_keyboard(
            current_status=current_filters.get('status'),
            current_service=service_id
        )
        await send_message(
            chat_id,
            f"🎯 **فیلتر سفارشات**\n\nسرویس انتخاب‌شده: {service_name}",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_filter_service_select: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب سرویس.")
        return True


async def handle_orders_filter_apply(chat_id: int, user_id: int) -> bool:
    """
    اعمال فیلترهای انتخاب‌شده و نمایش نتایج

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_filter_apply CALLED ===")
        filters = user_states.get(user_id, {}).get("orders_filters", {})
        status_filter = filters.get("status")
        service_filter = filters.get("button_id")

        logger.info(f"فیلترها: وضعیت={status_filter}, سرویس={service_filter}")

        all_orders = get_dynamic_orders()
        filtered_orders = all_orders

        if status_filter:
            filtered_orders = [o for o in filtered_orders if o.get('status') == status_filter]

        if service_filter:
            filtered_orders = [o for o in filtered_orders if o.get('button_id') == service_filter]

        if not filtered_orders:
            await send_message(chat_id, "📋 هیچ سفارشی با فیلترهای انتخاب‌شده یافت نشد.")
            return True

        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["orders_list"] = filtered_orders
        user_states[user_id]["orders_page"] = 0

        # استفاده از کیبورد تاریخ‌ها برای نمایش نتایج فیلتر شده
        from .grouping import admin_orders_date_keyboard

        keyboard = admin_orders_date_keyboard(filtered_orders, page=0)
        status_text = f"وضعیت: {status_filter or 'همه'}"
        service_text = ""
        if service_filter:
            btn = get_button_by_id(service_filter)
            service_text = f"سرویس: {btn['name'] if btn else service_filter}"
        filter_info = f" ({status_text} {service_text})".strip()
        await send_message(
            chat_id,
            f"📋 **نتایج فیلتر{filter_info}**\n"
            f"تعداد: {len(filtered_orders)} سفارش",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_filter_apply: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در اعمال فیلتر.")
        return True


async def handle_orders_filter_clear(chat_id: int, user_id: int) -> bool:
    """
    پاک کردن فیلترها

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_filter_clear CALLED ===")
        if user_id in user_states:
            user_states[user_id].pop("orders_filters", None)
            user_states[user_id].pop("orders_list", None)
        await send_message(chat_id, "✅ فیلترها پاک شدند.")
        return await handle_orders_filter_start(chat_id, user_id)
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_filter_clear: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در پاک کردن فیلتر.")
        return True


# ============================================================
# جستجوی سفارشات
# ============================================================

async def handle_orders_search(chat_id: int, user_id: int) -> bool:
    """
    شروع جستجوی سفارشات

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        user_states[user_id] = {"state": "admin_orders_search"}
        keyboard = admin_orders_search_keyboard()
        await send_message(
            chat_id,
            "🔍 **جستجوی سفارشات**\n\n"
            "لطفاً کلمه کلیدی (کد رهگیری، نام کاربر یا شناسه سفارش) را وارد کنید:",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_search: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع جستجو.")
        return True


async def handle_orders_search_result(chat_id: int, user_id: int, keyword: str) -> bool:
    """
    نمایش نتایج جستجو

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        keyword: کلمه کلیدی جستجو

    بازگشت: True در صورت موفقیت
    """
    try:
        if not keyword or keyword.strip() == "":
            await send_message(chat_id, "❌ لطفاً یک کلمه کلیدی معتبر وارد کنید.")
            return True

        results = search_orders(keyword.strip())

        if not results:
            await send_message(chat_id, f"❌ هیچ سفارشی با عبارت «{keyword}» یافت نشد.")
            return True

        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["orders_list"] = results
        user_states[user_id]["orders_page"] = 0

        # استفاده از کیبورد تاریخ‌ها برای نمایش نتایج جستجو
        from .grouping import admin_orders_date_keyboard

        keyboard = admin_orders_date_keyboard(results, page=0)
        await send_message(
            chat_id,
            f"🔍 **نتایج جستجو برای «{keyword}»**\n"
            f"تعداد: {len(results)} سفارش",
            keyboard
        )
        user_states[user_id]["state"] = "main"
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_search_result: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجو.")
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'handle_orders_filter_start',
    'handle_orders_filter_status',
    'handle_orders_filter_service',
    'handle_orders_filter_service_select',
    'handle_orders_filter_apply',
    'handle_orders_filter_clear',
    'handle_orders_search',
    'handle_orders_search_result',
]