# database/connection/init.py
# مقداردهی اولیه دیتابیس - ایجاد جداول، داده‌های پیش‌فرض و تنظیمات اولیه
# این فایل بخشی از پکیج connection در معماری جدید است

import os
import sqlite3
from typing import List, Dict, Any, Optional
from logger_config import logger
from config import config
from .manager import get_db_connection, DB_NAME


# ============================================================
# ایجاد جداول اصلی
# ============================================================

def create_tables() -> None:
    """
    ایجاد تمام جداول اصلی دیتابیس در صورت عدم وجود.
    این تابع توسط init_db در manager.py فراخوانی می‌شود.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # ========== جدول دسته‌بندی‌ها ==========
        cursor.execute("""
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
        """)

        # ========== جدول دکمه‌ها ==========
        cursor.execute("""
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
        """)

        # ========== جدول سوالات ==========
        cursor.execute("""
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
        """)

        # ========== جدول شرط‌های سوالات ==========
        cursor.execute("""
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
        """)

        # ========== جدول گزینه‌های دکمه‌ای ==========
        cursor.execute("""
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
        """)

        # ========== جدول تنظیمات ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT DEFAULT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== جدول پاسخ‌های کاربران ==========
        cursor.execute("""
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
        """)

        # ========== جدول سفارشات نهایی ==========
        cursor.execute("""
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
        """)

        # ========== جدول پروفایل‌های اعتبارسنجی ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                settings TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== جدول ادمین‌ها ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                role TEXT DEFAULT 'admin',
                is_active INTEGER DEFAULT 1,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== جدول کاربران ==========
        cursor.execute("""
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
        """)

        # ========== جدول آمار دکمه‌ها ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS button_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                button_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                amount INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (button_id) REFERENCES buttons (id) ON DELETE CASCADE
            )
        """)

        # ========== جدول لاگ خطاها ==========
        cursor.execute("""
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
        """)

        # ========== جدول نسخه‌های دکمه‌ها ==========
        cursor.execute("""
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
        """)

        # ========== جدول الگوهای سوال ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                questions_data TEXT NOT NULL,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ========== جدول تاریخچه سفارشات ==========
        cursor.execute("""
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
        """)

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

        conn.commit()
        logger.info("✅ همه جداول دیتابیس ایجاد/بررسی شدند.")


# ============================================================
# داده‌های پیش‌فرض
# ============================================================

def create_default_categories() -> None:
    """ایجاد دسته‌بندی‌های پیش‌فرض در صورت عدم وجود"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
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
            conn.commit()
            logger.info("✅ دسته‌بندی‌های اصلی ایجاد شدند.")
        else:
            logger.info("ℹ️ دسته‌بندی‌های موجود حفظ شدند.")


def add_owner_to_admins() -> None:
    """اضافه کردن OWNER_ID به جدول ادمین‌ها در صورت عدم وجود"""
    OWNER_ID = config.OWNER_ID
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO admins (user_id, role, is_active) VALUES (?, 'owner', 1)", (OWNER_ID,))
        conn.commit()
        logger.info(f"✅ OWNER_ID ({OWNER_ID}) به عنوان owner به جدول ادمین‌ها اضافه شد.")


def set_default_settings() -> None:
    """تنظیم مقادیر پیش‌فرض در جدول settings"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        default_settings = [
            ("default_menu_columns", "2", "تعداد ستون‌های پیش‌فرض منو (۱ تا ۸)"),
            ("default_price", "50000", "مبلغ پیش‌فرض برای دکمه‌های جدید (ریال)"),
            ("default_price_label", "هزینه خدمات", "برچسب مبلغ پیش‌فرض"),
        ]

        for key, value, description in default_settings:
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)",
                (key, value, description)
            )

        conn.commit()
        logger.info("✅ تنظیمات پیش‌فرض در جدول settings درج شدند.")


# ============================================================
# تابع اصلی مقداردهی اولیه
# ============================================================

def ensure_default_data() -> None:
    """
    اطمینان از وجود تمام داده‌های پیش‌فرض در دیتابیس.
    این تابع توسط init_db فراخوانی می‌شود.
    """
    create_default_categories()
    add_owner_to_admins()
    set_default_settings()
    logger.info("✅ داده‌های پیش‌فرض دیتابیس بروزرسانی شدند.")


# ============================================================
# توابع کمکی برای مدیریت دیتابیس
# ============================================================

def recreate_database() -> None:
    """
    بازسازی کامل دیتابیس (حذف و ایجاد مجدد).
    هشدار: این کار تمام داده‌ها را حذف می‌کند!
    """
    logger.warning("⚠️ در حال بازسازی کامل دیتابیس... همه داده‌ها حذف می‌شوند!")

    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        logger.info(f"🗑️ فایل دیتابیس {DB_NAME} حذف شد.")

    # ایجاد مجدد
    create_tables()
    ensure_default_data()
    logger.info("✅ دیتابیس با موفقیت بازسازی شد.")


def get_table_list() -> List[str]:
    """
    دریافت لیست تمام جداول دیتابیس

    بازگشت: لیست نام جداول
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        rows = cursor.fetchall()
        return [row['name'] for row in rows]


def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    """
    دریافت ساختار یک جدول

    پارامترها:
        table_name: نام جدول

    بازگشت: لیست دیکشنری‌های شامل اطلاعات ستون‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_table_count(table_name: str) -> int:
    """
    دریافت تعداد رکوردهای یک جدول

    پارامترها:
        table_name: نام جدول

    بازگشت: تعداد رکوردها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        row = cursor.fetchone()
        return row['count'] if row else 0


def get_database_size() -> int:
    """
    دریافت حجم فایل دیتابیس (به بایت)

    بازگشت: حجم دیتابیس یا 0 در صورت خطا
    """
    try:
        if os.path.exists(DB_NAME):
            return os.path.getsize(DB_NAME)
        return 0
    except Exception:
        return 0


def get_database_info() -> Dict[str, Any]:
    """
    دریافت اطلاعات کامل دیتابیس

    بازگشت: دیکشنری شامل اطلاعات
    """
    tables = get_table_list()
    table_info = {}
    total_rows = 0

    for table in tables:
        count = get_table_count(table)
        table_info[table] = {
            'rows': count,
            'schema': get_table_schema(table),
        }
        total_rows += count

    return {
        'path': DB_NAME,
        'exists': os.path.exists(DB_NAME),
        'size_bytes': get_database_size(),
        'size_kb': get_database_size() // 1024,
        'size_mb': get_database_size() // (1024 * 1024),
        'total_tables': len(tables),
        'total_rows': total_rows,
        'tables': table_info,
    }


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'create_tables',
    'create_default_categories',
    'add_owner_to_admins',
    'set_default_settings',
    'ensure_default_data',
    'recreate_database',
    'get_table_list',
    'get_table_schema',
    'get_table_count',
    'get_database_size',
    'get_database_info',
]