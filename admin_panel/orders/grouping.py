# admin_panel/orders/grouping.py
# گروه‌بندی سفارشات بر اساس تاریخ، سرویس و کاربر
# شامل: نمایش لیست تاریخ‌ها، سرویس‌های هر تاریخ، کاربران هر سرویس و جزئیات سفارش
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
import json
from typing import List, Dict, Any, Optional
from logger_config import logger
from core import send_message, user_states
from database import (
    get_dynamic_orders,
    get_dynamic_order_by_id,
    get_button_by_id,
)
from keyboards import admin_main_keyboard
from keyboards.kb_admin_common import admin_orders_menu_keyboard
from utils import (
    get_service_name,
    get_fullname_from_order,
    extract_date_from_order,
    format_number,
    format_datetime,
    get_order_status_persian,
)
from utils.error_handler import log_callback_error, log_general_error, log_database_error
from .actions import show_order_detail


# ============================================================
# کیبوردهای گروه‌بندی
# ============================================================

def admin_orders_date_keyboard(orders: List[Dict], page: int = 0, per_page: int = 5) -> Dict:
    """
    مرحله ۱: نمایش لیست تاریخ‌ها (گروه‌بندی بر اساس تاریخ)

    پارامترها:
        orders: لیست سفارشات
        page: شماره صفحه
        per_page: تعداد آیتم در هر صفحه

    بازگشت: کیبورد تاریخ‌ها
    """
    try:
        date_groups = {}
        for order in orders:
            date_str = extract_date_from_order(order)
            if not date_str:
                continue
            if date_str not in date_groups:
                date_groups[date_str] = []
            date_groups[date_str].append(order)

        dates = sorted(date_groups.keys(), reverse=True)
        total_dates = len(dates)

        start = page * per_page
        end = min(start + per_page, total_dates)
        current_dates = dates[start:end]

        keyboard = []
        for date_str in current_dates:
            count = len(date_groups[date_str])
            keyboard.append([
                {"text": f"📅 {date_str} ({count} سفارش)", "callback_data": f"admin_orders_date_{date_str}"}
            ])

        nav_row = []
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_orders_date_page_{page-1}"})
        if end < total_dates:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_orders_date_page_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)

        keyboard.append([{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}])
        return {"inline_keyboard": keyboard}

    except Exception as e:
        log_callback_error(
            f"Error in admin_orders_date_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری تاریخ‌ها", "callback_data": "admin_back"}]]}


def admin_orders_service_keyboard(orders: List[Dict], date_str: str, page: int = 0, per_page: int = 5) -> Dict:
    """
    مرحله ۲: نمایش سرویس‌های یک تاریخ خاص

    پارامترها:
        orders: لیست سفارشات
        date_str: تاریخ انتخاب‌شده
        page: شماره صفحه
        per_page: تعداد آیتم در هر صفحه

    بازگشت: کیبورد سرویس‌ها
    """
    try:
        filtered = [o for o in orders if extract_date_from_order(o) == date_str]

        if not filtered:
            return {"inline_keyboard": [
                [{"text": "❌ هیچ سفارشی در این تاریخ یافت نشد", "callback_data": "admin_back"}],
                [{"text": "🔙 برگشت به تاریخ‌ها", "callback_data": "admin_back"}]
            ]}

        service_groups = {}
        for order in filtered:
            btn_id = order.get('button_id')
            service_name = get_service_name(btn_id)
            if service_name not in service_groups:
                service_groups[service_name] = []
            service_groups[service_name].append(order)

        services = list(service_groups.keys())
        total_services = len(services)

        start = page * per_page
        end = min(start + per_page, total_services)
        current_services = services[start:end]

        keyboard = []
        for service_name in current_services:
            count = len(service_groups[service_name])
            sample_order = service_groups[service_name][0]
            btn_id = sample_order.get('button_id', 0)
            keyboard.append([
                {"text": f"📌 {service_name} ({count} سفارش)", "callback_data": f"admin_orders_service_{date_str}_{btn_id}"}
            ])

        nav_row = []
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_orders_service_page_{date_str}_{page-1}"})
        if end < total_services:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_orders_service_page_{date_str}_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)

        keyboard.append([{"text": "🔙 برگشت به تاریخ‌ها", "callback_data": "admin_back"}])
        return {"inline_keyboard": keyboard}

    except Exception as e:
        log_callback_error(
            f"Error in admin_orders_service_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری سرویس‌ها", "callback_data": "admin_back"}]]}


