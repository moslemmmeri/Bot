# dto/user_dto.py
# Data Transfer Object برای کاربران

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class UserDTO:
    """
    Data Transfer Object برای کاربران
    برای انتقال داده بین لایه‌های مختلف بدون وابستگی به مدل‌های دیتابیس
    """
    user_id: int = 0
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str = ""
    display_name: str = ""
    role: str = "user"
    role_label: str = "👤 کاربر"
    status: str = "active"
    status_label: str = "🟢 فعال"
    is_blocked: bool = False
    block_reason: Optional[str] = None
    blocked_at: Optional[str] = None
    first_seen: Optional[str] = None
    last_active: Optional[str] = None
    language: str = "fa"
    timezone: str = "Asia/Tehran"
    orders_count: int = 0
    total_payment: int = 0
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'UserDTO':
        """ایجاد از دیکشنری دیتابیس"""
        from models.user import User
        
        user = User.from_db(data)
        
        return cls(
            user_id=user.user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            display_name=user.display_name,
            role=user.role.name.lower(),
            role_label=user.role.label if hasattr(user.role, 'label') else "👤 کاربر",
            status="active" if user.is_active else "blocked" if user.is_blocked else "deleted",
            status_label="🟢 فعال" if user.is_active else "🔴 مسدود شده" if user.is_blocked else "🗑️ حذف شده",
            is_blocked=user.is_blocked,
            block_reason=user.block_reason,
            blocked_at=user.blocked_at.strftime("%Y-%m-%d %H:%M") if user.blocked_at else None,
            first_seen=user.first_seen.strftime("%Y-%m-%d %H:%M") if user.first_seen else None,
            last_active=user.last_active.strftime("%Y-%m-%d %H:%M") if user.last_active else None,
            language=user.language,
            timezone=user.timezone,
            extra_data=user.extra_data
        )
    
    @classmethod
    def from_db_with_stats(cls, data: Dict[str, Any]) -> 'UserDTO':
        """ایجاد از دیکشنری دیتابیس با آمار سفارشات"""
        dto = cls.from_db(data)
        dto.orders_count = data.get('orders_count', 0)
        dto.total_payment = data.get('total_payment', 0)
        return dto
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای JSON"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'role': self.role,
            'role_label': self.role_label,
            'status': self.status,
            'status_label': self.status_label,
            'is_blocked': self.is_blocked,
            'block_reason': self.block_reason,
            'blocked_at': self.blocked_at,
            'first_seen': self.first_seen,
            'last_active': self.last_active,
            'language': self.language,
            'timezone': self.timezone,
            'orders_count': self.orders_count,
            'total_payment': self.total_payment,
        }
    
    @property
    def is_admin(self) -> bool:
        return self.role in ["admin", "manager", "owner"]
    
    @property
    def is_owner(self) -> bool:
        return self.role == "owner"
    
    @property
    def is_active(self) -> bool:
        return self.status == "active" and not self.is_blocked
    
    @property
    def is_blocked_user(self) -> bool:
        return self.is_blocked
    
    @property
    def has_orders(self) -> bool:
        return self.orders_count > 0
    
    @property
    def avg_amount(self) -> int:
        return self.total_payment // self.orders_count if self.orders_count > 0 else 0
    
    @property
    def last_active_days(self) -> Optional[int]:
        """تعداد روزهای گذشته از آخرین فعالیت"""
        if not self.last_active:
            return None
        try:
            from datetime import datetime
            last = datetime.fromisoformat(self.last_active.replace('Z', '+00:00'))
            days = (datetime.now() - last).days
            return days
        except:
            return None
    
    @property
    def status_icon(self) -> str:
        if self.is_blocked:
            return "🔴"
        if self.is_active:
            return "🟢"
        return "⚪"
    
    def to_message(self) -> str:
        """تبدیل به پیام قابل نمایش"""
        msg = f"👤 **{self.display_name}**\n"
        msg += f"🆔 شناسه: {self.user_id}\n"
        if self.username:
            msg += f"👤 نام کاربری: @{self.username}\n"
        msg += f"📌 نقش: {self.role_label}\n"
        msg += f"📌 وضعیت: {self.status_label}\n"
        if self.is_blocked and self.block_reason:
            msg += f"📝 دلیل مسدودیت: {self.block_reason}\n"
        if self.first_seen:
            msg += f"📅 عضویت: {self.first_seen}\n"
        if self.last_active:
            msg += f"📅 آخرین فعالیت: {self.last_active}\n"
        if self.orders_count > 0:
            msg += f"\n📊 **آمار:**\n"
            msg += f"  • سفارشات: {self.orders_count}\n"
            msg += f"  • مجموع مبلغ: {self.total_payment:,} ریال\n"
            msg += f"  • میانگین: {self.avg_amount:,} ریال\n"
        return msg


@dataclass
class UserListDTO:
    """
    DTO برای لیست کاربران با صفحه‌بندی
    """
    items: List[UserDTO] = field(default_factory=list)
    total: int = 0
    page: int = 0
    per_page: int = 10
    total_pages: int = 0
    
    @classmethod
    def from_db_list(cls, users: List[Dict[str, Any]], 
                     page: int = 0, per_page: int = 10, total: int = 0) -> 'UserListDTO':
        """ایجاد از لیست دیکشنری‌های دیتابیس"""
        items = [UserDTO.from_db(user) for user in users]
        return cls(
            items=items,
            total=total or len(items),
            page=page,
            per_page=per_page,
            total_pages=((total or len(items)) + per_page - 1) // per_page if (total or len(items)) > 0 else 0
        )
    
    @classmethod
    def from_db_list_with_stats(cls, users: List[Dict[str, Any]], 
                                page: int = 0, per_page: int = 10, total: int = 0) -> 'UserListDTO':
        """ایجاد از لیست دیکشنری‌های دیتابیس با آمار"""
        items = [UserDTO.from_db_with_stats(user) for user in users]
        return cls(
            items=items,
            total=total or len(items),
            page=page,
            per_page=per_page,
            total_pages=((total or len(items)) + per_page - 1) // per_page if (total or len(items)) > 0 else 0
        )


