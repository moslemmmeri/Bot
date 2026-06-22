# database/connection/manager.py
# مدیریت اتصال به دیتابیس - هسته اصلی اتصال و مقداردهی اولیه
# این فایل جایگزین database/db_connection.py در معماری جدید است
# اصلاح شده با مدیریت خطا و لاگ‌گیری کامل در دیتابیس

import os
import time
import sqlite3
from contextlib import contextmanager
from typing import Optional, Generator, Dict, Any
from logger_config import logger
from config import config
from database.drivers import get_driver, get_connection
from database.drivers.sqlite_driver import SQLiteConnection
from database.drivers.postgres_driver import PostgresConnection
from database.drivers.mysql_driver import MySQLConnection
from utils.error_handler import log_database_error, log_critical_error


# ============================================================
# تنظیمات پایه
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_NAME = os.path.join(BASE_DIR, config.SQLITE_DB_PATH)

# پول اتصال (برای PostgreSQL/MySQL در آینده)
_connection_pool = None
_pool_size = 10


# ============================================================
# مدیریت اتصال
# ============================================================

@contextmanager
def get_db_connection(retries: int = 3, delay: float = 1.0) -> Generator:
    """
    ایجاد اتصال به دیتابیس با قابلیت تلاش مجدد در صورت خطا.
    با مدیریت صحیح بستن اتصال حتی در صورت بروز استثنا.

    پارامترها:
        retries: تعداد دفعات تلاش مجدد
        delay: زمان تأخیر بین هر تلاش (ثانیه)

    استفاده:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ...
    """
    last_exception = None

    for attempt in range(retries):
        try:
            # استفاده از درایور مناسب بر اساس نوع دیتابیس
            if config.DATABASE_TYPE == 'sqlite':
                conn = sqlite3.connect(DB_NAME, timeout=20, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                # تنظیمات بهینه برای SQLite
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA cache_size = 10000")
                logger.debug(f"✅ SQLite connection established (attempt {attempt + 1})")
            else:
                # برای PostgreSQL/MySQL از درایورهای اختصاصی استفاده می‌شود
                conn = get_connection()
                logger.debug(f"✅ {config.DATABASE_TYPE} connection established (attempt {attempt + 1})")

            try:
                yield conn
            finally:
                conn.close()
                logger.debug("Connection closed")

            break  # اگر موفقیت‌آمیز بود، حلقه را می‌شکنیم

        except sqlite3.OperationalError as e:
            last_exception = e
            logger.warning(f"Database connection error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                log_database_error(
                    f"Failed to connect to database after {retries} attempts: {str(e)}",
                    traceback=str(e)
                )
                raise
        except Exception as e:
            log_database_error(
                f"Unexpected database connection error: {str(e)}",
                traceback=str(e)
            )
            raise


def get_connection_pool() -> Optional[Any]:
    """
    دریافت پول اتصال برای دیتابیس‌های پشتیبانی‌کننده (PostgreSQL, MySQL)

    بازگشت: آبجکت پول اتصال یا None در صورت عدم پشتیبانی
    """
    global _connection_pool
    if _connection_pool is not None:
        return _connection_pool

    if config.DATABASE_TYPE in ['postgresql', 'mysql']:
        try:
            driver = get_driver()
            if hasattr(driver, 'create_pool'):
                _connection_pool = driver.create_pool(min_size=1, max_size=_pool_size)
                logger.info(f"✅ Connection pool created for {config.DATABASE_TYPE}")
            return _connection_pool
        except Exception as e:
            log_database_error(
                f"Failed to create connection pool: {str(e)}",
                traceback=str(e)
            )
            return None

    return None


def close_connection_pool():
    """بستن پول اتصال"""
    global _connection_pool
    if _connection_pool is not None:
        try:
            if hasattr(_connection_pool, 'close'):
                _connection_pool.close()
            logger.info("Connection pool closed")
        except Exception as e:
            log_database_error(
                f"Error closing connection pool: {str(e)}",
                traceback=str(e)
            )
        _connection_pool = None


def is_connected() -> bool:
    """
    بررسی اتصال به دیتابیس

    بازگشت: True اگر اتصال برقرار باشد
    """
    try:
        with get_db_connection(retries=1) as conn:
            conn.execute("SELECT 1")
            return True
    except Exception as e:
        log_database_error(
            f"Connection check failed: {str(e)}",
            traceback=str(e)
        )
        return False


def get_db_status() -> Dict[str, Any]:
    """
    دریافت وضعیت دیتابیس

    بازگشت: دیکشنری شامل اطلاعات وضعیت
    """
    status = {
        'type': config.DATABASE_TYPE,
        'connected': False,
        'path': DB_NAME if config.DATABASE_TYPE == 'sqlite' else None,
        'pool_size': _pool_size,
        'pool_active': _connection_pool is not None,
    }

    try:
        status['connected'] = is_connected()
    except Exception as e:
        log_database_error(
            f"Error getting db status: {str(e)}",
            traceback=str(e)
        )

    return status


# ============================================================
# افزودن ستون‌های جدید (برای ارتقای دیتابیس)
# ============================================================

def add_validation_columns_if_not_exists():
    """
    افزودن ستون‌های اعتبارسنجی به جدول questions در صورت عدم وجود.
    این ستون‌ها برای مدیریت اعتبارسنجی پیشرفته سوالات استفاده می‌شوند.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            columns = [
                ("is_required", "INTEGER DEFAULT 0"),
                ("validation_enabled", "INTEGER DEFAULT 0"),
                ("validation_type", "TEXT DEFAULT 'none'"),
                ("length_validation_enabled", "INTEGER DEFAULT 0"),
                ("min_length", "INTEGER"),
                ("max_length", "INTEGER"),
                ("word_validation_enabled", "INTEGER DEFAULT 0"),
                ("min_words", "INTEGER"),
                ("max_words", "INTEGER"),
                ("numeric_validation_enabled", "INTEGER DEFAULT 0"),
                ("min_value", "INTEGER"),
                ("max_value", "INTEGER"),
                ("step", "INTEGER"),
                ("date_validation_enabled", "INTEGER DEFAULT 0"),
                ("min_date", "TEXT"),
                ("max_date", "TEXT"),
                ("future_only", "INTEGER DEFAULT 0"),
                ("past_only", "INTEGER DEFAULT 0"),
                ("weekdays_only", "INTEGER DEFAULT 0"),
                ("file_validation_enabled", "INTEGER DEFAULT 0"),
                ("allowed_formats", "TEXT"),
                ("max_file_size", "INTEGER"),
                ("min_file_size", "INTEGER"),
                ("max_files", "INTEGER"),
                ("dimensions_enabled", "INTEGER DEFAULT 0"),
                ("required_width", "INTEGER"),
                ("required_height", "INTEGER"),
                ("aspect_ratio", "TEXT"),
                ("pattern_validation_enabled", "INTEGER DEFAULT 0"),
                ("regex_pattern", "TEXT"),
                ("starts_with", "TEXT"),
                ("ends_with", "TEXT"),
                ("contains_validation_enabled", "INTEGER DEFAULT 0"),
                ("contains", "TEXT"),
                ("not_contains", "TEXT"),
                ("forbidden_words", "TEXT"),
                ("required_words", "TEXT"),
                ("conditional_enabled", "INTEGER DEFAULT 0"),
                ("conditional_on", "INTEGER"),
                ("conditional_value", "TEXT"),
                ("auto_fix_enabled", "INTEGER DEFAULT 0"),
                ("validation_error", "TEXT"),
                ("validation_hint", "TEXT"),
            ]
            for col_name, col_type in columns:
                try:
                    cursor.execute(f"SELECT {col_name} FROM questions LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute(f"ALTER TABLE questions ADD COLUMN {col_name} {col_type}")
                    logger.info(f"✅ فیلد {col_name} به جدول questions اضافه شد.")
            conn.commit()
            logger.info("✅ ستون‌های اعتبارسنجی بروزرسانی شدند.")
    except Exception as e:
        log_database_error(
            f"Error in add_validation_columns_if_not_exists: {str(e)}",
            traceback=str(e)
        )


def add_order_columns_if_not_exists():
    """
    افزودن ستون‌های admin_note، status_history و last_reminder_sent به جدول dynamic_orders در صورت عدم وجود.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # ستون admin_note
            try:
                cursor.execute("SELECT admin_note FROM dynamic_orders LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE dynamic_orders ADD COLUMN admin_note TEXT")
                logger.info("✅ ستون admin_note به جدول dynamic_orders اضافه شد.")
            
            # ستون status_history
            try:
                cursor.execute("SELECT status_history FROM dynamic_orders LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE dynamic_orders ADD COLUMN status_history TEXT")
                logger.info("✅ ستون status_history به جدول dynamic_orders اضافه شد.")
            
            # ستون last_reminder_sent
            try:
                cursor.execute("SELECT last_reminder_sent FROM dynamic_orders LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE dynamic_orders ADD COLUMN last_reminder_sent TEXT")
                logger.info("✅ ستون last_reminder_sent به جدول dynamic_orders اضافه شد.")
            
            conn.commit()
            logger.info("✅ ستون‌های جدید جدول dynamic_orders بروزرسانی شدند.")
    except Exception as e:
        log_database_error(
            f"Error in add_order_columns_if_not_exists: {str(e)}",
            traceback=str(e)
        )


def add_price_columns_if_not_exists():
    """
    افزودن ستون‌های مربوط به قیمت متغیر به جدول buttons در صورت عدم وجود.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # ستون price_type
            try:
                cursor.execute("SELECT price_type FROM buttons LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE buttons ADD COLUMN price_type TEXT DEFAULT 'fixed'")
                logger.info("✅ ستون price_type به جدول buttons اضافه شد.")
            
            # ستون min_price
            try:
                cursor.execute("SELECT min_price FROM buttons LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE buttons ADD COLUMN min_price INTEGER")
                logger.info("✅ ستون min_price به جدول buttons اضافه شد.")
            
            # ستون max_price
            try:
                cursor.execute("SELECT max_price FROM buttons LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE buttons ADD COLUMN max_price INTEGER")
                logger.info("✅ ستون max_price به جدول buttons اضافه شد.")
            
            conn.commit()
            logger.info("✅ ستون‌های قیمت متغیر به جدول buttons اضافه شدند.")
    except Exception as e:
        log_database_error(
            f"Error in add_price_columns_if_not_exists: {str(e)}",
            traceback=str(e)
        )


def add_user_block_columns_if_not_exists():
    """
    افزودن ستون‌های مربوط به مسدودیت کاربر به جدول users در صورت عدم وجود.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # ستون is_blocked
            try:
                cursor.execute("SELECT is_blocked FROM users LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")
                logger.info("✅ ستون is_blocked به جدول users اضافه شد.")
            
            # ستون block_reason
            try:
                cursor.execute("SELECT block_reason FROM users LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE users ADD COLUMN block_reason TEXT")
                logger.info("✅ ستون block_reason به جدول users اضافه شد.")
            
            # ستون blocked_at
            try:
                cursor.execute("SELECT blocked_at FROM users LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE users ADD COLUMN blocked_at TEXT")
                logger.info("✅ ستون blocked_at به جدول users اضافه شد.")
            
            conn.commit()
            logger.info("✅ ستون‌های مسدودیت به جدول users اضافه شدند.")
    except Exception as e:
        log_database_error(
            f"Error in add_user_block_columns_if_not_exists: {str(e)}",
            traceback=str(e)
        )


def add_user_extra_columns_if_not_exists():
    """
    افزودن ستون‌های اضافی به جدول users برای پشتیبانی از زبان، منطقه زمانی، نقش و وضعیت.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            columns = [
                ("language", "TEXT DEFAULT 'fa'"),
                ("timezone", "TEXT DEFAULT 'Asia/Tehran'"),
                ("extra_data", "TEXT"),
                ("role", "INTEGER DEFAULT 0"),
                ("status", "INTEGER DEFAULT 0"),
            ]
            
            for col_name, col_type in columns:
                try:
                    cursor.execute(f"SELECT {col_name} FROM users LIMIT 1")
                except sqlite3.OperationalError:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    logger.info(f"✅ فیلد {col_name} به جدول users اضافه شد.")
            
            conn.commit()
            logger.info("✅ ستون‌های اضافی کاربران بروزرسانی شدند.")
    except Exception as e:
        log_database_error(
            f"Error in add_user_extra_columns_if_not_exists: {str(e)}",
            traceback=str(e)
        )


def create_order_logs_table():
    """ایجاد جدول order_logs برای ثبت تاریخچه سفارشات"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    note TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES dynamic_orders (id) ON DELETE CASCADE
                )
            ''')
            logger.info("✅ جدول order_logs ایجاد/بررسی شد.")
    except Exception as e:
        log_database_error(
            f"Error in create_order_logs_table: {str(e)}",
            traceback=str(e)
        )


def add_columns_if_not_exists():
    """اضافه کردن ستون‌های مدیریت ستون‌ها به جداول categories و buttons"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # ستون columns به categories
            try:
                cursor.execute("SELECT columns FROM categories LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE categories ADD COLUMN columns INTEGER DEFAULT 2")
                logger.info("✅ ستون columns به جدول categories اضافه شد.")
            
            # ستون columns به buttons
            try:
                cursor.execute("SELECT columns FROM buttons LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE buttons ADD COLUMN columns INTEGER DEFAULT NULL")
                logger.info("✅ ستون columns به جدول buttons اضافه شد.")
            
            # درج مقدار پیش‌فرض در settings
            cursor.execute("SELECT value FROM settings WHERE key = 'default_menu_columns'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
                    ("default_menu_columns", "2", "تعداد ستون‌های پیش‌فرض منو (۱ تا ۸)")
                )
                logger.info("✅ مقدار پیش‌فرض default_menu_columns=2 در جدول settings درج شد.")
            
            conn.commit()
    except Exception as e:
        log_database_error(
            f"Error in add_columns_if_not_exists: {str(e)}",
            traceback=str(e)
        )


def create_question_templates_table():
    """ایجاد جدول question_templates برای مدیریت الگوهای سوال"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    questions_data TEXT NOT NULL,
                    created_by INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("✅ جدول question_templates ایجاد/بررسی شد.")
    except Exception as e:
        log_database_error(
            f"Error in create_question_templates_table: {str(e)}",
            traceback=str(e)
        )


# ============================================================
# مقداردهی اولیه دیتابیس
# ============================================================

def init_db():
    """
    مقداردهی اولیه دیتابیس:
    - ایجاد تمام جداول اصلی
    - اضافه کردن دسته‌بندی‌های پیش‌فرض
    - اضافه کردن OWNER_ID به جدول ادمین‌ها
    - اعمال مهاجرت‌های دیتابیس
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # ========== جدول دسته‌بندی‌ها ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    icon TEXT DEFAULT '📁',
                    location TEXT DEFAULT 'main',
                    sort_order INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    columns INTEGER DEFAULT 2,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== جدول دکمه‌ها ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buttons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    parent_button_id INTEGER DEFAULT NULL,
                    name TEXT NOT NULL,
                    icon TEXT DEFAULT '',
                    callback_data TEXT UNIQUE NOT NULL,
                    has_submenu INTEGER DEFAULT 0,
                    has_payment INTEGER DEFAULT 0,
                    price_amount INTEGER DEFAULT 50000,
                    price_label TEXT DEFAULT 'هزینه خدمات',
                    price_type TEXT DEFAULT 'fixed',
                    min_price INTEGER,
                    max_price INTEGER,
                    sort_order INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    columns INTEGER DEFAULT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_button_id) REFERENCES buttons (id) ON DELETE CASCADE
                )
            ''')

            # ========== جدول سوالات ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    button_id INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type TEXT DEFAULT 'text',
                    validation_rule TEXT DEFAULT NULL,
                    error_message TEXT DEFAULT NULL,
                    needs_button INTEGER DEFAULT 0,
                    array_name TEXT DEFAULT NULL,
                    sort_order INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_required INTEGER DEFAULT 0,
                    validation_enabled INTEGER DEFAULT 0,
                    validation_type TEXT DEFAULT 'none',
                    length_validation_enabled INTEGER DEFAULT 0,
                    min_length INTEGER,
                    max_length INTEGER,
                    word_validation_enabled INTEGER DEFAULT 0,
                    min_words INTEGER,
                    max_words INTEGER,
                    numeric_validation_enabled INTEGER DEFAULT 0,
                    min_value INTEGER,
                    max_value INTEGER,
                    step INTEGER,
                    date_validation_enabled INTEGER DEFAULT 0,
                    min_date TEXT,
                    max_date TEXT,
                    future_only INTEGER DEFAULT 0,
                    past_only INTEGER DEFAULT 0,
                    weekdays_only INTEGER DEFAULT 0,
                    file_validation_enabled INTEGER DEFAULT 0,
                    allowed_formats TEXT,
                    max_file_size INTEGER,
                    min_file_size INTEGER,
                    max_files INTEGER,
                    dimensions_enabled INTEGER DEFAULT 0,
                    required_width INTEGER,
                    required_height INTEGER,
                    aspect_ratio TEXT,
                    pattern_validation_enabled INTEGER DEFAULT 0,
                    regex_pattern TEXT,
                    starts_with TEXT,
                    ends_with TEXT,
                    contains_validation_enabled INTEGER DEFAULT 0,
                    contains TEXT,
                    not_contains TEXT,
                    forbidden_words TEXT,
                    required_words TEXT,
                    conditional_enabled INTEGER DEFAULT 0,
                    conditional_on INTEGER,
                    conditional_value TEXT,
                    auto_fix_enabled INTEGER DEFAULT 0,
                    validation_error TEXT,
                    validation_hint TEXT,
                    FOREIGN KEY (button_id) REFERENCES buttons (id) ON DELETE CASCADE
                )
            ''')

            # ========== جدول شرط‌های سوالات ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_conditions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    condition_question_id INTEGER NOT NULL,
                    condition_operator TEXT NOT NULL,
                    condition_value TEXT NOT NULL,
                    logic_operator TEXT DEFAULT 'AND',
                    sort_order INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE,
                    FOREIGN KEY (condition_question_id) REFERENCES questions (id) ON DELETE CASCADE
                )
            ''')

            # ========== جدول گزینه‌های دکمه‌ای ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    option_text TEXT NOT NULL,
                    callback_data TEXT UNIQUE NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
                )
            ''')

            # ========== جدول تنظیمات ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT DEFAULT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== جدول پاسخ‌های کاربران ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    button_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    answer TEXT,
                    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (button_id) REFERENCES buttons (id) ON DELETE CASCADE,
                    FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
                )
            ''')

            # ========== جدول سفارشات نهایی ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dynamic_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    button_id INTEGER NOT NULL,
                    order_data TEXT NOT NULL,
                    payment_amount INTEGER,
                    tracking_code TEXT,
                    status TEXT DEFAULT 'pending',
                    admin_note TEXT,
                    status_history TEXT,
                    last_reminder_sent TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (button_id) REFERENCES buttons (id) ON DELETE CASCADE
                )
            ''')

            # ========== جدول پروفایل‌های اعتبارسنجی ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validation_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    settings TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== جدول ادمین‌ها ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    role TEXT DEFAULT 'admin',
                    is_active INTEGER DEFAULT 1,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== جدول کاربران ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_active TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_blocked INTEGER DEFAULT 0,
                    block_reason TEXT,
                    blocked_at TEXT,
                    role INTEGER DEFAULT 0,
                    status INTEGER DEFAULT 0,
                    language TEXT DEFAULT 'fa',
                    timezone TEXT DEFAULT 'Asia/Tehran',
                    extra_data TEXT
                )
            ''')

            # ========== جدول آمار دکمه‌ها ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS button_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    button_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    amount INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (button_id) REFERENCES buttons (id) ON DELETE CASCADE
                )
            ''')

            # ========== جدول لاگ خطاها ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    traceback TEXT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    data TEXT,
                    is_resolved INTEGER DEFAULT 0,
                    resolved_at TEXT,
                    resolved_by INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== جدول نسخه‌های دکمه‌ها ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS button_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    button_id INTEGER NOT NULL,
                    version_number INTEGER NOT NULL,
                    snapshot_data TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    note TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (button_id) REFERENCES buttons (id) ON DELETE CASCADE,
                    UNIQUE(button_id, version_number)
                )
            ''')

            # ========== جدول الگوهای سوال ==========
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    questions_data TEXT NOT NULL,
                    created_by INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ========== بررسی و اضافه کردن ستون‌های گم‌شده به جدول admins ==========
            try:
                cursor.execute("SELECT role FROM admins LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE admins ADD COLUMN role TEXT DEFAULT 'admin'")
                logger.info("✅ ستون role به جدول admins اضافه شد.")
            try:
                cursor.execute("SELECT is_active FROM admins LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE admins ADD COLUMN is_active INTEGER DEFAULT 1")
                logger.info("✅ ستون is_active به جدول admins اضافه شد.")

            # ========== ایجاد دسته‌بندی‌های اصلی ==========
            cursor.execute("SELECT COUNT(*) as count FROM categories")
            count_row = cursor.fetchone()
            if count_row and count_row["count"] == 0:
                default_categories = [
                    ("منوی اصلی", "main"),
                    ("منوی بیشتر", "more"),
                    ("دیگر خدمات", "other")
                ]
                for name, location in default_categories:
                    cursor.execute(
                        "INSERT INTO categories (name, location, is_active, columns) VALUES (?, ?, 1, 2)",
                        (name, location)
                    )
                logger.info("✅ دسته‌بندی‌های اصلی ایجاد شدند.")
            else:
                logger.info("ℹ️ دسته‌بندی‌های موجود حفظ شدند (هیچ تغییری اعمال نشد).")

            # ========== اضافه کردن OWNER_ID ==========
            from config import config
            OWNER_ID = config.OWNER_ID
            cursor.execute("INSERT OR IGNORE INTO admins (user_id, role, is_active) VALUES (?, 'owner', 1)", (OWNER_ID,))
            logger.info(f"✅ OWNER_ID ({OWNER_ID}) به عنوان owner به جدول ادمین‌ها اضافه شد.")

            # ========== درج مقدار پیش‌فرض default_menu_columns در settings ==========
            cursor.execute("SELECT value FROM settings WHERE key = 'default_menu_columns'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
                    ("default_menu_columns", "2", "تعداد ستون‌های پیش‌فرض منو (۱ تا ۸)")
                )
                logger.info("✅ مقدار پیش‌فرض default_menu_columns=2 در جدول settings درج شد.")

            conn.commit()
            logger.info("✅ دیتابیس با موفقیت ایجاد/بروزرسانی شد.")

    except Exception as e:
        log_critical_error(
            f"Error in init_db: {str(e)}",
            traceback=str(e)
        )
        raise

    # افزودن ستون‌های اعتبارسنجی در صورت نیاز (جدول questions)
    add_validation_columns_if_not_exists()
    # افزودن ستون‌های جدید به جدول dynamic_orders
    add_order_columns_if_not_exists()
    # ایجاد جدول order_logs
    create_order_logs_table()
    # افزودن ستون‌های مدیریت ستون‌ها (برای جداول قدیمی)
    add_columns_if_not_exists()
    # افزودن ستون‌های قیمت متغیر به جدول buttons
    add_price_columns_if_not_exists()
    # افزودن ستون‌های مسدودیت به جدول users
    add_user_block_columns_if_not_exists()
    # افزودن ستون‌های اضافی کاربران (زبان، نقش، وضعیت، ...) - جدید
    add_user_extra_columns_if_not_exists()
    # ایجاد جدول question_templates
    create_question_templates_table()


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'get_db_connection',
    'DB_NAME',
    'init_db',
    'add_validation_columns_if_not_exists',
    'add_order_columns_if_not_exists',
    'add_price_columns_if_not_exists',
    'add_user_block_columns_if_not_exists',
    'add_user_extra_columns_if_not_exists',
    'create_order_logs_table',
    'add_columns_if_not_exists',
    'create_question_templates_table',
    'get_connection_pool',
    'close_connection_pool',
    'is_connected',
    'get_db_status',
]