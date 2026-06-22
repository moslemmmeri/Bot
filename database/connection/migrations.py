# database/connection/migrations.py
# مدیریت نسخه‌بندی دیتابیس (Schema Migrations)
# این فایل جایگزین database/db_migrations.py در معماری جدید است
# امکان اعمال تغییرات ساختاری به‌صورت کنترل‌شده و ثبت تاریخچه مهاجرت‌ها

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from logger_config import logger
from .manager import get_db_connection


# ============================================================
# تنظیمات
# ============================================================

MIGRATIONS_TABLE = "schema_migrations"
CURRENT_VERSION = 8  # نسخه‌ی فعلی دیتابیس


# ============================================================
# توابع پایه
# ============================================================

def ensure_migrations_table() -> None:
    """اطمینان از وجود جدول schema_migrations"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL,
                description TEXT,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT
            )
        """)
        conn.commit()
        logger.debug(f"جدول {MIGRATIONS_TABLE} ایجاد/بررسی شد.")


def get_current_version() -> int:
    """دریافت نسخه‌ی فعلی دیتابیس"""
    ensure_migrations_table()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT MAX(version) as max_version FROM {MIGRATIONS_TABLE}")
        row = cursor.fetchone()
        return row['max_version'] if row and row['max_version'] is not None else 0


