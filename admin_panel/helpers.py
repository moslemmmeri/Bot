# admin_panel/helpers.py
# توابع کمکی مشترک برای بخش‌های مختلف پنل مدیریت
# شامل: بررسی دسترسی، فرمت‌بندی اعداد و تاریخ، و سایر توابع کاربردی

import json
import traceback  # ✅ اضافه شد برای traceback کامل
from datetime import datetime, timedelta
from config import config
from database import get_button_by_id
from utils import (
    format_number as utils_format_number,
    format_percent as utils_format_percent,
    format_datetime as utils_format_datetime,
    get_service_name as utils_get_service_name,
    get_fullname_from_order as utils_get_fullname,
    get_order_status_persian,
    format_price,
    get_user_display_name,
    get_role_label,
    get_status_label,
    get_today_str,
    get_yesterday_str,
    get_date_range,
)
from utils.error_handler import log_general_error  # ✅ اضافه شد


# ==================== توابع دسترسی ====================

def is_owner(user_id):
    """
    بررسی آیا کاربر OWNER_ID است.
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True اگر کاربر OWNER باشد، در غیر این صورت False
    """
    return user_id == config.OWNER_ID


# ==================== توابع فرمت‌بندی ====================

def format_number(num, default="۰"):
    """
    فرمت‌بندی اعداد با کاما (جداساز هزارگان).
    
    پارامترها:
        num: عدد (می‌تواند None، int یا float باشد)
        default: مقدار پیش‌فرض
    
    بازگشت: رشته فرمت‌شده یا مقدار پیش‌فرض در صورت None
    """
    return utils_format_number(num, default)


def format_percent(num, decimals=2, default="۰%"):
    """
    فرمت‌بندی درصد.
    
    پارامترها:
        num: عدد درصد
        decimals: تعداد رقم اعشار
        default: مقدار پیش‌فرض
    
    بازگشت: رشته فرمت‌شده با علامت درصد
    """
    return utils_format_percent(num, decimals, default)


def format_datetime(dt, default="نامشخص"):
    """
    فرمت‌بندی تاریخ و زمان به شکل خوانا.
    
    پارامترها:
        dt: رشته تاریخ یا None
        default: مقدار پیش‌فرض
    
    بازگشت: رشته فرمت‌شده یا مقدار پیش‌فرض
    """
    return utils_format_datetime(dt, default)


# ==================== توابع مربوط به سفارشات ====================

def extract_date_from_order(order):
    """
    استخراج تاریخ (فقط YYYY-MM-DD) از created_at سفارش.
    
    پارامترها:
        order: دیکشنری سفارش
    
    بازگشت: رشته تاریخ به فرمت YYYY-MM-DD
    """
    created_at = order.get('created_at', '')
    if not created_at:
        return ""
    if isinstance(created_at, str):
        if ' ' in created_at:
            return created_at.split(' ')[0]
        elif 'T' in created_at:
            return created_at.split('T')[0]
        return created_at[:10] if len(created_at) >= 10 else created_at
    if hasattr(created_at, 'strftime'):
        return created_at.strftime("%Y-%m-%d")
    return str(created_at)[:10]


