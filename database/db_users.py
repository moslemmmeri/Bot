# database/db_users.py
# مدیریت کاربران ربات - ثبت، به‌روزرسانی، آمار و لیست کاربران
# پشتیبانی از فیلدهای جدید: is_blocked, block_reason, blocked_at, role, status, language, timezone, extra_data
# اصلاح شده با مدیریت خطا و لاگ‌گیری کامل در دیتابیس

from logger_config import logger
from .db_connection import get_db_connection
from utils.error_handler import log_database_error, log_general_error


def upsert_user(user_id, username=None, first_name=None, last_name=None,
                language="fa", timezone="Asia/Tehran"):
    """
    ثبت یا به‌روزرسانی اطلاعات کاربر در جدول users.
    اگر کاربر وجود نداشته باشد، رکورد جدید با first_seen = CURRENT_TIMESTAMP ایجاد می‌شود.
    در غیر این صورت، last_active به‌روز می‌شود.
    
    پارامترها:
        user_id: شناسه کاربر
        username: نام کاربری (اختیاری)
        first_name: نام (اختیاری)
        last_name: نام خانوادگی (اختیاری)
        language: زبان (پیش‌فرض: fa)
        timezone: منطقه زمانی (پیش‌فرض: Asia/Tehran)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # بررسی وجود کاربر
            cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone() is not None

            if exists:
                # به‌روزرسانی last_active و اطلاعات اختیاری
                cursor.execute("""
                    UPDATE users 
                    SET last_active = CURRENT_TIMESTAMP,
                        username = COALESCE(?, username),
                        first_name = COALESCE(?, first_name),
                        last_name = COALESCE(?, last_name),
                        language = COALESCE(?, language),
                        timezone = COALESCE(?, timezone)
                    WHERE user_id = ?
                """, (username, first_name, last_name, language, timezone, user_id))
                logger.debug(f"کاربر {user_id} به‌روزرسانی شد (last_active)")
            else:
                # درج رکورد جدید با فیلدهای جدید
                cursor.execute("""
                    INSERT INTO users (
                        user_id, username, first_name, last_name, 
                        first_seen, last_active, language, timezone,
                        is_blocked, role, status
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, 0, 0, 0)
                """, (user_id, username, first_name, last_name, language, timezone))
                logger.info(f"کاربر جدید {user_id} ثبت شد.")

            conn.commit()
    except Exception as e:
        log_database_error(
            f"Error in upsert_user for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )


def get_user(user_id):
    """دریافت اطلاعات کامل یک کاربر"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log_database_error(
            f"Error in get_user for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return None


def get_all_users(limit=20, offset=0):
    """دریافت لیست کاربران با صفحه‌بندی، مرتب‌شده بر اساس آخرین فعالیت (جدیدترین اول)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users 
                ORDER BY last_active DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_all_users: {str(e)}",
            traceback=str(e)
        )
        return []


def get_total_users():
    """تعداد کل کاربران ثبت‌شده در ربات"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(
            f"Error in get_total_users: {str(e)}",
            traceback=str(e)
        )
        return 0


def get_active_users(days=1):
    """
    تعداد کاربرانی که در N روز اخیر فعالیت داشته‌اند.
    days: تعداد روزهای گذشته (پیش‌فرض ۱ روز)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM users 
                WHERE last_active >= datetime('now', '-' || ? || ' days')
                AND is_blocked = 0
            """, (days,))
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(
            f"Error in get_active_users for {days} days: {str(e)}",
            traceback=str(e)
        )
        return 0


def get_user_orders_count(user_id):
    """تعداد سفارشات ثبت‌شده توسط کاربر"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM dynamic_orders WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(
            f"Error in get_user_orders_count for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return 0


def get_user_total_payment(user_id):
    """مجموع مبلغ پرداختی کاربر (از سفارشات با وضعیت paid یا completed)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(COALESCE(payment_amount, 0)) as total 
                FROM dynamic_orders 
                WHERE user_id = ? AND status IN ('paid', 'completed')
            """, (user_id,))
            row = cursor.fetchone()
            return row['total'] if row and row['total'] is not None else 0
    except Exception as e:
        log_database_error(
            f"Error in get_user_total_payment for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return 0


def get_users_with_stats(limit=20, offset=0):
    """
    دریافت لیست کاربران به همراه آمار سفارشات (تعداد سفارش و مجموع مبلغ).
    این تابع با JOIN بین users و dynamic_orders انجام می‌شود.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    u.user_id,
                    u.username,
                    u.first_name,
                    u.last_name,
                    u.first_seen,
                    u.last_active,
                    u.is_blocked,
                    u.block_reason,
                    u.blocked_at,
                    u.role,
                    u.status,
                    u.language,
                    u.timezone,
                    COUNT(o.id) AS orders_count,
                    COALESCE(SUM(o.payment_amount), 0) AS total_payment
                FROM users u
                LEFT JOIN dynamic_orders o ON u.user_id = o.user_id AND o.status IN ('paid', 'completed')
                GROUP BY u.user_id
                ORDER BY u.last_active DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_users_with_stats: {str(e)}",
            traceback=str(e)
        )
        return []


