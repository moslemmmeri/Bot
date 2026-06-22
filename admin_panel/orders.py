# admin_panel/orders.py
# مدیریت سفارشات در پنل ادمین - نسخه کامل با تمام قابلیت‌ها
# شامل: گروه‌بندی سه‌لایه، فیلتر، جستجو، تغییر وضعیت، حذف، یادداشت، آمار و خروجی Excel
# پشتیبانی از فیلترهای پیشرفته (بازه زمانی، نوع سرویس، وضعیت، محدوده مبلغ، کاربر)

import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from logger_config import logger
from core import send_message, send_photo, send_document, user_states, OWNER_ID
from database import (
    get_dynamic_orders,
    get_dynamic_order_by_id,
    get_button_by_id,
    search_orders,
    update_order_status,
    delete_order,
    add_order_note,
    get_order_stats,
    get_orders_for_reminder,
    update_reminder_time,
)
from keyboards import admin_main_keyboard
from keyboards.kb_admin_common import (
    admin_orders_menu_keyboard,
    admin_orders_filter_keyboard,
    admin_orders_filter_service_keyboard,
    admin_orders_status_keyboard,
    admin_order_delete_confirm_keyboard,
    admin_order_detail_actions_keyboard,
    admin_order_note_keyboard,
    admin_order_stats_keyboard,
    admin_orders_search_keyboard,
    admin_orders_export_keyboard
)
from .common import extract_date_from_order, get_service_name, get_fullname_from_order
from .filters import AdvancedFilters, get_filter_manager
from .excel_export import export_orders_excel


# ==================== توابع کیبورد ====================

def admin_orders_date_keyboard(orders, page=0, per_page=5):
    """
    مرحله ۱: نمایش لیست تاریخ‌ها (گروه‌بندی بر اساس تاریخ)
    """
    try:
        date_groups = {}
        for order in orders:
            date_str = extract_date_from_order(order)
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
        logger.error(f"Error in admin_orders_date_keyboard: {e}", exc_info=True)
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری تاریخ‌ها", "callback_data": "admin_back"}]]}


