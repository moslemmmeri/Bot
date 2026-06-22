# admin_panel/user_management.py
# مدیریت کاربران و آمار فعالیت - نمایش لیست کاربران، جزئیات، جستجو و آمار کلی
# اصلاح شده با استفاده از ui_helpers و استایل simple برای جدول

import traceback
from typing import Dict, List, Any, Optional

from logger_config import logger
from core import send_message, user_states, OWNER_ID
from database import (
    get_users_with_stats,
    get_total_users,
    get_active_users,
    get_user,
    get_user_orders_count,
    get_user_total_payment,
    search_users,
    get_dynamic_orders,
    get_user_role,
    is_admin,
)
from keyboards import admin_main_keyboard
from utils import format_number, format_datetime
from services.permission_service import get_permission_service
from services.state_service import get_state_service
from utils.error_handler import (
    log_callback_error,
    log_database_error,
    log_general_error,
    log_security_error
)

# ========== ایمپورت از ui_helpers ==========
from ui_helpers import (
    Emojis,
    TextFormatter,
    TextTable,
    InfoCard,
    StatusMessage,
    build_menu_keyboard,
)


# ==================== کیبوردها ====================

def user_management_main_keyboard() -> Dict:
    items = [
        ("👥 لیست کاربران", "admin_users_list"),
        ("📊 آمار کاربران", "admin_users_stats"),
        ("🔍 جستجوی کاربر", "admin_users_search"),
        ("🚫 مدیریت کاربران مسدود شده", "admin_user_block_list"),
        ("🔙 برگشت به منو", "admin_back"),
    ]
    return {"inline_keyboard": build_menu_keyboard(items, cols=1)}


def user_list_keyboard(users: List[Dict], page: int = 0, per_page: int = 10, total: int = 0) -> Dict:
    try:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        keyboard_items = []
        for user in users:
            user_id = user.get('user_id')
            if user_id:
                status_icon = "🟢" if user.get('last_active', '') and today in user.get('last_active', '') else "⚪"
                name = user.get('username') or user.get('first_name') or f"کاربر {user_id}"
                orders = user.get('orders_count', 0)
                admin_icon = "🛡️" if is_admin(user_id) else ""
                label = f"{status_icon} {admin_icon} {user_id} - {name[:20]} ({orders} سفارش)"
                keyboard_items.append((label, f"admin_user_detail_{user_id}"))
        
        nav_items = []
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        if page > 0:
            nav_items.append(("⬅️ قبلی", f"admin_users_list_page_{page-1}"))
        if page < total_pages - 1:
            nav_items.append(("➡️ بعدی", f"admin_users_list_page_{page+1}"))
        
        action_items = [
            ("📊 آمار کاربران", "admin_users_stats"),
            ("🔍 جستجو", "admin_users_search"),
            ("🔙 برگشت به منو", "admin_users"),
        ]
        
        all_items = keyboard_items + nav_items + action_items
        keyboard = build_menu_keyboard(all_items, cols=1)
        
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in user_list_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری کاربران", "callback_data": "admin_users"}]]}


def user_detail_keyboard(user_id: int) -> Dict:
    items = [
        ("📋 مشاهده سفارشات کاربر", f"admin_orders_user_{user_id}"),
        ("🚫 مسدود کردن کاربر", f"admin_user_block_{user_id}"),
        ("👤 مشاهده فعالیت کاربر", f"admin_user_activity_{user_id}"),
        ("🔙 برگشت به لیست کاربران", "admin_users_list"),
        ("🔙 برگشت به منو", "admin_users"),
    ]
    return {"inline_keyboard": build_menu_keyboard(items, cols=1)}


def user_stats_keyboard() -> Dict:
    items = [
        ("👥 مشاهده لیست کاربران", "admin_users_list"),
        ("🔙 برگشت به منو", "admin_users"),
    ]
    return {"inline_keyboard": build_menu_keyboard(items, cols=1)}


def user_search_keyboard() -> Dict:
    return {
        "inline_keyboard": [
            [{"text": "🔍 لطفاً کلمه کلیدی (شناسه/نام) را وارد کنید:"}],
            [{"text": "🔙 انصراف", "callback_data": "admin_users"}]
        ]
    }


# ==================== توابع اصلی ====================