def admin_orders_user_keyboard(orders: List[Dict], date_str: str, button_id: int, page: int = 0, per_page: int = 5) -> Dict:
    """
    مرحله ۳: نمایش کاربرانی که یک سرویس خاص را در تاریخ مشخص ثبت کرده‌اند

    پارامترها:
        orders: لیست سفارشات
        date_str: تاریخ انتخاب‌شده
        button_id: شناسه سرویس
        page: شماره صفحه
        per_page: تعداد آیتم در هر صفحه

    بازگشت: کیبورد کاربران
    """
    try:
        filtered = [o for o in orders if extract_date_from_order(o) == date_str and o.get('button_id') == button_id]

        if not filtered:
            return {"inline_keyboard": [
                [{"text": "❌ هیچ کاربری برای این سرویس یافت نشد", "callback_data": f"admin_orders_service_{date_str}_{button_id}"}],
                [{"text": "🔙 برگشت به سرویس‌ها", "callback_data": f"admin_orders_service_back_{date_str}"}]
            ]}

        user_groups = {}
        for order in filtered:
            fullname = get_fullname_from_order(order)
            if fullname not in user_groups:
                user_groups[fullname] = []
            user_groups[fullname].append(order)

        users = list(user_groups.keys())
        total_users = len(users)

        start = page * per_page
        end = min(start + per_page, total_users)
        current_users = users[start:end]

        keyboard = []
        for fullname in current_users:
            last_order = user_groups[fullname][-1]
            status = last_order.get('status', 'pending')
            status_icon = "✅" if status == "paid" else "⏳" if status == "pending" else "❌"

            total_amount = 0
            for order in user_groups[fullname]:
                amount = order.get('payment_amount')
                if amount is None:
                    amount = 0
                total_amount += amount

            keyboard.append([
                {"text": f"{status_icon} {fullname} - {format_number(total_amount)} ریال",
                 "callback_data": f"admin_orders_user_{date_str}_{button_id}_{fullname}"}
            ])

        nav_row = []
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_orders_user_page_{date_str}_{button_id}_{page-1}"})
        if end < total_users:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_orders_user_page_{date_str}_{button_id}_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)

        keyboard.append([{"text": "🔙 برگشت به سرویس‌ها", "callback_data": f"admin_orders_service_back_{date_str}"}])
        return {"inline_keyboard": keyboard}

    except Exception as e:
        log_callback_error(
            f"Error in admin_orders_user_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری کاربران", "callback_data": f"admin_orders_service_back_{date_str}"}]]}


# ============================================================
# توابع اصلی گروه‌بندی
# ============================================================

async def handle_orders_list(chat_id: int, user_id: int) -> bool:
    """
    منوی اصلی سفارشات

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        keyboard = admin_orders_menu_keyboard()
        await send_message(
            chat_id,
            "📋 **مدیریت سفارشات**\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_list: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش منوی سفارشات.")
        return True


async def handle_orders_group_by_date(chat_id: int, user_id: int) -> bool:
    """
    گروه‌بندی سفارشات بر اساس تاریخ

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_group_by_date CALLED for user {user_id} ===")
        orders = get_dynamic_orders()
        logger.info(f"تعداد سفارشات دریافتی از دیتابیس: {len(orders)}")

        if not orders:
            await send_message(chat_id, "📋 هیچ سفارشی ثبت نشده است.", admin_main_keyboard())
            return True

        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["orders_list"] = orders
        user_states[user_id]["orders_page"] = 0

        keyboard = admin_orders_date_keyboard(orders, page=0)
        await send_message(chat_id, "📋 **لیست سفارشات (گروه‌بندی بر اساس تاریخ)**\nتاریخ مورد نظر را انتخاب کنید:", keyboard)
        logger.info(f"لیست سفارشات برای کاربر {user_id} نمایش داده شد. تعداد: {len(orders)}")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_group_by_date: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست سفارشات.")
        return True


