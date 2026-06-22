# database/drivers/__init__.py
# پکیج درایورهای دیتابیس
# شامل درایورهای SQLite، PostgreSQL و MySQL

from .sqlite_driver import (
    SQLiteConnection,
    SQLiteCursor,
    SQLiteDriver,
    get_sqlite_connection,
    get_sqlite_driver,
)

from .postgres_driver import (
    PostgresConnection,
    PostgresCursor,
    PostgreSQLDriver,
    get_postgres_connection,
    get_postgres_driver,
)

from .mysql_driver import (
    MySQLConnection,
    MySQLCursor,
    MySQLDriver,
    get_mysql_connection,
    get_mysql_driver,
)

# ============================================================
# تابع کمکی برای دریافت درایور مناسب بر اساس نوع دیتابیس
# ============================================================

def get_driver(db_type=None):
    """
    دریافت درایور مناسب بر اساس نوع دیتابیس.
    
    پارامترها:
        db_type: نوع دیتابیس ('sqlite', 'postgresql', 'mysql')
                 اگر None باشد، از تنظیمات config استفاده می‌شود.
    
    بازگشت: آبجکت درایور
    """
    if db_type is None:
        from config import config
        db_type = config.DATABASE_TYPE
    
    if db_type == 'sqlite':
        return get_sqlite_driver()
    elif db_type == 'postgresql':
        return get_postgres_driver()
    elif db_type == 'mysql':
        return get_mysql_driver()
    else:
        raise ValueError(f"نوع دیتابیس نامعتبر: {db_type}")


def get_connection(db_type=None):
    """
    دریافت اتصال به دیتابیس بر اساس نوع.
    
    پارامترها:
        db_type: نوع دیتابیس ('sqlite', 'postgresql', 'mysql')
                 اگر None باشد، از تنظیمات config استفاده می‌شود.
    
    بازگشت: اتصال به دیتابیس
    """
    driver = get_driver(db_type)
    return driver.get_connection()


def get_driver_name(db_type=None):
    """
    دریافت نام درایور بر اساس نوع دیتابیس.
    
    پارامترها:
        db_type: نوع دیتابیس ('sqlite', 'postgresql', 'mysql')
                 اگر None باشد، از تنظیمات config استفاده می‌شود.
    
    بازگشت: نام درایور
    """
    driver = get_driver(db_type)
    return driver.get_driver_name()


def is_driver_available(db_type=None):
    """
    بررسی در دسترس بودن درایور.
    
    پارامترها:
        db_type: نوع دیتابیس ('sqlite', 'postgresql', 'mysql')
                 اگر None باشد، از تنظیمات config استفاده می‌شود.
    
    بازگشت: True اگر درایور در دسترس باشد
    """
    driver = get_driver(db_type)
    return driver.is_available()


def get_connection_string(db_type=None):
    """
    دریافت رشته اتصال به دیتابیس بر اساس نوع.
    
    پارامترها:
        db_type: نوع دیتابیس ('sqlite', 'postgresql', 'mysql')
                 اگر None باشد، از تنظیمات config استفاده می‌شود.
    
    بازگشت: رشته اتصال
    """
    driver = get_driver(db_type)
    return driver.get_connection_string()


def get_placeholder(db_type=None):
    """
    دریافت placeholder برای پارامترهای کوئری.
    
    پارامترها:
        db_type: نوع دیتابیس ('sqlite', 'postgresql', 'mysql')
                 اگر None باشد، از تنظیمات config استفاده می‌شود.
    
    بازگشت: placeholder (مثلاً '?' برای SQLite)
    """
    driver = get_driver(db_type)
    return driver.get_placeholders()


# ============================================================
# صادر کردن همه چیز
# ============================================================

__all__ = [
    # درایور SQLite
    'SQLiteConnection',
    'SQLiteCursor',
    'SQLiteDriver',
    'get_sqlite_connection',
    'get_sqlite_driver',
    
    # درایور PostgreSQL
    'PostgresConnection',
    'PostgresCursor',
    'PostgreSQLDriver',
    'get_postgres_connection',
    'get_postgres_driver',
    
    # درایور MySQL
    'MySQLConnection',
    'MySQLCursor',
    'MySQLDriver',
    'get_mysql_connection',
    'get_mysql_driver',
    
    # توابع کمکی
    'get_driver',
    'get_connection',
    'get_driver_name',
    'is_driver_available',
    'get_connection_string',
    'get_placeholder',
]