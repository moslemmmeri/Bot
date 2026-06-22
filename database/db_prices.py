# database/db_prices.py
# مدیریت قیمت‌های متغیر سرویس‌ها
# شامل: دریافت، ذخیره و اعتبارسنجی قیمت‌های متغیر برای دکمه‌ها

from logger_config import logger
from .db_connection import get_db_connection


def get_button_price_info(button_id):
    """
    دریافت اطلاعات قیمت یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: دیکشنری شامل price_type, price_amount, price_label, min_price, max_price
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT price_amount, price_label, price_type, min_price, max_price 
            FROM buttons 
            WHERE id = ?
        """, (button_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            'price_amount': 50000,
            'price_label': 'هزینه خدمات',
            'price_type': 'fixed',
            'min_price': None,
            'max_price': None
        }


def update_button_price(button_id, price_amount=None, price_label=None, price_type=None, min_price=None, max_price=None):
    """
    به‌روزرسانی اطلاعات قیمت یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
        price_amount: مبلغ ثابت (برای نوع fixed)
        price_label: برچسب مبلغ
        price_type: نوع قیمت ('fixed' یا 'variable')
        min_price: حداقل مبلغ (برای نوع variable)
        max_price: حداکثر مبلغ (برای نوع variable)
    
    بازگشت: True در صورت موفقیت
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        updates = []
        values = []
        
        if price_amount is not None:
            updates.append("price_amount = ?")
            values.append(price_amount)
        if price_label is not None:
            updates.append("price_label = ?")
            values.append(price_label)
        if price_type is not None:
            updates.append("price_type = ?")
            values.append(price_type)
        if min_price is not None:
            updates.append("min_price = ?")
            values.append(min_price)
        if max_price is not None:
            updates.append("max_price = ?")
            values.append(max_price)
        
        if updates:
            values.append(button_id)
            cursor.execute(f"UPDATE buttons SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
            logger.info(f"✅ اطلاعات قیمت دکمه {button_id} به‌روزرسانی شد.")
            return True
        return False


def validate_price_input(price_input, button_id):
    """
    اعتبارسنجی مبلغ واردشده توسط کاربر برای دکمه با قیمت متغیر.
    
    پارامترها:
        price_input: مبلغ واردشده توسط کاربر (رشته یا عدد)
        button_id: شناسه دکمه
    
    بازگشت: (is_valid, price_amount, error_message)
        is_valid: True اگر معتبر باشد
        price_amount: مبلغ معتبر (به ریال)
        error_message: پیام خطا در صورت نامعتبر بودن
    """
    try:
        # تبدیل به عدد
        if isinstance(price_input, str):
            price = int(price_input.replace(',', '').replace(' ', ''))
        else:
            price = int(price_input)
        
        if price <= 0:
            return False, 0, "❌ مبلغ باید بزرگتر از صفر باشد."
        
        # دریافت اطلاعات قیمت دکمه
        price_info = get_button_price_info(button_id)
        price_type = price_info.get('price_type', 'fixed')
        
        # اگر قیمت ثابت است، مقدار باید دقیقاً برابر با price_amount باشد
        if price_type == 'fixed':
            fixed_amount = price_info.get('price_amount', 0)
            if price != fixed_amount:
                return False, 0, f"❌ مبلغ باید دقیقاً {fixed_amount:,} ریال باشد."
            return True, price, None
        
        # اگر قیمت متغیر است، بین min_price و max_price باشد
        if price_type == 'variable':
            min_price = price_info.get('min_price')
            max_price = price_info.get('max_price')
            
            if min_price is not None and price < min_price:
                return False, 0, f"❌ مبلغ نمی‌تواند کمتر از {min_price:,} ریال باشد."
            if max_price is not None and price > max_price:
                return False, 0, f"❌ مبلغ نمی‌تواند بیشتر از {max_price:,} ریال باشد."
            
            return True, price, None
        
        # نوع نامعتبر
        return False, 0, "❌ نوع قیمت نامعتبر است."
        
    except ValueError:
        return False, 0, "❌ لطفاً یک عدد معتبر وارد کنید."


def get_price_display(button_id):
    """
    دریافت متن قابل نمایش برای قیمت یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: رشته نمایشی قیمت
    """
    price_info = get_button_price_info(button_id)
    price_type = price_info.get('price_type', 'fixed')
    
    if price_type == 'fixed':
        amount = price_info.get('price_amount', 0)
        label = price_info.get('price_label', 'هزینه خدمات')
        return f"{label}: {amount:,} ریال"
    
    if price_type == 'variable':
        min_price = price_info.get('min_price')
        max_price = price_info.get('max_price')
        label = price_info.get('price_label', 'هزینه خدمات')
        
        if min_price is not None and max_price is not None:
            return f"{label}: {min_price:,} تا {max_price:,} ریال (متغیر)"
        elif min_price is not None:
            return f"{label}: حداقل {min_price:,} ریال (متغیر)"
        elif max_price is not None:
            return f"{label}: حداکثر {max_price:,} ریال (متغیر)"
        else:
            return f"{label}: متغیر (بدون محدودیت)"
    
    return "قیمت نامشخص"


def get_price_validation_hint(button_id):
    """
    دریافت پیام راهنما برای ورود مبلغ در سرویس‌های با قیمت متغیر.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: رشته راهنما
    """
    price_info = get_button_price_info(button_id)
    price_type = price_info.get('price_type', 'fixed')
    
    if price_type == 'fixed':
        return f"مبلغ ثابت: {price_info.get('price_amount', 0):,} ریال"
    
    if price_type == 'variable':
        min_price = price_info.get('min_price')
        max_price = price_info.get('max_price')
        
        if min_price is not None and max_price is not None:
            return f"مبلغ را بین {min_price:,} تا {max_price:,} ریال وارد کنید"
        elif min_price is not None:
            return f"حداقل مبلغ: {min_price:,} ریال"
        elif max_price is not None:
            return f"حداکثر مبلغ: {max_price:,} ریال"
        else:
            return "مبلغ مورد نظر را به ریال وارد کنید"
    
    return "مبلغ را وارد کنید"


def get_buttons_by_price_type(price_type='variable'):
    """
    دریافت دکمه‌ها بر اساس نوع قیمت.
    
    پارامترها:
        price_type: نوع قیمت ('fixed' یا 'variable')
    
    بازگشت: لیست دکمه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM buttons 
            WHERE price_type = ? AND is_active = 1
            ORDER BY sort_order, id
        """, (price_type,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_variable_price_buttons_with_stats():
    """
    دریافت دکمه‌های با قیمت متغیر به همراه آمار سفارشات.
    
    بازگشت: لیست دکمه‌ها با آمار
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                b.*,
                COUNT(o.id) as orders_count,
                COALESCE(AVG(o.payment_amount), 0) as avg_paid_amount,
                COALESCE(MIN(o.payment_amount), 0) as min_paid_amount,
                COALESCE(MAX(o.payment_amount), 0) as max_paid_amount
            FROM buttons b
            LEFT JOIN dynamic_orders o ON b.id = o.button_id AND o.status IN ('paid', 'completed')
            WHERE b.price_type = 'variable' AND b.is_active = 1
            GROUP BY b.id
            ORDER BY b.sort_order, b.id
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_price_statistics(button_id):
    """
    دریافت آمار قیمت‌های پرداخت‌شده برای یک دکمه با قیمت متغیر.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: دیکشنری شامل آمار
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_payments,
                COALESCE(AVG(payment_amount), 0) as avg_amount,
                COALESCE(MIN(payment_amount), 0) as min_amount,
                COALESCE(MAX(payment_amount), 0) as max_amount,
                COALESCE(SUM(payment_amount), 0) as total_amount
            FROM dynamic_orders 
            WHERE button_id = ? AND status IN ('paid', 'completed')
        """, (button_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            'total_payments': 0,
            'avg_amount': 0,
            'min_amount': 0,
            'max_amount': 0,
            'total_amount': 0
        }


