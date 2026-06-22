# admin_panel/user_actions.py
# مدیریت پیشرفته کاربران در پنل مدیریت
# شامل: مسدود کردن/رفع مسدودیت، مشاهده فعالیت، ارسال پیام انبوه
# اضافه شدن تابع صفحه‌بندی لیست کاربران مسدود شده
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
import json
from datetime import datetime, timedelta
from logger_config import logger
from core import send_message, user_states, OWNER_ID
from database import (
    get_user,
    get_all_users,
    get_users_with_stats,
    get_total_users,
    get_active_users,
    get_user_orders_count,
    get_user_total_payment,
    get_dynamic_orders,
    get_error_logs,
    get_button_stats,
    upsert_user,
    get_db_connection,
    search_users,
    block_user as db_block_user,
    unblock_user as db_unblock_user,
    is_user_blocked,
)
from keyboards import admin_main_keyboard
from utils.error_handler import (
    log_callback_error,
    log_database_error,
    log_general_error,
    log_security_error,
    log_api_error
)


# ============================================================
# توابع کمکی
# ============================================================

def _is_owner(user_id: int) -> bool:
    """بررسی آیا کاربر OWNER_ID است"""
    return user_id == OWNER_ID


def _format_number(num: int) -> str:
    """فرمت‌بندی اعداد با کاما"""
    if num is None:
        return "۰"
    try:
        return f"{int(num):,}"
    except Exception:
        return str(num)


def _format_datetime(dt) -> str:
    """فرمت‌بندی تاریخ و زمان"""
    if not dt:
        return "نامشخص"
    try:
        if isinstance(dt, str):
            if len(dt) > 16:
                return dt[:16]
            return dt
        return str(dt)
    except Exception:
        return str(dt)


def _get_status_persian(status: str) -> str:
    """تبدیل وضعیت به فارسی"""
    status_map = {
        'pending': '⏳ در انتظار پرداخت',
        'paid': '✅ پرداخت شده',
        'completed': '✅ تکمیل شده',
        'cancelled': '❌ لغو شده',
    }
    return status_map.get(status, status)