async def handle_orders_date_page(chat_id: int, user_id: int, data: str) -> bool:
    """
    صفحه‌بندی تاریخ‌ها (admin_orders_date_page_*)

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_date_page CALLED ===")
        parts = data.split("_")
        page = int(parts[4]) if len(parts) > 4 else 0
        logger.info(f"page: {page}")

        orders = user_states.get(user_id, {}).get("orders_list", [])
        if not orders:
            await send_message(chat_id, "📋 هیچ سفارشی ثبت نشده است.", admin_main_keyboard())
            return True

        keyboard = admin_orders_date_keyboard(orders, page=page)
        await send_message(chat_id, f"📋 **لیست تاریخ‌ها - صفحه {page + 1}**", keyboard)
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_date_page: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی تاریخ‌ها.")
        return True


async def handle_orders_date(chat_id: int, user_id: int, data: str) -> bool:
    """
    انتخاب تاریخ و نمایش سرویس‌های آن (admin_orders_date_*)

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_date CALLED ===")
        logger.info(f"chat_id: {chat_id}, user_id: {user_id}, data: {data}")

        parts = data.split("_")
        logger.info(f"parts: {parts}")

        if len(parts) < 4:
            logger.error(f"فرمت دیتا نامعتبر: {data}")
            await send_message(chat_id, "❌ فرمت تاریخ نامعتبر.", admin_main_keyboard())
            return True

        date_str = "_".join(parts[3:])
        logger.info(f"تاریخ استخراج شده: {date_str}")

        if not date_str:
            await send_message(chat_id, "❌ تاریخ نامعتبر.", admin_main_keyboard())
            return True

        logger.info(f"تاریخ انتخاب شده: {date_str} توسط کاربر {user_id}")

        orders = user_states.get(user_id, {}).get("orders_list", [])
        logger.info(f"تعداد سفارشات در user_states: {len(orders)}")

        if not orders:
            await send_message(chat_id, "❌ داده‌های سفارش یافت نشد. لطفاً دوباره از لیست سفارشات وارد شوید.", admin_main_keyboard())
            return True

        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["orders_date"] = date_str

        logger.info(f"ساخت کیبورد سرویس‌ها برای تاریخ {date_str}")
        keyboard = admin_orders_service_keyboard(orders, date_str)
        logger.info(f"کیبورد ساخته شد")

        await send_message(chat_id, f"📋 **سرویس‌های ثبت‌شده در تاریخ {date_str}**", keyboard)
        logger.info(f"پیام سرویس‌ها ارسال شد")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_date: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش سرویس‌های تاریخ.")
        return True


async def handle_orders_service_page(chat_id: int, user_id: int, data: str) -> bool:
    """
    صفحه‌بندی سرویس‌ها (admin_orders_service_page_*)

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_service_page CALLED ===")
        parts = data.split("_")
        if len(parts) < 6:
            await send_message(chat_id, "❌ خطا در صفحه‌بندی سرویس‌ها.", admin_main_keyboard())
            return True

        date_str = parts[4]
        page = int(parts[5]) if len(parts) > 5 else 0
        logger.info(f"date_str: {date_str}, page: {page}")

        orders = user_states.get(user_id, {}).get("orders_list", [])
        if not orders:
            await send_message(chat_id, "❌ داده‌های سفارش یافت نشد.", admin_main_keyboard())
            return True

        keyboard = admin_orders_service_keyboard(orders, date_str, page=page)
        await send_message(chat_id, f"📋 **سرویس‌های تاریخ {date_str} - صفحه {page + 1}**", keyboard)
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_service_page: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی سرویس‌ها.")
        return True


async def handle_orders_service_back(chat_id: int, user_id: int, data: str) -> bool:
    """
    بازگشت از مرحله سرویس به تاریخ‌ها (admin_orders_service_back_*)

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_service_back CALLED ===")
        orders = user_states.get(user_id, {}).get("orders_list", [])
        if orders:
            keyboard = admin_orders_date_keyboard(orders)
            await send_message(chat_id, f"📋 **لیست تاریخ‌ها**", keyboard)
        else:
            await send_message(chat_id, "📋 هیچ سفارشی یافت نشد.", admin_main_keyboard())
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_service_back: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در بازگشت به تاریخ‌ها.")
        return True


