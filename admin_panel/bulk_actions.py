# admin_panel/bulk_actions.py
# مدیریت تغییرات گروهی (Bulk Actions) روی سفارشات
# شامل: انتخاب گروهی، تغییر وضعیت گروهی، حذف گروهی، خروجی گروهی و ...
# اصلاح شده با استفاده از messenger برای ارسال همزمان

import json
import csv
import os
import traceback
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from logger_config import logger
from core import send_message, OWNER_ID
from database import (
    get_dynamic_orders,
    get_dynamic_order_by_id,
    update_order_status,
    delete_order,
    get_user,
    get_button_by_id,
    get_db_connection,
)
from keyboards import admin_main_keyboard
from services.permission_service import get_permission_service
from services.state_service import get_state_service
from utils import (
    format_number,
    get_service_name,
    get_fullname_from_order,
    get_order_status_persian,
)
from admin_panel.excel_export import export_orders_excel
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error,
    log_security_error
)

# ========== ایمپورت messenger ==========
from messenger import Messenger, get_messenger, send_messages_batch, send_documents_batch, MessageBuilder


# ============================================================
# توابع کمکی (بدون تغییر)
# ============================================================

def _get_selected_orders(user_id: int) -> List[Dict]:
    """دریافت لیست سفارشات انتخاب‌شده توسط کاربر"""
    try:
        state_service = get_state_service()
        state = state_service.get_state(user_id, {})
        return state.get("bulk_selected_orders", [])
    except Exception as e:
        log_general_error(
            f"Error in _get_selected_orders for user {user_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id
        )
        return []


def _set_selected_orders(user_id: int, orders: List[Dict]) -> None:
    """ذخیره لیست سفارشات انتخاب‌شده"""
    try:
        state_service = get_state_service()
        state_service.update_state(user_id, {"bulk_selected_orders": orders})
    except Exception as e:
        log_general_error(
            f"Error in _set_selected_orders for user {user_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id
        )


def _clear_selected_orders(user_id: int) -> None:
    """پاک کردن لیست سفارشات انتخاب‌شده"""
    try:
        state_service = get_state_service()
        state_service.update_state(user_id, {"bulk_selected_orders": []})
    except Exception as e:
        log_general_error(
            f"Error in _clear_selected_orders for user {user_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id
        )


def _get_orders_for_bulk(user_id: int) -> List[Dict]:
    """دریافت لیست سفارشات برای عملیات گروهی (همه سفارشات یا فیلتر شده)"""
    try:
        state_service = get_state_service()
        state = state_service.get_state(user_id, {})
        
        filtered_orders = state.get("orders_list", [])
        if filtered_orders:
            return filtered_orders
        
        return get_dynamic_orders()
    except Exception as e:
        log_database_error(
            f"Error in _get_orders_for_bulk for user {user_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id
        )
        return []


def _get_order_brief(order: Dict) -> str:
    """دریافت خلاصه کوتاه سفارش برای نمایش در کیبورد"""
    try:
        order_id = order.get('id')
        fullname = get_fullname_from_order(order)
        amount = order.get('payment_amount', 0) or 0
        status_icon = "✅" if order.get('status') in ['paid', 'completed'] else "⏳" if order.get('status') == 'pending' else "❌"
        service = get_service_name(order.get('button_id'))
        return f"{status_icon} #{order_id} - {fullname[:12]} - {service[:12]} - {format_number(amount)} ریال"
    except Exception as e:
        log_general_error(
            f"Error in _get_order_brief: {str(e)}",
            traceback=traceback.format_exc()
        )
        return "❌ سفارش نامعتبر"


# ============================================================
# کیبوردها (بدون تغییر)
# ============================================================

def bulk_actions_main_keyboard() -> Dict:
    """کیبورد اصلی Bulk Actions"""
    return {
        "inline_keyboard": [
            [{"text": "📋 انتخاب سفارشات", "callback_data": "admin_bulk_select"}],
            [{"text": "🔄 تغییر وضعیت گروهی", "callback_data": "admin_bulk_status"}],
            [{"text": "🗑️ حذف گروهی", "callback_data": "admin_bulk_delete"}],
            [{"text": "📥 خروجی گروهی", "callback_data": "admin_bulk_export"}],
            [{"text": "🔙 برگشت به سفارشات", "callback_data": "admin_orders"}]
        ]
    }


