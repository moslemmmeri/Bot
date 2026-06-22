# profile.py
# پروفایل کاربری و تاریخچه سفارشات - نسخه نهایی اصلاح‌شده با مدیریت خطا و لاگ‌گیری کامل

import json
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Dict, List, Optional, Any
from datetime import datetime

from logger_config import logger
from core import send_message, send_photo, send_document, get_main_menu_with_admin
from utils.error_handler import log_error
from database import (
    get_user,
    get_user_orders_count,
    get_user_total_payment,
    get_dynamic_orders,
    get_dynamic_order_by_id,
    get_button_by_id,
    update_order_status,
    upsert_user,
)
from utils import (
    format_number,
    format_datetime,
    get_service_name,
    get_fullname_from_order,
    get_order_status_persian,
    get_user_display_name,
)


# ============================================================
# کیبوردها
# ============================================================

def profile_main_keyboard(user_id: int) -> Dict:
    """کیبورد اصلی پروفایل کاربری"""
    return {
        "inline_keyboard": [
            [{"text": "📋 تاریخچه سفارشات", "callback_data": f"profile_orders_{user_id}"}],
            [{"text": "📊 آمار من", "callback_data": f"profile_stats_{user_id}"}],
            [{"text": "🔙 بازگشت به منو", "callback_data": "back_main"}]
        ]
    }


def profile_orders_keyboard(orders: List[Dict], user_id: int, page: int = 0, per_page: int = 5) -> Dict:
    """
    کیبورد نمایش لیست سفارشات کاربر با مدیریت خطا
    
    پارامترها:
        orders: لیست سفارشات
        user_id: شناسه کاربر (برای بازگشت به پروفایل)
        page: شماره صفحه
        per_page: تعداد آیتم در هر صفحه
    
    بازگشت: کیبورد (دیکشنری)
    """
    try:
        total = len(orders)
        start = page * per_page
        end = min(start + per_page, total)
        page_orders = orders[start:end]

        keyboard = []

        if not page_orders:
            keyboard.append([{"text": "📭 هیچ سفارشی یافت نشد", "callback_data": "profile_none"}])
        else:
            for order in page_orders:
                try:
                    order_id = order.get('id')
                    if not order_id:
                        continue
                    
                    status = order.get('status', 'pending')
                    status_icon = "✅" if status == "paid" else "⏳" if status == "pending" else "❌"
                    service_name = get_service_name(order.get('button_id'))
                    amount = order.get('payment_amount', 0) or 0

                    # محدود کردن طول نام سرویس برای نمایش بهتر
                    if len(service_name) > 15:
                        service_name = service_name[:15] + "..."

                    keyboard.append([
                        {"text": f"{status_icon} #{order_id} - {service_name} - {format_number(amount)} ریال",
                         "callback_data": f"profile_order_detail_{order_id}"}
                    ])
                except Exception as e:
                    # ✅ استفاده از log_error با traceback
                    log_error(
                        'general',
                        f"Error processing order {order.get('id')}: {str(e)}",
                        traceback=traceback.format_exc(),
                        user_id=user_id
                    )
                    # رد کردن این سفارش و ادامه
                    continue

        # دکمه‌های صفحه‌بندی
        nav_row = []
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"profile_orders_page_{page-1}"})
        if page < total_pages - 1:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"profile_orders_page_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)

        keyboard.append([{"text": "🔙 بازگشت به پروفایل", "callback_data": f"profile_main_{user_id}"}])

        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        # ✅ استفاده از log_error با traceback کامل
        log_error(
            'general',
            f"profile_orders_keyboard: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id
        )
        # کیبورد ساده با دکمه بازگشت
        return {
            "inline_keyboard": [
                [{"text": "❌ خطا در نمایش سفارشات", "callback_data": "profile_none"}],
                [{"text": "🔙 بازگشت به پروفایل", "callback_data": f"profile_main_{user_id}"}]
            ]
        }


