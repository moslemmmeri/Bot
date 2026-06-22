# admin_panel/common.py
# توابع کمکی مورد استفاده در بخش‌های مختلف مدیریت

import json
import traceback  # ✅ اضافه شد برای traceback کامل
from database import get_button_by_id
from utils.error_handler import log_general_error  # ✅ اضافه شد


def extract_date_from_order(order):
    """استخراج تاریخ (فقط YYYY-MM-DD) از created_at سفارش"""
    created_at = order.get('created_at', '')
    if created_at and ' ' in created_at:
        return created_at.split(' ')[0]
    return created_at[:10] if len(created_at) >= 10 else created_at


def get_service_name(button_id):
    """دریافت نام سرویس با در نظر گرفتن زیرمنو (اگر والد دارد)"""
    try:
        if not button_id:
            return "نامشخص"
        btn = get_button_by_id(button_id)
        if not btn:
            return "نامشخص"
        if btn.get('parent_button_id'):
            parent = get_button_by_id(btn['parent_button_id'])
            if parent:
                return f"{parent['name']} > {btn['name']}"
        return btn['name']
    except Exception as e:
        log_general_error(
            f"Error in get_service_name for button_id {button_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return "نامشخص"


def get_fullname_from_order(order):
    """استخراج نام کامل کاربر از order_data یا پاسخ‌ها"""
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
        # اگر در order_data نبود، از اولین پاسخ (معمولاً نام) استفاده می‌کنیم
        answers = order_data.get('answers', {})
        if answers:
            first_answer = next(iter(answers.values()), 'کاربر ناشناس')
            return first_answer
        return 'کاربر ناشناس'
    except Exception as e:
        log_general_error(
            f"Error in get_fullname_from_order: {str(e)}",
            traceback=traceback.format_exc()
        )
        return 'کاربر ناشناس'


def get_order_status_persian(status):
    """دریافت متن فارسی وضعیت سفارش"""
    status_map = {
        'pending': '⏳ در انتظار پرداخت',
        'paid': '✅ پرداخت شده',
        'completed': '✅ تکمیل شده',
        'cancelled': '❌ لغو شده',
        'failed': '❌ ناموفق',
        'refunded': '🔄 بازگشت وجه'
    }
    return status_map.get(status, status)


def get_button_name(button_id):
    """دریافت نام دکمه با شناسه"""
    try:
        btn = get_button_by_id(button_id)
        return btn['name'] if btn else f"دکمه {button_id}"
    except Exception as e:
        log_general_error(
            f"Error in get_button_name for button_id {button_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return f"دکمه {button_id}"


def format_price(amount):
    """فرمت‌بندی مبلغ با کاما"""
    try:
        if amount is None:
            return "۰"
        return f"{int(amount):,}"
    except (ValueError, TypeError) as e:
        log_general_error(
            f"Error in format_price for amount {amount}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return str(amount) if amount is not None else "۰"


def get_user_display_name(user):
    """دریافت نام قابل نمایش کاربر"""
    try:
        if not user:
            return "کاربر ناشناس"
        
        first_name = user.get('first_name')
        last_name = user.get('last_name')
        username = user.get('username')
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif username:
            return f"@{username}"
        return f"کاربر {user.get('user_id', 'نامشخص')}"
    except Exception as e:
        log_general_error(
            f"Error in get_user_display_name: {str(e)}",
            traceback=traceback.format_exc()
        )
        return "کاربر ناشناس"


def is_valid_uuid(value):
    """بررسی معتبر بودن UUID"""
    import re
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, str(value).lower()))


__all__ = [
    'extract_date_from_order',
    'get_service_name',
    'get_fullname_from_order',
    'get_order_status_persian',
    'get_button_name',
    'format_price',
    'get_user_display_name',
    'is_valid_uuid',
]