async def handle_orders_service(chat_id: int, user_id: int, data: str) -> bool:
    """
    انتخاب سرویس و نمایش کاربران آن (admin_orders_service_*)

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_service CALLED ===")
        parts = data.split("_")
        logger.info(f"parts: {parts}")

        if len(parts) < 5:
            await send_message(chat_id, "❌ خطا در دریافت اطلاعات سرویس.", admin_main_keyboard())
            return True

        date_str = parts[3]
        try:
            button_id = int(parts[4])
        except ValueError:
            await send_message(chat_id, "❌ شناسه سرویس نامعتبر.", admin_main_keyboard())
            return True

        logger.info(f"سرویس {button_id} در تاریخ {date_str} انتخاب شد توسط کاربر {user_id}")

        orders = user_states.get(user_id, {}).get("orders_list", [])
        if not orders:
            await send_message(chat_id, "❌ داده‌های سفارش یافت نشد.", admin_main_keyboard())
            return True

        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["orders_date"] = date_str
        user_states[user_id]["orders_service"] = button_id

        keyboard = admin_orders_user_keyboard(orders, date_str, button_id)
        service_name = get_service_name(button_id)
        await send_message(chat_id, f"👤 **کاربران سرویس «{service_name}» در تاریخ {date_str}**", keyboard)
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_service: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش کاربران سرویس.")
        return True


async def handle_orders_user_page(chat_id: int, user_id: int, data: str) -> bool:
    """
    صفحه‌بندی کاربران (admin_orders_user_page_*)

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_user_page CALLED ===")
        parts = data.split("_")
        if len(parts) < 6:
            await send_message(chat_id, "❌ خطا در صفحه‌بندی کاربران.", admin_main_keyboard())
            return True

        date_str = parts[3]
        button_id = int(parts[4]) if len(parts) > 4 else 0
        page = int(parts[-1]) if len(parts) > 5 else 0
        logger.info(f"date_str: {date_str}, button_id: {button_id}, page: {page}")

        orders = user_states.get(user_id, {}).get("orders_list", [])
        if not orders:
            await send_message(chat_id, "❌ داده‌های سفارش یافت نشد.", admin_main_keyboard())
            return True

        keyboard = admin_orders_user_keyboard(orders, date_str, button_id, page=page)
        service_name = get_service_name(button_id)
        await send_message(chat_id, f"👤 **کاربران سرویس «{service_name}» - صفحه {page + 1}**", keyboard)
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_user_page: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی کاربران.")
        return True


async def handle_orders_user(chat_id: int, user_id: int, data: str) -> bool:
    """
    انتخاب کاربر و نمایش جزئیات سفارش (admin_orders_user_*)

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_orders_user CALLED ===")
        parts = data.split("_")
        logger.info(f"parts: {parts}")

        if len(parts) < 6:
            await send_message(chat_id, "❌ خطا در دریافت اطلاعات کاربر.", admin_main_keyboard())
            return True

        date_str = parts[3]
        try:
            button_id = int(parts[4])
        except ValueError:
            await send_message(chat_id, "❌ شناسه سرویس نامعتبر.", admin_main_keyboard())
            return True
        fullname = "_".join(parts[5:])

        logger.info(f"کاربر {fullname} برای سرویس {button_id} در تاریخ {date_str} انتخاب شد")

        orders = user_states.get(user_id, {}).get("orders_list", [])
        target_orders = [o for o in orders if extract_date_from_order(o) == date_str 
                         and o.get('button_id') == button_id 
                         and get_fullname_from_order(o) == fullname]

        if not target_orders:
            await send_message(chat_id, "❌ سفارشی برای این کاربر یافت نشد.", admin_main_keyboard())
            return True

        order = target_orders[0]
        await show_order_detail(chat_id, user_id, order, "admin_orders")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_user: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش کاربر.")
        return True


async def handle_order_by_id(chat_id: int, user_id: int, data: str) -> bool:
    """
    نمایش جزئیات سفارش با شناسه (admin_order_*)
    برای سازگاری با کالبک قبلی

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"=== handle_order_by_id CALLED ===")
        parts = data.split("_")
        if len(parts) < 3:
            await send_message(chat_id, "❌ شناسه سفارش نامعتبر.", admin_main_keyboard())
            return True

        try:
            order_id = int(parts[2])
        except ValueError:
            await send_message(chat_id, "❌ شناسه سفارش نامعتبر.", admin_main_keyboard())
            return True

        logger.info(f"order_id: {order_id}")

        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.", admin_main_keyboard())
            return True

        await show_order_detail(chat_id, user_id, order, "admin_orders")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_order_by_id: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'admin_orders_date_keyboard',
    'admin_orders_service_keyboard',
    'admin_orders_user_keyboard',
    'handle_orders_list',
    'handle_orders_group_by_date',
    'handle_orders_date_page',
    'handle_orders_date',
    'handle_orders_service_page',
    'handle_orders_service_back',
    'handle_orders_service',
    'handle_orders_user_page',
    'handle_orders_user',
    'handle_order_by_id',
]