def profile_order_detail_keyboard(order_id: int, status: str) -> Dict:
    """کیبورد جزئیات سفارش"""
    keyboard = []

    # اگر سفارش در انتظار پرداخت است، دکمه لغو نمایش داده شود
    if status == 'pending':
        keyboard.append([
            {"text": "❌ لغو سفارش", "callback_data": f"profile_order_cancel_{order_id}"}
        ])

    keyboard.append([
        {"text": "🔙 بازگشت به لیست سفارشات", "callback_data": "profile_orders_back"}
    ])

    return {"inline_keyboard": keyboard}


def profile_stats_keyboard(user_id: int) -> Dict:
    """کیبورد آمار کاربر"""
    return {
        "inline_keyboard": [
            [{"text": "📋 مشاهده سفارشات", "callback_data": f"profile_orders_{user_id}"}],
            [{"text": "🔙 بازگشت به پروفایل", "callback_data": f"profile_main_{user_id}"}]
        ]
    }


# ============================================================
# توابع نمایش پروفایل
# ============================================================

async def show_profile(chat_id: int, user_id: int) -> bool:
    """
    نمایش پروفایل کاربری

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"👤 نمایش پروفایل کاربر {user_id}")
        
        # دریافت اطلاعات کاربر
        user = get_user(user_id)
        if not user:
            # اگر کاربر وجود نداشت، ثبت می‌کنیم
            upsert_user(user_id)
            user = get_user(user_id)

        if not user:
            await send_message(chat_id, "❌ خطا در دریافت اطلاعات کاربر.")
            return True

        # دریافت آمار سفارشات
        orders_count = get_user_orders_count(user_id)
        total_payment = get_user_total_payment(user_id)

        # دریافت آخرین سفارش
        orders = get_dynamic_orders()
        user_orders = [o for o in orders if o.get('user_id') == user_id]
        last_order = user_orders[0] if user_orders else None

        # ساخت پیام
        username = user.get('username')
        first_name = user.get('first_name')
        last_name = user.get('last_name')
        first_seen = format_datetime(user.get('first_seen'))
        last_active = format_datetime(user.get('last_active'))

        msg = f"👤 **پروفایل کاربری**\n\n"
        msg += f"🆔 شناسه: {user_id}\n"

        if username:
            msg += f"👤 نام کاربری: @{username}\n"
        if first_name:
            full_name = first_name
            if last_name:
                full_name += f" {last_name}"
            msg += f"📛 نام: {full_name}\n"

        msg += f"📅 عضویت: {first_seen}\n"
        msg += f"📅 آخرین فعالیت: {last_active}\n\n"

        msg += f"📊 **آمار سفارشات:**\n"
        msg += f"  • تعداد کل سفارشات: {format_number(orders_count)}\n"
        msg += f"  • مجموع پرداختی: {format_number(total_payment)} ریال\n"
        if orders_count > 0:
            avg_amount = total_payment // orders_count
            msg += f"  • میانگین هر سفارش: {format_number(avg_amount)} ریال\n"

        if last_order:
            msg += f"\n🕐 **آخرین سفارش:**\n"
            msg += f"  • شناسه: {last_order.get('id')}\n"
            msg += f"  • سرویس: {get_service_name(last_order.get('button_id'))}\n"
            msg += f"  • وضعیت: {get_order_status_persian(last_order.get('status', 'pending'))}\n"
            msg += f"  • تاریخ: {format_datetime(last_order.get('created_at'))}\n"

        await send_message(chat_id, msg, profile_main_keyboard(user_id))
        logger.info(f"✅ پروفایل کاربر {user_id} نمایش داده شد.")
        return True

    except Exception as e:
        logger.error(f"❌ Error in show_profile for user {user_id}: {e}", exc_info=True)
        log_error('general', f"show_profile: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش پروفایل. لطفاً دوباره تلاش کنید.")
        return True


async def show_profile_orders(chat_id: int, user_id: int, page: int = 0) -> bool:
    """
    نمایش لیست سفارشات کاربر با مدیریت خطا

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        page: شماره صفحه

    بازگشت: True در صورت موفقیت
    """
    try:
        logger.info(f"📋 نمایش سفارشات کاربر {user_id} - صفحه {page}")
        
        # دریافت سفارشات کاربر
        orders = get_dynamic_orders()
        logger.debug(f"تعداد کل سفارشات دریافت‌شده: {len(orders)}")
        
        user_orders = [o for o in orders if o.get('user_id') == user_id]
        logger.info(f"تعداد سفارشات کاربر {user_id}: {len(user_orders)}")
        
        # مرتب‌سازی بر اساس تاریخ (جدیدترین اول)
        user_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # ساخت کیبورد
        try:
            keyboard = profile_orders_keyboard(user_orders, user_id, page)
            logger.debug("کیبورد سفارشات ساخته شد.")
        except Exception as e:
            logger.error(f"خطا در ساخت کیبورد سفارشات: {e}", exc_info=True)
            log_error('general', f"profile_orders_keyboard: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
            await send_message(chat_id, "❌ خطا در ساخت کیبورد. لطفاً دوباره تلاش کنید.")
            return True
        
        total = len(user_orders)
        per_page = 5
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        msg = f"📋 **تاریخچه سفارشات**\n\n"
        msg += f"تعداد کل: {total} سفارش\n"
        if total > 0:
            msg += f"صفحه {page + 1} از {total_pages}\n\n"
            msg += "برای مشاهده جزئیات هر سفارش کلیک کنید:"
        else:
            msg += "📭 شما هیچ سفارشی ثبت نکرده‌اید."
        
        await send_message(chat_id, msg, keyboard)
        logger.info(f"✅ لیست سفارشات برای کاربر {user_id} نمایش داده شد.")
        return True
        
    except Exception as e:
        logger.error(f"❌❌❌ خطا در show_profile_orders برای کاربر {user_id}: {e}", exc_info=True)
        log_error('general', f"show_profile_orders: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش تاریخچه سفارشات. لطفاً دوباره تلاش کنید.")
        return True


async def show_profile_order_detail(chat_id: int, user_id: int, order_id: int) -> bool:
    """
    نمایش جزئیات کامل یک سفارش

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        order_id: شناسه سفارش

    بازگشت: True در صورت موفقیت
    """
    try:
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True

        # بررسی اینکه سفارش متعلق به کاربر است
        if order.get('user_id') != user_id:
            await send_message(chat_id, "⛔ شما دسترسی به این سفارش ندارید.")
            return True

        order_data = order.get('order_data', {})
        if isinstance(order_data, str):
            try:
                order_data = json.loads(order_data)
            except:
                order_data = {}

        status = order.get('status', 'pending')
        amount = order.get('payment_amount', 0) or 0
        tracking = order.get('tracking_code', 'ندارد')
        created_at = format_datetime(order.get('created_at'))
        service_name = get_service_name(order.get('button_id'))
        fullname = get_fullname_from_order(order)

        msg = f"📋 **جزئیات سفارش #{order_id}**\n\n"
        msg += f"🔘 سرویس: {service_name}\n"
        msg += f"👤 نام: {fullname}\n"
        msg += f"💰 مبلغ: {format_number(amount)} ریال\n"
        msg += f"📌 وضعیت: {get_order_status_persian(status)}\n"
        msg += f"🎫 کد رهگیری: {tracking}\n"
        msg += f"📅 تاریخ ثبت: {created_at}\n\n"

        msg += "📝 **پاسخ‌های شما:**\n"
        answers = order_data.get('answers', {})
        files = order_data.get('files', {})

        if answers:
            for q_text, ans in answers.items():
                if q_text in files:
                    msg += f"▪️ {q_text}: [فایل ارسال شده]\n"
                else:
                    msg += f"▪️ {q_text}: {ans}\n"
        else:
            msg += "▪️ پاسخی ثبت نشده است.\n"

        # ارسال فایل‌های ضمیمه
        if files:
            msg += "\n📎 **فایل‌های ارسالی:**\n"
            for question_text, file_info in files.items():
                file_id = file_info.get('file_id')
                file_type = file_info.get('type', 'document')
                caption = f"📎 {question_text}"
                try:
                    if file_type == 'photo':
                        await send_photo(chat_id, file_id, caption)
                    else:
                        await send_document(chat_id, file_id, caption)
                    msg += f"▪️ {question_text}: ارسال شد\n"
                except Exception as e:
                    logger.error(f"خطا در ارسال فایل برای سفارش {order_id}: {e}")

        keyboard = profile_order_detail_keyboard(order_id, status)
        await send_message(chat_id, msg, keyboard)
        return True

    except Exception as e:
        logger.error(f"Error in show_profile_order_detail: {e}", exc_info=True)
        log_error('general', str(e), traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
        return True


async def show_profile_stats(chat_id: int, user_id: int) -> bool:
    """
    نمایش آمار کاربر

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        user = get_user(user_id)
        orders_count = get_user_orders_count(user_id)
        total_payment = get_user_total_payment(user_id)

        # تفکیک وضعیت سفارشات
        orders = get_dynamic_orders()
        user_orders = [o for o in orders if o.get('user_id') == user_id]

        status_counts = {}
        for order in user_orders:
            status = order.get('status', 'pending')
            status_counts[status] = status_counts.get(status, 0) + 1

        msg = f"📊 **آمار من**\n\n"
        msg += f"👤 کاربر: {user_id}\n"
        if user and user.get('first_name'):
            msg += f"📛 نام: {user.get('first_name')}\n"
        msg += f"\n📦 **سفارشات:**\n"
        msg += f"  • تعداد کل: {format_number(orders_count)}\n"
        msg += f"  • مجموع مبلغ: {format_number(total_payment)} ریال\n"
        if orders_count > 0:
            avg_amount = total_payment // orders_count
            msg += f"  • میانگین هر سفارش: {format_number(avg_amount)} ریال\n"

        if status_counts:
            msg += f"\n📌 **تفکیک وضعیت:**\n"
            status_labels = {
                'pending': '⏳ در انتظار پرداخت',
                'paid': '✅ پرداخت شده',
                'completed': '✅ تکمیل شده',
                'cancelled': '❌ لغو شده',
            }
            for status, count in status_counts.items():
                label = status_labels.get(status, status)
                msg += f"  • {label}: {count}\n"

        await send_message(chat_id, msg, profile_stats_keyboard(user_id))
        return True

    except Exception as e:
        logger.error(f"Error in show_profile_stats: {e}", exc_info=True)
        log_error('general', str(e), traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش آمار.")
        return True


async def cancel_profile_order(chat_id: int, user_id: int, order_id: int) -> bool:
    """
    لغو سفارش در انتظار پرداخت

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        order_id: شناسه سفارش

    بازگشت: True در صورت موفقیت
    """
    try:
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True

        # بررسی اینکه سفارش متعلق به کاربر است
        if order.get('user_id') != user_id:
            await send_message(chat_id, "⛔ شما دسترسی به این سفارش ندارید.")
            return True

        # بررسی وضعیت سفارش
        if order.get('status') != 'pending':
            await send_message(chat_id, "❌ این سفارش قابل لغو نیست.")
            return True

        # لغو سفارش
        success = update_order_status(order_id, 'cancelled', user_id, note="لغو توسط کاربر")

        if success:
            # حذف state کاربر اگر در حالت فرم است
            from core import user_states
            if user_id in user_states:
                state = user_states.get(user_id, {})
                if state.get('state') in ['dynamic_awaiting_answer', 'dynamic_awaiting_option', 'dynamic_awaiting_payment']:
                    if state.get('button_id') == order.get('button_id'):
                        user_states[user_id] = {"state": "main"}

            await send_message(chat_id, "✅ سفارش با موفقیت لغو شد.")
        else:
            await send_message(chat_id, "❌ خطا در لغو سفارش.")

        # بازگشت به جزئیات سفارش
        await show_profile_order_detail(chat_id, user_id, order_id)
        return True

    except Exception as e:
        logger.error(f"Error in cancel_profile_order: {e}", exc_info=True)
        log_error('general', str(e), traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در لغو سفارش.")
        return True


# ============================================================
# توابع پردازش کالبک (برای پروفایل)
# ============================================================

async def handle_profile_callback(update: Dict) -> bool:
    """
    پردازش کالبک‌های مربوط به پروفایل کاربری

    پارامترها:
        update: دیکشنری آپدیت

    بازگشت: True اگر کالبک پردازش شد
    """
    try:
        cb = update.get("callback_query")
        if not cb:
            return False

        data = cb.get("data")
        user_id = cb.get("from", {}).get("id")
        chat_id = cb.get("message", {}).get("chat", {}).get("id")

        if not data or not user_id or not chat_id:
            return False

        logger.debug(f"پروفایل کالبک: {data} از کاربر {user_id}")

        # ========== نمایش پروفایل اصلی ==========
        if data == "profile_main":
            await show_profile(chat_id, user_id)
            return True

        # ========== نمایش سفارشات ==========
        if data.startswith("profile_orders_"):
            parts = data.split("_")
            if len(parts) >= 3:
                try:
                    target_user_id = int(parts[2])
                    if target_user_id == user_id:
                        await show_profile_orders(chat_id, user_id, 0)
                    else:
                        await send_message(chat_id, "⛔ دسترسی غیرمجاز.")
                except ValueError:
                    await send_message(chat_id, "❌ خطا.")
            return True

        # ========== صفحه‌بندی سفارشات ==========
        if data.startswith("profile_orders_page_"):
            try:
                page = int(data.split("_")[-1])
                await show_profile_orders(chat_id, user_id, page)
            except ValueError:
                await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
            return True

        # ========== بازگشت به لیست سفارشات ==========
        if data == "profile_orders_back":
            try:
                logger.info(f"🔄 بازگشت به لیست سفارشات برای کاربر {user_id}")
                await show_profile_orders(chat_id, user_id, 0)
                logger.info(f"✅ لیست سفارشات برای کاربر {user_id} نمایش داده شد.")
            except Exception as e:
                logger.error(f"❌❌❌ خطا در بازگشت به لیست سفارشات برای کاربر {user_id}: {e}", exc_info=True)
                log_error('callback', f"profile_orders_back: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
                await send_message(chat_id, "❌ خطا در بازگشت به لیست سفارشات. لطفاً دوباره تلاش کنید.")
            return True

        # ========== نمایش جزئیات سفارش ==========
        if data.startswith("profile_order_detail_"):
            try:
                order_id = int(data.split("_")[-1])
                await show_profile_order_detail(chat_id, user_id, order_id)
            except ValueError:
                await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
            return True

        # ========== لغو سفارش ==========
        if data.startswith("profile_order_cancel_"):
            try:
                order_id = int(data.split("_")[-1])
                await cancel_profile_order(chat_id, user_id, order_id)
            except ValueError:
                await send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
            return True

        # ========== نمایش آمار ==========
        if data.startswith("profile_stats_"):
            parts = data.split("_")
            if len(parts) >= 3:
                try:
                    target_user_id = int(parts[2])
                    if target_user_id == user_id:
                        await show_profile_stats(chat_id, user_id)
                    else:
                        await send_message(chat_id, "⛔ دسترسی غیرمجاز.")
                except ValueError:
                    await send_message(chat_id, "❌ خطا.")
            return True

        return False

    except Exception as e:
        logger.error(f"Error in handle_profile_callback: {e}", exc_info=True)
        log_error('callback', str(e), traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        return False


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'show_profile',
    'show_profile_orders',
    'show_profile_order_detail',
    'show_profile_stats',
    'cancel_profile_order',
    'handle_profile_callback',
    'profile_main_keyboard',
    'profile_orders_keyboard',
    'profile_order_detail_keyboard',
    'profile_stats_keyboard',
]