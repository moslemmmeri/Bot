# models/user.py
# مدل کاربر

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum, IntEnum


class UserRole(IntEnum):
    """نقش‌های کاربری"""
    USER = 0          # کاربر عادی
    ADMIN = 1         # ادمین
    MANAGER = 2       # مدیر
    OBSERVER = 3      # ناظر
    OWNER = 10        # مالک


class UserStatus(IntEnum):
    """وضعیت کاربر"""
    ACTIVE = 0        # فعال
    BLOCKED = 1       # مسدود شده
    DELETED = 2       # حذف شده


@dataclass
class User:
    """مدل کاربر"""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    is_blocked: bool = False
    block_reason: Optional[str] = None
    blocked_at: Optional[datetime] = None
    first_seen: Optional[datetime] = None
    last_active: Optional[datetime] = None
    language: str = "fa"
    timezone: str = "Asia/Tehran"
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """نام کامل کاربر"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username or str(self.user_id)
    
    @property
    def display_name(self) -> str:
        """نام قابل نمایش"""
        return self.full_name or self.username or f"کاربر {self.user_id}"
    
    @property
    def is_admin(self) -> bool:
        """آیا کاربر ادمین است"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.OWNER]
    
    @property
    def is_owner(self) -> bool:
        """آیا کاربر مالک است"""
        return self.role == UserRole.OWNER
    
    @property
    def is_active(self) -> bool:
        """آیا کاربر فعال است"""
        return self.status == UserStatus.ACTIVE and not self.is_blocked
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'User':
        """ایجاد از دیکشنری دیتابیس"""
        return cls(
            user_id=data.get('user_id', 0),
            username=data.get('username'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=UserRole(data.get('role', 0)),
            status=UserStatus(data.get('status', 0)),
            is_blocked=bool(data.get('is_blocked', 0)),
            block_reason=data.get('block_reason'),
            blocked_at=data.get('blocked_at'),
            first_seen=data.get('first_seen'),
            last_active=data.get('last_active'),
            language=data.get('language', 'fa'),
            timezone=data.get('timezone', 'Asia/Tehran'),
            extra_data=data.get('extra_data', {})
        )
    
    def to_db(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای ذخیره در دیتابیس"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value,
            'status': self.status.value,
            'is_blocked': 1 if self.is_blocked else 0,
            'block_reason': self.block_reason,
            'blocked_at': self.blocked_at,
            'first_seen': self.first_seen,
            'last_active': self.last_active,
            'language': self.language,
            'timezone': self.timezone,
            'extra_data': self.extra_data
        }
    
    def block(self, reason: Optional[str] = None) -> None:
        """مسدود کردن کاربر"""
        self.is_blocked = True
        self.block_reason = reason
        self.blocked_at = datetime.now()
    
    def unblock(self) -> None:
        """رفع مسدودیت کاربر"""
        self.is_blocked = False
        self.block_reason = None
        self.blocked_at = None
    
    def update_activity(self) -> None:
        """بروزرسانی زمان آخرین فعالیت"""
        self.last_active = datetime.now()
    
    def has_permission(self, permission: str) -> bool:
        """
        بررسی وجود مجوز برای کاربر
        
        پارامترها:
            permission: نام مجوز
        
        بازگشت: True اگر کاربر مجوز داشته باشد
        """
        if self.is_owner:
            return True
        
        # نقشه نقش‌ها به مجوزها
        role_permissions = {
            UserRole.ADMIN: [
                'manage_orders', 'manage_buttons', 'manage_categories',
                'manage_questions', 'view_analytics', 'manage_users',
                'manage_admins', 'view_reports', 'export_data'
            ],
            UserRole.MANAGER: [
                'manage_orders', 'view_analytics', 'view_reports',
                'export_data'
            ],
            UserRole.OBSERVER: [
                'view_analytics', 'view_reports'
            ]
        }
        
        permissions = role_permissions.get(self.role, [])
        return permission in permissions


# ============================================================
# توابع کمکی برای کار با کاربران
# ============================================================

def create_user(user_id: int, username: Optional[str] = None,
                first_name: Optional[str] = None,
                last_name: Optional[str] = None) -> User:
    """ایجاد کاربر جدید"""
    now = datetime.now()
    return User(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        first_seen=now,
        last_active=now
    )


__all__ = [
    'User',
    'UserRole',
    'UserStatus',
    'create_user',
]