# utils/user_helpers.py
# توابع کمکی برای پردازش اطلاعات کاربران
# جایگزین توابع تکراری در profile.py, admin_panel/user_management.py, admin_panel/admin_management.py

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from database import get_user, get_user_orders_count, get_user_total_payment, get_dynamic_orders
from .formatters import format_datetime, format_number, format_price, human_readable_time


# ============================================================
# توابع اصلی اطلاعات کاربر
# ============================================================

def get_user_display_name(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> str:
    """
    دریافت نام قابل نمایش کاربر

    پارامترها:
        user: دیکشنری اطلاعات کاربر (در صورت عدم ارائه، با user_id دریافت می‌شود)
        user_id: شناسه کاربر (در صورت عدم ارائه user)

    بازگشت: نام قابل نمایش
    """
    if not user and user_id:
        user = get_user(user_id)

    if not user:
        return "کاربر ناشناس"

    first_name = user.get('first_name')
    last_name = user.get('last_name')
    username = user.get('username')
    uid = user.get('user_id')

    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif username:
        return f"@{username}"
    elif uid:
        return f"کاربر {uid}"

    return "کاربر ناشناس"


def get_user_full_name(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> str:
    """
    دریافت نام کامل کاربر

    پارامترها:
        user: دیکشنری اطلاعات کاربر
        user_id: شناسه کاربر

    بازگشت: نام کامل یا 'کاربر ناشناس'
    """
    if not user and user_id:
        user = get_user(user_id)

    if not user:
        return "کاربر ناشناس"

    first_name = user.get('first_name', '')
    last_name = user.get('last_name', '')

    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif last_name:
        return last_name

    return "کاربر ناشناس"


def get_user_short_name(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None, max_length: int = 15) -> str:
    """
    دریافت نام کوتاه کاربر (برای نمایش در لیست‌ها)

    پارامترها:
        user: دیکشنری اطلاعات کاربر
        user_id: شناسه کاربر
        max_length: حداکثر طول نام

    بازگشت: نام کوتاه‌شده
    """
    name = get_user_display_name(user, user_id)
    if len(name) > max_length:
        return name[:max_length] + "..."
    return name


def get_user_mention(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> str:
    """
    دریافت منشن کاربر برای پیام‌ها

    پارامترها:
        user: دیکشنری اطلاعات کاربر
        user_id: شناسه کاربر

    بازگشت: منشن کاربر
    """
    if not user and user_id:
        user = get_user(user_id)

    if not user:
        return "کاربر ناشناس"

    username = user.get('username')
    if username:
        return f"@{username}"

    return get_user_display_name(user)


def get_user_profile_link(user_id: int) -> str:
    """
    دریافت لینک پروفایل کاربر (برای استفاده در پیام‌ها)

    پارامترها:
        user_id: شناسه کاربر

    بازگشت: لینک پروفایل
    """
    # در بله، لینک پروفایل به صورت t.me/username یا با شناسه مستقیم است
    user = get_user(user_id)
    if user and user.get('username'):
        return f"https://t.me/{user['username']}"
    return f"tg://user?id={user_id}"


# ============================================================
# توابع نقش و وضعیت
# ============================================================

def get_role_label(role: str) -> str:
    """
    دریافت برچسب فارسی نقش

    پارامترها:
        role: نقش (owner, admin, manager, observer)

    بازگشت: برچسب فارسی با آیکون
    """
    labels = {
        'owner': '👑 مالک',
        'admin': '🛡️ ادمین',
        'manager': '📋 مدیر',
        'observer': '👁️ ناظر',
        'user': '👤 کاربر',
        'super_admin': '👑 سوپر ادمین',
        'moderator': '🛡️ مدیر',
        'support': '📞 پشتیبان',
    }
    return labels.get(role, f"🎯 {role}")


def get_role_icon(role: str) -> str:
    """
    دریافت آیکون نقش

    پارامترها:
        role: نقش

    بازگشت: آیکون
    """
    icons = {
        'owner': '👑',
        'admin': '🛡️',
        'manager': '📋',
        'observer': '👁️',
        'user': '👤',
        'super_admin': '👑',
        'moderator': '🛡️',
        'support': '📞',
    }
    return icons.get(role, '🎯')


def get_role_priority(role: str) -> int:
    """
    دریافت اولویت نقش (عدد بزرگتر = دسترسی بیشتر)

    پارامترها:
        role: نقش

    بازگشت: عدد اولویت
    """
    priorities = {
        'owner': 100,
        'super_admin': 90,
        'admin': 80,
        'manager': 60,
        'moderator': 50,
        'support': 40,
        'observer': 30,
        'user': 10,
    }
    return priorities.get(role, 0)


def get_status_label(status: str) -> str:
    """
    دریافت برچسب فارسی وضعیت کاربر

    پارامترها:
        status: وضعیت (active, blocked, deleted)

    بازگشت: برچسب فارسی با آیکون
    """
    labels = {
        'active': '🟢 فعال',
        'blocked': '🔴 مسدود شده',
        'deleted': '🗑️ حذف شده',
        'inactive': '⚪ غیرفعال',
        'pending': '⏳ در انتظار تایید',
    }
    return labels.get(status, f"❓ {status}")


def get_status_icon(status: str) -> str:
    """
    دریافت آیکون وضعیت کاربر

    پارامترها:
        status: وضعیت

    بازگشت: آیکون
    """
    icons = {
        'active': '🟢',
        'blocked': '🔴',
        'deleted': '🗑️',
        'inactive': '⚪',
        'pending': '⏳',
    }
    return icons.get(status, '❓')


def is_user_active(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> bool:
    """
    بررسی فعال بودن کاربر

    پارامترها:
        user: دیکشنری اطلاعات کاربر
        user_id: شناسه کاربر

    بازگشت: True اگر کاربر فعال باشد
    """
    if not user and user_id:
        user = get_user(user_id)

    if not user:
        return False

    # بررسی مسدود نبودن
    if user.get('is_blocked', 0) == 1:
        return False

    # بررسی وضعیت
    status = user.get('status', 0)
    return status == 0  # 0 = فعال


def is_user_blocked(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> bool:
    """
    بررسی مسدود بودن کاربر

    پارامترها:
        user: دیکشنری اطلاعات کاربر
        user_id: شناسه کاربر

    بازگشت: True اگر کاربر مسدود باشد
    """
    if not user and user_id:
        user = get_user(user_id)

    if not user:
        return False

    return user.get('is_blocked', 0) == 1


def get_user_status_text(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> str:
    """
    دریافت متن وضعیت کاربر

    پارامترها:
        user: دیکشنری اطلاعات کاربر
        user_id: شناسه کاربر

    بازگشت: متن وضعیت
    """
    if not user and user_id:
        user = get_user(user_id)

    if not user:
        return "نامشخص"

    if is_user_blocked(user):
        reason = user.get('block_reason', 'بدون دلیل')
        blocked_at = user.get('blocked_at', '')
        if blocked_at:
            return f"🔴 مسدود شده (از {format_datetime(blocked_at)}) - دلیل: {reason}"
        return f"🔴 مسدود شده - دلیل: {reason}"

    if is_user_active(user):
        last_active = user.get('last_active')
        if last_active:
            return f"🟢 فعال (آخرین فعالیت: {format_datetime(last_active)})"
        return "🟢 فعال"

    status = user.get('status', 0)
    if status == 1:
        return "🔴 مسدود شده"
    if status == 2:
        return "🗑️ حذف شده"

    return "⚪ نامشخص"


def get_user_last_active_text(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> str:
    """
    دریافت متن آخرین فعالیت کاربر

    پارامترها:
        user: دیکشنری اطلاعات کاربر
        user_id: شناسه کاربر

    بازگشت: متن آخرین فعالیت
    """
    if not user and user_id:
        user = get_user(user_id)

    if not user:
        return "نامشخص"

    last_active = user.get('last_active')
    if not last_active:
        return "نامشخص"

    try:
        if isinstance(last_active, str):
            if 'T' in last_active:
                dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
            elif ' ' in last_active:
                dt = datetime.strptime(last_active[:19], "%Y-%m-%d %H:%M:%S")
            else:
                return format_datetime(last_active)
        elif isinstance(last_active, datetime):
            dt = last_active
        else:
            return format_datetime(last_active)

        return human_readable_time(dt)
    except:
        return format_datetime(last_active)


def get_user_joined_date(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> str:
    """
    دریافت تاریخ عضویت کاربر

    پارامترها:
        user: دیکشنری اطلاعات کاربر
        user_id: شناسه کاربر

    بازگشت: تاریخ عضویت
    """
    if not user and user_id:
        user = get_user(user_id)

    if not user:
        return "نامشخص"

    first_seen = user.get('first_seen')
    if not first_seen:
        return "نامشخص"

    return format_datetime(first_seen)


def get_user_age_days(user: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> Optional[int]:
    """
    دریافت تعداد روزهای از عضویت کاربر

    پارامترها:
        user: دیکشنری اطلاعات کاربر
        user_id: شناسه کاربر

    بازگشت: تعداد روزها یا None
    """
    if not user and user_id:
        user = get_user(user_id)

    if not user:
        return None

    first_seen = user.get('first_seen')
    if not first_seen:
        return None

    try:
        if isinstance(first_seen, str):
            if 'T' in first_seen:
                dt = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
            elif ' ' in first_seen:
                dt = datetime.strptime(first_seen[:19], "%Y-%m-%d %H:%M:%S")
            else:
                return None
        elif isinstance(first_seen, datetime):
            dt = first_seen
        else:
            return None

        diff = datetime.now() - dt
        return diff.days
    except:
        return None


# ============================================================
# توابع آمار کاربران
# ============================================================

def get_user_orders_summary(user_id: int) -> Dict[str, Any]:
    """
    دریافت خلاصه سفارشات کاربر

    پارامترها:
        user_id: شناسه کاربر

    بازگشت: دیکشنری شامل آمار سفارشات
    """
    orders_count = get_user_orders_count(user_id)
    total_payment = get_user_total_payment(user_id)

    # دریافت تفکیک وضعیت‌ها
    orders = get_dynamic_orders()
    user_orders = [o for o in orders if o.get('user_id') == user_id]

    status_counts = {}
    for order in user_orders:
        status = order.get('status', 'pending')
        status_counts[status] = status_counts.get(status, 0) + 1

    # آخرین سفارش
    last_order = None
    if user_orders:
        user_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        last_order = user_orders[0]

    return {
        'total_orders': orders_count,
        'total_payment': total_payment,
        'avg_amount': total_payment // orders_count if orders_count > 0 else 0,
        'status_counts': status_counts,
        'last_order': last_order,
        'has_orders': orders_count > 0,
    }


def get_user_activity_summary(user_id: int) -> Dict[str, Any]:
    """
    دریافت خلاصه فعالیت کاربر (کلیک‌ها، شروع فرم، ...)

    پارامترها:
        user_id: شناسه کاربر

    بازگشت: دیکشنری شامل آمار فعالیت
    """
    from database import get_db_connection

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # آمار کلیک‌ها
        cursor.execute("""
            SELECT action_type, COUNT(*) as count
            FROM button_stats
            WHERE user_id = ?
            GROUP BY action_type
        """, (user_id,))
        action_stats = [dict(row) for row in cursor.fetchall()]

        # آخرین فعالیت
        cursor.execute("""
            SELECT action_type, created_at
            FROM button_stats
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        last_activity = cursor.fetchone()

    total_actions = sum(s.get('count', 0) for s in action_stats)

    return {
        'total_actions': total_actions,
        'action_stats': action_stats,
        'last_activity': dict(last_activity) if last_activity else None,
        'clicks': sum(s.get('count', 0) for s in action_stats if s.get('action_type') == 'click'),
        'form_starts': sum(s.get('count', 0) for s in action_stats if s.get('action_type') == 'form_start'),
        'order_paid': sum(s.get('count', 0) for s in action_stats if s.get('action_type') == 'order_paid'),
    }


def get_user_brief(user_id: int) -> str:
    """
    دریافت خلاصه بسیار کوتاه کاربر (برای کیبوردها)

    پارامترها:
        user_id: شناسه کاربر

    بازگشت: متن کوتاه
    """
    user = get_user(user_id)
    if not user:
        return f"کاربر {user_id}"

    name = get_user_display_name(user)
    status_icon = "🟢" if is_user_active(user) else "🔴" if is_user_blocked(user) else "⚪"

    return f"{status_icon} {name} ({user_id})"


def get_user_display_for_admin(user_id: int) -> str:
    """
    دریافت اطلاعات نمایشی کاربر برای پنل مدیریت

    پارامترها:
        user_id: شناسه کاربر

    بازگشت: متن کامل
    """
    user = get_user(user_id)
    if not user:
        return f"کاربر {user_id} (نامشخص)"

    name = get_user_display_name(user)
    username = user.get('username')
    is_admin = False
    from database import is_admin as db_is_admin
    try:
        is_admin = db_is_admin(user_id)
    except:
        pass

    admin_tag = " 🛡️" if is_admin else ""
    blocked_tag = " 🔴" if is_user_blocked(user) else ""

    if username:
        return f"{name} (@{username}){admin_tag}{blocked_tag}"
    return f"{name} ({user_id}){admin_tag}{blocked_tag}"


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # توابع اطلاعات کاربر
    'get_user_display_name',
    'get_user_full_name',
    'get_user_short_name',
    'get_user_mention',
    'get_user_profile_link',

    # توابع نقش و وضعیت
    'get_role_label',
    'get_role_icon',
    'get_role_priority',
    'get_status_label',
    'get_status_icon',
    'is_user_active',
    'is_user_blocked',
    'get_user_status_text',
    'get_user_last_active_text',
    'get_user_joined_date',
    'get_user_age_days',

    # توابع آمار
    'get_user_orders_summary',
    'get_user_activity_summary',

    # توابع نمایش
    'get_user_brief',
    'get_user_display_for_admin',
]