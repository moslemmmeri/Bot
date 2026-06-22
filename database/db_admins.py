# database/db_admins.py
# مدیریت ادمین‌ها - شامل: بررسی، افزودن، حذف، به‌روزرسانی نقش، تغییر وضعیت و آمار ادمین‌ها
# اصلاح شده با مدیریت خطا و لاگ‌گیری کامل در دیتابیس

from logger_config import logger
from .db_connection import get_db_connection
from utils.error_handler import log_database_error, log_general_error


def is_admin(user_id):
    """
    بررسی اینکه آیا کاربر با شناسه داده‌شده یک ادمین فعال است یا خیر.
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True اگر کاربر ادمین فعال باشد، در غیر این صورت False
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id = ? AND is_active = 1", (user_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        log_database_error(
            f"Error in is_admin for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def add_admin(user_id, role='admin'):
    """
    افزودن یک کاربر جدید به لیست ادمین‌ها.
    
    پارامترها:
        user_id: شناسه کاربر
        role: نقش کاربر (admin, manager, observer) - پیش‌فرض admin
    
    بازگشت: True اگر کاربر با موفقیت اضافه شود، False اگر از قبل وجود داشته باشد
    """
    try:
        if role not in ['owner', 'admin', 'manager', 'observer']:
            role = 'admin'
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO admins (user_id, role, is_active) VALUES (?, ?, 1)",
                (user_id, role)
            )
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"✅ کاربر {user_id} با نقش {role} به لیست ادمین‌ها اضافه شد.")
                return True
            else:
                logger.warning(f"⚠️ کاربر {user_id} از قبل در لیست ادمین‌ها وجود دارد.")
                return False
    except Exception as e:
        log_database_error(
            f"Error in add_admin for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def remove_admin(user_id):
    """
    حذف کامل یک کاربر از لیست ادمین‌ها.
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True اگر کاربر با موفقیت حذف شود، False در غیر این صورت
    
    توجه: OWNER_ID قابل حذف نیست.
    """
    try:
        from config import config
        OWNER_ID = config.OWNER_ID
        if user_id == OWNER_ID:
            logger.warning(f"⚠️ تلاش برای حذف OWNER_ID ({user_id}) ناموفق بود.")
            return False
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"🗑️ کاربر {user_id} از لیست ادمین‌ها حذف شد.")
                return True
            return False
    except Exception as e:
        log_database_error(
            f"Error in remove_admin for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def get_all_admins():
    """
    دریافت لیست تمام ادمین‌ها (فعال و غیرفعال) به همراه اطلاعات کامل.
    
    بازگشت: لیست دیکشنری‌های ادمین‌ها
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, role, is_active, added_at FROM admins ORDER BY added_at")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_all_admins: {str(e)}",
            traceback=str(e)
        )
        return []


def get_active_admins():
    """
    دریافت لیست ادمین‌های فعال.
    
    بازگشت: لیست دیکشنری‌های ادمین‌های فعال
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, role, added_at FROM admins WHERE is_active = 1 ORDER BY added_at")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_active_admins: {str(e)}",
            traceback=str(e)
        )
        return []


def update_admin_role(user_id, role):
    """
    تغییر نقش یک ادمین.
    
    پارامترها:
        user_id: شناسه کاربر
        role: نقش جدید (admin, manager, observer)
    
    بازگشت: True در صورت موفقیت، False در غیر این صورت
    
    توجه: نقش OWNER_ID قابل تغییر نیست.
    """
    try:
        if role not in ['owner', 'admin', 'manager', 'observer']:
            return False
        
        from config import config
        OWNER_ID = config.OWNER_ID
        if user_id == OWNER_ID and role != 'owner':
            logger.warning(f"⚠️ نمی‌توان نقش OWNER_ID را تغییر داد.")
            return False
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE admins SET role = ? WHERE user_id = ?", (role, user_id))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"✅ نقش کاربر {user_id} به {role} تغییر یافت.")
                return True
            return False
    except Exception as e:
        log_database_error(
            f"Error in update_admin_role for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def toggle_admin_status(user_id):
    """
    تغییر وضعیت فعال/غیرفعال یک ادمین.
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: (success, new_status) که success نشان‌دهنده موفقیت و new_status وضعیت جدید (0 یا 1) است.
    
    توجه: وضعیت OWNER_ID قابل تغییر نیست.
    """
    try:
        from config import config
        OWNER_ID = config.OWNER_ID
        if user_id == OWNER_ID:
            logger.warning(f"⚠️ نمی‌توان وضعیت OWNER_ID را تغییر داد.")
            return False, None
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_active FROM admins WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False, None
            
            new_status = 0 if row['is_active'] == 1 else 1
            cursor.execute("UPDATE admins SET is_active = ? WHERE user_id = ?", (new_status, user_id))
            conn.commit()
            status_text = "فعال" if new_status == 1 else "غیرفعال"
            logger.info(f"✅ وضعیت کاربر {user_id} به {status_text} تغییر یافت.")
            return True, new_status
    except Exception as e:
        log_database_error(
            f"Error in toggle_admin_status for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False, None


def activate_admin(user_id):
    """
    فعال کردن یک ادمین (تنظیم is_active = 1)
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True در صورت موفقیت
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE admins SET is_active = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"✅ کاربر {user_id} فعال شد.")
                return True
            return False
    except Exception as e:
        log_database_error(
            f"Error in activate_admin for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def deactivate_admin(user_id):
    """
    غیرفعال کردن یک ادمین (تنظیم is_active = 0)
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True در صورت موفقیت
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE admins SET is_active = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"✅ کاربر {user_id} غیرفعال شد.")
                return True
            return False
    except Exception as e:
        log_database_error(
            f"Error in deactivate_admin for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


def get_admin_stats():
    """
    دریافت آمار کلی ادمین‌ها.
    
    بازگشت: دیکشنری شامل:
        - total: تعداد کل ادمین‌ها
        - active: تعداد ادمین‌های فعال
        - inactive: تعداد ادمین‌های غیرفعال
        - roles: تفکیک نقش‌ها (دیکشنری نقش -> تعداد)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM admins")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as active FROM admins WHERE is_active = 1")
            active = cursor.fetchone()['active']
            
            cursor.execute("SELECT role, COUNT(*) as count FROM admins GROUP BY role")
            role_rows = cursor.fetchall()
            roles = {row['role']: row['count'] for row in role_rows}
            
            return {
                'total': total,
                'active': active,
                'inactive': total - active,
                'roles': roles
            }
    except Exception as e:
        log_database_error(
            f"Error in get_admin_stats: {str(e)}",
            traceback=str(e)
        )
        return {
            'total': 0,
            'active': 0,
            'inactive': 0,
            'roles': {}
        }


