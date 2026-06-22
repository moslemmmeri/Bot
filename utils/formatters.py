# utils/formatters.py
# توابع فرمت‌بندی پیشرفته برای اعداد، تاریخ، قیمت، مدت زمان و ...
# جایگزین توابع تکراری در سراسر پروژه

import re
import json
from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict, List
from decimal import Decimal, InvalidOperation


# ============================================================
# فرمت‌بندی اعداد
# ============================================================

def format_number(num: Any, default: str = "۰") -> str:
    """
    فرمت‌بندی اعداد با کاما (جداساز هزارگان)

    پارامترها:
        num: عدد (می‌تواند None، int، float، str یا Decimal باشد)
        default: مقدار پیش‌فرض در صورت None یا نامعتبر بودن

    بازگشت: رشته فرمت‌شده
    """
    if num is None:
        return default
    
    try:
        # تبدیل به عدد
        if isinstance(num, str):
            # حذف کاراکترهای غیرعددی
            cleaned = re.sub(r'[^\d.]', '', num)
            if not cleaned:
                return default
            value = float(cleaned)
        elif isinstance(num, Decimal):
            value = float(num)
        else:
            value = float(num)
        
        # اگر عدد اعشاری است، با دو رقم اعشار نمایش بده
        if value.is_integer():
            return f"{int(value):,}"
        else:
            return f"{value:,.2f}"
            
    except (ValueError, TypeError, InvalidOperation):
        return default


def format_percent(value: Any, decimals: int = 2, default: str = "۰%") -> str:
    """
    فرمت‌بندی درصد

    پارامترها:
        value: عدد درصد
        decimals: تعداد رقم اعشار
        default: مقدار پیش‌فرض در صورت None یا نامعتبر بودن

    بازگشت: رشته فرمت‌شده با علامت درصد
    """
    if value is None:
        return default
    
    try:
        num = float(value)
        return f"{num:.{decimals}f}%"
    except (ValueError, TypeError):
        return default


def format_price(amount: Any, currency: str = "ریال", default: str = "۰") -> str:
    """
    فرمت‌بندی مبلغ با واحد پول

    پارامترها:
        amount: مبلغ
        currency: واحد پول (پیش‌فرض: ریال)
        default: مقدار پیش‌فرض

    بازگشت: رشته فرمت‌شده با واحد پول
    """
    if amount is None:
        return f"{default} {currency}"
    
    try:
        num = int(amount)
        return f"{num:,} {currency}"
    except (ValueError, TypeError):
        return f"{default} {currency}"


def format_currency(amount: Any, currency: str = "IRT", default: str = "۰") -> str:
    """
    فرمت‌بندی مبلغ با کد ارز (برای فاکتورها)

    پارامترها:
        amount: مبلغ
        currency: کد ارز (IRT, USD, EUR, ...)
        default: مقدار پیش‌فرض

    بازگشت: رشته فرمت‌شده با کد ارز
    """
    return format_price(amount, currency, default)


def format_boolean(value: Any, true_text: str = "بله", false_text: str = "خیر") -> str:
    """
    فرمت‌بندی مقدار بولی به متن

    پارامترها:
        value: مقدار (True/False یا 1/0 یا "1"/"0")
        true_text: متن برای True
        false_text: متن برای False

    بازگشت: متن مربوطه
    """
    if value is None:
        return false_text
    
    if isinstance(value, bool):
        return true_text if value else false_text
    
    if isinstance(value, (int, float)):
        return true_text if value else false_text
    
    if isinstance(value, str):
        return true_text if value.lower() in ('1', 'true', 'yes', 'بله') else false_text
    
    return false_text


def format_yes_no(value: Any) -> str:
    """فرمت‌بندی مقدار بولی به «بله/خیر»"""
    return format_boolean(value, "✅ بله", "❌ خیر")


def truncate_number(value: Any, max_value: int = 1000000000) -> str:
    """
    کوتاه‌سازی اعداد بزرگ با واحدهای K, M, B, T

    پارامترها:
        value: عدد
        max_value: حداکثر مقدار قبل از کوتاه‌سازی

    بازگشت: رشته کوتاه‌شده
    """
    if value is None:
        return "۰"
    
    try:
        num = float(value)
        
        if num < 1000:
            return str(int(num))
        elif num < 1000000:
            return f"{num/1000:.1f}K"
        elif num < 1000000000:
            return f"{num/1000000:.1f}M"
        elif num < 1000000000000:
            return f"{num/1000000000:.1f}B"
        else:
            return f"{num/1000000000000:.1f}T"
            
    except (ValueError, TypeError):
        return "۰"