@dataclass
class UserStatsDTO:
    """
    DTO برای آمار کاربران
    """
    total_users: int = 0
    active_today: int = 0
    active_week: int = 0
    active_month: int = 0
    blocked_users: int = 0
    users_with_orders: int = 0
    users_with_payment: int = 0
    growth_percent: float = 0.0
    active_percent: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserStatsDTO':
        """ایجاد از دیکشنری"""
        return cls(
            total_users=data.get('total_users', 0),
            active_today=data.get('active_today', 0),
            active_week=data.get('active_week', 0),
            active_month=data.get('active_month', 0),
            blocked_users=data.get('blocked_users', 0),
            users_with_orders=data.get('users_with_orders', 0),
            users_with_payment=data.get('users_with_payment', 0),
            growth_percent=data.get('growth_percent', 0.0),
            active_percent=data.get('active_percent', 0.0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_users': self.total_users,
            'active_today': self.active_today,
            'active_week': self.active_week,
            'active_month': self.active_month,
            'blocked_users': self.blocked_users,
            'users_with_orders': self.users_with_orders,
            'users_with_payment': self.users_with_payment,
            'growth_percent': self.growth_percent,
            'active_percent': self.active_percent
        }
    
    def to_message(self) -> str:
        """تبدیل به پیام قابل نمایش"""
        msg = f"📊 **آمار کاربران**\n\n"
        msg += f"👥 کل کاربران: {self.total_users:,}\n"
        msg += f"🟢 فعال امروز: {self.active_today:,}\n"
        msg += f"🟢 فعال هفته: {self.active_week:,}\n"
        msg += f"🟢 فعال ماه: {self.active_month:,}\n"
        msg += f"🔴 مسدود شده: {self.blocked_users:,}\n"
        msg += f"📦 دارای سفارش: {self.users_with_orders:,}\n"
        msg += f"💰 دارای پرداخت: {self.users_with_payment:,}\n"
        msg += f"📈 نرخ رشد: {self.growth_percent:.1f}%\n"
        msg += f"📊 نرخ مشارکت: {self.active_percent:.1f}%\n"
        return msg


@dataclass
class UserCreateDTO:
    """
    DTO برای ایجاد کاربر جدید
    """
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: str = "fa"
    timezone: str = "Asia/Tehran"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'language': self.language,
            'timezone': self.timezone
        }


@dataclass
class UserUpdateDTO:
    """
    DTO برای به‌روزرسانی کاربر
    """
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_blocked: Optional[bool] = None
    block_reason: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


@dataclass
class UserFilterDTO:
    """
    DTO برای فیلترهای جستجوی کاربران
    """
    keyword: Optional[str] = None
    is_blocked: Optional[bool] = None
    role: Optional[str] = None
    has_orders: Optional[bool] = None
    active_since: Optional[int] = None
    order_by: str = "last_active"
    order_desc: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.keyword:
            result['keyword'] = self.keyword
        if self.is_blocked is not None:
            result['is_blocked'] = self.is_blocked
        if self.role:
            result['role'] = self.role
        if self.has_orders is not None:
            result['has_orders'] = self.has_orders
        if self.active_since:
            result['active_since'] = self.active_since
        return result


@dataclass
class UserActivityDTO:
    """
    DTO برای فعالیت‌های کاربر
    """
    user_id: int
    date: str
    clicks: int = 0
    form_starts: int = 0
    orders: int = 0
    revenue: int = 0
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'UserActivityDTO':
        return cls(
            user_id=data.get('user_id', 0),
            date=data.get('date', ''),
            clicks=data.get('clicks', 0),
            form_starts=data.get('form_starts', 0),
            orders=data.get('orders', 0),
            revenue=data.get('revenue', 0)
        )


@dataclass
class UserBriefDTO:
    """
    DTO خلاصه کاربر (برای نمایش در لیست‌های کوچک)
    """
    user_id: int
    display_name: str
    username: Optional[str] = None
    status_icon: str = "🟢"
    
    @classmethod
    def from_user_dto(cls, dto: UserDTO) -> 'UserBriefDTO':
        return cls(
            user_id=dto.user_id,
            display_name=dto.display_name,
            username=dto.username,
            status_icon=dto.status_icon
        )
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'UserBriefDTO':
        from models.user import User
        user = User.from_db(data)
        return cls(
            user_id=user.user_id,
            display_name=user.display_name,
            username=user.username,
            status_icon="🟢" if user.is_active else "🔴" if user.is_blocked else "⚪"
        )
    
    def to_message(self) -> str:
        return f"{self.status_icon} {self.display_name} ({self.user_id})"


__all__ = [
    'UserDTO',
    'UserListDTO',
    'UserStatsDTO',
    'UserCreateDTO',
    'UserUpdateDTO',
    'UserFilterDTO',
    'UserActivityDTO',
    'UserBriefDTO',
]