def search_users(keyword, limit=20):
    """
    جستجوی کاربران بر اساس user_id, username, first_name, last_name
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # اگر کلمه کلیدی عددی باشد، روی user_id جستجو می‌شود
            if keyword.isdigit():
                cursor.execute("""
                    SELECT * FROM users 
                    WHERE user_id LIKE ? OR username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
                    LIMIT ?
                """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit))
            else:
                cursor.execute("""
                    SELECT * FROM users 
                    WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
                    LIMIT ?
                """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in search_users for keyword '{keyword}': {str(e)}",
            traceback=str(e)
        )
        return []


# ==================== توابع جدید مدیریت مسدودیت کاربران ====================

def block_user(user_id, reason=None):
    """
    مسدود کردن یک کاربر
    
    پارامترها:
        user_id: شناسه کاربر
        reason: دلیل مسدودیت (اختیاری)
    
    بازگشت: True در صورت موفقیت
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET is_blocked = 1, 
                    block_reason = ?,
                    blocked_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (reason or 'مسدود شده توسط ادمین', user_id))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"🚫 کاربر {user_id} مسدود شد. دلیل: {reason or 'نامشخص'}")
                return True
            return False
    except Exception as e:
        log_database_error(
            f"Error in block_user for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def unblock_user(user_id):
    """
    رفع مسدودیت کاربر
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True در صورت موفقیت
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET is_blocked = 0, 
                    block_reason = NULL,
                    blocked_at = NULL
                WHERE user_id = ?
            """, (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"✅ کاربر {user_id} رفع مسدودیت شد.")
                return True
            return False
    except Exception as e:
        log_database_error(
            f"Error in unblock_user for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def is_user_blocked(user_id):
    """
    بررسی مسدود بودن کاربر
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True اگر کاربر مسدود باشد
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_blocked FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row and row['is_blocked'] == 1
    except Exception as e:
        log_database_error(
            f"Error in is_user_blocked for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def get_blocked_users(limit=20, offset=0):
    """
    دریافت لیست کاربران مسدود شده
    
    پارامترها:
        limit: تعداد نتایج
        offset: موقعیت شروع
    
    بازگشت: لیست کاربران مسدود شده
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users 
                WHERE is_blocked = 1
                ORDER BY blocked_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_blocked_users: {str(e)}",
            traceback=str(e)
        )
        return []


def get_blocked_count():
    """تعداد کاربران مسدود شده"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_blocked = 1")
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(
            f"Error in get_blocked_count: {str(e)}",
            traceback=str(e)
        )
        return 0


# ==================== توابع جدید مدیریت نقش کاربران ====================

def update_user_role(user_id, role):
    """
    تغییر نقش کاربر
    
    پارامترها:
        user_id: شناسه کاربر
        role: نقش جدید (0=کاربر عادی، 1=ادمین، 2=مدیر، 3=ناظر، 10=مالک)
    
    بازگشت: True در صورت موفقیت
    """
    if role not in [0, 1, 2, 3, 10]:
        log_general_error(f"Invalid role {role} for user {user_id}")
        return False
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"🔄 نقش کاربر {user_id} به {role} تغییر یافت.")
                return True
            return False
    except Exception as e:
        log_database_error(
            f"Error in update_user_role for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def get_user_role(user_id):
    """
    دریافت نقش کاربر
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: نقش کاربر (عدد) یا None در صورت عدم وجود
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row['role'] if row else None
    except Exception as e:
        log_database_error(
            f"Error in get_user_role for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return None


def get_users_by_role(role, limit=20, offset=0):
    """
    دریافت کاربران با نقش مشخص
    
    پارامترها:
        role: نقش (0=کاربر عادی، 1=ادمین، 2=مدیر، 3=ناظر، 10=مالک)
        limit: تعداد نتایج
        offset: موقعیت شروع
    
    بازگشت: لیست کاربران
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users 
                WHERE role = ?
                ORDER BY user_id
                LIMIT ? OFFSET ?
            """, (role, limit, offset))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_users_by_role for role {role}: {str(e)}",
            traceback=str(e)
        )
        return []


# ==================== توابع کمکی ====================

