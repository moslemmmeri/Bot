# admin_panel/orders/actions.py
# مدیریت اقدامات روی سفارشات
# شامل: تغییر وضعیت، حذف، افزودن یادداشت و نمایش جزئیات کامل سفارش
# اصلاح شده با استفاده از ui_helpers برای یکپارچه‌سازی UI

import traceback
import json
from typing import Dict, Any, Optional

from logger_config import logger
from core import send_message, send_photo, send_document, user_states
from database import (
    get_dynamic_order_by_id,
    update_order_status,
    delete_order,
    add_order_note,
)
from keyboards.kb_admin_common import (
    admin_order_detail_actions_keyboard,
    admin_orders_status_keyboard,
    admin_order_delete_confirm_keyboard,
    admin_order_note_keyboard,
)
from utils import (
    get_service_name,
    get_fullname_from_order,
    format_number,
    get_order_status_persian,
)
from utils.error_handler import log_callback_error, log_general_error, log_database_error

# ========== ایمپورت‌های جدید از ui_helpers ==========
from ui_helpers import (
    Emojis,
    TextFormatter,
    TextTable,
    InfoCard,
    StatusMessage,
    build_menu_keyboard,
)


# ============================================================
# نمایش جزئیات کامل سفارش (اصلاح شده با InfoCard)
# ============================================================

