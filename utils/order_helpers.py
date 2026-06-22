# utils/order_helpers.py
# توابع کمکی برای پردازش سفارشات
# جایگزین توابع تکراری در profile.py, admin_panel/orders.py, admin_panel/common.py

import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

# ایمپورت از ماژول‌های پروژه
from database import get_button_by_id
from .formatters import format_number, format_datetime, format_date, format_price


# ============================================================
# توابع اصلی سفارشات
# ============================================================

def get_service_name(button_id: int) -> str:
    """
    دریافت نام سرویس با در نظر گرفتن زیرمنو (اگر والد دارد)

    پارامترها:
        button_id: شناسه دکمه

    بازگشت: نام کامل سرویس (با والد اگر وجود داشته باشد)
    """
    if not button_id:
        return "نامشخص"

    btn = get_button_by_id(button_id)
    if not btn:
        return f"سرویس {button_id}"

    if btn.get('parent_button_id'):
        parent = get_button_by_id(btn['parent_button_id'])
        if parent:
            return f"{parent['name']} > {btn['name']}"

    return btn['name']


def get_service_name_short(button_id: int, max_length: int = 20) -> str:
    """
    دریافت نام کوتاه سرویس (برای نمایش در لیست‌ها)

    پارامترها:
        button_id: شناسه دکمه
        max_length: حداکثر طول نام

    بازگشت: نام کوتاه‌شده سرویس
    """
    name = get_service_name(button_id)
    if len(name) > max_length:
        return name[:max_length] + "..."
    return name


def get_fullname_from_order(order: Dict[str, Any]) -> str:
    """
    استخراج نام کامل کاربر از order_data یا پاسخ‌ها

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: نام کامل کاربر یا 'کاربر ناشناس'
    """
    if not order:
        return 'کاربر ناشناس'

    order_data = order.get('order_data', {})
    if isinstance(order_data, str):
        try:
            order_data = json.loads(order_data)
        except:
            order_data = {}

    # بررسی فیلد fullname در order_data
    fullname = order_data.get('fullname')
    if fullname:
        return fullname

    # اگر در order_data نبود، از اولین پاسخ (معمولاً نام) استفاده می‌کنیم
    answers = order_data.get('answers', {})
    if answers:
        first_answer = next(iter(answers.values()), 'کاربر ناشناس')
        return str(first_answer)

    return 'کاربر ناشناس'


def extract_date_from_order(order: Dict[str, Any]) -> str:
    """
    استخراج تاریخ (فقط YYYY-MM-DD) از created_at سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: رشته تاریخ به فرمت YYYY-MM-DD
    """
    if not order:
        return ""

    created_at = order.get('created_at', '')
    if not created_at:
        return ""

    if isinstance(created_at, str):
        if ' ' in created_at:
            return created_at.split(' ')[0]
        elif 'T' in created_at:
            return created_at.split('T')[0]
        return created_at[:10] if len(created_at) >= 10 else created_at

    if isinstance(created_at, datetime):
        return created_at.strftime("%Y-%m-%d")

    return str(created_at)[:10]


def get_order_status_persian(status: str) -> str:
    """
    دریافت متن فارسی وضعیت سفارش

    پارامترها:
        status: وضعیت سفارش (pending, paid, completed, cancelled, ...)

    بازگشت: متن فارسی با آیکون
    """
    status_map = {
        'pending': '⏳ در انتظار پرداخت',
        'paid': '✅ پرداخت شده',
        'completed': '✅ تکمیل شده',
        'cancelled': '❌ لغو شده',
        'failed': '❌ ناموفق',
        'refunded': '🔄 بازگشت وجه',
        'unknown': '❓ نامشخص'
    }
    return status_map.get(status, status_map.get('unknown', status))


def get_order_status_icon(status: str) -> str:
    """
    دریافت آیکون وضعیت سفارش

    پارامترها:
        status: وضعیت سفارش

    بازگشت: آیکون
    """
    icons = {
        'pending': '⏳',
        'paid': '✅',
        'completed': '🎉',
        'cancelled': '❌',
        'failed': '🚫',
        'refunded': '🔄',
    }
    return icons.get(status, '❓')


