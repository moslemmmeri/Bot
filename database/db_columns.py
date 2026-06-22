# database/db_columns.py
# مدیریت ستون‌های منو - توابع مربوط به تعداد ستون‌های نمایش دکمه‌ها در منوها
# شامل: دریافت تنظیمات پیش‌فرض، ستون‌های دسته‌بندی، ستون‌های دکمه و محاسبه ستون‌های مؤثر

from logger_config import logger
from .db_connection import get_db_connection


def get_default_menu_columns():
    """
    دریافت تعداد ستون‌های پیش‌فرض از جدول settings.
    
    بازگشت: تعداد ستون‌های پیش‌فرض (عدد صحیح بین ۱ تا ۸)، در صورت عدم وجود مقدار ۲ برمی‌گرداند.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'default_menu_columns'")
        row = cursor.fetchone()
        if row:
            try:
                value = int(row['value'])
                if 1 <= value <= 8:
                    return value
                else:
                    logger.warning(f"مقدار default_menu_columns نامعتبر: {value}، استفاده از پیش‌فرض ۲")
                    return 2
            except ValueError:
                logger.warning(f"مقدار default_menu_columns غیرعددی: {row['value']}، استفاده از پیش‌فرض ۲")
                return 2
        return 2


def get_category_columns(category_id):
    """
    دریافت تعداد ستون‌های یک دسته‌بندی.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
    
    بازگشت: تعداد ستون‌ها (عدد صحیح) یا None در صورت عدم وجود یا نامعتبر بودن
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT columns FROM categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        if row and row['columns'] is not None:
            try:
                value = int(row['columns'])
                if 1 <= value <= 8:
                    return value
                else:
                    logger.warning(f"مقدار columns برای دسته‌بندی {category_id} نامعتبر: {value}")
                    return None
            except ValueError:
                logger.warning(f"مقدار columns برای دسته‌بندی {category_id} غیرعددی: {row['columns']}")
                return None
        return None