def search_admins(keyword, limit=20):
    """
    جستجوی ادمین‌ها بر اساس شناسه کاربری یا نقش.
    
    پارامترها:
        keyword: کلمه کلیدی برای جستجو
        limit: حداکثر تعداد نتایج
    
    بازگشت: لیست دیکشنری‌های ادمین‌های یافت‌شده
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if keyword.isdigit():
                cursor.execute(
                    "SELECT user_id, role, is_active, added_at FROM admins WHERE user_id LIKE ? OR role LIKE ? LIMIT ?",
                    (f"%{keyword}%", f"%{keyword}%", limit)
                )
            else:
                cursor.execute(
                    "SELECT user_id, role, is_active, added_at FROM admins WHERE role LIKE ? LIMIT ?",
                    (f"%{keyword}%", limit)
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in search_admins with keyword '{keyword}': {str(e)}",
            traceback=str(e)
        )
        return []


def get_admin_by_user_id(user_id):
    """
    دریافت اطلاعات یک ادمین بر اساس شناسه کاربر.
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: دیکشنری اطلاعات ادمین یا None
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, role, is_active, added_at FROM admins WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log_database_error(
            f"Error in get_admin_by_user_id for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return None


def get_admin_role(user_id):
    """
    دریافت نقش یک کاربر در صورت ادمین بودن.
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: نقش کاربر یا None در صورت عدم وجود
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM admins WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row['role'] if row else None
    except Exception as e:
        log_database_error(
            f"Error in get_admin_role for user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return None


def count_admins():
    """
    تعداد کل ادمین‌ها.
    
    بازگشت: تعداد ادمین‌ها
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM admins")
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(
            f"Error in count_admins: {str(e)}",
            traceback=str(e)
        )
        return 0


def count_active_admins():
    """
    تعداد ادمین‌های فعال.
    
    بازگشت: تعداد ادمین‌های فعال
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM admins WHERE is_active = 1")
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(
            f"Error in count_active_admins: {str(e)}",
            traceback=str(e)
        )
        return 0


def count_admins_by_role(role):
    """
    تعداد ادمین‌ها با نقش مشخص.
    
    پارامترها:
        role: نقش (admin, manager, observer, owner)
    
    بازگشت: تعداد ادمین‌ها
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM admins WHERE role = ?", (role,))
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(
            f"Error in count_admins_by_role for role '{role}': {str(e)}",
            traceback=str(e)
        )
        return 0


def get_owners():
    """
    دریافت ادمین‌های با نقش owner.
    
    بازگشت: لیست دیکشنری‌های ادمین‌های owner
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE role = 'owner' ORDER BY added_at")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_owners: {str(e)}",
            traceback=str(e)
        )
        return []


def get_managers():
    """
    دریافت ادمین‌های با نقش manager.
    
    بازگشت: لیست دیکشنری‌های ادمین‌های manager
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE role = 'manager' ORDER BY added_at")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_managers: {str(e)}",
            traceback=str(e)
        )
        return []


def get_observers():
    """
    دریافت ادمین‌های با نقش observer.
    
    بازگشت: لیست دیکشنری‌های ادمین‌های observer
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE role = 'observer' ORDER BY added_at")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in get_observers: {str(e)}",
            traceback=str(e)
        )
        return []


__all__ = [
    'is_admin',
    'add_admin',
    'remove_admin',
    'get_all_admins',
    'get_active_admins',
    'update_admin_role',
    'toggle_admin_status',
    'activate_admin',
    'deactivate_admin',
    'get_admin_stats',
    'search_admins',
    'get_admin_by_user_id',
    'get_admin_role',
    'count_admins',
    'count_active_admins',
    'count_admins_by_role',
    'get_owners',
    'get_managers',
    'get_observers',
]