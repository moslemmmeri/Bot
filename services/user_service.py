# services/user_service.py
# سرویس مدیریت کاربران - منطق کسب‌وکار مربوط به کاربران

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from logger_config import logger
from repositories import UserRepository
from models.user import User, UserRole, UserStatus
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class UserService:
    """سرویس مدیریت کاربران"""
    
    def __init__(self, connection, repository: Optional[UserRepository] = None):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            repository: ریپازیتوری کاربران (اختیاری)
        """
        self._connection = connection
        self._repository = repository or UserRepository(connection)
    
    # ============================================================
    # عملیات پایه
    # ============================================================
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """دریافت کاربر بر اساس شناسه"""
        return self._repository.get_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """دریافت کاربر بر اساس نام کاربری"""
        return self._repository.get_by_username(username)
    
    def get_or_create_user(self, user_id: int, username: Optional[str] = None,
                           first_name: Optional[str] = None,
                           last_name: Optional[str] = None) -> Dict[str, Any]:
        """
        دریافت کاربر یا ایجاد آن در صورت عدم وجود
        
        بازگشت: دیکشنری اطلاعات کاربر
        """
        return self._repository.get_or_create(user_id, username, first_name, last_name)
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت تمام کاربران با صفحه‌بندی"""
        return self._repository.get_all(limit, offset)
    
    def get_total_users(self) -> int:
        """تعداد کل کاربران"""
        return self._repository.get_total_count()
    
    # ============================================================
    # مدیریت وضعیت کاربران
    # ============================================================
    
    def update_last_active(self, user_id: int) -> bool:
        """بروزرسانی زمان آخرین فعالیت کاربر"""
        return self._repository.update_last_active(user_id)
    
    def get_active_users(self, days: int = 1) -> List[Dict[str, Any]]:
        """دریافت کاربران فعال در تعداد روزهای اخیر"""
        return self._repository.get_active_users(days)
    
    def get_active_count(self, days: int = 1) -> int:
        """تعداد کاربران فعال در تعداد روزهای اخیر"""
        return self._repository.get_active_count(days)
    
    def get_blocked_users(self) -> List[Dict[str, Any]]:
        """دریافت لیست کاربران مسدود شده"""
        return self._repository.get_blocked_users()
    
    def get_blocked_count(self) -> int:
        """تعداد کاربران مسدود شده"""
        return self._repository.get_blocked_count()
    
    def block_user(self, user_id: int, reason: Optional[str] = None) -> bool:
        """مسدود کردن کاربر"""
        if user_id == self._get_owner_id():
            logger.warning(f"Cannot block owner user {user_id}")
            return False
        
        try:
            return self._repository.block_user(user_id, reason)
        except Exception as e:
            log_database_error(
                f"Error blocking user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def unblock_user(self, user_id: int) -> bool:
        """رفع مسدودیت کاربر"""
        try:
            return self._repository.unblock_user(user_id)
        except Exception as e:
            log_database_error(
                f"Error unblocking user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def is_blocked(self, user_id: int) -> bool:
        """بررسی مسدود بودن کاربر"""
        return self._repository.is_blocked(user_id)
    
    def _get_owner_id(self) -> int:
        """دریافت شناسه مالک"""
        from config import config
        return config.OWNER_ID
    
    # ============================================================
    # مدیریت نقش‌ها
    # ============================================================
    
    def update_role(self, user_id: int, role: int) -> bool:
        """تغییر نقش کاربر"""
        if user_id == self._get_owner_id():
            logger.warning(f"Cannot change role of owner user {user_id}")
            return False
        
        try:
            return self._repository.update_role(user_id, role)
        except Exception as e:
            log_database_error(
                f"Error updating role for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def get_user_role(self, user_id: int) -> Optional[str]:
        """دریافت نقش کاربر"""
        try:
            user = self.get_user(user_id)
            if not user:
                return None
            
            role_value = user.get('role', 0)
            try:
                return UserRole(role_value).name
            except:
                return None
        except Exception as e:
            log_general_error(
                f"Error getting user role for {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return None
    
    def is_admin(self, user_id: int) -> bool:
        """بررسی ادمین بودن کاربر (از جدول admins)"""
        from database import is_admin as db_is_admin
        return db_is_admin(user_id)
    
    def is_owner(self, user_id: int) -> bool:
        """بررسی مالک بودن کاربر"""
        return user_id == self._get_owner_id()
    
    # ============================================================
    # جستجو
    # ============================================================
    
    def search_users(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """جستجوی کاربران بر اساس کلمه کلیدی"""
        return self._repository.search(keyword, limit)
    
    def get_users_with_stats(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت کاربران با آمار سفارشات"""
        return self._repository.get_with_stats(limit, offset)
    
    def get_recent_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """دریافت کاربران جدید (اخیراً ثبت‌شده)"""
        return self._repository.get_recent_users(limit)
    
    def get_users_by_role(self, role: int) -> List[Dict[str, Any]]:
        """دریافت کاربران با نقش مشخص"""
        return self._repository.get_users_by_role(role)
    
    # ============================================================
    # آمار کاربران
    # ============================================================
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت آمار کامل یک کاربر
        
        بازگشت: دیکشنری شامل اطلاعات کاربر و آمار سفارشات
        """
        try:
            user = self.get_user(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # آمار سفارشات
            from services.order_service import OrderService
            order_service = OrderService(self._connection)
            order_stats = order_service.get_user_stats(user_id)
            
            # اطلاعات کاربر
            result = dict(user)
            result['orders_stats'] = order_stats
            
            return result
        except Exception as e:
            log_general_error(
                f"Error getting user stats for {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return {'error': str(e)}
    
    def get_users_summary(self) -> Dict[str, Any]:
        """
        دریافت خلاصه آمار کاربران برای داشبورد
        
        بازگشت: دیکشنری شامل آمار کلی کاربران
        """
        try:
            total = self.get_total_users()
            active_today = self.get_active_count(1)
            active_week = self.get_active_count(7)
            active_month = self.get_active_count(30)
            blocked = self.get_blocked_count()
            
            # تعداد کاربران با سفارش
            from services.order_service import OrderService
            order_service = OrderService(self._connection)
            stats = order_service.get_stats()
            users_with_orders = stats.get('total_users', 0)
            
            # کاربران با پرداخت
            users_with_payment = 0
            try:
                from database import get_db_connection
                query = """
                    SELECT COUNT(DISTINCT user_id) as count 
                    FROM dynamic_orders 
                    WHERE status IN ('paid', 'completed')
                """
                with self._connection.get_cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    users_with_payment = result.get('count', 0) if result else 0
            except Exception as e:
                log_database_error(
                    f"Error counting users with payment: {str(e)}",
                    traceback=traceback.format_exc()
                )
            
            # محاسبه نرخ رشد
            growth = 0
            if total > 0:
                yesterday = self.get_active_count(2) - active_today
                if yesterday > 0:
                    growth = ((active_today - yesterday) / yesterday) * 100
            
            return {
                'total_users': total,
                'active_today': active_today,
                'active_week': active_week,
                'active_month': active_month,
                'blocked_users': blocked,
                'users_with_orders': users_with_orders,
                'users_with_payment': users_with_payment,
                'growth_percent': round(growth, 1),
                'active_percent': round((active_today / total * 100) if total > 0 else 0, 1)
            }
        except Exception as e:
            log_general_error(
                f"Error getting users summary: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {}
    
    def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        دریافت کاربران برتر بر اساس تعداد سفارش یا مبلغ پرداختی
        
        پارامترها:
            limit: تعداد نتایج
        
        بازگشت: لیست کاربران برتر
        """
        try:
            from database import get_top_users as db_get_top_users
            return db_get_top_users(limit)
        except Exception as e:
            log_database_error(
                f"Error getting top users: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    # ============================================================
    # متدهای کمکی برای پنل مدیریت
    # ============================================================
    
    def get_username_suggestions(self, keyword: str, limit: int = 10) -> List[str]:
        """دریافت پیشنهادات نام کاربری برای جستجو"""
        return self._repository.get_username_suggestions(keyword, limit)
    
    def get_user_orders(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت سفارشات یک کاربر (با استفاده از OrderService)"""
        from services.order_service import OrderService
        order_service = OrderService(self._connection)
        return order_service.get_orders_by_user(user_id, limit)
    
    def get_user_orders_count(self, user_id: int) -> int:
        """تعداد سفارشات یک کاربر"""
        from services.order_service import OrderService
        order_service = OrderService(self._connection)
        return order_service.count_by_user(user_id)
    
    def get_user_total_payment(self, user_id: int) -> int:
        """مجموع مبلغ پرداختی یک کاربر"""
        from services.order_service import OrderService
        order_service = OrderService(self._connection)
        return order_service.calculate_total_amount(user_id)
    
    def get_user_status(self, user_id: int) -> str:
        """
        دریافت وضعیت کاربر به صورت رشته
        
        بازگشت: 'active', 'blocked', 'not_found'
        """
        try:
            user = self.get_user(user_id)
            if not user:
                return 'not_found'
            
            if user.get('is_blocked', 0) == 1:
                return 'blocked'
            
            return 'active'
        except Exception as e:
            log_general_error(
                f"Error getting user status for {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return 'not_found'
    
    def get_user_display_name(self, user_id: int) -> str:
        """
        دریافت نام قابل نمایش کاربر
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: نام کاربر یا 'کاربر ناشناس'
        """
        try:
            user = self.get_user(user_id)
            if not user:
                return 'کاربر ناشناس'
            
            first_name = user.get('first_name')
            last_name = user.get('last_name')
            username = user.get('username')
            
            if first_name and last_name:
                return f"{first_name} {last_name}"
            elif first_name:
                return first_name
            elif username:
                return f"@{username}"
            
            return f"کاربر {user_id}"
        except Exception as e:
            log_general_error(
                f"Error getting display name for {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return f"کاربر {user_id}"
    
    def get_user_by_id_or_username(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        دریافت کاربر بر اساس شناسه یا نام کاربری
        
        پارامترها:
            identifier: شناسه عددی یا نام کاربری (با یا بدون @)
        
        بازگشت: دیکشنری کاربر یا None
        """
        try:
            identifier = identifier.strip()
            
            # اگر عددی است، به عنوان user_id جستجو کن
            if identifier.isdigit():
                return self.get_user(int(identifier))
            
            # حذف @ از ابتدا
            username = identifier.lstrip('@')
            return self.get_user_by_username(username)
        except Exception as e:
            log_general_error(
                f"Error getting user by identifier {identifier}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_users_with_filter(self, filters: Dict[str, Any],
                              limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        دریافت کاربران با فیلترهای مختلف
        
        پارامترها:
            filters: دیکشنری فیلترها شامل:
                - is_blocked: True/False
                - has_orders: True/False
                - role: نقش
                - active_since: تعداد روزهای اخیر
            limit: تعداد نتایج
            offset: موقعیت شروع
        
        بازگشت: لیست کاربران
        """
        try:
            conditions = []
            params = []
            
            # فیلتر مسدود بودن
            if 'is_blocked' in filters:
                conditions.append("is_blocked = ?")
                params.append(1 if filters['is_blocked'] else 0)
            
            # فیلتر نقش
            if 'role' in filters:
                conditions.append("role = ?")
                params.append(filters['role'])
            
            # فیلتر فعالیت اخیر
            if 'active_since' in filters and filters['active_since'] > 0:
                conditions.append("last_active >= datetime('now', '-' || ? || ' days')")
                params.append(filters['active_since'])
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # کوئری پایه
            query = f"SELECT * FROM users WHERE {where_clause} ORDER BY last_active DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            results = self._repository.custom_query(query, params)
            
            # فیلتر کاربران با سفارش (در صورت درخواست)
            if filters.get('has_orders', False):
                from services.order_service import OrderService
                order_service = OrderService(self._connection)
                
                filtered = []
                for user in results:
                    count = order_service.count_by_user(user['user_id'])
                    if count > 0:
                        filtered.append(user)
                return filtered
            
            return results
        except Exception as e:
            log_general_error(
                f"Error getting users with filter: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_users_with_filter_count(self, filters: Dict[str, Any]) -> int:
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
            query = f"SELECT COUNT(*) as count FROM users WHERE {where_clause}"
            
            result = self._repository.custom_query_one(query, params)
            count = result.get('count', 0) if result else 0
            
            # فیلتر کاربران با سفارش
            if filters.get('has_orders', False):
                from services.order_service import OrderService
                order_service = OrderService(self._connection)
                users = self._repository.custom_query(f"SELECT user_id FROM users WHERE {where_clause}", params)
                count = 0
                for user in users:
                    if order_service.count_by_user(user['user_id']) > 0:
                        count += 1
            
            return count
        except Exception as e:
            log_general_error(
                f"Error getting users with filter count: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # متدهای امنیتی
    # ============================================================
    
    def can_user_access_admin(self, user_id: int) -> bool:
        """بررسی دسترسی کاربر به پنل مدیریت"""
        if self.is_owner(user_id):
            return True
        
        if self.is_admin(user_id):
            return True
        
        return False
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """دریافت مجوزهای یک کاربر"""
        try:
            if self.is_owner(user_id):
                return ['*']
            
            if self.is_admin(user_id):
                from database import get_user_role
                role = get_user_role(user_id)
                if role:
                    from models.enums import AdminRole
                    try:
                        admin_role = AdminRole.from_string(role)
                        return admin_role.permissions
                    except:
                        pass
            
            return []
        except Exception as e:
            log_general_error(
                f"Error getting user permissions for {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return []


__all__ = [
    'UserService',
]