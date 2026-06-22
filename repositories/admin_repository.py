# repositories/admin_repository.py
# ریپازیتوری ادمین‌ها - مدیریت عملیات دیتابیس مربوط به ادمین‌ها

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime
from logger_config import logger
from .base_repository import BaseRepository
from models.enums import AdminRole
from utils.error_handler import log_database_error  # ✅ اضافه شد


class AdminRepository(BaseRepository):
    """ریپازیتوری ادمین‌ها - مدیریت عملیات دیتابیس مربوط به ادمین‌ها"""
    
    def __init__(self, connection):
        super().__init__(connection, 'admins', 'user_id')
    
    # ============================================================
    # متدهای پایه
    # ============================================================
    
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """دریافت ادمین بر اساس شناسه کاربر"""
        try:
            return super().get_by_id(user_id)
        except Exception as e:
            log_database_error(
                f"Error getting admin by id {user_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت تمام ادمین‌ها با صفحه‌بندی"""
        try:
            return super().get_all(limit, offset, order_by='added_at')
        except Exception as e:
            log_database_error(
                f"Error getting all admins: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_active(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت ادمین‌های فعال"""
        try:
            query = """
                SELECT * FROM admins 
                WHERE is_active = 1 
                ORDER BY added_at 
                LIMIT ? OFFSET ?
            """
            return self.custom_query(query, [limit, offset])
        except Exception as e:
            log_database_error(
                f"Error getting active admins: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_by_role(self, role: str) -> List[Dict[str, Any]]:
        """دریافت ادمین‌ها بر اساس نقش"""
        try:
            query = "SELECT * FROM admins WHERE role = ? ORDER BY added_at"
            return self.custom_query(query, [role])
        except Exception as e:
            log_database_error(
                f"Error getting admins by role {role}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    # ============================================================
    # عملیات اصلی مدیریت ادمین‌ها
    # ============================================================
    
    def is_admin(self, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر یک ادمین فعال است
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر ادمین فعال باشد
        """
        try:
            query = "SELECT 1 FROM admins WHERE user_id = ? AND is_active = 1"
            result = self.custom_query_one(query, [user_id])
            return result is not None
        except Exception as e:
            log_database_error(
                f"Error checking if user {user_id} is admin: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def exists(self, user_id: int) -> bool:
        """
        بررسی وجود ادمین در دیتابیس (صرف‌نظر از وضعیت فعال/غیرفعال)
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر در جدول admins وجود داشته باشد
        """
        try:
            return super().exists('user_id', user_id)
        except Exception as e:
            log_database_error(
                f"Error checking if admin {user_id} exists: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def add_admin(self, user_id: int, role: str = 'admin') -> bool:
        """
        افزودن یک کاربر جدید به لیست ادمین‌ها
        
        پارامترها:
            user_id: شناسه کاربر
            role: نقش کاربر (admin, manager, observer)
        
        بازگشت: True در صورت موفقیت، False اگر از قبل وجود داشته باشد
        """
        try:
            if role not in ['owner', 'admin', 'manager', 'observer']:
                role = 'admin'
            
            # بررسی وجود کاربر
            if self.exists(user_id):
                logger.warning(f"User {user_id} already exists in admins")
                return False
            
            data = {
                'user_id': user_id,
                'role': role,
                'is_active': 1,
                'added_at': datetime.now().isoformat()
            }
            return self.insert(data) is not None
        except Exception as e:
            log_database_error(
                f"Error adding admin {user_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def remove_admin(self, user_id: int) -> bool:
        """
        حذف کامل یک کاربر از لیست ادمین‌ها
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True در صورت موفقیت
        """
        try:
            # OWNER_ID نباید حذف شود (بررسی در لایه بالاتر انجام می‌شود)
            return self.delete(user_id)
        except Exception as e:
            log_database_error(
                f"Error removing admin {user_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_role(self, user_id: int, role: str) -> bool:
        """
        تغییر نقش یک ادمین
        
        پارامترها:
            user_id: شناسه کاربر
            role: نقش جدید (admin, manager, observer)
        
        بازگشت: True در صورت موفقیت
        """
        try:
            if role not in ['owner', 'admin', 'manager', 'observer']:
                return False
            
            return self.update(user_id, {'role': role})
        except Exception as e:
            log_database_error(
                f"Error updating role for admin {user_id} to {role}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def toggle_status(self, user_id: int) -> tuple:
        """
        تغییر وضعیت فعال/غیرفعال یک ادمین
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: (success, new_status) که success نشان‌دهنده موفقیت و new_status وضعیت جدید (0 یا 1) است.
        """
        try:
            admin = self.get_by_id(user_id)
            if not admin:
                return False, None
            
            new_status = 0 if admin.get('is_active', 1) == 1 else 1
            success = self.update(user_id, {'is_active': new_status})
            return success, new_status
        except Exception as e:
            log_database_error(
                f"Error toggling status for admin {user_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False, None
    
    def activate(self, user_id: int) -> bool:
        """فعال کردن یک ادمین"""
        try:
            return self.update(user_id, {'is_active': 1})
        except Exception as e:
            log_database_error(
                f"Error activating admin {user_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def deactivate(self, user_id: int) -> bool:
        """غیرفعال کردن یک ادمین"""
        try:
            return self.update(user_id, {'is_active': 0})
        except Exception as e:
            log_database_error(
                f"Error deactivating admin {user_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # جستجو و آمار
    # ============================================================
    
    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        جستجوی ادمین‌ها بر اساس شناسه کاربری یا نقش
        
        پارامترها:
            keyword: کلمه کلیدی برای جستجو
            limit: حداکثر تعداد نتایج
        
        بازگشت: لیست ادمین‌های یافت‌شده
        """
        try:
            if keyword.isdigit():
                query = """
                    SELECT * FROM admins 
                    WHERE user_id = ? OR role LIKE ? 
                    LIMIT ?
                """
                params = [int(keyword), f"%{keyword}%", limit]
            else:
                query = """
                    SELECT * FROM admins 
                    WHERE role LIKE ? 
                    LIMIT ?
                """
                params = [f"%{keyword}%", limit]
            
            return self.custom_query(query, params)
        except Exception as e:
            log_database_error(
                f"Error searching admins with keyword '{keyword}': {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی ادمین‌ها
        
        بازگشت: دیکشنری شامل:
            - total: تعداد کل ادمین‌ها
            - active: تعداد ادمین‌های فعال
            - inactive: تعداد ادمین‌های غیرفعال
            - roles: تفکیک نقش‌ها (دیکشنری نقش -> تعداد)
        """
        try:
            # تعداد کل
            query_total = "SELECT COUNT(*) as total FROM admins"
            total_result = self.custom_query_one(query_total)
            total = total_result.get('total', 0) if total_result else 0
            
            # تعداد فعال
            query_active = "SELECT COUNT(*) as active FROM admins WHERE is_active = 1"
            active_result = self.custom_query_one(query_active)
            active = active_result.get('active', 0) if active_result else 0
            
            # تفکیک نقش‌ها
            query_roles = "SELECT role, COUNT(*) as count FROM admins GROUP BY role"
            role_rows = self.custom_query(query_roles)
            roles = {row['role']: row['count'] for row in role_rows}
            
            return {
                'total': total,
                'active': active,
                'inactive': total - active,
                'roles': roles
            }
        except Exception as e:
            log_database_error(
                f"Error getting admin stats: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total': 0,
                'active': 0,
                'inactive': 0,
                'roles': {}
            }
    
    def count(self) -> int:
        """تعداد کل ادمین‌ها"""
        try:
            return super().count()
        except Exception as e:
            log_database_error(
                f"Error counting admins: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def count_active(self) -> int:
        """تعداد ادمین‌های فعال"""
        try:
            query = "SELECT COUNT(*) as count FROM admins WHERE is_active = 1"
            result = self.custom_query_one(query)
            return result.get('count', 0) if result else 0
        except Exception as e:
            log_database_error(
                f"Error counting active admins: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def count_by_role(self, role: str) -> int:
        """تعداد ادمین‌ها با نقش مشخص"""
        try:
            query = "SELECT COUNT(*) as count FROM admins WHERE role = ?"
            result = self.custom_query_one(query, [role])
            return result.get('count', 0) if result else 0
        except Exception as e:
            log_database_error(
                f"Error counting admins by role {role}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    def get_owners(self) -> List[Dict[str, Any]]:
        """دریافت ادمین‌های با نقش owner"""
        return self.get_by_role('owner')
    
    def get_admins(self) -> List[Dict[str, Any]]:
        """دریافت ادمین‌های با نقش admin"""
        return self.get_by_role('admin')
    
    def get_managers(self) -> List[Dict[str, Any]]:
        """دریافت ادمین‌های با نقش manager"""
        return self.get_by_role('manager')
    
    def get_observers(self) -> List[Dict[str, Any]]:
        """دریافت ادمین‌های با نقش observer"""
        return self.get_by_role('observer')
    
    def get_role(self, user_id: int) -> Optional[str]:
        """
        دریافت نقش یک کاربر
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: نقش کاربر یا None در صورت عدم وجود
        """
        try:
            admin = self.get_by_id(user_id)
            return admin.get('role') if admin else None
        except Exception as e:
            log_database_error(
                f"Error getting role for admin {user_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def is_active(self, user_id: int) -> bool:
        """
        بررسی فعال بودن ادمین
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر ادمین فعال باشد
        """
        try:
            admin = self.get_by_id(user_id)
            return admin.get('is_active', 0) == 1 if admin else False
        except Exception as e:
            log_database_error(
                f"Error checking if admin {user_id} is active: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def get_all_with_details(self) -> List[Dict[str, Any]]:
        """
        دریافت لیست تمام ادمین‌ها به همراه اطلاعات کامل
        
        بازگشت: لیست ادمین‌ها
        """
        try:
            return self.custom_query("SELECT * FROM admins ORDER BY added_at")
        except Exception as e:
            log_database_error(
                f"Error getting all admins with details: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_paginated(self, page: int = 0, per_page: int = 10) -> Dict[str, Any]:
        """
        دریافت لیست ادمین‌ها با صفحه‌بندی
        
        پارامترها:
            page: شماره صفحه (از ۰ شروع می‌شود)
            per_page: تعداد آیتم در هر صفحه
        
        بازگشت: دیکشنری شامل items, total, page, per_page
        """
        try:
            offset = page * per_page
            items = self.get_all(limit=per_page, offset=offset)
            total = self.count()
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page if total > 0 else 0
            }
        except Exception as e:
            log_database_error(
                f"Error getting paginated admins: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            }
    
    def update_added_at(self, user_id: int) -> bool:
        """به‌روزرسانی زمان افزودن ادمین (در صورت نیاز)"""
        try:
            return self.update(user_id, {'added_at': datetime.now().isoformat()})
        except Exception as e:
            log_database_error(
                f"Error updating added_at for admin {user_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False


__all__ = [
    'AdminRepository',
]