def get_order_status_color(status: str) -> str:
    """
    دریافت رنگ وضعیت سفارش (برای استفاده در UI)

    پارامترها:
        status: وضعیت سفارش

    بازگشت: کد رنگ
    """
    colors = {
        'pending': '#FFA500',   # نارنجی
        'paid': '#28A745',      # سبز
        'completed': '#17A2B8', # آبی
        'cancelled': '#DC3545', # قرمز
        'failed': '#DC3545',    # قرمز
        'refunded': '#6C757D',  # خاکستری
    }
    return colors.get(status, '#6C757D')


def get_order_status_emoji(status: str) -> str:
    """دریافت ایموجی وضعیت سفارش (همان get_order_status_icon)"""
    return get_order_status_icon(status)


def is_order_paid(order: Dict[str, Any]) -> bool:
    """
    بررسی پرداخت‌شده بودن سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: True اگر سفارش پرداخت شده باشد
    """
    if not order:
        return False
    status = order.get('status', '')
    return status in ['paid', 'completed']


def is_order_pending(order: Dict[str, Any]) -> bool:
    """
    بررسی در انتظار بودن سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: True اگر سفارش در انتظار پرداخت باشد
    """
    if not order:
        return False
    return order.get('status', '') == 'pending'


def is_order_completed(order: Dict[str, Any]) -> bool:
    """
    بررسی تکمیل‌شده بودن سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: True اگر سفارش تکمیل شده باشد
    """
    if not order:
        return False
    return order.get('status', '') == 'completed'


def is_order_cancelled(order: Dict[str, Any]) -> bool:
    """
    بررسی لغو‌شده بودن سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: True اگر سفارش لغو شده باشد
    """
    if not order:
        return False
    return order.get('status', '') == 'cancelled'


def get_order_amount(order: Dict[str, Any]) -> int:
    """
    دریافت مبلغ سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: مبلغ (عدد صحیح)
    """
    if not order:
        return 0
    amount = order.get('payment_amount', 0)
    return int(amount) if amount else 0


def get_order_amount_formatted(order: Dict[str, Any]) -> str:
    """
    دریافت مبلغ فرمت‌شده سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: مبلغ فرمت‌شده با کاما
    """
    return format_number(get_order_amount(order))


def get_order_tracking_code(order: Dict[str, Any]) -> str:
    """
    دریافت کد رهگیری سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: کد رهگیری یا 'ندارد'
    """
    if not order:
        return 'ندارد'
    code = order.get('tracking_code')
    return code if code else 'ندارد'


def get_order_admin_note(order: Dict[str, Any]) -> str:
    """
    دریافت یادداشت ادمین سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: یادداشت ادمین یا ''
    """
    if not order:
        return ''
    note = order.get('admin_note')
    return note if note else ''