def admin_orders_service_keyboard(orders, date_str, page=0, per_page=5):
    """
    مرحله ۲: نمایش سرویس‌های یک تاریخ خاص
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
        logger.error(f"Error in admin_orders_service_keyboard: {e}", exc_info=True)
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری سرویس‌ها", "callback_data": "admin_back"}]]}


def admin_orders_user_keyboard(orders, date_str, button_id, page=0, per_page=5):
    """
    مرحله ۳: نمایش کاربرانی که یک سرویس خاص را در تاریخ مشخص ثبت کرده‌اند
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
                {"text": f"{status_icon} {fullname} - {total_amount:,} ریال", 
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
        logger.error(f"Error in admin_orders_user_keyboard: {e}", exc_info=True)
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری کاربران", "callback_data": f"admin_orders_service_back_{date_str}"}]]}


# ==================== نمایش جزئیات سفارش ====================

async def show_order_detail(chat_id, user_id, order, back_callback):
    """نمایش جزئیات کامل یک سفارش با دکمه بازگشت و ارسال فایل‌های ضمیمه"""
    try:
        order_data = order.get('order_data', {})
        if isinstance(order_data, str):
            try:
                order_data = json.loads(order_data)
            except json.JSONDecodeError:
                logger.warning(f"خطا در دیکد کردن order_data برای سفارش {order.get('id')}")
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
        
        msg = f"📋 **جزئیات سفارش #{order['id']}**\n\n"
        msg += f"👤 کاربر: {fullname}\n"
        msg += f"🆔 شناسه کاربر: {order.get('user_id', 'نامشخص')}\n"
        msg += f"🔘 سرویس: {service_name}\n"
        msg += f"💰 مبلغ: {payment_amount:,} ریال\n"
        msg += f"🎫 کد رهگیری: {order.get('tracking_code', 'ندارد') or 'ندارد'}\n"
        msg += f"📌 وضعیت: {status_text}\n"
        msg += f"⏰ زمان ثبت: {order.get('created_at', 'نامشخص') or 'نامشخص'}\n\n"
        
        admin_note = order.get('admin_note')
        if admin_note:
            msg += f"📝 **یادداشت ادمین:**\n{admin_note}\n\n"
        
        msg += "📝 **پاسخ‌های کاربر:**\n"
        answers = order_data.get('answers', {})
        if answers:
            for q_text, ans in answers.items():
                msg += f"▪️ {q_text}: {ans}\n"
        else:
            msg += "▪️ پاسخی ثبت نشده است.\n"
        
        keyboard = admin_order_detail_actions_keyboard(order['id'], order.get('status', 'pending'))
        await send_message(chat_id, msg, keyboard)
        
        # ارسال فایل‌های ضمیمه
        files = order_data.get('files', {})
        if files:
            for question_text, file_info in files.items():
                file_id = file_info.get('file_id')
                file_type = file_info.get('type', 'document')
                caption = f"📎 {question_text}"
                try:
                    if file_type == 'photo':
                        await send_photo(chat_id, file_id, caption)
                    else:
                        await send_document(chat_id, file_id, caption)
                except Exception as e:
                    logger.error(f"خطا در ارسال فایل برای سفارش {order.get('id')}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in show_order_detail for order {order.get('id')}: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
        return True


# ==================== توابع اصلی مدیریت سفارشات ====================

async def handle_orders_group_by_date(chat_id, user_id):
    """گروه‌بندی سفارشات بر اساس تاریخ"""
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
        logger.error(f"Error in handle_orders_group_by_date: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش لیست سفارشات.")
        return True


async def handle_orders_list(chat_id, user_id):
    """منوی اصلی سفارشات"""
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
        logger.error(f"Error in handle_orders_list: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش منوی سفارشات.")
        return True


async def handle_orders_date_page(chat_id, user_id, data):
    """صفحه‌بندی تاریخ‌ها (admin_orders_date_page_*)"""
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
        await send_message(chat_id, f"📋 **لیست تاریخ‌ها - صفحه {page+1}**", keyboard)
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_orders_date_page: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در صفحه‌بندی تاریخ‌ها.")
        return True


async def handle_orders_date(chat_id, user_id, data):
    """انتخاب تاریخ و نمایش سرویس‌های آن (admin_orders_date_*)"""
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
        logger.error(f"Error in handle_orders_date: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش سرویس‌های تاریخ.")
        return True


async def handle_orders_service_page(chat_id, user_id, data):
    """صفحه‌بندی سرویس‌ها (admin_orders_service_page_*)"""
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
        await send_message(chat_id, f"📋 **سرویس‌های تاریخ {date_str} - صفحه {page+1}**", keyboard)
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_orders_service_page: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در صفحه‌بندی سرویس‌ها.")
        return True


async def handle_orders_service_back(chat_id, user_id, data):
    """بازگشت از مرحله سرویس به تاریخ‌ها (admin_orders_service_back_*)"""
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
        logger.error(f"Error in handle_orders_service_back: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در بازگشت به تاریخ‌ها.")
        return True


async def handle_orders_service(chat_id, user_id, data):
    """انتخاب سرویس و نمایش کاربران آن (admin_orders_service_*)"""
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
        logger.error(f"Error in handle_orders_service: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش کاربران سرویس.")
        return True


async def handle_orders_user_page(chat_id, user_id, data):
    """صفحه‌بندی کاربران (admin_orders_user_page_*)"""
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
        await send_message(chat_id, f"👤 **کاربران سرویس «{service_name}» - صفحه {page+1}**", keyboard)
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_orders_user_page: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در صفحه‌بندی کاربران.")
        return True


async def handle_orders_user(chat_id, user_id, data):
    """انتخاب کاربر و نمایش جزئیات سفارش (admin_orders_user_*)"""
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
        back_callback = f"admin_orders_service_{date_str}_{button_id}"
        await show_order_detail(chat_id, user_id, order, back_callback)
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_orders_user: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش کاربر.")
        return True


async def handle_order_by_id(chat_id, user_id, data):
    """نمایش جزئیات سفارش با شناسه (admin_order_*) - برای سازگاری با کالبک قبلی"""
    try:
        logger.info(f"=== handle_order_by_id CALLED ===")
        order_id = int(data.split("_")[2]) if len(data.split("_")) > 2 else 0
        if not order_id:
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
        logger.error(f"Error in handle_order_by_id: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
        return True


# ==================== توابع جدید مدیریت پیشرفته سفارشات ====================

async def handle_orders_filter_start(chat_id, user_id):
    """شروع فیلتر سفارشات"""
    try:
        current_filters = user_states.get(user_id, {}).get("orders_filters", {})
        current_status = current_filters.get('status')
        current_service = current_filters.get('button_id')
        
        keyboard = admin_orders_filter_keyboard(current_status=current_status, current_service=current_service)
        await send_message(chat_id, "🎯 **فیلتر سفارشات**\n\nوضعیت یا سرویس مورد نظر را انتخاب کنید:", keyboard)
        return True
    except Exception as e:
        logger.error(f"Error in handle_orders_filter_start: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش فیلتر.")
        return True


async def handle_orders_filter_status(chat_id, user_id, data):
    """انتخاب وضعیت برای فیلتر"""
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
        await send_message(chat_id, f"🎯 **فیلتر سفارشات**\n\nوضعیت انتخاب‌شده: {status_text}", keyboard)
        return True
    except Exception as e:
        logger.error(f"Error in handle_orders_filter_status: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در انتخاب وضعیت.")
        return True


async def handle_orders_filter_service(chat_id, user_id, data):
    """نمایش لیست سرویس‌ها برای انتخاب فیلتر"""
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
        logger.error(f"Error in handle_orders_filter_service: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش سرویس‌ها.")
        return True


async def handle_orders_filter_service_select(chat_id, user_id, data):
    """انتخاب سرویس برای فیلتر"""
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
        await send_message(chat_id, f"🎯 **فیلتر سفارشات**\n\nسرویس انتخاب‌شده: {service_name}", keyboard)
        return True
    except Exception as e:
        logger.error(f"Error in handle_orders_filter_service_select: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در انتخاب سرویس.")
        return True


async def handle_orders_filter_apply(chat_id, user_id):
    """اعمال فیلترهای انتخاب‌شده و نمایش نتایج"""
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
        
        keyboard = admin_orders_date_keyboard(filtered_orders, page=0)
        status_text = f"وضعیت: {status_filter or 'همه'}"
        service_text = ""
        if service_filter:
            btn = get_button_by_id(service_filter)
            service_text = f"سرویس: {btn['name'] if btn else service_filter}"
        filter_info = f" ({status_text} {service_text})".strip()
        await send_message(chat_id, f"📋 **نتایج فیلتر{filter_info}**\nتعداد: {len(filtered_orders)} سفارش", keyboard)
        return True
    except Exception as e:
        logger.error(f"Error in handle_orders_filter_apply: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در اعمال فیلتر.")
        return True


async def handle_orders_filter_clear(chat_id, user_id):
    """پاک کردن فیلترها"""
    try:
        logger.info(f"=== handle_orders_filter_clear CALLED ===")
        if user_id in user_states:
            user_states[user_id].pop("orders_filters", None)
            user_states[user_id].pop("orders_list", None)
        await send_message(chat_id, "✅ فیلترها پاک شدند.")
        return await handle_orders_filter_start(chat_id, user_id)
    except Exception as e:
        logger.error(f"Error in handle_orders_filter_clear: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در پاک کردن فیلتر.")
        return True


async def handle_orders_search(chat_id, user_id):
    """شروع جستجوی سفارشات"""
    try:
        user_states[user_id] = {"state": "admin_orders_search"}
        keyboard = admin_orders_search_keyboard()
        await send_message(chat_id, "🔍 **جستجوی سفارشات**\n\nلطفاً کلمه کلیدی (کد رهگیری، نام کاربر یا شناسه سفارش) را وارد کنید:", keyboard)
        return True
    except Exception as e:
        logger.error(f"Error in handle_orders_search: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در شروع جستجو.")
        return True


async def handle_orders_search_result(chat_id, user_id, keyword):
    """نمایش نتایج جستجو"""
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
        
        keyboard = admin_orders_date_keyboard(results, page=0)
        await send_message(chat_id, f"🔍 **نتایج جستجو برای «{keyword}»**\nتعداد: {len(results)} سفارش", keyboard)
        user_states[user_id]["state"] = "main"
        return True
    except Exception as e:
        logger.error(f"Error in handle_orders_search_result: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در جستجو.")
        return True


async def handle_orders_stats(chat_id, user_id):
    """نمایش آمار سفارشات"""
    try:
        stats = get_order_stats()
        keyboard = admin_order_stats_keyboard(stats)
        await send_message(chat_id, "📊 **آمار سفارشات**", keyboard)
        return True
    except Exception as e:
        logger.error(f"Error in handle_orders_stats: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش آمار.")
        return True


async def handle_orders_export(chat_id, user_id, filtered=False):
    """خروجی Excel از سفارشات (همه یا فیلتر شده)"""
    try:
        if filtered:
            orders = user_states.get(user_id, {}).get("orders_list", [])
            if not orders:
                await send_message(chat_id, "❌ هیچ سفارشی برای خروجی یافت نشد.")
                return True
        else:
            orders = get_dynamic_orders()
            if not orders:
                await send_message(chat_id, "❌ هیچ سفارشی برای خروجی یافت نشد.")
                return True
        
        await send_message(chat_id, f"⏳ در حال تولید فایل Excel برای {len(orders)} سفارش...")
        
        filepath = export_orders_excel(orders)
        
        if filepath and os.path.exists(filepath):
            await send_document(
                chat_id,
                file_path=filepath,
                caption=f"📊 **گزارش سفارشات**\n\n📦 {len(orders)} سفارش\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            try:
                os.remove(filepath)
            except:
                pass
        else:
            await send_message(chat_id, "❌ خطا در تولید فایل Excel.")
        
        return True
    except Exception as e:
        logger.error(f"Error in handle_orders_export: {e}", exc_info=True)
        await send_message(chat_id, f"❌ خطا در خروجی Excel: {str(e)}")
        return True


async def handle_order_status_change(chat_id, user_id, data):
    """شروع تغییر وضعیت سفارش"""
    try:
        order_id = int(data.split("_")[-1])
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True
        
        current_status = order.get('status', 'pending')
        keyboard = admin_orders_status_keyboard(order_id, current_status)
        await send_message(chat_id, f"🔄 **تغییر وضعیت سفارش #{order_id}**\nوضعیت فعلی: {current_status}", keyboard)
        return True
    except Exception as e:
        logger.error(f"Error in handle_order_status_change: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در تغییر وضعیت.")
        return True


async def handle_order_status_change_confirm(chat_id, user_id, data):
    """اعمال تغییر وضعیت سفارش"""
    try:
        parts = data.split("_")
        order_id = int(parts[4])
        new_status = parts[5]
        
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True
        
        success = update_order_status(order_id, new_status, user_id, note=f"تغییر وضعیت توسط ادمین")
        if success:
            await send_message(chat_id, f"✅ وضعیت سفارش #{order_id} به «{new_status}» تغییر یافت.")
        else:
            await send_message(chat_id, f"❌ خطا در تغییر وضعیت سفارش #{order_id}.")
        
        await handle_order_by_id(chat_id, user_id, f"admin_order_{order_id}")
        return True
    except Exception as e:
        logger.error(f"Error in handle_order_status_change_confirm: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در تغییر وضعیت.")
        return True


async def handle_order_delete(chat_id, user_id, data):
    """نمایش تایید حذف سفارش"""
    try:
        order_id = int(data.split("_")[-1])
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True
        
        keyboard = admin_order_delete_confirm_keyboard(order_id)
        await send_message(chat_id, f"⚠️ **هشدار حذف سفارش #{order_id}**\nآیا از حذف این سفارش مطمئن هستید؟", keyboard)
        return True
    except Exception as e:
        logger.error(f"Error in handle_order_delete: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در شروع حذف.")
        return True


async def handle_order_delete_confirm(chat_id, user_id, data):
    """اجرای حذف سفارش"""
    try:
        order_id = int(data.split("_")[-1])
        success = delete_order(order_id)
        if success:
            await send_message(chat_id, f"✅ سفارش #{order_id} با موفقیت حذف شد.")
        else:
            await send_message(chat_id, f"❌ خطا در حذف سفارش #{order_id}.")
        
        await handle_orders_list(chat_id, user_id)
        return True
    except Exception as e:
        logger.error(f"Error in handle_order_delete_confirm: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در حذف سفارش.")
        return True


async def handle_order_note(chat_id, user_id, data):
    """شروع افزودن یادداشت به سفارش"""
    try:
        order_id = int(data.split("_")[-1])
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True
        
        user_states[user_id] = {"state": "admin_order_note", "order_id": order_id}
        keyboard = admin_order_note_keyboard(order_id)
        await send_message(chat_id, f"📝 **افزودن یادداشت برای سفارش #{order_id}**\n\nلطفاً متن یادداشت را وارد کنید:", keyboard)
        return True
    except Exception as e:
        logger.error(f"Error in handle_order_note: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در شروع افزودن یادداشت.")
        return True


async def handle_order_note_add(chat_id, user_id, text):
    """ذخیره یادداشت سفارش"""
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
            await send_message(chat_id, f"✅ یادداشت برای سفارش #{order_id} با موفقیت اضافه شد.")
        else:
            await send_message(chat_id, f"❌ خطا در افزودن یادداشت برای سفارش #{order_id}.")
        
        user_states[user_id] = {"state": "main"}
        await handle_order_by_id(chat_id, user_id, f"admin_order_{order_id}")
        return True
    except Exception as e:
        logger.error(f"Error in handle_order_note_add: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در افزودن یادداشت.")
        return True


async def handle_order_detail(chat_id, user_id, order_id):
    """نمایش جزئیات سفارش با دکمه‌های اقدامات"""
    try:
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True
        
        await show_order_detail(chat_id, user_id, order, "admin_orders")
        return True
    except Exception as e:
        logger.error(f"Error in handle_order_detail: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
        return True


# ==================== یادآوری سفارشات ====================

async def handle_order_reminder(chat_id, user_id):
    """نمایش لیست سفارشات نیازمند یادآوری و ارسال دستی"""
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
        
        keyboard = {
            "inline_keyboard": [
                [{"text": f"📋 {len(orders)} سفارش نیازمند یادآوری"}],
            ]
        }
        
        for order in orders[:10]:
            order_id = order.get('id')
            user_id_order = order.get('user_id')
            created_at = order.get('created_at', '')
            amount = order.get('payment_amount', 0) or 0
            keyboard["inline_keyboard"].append([
                {"text": f"🆔 #{order_id} - کاربر {user_id_order} - {amount:,} ریال",
                 "callback_data": f"admin_order_remind_{order_id}"}
            ])
        
        keyboard["inline_keyboard"].append([
            {"text": "📨 ارسال یادآوری به همه", "callback_data": "admin_order_remind_all"}
        ])
        keyboard["inline_keyboard"].append([
            {"text": "🔙 برگشت", "callback_data": "admin_orders"}
        ])
        
        await send_message(
            chat_id,
            f"⏰ **یادآوری سفارشات ناتمام**\n\n"
            f"{len(orders)} سفارش نیاز به یادآوری دارند.\n"
            f"(سفارشاتی که بیش از {hours} ساعت از ثبت آنها گذشته)",
            keyboard
        )
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_order_reminder: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در نمایش سفارشات نیازمند یادآوری.")
        return True


async def handle_order_remind_single(chat_id, user_id, data):
    """ارسال یادآوری برای یک سفارش خاص"""
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
        logger.error(f"Error in handle_order_remind_single: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در ارسال یادآوری.")
        return True


async def handle_order_remind_all(chat_id, user_id):
    """ارسال یادآوری به همه سفارشات ناتمام"""
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
        logger.error(f"Error in handle_order_remind_all: {e}", exc_info=True)
        await send_message(chat_id, "❌ خطا در ارسال یادآوری گروهی.")
        return True


__all__ = [
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
    'handle_orders_filter_start',
    'handle_orders_filter_status',
    'handle_orders_filter_service',
    'handle_orders_filter_service_select',
    'handle_orders_filter_apply',
    'handle_orders_filter_clear',
    'handle_orders_search',
    'handle_orders_search_result',
    'handle_orders_stats',
    'handle_orders_export',
    'handle_order_status_change',
    'handle_order_status_change_confirm',
    'handle_order_delete',
    'handle_order_delete_confirm',
    'handle_order_note',
    'handle_order_note_add',
    'handle_order_detail',
    'show_order_detail',
    'handle_order_reminder',
    'handle_order_remind_single',
    'handle_order_remind_all',
]