async def handle_user_management(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        total_users = get_total_users()
        active_today = get_active_users(1)
        from database import get_blocked_count
        blocked_count = get_blocked_count()
        
        stats = {
            "کل کاربران": TextFormatter.format_number(total_users),
            "کاربران فعال امروز": TextFormatter.format_number(active_today),
            "کاربران مسدود شده": TextFormatter.format_number(blocked_count),
        }
        msg = StatusMessage.info(
            "مدیریت کاربران",
            details=stats
        )
        msg += "\n\nاز گزینه‌های زیر برای مدیریت کاربران استفاده کنید:"
        
        await send_message(chat_id, msg, user_management_main_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_management: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش صفحه مدیریت کاربران.")
        return True


async def handle_user_list(chat_id: int, user_id: int, page: int = 0) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        per_page = 10
        offset = page * per_page
        
        users = get_users_with_stats(limit=per_page, offset=offset)
        total = get_total_users()
        
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        for user in users:
            last_active = user.get('last_active', '')
            user['is_active_recent'] = bool(last_active and today in last_active)
        
        keyboard = user_list_keyboard(users, page, per_page, total)
        
        total_pages = ((total + per_page - 1) // per_page) if total > 0 else 1
        msg = (
            f"{Emojis.USER_GROUP} **لیست کاربران**\n\n"
            f"تعداد کل: {TextFormatter.format_number(total)} کاربر\n"
            f"صفحه‌ی {page + 1} از {total_pages}\n\n"
            f"🟢 فعال امروز | ⚪ غیرفعال امروز | 🛡️ ادمین"
        )
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_list: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست کاربران.")
        return True


async def handle_user_list_page(chat_id: int, user_id: int, data: str) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        page = int(data.split("_")[-1]) if data.split("_")[-1].isdigit() else 0
        await handle_user_list(chat_id, user_id, page)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_list_page: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی.")
        return True


async def handle_user_detail(chat_id: int, user_id: int, data: str) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        target_user_id = int(data.split("_")[-1])
        
        user_info = get_user(target_user_id)
        if not user_info:
            await send_message(chat_id, f"❌ کاربر {target_user_id} یافت نشد.")
            return True
        
        orders_count = get_user_orders_count(target_user_id)
        total_payment = get_user_total_payment(target_user_id)
        
        orders = get_dynamic_orders()
        last_order = None
        for order in orders:
            if order.get('user_id') == target_user_id:
                last_order = order
                break
        
        items = {
            "🆔 شناسه": TextFormatter.bold(str(target_user_id)),
        }
        
        username = user_info.get('username')
        first_name = user_info.get('first_name')
        last_name = user_info.get('last_name')
        
        if username:
            items["👤 نام کاربری"] = f"@{username}"
        if first_name:
            full_name = first_name
            if last_name:
                full_name += f" {last_name}"
            items["📛 نام"] = full_name
        
        role = get_user_role(target_user_id)
        role_labels = {
            0: 'کاربر عادی',
            1: '🛡️ ادمین',
            2: '📋 مدیر',
            3: '👁️ ناظر',
            10: '👑 مالک'
        }
        role_text = role_labels.get(role, 'نامشخص')
        items["🎯 نقش"] = role_text
        
        is_blocked = user_info.get('is_blocked', 0) == 1
        if is_blocked:
            blocked_at = user_info.get('blocked_at', 'نامشخص')
            block_reason = user_info.get('block_reason', 'بدون دلیل')
            items["🔴 وضعیت"] = f"مسدود شده (از {blocked_at}) - دلیل: {block_reason}"
        else:
            items["🟢 وضعیت"] = "فعال"
        
        items["📅 اولین فعالیت"] = TextFormatter.format_datetime(user_info.get('first_seen'))
        items["📅 آخرین فعالیت"] = TextFormatter.format_datetime(user_info.get('last_active'))
        
        items["📊 تعداد سفارشات"] = TextFormatter.format_number(orders_count)
        items["💰 مجموع پرداختی"] = TextFormatter.format_currency(total_payment)
        
        if last_order:
            from admin_panel.common import get_order_status_persian
            items["🕐 آخرین سفارش"] = TextFormatter.format_datetime(last_order.get('created_at'))
            items["📌 وضعیت آخرین سفارش"] = get_order_status_persian(last_order.get('status', 'نامشخص'))
        
        msg = InfoCard.create(f"کاربر {target_user_id}", items, emoji=Emojis.USER)
        
        keyboard = user_detail_keyboard(target_user_id)
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_detail: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات کاربر.")
        return True


async def handle_user_stats(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        total_users = get_total_users()
        active_today = get_active_users(1)
        active_week = get_active_users(7)
        active_month = get_active_users(30)
        
        from database import get_blocked_count
        blocked_count = get_blocked_count()
        
        active_yesterday = get_active_users(2) - active_today
        growth_rate = 0
        if active_yesterday > 0:
            growth_rate = ((active_today - active_yesterday) / active_yesterday) * 100
        elif active_today > 0:
            growth_rate = 100
        
        table = TextTable(
            headers=["بازه", "تعداد کاربران"],
            align=["l", "r"]
        )
        table.add_row(["کل کاربران", str(total_users)])
        table.add_row(["مسدود شده", str(blocked_count)])
        table.add_row(["فعال امروز", str(active_today)])
        table.add_row(["فعال هفته", str(active_week)])
        table.add_row(["فعال ماه", str(active_month)])
        table.add_row(["نرخ رشد (امروز نسبت به دیروز)", f"{growth_rate:.1f}%"])
        
        active_percent = 0
        if total_users > 0:
            active_percent = (active_today / total_users) * 100
        table.add_row(["نرخ مشارکت", f"{active_percent:.1f}%"])
        
        # استفاده از استایل simple برای نمایش منظم‌تر
        msg = f"{Emojis.STATS} **آمار کاربران**\n\n"
        msg += table.render(style="simple")
        
        keyboard = user_stats_keyboard()
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_stats: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش آمار کاربران.")
        return True


async def handle_user_search(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        state_service = get_state_service()
        await state_service.set_state_field(user_id, "state", "admin_search_users")
        
        keyboard = user_search_keyboard()
        await send_message(
            chat_id,
            f"{Emojis.MAGNIFY} **جستجوی کاربران**\n\n"
            "لطفاً کلمه کلیدی را وارد کنید:\n"
            "(شناسه کاربری، نام کاربری یا نام کامل)\n\n"
            "برای انصراف، /cancel را ارسال کنید.",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_search: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع جستجو.")
        return True


async def handle_user_search_result(chat_id: int, user_id: int, keyword: str) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if not keyword or keyword.strip() == "":
            await send_message(chat_id, "❌ لطفاً یک کلمه کلیدی معتبر وارد کنید.")
            return True
        
        results = search_users(keyword.strip(), limit=20)
        
        if not results:
            msg = StatusMessage.error(
                f"هیچ کاربری با عبارت «{keyword}» یافت نشد."
            )
            await send_message(
                chat_id,
                msg,
                {
                    "inline_keyboard": [
                        [{"text": "🔙 برگشت به مدیریت کاربران", "callback_data": "admin_users"}]
                    ]
                }
            )
            await get_state_service().set_state_field(user_id, "state", "main")
            return True
        
        table = TextTable(
            headers=["وضعیت", "شناسه", "نام کاربری", "تاریخ عضویت"],
            align=["c", "l", "l", "l"]
        )
        
        for user in results:
            user_id_found = user.get('user_id', 'نامشخص')
            username = user.get('username') or user.get('first_name') or 'کاربر ناشناس'
            first_seen = format_datetime(user.get('first_seen'))
            is_blocked = user.get('is_blocked', 0) == 1
            status_icon = "🔴" if is_blocked else "🟢"
            
            table.add_row([
                status_icon,
                str(user_id_found),
                username[:20],
                first_seen,
            ])
        
        msg = f"{Emojis.MAGNIFY} **نتایج جستجو برای «{keyword}»**\n\n"
        msg += f"تعداد: {len(results)} کاربر\n\n"
        msg += table.render(style="simple")
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "👥 مشاهده لیست کامل", "callback_data": "admin_users_list"}],
                [{"text": "🔙 برگشت به مدیریت کاربران", "callback_data": "admin_users"}]
            ]
        }
        
        await send_message(chat_id, msg, keyboard)
        await get_state_service().set_state_field(user_id, "state", "main")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_search_result: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجو.")
        await get_state_service().set_state_field(user_id, "state", "main")
        return True


async def handle_user_orders(chat_id: int, user_id: int, data: str) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        parts = data.split("_")
        last_part = parts[-1]
        
        try:
            target_user_id = int(last_part)
        except ValueError:
            await send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
            return True
        
        orders = get_dynamic_orders()
        user_orders = [o for o in orders if o.get('user_id') == target_user_id]
        
        if not user_orders:
            await send_message(chat_id, f"📋 کاربر {target_user_id} هیچ سفارشی ندارد.")
            return True
        
        state_service = get_state_service()
        await state_service.set_state_field(user_id, "orders_list", user_orders)
        await state_service.set_state_field(user_id, "orders_page", 0)
        
        from .orders import admin_orders_date_keyboard
        
        keyboard = admin_orders_date_keyboard(user_orders, page=0)
        await send_message(
            chat_id,
            f"📋 **سفارشات کاربر {target_user_id}**\n\n"
            f"تعداد: {len(user_orders)} سفارش",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_orders: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش سفارشات کاربر.")
        return True


async def handle_user_unblock_from_list(chat_id: int, user_id: int, data: str) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        target_user_id = int(data.split("_")[-1])
        
        from database import unblock_user
        success = unblock_user(target_user_id)
        
        if success:
            msg = StatusMessage.success(f"کاربر {target_user_id} با موفقیت رفع مسدودیت شد.")
            await send_message(chat_id, msg)
        else:
            msg = StatusMessage.error(f"خطا در رفع مسدودیت کاربر {target_user_id}.")
            await send_message(chat_id, msg)
        
        return await handle_user_list(chat_id, user_id, 0)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_user_unblock_from_list: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در رفع مسدودیت کاربر.")
        return True


__all__ = [
    'handle_user_management',
    'handle_user_list',
    'handle_user_list_page',
    'handle_user_detail',
    'handle_user_stats',
    'handle_user_search',
    'handle_user_search_result',
    'handle_user_orders',
    'handle_user_unblock_from_list',
    'user_management_main_keyboard',
    'user_list_keyboard',
    'user_detail_keyboard',
    'user_stats_keyboard',
    'user_search_keyboard',
]