def _get_service_name(button_id: int) -> str:
    """دریافت نام سرویس"""
    from database import get_button_by_id
    if not button_id:
        return "نامشخص"
    try:
        btn = get_button_by_id(button_id)
        if not btn:
            return f"سرویس {button_id}"
        if btn.get('parent_button_id'):
            parent = get_button_by_id(btn['parent_button_id'])
            if parent:
                return f"{parent['name']} > {btn['name']}"
        return btn['name']
    except Exception as e:
        log_database_error(
            f"Error in _get_service_name for {button_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return f"سرویس {button_id}"


def _get_fullname_from_order(order: dict) -> str:
    """استخراج نام کامل از سفارش"""
    try:
        order_data = order.get('order_data', {})
        if isinstance(order_data, str):
            try:
                order_data = json.loads(order_data)
            except:
                order_data = {}
        
        fullname = order_data.get('fullname')
        if fullname:
            return fullname
        
        answers = order_data.get('answers', {})
        if answers:
            first_answer = next(iter(answers.values()), 'کاربر ناشناس')
            return first_answer
        
        return 'کاربر ناشناس'
    except Exception as e:
        log_general_error(
            f"Error in _get_fullname_from_order: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 'کاربر ناشناس'


# ============================================================
# کیبوردها
# ============================================================

def user_actions_main_keyboard() -> dict:
    """کیبورد اصلی مدیریت پیشرفته کاربران"""
    return {
        "inline_keyboard": [
            [{"text": "🚫 مدیریت کاربران مسدود شده", "callback_data": "admin_user_block_list"}],
            [{"text": "👤 مشاهده فعالیت کاربر", "callback_data": "admin_user_activity_search"}],
            [{"text": "📨 ارسال پیام انبوه", "callback_data": "admin_user_broadcast"}],
            [{"text": "📊 آمار کاربران", "callback_data": "admin_user_actions_stats"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


def user_block_list_keyboard(users: list, page: int = 0, per_page: int = 5) -> dict:
    """کیبورد نمایش لیست کاربران مسدود شده"""
    try:
        total = len(users)
        start = page * per_page
        end = min(start + per_page, total)
        page_users = users[start:end]
        
        keyboard = []
        
        if not page_users:
            keyboard.append([{"text": "✅ هیچ کاربر مسدود شده‌ای وجود ندارد", "callback_data": "admin_none"}])
        else:
            for user in page_users:
                user_id = user.get('user_id')
                username = user.get('username') or user.get('first_name') or 'کاربر ناشناس'
                blocked_at = user.get('blocked_at', 'نامشخص')
                
                keyboard.append([
                    {"text": f"🔴 {user_id} - {username[:15]}", 
                     "callback_data": f"admin_user_block_detail_{user_id}"}
                ])
        
        # دکمه‌های صفحه‌بندی
        nav_row = []
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_user_block_list_page_{page-1}"})
        if page < total_pages - 1:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_user_block_list_page_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)
        
        keyboard.append([{"text": "🔙 برگشت به مدیریت کاربران", "callback_data": "admin_user_actions"}])
        
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in user_block_list_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری کاربران", "callback_data": "admin_user_actions"}]]}


def user_block_detail_keyboard(user_id: int, is_blocked: bool) -> dict:
    """کیبورد جزئیات کاربر مسدود شده"""
    keyboard = []
    
    if is_blocked:
        keyboard.append([{"text": "✅ رفع مسدودیت", "callback_data": f"admin_user_unblock_{user_id}"}])
    else:
        keyboard.append([{"text": "🚫 مسدود کردن", "callback_data": f"admin_user_block_{user_id}"}])
    
    keyboard.append([
        {"text": "👤 مشاهده پروفایل", "callback_data": f"admin_user_profile_{user_id}"},
        {"text": "📋 سفارشات", "callback_data": f"admin_user_orders_{user_id}"}
    ])
    keyboard.append([{"text": "🔙 بازگشت به لیست", "callback_data": "admin_user_block_list"}])
    
    return {"inline_keyboard": keyboard}


def user_activity_keyboard(user_id: int) -> dict:
    """کیبورد نمایش فعالیت کاربر"""
    return {
        "inline_keyboard": [
            [{"text": "📋 سفارشات کاربر", "callback_data": f"admin_user_orders_{user_id}"}],
            [{"text": "📊 آمار کلیک‌ها", "callback_data": f"admin_user_stats_{user_id}"}],
            [{"text": "🚨 خطاهای کاربر", "callback_data": f"admin_user_errors_{user_id}"}],
            [{"text": "🔙 بازگشت به مدیریت کاربران", "callback_data": "admin_user_actions"}]
        ]
    }


def broadcast_keyboard() -> dict:
    """کیبورد ارسال پیام انبوه"""
    return {
        "inline_keyboard": [
            [{"text": "👥 همه کاربران", "callback_data": "admin_broadcast_all"}],
            [{"text": "🟢 کاربران فعال (امروز)", "callback_data": "admin_broadcast_active"}],
            [{"text": "📅 کاربران فعال (هفته اخیر)", "callback_data": "admin_broadcast_active_week"}],
            [{"text": "💰 کاربرانی که سفارش دارند", "callback_data": "admin_broadcast_with_orders"}],
            [{"text": "🚫 کاربران مسدود شده (ارسال نمی‌شود)", "callback_data": "admin_broadcast_blocked"}],
            [{"text": "🔙 انصراف", "callback_data": "admin_user_actions"}]
        ]
    }


def broadcast_confirm_keyboard(target_type: str, count: int) -> dict:
    """کیبورد تایید ارسال پیام انبوه"""
    return {
        "inline_keyboard": [
            [{"text": f"⚠️ ارسال به {count} کاربر", "callback_data": "admin_none"}],
            [{"text": "✅ تایید و ارسال", "callback_data": f"admin_broadcast_send_{target_type}"}],
            [{"text": "❌ انصراف", "callback_data": "admin_user_actions"}]
        ]
    }


# ============================================================
# توابع اصلی مدیریت کاربران مسدود شده
# ============================================================

async def handle_user_actions(chat_id: int, user_id: int) -> bool:
    """نمایش منوی اصلی مدیریت پیشرفته کاربران"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        # آمار سریع
        total_users = get_total_users()
        blocked_users = _get_blocked_users_count()
        active_today = get_active_users(1)
        
        msg = (
            f"👥 **مدیریت پیشرفته کاربران**\n\n"
            f"📊 **آمار سریع:**\n"
            f"  • کل کاربران: {_format_number(total_users)}\n"
            f"  • کاربران مسدود شده: {_format_number(blocked_users)}\n"
            f"  • کاربران فعال امروز: {_format_number(active_today)}\n\n"
            f"از گزینه‌های زیر برای مدیریت کاربران استفاده کنید:"
        )
        
        await send_message(chat_id, msg, user_actions_main_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_actions: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش مدیریت کاربران.")
        return True


def _get_blocked_users() -> list:
    """دریافت لیست کاربران مسدود شده"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE is_blocked = 1 ORDER BY blocked_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in _get_blocked_users: {str(e)}",
            traceback=traceback.format_exc()
        )
        return []


def _get_blocked_users_count() -> int:
    """تعداد کاربران مسدود شده"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_blocked = 1")
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(
            f"Error in _get_blocked_users_count: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 0


async def handle_user_block_list(chat_id: int, user_id: int, page: int = 0) -> bool:
    """نمایش لیست کاربران مسدود شده"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        blocked_users = _get_blocked_users()
        
        keyboard = user_block_list_keyboard(blocked_users, page)
        
        msg = (
            f"🚫 **لیست کاربران مسدود شده**\n\n"
            f"تعداد: {len(blocked_users)} کاربر\n"
            f"برای مشاهده جزئیات هر کاربر کلیک کنید:"
        )
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_block_list: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست کاربران مسدود شده.")
        return True


async def handle_user_block_list_page(chat_id: int, user_id: int, data: str) -> bool:
    """صفحه‌بندی لیست کاربران مسدود شده"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        page = int(data.split("_")[-1]) if data.split("_")[-1].isdigit() else 0
        return await handle_user_block_list(chat_id, user_id, page)
    except ValueError:
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_block_list_page: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی لیست کاربران مسدود شده.")
        return True


async def handle_user_block_detail(chat_id: int, user_id: int, target_user_id: int) -> bool:
    """نمایش جزئیات یک کاربر مسدود شده"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user = get_user(target_user_id)
        if not user:
            await send_message(chat_id, "❌ کاربر یافت نشد.")
            return True
        
        is_blocked = user.get('is_blocked', 0) == 1
        blocked_at = user.get('blocked_at', 'نامشخص')
        block_reason = user.get('block_reason', 'بدون دلیل')
        
        username = user.get('username')
        first_name = user.get('first_name')
        last_name = user.get('last_name')
        
        msg = (
            f"👤 **جزئیات کاربر**\n\n"
            f"🆔 شناسه: {target_user_id}\n"
        )
        if username:
            msg += f"👤 نام کاربری: @{username}\n"
        if first_name:
            full_name = first_name
            if last_name:
                full_name += f" {last_name}"
            msg += f"📛 نام: {full_name}\n"
        
        msg += (
            f"📌 وضعیت: {'🔴 مسدود شده' if is_blocked else '🟢 فعال'}\n"
            f"📅 تاریخ مسدودیت: {_format_datetime(blocked_at)}\n"
            f"📝 دلیل: {block_reason}\n"
        )
        
        keyboard = user_block_detail_keyboard(target_user_id, is_blocked)
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_block_detail for user {target_user_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات کاربر.")
        return True


async def handle_user_block(chat_id: int, user_id: int, target_user_id: int, reason: str = None) -> bool:
    """مسدود کردن یک کاربر"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if target_user_id == OWNER_ID:
            await send_message(chat_id, "⚠️ نمی‌توانید OWNER را مسدود کنید.")
            return True
        
        success = db_block_user(target_user_id, reason or 'مسدود شده توسط ادمین')
        
        if success:
            logger.info(f"User {target_user_id} blocked by {user_id}")
            await send_message(chat_id, f"✅ کاربر {target_user_id} با موفقیت مسدود شد.")
        else:
            await send_message(chat_id, f"❌ خطا در مسدود کردن کاربر {target_user_id}.")
        
        # بازگشت به جزئیات
        await handle_user_block_detail(chat_id, user_id, target_user_id)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_block for user {target_user_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در مسدود کردن کاربر.")
        return True


async def handle_user_unblock(chat_id: int, user_id: int, target_user_id: int) -> bool:
    """رفع مسدودیت کاربر"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        success = db_unblock_user(target_user_id)
        
        if success:
            logger.info(f"User {target_user_id} unblocked by {user_id}")
            await send_message(chat_id, f"✅ کاربر {target_user_id} با موفقیت رفع مسدودیت شد.")
        else:
            await send_message(chat_id, f"❌ خطا در رفع مسدودیت کاربر {target_user_id}.")
        
        # بازگشت به جزئیات
        await handle_user_block_detail(chat_id, user_id, target_user_id)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_unblock for user {target_user_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در رفع مسدودیت کاربر.")
        return True


# ============================================================
# مشاهده فعالیت کاربر
# ============================================================

async def handle_user_activity_search(chat_id: int, user_id: int) -> bool:
    """شروع جستجوی کاربر برای مشاهده فعالیت"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_states[user_id] = {"state": "admin_activity_search"}
        await send_message(
            chat_id,
            "🔍 **جستجوی کاربر برای مشاهده فعالیت**\n\n"
            "لطفاً شناسه کاربری (user_id) یا نام کاربری را وارد کنید:\n"
            "(مثال: 123456789 یا @username)\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_activity_search: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع جستجو.")
        return True


async def show_user_activity(chat_id: int, user_id: int, data) -> bool:
    """نمایش فعالیت کامل یک کاربر"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        # استخراج target_user_id از data
        if isinstance(data, str) and data.startswith("admin_user_activity_"):
            target_user_id = int(data.split("_")[-1])
        elif isinstance(data, int):
            target_user_id = data
        else:
            await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
            return True
        
        user = get_user(target_user_id)
        if not user:
            await send_message(chat_id, "❌ کاربر یافت نشد.")
            return True
        
        # آمار سفارشات
        orders_count = get_user_orders_count(target_user_id)
        total_payment = get_user_total_payment(target_user_id)
        
        # دریافت آخرین سفارشات
        all_orders = get_dynamic_orders()
        user_orders = [o for o in all_orders if o.get('user_id') == target_user_id]
        user_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # دریافت خطاهای کاربر
        error_logs = get_error_logs(limit=5)
        error_logs = [e for e in error_logs if e.get('user_id') == target_user_id]
        
        # دریافت آمار کلیک‌ها
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT action_type, COUNT(*) as count 
                FROM button_stats 
                WHERE user_id = ? 
                GROUP BY action_type
            """, (target_user_id,))
            click_stats = [dict(row) for row in cursor.fetchall()]
        
        # ساخت پیام
        username = user.get('username')
        first_name = user.get('first_name')
        last_name = user.get('last_name')
        first_seen = user.get('first_seen')
        last_active = user.get('last_active')
        is_blocked = user.get('is_blocked', 0) == 1
        
        msg = (
            f"📊 **فعالیت کاربر**\n\n"
            f"🆔 شناسه: {target_user_id}\n"
        )
        if username:
            msg += f"👤 نام کاربری: @{username}\n"
        if first_name:
            full_name = first_name
            if last_name:
                full_name += f" {last_name}"
            msg += f"📛 نام: {full_name}\n"
        
        msg += (
            f"📌 وضعیت: {'🔴 مسدود شده' if is_blocked else '🟢 فعال'}\n"
            f"📅 عضویت: {_format_datetime(first_seen)}\n"
            f"📅 آخرین فعالیت: {_format_datetime(last_active)}\n\n"
            f"📦 **سفارشات:**\n"
            f"  • تعداد: {_format_number(orders_count)}\n"
            f"  • مجموع مبلغ: {_format_number(total_payment)} ریال\n"
        )
        
        # سفارشات اخیر
        if user_orders:
            msg += f"\n🕐 **۳ سفارش اخیر:**\n"
            for order in user_orders[:3]:
                service = _get_service_name(order.get('button_id'))
                status = _get_status_persian(order.get('status', 'pending'))
                amount = order.get('payment_amount', 0) or 0
                msg += f"  • #{order.get('id')} - {service[:15]} - {_format_number(amount)} ریال - {status}\n"
        
        # آمار کلیک‌ها
        if click_stats:
            msg += f"\n🖱️ **آمار کلیک‌ها:**\n"
            for stat in click_stats:
                action = stat.get('action_type', 'unknown')
                count = stat.get('count', 0)
                action_labels = {
                    'click': 'کلیک روی دکمه',
                    'form_start': 'شروع فرم',
                    'order_paid': 'سفارش پرداخت شده'
                }
                label = action_labels.get(action, action)
                msg += f"  • {label}: {count}\n"
        
        # خطاهای اخیر
        if error_logs:
            msg += f"\n🚨 **خطاهای اخیر ({len(error_logs)} مورد):**\n"
            for err in error_logs[:3]:
                err_type = err.get('error_type', 'general')
                err_msg = err.get('error_message', '')[:30]
                err_time = _format_datetime(err.get('created_at'))
                msg += f"  • [{err_type}] {err_msg}... ({err_time})\n"
        else:
            msg += f"\n✅ بدون خطا\n"
        
        keyboard = user_activity_keyboard(target_user_id)
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in show_user_activity: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش فعالیت کاربر.")
        return True


async def handle_user_errors(chat_id: int, user_id: int, data) -> bool:
    """نمایش خطاهای یک کاربر"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        target_user_id = int(data.split("_")[-1])
        error_logs = get_error_logs(limit=20)
        error_logs = [e for e in error_logs if e.get('user_id') == target_user_id]
        
        if not error_logs:
            await send_message(chat_id, f"✅ کاربر {target_user_id} هیچ خطایی ندارد.")
            return True
        
        msg = f"🚨 **خطاهای کاربر {target_user_id}**\n\n"
        for err in error_logs[:10]:
            err_id = err.get('id')
            err_type = err.get('error_type', 'general')
            err_msg = err.get('error_message', '')
            err_time = _format_datetime(err.get('created_at'))
            is_resolved = err.get('is_resolved', 0)
            status_icon = "✅" if is_resolved else "🔴"
            
            msg += f"{status_icon} #{err_id} - {err_type}: {err_msg[:40]}...\n"
            msg += f"   🕐 {err_time}\n\n"
        
        if len(error_logs) > 10:
            msg += f"... و {len(error_logs) - 10} خطای دیگر"
        
        await send_message(
            chat_id,
            msg,
            {"inline_keyboard": [[{"text": "🔙 بازگشت به فعالیت", "callback_data": f"admin_user_activity_{target_user_id}"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_errors: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش خطاهای کاربر.")
        return True


# ============================================================
# ارسال پیام انبوه
# ============================================================

async def handle_broadcast(chat_id: int, user_id: int) -> bool:
    """نمایش صفحه انتخاب مخاطبان برای پیام انبوه"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        total_users = get_total_users()
        active_today = get_active_users(1)
        active_week = get_active_users(7)
        
        # تعداد کاربرانی که حداقل یک سفارش دارند
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM dynamic_orders")
            row = cursor.fetchone()
            users_with_orders = row['count'] if row else 0
        
        msg = (
            f"📨 **ارسال پیام انبوه**\n\n"
            f"📊 **آمار کاربران:**\n"
            f"  • کل کاربران: {_format_number(total_users)}\n"
            f"  • فعال امروز: {_format_number(active_today)}\n"
            f"  • فعال هفته اخیر: {_format_number(active_week)}\n"
            f"  • دارای سفارش: {_format_number(users_with_orders)}\n\n"
            f"گروه مخاطبان را انتخاب کنید:\n"
            f"(کاربران مسدود شده پیام دریافت نمی‌کنند)"
        )
        
        await send_message(chat_id, msg, broadcast_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_broadcast: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش ارسال پیام انبوه.")
        return True


def _get_broadcast_users(target_type: str) -> list:
    """دریافت لیست کاربران برای ارسال پیام انبوه"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if target_type == "all":
                cursor.execute("SELECT user_id FROM users WHERE is_blocked = 0")
            
            elif target_type == "active":
                cursor.execute("""
                    SELECT user_id FROM users 
                    WHERE is_blocked = 0 
                    AND last_active >= datetime('now', '-1 day')
                """)
            
            elif target_type == "active_week":
                cursor.execute("""
                    SELECT user_id FROM users 
                    WHERE is_blocked = 0 
                    AND last_active >= datetime('now', '-7 days')
                """)
            
            elif target_type == "with_orders":
                cursor.execute("""
                    SELECT DISTINCT u.user_id 
                    FROM users u
                    INNER JOIN dynamic_orders o ON u.user_id = o.user_id
                    WHERE u.is_blocked = 0
                """)
            
            elif target_type == "blocked":
                cursor.execute("SELECT user_id FROM users WHERE is_blocked = 1")
            
            else:
                return []
            
            rows = cursor.fetchall()
            return [row['user_id'] for row in rows]
            
    except Exception as e:
        log_database_error(
            f"Error in _get_broadcast_users for {target_type}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return []


async def handle_broadcast_target(chat_id: int, user_id: int, target_type: str) -> bool:
    """نمایش تاییدیه ارسال پیام به گروه انتخاب‌شده"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        target_users = _get_broadcast_users(target_type)
        
        if not target_users:
            await send_message(
                chat_id,
                "❌ هیچ کاربری برای این گروه یافت نشد.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "admin_user_actions"}]]}
            )
            return True
        
        # ذخیره کاربران در user_states
        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["broadcast_users"] = target_users
        user_states[user_id]["broadcast_type"] = target_type
        
        # نمایش تاییدیه
        target_labels = {
            'all': 'همه کاربران',
            'active': 'کاربران فعال امروز',
            'active_week': 'کاربران فعال هفته اخیر',
            'with_orders': 'کاربران دارای سفارش',
            'blocked': 'کاربران مسدود شده',
        }
        label = target_labels.get(target_type, target_type)
        
        keyboard = broadcast_confirm_keyboard(target_type, len(target_users))
        
        await send_message(
            chat_id,
            f"📨 **تایید ارسال پیام انبوه**\n\n"
            f"🎯 گروه: {label}\n"
            f"👥 تعداد کاربران: {len(target_users)}\n\n"
            f"لطفاً پیام مورد نظر را وارد کنید:\n"
            f"(بعد از وارد کردن پیام، روی «تایید و ارسال» کلیک کنید)\n\n"
            f"📌 **نکته:** کاربران مسدود شده پیام دریافت نمی‌کنند.",
            keyboard
        )
        user_states[user_id]["state"] = "admin_broadcast_message"
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_broadcast_target: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب گروه مخاطبان.")
        return True


async def handle_broadcast_send(chat_id: int, user_id: int, target_type: str, message: str = None) -> bool:
    """ارسال پیام انبوه"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        # دریافت پیام از user_states اگر ارسال نشده باشد
        if message is None:
            state_info = user_states.get(user_id, {})
            message = state_info.get("broadcast_message")
        
        if not message:
            await send_message(chat_id, "❌ پیام وارد نشده است.")
            return True
        
        # دریافت لیست کاربران
        target_users = user_states.get(user_id, {}).get("broadcast_users", [])
        if not target_users:
            await send_message(chat_id, "❌ لیست کاربران خالی است.")
            return True
        
        # ارسال پیام
        await send_message(chat_id, f"⏳ در حال ارسال پیام به {len(target_users)} کاربر...")
        
        success_count = 0
        fail_count = 0
        failed_users = []
        
        for i, target in enumerate(target_users):
            try:
                await send_message(target, message)
                success_count += 1
            except Exception as e:
                fail_count += 1
                failed_users.append(target)
                log_api_error(
                    f"Error sending broadcast to user {target}: {str(e)}",
                    traceback=traceback.format_exc(),
                    user_id=target,
                    chat_id=chat_id
                )
            
            # ارسال گزارش هر ۱۰۰ کاربر
            if (i + 1) % 100 == 0:
                await send_message(
                    chat_id,
                    f"⏳ پیشرفت: {i + 1}/{len(target_users)} ارسال شد..."
                )
        
        # گزارش نهایی
        report = (
            f"📨 **گزارش ارسال پیام انبوه**\n\n"
            f"👥 کل: {len(target_users)} کاربر\n"
            f"✅ موفق: {success_count}\n"
            f"❌ ناموفق: {fail_count}\n"
        )
        
        if failed_users:
            report += f"\n⚠️ کاربران ناموفق:\n"
            for uid in failed_users[:10]:
                report += f"  • {uid}\n"
            if len(failed_users) > 10:
                report += f"  ... و {len(failed_users) - 10} کاربر دیگر\n"
        
        await send_message(chat_id, report)
        
        # پاک کردن state
        if user_id in user_states:
            user_states[user_id].pop("broadcast_users", None)
            user_states[user_id].pop("broadcast_type", None)
            user_states[user_id].pop("broadcast_message", None)
            user_states[user_id]["state"] = "main"
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_broadcast_send: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ارسال پیام انبوه.")
        return True


# ============================================================
# آمار کاربران
# ============================================================

async def handle_user_actions_stats(chat_id: int, user_id: int) -> bool:
    """نمایش آمار کامل کاربران"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        total_users = get_total_users()
        active_today = get_active_users(1)
        active_week = get_active_users(7)
        active_month = get_active_users(30)
        blocked_users = _get_blocked_users_count()
        
        # کاربران دارای سفارش
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM dynamic_orders")
            row = cursor.fetchone()
            users_with_orders = row['count'] if row else 0
        
        # کاربران با پرداخت
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as count 
                FROM dynamic_orders 
                WHERE status IN ('paid', 'completed')
            """)
            row = cursor.fetchone()
            users_with_payment = row['count'] if row else 0
        
        # میانگین مبلغ هر کاربر
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT user_id) as user_count,
                    SUM(payment_amount) as total
                FROM dynamic_orders 
                WHERE status IN ('paid', 'completed')
            """)
            row = cursor.fetchone()
            total_amount = row['total'] if row else 0
            user_count = row['user_count'] if row else 0
            avg_per_user = total_amount / user_count if user_count > 0 else 0
        
        msg = (
            f"📊 **آمار کاربران**\n\n"
            f"👥 **تعداد کل کاربران:**\n"
            f"  • ثبت‌شده: {_format_number(total_users)}\n"
            f"  • مسدود شده: {_format_number(blocked_users)}\n\n"
            f"📈 **کاربران فعال:**\n"
            f"  • امروز: {_format_number(active_today)}\n"
            f"  • هفته اخیر: {_format_number(active_week)}\n"
            f"  • ماه اخیر: {_format_number(active_month)}\n\n"
            f"💰 **آمار مالی:**\n"
            f"  • کاربران دارای سفارش: {_format_number(users_with_orders)}\n"
            f"  • کاربران با پرداخت: {_format_number(users_with_payment)}\n"
            f"  • میانگین مبلغ هر کاربر: {_format_number(avg_per_user)} ریال\n\n"
            f"📊 **نرخ تبدیل (کلیک به سفارش):**\n"
        )
        
        # نرخ تبدیل کلی
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM button_stats WHERE action_type = 'click'")
            clicks_row = cursor.fetchone()
            clicks = clicks_row['count'] if clicks_row else 0
            
            cursor.execute("SELECT COUNT(*) as count FROM dynamic_orders")
            orders_row = cursor.fetchone()
            orders = orders_row['count'] if orders_row else 0
            
            conversion = (orders / clicks * 100) if clicks > 0 else 0
            msg += f"  • کلیک → سفارش: {conversion:.2f}%\n"
        
        await send_message(
            chat_id,
            msg,
            {
                "inline_keyboard": [
                    [{"text": "👥 مشاهده لیست کاربران", "callback_data": "admin_users_list"}],
                    [{"text": "🚫 مدیریت کاربران مسدود شده", "callback_data": "admin_user_block_list"}],
                    [{"text": "🔙 بازگشت به مدیریت کاربران", "callback_data": "admin_user_actions"}]
                ]
            }
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_actions_stats: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش آمار کاربران.")
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'handle_user_actions',
    'handle_user_block_list',
    'handle_user_block_list_page',
    'handle_user_block_detail',
    'handle_user_block',
    'handle_user_unblock',
    'handle_user_activity_search',
    'show_user_activity',
    'handle_user_errors',
    'handle_broadcast',
    'handle_broadcast_target',
    'handle_broadcast_send',
    'handle_user_actions_stats',
]