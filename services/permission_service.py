# services/permission_service.py
# سرویس مجوزدهی (Permission Service)
# مدیریت دسترسی‌ها بر اساس نقش‌های کاربران
# جایگزین بررسی‌های مستقیم OWNER_ID در سراسر پروژه

import time
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import List, Optional, Set, Union
from enum import Enum
from logger_config import logger
from config import config
from database import is_admin, get_user_role, get_user
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class Permission(str, Enum):
    """مجوزهای قابل دسترسی در سیستم"""
    
    # مجوزهای عمومی
    VIEW_PROFILE = "view_profile"
    VIEW_ORDERS = "view_orders"
    
    # مجوزهای مدیریت کاربران
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    BLOCK_USERS = "block_users"
    UNBLOCK_USERS = "unblock_users"
    VIEW_USER_ACTIVITY = "view_user_activity"
    
    # مجوزهای مدیریت ادمین‌ها
    MANAGE_ADMINS = "manage_admins"
    VIEW_ADMINS = "view_admins"
    ADD_ADMIN = "add_admin"
    REMOVE_ADMIN = "remove_admin"
    CHANGE_ADMIN_ROLE = "change_admin_role"
    
    # مجوزهای مدیریت سفارشات
    MANAGE_ORDERS = "manage_orders"
    VIEW_ORDERS_ALL = "view_orders_all"
    CHANGE_ORDER_STATUS = "change_order_status"
    DELETE_ORDER = "delete_order"
    ADD_ORDER_NOTE = "add_order_note"
    EXPORT_ORDERS = "export_orders"
    
    # مجوزهای مدیریت دکمه‌ها
    MANAGE_BUTTONS = "manage_buttons"
    VIEW_BUTTONS = "view_buttons"
    CREATE_BUTTON = "create_button"
    EDIT_BUTTON = "edit_button"
    DELETE_BUTTON = "delete_button"
    MANAGE_CATEGORIES = "manage_categories"
    
    # مجوزهای مدیریت سوالات
    MANAGE_QUESTIONS = "manage_questions"
    VIEW_QUESTIONS = "view_questions"
    CREATE_QUESTION = "create_question"
    EDIT_QUESTION = "edit_question"
    DELETE_QUESTION = "delete_question"
    MANAGE_VALIDATION = "manage_validation"
    
    # مجوزهای مدیریت الگوها
    MANAGE_TEMPLATES = "manage_templates"
    VIEW_TEMPLATES = "view_templates"
    CREATE_TEMPLATE = "create_template"
    EDIT_TEMPLATE = "edit_template"
    DELETE_TEMPLATE = "delete_template"
    APPLY_TEMPLATE = "apply_template"
    
    # مجوزهای آمار و گزارش‌ها
    VIEW_ANALYTICS = "view_analytics"
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORTS = "export_reports"
    VIEW_CHARTS = "view_charts"
    
    # مجوزهای نسخه‌سازی
    MANAGE_VERSIONS = "manage_versions"
    VIEW_VERSIONS = "view_versions"
    CREATE_VERSION = "create_version"
    RESTORE_VERSION = "restore_version"
    DELETE_VERSION = "delete_version"
    
    # مجوزهای پشتیبان‌گیری
    MANAGE_BACKUP = "manage_backup"
    CREATE_BACKUP = "create_backup"
    RESTORE_BACKUP = "restore_backup"
    DELETE_BACKUP = "delete_backup"
    DOWNLOAD_BACKUP = "download_backup"
    
    # مجوزهای برندینگ
    MANAGE_BRANDING = "manage_branding"
    EDIT_BRANDING = "edit_branding"
    RESET_BRANDING = "reset_branding"
    
    # مجوزهای مدیریت خطاها
    MANAGE_ERRORS = "manage_errors"
    VIEW_ERRORS = "view_errors"
    RESOLVE_ERRORS = "resolve_errors"
    DELETE_ERRORS = "delete_errors"
    
    # مجوزهای تنظیمات
    MANAGE_SETTINGS = "manage_settings"
    EDIT_SETTINGS = "edit_settings"
    
    # مجوزهای ارسال پیام
    SEND_BROADCAST = "send_broadcast"
    SEND_NOTIFICATIONS = "send_notifications"
    
    # مجوزهای مدیریت ستون‌های منو
    MANAGE_COLUMNS = "manage_columns"
    EDIT_COLUMNS = "edit_columns"
    RESET_COLUMNS = "reset_columns"
    
    # مجوزهای ویژه
    FULL_ACCESS = "*"  # همه مجوزها


