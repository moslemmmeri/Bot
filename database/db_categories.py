# database/db_categories.py
# مدیریت دسته‌بندی‌ها - شامل: افزودن، دریافت، به‌روزرسانی و حذف دسته‌بندی‌ها
# پشتیبانی از ستون‌های جدید (columns, sort_order, is_active)

from logger_config import logger
from .db_connection import get_db_connection


def add_category(name, icon="📁", location="main", sort_order=0, columns=2):
    """
    افزودن دسته‌بندی جدید به دیتابیس.
    
    پارامترها:
        name: نام دسته‌بندی
        icon: آیکون دسته‌بندی
        location: مکان دسته‌بندی (main, more, other)
        sort_order: ترتیب نمایش
        columns: تعداد ستون‌های پیش‌فرض برای این دسته‌بندی
    
    بازگشت: شناسه دسته‌بندی ایجادشده
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories (name, icon, location, sort_order, columns) VALUES (?, ?, ?, ?, ?)",
            (name, icon, location, sort_order, columns)
        )
        conn.commit()
        category_id = cursor.lastrowid
        logger.info(f"✅ دسته‌بندی جدید با id={category_id} ایجاد شد: {name}")
        return category_id


def get_category_by_location(location):
    """
    دریافت دسته‌بندی بر اساس location.
    
    پارامترها:
        location: نام بخش (main, more, other)
    
    بازگشت: دیکشنری اطلاعات دسته‌بندی یا None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE location = ? AND is_active = 1", (location,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_categories(location=None):
    """
    دریافت لیست تمام دسته‌بندی‌های فعال که حداقل یک دکمه فعال دارند.
    
    پارامترها:
        location: (اختیاری) فیلتر بر اساس مکان
    
    بازگشت: لیست دیکشنری‌های دسته‌بندی‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if location:
            cursor.execute('''
                SELECT c.* FROM categories c
                WHERE c.is_active = 1 AND c.location = ?
                AND EXISTS (
                    SELECT 1 FROM buttons b 
                    WHERE b.category_id = c.id 
                    AND b.is_active = 1 
                    AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
                )
                ORDER BY c.sort_order, c.id
            ''', (location,))
        else:
            cursor.execute('''
                SELECT c.* FROM categories c
                WHERE c.is_active = 1
                AND EXISTS (
                    SELECT 1 FROM buttons b 
                    WHERE b.category_id = c.id 
                    AND b.is_active = 1 
                    AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
                )
                ORDER BY c.sort_order, c.id
            ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_all_categories_admin():
    """
    دریافت لیست تمام دسته‌بندی‌ها برای پنل مدیریت (بدون فیلتر دکمه‌ها).
    
    بازگشت: لیست دیکشنری‌های دسته‌بندی‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order, id
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_categories_with_buttons(location=None):
    """
    دریافت دسته‌بندی‌هایی که حداقل یک دکمه فعال دارند.
    
    پارامترها:
        location: (اختیاری) فیلتر بر اساس مکان
    
    بازگشت: لیست دیکشنری‌های دسته‌بندی‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if location:
            cursor.execute('''
                SELECT DISTINCT c.* FROM categories c
                INNER JOIN buttons b ON b.category_id = c.id
                WHERE c.is_active = 1 
                AND c.location = ?
                AND b.is_active = 1
                AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
                ORDER BY c.sort_order, c.id
            ''', (location,))
        else:
            cursor.execute('''
                SELECT DISTINCT c.* FROM categories c
                INNER JOIN buttons b ON b.category_id = c.id
                WHERE c.is_active = 1 
                AND b.is_active = 1
                AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
                ORDER BY c.sort_order, c.id
            ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_category_by_id(category_id):
    """
    دریافت اطلاعات یک دسته‌بندی بر اساس شناسه.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
    
    بازگشت: دیکشنری اطلاعات دسته‌بندی یا None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_category(category_id, name=None, icon=None, location=None, sort_order=None, is_active=None, columns=None):
    """
    به‌روزرسانی اطلاعات یک دسته‌بندی.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
        name: نام جدید (اختیاری)
        icon: آیکون جدید (اختیاری)
        location: مکان جدید (اختیاری)
        sort_order: ترتیب جدید (اختیاری)
        is_active: وضعیت فعال/غیرفعال (اختیاری)
        columns: تعداد ستون‌های جدید (اختیاری)
    
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
        if location is not None:
            updates.append("location = ?")
            values.append(location)
        if sort_order is not None:
            updates.append("sort_order = ?")
            values.append(sort_order)
        if is_active is not None:
            updates.append("is_active = ?")
            values.append(is_active)
        if columns is not None:
            updates.append("columns = ?")
            values.append(columns)
        
        if updates:
            values.append(category_id)
            cursor.execute(f"UPDATE categories SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
            logger.info(f"✅ دسته‌بندی {category_id} به‌روزرسانی شد.")
            return True
        return False


def delete_category(category_id):
    """
    حذف یک دسته‌بندی و تمام دکمه‌های مرتبط با آن.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
    
    بازگشت: True در صورت موفقیت
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        logger.info(f"🗑️ دسته‌بندی {category_id} حذف شد.")
        return True


