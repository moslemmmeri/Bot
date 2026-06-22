# database/db_buttons.py
# مدیریت دکمه‌ها - شامل: افزودن، دریافت، به‌روزرسانی و حذف دکمه‌ها و زیرمنوها
# پشتیبانی از قیمت متغیر، ستون‌ها، sort_order و فیلدهای جدید

from logger_config import logger
from .db_connection import get_db_connection
from datetime import datetime


def add_button(
    category_id,
    name,
    icon="",
    callback_data=None,
    parent_button_id=None,
    has_submenu=0,
    has_payment=0,
    price_amount=50000,
    price_label="هزینه خدمات",
    price_type="fixed",
    min_price=None,
    max_price=None,
    sort_order=0,
    columns=None
):
    """
    افزودن دکمه جدید به دیتابیس.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
        name: نام دکمه
        icon: آیکون دکمه
        callback_data: داده‌های کالبک (در صورت عدم ارائه، به‌صورت خودکار تولید می‌شود)
        parent_button_id: شناسه دکمه والد (برای زیرمنوها)
        has_submenu: آیا دکمه زیرمنو دارد (0 یا 1)
        has_payment: آیا دکمه نیاز به پرداخت دارد (0 یا 1)
        price_amount: مبلغ پرداخت
        price_label: برچسب مبلغ
        price_type: نوع قیمت ('fixed' یا 'variable')
        min_price: حداقل مبلغ (برای قیمت متغیر)
        max_price: حداکثر مبلغ (برای قیمت متغیر)
        sort_order: ترتیب نمایش
        columns: تعداد ستون‌های اختصاصی برای این دکمه
    
    بازگشت: شناسه دکمه ایجادشده
    """
    if callback_data is None:
        callback_data = f"btn_{category_id}_{int(datetime.now().timestamp())}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO buttons (
                category_id, parent_button_id, name, icon, callback_data, 
                has_submenu, has_payment, price_amount, price_label, price_type,
                min_price, max_price, sort_order, columns
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                category_id, parent_button_id, name, icon, callback_data,
                has_submenu, has_payment, price_amount, price_label, price_type,
                min_price, max_price, sort_order, columns
            )
        )
        conn.commit()
        button_id = cursor.lastrowid
        logger.info(f"✅ دکمه جدید با id={button_id} ایجاد شد: {name}")
        return button_id


