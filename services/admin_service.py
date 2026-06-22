# services/admin_service.py
# سرویس مدیریت ادمین‌ها - منطق کسب‌وکار مربوط به ادمین‌ها و نقش‌ها

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from logger_config import logger
from config import config
from repositories import AdminRepository
from services.user_service import UserService
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class AdminService:
    """سرویس مدیریت ادمین‌ها"""
    
    def __init__(self, connection, repository: Optional[AdminRepository] = None):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            repository: ریپازیتوری ادمین‌ها (اختیاری)
        """
        self._connection = connection
        self._repository = repository or AdminRepository(connection)
        self._user_service = UserService(connection)
        self._owner_id = config.OWNER_ID
    
    # ============================================================
    # عملیات پایه
    # ============================================================
    
    def get_admin(self, user_id: int) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات یک ادمین بر اساس شناسه کاربر"""
        return self._repository.get_by_id(user_id)
    
    def get_all_admins(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت لیست تمام ادمین‌ها با صفحه‌بندی"""
        return self._repository.get_all(limit, offset)
    
    def get_active_admins(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت لیست ادمین‌های فعال"""
        return self._repository.get_active(limit, offset)
    
    def get_admins_with_details(self) -> List[Dict[str, Any]]:
        """دریافت لیست تمام ادمین‌ها با نام کاربری و اطلاعات کامل"""
        admins = self._repository.get_all_with_details()
        result = []
        for admin in admins:
            admin_dict = dict(admin)
            # افزودن نام کاربر
            user = self._user_service.get_user(admin['user_id'])
            if user:
                admin_dict['username'] = user.get('username')
                admin_dict['first_name'] = user.get('first_name')
                admin_dict['last_name'] = user.get('last_name')
                admin_dict['display_name'] = self._user_service.get_user_display_name(admin['user_id'])
            else:
                admin_dict['display_name'] = str(admin['user_id'])
            result.append(admin_dict)
        return result
    
    def get_admin_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات یک ادمین بر اساس شناسه کاربر"""
        return self._repository.get_by_id(user_id)
    
    def get_admin_role(self, user_id: int) -> Optional[str]:
        """دریافت نقش یک کاربر در صورت ادمین بودن"""
        return self._repository.get_admin_role(user_id)
    
    def is_admin(self, user_id: int) -> bool:
        """بررسی ادمین بودن کاربر"""
        return self._repository.is_admin(user_id)
    
    def is_active(self, user_id: int) -> bool:
        """بررسی فعال بودن ادمین"""
        return self._repository.is_active(user_id)
    
    def is_owner(self, user_id: int) -> bool:
        """بررسی مالک بودن کاربر"""
        return user_id == self._owner_id
    
    def can_access_admin_panel(self, user_id: int) -> bool:
        """بررسی دسترسی کاربر به پنل مدیریت"""
        if self.is_owner(user_id):
            return True
        return self.is_admin(user_id)
    
    def admin_exists(self, user_id: int) -> bool:
        """بررسی وجود ادمین در دیتابیس"""
        return self._repository.exists(user_id)
    
    # ============================================================
    # مدیریت ادمین‌ها
    # ============================================================
    
    def add_admin(self, user_id: int, role: str = 'admin') -> bool:
        """
        افزودن یک کاربر جدید به لیست ادمین‌ها
        
        پارامترها:
            user_id: شناسه کاربر
            role: نقش کاربر (admin, manager, observer)
        
        بازگشت: True در صورت موفقیت
        """
        # بررسی اینکه کاربر از قبل ادمین نباشد
        if self.admin_exists(user_id):
            logger.warning(f"User {user_id} is already an admin")
            return False
        
        # بررسی اینکه کاربر در دیتابیس وجود داشته باشد
        user = self._user_service.get_user(user_id)
        if not user:
            logger.warning(f"User {user_id} not found in database")
            return False
        
        # افزودن ادمین
        try:
            return self._repository.add_admin(user_id, role)
        except Exception as e:
            log_database_error(
                f"Error adding admin {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def remove_admin(self, user_id: int) -> bool:
        """
        حذف کامل یک کاربر از لیست ادمین‌ها
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True در صورت موفقیت
        """
        # OWNER_ID نباید حذف شود
        if self.is_owner(user_id):
            logger.warning(f"Cannot remove OWNER_ID {user_id}")
            return False
        
        # بررسی وجود ادمین
        if not self.admin_exists(user_id):
            logger.warning(f"User {user_id} is not an admin")
            return False
        
        try:
            return self._repository.remove_admin(user_id)
        except Exception as e:
            log_database_error(
                f"Error removing admin {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
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
        # OWNER_ID نقشش قابل تغییر نیست
        if self.is_owner(user_id):
            logger.warning(f"Cannot change role of OWNER_ID {user_id}")
            return False
        
        # بررسی وجود ادمین
        if not self.admin_exists(user_id):
            logger.warning(f"User {user_id} is not an admin")
            return False
        
        try:
            return self._repository.update_role(user_id, role)
        except Exception as e:
            log_database_error(
                f"Error updating role for admin {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def toggle_status(self, user_id: int) -> tuple:
        """
        تغییر وضعیت فعال/غیرفعال یک ادمین
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: (success, new_status)
        """
        # OWNER_ID وضعیتش قابل تغییر نیست
        if self.is_owner(user_id):
            logger.warning(f"Cannot toggle status of OWNER_ID {user_id}")
            return False, None
        
        # بررسی وجود ادمین
        if not self.admin_exists(user_id):
            logger.warning(f"User {user_id} is not an admin")
            return False, None
        
        try:
            return self._repository.toggle_status(user_id)
        except Exception as e:
            log_database_error(
                f"Error toggling status for admin {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False, None
    
    def activate_admin(self, user_id: int) -> bool:
        """فعال کردن یک ادمین"""
        try:
            return self._repository.activate(user_id)
        except Exception as e:
            log_database_error(
                f"Error activating admin {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def deactivate_admin(self, user_id: int) -> bool:
        """غیرفعال کردن یک ادمین"""
        try:
            return self._repository.deactivate(user_id)
        except Exception as e:
            log_database_error(
                f"Error deactivating admin {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    # ============================================================
    # جستجو و آمار
    # ============================================================
    
    def search_admins(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        جستجوی ادمین‌ها بر اساس شناسه کاربری یا نقش
        
        پارامترها:
            keyword: کلمه کلیدی
            limit: حداکثر تعداد نتایج
        
        بازگشت: لیست ادمین‌های یافت‌شده
        """
        try:
            results = self._repository.search(keyword, limit)
            # افزودن نام کاربر به نتایج
            for admin in results:
                user = self._user_service.get_user(admin['user_id'])
                if user:
                    admin['display_name'] = self._user_service.get_user_display_name(admin['user_id'])
                else:
                    admin['display_name'] = str(admin['user_id'])
            return results
        except Exception as e:
            log_database_error(
                f"Error searching admins with keyword '{keyword}': {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی ادمین‌ها
        
        بازگشت: دیکشنری شامل total, active, inactive, roles
        """
        return self._repository.get_stats()
    
    def count_admins(self) -> int:
        """تعداد کل ادمین‌ها"""
        return self._repository.count()
    
    def count_active_admins(self) -> int:
        """تعداد ادمین‌های فعال"""
        return self._repository.count_active()
    
    def count_by_role(self, role: str) -> int:
        """تعداد ادمین‌ها با نقش مشخص"""
        return self._repository.count_admins_by_role(role)
    
    def get_owners(self) -> List[Dict[str, Any]]:
        """دریافت ادمین‌های با نقش owner"""
        return self._repository.get_owners()
    
    def get_admins(self) -> List[Dict[str, Any]]:
        """دریافت ادمین‌های با نقش admin"""
        return self._repository.get_admins()
    
    def get_managers(self) -> List[Dict[str, Any]]:
        """دریافت ادمین‌های با نقش manager"""
        return self._repository.get_managers()
    
    def get_observers(self) -> List[Dict[str, Any]]:
        """دریافت ادمین‌های با نقش observer"""
        return self._repository.get_observers()
    
    # ============================================================
    # متدهای کمکی برای پنل مدیریت
    # ============================================================
    
    def get_paginated_admins(self, page: int = 0, per_page: int = 10) -> Dict[str, Any]:
        """
        دریافت لیست ادمین‌ها با صفحه‌بندی و اطلاعات کامل
        
        پارامترها:
            page: شماره صفحه (از ۰ شروع می‌شود)
            per_page: تعداد آیتم در هر صفحه
        
        بازگشت: دیکشنری شامل items, total, page, per_page, total_pages
        """
        try:
            result = self._repository.get_paginated(page, per_page)
            
            # افزودن نام کاربر به هر ادمین
            for admin in result['items']:
                user = self._user_service.get_user(admin['user_id'])
                if user:
                    admin['display_name'] = self._user_service.get_user_display_name(admin['user_id'])
                else:
                    admin['display_name'] = str(admin['user_id'])
            
            return result
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
    
    def get_all_admin_ids(self) -> List[int]:
        """دریافت لیست شناسه‌های تمام ادمین‌ها"""
        try:
            admins = self.get_all_admins(limit=1000)
            return [admin['user_id'] for admin in admins]
        except Exception as e:
            log_database_error(
                f"Error getting all admin ids: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_admin_count_by_role(self, role: str) -> int:
        """تعداد ادمین‌ها با نقش مشخص"""
        return self.count_by_role(role)
    
    def is_last_admin(self, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر آخرین ادمین (به جز OWNER) است
        """
        if self.is_owner(user_id):
            return False
        
        try:
            active_admins = self.get_active_admins()
            # OWNER را از لیست حذف می‌کنیم
            non_owner_admins = [a for a in active_admins if a['user_id'] != self._owner_id]
            return len(non_owner_admins) <= 1 and non_owner_admins[0]['user_id'] == user_id if non_owner_admins else False
        except Exception as e:
            log_database_error(
                f"Error checking if user {user_id} is last admin: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def validate_role(self, role: str) -> bool:
        """بررسی معتبر بودن نقش"""
        return role in ['admin', 'manager', 'observer', 'owner']
    
    def get_role_label(self, role: str) -> str:
        """دریافت برچسب فارسی نقش"""
        labels = {
            'owner': '👑 مالک',
            'admin': '🛡️ ادمین',
            'manager': '📋 مدیر',
            'observer': '👁️ ناظر'
        }
        return labels.get(role, role)
    
    def get_status_label(self, is_active: bool) -> str:
        """دریافت برچسب فارسی وضعیت"""
        return "🟢 فعال" if is_active else "🔴 غیرفعال"
    
    def get_admin_permissions(self, user_id: int) -> List[str]:
        """
        دریافت مجوزهای یک ادمین
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: لیست مجوزها
        """
        try:
            if self.is_owner(user_id):
                return ['*']  # همه مجوزها
            
            admin = self.get_admin(user_id)
            if not admin:
                return []
            
            role = admin.get('role', 'admin')
            role_permissions = {
                'admin': [
                    'manage_orders', 'manage_buttons', 'manage_categories',
                    'manage_questions', 'view_analytics', 'manage_users',
                    'view_reports', 'export_data'
                ],
                'manager': [
                    'manage_orders', 'view_analytics', 'view_reports',
                    'export_data'
                ],
                'observer': [
                    'view_analytics', 'view_reports'
                ]
            }
            return role_permissions.get(role, [])
        except Exception as e:
            log_general_error(
                f"Error getting permissions for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return []
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """
        بررسی وجود مجوز برای ادمین
        
        پارامترها:
            user_id: شناسه کاربر
            permission: نام مجوز
        
        بازگشت: True اگر کاربر مجوز داشته باشد
        """
        if self.is_owner(user_id):
            return True
        
        permissions = self.get_admin_permissions(user_id)
        return permission in permissions
    
    def get_owners_count(self) -> int:
        """تعداد ادمین‌های با نقش owner"""
        return len(self.get_owners())
    
    def can_manage_admins(self, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر می‌تواند ادمین‌ها را مدیریت کند
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر مجوز مدیریت ادمین‌ها را داشته باشد
        """
        # فقط OWNER می‌تواند ادمین‌ها را مدیریت کند
        return self.is_owner(user_id)
    
    def get_admin_dashboard_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کامل برای داشبورد مدیریت
        
        بازگشت: دیکشنری شامل آمارهای مختلف
        """
        try:
            stats = self.get_stats()
            
            # تعداد کل کاربران ثبت‌شده
            total_users = self._user_service.get_total_users()
            
            # تعداد کاربران فعال امروز
            active_today = self._user_service.get_active_count(1)
            
            return {
                'total_admins': stats.get('total', 0),
                'active_admins': stats.get('active', 0),
                'inactive_admins': stats.get('inactive', 0),
                'roles': stats.get('roles', {}),
                'total_users': total_users,
                'active_today': active_today,
                'owners_count': len(self.get_owners()),
            }
        except Exception as e:
            log_general_error(
                f"Error getting admin dashboard stats: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total_admins': 0,
                'active_admins': 0,
                'inactive_admins': 0,
                'roles': {},
                'total_users': 0,
                'active_today': 0,
                'owners_count': 0,
            }
    
    def get_admin_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        دریافت ادمین بر اساس نام کاربری
        
        پارامترها:
            username: نام کاربری
        
        بازگشت: دیکشنری اطلاعات ادمین یا None
        """
        try:
            user = self._user_service.get_user_by_username(username)
            if not user:
                return None
            
            return self.get_admin(user['user_id'])
        except Exception as e:
            log_general_error(
                f"Error getting admin by username '{username}': {str(e)}",
                traceback=traceback.format_exc()
            )
            return None


__all__ = [
    'AdminService',
]