def bulk_select_keyboard(orders: List[Dict], selected_ids: List[int], page: int = 0, per_page: int = 5) -> Dict:
    """کیبورد انتخاب سفارشات با صفحه‌بندی"""
    try:
        total = len(orders)
        start = page * per_page
        end = min(start + per_page, total)
        page_orders = orders[start:end]
        
        keyboard = []
        
        keyboard.append([
            {"text": "☑️ انتخاب همه", "callback_data": "admin_bulk_select_all"},
            {"text": "⬜ لغو همه", "callback_data": "admin_bulk_select_none"}
        ])
        
        for order in page_orders:
            order_id = order.get('id')
            is_selected = order_id in selected_ids
            check = "☑️" if is_selected else "⬜"
            brief = _get_order_brief(order)
            
            keyboard.append([
                {"text": f"{check} {brief}",
                 "callback_data": f"admin_bulk_toggle_{order_id}"}
            ])
        
        if not orders:
            keyboard.append([{"text": "❌ هیچ سفارشی یافت نشد", "callback_data": "admin_none"}])
        
        nav_row = []
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_bulk_select_page_{page-1}"})
        if page < total_pages - 1:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_bulk_select_page_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)
        
        keyboard.append([
            {"text": f"📊 {len(selected_ids)} سفارش انتخاب شده از {total}",
             "callback_data": "admin_none"}
        ])
        
        keyboard.append([
            {"text": "✅ اعمال روی انتخاب‌ها", "callback_data": "admin_bulk_actions"},
            {"text": "🔙 برگشت", "callback_data": "admin_orders"}
        ])
        
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in bulk_select_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری سفارشات", "callback_data": "admin_orders"}]]}


def bulk_status_keyboard(current_status: str = None) -> Dict:
    """کیبورد انتخاب وضعیت برای تغییر گروهی"""
    statuses = [
        ('pending', '⏳ در انتظار پرداخت'),
        ('paid', '✅ پرداخت شده'),
        ('completed', '✅ تکمیل شده'),
        ('cancelled', '❌ لغو شده'),
        ('failed', '❌ ناموفق'),
        ('refunded', '🔄 بازگشت وجه')
    ]
    
    keyboard = []
    for status, label in statuses:
        selected = "✅ " if status == current_status else ""
        keyboard.append([
            {"text": f"{selected}{label}", "callback_data": f"admin_bulk_status_set_{status}"}
        ])
    
    keyboard.append([{"text": "🔙 بازگشت", "callback_data": "admin_bulk_actions"}])
    return {"inline_keyboard": keyboard}


def bulk_delete_confirm_keyboard(count: int) -> Dict:
    """کیبورد تایید حذف گروهی"""
    return {
        "inline_keyboard": [
            [{"text": f"⚠️ آیا از حذف {count} سفارش مطمئن هستید؟"}],
            [{"text": "⚠️ این عملیات غیرقابل بازگشت است!"}],
            [{"text": "✅ بله، حذف شوند", "callback_data": "admin_bulk_delete_confirm"}],
            [{"text": "❌ خیر، انصراف", "callback_data": "admin_bulk_actions"}]
        ]
    }


def bulk_export_keyboard() -> Dict:
    """کیبورد انتخاب نوع خروجی گروهی"""
    return {
        "inline_keyboard": [
            [{"text": "📊 Excel", "callback_data": "admin_bulk_export_excel"}],
            [{"text": "📋 CSV", "callback_data": "admin_bulk_export_csv"}],
            [{"text": "📄 JSON", "callback_data": "admin_bulk_export_json"}],
            [{"text": "🔙 بازگشت", "callback_data": "admin_bulk_actions"}]
        ]
    }


# ============================================================
# توابع اصلی Bulk Actions (اصلاح شده با messenger)
# ============================================================