async def show_order_detail(
    chat_id: int,
    user_id: int,
    order: Dict[str, Any],
    back_callback: str = "admin_orders"
) -> bool:
    """
    نمایش جزئیات کامل یک سفارش با دکمه بازگشت و ارسال فایل‌های ضمیمه
    اصلاح شده با استفاده از InfoCard و TextFormatter
    """
    try:
        order_data = order.get('order_data', {})
        if isinstance(order_data, str):
            try:
                order_data = json.loads(order_data)
            except json.JSONDecodeError as e:
                log_general_error(
                    f"خطا در دیکد کردن order_data برای سفارش {order.get('id')}: {str(e)}",
                    traceback=traceback.format_exc(),
                    user_id=user_id,
                    chat_id=chat_id
                )
                order_data = {}

        fullname = get_fullname_from_order(order)
        button_id = order.get('button_id')
        service_name = get_service_name(button_id)

        status_map = {
            "pending": "⏳ در انتظار پرداخت",
            "paid": "✅ پرداخت شده",
            "completed": "✅ تکمیل شده",
            "cancelled": "❌ لغو شده",
            "failed": "❌ ناموفق",
            "refunded": "🔄 بازگشت وجه"
        }
        status_text = status_map.get(order.get('status', 'pending'), order.get('status', 'نامشخص'))

        payment_amount = order.get('payment_amount')
        if payment_amount is None:
            payment_amount = 0

        # ========== ساخت کارت اطلاعاتی با InfoCard ==========
        items = {
            "👤 کاربر": fullname,
            "🆔 شناسه کاربر": order.get('user_id', 'نامشخص'),
            "🔘 سرویس": service_name,
            "💰 مبلغ": TextFormatter.format_currency(payment_amount),
            "🎫 کد رهگیری": order.get('tracking_code', 'ندارد') or 'ندارد',
            "📌 وضعیت": status_text,
            "⏰ زمان ثبت": order.get('created_at', 'نامشخص') or 'نامشخص',
        }

        admin_note = order.get('admin_note')
        if admin_note:
            items["📝 یادداشت ادمین"] = f"```\n{admin_note}\n```"

        msg = InfoCard.create(f"سفارش #{order['id']}", items, emoji=Emojis.MENU)

        # ========== افزودن پاسخ‌های کاربر با لیست گلوله‌ای ==========
        answers = order_data.get('answers', {})
        if answers:
            msg += "\n📝 **پاسخ‌های کاربر:**\n"
            answer_lines = []
            for q_text, ans in answers.items():
                answer_lines.append(f"▪️ {q_text}: {ans}")
            msg += "\n".join(answer_lines)
        else:
            msg += "\n📝 **پاسخ‌های کاربر:**\n▪️ پاسخی ثبت نشده است."

        keyboard = admin_order_detail_actions_keyboard(order['id'], order.get('status', 'pending'))
        await send_message(chat_id, msg, keyboard)

        # ========== ارسال فایل‌های ضمیمه ==========
        files = order_data.get('files', {})
        if files:
            file_msg = f"\n{Emojis.DOCUMENT} **فایل‌های ارسالی:**\n"
            for question_text, file_info in files.items():
                file_id = file_info.get('file_id')
                file_type = file_info.get('type', 'document')
                caption = f"📎 {question_text}"
                try:
                    if file_type == 'photo':
                        await send_photo(chat_id, file_id, caption)
                    else:
                        await send_document(chat_id, file_id, caption)
                    file_msg += f"▪️ {question_text}: ارسال شد\n"
                except Exception as e:
                    log_callback_error(
                        f"خطا در ارسال فایل برای سفارش {order.get('id')}: {str(e)}",
                        traceback=traceback.format_exc(),
                        user_id=user_id,
                        chat_id=chat_id
                    )
                    file_msg += f"▪️ {question_text}: ❌ خطا در ارسال\n"
            await send_message(chat_id, file_msg)

        return True

    except Exception as e:
        log_callback_error(
            f"Error in show_order_detail for order {order.get('id')}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
        return True


# ============================================================
# تغییر وضعیت سفارش
# ============================================================

async def handle_order_status_change(chat_id: int, user_id: int, data: str) -> bool:
    """
    شروع تغییر وضعیت سفارش (admin_order_status_<order_id>)
    اصلاح شده با StatusMessage
    """
    try:
        order_id = int(data.split("_")[-1])
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, StatusMessage.error("سفارش یافت نشد."))
            return True

        current_status = order.get('status', 'pending')
        keyboard = admin_orders_status_keyboard(order_id, current_status)
        await send_message(
            chat_id,
            f"🔄 **تغییر وضعیت سفارش #{order_id}**\nوضعیت فعلی: {current_status}",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_order_status_change: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر وضعیت.")
        return True


async def handle_order_status_change_confirm(chat_id: int, user_id: int, data: str) -> bool:
    """
    اعمال تغییر وضعیت سفارش (admin_order_status_change_<order_id>_<new_status>)
    اصلاح شده با StatusMessage
    """
    try:
        parts = data.split("_")
        order_id = int(parts[4])
        new_status = parts[5]

        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, StatusMessage.error("سفارش یافت نشد."))
            return True

        success = update_order_status(order_id, new_status, user_id, note=f"تغییر وضعیت توسط ادمین")
        if success:
            msg = StatusMessage.success(f"وضعیت سفارش #{order_id} به «{new_status}» تغییر یافت.")
            await send_message(chat_id, msg)
        else:
            msg = StatusMessage.error(f"خطا در تغییر وضعیت سفارش #{order_id}.")
            await send_message(chat_id, msg)

        await show_order_detail_by_id(chat_id, user_id, order_id)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_order_status_change_confirm: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر وضعیت.")
        return True


# ============================================================
# حذف سفارش
# ============================================================