def get_order_status_history(order: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    دریافت تاریخچه تغییرات وضعیت سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: لیست تاریخچه تغییرات
    """
    if not order:
        return []

    history = order.get('status_history')
    if not history:
        return []

    if isinstance(history, str):
        try:
            return json.loads(history)
        except:
            return []

    if isinstance(history, list):
        return history

    return []


def extract_answers_from_order(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    استخراج پاسخ‌های کاربر از سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: دیکشنری پاسخ‌ها
    """
    if not order:
        return {}

    order_data = order.get('order_data', {})
    if isinstance(order_data, str):
        try:
            order_data = json.loads(order_data)
        except:
            order_data = {}

    answers = order_data.get('answers', {})
    return answers if isinstance(answers, dict) else {}


def extract_files_from_order(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    استخراج فایل‌های ارسالی از سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: دیکشنری فایل‌ها
    """
    if not order:
        return {}

    order_data = order.get('order_data', {})
    if isinstance(order_data, str):
        try:
            order_data = json.loads(order_data)
        except:
            order_data = {}

    files = order_data.get('files', {})
    return files if isinstance(files, dict) else {}


def extract_order_data(order: Dict[str, Any]) -> Dict[str, Any]:
    """
    استخراج داده‌های کامل سفارش

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: دیکشنری order_data
    """
    if not order:
        return {}

    order_data = order.get('order_data', {})
    if isinstance(order_data, str):
        try:
            return json.loads(order_data)
        except:
            return {}

    return order_data if isinstance(order_data, dict) else {}


def get_order_summary(order: Dict[str, Any], include_user: bool = True) -> str:
    """
    دریافت خلاصه سفارش به صورت متن

    پارامترها:
        order: دیکشنری سفارش
        include_user: آیا نام کاربر نمایش داده شود

    بازگشت: متن خلاصه
    """
    if not order:
        return "سفارش نامعتبر"

    order_id = order.get('id', 'نامشخص')
    status = get_order_status_persian(order.get('status', 'unknown'))
    amount = get_order_amount_formatted(order)
    service = get_service_name(order.get('button_id'))
    created = format_datetime(order.get('created_at'))

    parts = [
        f"🆔 #{order_id}",
        f"🔘 {service}",
        f"💰 {amount} ریال",
        f"📌 {status}",
        f"📅 {created}"
    ]

    if include_user:
        user = get_fullname_from_order(order)
        parts.insert(1, f"👤 {user}")

    return " | ".join(parts)


def get_order_brief(order: Dict[str, Any]) -> str:
    """
    دریافت خلاصه بسیار کوتاه سفارش (برای کیبوردها)

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: متن کوتاه
    """
    if not order:
        return "❌ سفارش نامعتبر"

    order_id = order.get('id', '?')
    status_icon = get_order_status_icon(order.get('status', 'pending'))
    amount = get_order_amount_formatted(order)

    return f"{status_icon} #{order_id} - {amount} ریال"


def get_order_creation_date(order: Dict[str, Any]) -> Optional[datetime]:
    """
    دریافت تاریخ ایجاد سفارش به صورت datetime

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: datetime یا None
    """
    if not order:
        return None

    created_at = order.get('created_at')
    if not created_at:
        return None

    try:
        if isinstance(created_at, datetime):
            return created_at
        if isinstance(created_at, str):
            if 'T' in created_at:
                return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            if ' ' in created_at:
                return datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S")
            return datetime.strptime(created_at[:10], "%Y-%m-%d")
        return None
    except:
        return None


def get_order_age(order: Dict[str, Any]) -> Optional[int]:
    """
    دریافت سن سفارش (تعداد ثانیه از زمان ثبت)

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: تعداد ثانیه یا None
    """
    created = get_order_creation_date(order)
    if not created:
        return None

    now = datetime.now()
    diff = now - created
    return int(diff.total_seconds())


def get_order_age_text(order: Dict[str, Any]) -> str:
    """
    دریافت سن سفارش به صورت متن خوانا

    پارامترها:
        order: دیکشنری سفارش

    بازگشت: متن خوانا (مثلاً "۲ روز پیش")
    """
    seconds = get_order_age(order)
    if seconds is None:
        return "نامشخص"

    from .formatters import human_readable_time
    created = get_order_creation_date(order)
    if created:
        return human_readable_time(created)

    return "نامشخص"


def get_orders_summary(orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    دریافت خلاصه آماری از لیست سفارشات

    پارامترها:
        orders: لیست سفارشات

    بازگشت: دیکشنری شامل آمار
    """
    if not orders:
        return {
            'total': 0,
            'total_amount': 0,
            'avg_amount': 0,
            'statuses': {},
            'services': {},
            'users': set(),
        }

    total_amount = 0
    statuses = {}
    services = {}
    users = set()

    for order in orders:
        amount = get_order_amount(order)
        total_amount += amount

        status = order.get('status', 'unknown')
        statuses[status] = statuses.get(status, 0) + 1

        button_id = order.get('button_id')
        if button_id:
            service_name = get_service_name(button_id)
            services[service_name] = services.get(service_name, 0) + 1

        user_id = order.get('user_id')
        if user_id:
            users.add(user_id)

    return {
        'total': len(orders),
        'total_amount': total_amount,
        'avg_amount': total_amount // len(orders) if orders else 0,
        'statuses': statuses,
        'services': services,
        'users': list(users),
        'user_count': len(users),
    }


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # توابع اصلی
    'get_service_name',
    'get_service_name_short',
    'get_fullname_from_order',
    'extract_date_from_order',
    'get_order_status_persian',
    'get_order_status_icon',
    'get_order_status_color',
    'get_order_status_emoji',

    # توابع بررسی وضعیت
    'is_order_paid',
    'is_order_pending',
    'is_order_completed',
    'is_order_cancelled',

    # توابع استخراج اطلاعات
    'get_order_amount',
    'get_order_amount_formatted',
    'get_order_tracking_code',
    'get_order_admin_note',
    'get_order_status_history',
    'extract_answers_from_order',
    'extract_files_from_order',
    'extract_order_data',

    # توابع نمایش
    'get_order_summary',
    'get_order_brief',
    'get_order_creation_date',
    'get_order_age',
    'get_order_age_text',

    # توابع آماری
    'get_orders_summary',
]