# database/db_factory.py
# کارخانه‌ی تولید درایور دیتابیس بر اساس نوع دیتابیس انتخابی

from typing import Optional
from logger_config import logger
from config import config
from .interfaces import DatabaseDriver, DatabaseConnection
from .drivers.sqlite_driver import SQLiteDriver, SQLiteConnection
from .drivers.postgres_driver import PostgreSQLDriver, PostgresConnection
from .drivers.mysql_driver import MySQLDriver, MySQLConnection


class DatabaseFactory:
    """
    کارخانه‌ی تولید اتصال و درایور دیتابیس.
    بر اساس نوع دیتابیس تنظیم‌شده در config، درایور مناسب را برمی‌گرداند.
    """
    
    _instance: Optional['DatabaseFactory'] = None
    _driver: Optional[DatabaseDriver] = None
    
    def __new__(cls) -> 'DatabaseFactory':
        """پیاده‌سازی Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """مقداردهی اولیه"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._driver_type = config.DATABASE_TYPE.lower()
            logger.info(f"DatabaseFactory initialized with type: {self._driver_type}")
    
    def get_driver(self) -> DatabaseDriver:
        """
        دریافت درایور مناسب بر اساس نوع دیتابیس.
        
        بازگشت:
            نمونه‌ای از DatabaseDriver
        
        استثنا:
            ValueError: در صورت نامعتبر بودن نوع دیتابیس
        """
        if self._driver is None:
            self._driver = self._create_driver()
        return self._driver
    
    def get_connection(self) -> DatabaseConnection:
        """
        دریافت یک اتصال جدید به دیتابیس.
        
        بازگشت:
            نمونه‌ای از DatabaseConnection
        """
        driver = self.get_driver()
        return driver.get_connection()
    
    def _create_driver(self) -> DatabaseDriver:
        """
        ایجاد درایور مناسب بر اساس نوع دیتابیس.
        
        بازگشت:
            نمونه‌ای از DatabaseDriver
        
        استثنا:
            ValueError: در صورت نامعتبر بودن نوع دیتابیس یا عدم دسترسی به درایور
        """
        if self._driver_type == "sqlite":
            logger.debug("Creating SQLite driver")
            return SQLiteDriver()
        elif self._driver_type == "postgresql":
            logger.debug("Creating PostgreSQL driver")
            if not PostgreSQLDriver().is_available():
                logger.warning("asyncpg is not installed. Please install it with: pip install asyncpg")
            return PostgreSQLDriver()
        elif self._driver_type == "mysql":
            logger.debug("Creating MySQL driver")
            if not MySQLDriver().is_available():
                logger.warning("aiomysql is not installed. Please install it with: pip install aiomysql")
            return MySQLDriver()
        else:
            error_msg = f"نوع دیتابیس نامعتبر: {self._driver_type}. گزینه‌های مجاز: sqlite, postgresql, mysql"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def get_connection_string(self) -> str:
        """
        دریافت رشته اتصال به دیتابیس (برای نمایش یا استفاده در ORM).
        
        بازگشت:
            رشته اتصال
        """
        driver = self.get_driver()
        return driver.get_connection_string()
    
    def get_driver_name(self) -> str:
        """
        دریافت نام درایور فعلی.
        
        بازگشت:
            نام درایور (sqlite, postgresql, mysql)
        """
        return self._driver_type
    
    def is_available(self) -> bool:
        """
        بررسی در دسترس بودن درایور انتخابی.
        
        بازگشت:
            True اگر درایور نصب شده باشد
        """
        driver = self.get_driver()
        return driver.is_available()
    
    def get_placeholders(self) -> str:
        """
        دریافت placeholder برای پارامترهای کوئری.
        
        بازگشت:
            رشته placeholder (?, $, %s)
        """
        driver = self.get_driver()
        return driver.get_placeholders()


# ============================================================
# توابع کمکی سراسری
# ============================================================

_db_factory: Optional[DatabaseFactory] = None


def get_db_factory() -> DatabaseFactory:
    """دریافت آبجکت سراسری DatabaseFactory (Singleton)"""
    global _db_factory
    if _db_factory is None:
        _db_factory = DatabaseFactory()
    return _db_factory


def get_db_connection() -> DatabaseConnection:
    """
    دریافت یک اتصال جدید به دیتابیس.
    
    استفاده:
        with get_db_connection() as conn:
            cursor = conn.get_cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
    
    بازگشت:
        نمونه‌ای از DatabaseConnection
    """
    factory = get_db_factory()
    return factory.get_connection()


def get_db_driver() -> DatabaseDriver:
    """
    دریافت درایور دیتابیس.
    
    استفاده:
        driver = get_db_driver()
        with driver.get_connection() as conn:
            ...
    
    بازگشت:
        نمونه‌ای از DatabaseDriver
    """
    factory = get_db_factory()
    return factory.get_driver()


def get_db_connection_string() -> str:
    """
    دریافت رشته اتصال به دیتابیس.
    
    بازگشت:
        رشته اتصال
    """
    factory = get_db_factory()
    return factory.get_connection_string()


def get_db_placeholders() -> str:
    """
    دریافت placeholder برای پارامترهای کوئری.
    
    بازگشت:
        رشته placeholder
    """
    factory = get_db_factory()
    return factory.get_placeholders()


# ============================================================
# سازگاری با کدهای قبلی (SQLite)
# ============================================================

def get_legacy_db_connection():
    """
    دریافت اتصال به دیتابیس با روش قدیمی (برای سازگاری).
    اگر نوع دیتابیس SQLite باشد، از همان روش قبلی استفاده می‌شود.
    """
    factory = get_db_factory()
    if factory.get_driver_name() == "sqlite":
        return factory.get_connection()
    else:
        logger.warning("Legacy connection requested but database type is not SQLite.")
        return factory.get_connection()


__all__ = [
    'DatabaseFactory',
    'get_db_factory',
    'get_db_connection',
    'get_db_driver',
    'get_db_connection_string',
    'get_db_placeholders',
    'get_legacy_db_connection',
]