def get_button_columns(button_id):
    """
    دریافت تعداد ستون‌های اختصاصی یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: تعداد ستون‌ها (عدد صحیح) یا None در صورت عدم وجود یا نامعتبر بودن
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT columns FROM buttons WHERE id = ?", (button_id,))
        row = cursor.fetchone()
        if row and row['columns'] is not None:
            try:
                value = int(row['columns'])
                if 1 <= value <= 8:
                    return value
                else:
                    logger.warning(f"مقدار columns برای دکمه {button_id} نامعتبر: {value}")
                    return None
            except ValueError:
                logger.warning(f"مقدار columns برای دکمه {button_id} غیرعددی: {row['columns']}")
                return None
        return None


def get_effective_columns(button_id=None, category_id=None):
    """
    دریافت تعداد ستون‌های مؤثر بر اساس اولویت:
    1. ستون اختصاصی دکمه (اگر وجود داشته باشد)
    2. ستون دسته‌بندی (اگر وجود داشته باشد)
    3. مقدار پیش‌فرض عمومی (default_menu_columns)
    
    پارامترها:
        button_id: (اختیاری) شناسه دکمه
        category_id: (اختیاری) شناسه دسته‌بندی
    
    بازگشت: تعداد ستون‌های مؤثر (عدد صحیح بین ۱ تا ۸)
    """
    # اولویت ۱: دکمه
    if button_id:
        btn_cols = get_button_columns(button_id)
        if btn_cols is not None:
            return btn_cols
    
    # اولویت ۲: دسته‌بندی
    if category_id:
        cat_cols = get_category_columns(category_id)
        if cat_cols is not None:
            return cat_cols
    
    # اولویت ۳: پیش‌فرض عمومی
    return get_default_menu_columns()


def set_default_menu_columns(columns):
    """
    تنظیم تعداد ستون‌های پیش‌فرض منو.
    
    پارامترها:
        columns: تعداد ستون‌ها (عدد صحیح بین ۱ تا ۸)
    
    بازگشت: True در صورت موفقیت، False در غیر این صورت
    """
    if not isinstance(columns, int) or columns < 1 or columns > 8:
        logger.error(f"تعداد ستون‌های پیش‌فرض نامعتبر: {columns} (باید بین ۱ تا ۸ باشد)")
        return False
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value, description, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            ("default_menu_columns", str(columns), "تعداد ستون‌های پیش‌فرض منو (۱ تا ۸)")
        )
        conn.commit()
        logger.info(f"✅ تعداد ستون‌های پیش‌فرض به {columns} تنظیم شد.")
        return True


def set_category_columns(category_id, columns):
    """
    تنظیم تعداد ستون‌های یک دسته‌بندی.
    
    پارامترها:
        category_id: شناسه دسته‌بندی
        columns: تعداد ستون‌ها (عدد صحیح بین ۱ تا ۸) یا None برای حذف تنظیمات اختصاصی
    
    بازگشت: True در صورت موفقیت، False در غیر این صورت
    """
    if columns is not None:
        if not isinstance(columns, int) or columns < 1 or columns > 8:
            logger.error(f"تعداد ستون‌های دسته‌بندی نامعتبر: {columns} (باید بین ۱ تا ۸ باشد)")
            return False
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE categories SET columns = ? WHERE id = ?", (columns, category_id))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"✅ تعداد ستون‌های دسته‌بندی {category_id} به {columns} تغییر یافت.")
            return True
        else:
            logger.warning(f"⚠️ دسته‌بندی {category_id} یافت نشد.")
            return False


def set_button_columns(button_id, columns):
    """
    تنظیم تعداد ستون‌های اختصاصی یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
        columns: تعداد ستون‌ها (عدد صحیح بین ۱ تا ۸) یا None برای حذف تنظیمات اختصاصی
    
    بازگشت: True در صورت موفقیت، False در غیر این صورت
    """
    if columns is not None:
        if not isinstance(columns, int) or columns < 1 or columns > 8:
            logger.error(f"تعداد ستون‌های دکمه نامعتبر: {columns} (باید بین ۱ تا ۸ باشد)")
            return False
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE buttons SET columns = ? WHERE id = ?", (columns, button_id))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"✅ تعداد ستون‌های دکمه {button_id} به {columns} تغییر یافت.")
            return True
        else:
            logger.warning(f"⚠️ دکمه {button_id} یافت نشد.")
            return False


def get_columns_info(button_id=None, category_id=None):
    """
    دریافت اطلاعات کامل درباره ستون‌های یک دکمه یا دسته‌بندی برای نمایش در پنل مدیریت.
    
    پارامترها:
        button_id: (اختیاری) شناسه دکمه
        category_id: (اختیاری) شناسه دسته‌بندی
    
    بازگشت: دیکشنری شامل:
        - button_columns: ستون اختصاصی دکمه (یا None)
        - category_columns: ستون دسته‌بندی (یا None)
        - default_columns: ستون پیش‌فرض عمومی
        - effective_columns: ستون مؤثر نهایی
    """
    result = {
        'button_columns': None,
        'category_columns': None,
        'default_columns': get_default_menu_columns(),
        'effective_columns': 2
    }
    
    if button_id:
        result['button_columns'] = get_button_columns(button_id)
    
    if category_id:
        result['category_columns'] = get_category_columns(category_id)
    
    result['effective_columns'] = get_effective_columns(button_id, category_id)
    
    return result


def get_all_columns_status():
    """
    دریافت وضعیت کامل ستون‌های تمام دسته‌بندی‌ها و دکمه‌ها.
    برای نمایش در داشبورد مدیریت پیشرفته ستون‌ها.
    
    بازگشت: دیکشنری شامل اطلاعات کامل
    """
    from .db_categories import get_all_categories_admin
    from .db_buttons import get_all_buttons
    
    categories = get_all_categories_admin()
    buttons = get_all_buttons()
    
    category_status = []
    for cat in categories:
        category_status.append({
            'id': cat['id'],
            'name': cat['name'],
            'location': cat.get('location', 'main'),
            'custom_columns': cat.get('columns'),
            'effective_columns': get_effective_columns(category_id=cat['id']),
            'has_custom': cat.get('columns') is not None
        })
    
    button_status = []
    for btn in buttons:
        # فقط دکمه‌هایی که تنظیمات اختصاصی دارند
        if btn.get('columns') is not None:
            button_status.append({
                'id': btn['id'],
                'name': btn['name'],
                'category_id': btn['category_id'],
                'custom_columns': btn['columns'],
                'effective_columns': get_effective_columns(button_id=btn['id'], category_id=btn['category_id'])
            })
    
    return {
        'default_columns': get_default_menu_columns(),
        'categories': category_status,
        'buttons_with_custom': button_status,
        'total_categories': len(category_status),
        'total_buttons_with_custom': len(button_status)
    }


def reset_all_columns_settings():
    """
    بازنشانی همه تنظیمات ستون‌ها به حالت پیش‌فرض:
    1. تنظیم default_menu_columns = 2
    2. حذف تنظیمات اختصاصی همه دسته‌بندی‌ها
    3. حذف تنظیمات اختصاصی همه دکمه‌ها
    
    بازگشت: دیکشنری شامل تعداد آیتم‌های بازنشانی‌شده
    """
    from .db_categories import get_all_categories_admin
    from .db_buttons import get_all_buttons
    
    result = {
        'default_reset': False,
        'categories_reset': 0,
        'buttons_reset': 0
    }
    
    # ۱. بازنشانی پیش‌فرض
    result['default_reset'] = set_default_menu_columns(2)
    
    # ۲. بازنشانی دسته‌بندی‌ها
    categories = get_all_categories_admin()
    for cat in categories:
        if cat.get('columns') is not None:
            if set_category_columns(cat['id'], None):
                result['categories_reset'] += 1
    
    # ۳. بازنشانی دکمه‌ها
    buttons = get_all_buttons()
    for btn in buttons:
        if btn.get('columns') is not None:
            if set_button_columns(btn['id'], None):
                result['buttons_reset'] += 1
    
    logger.info(f"🔄 تنظیمات ستون‌ها بازنشانی شدند: {result}")
    return result


__all__ = [
    'get_default_menu_columns',
    'get_category_columns',
    'get_button_columns',
    'get_effective_columns',
    'set_default_menu_columns',
    'set_category_columns',
    'set_button_columns',
    'get_columns_info',
    'get_all_columns_status',
    'reset_all_columns_settings',
]