def get_buttons_by_location(location):
    """
    دریافت دکمه‌های یک مکان خاص (منوی اصلی، بیشتر، دیگر خدمات).
    
    پارامترها:
        location: نام بخش (main, more, other)
    
    بازگشت: لیست دیکشنری‌های دکمه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.* FROM buttons b
            JOIN categories c ON b.category_id = c.id
            WHERE c.location = ? AND b.is_active = 1 
            AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
            ORDER BY b.sort_order, b.id
        ''', (location,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_buttons_by_category(category_id):
    """
    دریافت دکمه‌های یک دسته‌بندی خاص (بدون زیرمنوها).
    
    پارامترها:
        category_id: شناسه دسته‌بندی
    
    بازگشت: لیست دیکشنری‌های دکمه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM buttons WHERE category_id = ? AND is_active = 1 AND (parent_button_id IS NULL OR parent_button_id = 0) ORDER BY sort_order, id",
            (category_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_buttons_by_category_for_admin(category_id):
    """
    دریافت دکمه‌های یک دسته‌بندی برای پنل مدیریت (با آیکون نمایشی).
    
    پارامترها:
        category_id: شناسه دسته‌بندی
    
    بازگشت: لیست دیکشنری‌های دکمه‌ها با فیلد display_icon
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.*, 
                   CASE 
                       WHEN b.has_submenu = 1 THEN '📂' 
                       ELSE '📄' 
                   END as display_icon
            FROM buttons b
            WHERE b.category_id = ? 
            AND b.is_active = 1 
            AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
            ORDER BY b.sort_order, b.id
        ''', (category_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_buttons_by_parent(parent_button_id):
    """
    دریافت زیرمنوهای یک دکمه (دکمه‌هایی که parent_button_id برابر با مقدار داده‌شده دارند).
    
    پارامترها:
        parent_button_id: شناسه دکمه والد
    
    بازگشت: لیست دیکشنری‌های دکمه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM buttons WHERE parent_button_id = ? AND is_active = 1 ORDER BY sort_order, id",
            (parent_button_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_all_buttons():
    """
    دریافت تمام دکمه‌های فعال (سطح اول) به همراه نام دسته‌بندی و مکان.
    
    بازگشت: لیست دیکشنری‌های دکمه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.*, c.name as category_name, c.location 
            FROM buttons b 
            JOIN categories c ON b.category_id = c.id 
            WHERE c.is_active = 1 AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
            ORDER BY c.name, b.sort_order, b.id
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_all_submenus(button_id):
    """
    دریافت لیست تمام زیرمنوهای یک دکمه (فقط نام و شناسه).
    
    پارامترها:
        button_id: شناسه دکمه والد
    
    بازگشت: لیست دیکشنری‌های زیرمنوها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name FROM buttons WHERE parent_button_id = ? AND is_active = 1 ORDER BY sort_order, id",
            (button_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_button_by_callback(callback_data):
    """
    دریافت یک دکمه بر اساس callback_data.
    
    پارامترها:
        callback_data: داده‌های کالبک دکمه
    
    بازگشت: دیکشنری اطلاعات دکمه یا None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM buttons WHERE callback_data = ? AND is_active = 1", (callback_data,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_button_by_id(button_id):
    """
    دریافت یک دکمه بر اساس شناسه.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: دیکشنری اطلاعات دکمه یا None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM buttons WHERE id = ?", (button_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_button(
    button_id,
    name=None,
    icon=None,
    callback_data=None,
    parent_button_id=None,
    has_submenu=None,
    has_payment=None,
    price_amount=None,
    price_label=None,
    price_type=None,
    min_price=None,
    max_price=None,
    sort_order=None,
    is_active=None,
    columns=None,
    category_id=None
):
    """
    به‌روزرسانی اطلاعات یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
        سایر پارامترها: مقادیر جدید (اختیاری)
    
    بازگشت: True در صورت موفقیت
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        updates = []
        values = []
        
        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if icon is not None:
            updates.append("icon = ?")
            values.append(icon)
        if callback_data is not None:
            updates.append("callback_data = ?")
            values.append(callback_data)
        if parent_button_id is not None:
            updates.append("parent_button_id = ?")
            values.append(parent_button_id)
        if has_submenu is not None:
            updates.append("has_submenu = ?")
            values.append(has_submenu)
        if has_payment is not None:
            updates.append("has_payment = ?")
            values.append(has_payment)
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
        if sort_order is not None:
            updates.append("sort_order = ?")
            values.append(sort_order)
        if is_active is not None:
            updates.append("is_active = ?")
            values.append(is_active)
        if columns is not None:
            updates.append("columns = ?")
            values.append(columns)
        if category_id is not None:
            updates.append("category_id = ?")
            values.append(category_id)
        
        if updates:
            values.append(button_id)
            cursor.execute(f"UPDATE buttons SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
            logger.info(f"✅ دکمه {button_id} به‌روزرسانی شد.")
            return True
        return False


def delete_button(button_id):
    """
    حذف یک دکمه و تمام زیرمنوهای آن (به‌دلیل ON DELETE CASCADE).
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: True در صورت موفقیت، False در صورت عدم وجود
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category_id FROM buttons WHERE id = ?", (button_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        category_id = row["category_id"]
        cursor.execute("DELETE FROM buttons WHERE id = ?", (button_id,))
        
        # بررسی اینکه آیا دسته‌بندی هنوز دکمه‌ای دارد
        cursor.execute("SELECT COUNT(*) as count FROM buttons WHERE category_id = ? AND is_active = 1", (category_id,))
        count_row = cursor.fetchone()
        if count_row and count_row["count"] == 0:
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        
        conn.commit()
        logger.info(f"🗑️ دکمه {button_id} حذف شد.")
        return True


def delete_duplicate_submenus(button_id):
    """
    حذف زیرمنوهای تکراری که نامشان با نام دکمه والد یکسان است.
    
    پارامترها:
        button_id: شناسه دکمه والد
    
    بازگشت: تعداد زیرمنوهای حذف‌شده
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM buttons WHERE id = ?", (button_id,))
        row = cursor.fetchone()
        if not row:
            return 0
        
        main_name = row["name"]
        cursor.execute(
            "DELETE FROM buttons WHERE parent_button_id = ? AND name = ? AND id != ?",
            (button_id, main_name, button_id)
        )
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            logger.info(f"🗑️ {deleted_count} زیرمنوی تکراری برای دکمه {button_id} حذف شد.")
        return deleted_count


def get_button_columns(button_id):
    """
    دریافت تعداد ستون‌های اختصاصی یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: تعداد ستون‌ها یا None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT columns FROM buttons WHERE id = ?", (button_id,))
        row = cursor.fetchone()
        if row and row['columns'] is not None:
            return int(row['columns'])
        return None


def get_button_price_info(button_id):
    """
    دریافت اطلاعات قیمت یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: دیکشنری اطلاعات قیمت
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


def get_buttons_with_price_type(price_type='variable'):
    """
    دریافت دکمه‌ها بر اساس نوع قیمت.
    
    پارامترها:
        price_type: نوع قیمت ('fixed' یا 'variable')
    
    بازگشت: لیست دیکشنری‌های دکمه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM buttons WHERE price_type = ? AND is_active = 1 ORDER BY sort_order, id",
            (price_type,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_parent_buttons(category_id=None):
    """
    دریافت دکمه‌های والد (بدون parent) در یک دسته‌بندی یا همه.
    
    پارامترها:
        category_id: (اختیاری) شناسه دسته‌بندی
    
    بازگشت: لیست دیکشنری‌های دکمه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if category_id:
            cursor.execute("""
                SELECT * FROM buttons 
                WHERE category_id = ? AND (parent_button_id IS NULL OR parent_button_id = 0)
                AND is_active = 1
                ORDER BY sort_order, id
            """, (category_id,))
        else:
            cursor.execute("""
                SELECT * FROM buttons 
                WHERE (parent_button_id IS NULL OR parent_button_id = 0)
                AND is_active = 1
                ORDER BY sort_order, id
            """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def count_buttons_by_category(category_id):
    """
    تعداد دکمه‌های یک دسته‌بندی.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
    
    بازگشت: تعداد دکمه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM buttons 
            WHERE category_id = ? AND is_active = 1
        """, (category_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0


def count_submenus(button_id):
    """
    تعداد زیرمنوهای یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه والد
    
    بازگشت: تعداد زیرمنوها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM buttons 
            WHERE parent_button_id = ? AND is_active = 1
        """, (button_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0


def get_button_max_sort_order(category_id, parent_id=None):
    """
    دریافت حداکثر sort_order در یک دسته‌بندی (با والد اختیاری).
    
    پارامترها:
        category_id: شناسه دسته‌بندی
        parent_id: شناسه والد (اختیاری)
    
    بازگشت: حداکثر sort_order یا -1
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if parent_id:
            cursor.execute("""
                SELECT MAX(sort_order) as max_order FROM buttons 
                WHERE category_id = ? AND parent_button_id = ?
            """, (category_id, parent_id))
        else:
            cursor.execute("""
                SELECT MAX(sort_order) as max_order FROM buttons 
                WHERE category_id = ? AND (parent_button_id IS NULL OR parent_button_id = 0)
            """, (category_id,))
        row = cursor.fetchone()
        return row['max_order'] if row and row['max_order'] is not None else -1


def swap_button_sort_order(button_id_1, button_id_2):
    """
    جابجایی sort_order دو دکمه.
    
    پارامترها:
        button_id_1: شناسه دکمه اول
        button_id_2: شناسه دکمه دوم
    
    بازگشت: True در صورت موفقیت
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT sort_order FROM buttons WHERE id = ?", (button_id_1,))
        row1 = cursor.fetchone()
        cursor.execute("SELECT sort_order FROM buttons WHERE id = ?", (button_id_2,))
        row2 = cursor.fetchone()
        
        if not row1 or not row2:
            return False
        
        order1 = row1['sort_order']
        order2 = row2['sort_order']
        
        cursor.execute("UPDATE buttons SET sort_order = ? WHERE id = ?", (order2, button_id_1))
        cursor.execute("UPDATE buttons SET sort_order = ? WHERE id = ?", (order1, button_id_2))
        conn.commit()
        
        logger.info(f"✅ sort_order دکمه‌های {button_id_1} و {button_id_2} جابجا شد.")
        return True


__all__ = [
    'add_button',
    'get_buttons_by_location',
    'get_buttons_by_category',
    'get_buttons_by_category_for_admin',
    'get_buttons_by_parent',
    'get_all_buttons',
    'get_all_submenus',
    'get_button_by_callback',
    'get_button_by_id',
    'update_button',
    'delete_button',
    'delete_duplicate_submenus',
    'get_button_columns',
    'get_button_price_info',
    'get_buttons_with_price_type',
    'get_parent_buttons',
    'count_buttons_by_category',
    'count_submenus',
    'get_button_max_sort_order',
    'swap_button_sort_order',
]