def get_service_name(button_id):
    """
    دریافت نام سرویس با در نظر گرفتن زیرمنو (اگر والد دارد).
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: نام کامل سرویس (با والد اگر وجود داشته باشد)
    """
    try:
        return utils_get_service_name(button_id)
    except Exception as e:
        log_general_error(
            f"Error in get_service_name for button_id {button_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return f"سرویس {button_id}"


def get_fullname_from_order(order):
    """
    استخراج نام کامل کاربر از order_data یا پاسخ‌ها.
    
    پارامترها:
        order: دیکشنری سفارش
    
    بازگشت: نام کامل کاربر یا 'کاربر ناشناس'
    """
    return utils_get_fullname(order)


def get_order_status_label(status):
    """
    دریافت برچسب فارسی وضعیت سفارش.
    
    پارامترها:
        status: وضعیت سفارش (pending, paid, completed, cancelled, ...)
    
    بازگشت: برچسب فارسی با آیکون
    """
    return get_order_status_persian(status)


# ==================== توابع نقش و وضعیت ====================

def get_role_label(role):
    """
    دریافت برچسب فارسی نقش.
    
    پارامترها:
        role: نقش (owner, admin, manager, observer)
    
    بازگشت: برچسب فارسی با آیکون
    """
    return get_role_label(role)


def get_status_label(is_active):
    """
    دریافت برچسب فارسی وضعیت.
    
    پارامترها:
        is_active: 1 یا 0
    
    بازگشت: برچسب فارسی با آیکون
    """
    return "🟢 فعال" if is_active == 1 else "🔴 غیرفعال"


# ==================== توابع مربوط به کیبورد و منو ====================

def chunk_list(lst, n=2):
    """
    تقسیم لیست به گروه‌های n تایی برای نمایش در ردیف‌های کنار هم.
    
    پارامترها:
        lst: لیست ورودی
        n: تعداد ستون‌ها (تعداد دکمه در هر ردیف)
    
    بازگشت: لیستی از گروه‌های n تایی
    """
    if n < 1:
        n = 1
    if n > 8:  # حداکثر ۸ دکمه در هر ردیف (محدودیت تلگرام)
        n = 8
    return [lst[i:i+n] for i in range(0, len(lst), n)]


# ==================== توابع مربوط به خطاها ====================

def get_error_type_icon(error_type):
    """
    دریافت آیکون مناسب برای نوع خطا.
    
    پارامترها:
        error_type: نوع خطا
    
    بازگشت: آیکون (اموجی)
    """
    type_icons = {
        'database': '🗄️',
        'api': '🌐',
        'callback': '🔄',
        'general': '📌',
        'payment': '💰',
        'security': '🔒',
        'critical': '🚨'
    }
    return type_icons.get(error_type, '⚠️')


# ==================== توابع مربوط به نسخه‌سازی ====================

def get_button_name(button_id):
    """
    دریافت نام دکمه با شناسه.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: نام دکمه یا "دکمه {شناسه}" در صورت عدم وجود
    """
    try:
        btn = get_button_by_id(button_id)
        return btn['name'] if btn else f"دکمه {button_id}"
    except Exception as e:
        log_general_error(
            f"Error in get_button_name for button_id {button_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return f"دکمه {button_id}"


# ==================== توابع مربوط به قیمت متغیر ====================

def get_price_display(price_info):
    """
    دریافت متن قابل نمایش برای قیمت.
    
    پارامترها:
        price_info: دیکشنری اطلاعات قیمت
    
    بازگشت: رشته نمایشی قیمت
    """
    try:
        price_type = price_info.get('price_type', 'fixed')
        
        if price_type == 'fixed':
            amount = price_info.get('price_amount', 0)
            label = price_info.get('price_label', 'هزینه خدمات')
            return f"{label}: {format_number(amount)} ریال"
        
        if price_type == 'variable':
            min_price = price_info.get('min_price')
            max_price = price_info.get('max_price')
            label = price_info.get('price_label', 'هزینه خدمات')
            
            if min_price is not None and max_price is not None:
                return f"{label}: {format_number(min_price)} تا {format_number(max_price)} ریال (متغیر)"
            elif min_price is not None:
                return f"{label}: حداقل {format_number(min_price)} ریال (متغیر)"
            elif max_price is not None:
                return f"{label}: حداکثر {format_number(max_price)} ریال (متغیر)"
            else:
                return f"{label}: متغیر (بدون محدودیت)"
        
        return "قیمت نامشخص"
    except Exception as e:
        log_general_error(
            f"Error in get_price_display: {str(e)}",
            traceback=traceback.format_exc()
        )
        return "خطا در نمایش قیمت"


# ==================== توابع مربوط به تاریخ ====================

def get_today_str():
    """دریافت تاریخ امروز به فرمت YYYY-MM-DD"""
    return get_today_str()


def get_yesterday_str():
    """دریافت تاریخ دیروز به فرمت YYYY-MM-DD"""
    return get_yesterday_str()


def get_date_range(days=30):
    """
    دریافت بازه زمانی از امروز تا days روز قبل.
    
    پارامترها:
        days: تعداد روزهای گذشته
    
    بازگشت: (start_date, end_date) به فرمت YYYY-MM-DD
    """
    return get_date_range(days)


# ==================== سایر توابع کمکی ====================

def format_price(amount, currency="ریال", default="۰"):
    """فرمت‌بندی مبلغ با واحد پول"""
    return format_price(amount, currency, default)


def get_user_display_name_from_id(user_id):
    """دریافت نام قابل نمایش کاربر با شناسه"""
    return get_user_display_name(user_id=user_id)


def is_valid_uuid(value):
    """بررسی معتبر بودن UUID"""
    import re
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, str(value).lower()))


def safe_json_loads(json_str, default=None):
    """تبدیل ایمن JSON به دیکشنری"""
    try:
        if not json_str:
            return default
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        log_general_error(
            f"Error in safe_json_loads: {str(e)}",
            traceback=traceback.format_exc()
        )
        return default


# ==================== صادر کردن ====================

__all__ = [
    # دسترسی
    'is_owner',
    # فرمت‌بندی
    'format_number',
    'format_percent',
    'format_datetime',
    # سفارشات
    'extract_date_from_order',
    'get_service_name',
    'get_fullname_from_order',
    'get_order_status_label',
    # نقش و وضعیت
    'get_role_label',
    'get_status_label',
    # کیبورد
    'chunk_list',
    # خطاها
    'get_error_type_icon',
    # نسخه‌سازی
    'get_button_name',
    # قیمت
    'get_price_display',
    # تاریخ
    'get_today_str',
    'get_yesterday_str',
    'get_date_range',
    # سایر
    'format_price',
    'get_user_display_name_from_id',
    'is_valid_uuid',
    'safe_json_loads',
]