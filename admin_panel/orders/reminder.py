# admin_panel/orders/reminder.py
# یادآوری سفارشات ناتمام در پنل مدیریت
# شامل: نمایش لیست سفارشات نیازمند یادآوری، ارسال دستی یادآوری و ارسال گروهی

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import List, Dict, Any
from logger_config import logger
from core import send_message
from database import (
    get_dynamic_order_by_id,
    get_orders_for_reminder,
    update_reminder_time,
)
from utils import (
    get_service_name,
    get_fullname_from_order,
    format_number,
    format_datetime,
    get_order_status_persian,
)
from utils.error_handler import log_general_error, log_callback_error, log_database_error


# ============================================================
# کیبوردهای یادآوری
# ============================================================

def reminder_list_keyboard(orders: List[Dict], limit: int = 10) -> Dict:
    """
    کیبورد نمایش لیست سفارشات نیازمند یادآوری

    پارامترها:
        orders: لیست سفارشات
        limit: حداکثر تعداد نمایش

    بازگشت: کیبورد
    """
    try:
        keyboard = []

        if not orders:
            keyboard.append([{"text": "✅ هیچ سفارشی نیاز به یادآوری ندارد", "callback_data": "admin_none"}])
        else:
            for order in orders[:limit]:
                order_id = order.get('id')
                user_id = order.get('user_id')
                amount = order.get('payment_amount', 0) or 0
                created_at = order.get('created_at', '')
                fullname = get_fullname_from_order(order)

                keyboard.append([
                    {"text": f"🆔 #{order_id} - {fullname[:12]} - {format_number(amount)} ریال",
                     "callback_data": f"admin_order_remind_{order_id}"}
                ])

            if len(orders) > limit:
                keyboard.append([
                    {"text": f"... و {len(orders) - limit} سفارش دیگر", "callback_data": "admin_none"}
                ])

        keyboard.append([
            {"text": "📨 ارسال یادآوری به همه", "callback_data": "admin_order_remind_all"}
        ])
        keyboard.append([
            {"text": "🔙 برگشت", "callback_data": "admin_orders"}
        ])

        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in reminder_list_keyboard: {str(e)}",
            traceback=traceback.format_exc()  # ✅ traceback کامل
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری یادآوری‌ها", "callback_data": "admin_none"}]]}


# ============================================================
# توابع اصلی یادآوری
# ============================================================

async def handle_order_reminder(chat_id: int, user_id: int) -> bool:
    """
    نمایش لیست سفارشات نیازمند یادآوری و ارسال دستی

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        hours = 24
        orders = get_orders_for_reminder(hours)

        if not orders:
            await send_message(
                chat_id,
                f"✅ هیچ سفارشی نیاز به یادآوری ندارد.\n\n"
                f"سفارشاتی که بیش از {hours} ساعت از ثبت آنها گذشته باشد، نمایش داده می‌شوند."
            )
            return True

        keyboard = reminder_list_keyboard(orders)

        await send_message(
            chat_id,
            f"⏰ **یادآوری سفارشات ناتمام**\n\n"
            f"{len(orders)} سفارش نیاز به یادآوری دارند.\n"
            f"(سفارشاتی که بیش از {hours} ساعت از ثبت آنها گذشته)\n\n"
            f"برای ارسال یادآوری به هر سفارش، روی آن کلیک کنید:",
            keyboard
        )
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_order_reminder: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش سفارشات نیازمند یادآوری.")
        return True


async def handle_order_remind_single(chat_id: int, user_id: int, data: str) -> bool:
    """
    ارسال یادآوری برای یک سفارش خاص (admin_order_remind_<order_id>)

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        data: داده کالبک

    بازگشت: True در صورت موفقیت
    """
    try:
        order_id = int(data.split("_")[-1])
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True

        from reminder import send_reminder_for_order
        success = await send_reminder_for_order(order_id)

        if success:
            await send_message(chat_id, f"✅ یادآوری برای سفارش #{order_id} ارسال شد.")
        else:
            await send_message(chat_id, f"❌ خطا در ارسال یادآوری برای سفارش #{order_id}.")

        return await handle_order_reminder(chat_id, user_id)

    except Exception as e:
        log_callback_error(
            f"Error in handle_order_remind_single: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ارسال یادآوری.")
        return True


async def handle_order_remind_all(chat_id: int, user_id: int) -> bool:
    """
    ارسال یادآوری به همه سفارشات ناتمام

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        orders = get_orders_for_reminder(24)

        if not orders:
            await send_message(chat_id, "✅ هیچ سفارشی نیاز به یادآوری ندارد.")
            return True

        await send_message(chat_id, f"⏳ در حال ارسال یادآوری به {len(orders)} سفارش...")

        from reminder import process_all_reminders
        results = await process_all_reminders()

        await send_message(
            chat_id,
            f"📨 **گزارش ارسال یادآوری**\n\n"
            f"👥 کل سفارشات: {results.get('total', 0)}\n"
            f"✅ ارسال‌شده: {results.get('sent', 0)}\n"
            f"❌ ناموفق: {results.get('failed', 0)}"
        )

        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_order_remind_all: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ارسال یادآوری گروهی.")
        return True


# ============================================================
# تابع کمکی برای ساخت پیام یادآوری (در صورت نیاز)
# ============================================================

def build_reminder_message(order: Dict, user_fullname: str) -> str:
    """
    ساخت پیام یادآوری برای یک سفارش

    پارامترها:
        order: دیکشنری سفارش
        user_fullname: نام کامل کاربر

    بازگشت: متن پیام یادآوری
    """
    try:
        order_id = order.get('id')
        amount = order.get('payment_amount', 0) or 0
        created_at = order.get('created_at', '')
        tracking_code = order.get('tracking_code', 'ندارد')
        service_name = get_service_name(order.get('button_id'))

        msg = (
            f"⏰ **یادآوری سفارش ناتمام**\n\n"
            f"سلام {user_fullname} عزیز،\n\n"
            f"شما یک سفارش ثبت کرده‌اید که **هنوز پرداخت نشده** است.\n\n"
            f"📋 **جزئیات سفارش:**\n"
            f"  🆔 شناسه: {order_id}\n"
            f"  🔘 سرویس: {service_name}\n"
            f"  💰 مبلغ: {format_number(amount)} ریال\n"
            f"  📅 تاریخ ثبت: {format_datetime(created_at)}\n"
            f"  🎫 کد رهگیری: {tracking_code}\n\n"
            f"📌 **نکته:**\n"
            f"برای تکمیل سفارش، لطفاً هرچه سریع‌تر اقدام به پرداخت کنید.\n"
            f"در صورت نیاز به راهنمایی، با پشتیبانی تماس بگیرید.\n\n"
            f"با تشکر از شما 🙏"
        )

        return msg

    except Exception as e:
        log_general_error(
            f"Error in build_reminder_message: {str(e)}",
            traceback=traceback.format_exc()  # ✅ traceback کامل
        )
        return "❌ خطا در ساخت پیام یادآوری."


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'reminder_list_keyboard',
    'handle_order_reminder',
    'handle_order_remind_single',
    'handle_order_remind_all',
    'build_reminder_message',
]