def get_category_columns(category_id):
    """
    دریافت تعداد ستون‌های یک دسته‌بندی.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
    
    بازگشت: تعداد ستون‌ها یا None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT columns FROM categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        if row and row['columns'] is not None:
            return int(row['columns'])
        return None


def get_category_location(category_id):
    """
    دریافت مکان یک دسته‌بندی.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
    
    بازگشت: مکان دسته‌بندی یا None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT location FROM categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        return row['location'] if row else None


def get_category_count(location=None):
    """
    دریافت تعداد دسته‌بندی‌ها.
    
    پارامترها:
        location: (اختیاری) فیلتر بر اساس مکان
    
    بازگشت: تعداد دسته‌بندی‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if location:
            cursor.execute("SELECT COUNT(*) as count FROM categories WHERE location = ? AND is_active = 1", (location,))
        else:
            cursor.execute("SELECT COUNT(*) as count FROM categories WHERE is_active = 1")
        row = cursor.fetchone()
        return row['count'] if row else 0


def get_category_with_button_count(category_id):
    """
    دریافت تعداد دکمه‌های فعال یک دسته‌بندی.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
    
    بازگشت: تعداد دکمه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM buttons 
            WHERE category_id = ? AND is_active = 1 
            AND (parent_button_id IS NULL OR parent_button_id = 0)
        """, (category_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0


def get_all_categories_with_stats():
    """
    دریافت تمام دسته‌بندی‌ها به همراه آمار (تعداد دکمه‌ها، تعداد دکمه‌های فعال و ...)
    
    بازگشت: لیست دیکشنری‌های دسته‌بندی‌ها با آمار
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                c.*,
                COUNT(b.id) as total_buttons,
                COUNT(CASE WHEN b.is_active = 1 THEN 1 END) as active_buttons,
                COUNT(CASE WHEN b.has_submenu = 1 THEN 1 END) as submenu_count,
                COUNT(CASE WHEN b.has_payment = 1 THEN 1 END) as payment_count
            FROM categories c
            LEFT JOIN buttons b ON c.id = b.category_id AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
            WHERE c.is_active = 1
            GROUP BY c.id
            ORDER BY c.sort_order, c.id
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_category_locations():
    """
    دریافت لیست مکان‌های موجود در دسته‌بندی‌ها.
    
    بازگشت: لیست مکان‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT location FROM categories WHERE is_active = 1 ORDER BY location")
        rows = cursor.fetchall()
        return [row['location'] for row in rows]


def get_category_by_name(name, location=None):
    """
    دریافت دسته‌بندی بر اساس نام (و مکان اختیاری).
    
    پارامترها:
        name: نام دسته‌بندی
        location: (اختیاری) مکان دسته‌بندی
    
    بازگشت: دیکشنری اطلاعات دسته‌بندی یا None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if location:
            cursor.execute("SELECT * FROM categories WHERE name = ? AND location = ? AND is_active = 1", (name, location))
        else:
            cursor.execute("SELECT * FROM categories WHERE name = ? AND is_active = 1", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_category_columns(category_id, columns):
    """
    به‌روزرسانی تعداد ستون‌های یک دسته‌بندی.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
        columns: تعداد ستون‌ها (۱ تا ۸) یا None برای حذف تنظیمات اختصاصی
    
    بازگشت: True در صورت موفقیت
    """
    if columns is not None and (columns < 1 or columns > 8):
        logger.warning(f"تعداد ستون‌های دسته‌بندی نامعتبر: {columns}")
        return False
    
    return update_category(category_id, columns=columns)


def get_categories_with_effective_columns():
    """
    دریافت تمام دسته‌بندی‌ها با ستون‌های مؤثر.
    
    بازگشت: لیست دیکشنری‌های دسته‌بندی‌ها با فیلد effective_columns
    """
    from .db_columns import get_effective_columns
    
    categories = get_all_categories_admin()
    result = []
    for cat in categories:
        cat_dict = dict(cat)
        cat_dict['effective_columns'] = get_effective_columns(category_id=cat['id'])
        cat_dict['has_custom_columns'] = cat.get('columns') is not None
        result.append(cat_dict)
    
    return result


def ensure_default_categories():
    """
    اطمینان از وجود دسته‌بندی‌های پیش‌فرض در دیتابیس.
    اگر دسته‌بندی‌های اصلی وجود نداشته باشند، ایجاد می‌شوند.
    """
    default_categories = [
        {'name': 'منوی اصلی', 'location': 'main', 'icon': '🏠', 'columns': 2},
        {'name': 'منوی بیشتر', 'location': 'more', 'icon': '➕', 'columns': 2},
        {'name': 'دیگر خدمات', 'location': 'other', 'icon': '🔧', 'columns': 2},
    ]
    
    for cat_data in default_categories:
        existing = get_category_by_location(cat_data['location'])
        if not existing:
            add_category(
                name=cat_data['name'],
                icon=cat_data['icon'],
                location=cat_data['location'],
                columns=cat_data['columns']
            )
            logger.info(f"✅ دسته‌بندی پیش‌فرض ایجاد شد: {cat_data['name']}")


__all__ = [
    'add_category',
    'get_category_by_location',
    'get_all_categories',
    'get_all_categories_admin',
    'get_categories_with_buttons',
    'get_category_by_id',
    'update_category',
    'delete_category',
    'get_category_columns',
    'get_category_location',
    'get_category_count',
    'get_category_with_button_count',
    'get_all_categories_with_stats',
    'get_category_locations',
    'get_category_by_name',
    'update_category_columns',
    'get_categories_with_effective_columns',
    'ensure_default_categories',
]