def human_readable_size(size_bytes: Any, decimals: int = 2) -> str:
    """
    تبدیل حجم به فرمت خوانا (B, KB, MB, GB, TB)

    پارامترها:
        size_bytes: حجم به بایت
        decimals: تعداد رقم اعشار

    بازگشت: رشته فرمت‌شده
    """
    if size_bytes is None or size_bytes == 0:
        return "۰ B"
    
    try:
        size = float(size_bytes)
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        
        for unit in units:
            if size < 1024.0:
                return f"{size:.{decimals}f} {unit}"
            size /= 1024.0
        
        return f"{size:.{decimals}f} {units[-1]}"
        
    except (ValueError, TypeError):
        return "نامشخص"


# ============================================================
# فرمت‌بندی تاریخ و زمان
# ============================================================

def format_datetime(dt: Any, default: str = "نامشخص") -> str:
    """
    فرمت‌بندی تاریخ و زمان

    پارامترها:
        dt: تاریخ (datetime, str یا None)
        default: مقدار پیش‌فرض

    بازگشت: رشته فرمت‌شده (YYYY-MM-DD HH:MM)
    """
    if not dt:
        return default
    
    try:
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M")
        
        if isinstance(dt, str):
            # تلاش برای تشخیص فرمت‌های مختلف
            if len(dt) >= 10:
                # اگر شامل تاریخ است
                if 'T' in dt:
                    # فرمت ISO
                    dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                    return dt_obj.strftime("%Y-%m-%d %H:%M")
                elif ' ' in dt:
                    # فرمت با فاصله
                    parts = dt.split(' ')
                    if len(parts) >= 2:
                        return ' '.join(parts[:2])[:16]
                    return dt[:16]
                else:
                    # فقط تاریخ
                    return dt[:10]
            return dt
        
        return str(dt)
        
    except Exception:
        return default


def format_date(dt: Any, default: str = "نامشخص") -> str:
    """
    فرمت‌بندی تاریخ (بدون زمان)

    پارامترها:
        dt: تاریخ (datetime, str یا None)
        default: مقدار پیش‌فرض

    بازگشت: رشته فرمت‌شده (YYYY-MM-DD)
    """
    if not dt:
        return default
    
    try:
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d")
        
        if isinstance(dt, str):
            # استخراج تاریخ
            if len(dt) >= 10:
                if 'T' in dt:
                    return dt[:10]
                elif ' ' in dt:
                    return dt.split(' ')[0][:10]
                else:
                    return dt[:10]
            return dt
        
        return str(dt)
        
    except Exception:
        return default


def format_time(dt: Any, default: str = "نامشخص") -> str:
    """
    فرمت‌بندی زمان (بدون تاریخ)

    پارامترها:
        dt: تاریخ (datetime, str یا None)
        default: مقدار پیش‌فرض

    بازگشت: رشته فرمت‌شده (HH:MM)
    """
    if not dt:
        return default
    
    try:
        if isinstance(dt, datetime):
            return dt.strftime("%H:%M")
        
        if isinstance(dt, str):
            if ' ' in dt:
                parts = dt.split(' ')
                if len(parts) > 1:
                    time_part = parts[1]
                    return time_part[:5]
            elif 'T' in dt:
                parts = dt.split('T')
                if len(parts) > 1:
                    time_part = parts[1]
                    return time_part[:5]
            return dt[:5]
        
        return str(dt)
        
    except Exception:
        return default