class Role(str, Enum):
    """نقش‌های کاربری در سیستم"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    OBSERVER = "observer"
    USER = "user"
    
    @classmethod
    def from_db_role(cls, role_value: Union[int, str]) -> 'Role':
        """تبدیل نقش از دیتابیس به Enum"""
        if isinstance(role_value, int):
            # نقش‌های عددی از جدول users (0=کاربر عادی، 1=ادمین، ...)
            role_map = {
                0: cls.USER,
                1: cls.ADMIN,
                2: cls.MANAGER,
                3: cls.OBSERVER,
                10: cls.OWNER,
            }
            return role_map.get(role_value, cls.USER)
        elif isinstance(role_value, str):
            # نقش‌های رشته‌ای از جدول admins
            role_map = {
                'owner': cls.OWNER,
                'admin': cls.ADMIN,
                'manager': cls.MANAGER,
                'observer': cls.OBSERVER,
                'user': cls.USER,
            }
            return role_map.get(role_value.lower(), cls.USER)
        return cls.USER
    
    def get_permissions(self) -> Set[Permission]:
        """دریافت مجوزهای مربوط به نقش"""
        permissions_map = {
            Role.OWNER: {Permission.FULL_ACCESS},
            Role.ADMIN: {
                Permission.VIEW_PROFILE,
                Permission.VIEW_ORDERS,
                Permission.MANAGE_ORDERS,
                Permission.VIEW_ORDERS_ALL,
                Permission.CHANGE_ORDER_STATUS,
                Permission.DELETE_ORDER,
                Permission.ADD_ORDER_NOTE,
                Permission.EXPORT_ORDERS,
                Permission.MANAGE_BUTTONS,
                Permission.VIEW_BUTTONS,
                Permission.CREATE_BUTTON,
                Permission.EDIT_BUTTON,
                Permission.DELETE_BUTTON,
                Permission.MANAGE_CATEGORIES,
                Permission.MANAGE_QUESTIONS,
                Permission.VIEW_QUESTIONS,
                Permission.CREATE_QUESTION,
                Permission.EDIT_QUESTION,
                Permission.DELETE_QUESTION,
                Permission.MANAGE_VALIDATION,
                Permission.MANAGE_TEMPLATES,
                Permission.VIEW_TEMPLATES,
                Permission.CREATE_TEMPLATE,
                Permission.EDIT_TEMPLATE,
                Permission.DELETE_TEMPLATE,
                Permission.APPLY_TEMPLATE,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_DASHBOARD,
                Permission.VIEW_REPORTS,
                Permission.EXPORT_REPORTS,
                Permission.VIEW_CHARTS,
                Permission.VIEW_USERS,
                Permission.BLOCK_USERS,
                Permission.UNBLOCK_USERS,
                Permission.VIEW_USER_ACTIVITY,
                Permission.MANAGE_VERSIONS,
                Permission.VIEW_VERSIONS,
                Permission.CREATE_VERSION,
                Permission.RESTORE_VERSION,
                Permission.DELETE_VERSION,
                Permission.MANAGE_BACKUP,
                Permission.CREATE_BACKUP,
                Permission.DOWNLOAD_BACKUP,
                Permission.MANAGE_BRANDING,
                Permission.EDIT_BRANDING,
                Permission.RESET_BRANDING,
                Permission.VIEW_ERRORS,
                Permission.RESOLVE_ERRORS,
                Permission.MANAGE_SETTINGS,
                Permission.EDIT_SETTINGS,
                Permission.SEND_BROADCAST,
                Permission.SEND_NOTIFICATIONS,
                Permission.MANAGE_COLUMNS,
                Permission.EDIT_COLUMNS,
                Permission.RESET_COLUMNS,
            },
            Role.MANAGER: {
                Permission.VIEW_PROFILE,
                Permission.VIEW_ORDERS,
                Permission.MANAGE_ORDERS,
                Permission.VIEW_ORDERS_ALL,
                Permission.CHANGE_ORDER_STATUS,
                Permission.ADD_ORDER_NOTE,
                Permission.EXPORT_ORDERS,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_DASHBOARD,
                Permission.VIEW_REPORTS,
                Permission.EXPORT_REPORTS,
                Permission.VIEW_CHARTS,
                Permission.VIEW_USERS,
                Permission.VIEW_USER_ACTIVITY,
                Permission.VIEW_VERSIONS,
                Permission.VIEW_BUTTONS,
                Permission.VIEW_QUESTIONS,
                Permission.VIEW_TEMPLATES,
                Permission.VIEW_ERRORS,
            },
            Role.OBSERVER: {
                Permission.VIEW_PROFILE,
                Permission.VIEW_ORDERS,
                Permission.VIEW_ORDERS_ALL,
                Permission.VIEW_ANALYTICS,
                Permission.VIEW_DASHBOARD,
                Permission.VIEW_REPORTS,
                Permission.VIEW_CHARTS,
                Permission.VIEW_USERS,
                Permission.VIEW_USER_ACTIVITY,
                Permission.VIEW_VERSIONS,
                Permission.VIEW_BUTTONS,
                Permission.VIEW_QUESTIONS,
                Permission.VIEW_TEMPLATES,
                Permission.VIEW_ERRORS,
            },
            Role.USER: {
                Permission.VIEW_PROFILE,
                Permission.VIEW_ORDERS,
            },
        }
        return permissions_map.get(self, set())
    
    def has_permission(self, permission: Permission) -> bool:
        """بررسی وجود مجوز برای نقش"""
        if self == Role.OWNER:
            return True
        return permission in self.get_permissions()
    
    @property
    def label(self) -> str:
        """برچسب فارسی نقش"""
        labels = {
            Role.OWNER: '👑 مالک',
            Role.ADMIN: '🛡️ ادمین',
            Role.MANAGER: '📋 مدیر',
            Role.OBSERVER: '👁️ ناظر',
            Role.USER: '👤 کاربر',
        }
        return labels.get(self, 'نامشخص')
    
    @property
    def priority(self) -> int:
        """اولویت نقش (عدد بزرگتر = دسترسی بیشتر)"""
        priorities = {
            Role.OWNER: 100,
            Role.ADMIN: 80,
            Role.MANAGER: 60,
            Role.OBSERVER: 40,
            Role.USER: 20,
        }
        return priorities.get(self, 0)


class PermissionService:
    """
    سرویس مجوزدهی (Permission Service)
    
    این سرویس مسئول بررسی دسترسی‌های کاربران بر اساس نقش‌های آنهاست.
    جایگزین بررسی‌های مستقیم `OWNER_ID` در سراسر پروژه.
    
    ویژگی‌ها:
    - مدیریت نقش‌های مختلف (owner, admin, manager, observer, user)
    - بررسی مجوزهای خاص (Permissions)
    - کش کردن نقش کاربران برای بهبود عملکرد
    - سازگاری با جداول `users` و `admins`
    - قابلیت گسترش نقش‌ها و مجوزها
    
    استفاده:
        permission_service = PermissionService()
        
        # بررسی دسترسی کلی به پنل مدیریت
        if await permission_service.can_access_admin(user_id):
            ...
        
        # بررسی مجوز خاص
        if await permission_service.has_permission(user_id, Permission.MANAGE_ORDERS):
            ...
        
        # بررسی مالک بودن
        if await permission_service.is_owner(user_id):
            ...
    """
    
    def __init__(self):
        """مقداردهی اولیه سرویس مجوزدهی"""
        self._owner_id = config.OWNER_ID
        self._cache: dict = {}  # کش ساده برای نقش‌ها {user_id: Role}
        self._cache_ttl: dict = {}  # زمان انقضای کش
        self._cache_duration = 300  # ۵ دقیقه
        
        logger.info("✅ PermissionService initialized")
    
    # ============================================================
    # متدهای اصلی بررسی مجوز
    # ============================================================
    
    async def has_permission(self, user_id: int, permission: Union[Permission, str]) -> bool:
        """
        بررسی وجود مجوز برای کاربر
        
        پارامترها:
            user_id: شناسه کاربر
            permission: مجوز مورد نظر (از نوع Permission یا رشته)
        
        بازگشت: True اگر کاربر مجوز داشته باشد
        """
        # مالک همیشه همه مجوزها را دارد
        if self.is_owner(user_id):
            return True
        
        # دریافت نقش کاربر
        role = await self._get_user_role(user_id)
        if not role:
            return False
        
        # تبدیل رشته به Permission اگر لازم باشد
        if isinstance(permission, str):
            try:
                permission = Permission(permission)
            except ValueError:
                logger.warning(f"Invalid permission string: {permission}")
                return False
        
        # بررسی مجوز
        return role.has_permission(permission)
    
    async def has_any_permission(self, user_id: int, permissions: List[Union[Permission, str]]) -> bool:
        """
        بررسی وجود حداقل یکی از مجوزها برای کاربر
        
        پارامترها:
            user_id: شناسه کاربر
            permissions: لیست مجوزها
        
        بازگشت: True اگر کاربر حداقل یکی از مجوزها را داشته باشد
        """
        for perm in permissions:
            if await self.has_permission(user_id, perm):
                return True
        return False
    
    async def has_all_permissions(self, user_id: int, permissions: List[Union[Permission, str]]) -> bool:
        """
        بررسی وجود همه‌ی مجوزها برای کاربر
        
        پارامترها:
            user_id: شناسه کاربر
            permissions: لیست مجوزها
        
        بازگشت: True اگر کاربر همه‌ی مجوزها را داشته باشد
        """
        for perm in permissions:
            if not await self.has_permission(user_id, perm):
                return False
        return True
    
    # ============================================================
    # متدهای دسترسی به پنل مدیریت
    # ============================================================
    
    async def can_access_admin(self, user_id: int) -> bool:
        """
        بررسی دسترسی کاربر به پنل مدیریت
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر به پنل مدیریت دسترسی داشته باشد
        """
        # مالک همیشه دسترسی دارد
        if self.is_owner(user_id):
            return True
        
        # ادمین‌های فعال از جدول admins
        if is_admin(user_id):
            return True
        
        # بررسی نقش‌های مجاز (admin, manager, observer)
        role = await self._get_user_role(user_id)
        if role in [Role.ADMIN, Role.MANAGER, Role.OBSERVER]:
            return True
        
        return False
    
    async def can_manage_admins(self, user_id: int) -> bool:
        """
        بررسی دسترسی کاربر برای مدیریت ادمین‌ها
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر بتواند ادمین‌ها را مدیریت کند
        """
        # فقط مالک می‌تواند ادمین‌ها را مدیریت کند
        return self.is_owner(user_id)
    
    async def can_manage_sensitive(self, user_id: int) -> bool:
        """
        بررسی دسترسی کاربر به بخش‌های حساس (پشتیبان‌گیری، تنظیمات، برندینگ، ...)
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر به بخش‌های حساس دسترسی داشته باشد
        """
        # مالک همیشه دسترسی دارد
        if self.is_owner(user_id):
            return True
        
        # فقط ادمین‌های کامل به بخش‌های حساس دسترسی دارند
        role = await self._get_user_role(user_id)
        return role in [Role.ADMIN, Role.OWNER]
    
    # ============================================================
    # متدهای بررسی نقش
    # ============================================================
    
    def is_owner(self, user_id: int) -> bool:
        """
        بررسی مالک بودن کاربر (بررسی مستقیم OWNER_ID)
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر مالک باشد
        """
        return user_id == self._owner_id
    
    async def is_admin(self, user_id: int) -> bool:
        """
        بررسی ادمین بودن کاربر (از جدول admins)
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر ادمین فعال باشد
        """
        # مالک همیشه ادمین است
        if self.is_owner(user_id):
            return True
        
        return is_admin(user_id)
    
    async def get_user_role(self, user_id: int) -> Optional[Role]:
        """
        دریافت نقش کاربر
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: نقش کاربر یا None در صورت عدم وجود
        """
        # مالک نقش OWNER دارد
        if self.is_owner(user_id):
            return Role.OWNER
        
        return await self._get_user_role(user_id)
    
    async def get_user_role_label(self, user_id: int) -> str:
        """
        دریافت برچسب فارسی نقش کاربر
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: برچسب نقش یا 'نامشخص'
        """
        role = await self.get_user_role(user_id)
        if role:
            return role.label
        return 'نامشخص'
    
    async def get_user_permissions(self, user_id: int) -> Set[Permission]:
        """
        دریافت لیست مجوزهای کاربر
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: مجموعه‌ای از مجوزها
        """
        # مالک همه مجوزها را دارد
        if self.is_owner(user_id):
            return {Permission.FULL_ACCESS}
        
        role = await self._get_user_role(user_id)
        if role:
            return role.get_permissions()
        
        return set()
    
    # ============================================================
    # متدهای سطح دسترسی (برای راحتی استفاده)
    # ============================================================
    
    async def can_view_users(self, user_id: int) -> bool:
        """بررسی دسترسی به مشاهده‌ی لیست کاربران"""
        return await self.has_permission(user_id, Permission.VIEW_USERS)
    
    async def can_manage_users(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت کاربران (مسدودیت، ...)"""
        return await self.has_permission(user_id, Permission.MANAGE_USERS)
    
    async def can_view_orders(self, user_id: int) -> bool:
        """بررسی دسترسی به مشاهده‌ی سفارشات"""
        return await self.has_permission(user_id, Permission.VIEW_ORDERS_ALL)
    
    async def can_manage_orders(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت سفارشات (تغییر وضعیت، ...)"""
        return await self.has_permission(user_id, Permission.MANAGE_ORDERS)
    
    async def can_manage_buttons(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت دکمه‌ها"""
        return await self.has_permission(user_id, Permission.MANAGE_BUTTONS)
    
    async def can_manage_questions(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت سوالات"""
        return await self.has_permission(user_id, Permission.MANAGE_QUESTIONS)
    
    async def can_view_analytics(self, user_id: int) -> bool:
        """بررسی دسترسی به مشاهده‌ی آمار و تحلیل"""
        return await self.has_permission(user_id, Permission.VIEW_ANALYTICS)
    
    async def can_manage_backup(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت پشتیبان‌گیری"""
        return await self.has_permission(user_id, Permission.MANAGE_BACKUP)
    
    async def can_manage_settings(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت تنظیمات"""
        return await self.has_permission(user_id, Permission.MANAGE_SETTINGS)
    
    async def can_manage_branding(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت برندینگ"""
        return await self.has_permission(user_id, Permission.MANAGE_BRANDING)
    
    async def can_send_broadcast(self, user_id: int) -> bool:
        """بررسی دسترسی به ارسال پیام انبوه"""
        return await self.has_permission(user_id, Permission.SEND_BROADCAST)
    
    async def can_manage_errors(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت خطاها"""
        return await self.has_permission(user_id, Permission.MANAGE_ERRORS)
    
    async def can_manage_versions(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت نسخه‌سازی"""
        return await self.has_permission(user_id, Permission.MANAGE_VERSIONS)
    
    async def can_manage_columns(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت ستون‌های منو"""
        return await self.has_permission(user_id, Permission.MANAGE_COLUMNS)
    
    async def can_manage_templates(self, user_id: int) -> bool:
        """بررسی دسترسی به مدیریت الگوها"""
        return await self.has_permission(user_id, Permission.MANAGE_TEMPLATES)
    
    # ============================================================
    # متدهای خصوصی (Private Methods)
    # ============================================================
    
    async def _get_user_role(self, user_id: int) -> Optional[Role]:
        """
        دریافت نقش کاربر از دیتابیس (با کش)
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: نقش کاربر یا None
        """
        # بررسی کش
        if user_id in self._cache:
            # بررسی انقضای کش
            if user_id in self._cache_ttl:
                if time.time() < self._cache_ttl[user_id]:
                    return self._cache[user_id]
                else:
                    # کش منقضی شده، حذف کن
                    del self._cache[user_id]
                    del self._cache_ttl[user_id]
        
        # دریافت نقش از دیتابیس
        try:
            # اول از جدول admins (نقش‌های رشته‌ای)
            from database import get_admin_role as db_get_admin_role
            admin_role = db_get_admin_role(user_id)
            if admin_role:
                role = Role.from_db_role(admin_role)
                self._cache[user_id] = role
                self._cache_ttl[user_id] = time.time() + self._cache_duration
                return role
            
            # اگر در admins نبود، از جدول users (نقش‌های عددی)
            user_role_value = get_user_role(user_id)
            if user_role_value is not None:
                role = Role.from_db_role(user_role_value)
                self._cache[user_id] = role
                self._cache_ttl[user_id] = time.time() + self._cache_duration
                return role
            
            # کاربر معمولی
            self._cache[user_id] = Role.USER
            self._cache_ttl[user_id] = time.time() + self._cache_duration
            return Role.USER
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error getting user role for {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return None
    
    def _clear_cache(self, user_id: Optional[int] = None):
        """
        پاک کردن کش نقش‌ها
        
        پارامترها:
            user_id: شناسه کاربر (در صورت عدم ارائه، همه‌ی کش پاک می‌شود)
        """
        if user_id:
            self._cache.pop(user_id, None)
            self._cache_ttl.pop(user_id, None)
        else:
            self._cache.clear()
            self._cache_ttl.clear()
        logger.debug(f"Permission cache cleared for user: {user_id or 'all'}")
    
    # ============================================================
    # متدهای آمار و اطلاعات
    # ============================================================
    
    def get_stats(self) -> dict:
        """
        دریافت آمار سرویس مجوزدهی
        
        بازگشت: دیکشنری آمار
        """
        return {
            'cache_size': len(self._cache),
            'owner_id': self._owner_id,
            'cache_duration': self._cache_duration,
        }
    
    def get_role_info(self, role: Union[Role, str]) -> dict:
        """
        دریافت اطلاعات یک نقش
        
        پارامترها:
            role: نقش (از نوع Role یا رشته)
        
        بازگشت: دیکشنری اطلاعات نقش
        """
        if isinstance(role, str):
            try:
                role = Role(role)
            except ValueError:
                return {'error': f'Invalid role: {role}'}
        
        return {
            'name': role.value,
            'label': role.label,
            'priority': role.priority,
            'permissions': [p.value for p in role.get_permissions()],
            'permission_count': len(role.get_permissions()),
        }
    
    def list_roles(self) -> List[dict]:
        """
        دریافت لیست تمام نقش‌ها با اطلاعات کامل
        
        بازگشت: لیست دیکشنری‌های اطلاعات نقش‌ها
        """
        return [
            {
                'name': role.value,
                'label': role.label,
                'priority': role.priority,
                'permission_count': len(role.get_permissions()),
                'is_default': role == Role.USER,
            }
            for role in Role
        ]
    
    def list_permissions(self, role: Optional[Union[Role, str]] = None) -> List[dict]:
        """
        دریافت لیست مجوزها (با فیلتر اختیاری بر اساس نقش)
        
        پارامترها:
            role: نقش (اختیاری) - در صورت ارائه، فقط مجوزهای آن نقش نمایش داده می‌شود
        
        بازگشت: لیست دیکشنری‌های اطلاعات مجوزها
        """
        if role:
            if isinstance(role, str):
                try:
                    role = Role(role)
                except ValueError:
                    return [{'error': f'Invalid role: {role}'}]
            permissions = role.get_permissions()
            return [
                {
                    'name': p.value,
                    'label': p.value.replace('_', ' ').title(),
                    'available_for': role.value,
                }
                for p in permissions
            ]
        
        # همه مجوزها
        all_perms = set()
        for r in Role:
            all_perms.update(r.get_permissions())
        
        return [
            {
                'name': p.value,
                'label': p.value.replace('_', ' ').title(),
            }
            for p in sorted(all_perms, key=lambda x: x.value)
        ]


# ============================================================
# توابع کمکی برای import مستقیم (برای سازگاری با کدهای قدیمی)
# ============================================================

def get_admin_role(user_id: int) -> Optional[str]:
    """دریافت نقش ادمین از دیتابیس (برای استفاده در PermissionService)"""
    from database import get_admin_role as db_get_admin_role
    return db_get_admin_role(user_id)


# ============================================================
# آبجکت سراسری (Singleton)
# ============================================================

_permission_service: Optional[PermissionService] = None


def get_permission_service() -> PermissionService:
    """
    دریافت آبجکت سراسری PermissionService (Singleton)
    
    بازگشت: نمونه‌ی PermissionService
    """
    global _permission_service
    if _permission_service is None:
        _permission_service = PermissionService()
    return _permission_service


# ============================================================
# توابع راحت‌تر برای استفاده در سایر بخش‌ها
# ============================================================

async def has_permission(user_id: int, permission: Union[Permission, str]) -> bool:
    """بررسی مجوز برای کاربر (تابع راحت)"""
    return await get_permission_service().has_permission(user_id, permission)


async def can_access_admin(user_id: int) -> bool:
    """بررسی دسترسی به پنل مدیریت (تابع راحت)"""
    return await get_permission_service().can_access_admin(user_id)


def is_owner(user_id: int) -> bool:
    """بررسی مالک بودن (تابع راحت)"""
    return get_permission_service().is_owner(user_id)


async def get_user_role(user_id: int) -> Optional[Role]:
    """دریافت نقش کاربر (تابع راحت)"""
    return await get_permission_service().get_user_role(user_id)


async def get_user_role_label(user_id: int) -> str:
    """دریافت برچسب نقش کاربر (تابع راحت)"""
    return await get_permission_service().get_user_role_label(user_id)


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # کلاس‌ها و Enumها
    'Permission',
    'Role',
    'PermissionService',
    
    # آبجکت سراسری
    'get_permission_service',
    
    # توابع راحت
    'has_permission',
    'can_access_admin',
    'is_owner',
    'get_user_role',
    'get_user_role_label',
]