async def handle_bulk_actions(chat_id: int, user_id: int) -> bool:
    """نمایش منوی اصلی Bulk Actions"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = _get_selected_orders(user_id)
        count = len(selected)
        
        msg = (
            f"📦 **عملیات گروهی (Bulk Actions)**\n\n"
            f"📊 تعداد سفارشات انتخاب‌شده: {count}\n\n"
            f"از گزینه‌های زیر برای انجام عملیات گروهی استفاده کنید:\n"
            f"• انتخاب سفارشات\n"
            f"• تغییر وضعیت گروهی\n"
            f"• حذف گروهی\n"
            f"• خروجی گروهی (Excel, CSV, JSON)"
        )
        
        await send_message(chat_id, msg, bulk_actions_main_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_actions: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش عملیات گروهی.")
        return True


async def handle_bulk_select(chat_id: int, user_id: int, page: int = 0) -> bool:
    """
    نمایش صفحه انتخاب سفارشات (بدون تغییر - فقط پیام متنی ارسال می‌کند)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        orders = _get_orders_for_bulk(user_id)
        selected = _get_selected_orders(user_id)
        selected_ids = [o.get('id') for o in selected if o.get('id')]
        
        keyboard = bulk_select_keyboard(orders, selected_ids, page)
        
        total = len(orders)
        per_page = 5
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        await send_message(
            chat_id,
            f"📋 **انتخاب سفارشات - صفحه {page + 1} از {total_pages}**\n\n"
            f"برای انتخاب/لغو انتخاب هر سفارش کلیک کنید.\n"
            f"سفارشات انتخاب‌شده: {len(selected_ids)} عدد",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_select: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش انتخاب سفارشات.")
        return True


async def handle_bulk_toggle(chat_id: int, user_id: int, order_id: int) -> bool:
    """
    تغییر انتخاب یک سفارش (بدون تغییر - فقط پیام متنی ارسال می‌کند)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True
        
        selected = _get_selected_orders(user_id)
        selected_ids = [o.get('id') for o in selected if o.get('id')]
        
        if order_id in selected_ids:
            selected = [o for o in selected if o.get('id') != order_id]
        else:
            selected.append(order)
        
        _set_selected_orders(user_id, selected)
        
        return await handle_bulk_select(chat_id, user_id, 0)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_toggle for order {order_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر انتخاب.")
        return True


async def handle_bulk_select_all(chat_id: int, user_id: int) -> bool:
    """انتخاب همه سفارشات (بدون تغییر)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        orders = _get_orders_for_bulk(user_id)
        _set_selected_orders(user_id, orders)
        
        await send_message(chat_id, f"✅ {len(orders)} سفارش انتخاب شدند.")
        return await handle_bulk_select(chat_id, user_id, 0)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_select_all: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب همه سفارشات.")
        return True


async def handle_bulk_select_none(chat_id: int, user_id: int) -> bool:
    """لغو انتخاب همه سفارشات (بدون تغییر)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        _clear_selected_orders(user_id)
        
        await send_message(chat_id, "✅ همه انتخاب‌ها لغو شدند.")
        return await handle_bulk_select(chat_id, user_id, 0)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_select_none: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در لغو انتخاب همه سفارشات.")
        return True


async def handle_bulk_select_page(chat_id: int, user_id: int, page: int) -> bool:
    """صفحه‌بندی انتخاب سفارشات (بدون تغییر)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        return await handle_bulk_select(chat_id, user_id, page)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_select_page: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی.")
        return True


async def handle_bulk_status(chat_id: int, user_id: int) -> bool:
    """نمایش صفحه انتخاب وضعیت برای تغییر گروهی (بدون تغییر)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = _get_selected_orders(user_id)
        if not selected:
            await send_message(
                chat_id,
                "❌ هیچ سفارشی انتخاب نشده است.\n"
                "لطفاً ابتدا از بخش «انتخاب سفارشات» سفارش‌های مورد نظر را انتخاب کنید."
            )
            return True
        
        await send_message(
            chat_id,
            f"🔄 **تغییر وضعیت گروهی**\n\n"
            f"تعداد سفارشات انتخاب‌شده: {len(selected)}\n\n"
            f"وضعیت جدید را انتخاب کنید:",
            bulk_status_keyboard()
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_status: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش تغییر وضعیت گروهی.")
        return True


async def handle_bulk_status_set(chat_id: int, user_id: int, new_status: str) -> bool:
    """اعمال تغییر وضعیت گروهی (بدون تغییر)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = _get_selected_orders(user_id)
        if not selected:
            await send_message(chat_id, "❌ هیچ سفارشی انتخاب نشده است.")
            return True
        
        valid_statuses = ['pending', 'paid', 'completed', 'cancelled', 'failed', 'refunded']
        if new_status not in valid_statuses:
            await send_message(chat_id, "❌ وضعیت نامعتبر.")
            return True
        
        success_count = 0
        failed_count = 0
        failed_orders = []
        
        for order in selected:
            order_id = order.get('id')
            try:
                success = update_order_status(order_id, new_status, user_id, note=f"تغییر وضعیت گروهی توسط ادمین")
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_orders.append(order_id)
            except Exception as e:
                failed_count += 1
                failed_orders.append(order_id)
                log_database_error(
                    f"Error updating order {order_id} status to {new_status}: {str(e)}",
                    traceback=traceback.format_exc(),
                    user_id=user_id,
                    chat_id=chat_id
                )
        
        msg = f"✅ **نتیجه تغییر وضعیت گروهی**\n\n"
        msg += f"📌 وضعیت جدید: {new_status}\n"
        msg += f"✅ موفق: {success_count}\n"
        msg += f"❌ ناموفق: {failed_count}\n"
        
        if failed_orders:
            msg += f"\n⚠️ سفارشات ناموفق:\n"
            for oid in failed_orders[:10]:
                msg += f"  • #{oid}\n"
            if len(failed_orders) > 10:
                msg += f"  ... و {len(failed_orders) - 10} مورد دیگر\n"
        
        await send_message(chat_id, msg)
        
        _clear_selected_orders(user_id)
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_status_set: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر وضعیت گروهی.")
        return True


async def handle_bulk_delete(chat_id: int, user_id: int) -> bool:
    """نمایش تاییدیه حذف گروهی سفارشات (بدون تغییر)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = _get_selected_orders(user_id)
        if not selected:
            await send_message(
                chat_id,
                "❌ هیچ سفارشی انتخاب نشده است.\n"
                "لطفاً ابتدا از بخش «انتخاب سفارشات» سفارش‌های مورد نظر را انتخاب کنید."
            )
            return True
        
        deletable = [o for o in selected if o.get('status') in ['pending', 'cancelled']]
        non_deletable = [o for o in selected if o.get('status') not in ['pending', 'cancelled']]
        
        if not deletable:
            await send_message(
                chat_id,
                f"❌ هیچ یک از {len(selected)} سفارش انتخاب‌شده قابل حذف نیستند.\n"
                f"فقط سفارشات با وضعیت «در انتظار پرداخت» یا «لغو شده» قابل حذف هستند."
            )
            return True
        
        msg = f"🗑️ **حذف گروهی سفارشات**\n\n"
        msg += f"📊 سفارشات قابل حذف: {len(deletable)}\n"
        
        if non_deletable:
            msg += f"⚠️ سفارشات غیرقابل حذف (وضعیت نامناسب): {len(non_deletable)}\n"
        
        keyboard = bulk_delete_confirm_keyboard(len(deletable))
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_delete: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش حذف گروهی.")
        return True


async def handle_bulk_delete_confirm(chat_id: int, user_id: int) -> bool:
    """اجرای حذف گروهی سفارشات (بدون تغییر)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = _get_selected_orders(user_id)
        deletable = [o for o in selected if o.get('status') in ['pending', 'cancelled']]
        
        if not deletable:
            await send_message(chat_id, "❌ هیچ سفارش قابل حذفی وجود ندارد.")
            return True
        
        success_count = 0
        failed_count = 0
        failed_orders = []
        
        for order in deletable:
            order_id = order.get('id')
            try:
                success = delete_order(order_id)
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_orders.append(order_id)
            except Exception as e:
                failed_count += 1
                failed_orders.append(order_id)
                log_database_error(
                    f"Error deleting order {order_id}: {str(e)}",
                    traceback=traceback.format_exc(),
                    user_id=user_id,
                    chat_id=chat_id
                )
        
        msg = f"✅ **نتیجه حذف گروهی**\n\n"
        msg += f"✅ موفق: {success_count}\n"
        msg += f"❌ ناموفق: {failed_count}\n"
        
        if failed_orders:
            msg += f"\n⚠️ سفارشات ناموفق:\n"
            for oid in failed_orders[:10]:
                msg += f"  • #{oid}\n"
            if len(failed_orders) > 10:
                msg += f"  ... و {len(failed_orders) - 10} مورد دیگر\n"
        
        await send_message(chat_id, msg)
        
        _clear_selected_orders(user_id)
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_delete_confirm: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف گروهی سفارشات.")
        return True


async def handle_bulk_export(chat_id: int, user_id: int) -> bool:
    """نمایش صفحه انتخاب نوع خروجی گروهی (بدون تغییر)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = _get_selected_orders(user_id)
        if not selected:
            await send_message(
                chat_id,
                "❌ هیچ سفارشی انتخاب نشده است.\n"
                "لطفاً ابتدا از بخش «انتخاب سفارشات» سفارش‌های مورد نظر را انتخاب کنید."
            )
            return True
        
        await send_message(
            chat_id,
            f"📥 **خروجی گروهی سفارشات**\n\n"
            f"تعداد سفارشات انتخاب‌شده: {len(selected)}\n\n"
            f"نوع خروجی مورد نظر را انتخاب کنید:",
            bulk_export_keyboard()
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_export: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش خروجی گروهی.")
        return True


# ============================================================
# توابع خروجی گروهی (اصلاح شده با messenger)
# ============================================================

async def handle_bulk_export_excel(chat_id: int, user_id: int) -> bool:
    """
    خروجی Excel از سفارشات انتخاب‌شده با استفاده از messenger
    
    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = _get_selected_orders(user_id)
        if not selected:
            await send_message(chat_id, "❌ هیچ سفارشی انتخاب نشده است.")
            return True
        
        await send_message(chat_id, f"⏳ در حال تولید فایل Excel برای {len(selected)} سفارش...")
        
        filepath = export_orders_excel(selected)
        
        if filepath and os.path.exists(filepath):
            # ========== ارسال با messenger ==========
            messenger = get_messenger()
            
            caption = (
                f"📊 **خروجی گروهی سفارشات**\n\n"
                f"📦 {len(selected)} سفارش\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            result = await messenger.send_documents([
                {
                    'chat_id': chat_id,
                    'file_path': filepath,
                    'caption': caption
                }
            ])
            
            if result and len(result) > 0:
                if isinstance(result[0], Exception):
                    log_general_error(
                        f"Error sending Excel file via messenger: {result[0]}",
                        traceback=traceback.format_exc(),
                        user_id=user_id,
                        chat_id=chat_id
                    )
                    await send_message(chat_id, "❌ خطا در ارسال فایل Excel.")
                else:
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    logger.info(f"✅ Bulk Excel file sent via messenger for {len(selected)} orders")
            else:
                await send_message(chat_id, "❌ خطا در ارسال فایل Excel.")
        else:
            await send_message(chat_id, "❌ خطا در تولید فایل Excel.")
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_export_excel: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در خروجی Excel: {str(e)}")
        return True