def update_price_range(button_id, min_price=None, max_price=None):
    """
    به‌روزرسانی محدوده قیمت متغیر یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
        min_price: حداقل مبلغ جدید (یا None برای حذف)
        max_price: حداکثر مبلغ جدید (یا None برای حذف)
    
    بازگشت: True در صورت موفقیت
    """
    if min_price is not None and min_price < 0:
        logger.warning(f"حداقل مبلغ نامعتبر: {min_price}")
        return False
    
    if max_price is not None and max_price < 0:
        logger.warning(f"حداکثر مبلغ نامعتبر: {max_price}")
        return False
    
    if min_price is not None and max_price is not None and min_price > max_price:
        logger.warning(f"حداقل ({min_price}) نباید از حداکثر ({max_price}) بیشتر باشد.")
        return False
    
    return update_button_price(button_id, min_price=min_price, max_price=max_price)


def convert_to_variable_price(button_id, min_price=None, max_price=None):
    """
    تبدیل یک دکمه به قیمت متغیر.
    
    پارامترها:
        button_id: شناسه دکمه
        min_price: حداقل مبلغ (اختیاری)
        max_price: حداکثر مبلغ (اختیاری)
    
    بازگشت: True در صورت موفقیت
    """
    return update_button_price(
        button_id,
        price_type='variable',
        min_price=min_price,
        max_price=max_price
    )


def convert_to_fixed_price(button_id, price_amount=None):
    """
    تبدیل یک دکمه به قیمت ثابت.
    
    پارامترها:
        button_id: شناسه دکمه
        price_amount: مبلغ ثابت (اگر None باشد، مقدار فعلی نگهداری می‌شود)
    
    بازگشت: True در صورت موفقیت
    """
    if price_amount is None:
        # دریافت مبلغ فعلی
        info = get_button_price_info(button_id)
        price_amount = info.get('price_amount', 50000)
    
    return update_button_price(
        button_id,
        price_type='fixed',
        price_amount=price_amount,
        min_price=None,
        max_price=None
    )


__all__ = [
    'get_button_price_info',
    'update_button_price',
    'validate_price_input',
    'get_price_display',
    'get_price_validation_hint',
    'get_buttons_by_price_type',
    'get_variable_price_buttons_with_stats',
    'get_price_statistics',
    'update_price_range',
    'convert_to_variable_price',
    'convert_to_fixed_price',
]