def get_user_by_username(username):
    """
    دریافت کاربر بر اساس نام کاربری
    
    پارامترها:
        username: نام کاربری
    
    بازگشت: دیکشنری اطلاعات کاربر یا None
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log_database_error(
            f"Error in get_user_by_username for {username}: {str(e)}",
            traceback=str(e)
        )
        return None


def update_user_language(user_id, language):
    """
    به‌روزرسانی زبان کاربر
    
    پارامترها:
        user_id: شناسه کاربر
        language: کد زبان (fa, en, ...)
    
    بازگشت: True در صورت موفقیت
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        log_database_error(
            f"Error in update_user_language for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def update_user_timezone(user_id, timezone):
    """
    به‌روزرسانی منطقه زمانی کاربر
    
    پارامترها:
        user_id: شناسه کاربر
        timezone: منطقه زمانی (مثال: Asia/Tehran)
    
    بازگشت: True در صورت موفقیت
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET timezone = ? WHERE user_id = ?", (timezone, user_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        log_database_error(
            f"Error in update_user_timezone for {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def get_recent_users(limit=10):
    """
    دریافت کاربران جدید (اخیراً ثبت‌شده)
    
    پارامترها:
        limit: تعداد نتایج
    
    بازگشت: لیست کاربران جدید
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users 
                ORDER BY first_seen DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_recent_users: {str(e)}",
            traceback=str(e)
        )
        return []


def get_users_with_filter(filters, limit=20, offset=0):
    """
    دریافت کاربران با فیلترهای مختلف
    
    پارامترها:
        filters: دیکشنری فیلترها
            - is_blocked: True/False
            - role: عدد نقش
            - has_orders: True/False
            - active_since: تعداد روزهای اخیر
        limit: تعداد نتایج
        offset: موقعیت شروع
    
    بازگشت: لیست کاربران
    """
    try:
        conditions = []
        params = []
        
        if 'is_blocked' in filters:
            conditions.append("is_blocked = ?")
            params.append(1 if filters['is_blocked'] else 0)
        
        if 'role' in filters:
            conditions.append("role = ?")
            params.append(filters['role'])
        
        if 'active_since' in filters and filters['active_since'] > 0:
            conditions.append("last_active >= datetime('now', '-' || ? || ' days')")
            params.append(filters['active_since'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM users 
                WHERE {where_clause}
                ORDER BY last_active DESC
                LIMIT ? OFFSET ?
            """, (*params, limit, offset))
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
        
        # فیلتر کاربران با سفارش (در صورت درخواست)
        if filters.get('has_orders', False):
            filtered = []
            for user in results:
                count = get_user_orders_count(user['user_id'])
                if count > 0:
                    filtered.append(user)
            return filtered
        
        return results
    except Exception as e:
        log_database_error(
            f"Error in get_users_with_filter: {str(e)}",
            traceback=str(e)
        )
        return []


def get_users_with_filter_count(filters):
    """تعداد نتایج فیلتر کاربران"""
    try:
        conditions = []
        params = []
        
        if 'is_blocked' in filters:
            conditions.append("is_blocked = ?")
            params.append(1 if filters['is_blocked'] else 0)
        
        if 'role' in filters:
            conditions.append("role = ?")
            params.append(filters['role'])
        
        if 'active_since' in filters and filters['active_since'] > 0:
            conditions.append("last_active >= datetime('now', '-' || ? || ' days')")
            params.append(filters['active_since'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as count FROM users WHERE {where_clause}", params)
            row = cursor.fetchone()
            count = row['count'] if row else 0
        
        # فیلتر کاربران با سفارش
        if filters.get('has_orders', False):
            cursor.execute(f"SELECT user_id FROM users WHERE {where_clause}", params)
            users = cursor.fetchall()
            count = 0
            for user in users:
                if get_user_orders_count(user['user_id']) > 0:
                    count += 1
        
        return count
    except Exception as e:
        log_database_error(
            f"Error in get_users_with_filter_count: {str(e)}",
            traceback=str(e)
        )
        return 0


__all__ = [
    'upsert_user',
    'get_user',
    'get_all_users',
    'get_total_users',
    'get_active_users',
    'get_user_orders_count',
    'get_user_total_payment',
    'get_users_with_stats',
    'search_users',
    'block_user',
    'unblock_user',
    'is_user_blocked',
    'get_blocked_users',
    'get_blocked_count',
    'update_user_role',
    'get_user_role',
    'get_users_by_role',
    'get_user_by_username',
    'update_user_language',
    'update_user_timezone',
    'get_recent_users',
    'get_users_with_filter',
    'get_users_with_filter_count',
]