async def handle_bulk_export_csv(chat_id: int, user_id: int) -> bool:
    """
    خروجی CSV از سفارشات انتخاب‌شده با استفاده از messenger
    
    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = _get_selected_orders(user_id)
        if not selected:
            await send_message(chat_id, "❌ هیچ سفارشی انتخاب نشده است.")
            return True
        
        await send_message(chat_id, f"⏳ در حال تولید فایل CSV برای {len(selected)} سفارش...")
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            headers = ['شناسه', 'شناسه کاربر', 'نام کاربر', 'سرویس', 'مبلغ (ریال)', 'وضعیت', 'کد رهگیری', 'تاریخ ثبت', 'یادداشت']
            writer.writerow(headers)
            
            for order in selected:
                row = [
                    order.get('id', ''),
                    order.get('user_id', ''),
                    get_fullname_from_order(order),
                    get_service_name(order.get('button_id')),
                    order.get('payment_amount', 0) or 0,
                    get_order_status_persian(order.get('status', 'pending')),
                    order.get('tracking_code', ''),
                    order.get('created_at', ''),
                    order.get('admin_note', ''),
                ]
                writer.writerow(row)
            
            filepath = f.name
        
        if filepath and os.path.exists(filepath):
            # ========== ارسال با messenger ==========
            messenger = get_messenger()
            
            caption = (
                f"📋 **خروجی CSV سفارشات**\n\n"
                f"📦 {len(selected)} سفارش\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            result = await messenger.send_documents([
                {
                    'chat_id': chat_id,
                    'file_path': filepath,
                    'caption': caption
                }
            ])
            
            if result and len(result) > 0:
                if isinstance(result[0], Exception):
                    log_general_error(
                        f"Error sending CSV file via messenger: {result[0]}",
                        traceback=traceback.format_exc(),
                        user_id=user_id,
                        chat_id=chat_id
                    )
                    await send_message(chat_id, "❌ خطا در ارسال فایل CSV.")
                else:
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    logger.info(f"✅ Bulk CSV file sent via messenger for {len(selected)} orders")
            else:
                await send_message(chat_id, "❌ خطا در ارسال فایل CSV.")
        else:
            await send_message(chat_id, "❌ خطا در تولید فایل CSV.")
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_export_csv: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در خروجی CSV: {str(e)}")
        return True


async def handle_bulk_export_json(chat_id: int, user_id: int) -> bool:
    """
    خروجی JSON از سفارشات انتخاب‌شده با استفاده از messenger
    
    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = _get_selected_orders(user_id)
        if not selected:
            await send_message(chat_id, "❌ هیچ سفارشی انتخاب نشده است.")
            return True
        
        await send_message(chat_id, f"⏳ در حال تولید فایل JSON برای {len(selected)} سفارش...")
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(selected, f, ensure_ascii=False, indent=2, default=str)
            filepath = f.name
        
        if filepath and os.path.exists(filepath):
            # ========== ارسال با messenger ==========
            messenger = get_messenger()
            
            caption = (
                f"📄 **خروجی JSON سفارشات**\n\n"
                f"📦 {len(selected)} سفارش\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            result = await messenger.send_documents([
                {
                    'chat_id': chat_id,
                    'file_path': filepath,
                    'caption': caption
                }
            ])
            
            if result and len(result) > 0:
                if isinstance(result[0], Exception):
                    log_general_error(
                        f"Error sending JSON file via messenger: {result[0]}",
                        traceback=traceback.format_exc(),
                        user_id=user_id,
                        chat_id=chat_id
                    )
                    await send_message(chat_id, "❌ خطا در ارسال فایل JSON.")
                else:
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    logger.info(f"✅ Bulk JSON file sent via messenger for {len(selected)} orders")
            else:
                await send_message(chat_id, "❌ خطا در ارسال فایل JSON.")
        else:
            await send_message(chat_id, "❌ خطا در تولید فایل JSON.")
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_bulk_export_json: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در خروجی JSON: {str(e)}")
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'handle_bulk_actions',
    'handle_bulk_select',
    'handle_bulk_toggle',
    'handle_bulk_select_all',
    'handle_bulk_select_none',
    'handle_bulk_select_page',
    'handle_bulk_status',
    'handle_bulk_status_set',
    'handle_bulk_delete',
    'handle_bulk_delete_confirm',
    'handle_bulk_export',
    'handle_bulk_export_excel',
    'handle_bulk_export_csv',
    'handle_bulk_export_json',
]