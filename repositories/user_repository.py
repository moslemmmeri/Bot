# repositories/user_repository.py
# ریپازیتوری کاربر

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from logger_config import logger
from .base_repository import BaseRepository
from models.user import User, UserRole, UserStatus
from utils.error_handler import log_database_error  # ✅ اضافه شد


class UserRepository(BaseRepository):
    """ریپازیتوری کاربر - مدیریت عملیات دیتابیس مربوط به کاربران"""
    
    def __init__(self, connection):
        super().__init__(connection, 'users', 'user_id')
    
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """دریافت کاربر بر اساس شناسه"""
        return super().get_by_id(user_id)
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """دریافت کاربر بر اساس نام کاربری"""
        return self.get_by_field('username', username)
    
    def get_or_create(self, user_id: int, username: Optional[str] = None,
                      first_name: Optional[str] = None,
                      last_name: Optional[str] = None) -> Dict[str, Any]:
        """
        دریافت کاربر یا ایجاد آن در صورت عدم وجود
        
        بازگشت: دیکشنری اطلاعات کاربر
        """
        user = self.get_by_id(user_id)
        if user:
            # به‌روزرسانی اطلاعات در صورت تغییر
            update_data = {}
            if username and user.get('username') != username:
                update_data['username'] = username
            if first_name and user.get('first_name') != first_name:
                update_data['first_name'] = first_name
            if last_name and user.get('last_name') != last_name:
                update_data['last_name'] = last_name
            
            if update_data:
                update_data['last_active'] = datetime.now().isoformat()
                self.update(user_id, update_data)
                user = self.get_by_id(user_id)
            
            return user
        
        # ایجاد کاربر جدید
        now = datetime.now().isoformat()
        data = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'first_seen': now,
            'last_active': now,
            'role': UserRole.USER.value,
            'status': UserStatus.ACTIVE.value,
            'is_blocked': 0,
        }
        
        self.insert(data)
        return self.get_by_id(user_id)
    
    def update_last_active(self, user_id: int) -> bool:
        """بروزرسانی زمان آخرین فعالیت کاربر"""
        return self.update(user_id, {
            'last_active': datetime.now().isoformat()
        })
    
    def get_active_users(self, days: int = 1) -> List[Dict[str, Any]]:
        """
        دریافت کاربران فعال در تعداد روزهای اخیر
        
        پارامترها:
            days: تعداد روزهای اخیر
        
        بازگشت: لیست کاربران فعال
        """
        query = """
            SELECT * FROM users 
            WHERE last_active >= datetime('now', '-' || ? || ' days')
            AND is_blocked = 0
            ORDER BY last_active DESC
        """
        return self.custom_query(query, [days])
    
    def get_active_count(self, days: int = 1) -> int:
        """تعداد کاربران فعال در تعداد روزهای اخیر"""
        query = """
            SELECT COUNT(*) as count FROM users 
            WHERE last_active >= datetime('now', '-' || ? || ' days')
            AND is_blocked = 0
        """
        result = self.custom_query_one(query, [days])
        return result.get('count', 0) if result else 0
    
    def get_blocked_users(self) -> List[Dict[str, Any]]:
        """دریافت لیست کاربران مسدود شده"""
        query = """
            SELECT * FROM users 
            WHERE is_blocked = 1 
            ORDER BY blocked_at DESC
        """
        return self.custom_query(query)
    
    def block_user(self, user_id: int, reason: Optional[str] = None) -> bool:
        """مسدود کردن کاربر"""
        return self.update(user_id, {
            'is_blocked': 1,
            'blocked_at': datetime.now().isoformat(),
            'block_reason': reason or 'مسدود شده توسط ادمین'
        })
    
    def unblock_user(self, user_id: int) -> bool:
        """رفع مسدودیت کاربر"""
        return self.update(user_id, {
            'is_blocked': 0,
            'blocked_at': None,
            'block_reason': None
        })
    
    def is_blocked(self, user_id: int) -> bool:
        """بررسی مسدود بودن کاربر"""
        user = self.get_by_id(user_id)
        return user.get('is_blocked', 0) == 1 if user else False
    
    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        جستجوی کاربران بر اساس کلمه کلیدی
        
        پارامترها:
            keyword: کلمه کلیدی (شناسه، نام کاربری، نام)
            limit: حداکثر تعداد نتایج
        
        بازگشت: لیست کاربران یافت‌شده
        """
        if keyword.isdigit():
            query = """
                SELECT * FROM users 
                WHERE user_id LIKE ? OR username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
                LIMIT ?
            """
            params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit]
        else:
            query = """
                SELECT * FROM users 
                WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
                LIMIT ?
            """
            params = [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit]
        
        return self.custom_query(query, params)
    
    def get_with_stats(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        دریافت لیست کاربران به همراه آمار سفارشات
        
        پارامترها:
            limit: تعداد کاربران
            offset: موقعیت شروع
        
        بازگشت: لیست کاربران با فیلدهای orders_count و total_payment
        """
        query = """
            SELECT 
                u.*,
                COUNT(o.id) AS orders_count,
                COALESCE(SUM(o.payment_amount), 0) AS total_payment
            FROM users u
            LEFT JOIN dynamic_orders o ON u.user_id = o.user_id AND o.status IN ('paid', 'completed')
            GROUP BY u.user_id
            ORDER BY u.last_active DESC
            LIMIT ? OFFSET ?
        """
        return self.custom_query(query, [limit, offset])
    
    def get_total_count(self) -> int:
        """تعداد کل کاربران"""
        return self.count()
    
    def get_blocked_count(self) -> int:
        """تعداد کاربران مسدود شده"""
        query = "SELECT COUNT(*) as count FROM users WHERE is_blocked = 1"
        result = self.custom_query_one(query)
        return result.get('count', 0) if result else 0
    
    def get_user_orders_stats(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت آمار سفارشات یک کاربر
        
        بازگشت: دیکشنری شامل total_orders, total_amount, avg_amount, statuses
        """
        query = """
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(payment_amount), 0) as total_amount,
                COALESCE(AVG(payment_amount), 0) as avg_amount
            FROM dynamic_orders 
            WHERE user_id = ?
        """
        stats = self.custom_query_one(query, [user_id]) or {}
        
        # تفکیک وضعیت‌ها
        status_query = """
            SELECT status, COUNT(*) as count 
            FROM dynamic_orders 
            WHERE user_id = ? 
            GROUP BY status
        """
        statuses = self.custom_query(status_query, [user_id])
        stats['statuses'] = statuses
        
        return stats
    
    def get_recent_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """دریافت کاربران جدید (اخیراً ثبت‌شده)"""
        query = """
            SELECT * FROM users 
            ORDER BY first_seen DESC 
            LIMIT ?
        """
        return self.custom_query(query, [limit])
    
    def get_users_by_role(self, role: int) -> List[Dict[str, Any]]:
        """دریافت کاربران با نقش مشخص"""
        query = "SELECT * FROM users WHERE role = ? ORDER BY user_id"
        return self.custom_query(query, [role])
    
    def update_role(self, user_id: int, role: int) -> bool:
        """تغییر نقش کاربر"""
        return self.update(user_id, {'role': role})
    
    def get_username_suggestions(self, keyword: str, limit: int = 10) -> List[str]:
        """دریافت پیشنهادات نام کاربری برای جستجو"""
        query = """
            SELECT username FROM users 
            WHERE username LIKE ? 
            LIMIT ?
        """
        results = self.custom_query(query, [f"%{keyword}%", limit])
        return [r.get('username') for r in results if r.get('username')]


__all__ = [
    'UserRepository',
]