async def handle_order_delete(chat_id: int, user_id: int, data: str) -> bool:
    """
    نمایش تایید حذف سفارش (admin_order_delete_<order_id>)
    اصلاح شده با StatusMessage.warning
    """
    try:
        order_id = int(data.split("_")[-1])
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, StatusMessage.error("سفارش یافت نشد."))
            return True

        keyboard = admin_order_delete_confirm_keyboard(order_id)
        msg = StatusMessage.warning(
            f"آیا از حذف سفارش #{order_id} مطمئن هستید؟",
            details={
                "شناسه سفارش": order_id,
                "کاربر": get_fullname_from_order(order),
                "سرویس": get_service_name(order.get('button_id')),
                "مبلغ": TextFormatter.format_currency(order.get('payment_amount', 0)),
            }
        )
        await send_message(chat_id, msg, keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_order_delete: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع حذف.")
        return True


async def handle_order_delete_confirm(chat_id: int, user_id: int, data: str) -> bool:
    """
    اجرای حذف سفارش (admin_order_delete_yes_<order_id>)
    اصلاح شده با StatusMessage
    """
    try:
        order_id = int(data.split("_")[-1])
        success = delete_order(order_id)
        if success:
            msg = StatusMessage.success(f"سفارش #{order_id} با موفقیت حذف شد.")
            await send_message(chat_id, msg)
        else:
            msg = StatusMessage.error(f"خطا در حذف سفارش #{order_id}.")
            await send_message(chat_id, msg)

        from .grouping import handle_orders_list
        await handle_orders_list(chat_id, user_id)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_order_delete_confirm: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف سفارش.")
        return True


# ============================================================
# افزودن یادداشت به سفارش
# ============================================================

async def handle_order_note(chat_id: int, user_id: int, data: str) -> bool:
    """
    شروع افزودن یادداشت به سفارش (admin_order_note_<order_id>)
    """
    try:
        order_id = int(data.split("_")[-1])
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, StatusMessage.error("سفارش یافت نشد."))
            return True

        user_states[user_id] = {"state": "admin_order_note", "order_id": order_id}
        keyboard = admin_order_note_keyboard(order_id)
        await send_message(
            chat_id,
            f"📝 **افزودن یادداشت برای سفارش #{order_id}**\n\nلطفاً متن یادداشت را وارد کنید:",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_order_note: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع افزودن یادداشت.")
        return True


async def handle_order_note_add(chat_id: int, user_id: int, text: str) -> bool:
    """
    ذخیره یادداشت سفارش (از msg_admin صدا زده می‌شود)
    اصلاح شده با StatusMessage
    """
    try:
        order_id = user_states.get(user_id, {}).get("order_id")
        if not order_id:
            await send_message(chat_id, "❌ خطا: شناسه سفارش یافت نشد.")
            return True

        if not text or text.strip() == "":
            await send_message(chat_id, "❌ متن یادداشت نمی‌تواند خالی باشد.")
            return True

        success = add_order_note(order_id, text.strip(), user_id)
        if success:
            msg = StatusMessage.success(f"یادداشت برای سفارش #{order_id} با موفقیت اضافه شد.")
            await send_message(chat_id, msg)
        else:
            msg = StatusMessage.error(f"خطا در افزودن یادداشت برای سفارش #{order_id}.")
            await send_message(chat_id, msg)

        user_states[user_id] = {"state": "main"}
        await show_order_detail_by_id(chat_id, user_id, order_id)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_order_note_add: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در افزودن یادداشت.")
        return True


# ============================================================
# نمایش جزئیات سفارش با شناسه
# ============================================================

async def handle_order_detail(chat_id: int, user_id: int, order_id: int) -> bool:
    """
    نمایش جزئیات سفارش با دکمه‌های اقدامات
    """
    try:
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, StatusMessage.error("سفارش یافت نشد."))
            return True

        await show_order_detail(chat_id, user_id, order, "admin_orders")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_order_detail: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
        return True


async def show_order_detail_by_id(chat_id: int, user_id: int, order_id: int) -> bool:
    """
    تابع کمکی برای نمایش جزئیات سفارش با شناسه
    """
    order = get_dynamic_order_by_id(order_id)
    if not order:
        await send_message(chat_id, StatusMessage.error("سفارش یافت نشد."))
        return True

    return await show_order_detail(chat_id, user_id, order, "admin_orders")


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'show_order_detail',
    'handle_order_status_change',
    'handle_order_status_change_confirm',
    'handle_order_delete',
    'handle_order_delete_confirm',
    'handle_order_note',
    'handle_order_note_add',
    'handle_order_detail',
    'show_order_detail_by_id',
]