def format_duration(seconds: Any, default: str = "نامشخص") -> str:
    """
    فرمت‌بندی مدت زمان

    پارامترها:
        seconds: تعداد ثانیه
        default: مقدار پیش‌فرض

    بازگشت: رشته فرمت‌شده (X روز X ساعت X دقیقه X ثانیه)
    """
    if seconds is None:
        return default
    
    try:
        total_seconds = int(seconds)
        
        if total_seconds < 0:
            return default
        
        if total_seconds < 60:
            return f"{total_seconds} ثانیه"
        
        minutes = total_seconds // 60
        if minutes < 60:
            return f"{minutes} دقیقه"
        
        hours = minutes // 60
        minutes_remain = minutes % 60
        
        if hours < 24:
            if minutes_remain == 0:
                return f"{hours} ساعت"
            return f"{hours} ساعت و {minutes_remain} دقیقه"
        
        days = hours // 24
        hours_remain = hours % 24
        
        if hours_remain == 0:
            return f"{days} روز"
        if minutes_remain == 0:
            return f"{days} روز و {hours_remain} ساعت"
        return f"{days} روز و {hours_remain} ساعت و {minutes_remain} دقیقه"
        
    except (ValueError, TypeError):
        return default


def human_readable_time(timestamp: Any) -> str:
    """
    تبدیل timestamp به زمان خوانا به صورت نسبی (مثلاً "۵ دقیقه پیش")

    پارامترها:
        timestamp: زمان (datetime یا timestamp عددی)

    بازگشت: رشته زمان نسبی
    """
    try:
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            return format_datetime(timestamp)
        
        now = datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "چند لحظه پیش"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} دقیقه پیش"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} ساعت پیش"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} روز پیش"
        elif seconds < 2592000:
            weeks = int(seconds // 604800)
            return f"{weeks} هفته پیش"
        elif seconds < 31536000:
            months = int(seconds // 2592000)
            return f"{months} ماه پیش"
        else:
            years = int(seconds // 31536000)
            return f"{years} سال پیش"
            
    except Exception:
        return format_datetime(timestamp)


# ============================================================
# فرمت‌بندی اختصاصی
# ============================================================

def format_phone(phone: Any, default: str = "نامشخص") -> str:
    """
    فرمت‌بندی شماره تلفن

    پارامترها:
        phone: شماره تلفن
        default: مقدار پیش‌فرض

    بازگشت: شماره فرمت‌شده
    """
    if not phone:
        return default
    
    try:
        phone_str = str(phone).strip()
        # حذف کاراکترهای غیرعددی
        cleaned = re.sub(r'[^\d]', '', phone_str)
        
        if len(cleaned) == 11 and cleaned.startswith('09'):
            # تلفن همراه: ۰۹۱۲۳۴۵۶۷۸۹
            return f"{cleaned[:4]} {cleaned[4:7]} {cleaned[7:]}"
        elif len(cleaned) == 10:
            # تلفن ثابت: ۰۲۱۲۳۴۵۶۷۸
            return f"{cleaned[:3]} {cleaned[3:6]} {cleaned[6:]}"
        elif len(cleaned) > 0:
            # سایر
            return cleaned
        else:
            return default
            
    except Exception:
        return default


def format_national_code(code: Any, default: str = "نامشخص") -> str:
    """
    فرمت‌بندی کد ملی

    پارامترها:
        code: کد ملی
        default: مقدار پیش‌فرض

    بازگشت: کد ملی فرمت‌شده
    """
    if not code:
        return default
    
    try:
        code_str = str(code).strip()
        cleaned = re.sub(r'[^\d]', '', code_str)
        
        if len(cleaned) == 10:
            return cleaned
        return cleaned if cleaned else default
        
    except Exception:
        return default


def format_tracking_code(code: Any, default: str = "ندارد") -> str:
    """
    فرمت‌بندی کد رهگیری

    پارامترها:
        code: کد رهگیری
        default: مقدار پیش‌فرض

    بازگشت: کد رهگیری فرمت‌شده
    """
    if not code:
        return default
    
    try:
        code_str = str(code).strip()
        if len(code_str) > 8:
            return f"{code_str[:4]}-{code_str[4:8]}-{code_str[8:]}"
        return code_str
    except Exception:
        return default


def format_order_status(status: str) -> str:
    """
    فرمت‌بندی وضعیت سفارش با آیکون

    پارامترها:
        status: وضعیت سفارش

    بازگشت: وضعیت با آیکون
    """
    status_map = {
        'pending': '⏳ در انتظار پرداخت',
        'paid': '✅ پرداخت شده',
        'completed': '✅ تکمیل شده',
        'cancelled': '❌ لغو شده',
        'failed': '❌ ناموفق',
        'refunded': '🔄 بازگشت وجه',
    }
    return status_map.get(status, status)


# ============================================================
# فرمت‌بندی برای نمایش در پیام‌ها
# ============================================================

def format_ordered_list(items: List[Any], start: int = 1) -> str:
    """
    فرمت‌بندی لیست شماره‌دار

    پارامترها:
        items: لیست آیتم‌ها
        start: شماره شروع

    بازگشت: رشته لیست شماره‌دار
    """
    if not items:
        return ""
    
    result = []
    for i, item in enumerate(items, start):
        result.append(f"{i}. {item}")
    
    return "\n".join(result)


def format_bullet_list(items: List[Any], bullet: str = "•") -> str:
    """
    فرمت‌بندی لیست گلوله‌ای

    پارامترها:
        items: لیست آیتم‌ها
        bullet: علامت گلوله

    بازگشت: رشته لیست گلوله‌ای
    """
    if not items:
        return ""
    
    result = []
    for item in items:
        result.append(f"{bullet} {item}")
    
    return "\n".join(result)


def format_key_value(key: str, value: Any, separator: str = ": ") -> str:
    """
    فرمت‌بندی کلید-مقدار

    پارامترها:
        key: کلید
        value: مقدار
        separator: جداکننده

    بازگشت: رشته فرمت‌شده
    """
    return f"{key}{separator}{value}"


def format_key_value_list(data: Dict[str, Any], separator: str = ": ") -> str:
    """
    فرمت‌بندی دیکشنری به صورت لیست کلید-مقدار

    پارامترها:
        data: دیکشنری
        separator: جداکننده

    بازگشت: رشته فرمت‌شده
    """
    if not data:
        return ""
    
    result = []
    for key, value in data.items():
        if value is not None:
            result.append(format_key_value(key, value, separator))
    
    return "\n".join(result)


# ============================================================
# اعتبارسنجی و تبدیل
# ============================================================

def safe_int(value: Any, default: int = 0) -> int:
    """
    تبدیل ایمن به عدد صحیح

    پارامترها:
        value: مقدار
        default: مقدار پیش‌فرض در صورت خطا

    بازگشت: عدد صحیح
    """
    try:
        if isinstance(value, str):
            cleaned = re.sub(r'[^\d-]', '', value)
            return int(cleaned) if cleaned else default
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    تبدیل ایمن به عدد اعشاری

    پارامترها:
        value: مقدار
        default: مقدار پیش‌فرض در صورت خطا

    بازگشت: عدد اعشاری
    """
    try:
        if isinstance(value, str):
            cleaned = re.sub(r'[^\d.-]', '', value)
            return float(cleaned) if cleaned else default
        return float(value)
    except (ValueError, TypeError):
        return default


# ============================================================
# توابع کمکی تاریخ و خطا (اضافه شده)
# ============================================================

def get_today_str() -> str:
    """دریافت تاریخ امروز به فرمت YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")


def get_yesterday_str() -> str:
    """دریافت تاریخ دیروز به فرمت YYYY-MM-DD"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def get_date_range(days: int = 30) -> tuple:
    """
    دریافت بازه زمانی از امروز تا days روز قبل.
    
    پارامترها:
        days: تعداد روزهای گذشته
    
    بازگشت: (start_date, end_date) به فرمت YYYY-MM-DD
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return start_date, end_date


def get_error_type_icon(error_type: str) -> str:
    """دریافت آیکون مناسب برای نوع خطا"""
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


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # اعداد
    'format_number',
    'format_percent',
    'format_price',
    'format_currency',
    'format_boolean',
    'format_yes_no',
    'truncate_number',
    'human_readable_size',
    
    # تاریخ و زمان
    'format_datetime',
    'format_date',
    'format_time',
    'format_duration',
    'human_readable_time',
    
    # اختصاصی
    'format_phone',
    'format_national_code',
    'format_tracking_code',
    'format_order_status',
    
    # لیست‌ها
    'format_ordered_list',
    'format_bullet_list',
    'format_key_value',
    'format_key_value_list',
    
    # اعتبارسنجی
    'safe_int',
    'safe_float',
    
    # تاریخ و خطا (اضافه شده)
    'get_today_str',
    'get_yesterday_str',
    'get_date_range',
    'get_error_type_icon',
]