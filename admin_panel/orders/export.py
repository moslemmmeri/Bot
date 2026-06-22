# admin_panel/orders/export.py
# خروجی Excel و آمار سفارشات
# شامل: تولید فایل Excel، نمایش آمار سفارشات و گزارش‌های تحلیلی
# اصلاح شده با استفاده از messenger برای ارسال همزمان فایل‌ها

import traceback
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from logger_config import logger
from core import send_message, user_states
from database import get_order_stats
from keyboards.kb_admin_common import admin_order_stats_keyboard
from utils import format_number
from utils.error_handler import log_callback_error, log_general_error, log_database_error
from .grouping import handle_orders_list

# ========== ایمپورت messenger ==========
from messenger import Messenger, get_messenger, send_documents_batch


# ============================================================
# خروجی Excel (اصلاح شده با messenger)
# ============================================================

async def handle_orders_export(chat_id: int, user_id: int, filtered: bool = False) -> bool:
    """
    خروجی Excel از سفارشات (همه یا فیلتر شده) با استفاده از messenger
    
    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        filtered: آیا سفارشات فیلتر شده را خروجی بگیرد

    بازگشت: True در صورت موفقیت
    """
    try:
        from .grouping import admin_orders_date_keyboard

        if filtered:
            orders = user_states.get(user_id, {}).get("orders_list", [])
            if not orders:
                await send_message(chat_id, "❌ هیچ سفارشی برای خروجی یافت نشد.")
                return True
        else:
            from database import get_dynamic_orders
            orders = get_dynamic_orders()
            if not orders:
                await send_message(chat_id, "❌ هیچ سفارشی برای خروجی یافت نشد.")
                return True

        await send_message(chat_id, f"⏳ در حال تولید فایل Excel برای {len(orders)} سفارش...")

        from admin_panel.excel_export import export_orders_excel

        filepath = export_orders_excel(orders)

        if filepath and os.path.exists(filepath):
            # ========== ارسال با messenger ==========
            messenger = get_messenger()
            
            caption = (
                f"📊 **گزارش سفارشات**\n\n"
                f"📦 {len(orders)} سفارش\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # ارسال فایل با messenger (با قابلیت ارسال همزمان در آینده)
            result = await messenger.send_documents([
                {
                    'chat_id': chat_id,
                    'file_path': filepath,
                    'caption': caption
                }
            ])
            
            # بررسی نتیجه
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
                    # حذف فایل موقت پس از ارسال موفق
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        log_general_error(
                            f"Error removing temporary Excel file {filepath}: {str(e)}",
                            traceback=traceback.format_exc(),
                            user_id=user_id,
                            chat_id=chat_id
                        )
                    logger.info(f"✅ Excel file sent via messenger for {len(orders)} orders")
            else:
                await send_message(chat_id, "❌ خطا در ارسال فایل Excel.")
        else:
            await send_message(chat_id, "❌ خطا در تولید فایل Excel.")

        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_export: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در خروجی Excel: {str(e)}")
        return True


# ============================================================
# آمار سفارشات (بدون تغییر - با core.send_message)
# ============================================================

async def handle_orders_stats(chat_id: int, user_id: int) -> bool:
    """
    نمایش آمار سفارشات (بدون تغییر - از core.send_message استفاده می‌کند)
    
    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        stats = get_order_stats()
        
        # ========== ایمن‌سازی مقادیر عددی ==========
        total = stats.get('total', 0)
        if total is None:
            total = 0
        
        total_amount = stats.get('total_amount', 0)
        if total_amount is None:
            total_amount = 0
        
        avg_amount = stats.get('avg_amount', 0)
        if avg_amount is None:
            avg_amount = 0
        
        total_users = stats.get('total_users', 0)
        if total_users is None:
            total_users = 0
        
        top_service_count = stats.get('top_service_count', 0)
        if top_service_count is None:
            top_service_count = 0
        
        # ========== ساخت پیام با مقادیر ایمن ==========
        msg = f"📊 **آمار سفارشات**\n\n"
        msg += f"📦 تعداد کل: {format_number(total)}\n"
        msg += f"💰 مجموع مبلغ: {format_number(total_amount)} ریال\n"
        msg += f"📊 میانگین مبلغ: {format_number(int(avg_amount))} ریال\n"
        msg += f"👥 تعداد کاربران: {format_number(total_users)}\n\n"

        # تفکیک وضعیت
        statuses = stats.get('statuses', {})
        if statuses:
            msg += "📌 **تفکیک وضعیت:**\n"
            status_labels = {
                'pending': '⏳ در انتظار پرداخت',
                'paid': '✅ پرداخت شده',
                'completed': '✅ تکمیل شده',
                'cancelled': '❌ لغو شده',
                'failed': '❌ ناموفق',
                'refunded': '🔄 بازگشت وجه'
            }
            for status, count in statuses.items():
                label = status_labels.get(status, status)
                msg += f"  • {label}: {format_number(count)}\n"

        # بیشترین سرویس
        top_service_id = stats.get('top_service_id')
        if top_service_id:
            from utils import get_service_name
            service_name = get_service_name(top_service_id)
            msg += f"\n🏆 **بیشترین سرویس:** {service_name} ({format_number(top_service_count)} سفارش)"

        keyboard = admin_order_stats_keyboard(stats)
        await send_message(chat_id, msg, keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_orders_stats: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش آمار.")
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'handle_orders_export',
    'handle_orders_stats',
]