def get_applied_migrations() -> List[Dict[str, Any]]:
    """دریافت لیست تمام مهاجرت‌های اعمال‌شده"""
    ensure_migrations_table()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {MIGRATIONS_TABLE} ORDER BY version")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def record_migration(version: int, description: str, checksum: Optional[str] = None) -> None:
    """ثبت یک مهاجرت در جدول migrations"""
    ensure_migrations_table()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {MIGRATIONS_TABLE} (version, description, checksum)
            VALUES (?, ?, ?)
        """, (version, description, checksum))
        conn.commit()
        logger.info(f"✅ مهاجرت نسخه {version} ثبت شد: {description}")


# ============================================================
# تعریف مهاجرت‌ها
# ============================================================

MIGRATIONS = {
    1: {
        "description": "ایجاد جداول اولیه (users, button_stats, error_logs, button_versions)",
        "up": """
            -- جدول users
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- جدول button_stats
            CREATE TABLE IF NOT EXISTS button_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                button_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                amount INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (button_id) REFERENCES buttons (id) ON DELETE CASCADE
            );

            -- جدول error_logs
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
            );

            -- جدول button_versions
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
            );

            -- ایجاد ایندکس‌ها
            CREATE INDEX IF NOT EXISTS idx_button_stats_button_id ON button_stats(button_id);
            CREATE INDEX IF NOT EXISTS idx_button_stats_user_id ON button_stats(user_id);
            CREATE INDEX IF NOT EXISTS idx_button_stats_action_type ON button_stats(action_type);
            CREATE INDEX IF NOT EXISTS idx_button_stats_created_at ON button_stats(created_at);
            CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at);
            CREATE INDEX IF NOT EXISTS idx_error_logs_type ON error_logs(error_type);
            CREATE INDEX IF NOT EXISTS idx_error_logs_resolved ON error_logs(is_resolved);
            CREATE INDEX IF NOT EXISTS idx_button_versions_button_id ON button_versions(button_id);
            CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);
        """,
        "down": """
            DROP TABLE IF EXISTS button_versions;
            DROP TABLE IF EXISTS error_logs;
            DROP TABLE IF EXISTS button_stats;
            DROP TABLE IF EXISTS users;
        """
    },
    2: {
        "description": "افزودن ستون‌های admin_note و status_history به dynamic_orders",
        "up": """
            ALTER TABLE dynamic_orders ADD COLUMN admin_note TEXT;
            ALTER TABLE dynamic_orders ADD COLUMN status_history TEXT;
        """,
        "down": """
            -- SQLite از DROP COLUMN پشتیبانی نمی‌کند، بنابراین این مهاجرت قابل بازگشت نیست.
            SELECT 'Migration 2 cannot be reverted directly' as warning;
        """
    },
    3: {
        "description": "افزودن ستون‌های sort_order به جداول اصلی",
        "up": """
            ALTER TABLE categories ADD COLUMN sort_order INTEGER DEFAULT 0;
            ALTER TABLE buttons ADD COLUMN sort_order INTEGER DEFAULT 0;
            ALTER TABLE questions ADD COLUMN sort_order INTEGER DEFAULT 0;
            ALTER TABLE question_options ADD COLUMN sort_order INTEGER DEFAULT 0;
            ALTER TABLE question_conditions ADD COLUMN sort_order INTEGER DEFAULT 0;
        """,
        "down": """
            SELECT 'Migration 3 cannot be reverted directly' as warning;
        """
    },
    4: {
        "description": "افزودن ستون‌های مدیریت ستون‌ها (تعداد ستون‌های منو) به جداول categories و buttons و تنظیمات پیش‌فرض",
        "up": """
            ALTER TABLE categories ADD COLUMN columns INTEGER DEFAULT 2;
            ALTER TABLE buttons ADD COLUMN columns INTEGER DEFAULT NULL;
            INSERT OR IGNORE INTO settings (key, value, description) 
            VALUES ('default_menu_columns', '2', 'تعداد ستون‌های پیش‌فرض منو (۱ تا ۸)');
        """,
        "down": """
            SELECT 'Migration 4 cannot be reverted directly' as warning;
        """
    },
    5: {
        "description": "افزودن ستون‌های قیمت متغیر به جدول buttons",
        "up": """
            ALTER TABLE buttons ADD COLUMN price_type TEXT DEFAULT 'fixed';
            ALTER TABLE buttons ADD COLUMN min_price INTEGER;
            ALTER TABLE buttons ADD COLUMN max_price INTEGER;
            UPDATE buttons SET price_type = 'fixed' WHERE price_type IS NULL;
        """,
        "down": """
            SELECT 'Migration 5 cannot be reverted directly' as warning;
        """
    },
    6: {
        "description": "افزودن ستون‌های مسدودیت کاربران به جدول users",
        "up": """
            ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0;
            ALTER TABLE users ADD COLUMN block_reason TEXT;
            ALTER TABLE users ADD COLUMN blocked_at TEXT;
            ALTER TABLE users ADD COLUMN role INTEGER DEFAULT 0;
            ALTER TABLE users ADD COLUMN status INTEGER DEFAULT 0;
            ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'fa';
            ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'Asia/Tehran';
            ALTER TABLE users ADD COLUMN extra_data TEXT;
        """,
        "down": """
            SELECT 'Migration 6 cannot be reverted directly' as warning;
        """
    },
    7: {
        "description": "افزودن ستون last_reminder_sent به جدول dynamic_orders",
        "up": """
            ALTER TABLE dynamic_orders ADD COLUMN last_reminder_sent TEXT;
        """,
        "down": """
            SELECT 'Migration 7 cannot be reverted directly' as warning;
        """
    },
    8: {
        "description": "ایجاد جدول question_templates برای مدیریت الگوهای سوال",
        "up": """
            CREATE TABLE IF NOT EXISTS question_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                questions_data TEXT NOT NULL,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_question_templates_name ON question_templates(name);
            CREATE INDEX IF NOT EXISTS idx_question_templates_created_by ON question_templates(created_by);
        """,
        "down": """
            DROP TABLE IF EXISTS question_templates;
        """
    }
}


# ============================================================
# توابع اصلی مهاجرت
# ============================================================

def apply_migration(version: int) -> bool:
    """
    اعمال یک مهاجرت خاص با شماره نسخه.

    پارامترها:
        version: شماره نسخه

    بازگشت: True در صورت موفقیت، False در غیر این صورت
    """
    if version not in MIGRATIONS:
        logger.error(f"❌ مهاجرت نسخه {version} یافت نشد.")
        return False

    migration = MIGRATIONS[version]
    up_sql = migration.get("up", "")

    if not up_sql:
        logger.warning(f"⚠️ مهاجرت نسخه {version} اسکریپت up ندارد.")
        return False

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # اجرای اسکریپت (می‌تواند شامل چندین دستور باشد)
            statements = [s.strip() for s in up_sql.split(';') if s.strip()]
            for stmt in statements:
                cursor.execute(stmt)
            conn.commit()

        # ثبت مهاجرت
        record_migration(version, migration.get("description", ""))
        logger.info(f"✅ مهاجرت نسخه {version} با موفقیت اعمال شد.")
        return True

    except sqlite3.OperationalError as e:
        # اگر جدول یا ستون از قبل وجود داشته باشد، خطا را نادیده می‌گیریم
        if "already exists" in str(e) or "duplicate column" in str(e):
            logger.warning(f"⚠️ مهاجرت نسخه {version} قبلاً اعمال شده است: {e}")
            # ثبت به‌عنوان اعمال‌شده اگر قبلاً ثبت نشده باشد
            current = get_current_version()
            if current < version:
                record_migration(version, MIGRATIONS[version].get("description", ""))
            return True
        else:
            logger.error(f"❌ خطا در اعمال مهاجرت نسخه {version}: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ خطا در اعمال مهاجرت نسخه {version}: {e}")
        return False


def migrate_to_version(target_version: int) -> bool:
    """
    مهاجرت دیتابیس به نسخه‌ی مشخص.
    تمام مهاجرت‌های بین نسخه‌ی فعلی و نسخه‌ی هدف اعمال می‌شوند.

    پارامترها:
        target_version: نسخه‌ی هدف

    بازگشت: True در صورت موفقیت، False در غیر این صورت
    """
    current = get_current_version()

    if current == target_version:
        logger.info(f"ℹ️ دیتابیس در نسخه {current} است. نیازی به مهاجرت نیست.")
        return True

    if current > target_version:
        logger.warning(f"⚠️ نسخه‌ی فعلی ({current}) بزرگتر از نسخه‌ی هدف ({target_version}) است. امکان Downgrade وجود ندارد.")
        return False

    logger.info(f"🔄 مهاجرت از نسخه {current} به {target_version}...")

    for version in range(current + 1, target_version + 1):
        if version in MIGRATIONS:
            logger.info(f"📌 اعمال مهاجرت نسخه {version}: {MIGRATIONS[version].get('description', '')}")
            success = apply_migration(version)
            if not success:
                logger.error(f"❌ مهاجرت به نسخه {version} ناموفق بود. فرآیند متوقف شد.")
                return False
        else:
            logger.warning(f"⚠️ مهاجرت نسخه {version} تعریف نشده است. ادامه می‌دهیم...")

    logger.info(f"✅ مهاجرت به نسخه {target_version} با موفقیت کامل شد.")
    return True


def migrate_to_latest() -> bool:
    """مهاجرت دیتابیس به آخرین نسخه‌ی موجود"""
    return migrate_to_version(CURRENT_VERSION)


def get_pending_migrations() -> List[Dict[str, Any]]:
    """دریافت لیست مهاجرت‌هایی که هنوز اعمال نشده‌اند"""
    current = get_current_version()
    pending = []
    for version in sorted(MIGRATIONS.keys()):
        if version > current:
            pending.append({
                "version": version,
                "description": MIGRATIONS[version].get("description", ""),
                "up": MIGRATIONS[version].get("up", "")[:200] + "..."
            })
    return pending


def get_migration_status() -> Dict[str, Any]:
    """
    دریافت وضعیت کامل مهاجرت‌ها به‌صورت دیکشنری.

    بازگشت: دیکشنری شامل اطلاعات وضعیت
    """
    current = get_current_version()
    applied = get_applied_migrations()
    pending = get_pending_migrations()

    return {
        "current_version": current,
        "latest_version": CURRENT_VERSION,
        "applied_count": len(applied),
        "pending_count": len(pending),
        "applied_migrations": applied,
        "pending_migrations": pending,
        "is_latest": current >= CURRENT_VERSION
    }


def generate_checksum(sql: str) -> str:
    """تولید checksum برای یک اسکریپت SQL"""
    import hashlib
    return hashlib.md5(sql.encode('utf-8')).hexdigest()


def validate_migration_integrity() -> Dict[str, Any]:
    """
    اعتبارسنجی یکپارچگی مهاجرت‌ها.
    بررسی می‌کند که checksum مهاجرت‌های اعمال‌شده با تعاریف فعلی مطابقت داشته باشد.

    بازگشت: دیکشنری شامل وضعیت اعتبارسنجی
    """
    applied = get_applied_migrations()
    issues = []

    for record in applied:
        version = record.get('version')
        stored_checksum = record.get('checksum')

        if version in MIGRATIONS:
            current_checksum = generate_checksum(MIGRATIONS[version].get("up", ""))
            if stored_checksum and stored_checksum != current_checksum:
                issues.append({
                    "version": version,
                    "message": f"checksum mismatch: stored={stored_checksum}, current={current_checksum}"
                })

    return {
        "is_valid": len(issues) == 0,
        "issues": issues
    }


def get_migration_sql(version: int, direction: str = "up") -> Optional[str]:
    """
    دریافت اسکریپت SQL یک مهاجرت خاص.

    پارامترها:
        version: شماره نسخه
        direction: 'up' یا 'down'

    بازگشت: اسکریپت SQL یا None در صورت عدم وجود
    """
    if version not in MIGRATIONS:
        return None
    return MIGRATIONS[version].get(direction)


# ============================================================
# توابع مدیریت نسخه (فقط برای توسعه)
# ============================================================

def reset_migrations() -> None:
    """
    بازنشانی جدول migrations (فقط برای توسعه).
    هشدار: این کار تاریخچه مهاجرت‌ها را پاک می‌کند.
    """
    ensure_migrations_table()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {MIGRATIONS_TABLE}")
        conn.commit()
        logger.warning(f"🗑️ تمام رکوردهای جدول {MIGRATIONS_TABLE} حذف شدند.")


def force_version(version: int) -> None:
    """
    تنظیم نسخه‌ی دیتابیس به مقدار مشخص (بدون اعمال مهاجرت).
    فقط برای مواقع اضطراری استفاده شود.

    پارامترها:
        version: شماره نسخه
    """
    ensure_migrations_table()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # حذف رکوردهای قدیمی‌تر از نسخه‌ی مورد نظر
        cursor.execute(f"DELETE FROM {MIGRATIONS_TABLE} WHERE version > ?", (version,))

        # اگر نسخه‌ی مورد نظر وجود ندارد، ایجاد می‌کنیم
        cursor.execute(f"SELECT 1 FROM {MIGRATIONS_TABLE} WHERE version = ?", (version,))
        if not cursor.fetchone():
            cursor.execute(f"""
                INSERT INTO {MIGRATIONS_TABLE} (version, description)
                VALUES (?, ?)
            """, (version, f"Forced to version {version}"))
        conn.commit()
        logger.warning(f"⚠️ نسخه‌ی دیتابیس به اجبار به {version} تنظیم شد.")


# ============================================================
# تابع یکپارچه برای استفاده در زمان راه‌اندازی
# ============================================================

def run_migrations_if_needed() -> None:
    """
    تابعی که در زمان راه‌اندازی ربات صدا زده می‌شود.
    اگر دیتابیس نیاز به مهاجرت داشته باشد، آن را اعمال می‌کند.
    """
    try:
        ensure_migrations_table()
        current = get_current_version()

        if current < CURRENT_VERSION:
            logger.info(f"🔄 دیتابیس نیاز به مهاجرت دارد (نسخه {current} -> {CURRENT_VERSION})")
            success = migrate_to_latest()
            if success:
                logger.info(f"✅ دیتابیس با موفقیت به نسخه {CURRENT_VERSION} مهاجرت کرد.")
            else:
                logger.error(f"❌ مهاجرت دیتابیس ناموفق بود!")
        else:
            logger.info(f"ℹ️ دیتابیس در آخرین نسخه ({CURRENT_VERSION}) است.")

    except Exception as e:
        logger.error(f"❌ خطا در اجرای مهاجرت‌ها: {e}", exc_info=True)


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'MIGRATIONS_TABLE',
    'CURRENT_VERSION',
    'ensure_migrations_table',
    'get_current_version',
    'get_applied_migrations',
    'record_migration',
    'apply_migration',
    'migrate_to_version',
    'migrate_to_latest',
    'get_pending_migrations',
    'get_migration_status',
    'generate_checksum',
    'validate_migration_integrity',
    'get_migration_sql',
    'reset_migrations',
    'force_version',
    'run_migrations_if_needed',
]