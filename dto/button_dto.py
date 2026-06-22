# dto/button_dto.py
# Data Transfer Object برای دکمه‌ها

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ButtonDTO:
    """
    Data Transfer Object برای دکمه‌ها
    برای انتقال داده بین لایه‌های مختلف بدون وابستگی به مدل‌های دیتابیس
    """
    id: Optional[int] = None
    category_id: int = 0
    parent_button_id: Optional[int] = None
    name: str = ""
    icon: str = ""
    callback_data: str = ""
    has_submenu: bool = False
    has_payment: bool = False
    price_amount: int = 50000
    price_label: str = "هزینه خدمات"
    sort_order: int = 0
    is_active: bool = True
    columns: Optional[int] = None
    effective_columns: int = 2
    created_at: Optional[str] = None
    category_name: str = ""
    category_location: str = "main"
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'ButtonDTO':
        """ایجاد از دیکشنری دیتابیس"""
        from models.button import Button
        
        btn = Button.from_db(data)
        
        return cls(
            id=btn.id,
            category_id=btn.category_id,
            parent_button_id=btn.parent_button_id,
            name=btn.name,
            icon=btn.icon,
            callback_data=btn.callback_data,
            has_submenu=btn.has_submenu,
            has_payment=btn.has_payment,
            price_amount=btn.price_amount,
            price_label=btn.price_label,
            sort_order=btn.sort_order,
            is_active=btn.is_active,
            columns=btn.columns,
            created_at=btn.created_at.strftime("%Y-%m-%d %H:%M") if btn.created_at else None,
        )
    
    @classmethod
    def from_db_with_effective_columns(cls, data: Dict[str, Any], effective_columns: int) -> 'ButtonDTO':
        """ایجاد از دیکشنری دیتابیس با ستون‌های مؤثر"""
        dto = cls.from_db(data)
        dto.effective_columns = effective_columns
        return dto
    
    @classmethod
    def from_db_with_category(cls, data: Dict[str, Any], category_name: str, category_location: str = "main") -> 'ButtonDTO':
        """ایجاد از دیکشنری دیتابیس با نام دسته‌بندی"""
        dto = cls.from_db(data)
        dto.category_name = category_name
        dto.category_location = category_location
        return dto
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای JSON"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'parent_button_id': self.parent_button_id,
            'name': self.name,
            'icon': self.icon,
            'callback_data': self.callback_data,
            'has_submenu': self.has_submenu,
            'has_payment': self.has_payment,
            'price_amount': self.price_amount,
            'price_label': self.price_label,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'columns': self.columns,
            'effective_columns': self.effective_columns,
            'created_at': self.created_at,
            'category_name': self.category_name,
            'category_location': self.category_location,
        }
    
    @property
    def display_name(self) -> str:
        """نام قابل نمایش با آیکون"""
        icon = self.icon or ("📂" if self.has_submenu else "🔘")
        return f"{icon} {self.name}"
    
    @property
    def is_submenu(self) -> bool:
        """آیا دکمه زیرمنو است"""
        return self.parent_button_id is not None and self.parent_button_id > 0
    
    @property
    def is_payable(self) -> bool:
        """آیا دکمه نیاز به پرداخت دارد"""
        return self.has_payment
    
    @property
    def button_type(self) -> str:
        """نوع دکمه"""
        if self.has_submenu:
            return "submenu"
        elif self.has_payment:
            return "service"
        return "normal"
    
    @property
    def button_type_label(self) -> str:
        """برچسب نوع دکمه"""
        labels = {
            "submenu": "📂 زیرمنو",
            "service": "💰 سرویس",
            "normal": "🔘 عادی"
        }
        return labels.get(self.button_type, "🔘 عادی")
    
    @property
    def price_formatted(self) -> str:
        """مبلغ فرمت‌شده با کاما"""
        return f"{self.price_amount:,}"
    
    @property
    def status_text(self) -> str:
        """متن وضعیت به فارسی"""
        return "🟢 فعال" if self.is_active else "🔴 غیرفعال"
    
    @property
    def submenu_text(self) -> str:
        """متن زیرمنو"""
        return "📂 دارد" if self.has_submenu else "📄 ندارد"
    
    @property
    def payment_text(self) -> str:
        """متن وضعیت پرداخت"""
        return "💰 فعال" if self.has_payment else "💳 غیرفعال"
    
    @property
    def columns_display(self) -> str:
        """نمایش تعداد ستون‌ها"""
        if self.columns is not None:
            return str(self.columns)
        return "پیش‌فرض"
    
    @property
    def effective_columns_display(self) -> str:
        """نمایش ستون‌های مؤثر"""
        return str(self.effective_columns)
    
    def to_message(self, detailed: bool = False) -> str:
        """تبدیل به پیام قابل نمایش"""
        msg = f"🔘 **{self.name}**\n"
        msg += f"🆔 شناسه: {self.id}\n"
        if self.category_name:
            msg += f"📂 دسته‌بندی: {self.category_name}\n"
        if self.parent_button_id:
            msg += f"🔗 زیرمنوی: {self.parent_button_id}\n"
        msg += f"📌 نوع: {self.button_type_label}\n"
        msg += f"📌 وضعیت: {self.status_text}\n"
        msg += f"📌 زیرمنو: {self.submenu_text}\n"
        msg += f"📌 پرداخت: {self.payment_text}\n"
        if self.has_payment:
            msg += f"💰 مبلغ: {self.price_formatted} ریال\n"
        msg += f"📊 ستون‌ها: {self.columns_display} (مؤثر: {self.effective_columns_display})\n"
        if detailed:
            msg += f"🔄 ترتیب: {self.sort_order}\n"
            msg += f"📅 ایجاد: {self.created_at or 'نامشخص'}\n"
            msg += f"🔗 کالبک: {self.callback_data}\n"
        return msg


@dataclass
class ButtonListDTO:
    """
    DTO برای لیست دکمه‌ها با آمار
    """
    items: List[ButtonDTO] = field(default_factory=list)
    total: int = 0
    page: int = 0
    per_page: int = 10
    total_pages: int = 0
    
    @classmethod
    def from_db_list(cls, buttons: List[Dict[str, Any]], 
                     page: int = 0, per_page: int = 10, total: int = 0) -> 'ButtonListDTO':
        """ایجاد از لیست دیکشنری‌های دیتابیس"""
        items = [ButtonDTO.from_db(btn) for btn in buttons]
        return cls(
            items=items,
            total=total or len(items),
            page=page,
            per_page=per_page,
            total_pages=((total or len(items)) + per_page - 1) // per_page if (total or len(items)) > 0 else 0
        )
    
    @classmethod
    def from_db_list_with_effective_columns(cls, buttons: List[Dict[str, Any]], 
                                           effective_columns: Dict[int, int],
                                           page: int = 0, per_page: int = 10, total: int = 0) -> 'ButtonListDTO':
        """ایجاد از لیست دیکشنری‌های دیتابیس با ستون‌های مؤثر"""
        items = []
        for btn in buttons:
            dto = ButtonDTO.from_db(btn)
            if btn['id'] in effective_columns:
                dto.effective_columns = effective_columns[btn['id']]
            items.append(dto)
        return cls(
            items=items,
            total=total or len(items),
            page=page,
            per_page=per_page,
            total_pages=((total or len(items)) + per_page - 1) // per_page if (total or len(items)) > 0 else 0
        )


@dataclass
class ButtonStatsDTO:
    """
    DTO برای آمار یک دکمه
    """
    button_id: int
    button_name: str = ""
    clicks: int = 0
    form_starts: int = 0
    orders: int = 0
    revenue: int = 0
    conversion_rate: float = 0.0
    
    @classmethod
    def from_db_stats(cls, button_id: int, stats: Dict[str, Any], button_name: str = "") -> 'ButtonStatsDTO':
        """ایجاد از دیکشنری آمار دیتابیس"""
        clicks = stats.get('clicks', 0)
        orders = stats.get('orders', 0)
        return cls(
            button_id=button_id,
            button_name=button_name,
            clicks=clicks,
            form_starts=stats.get('form_starts', 0),
            orders=orders,
            revenue=stats.get('revenue', 0),
            conversion_rate=(orders / clicks * 100) if clicks > 0 else 0.0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'button_id': self.button_id,
            'button_name': self.button_name,
            'clicks': self.clicks,
            'form_starts': self.form_starts,
            'orders': self.orders,
            'revenue': self.revenue,
            'conversion_rate': self.conversion_rate
        }
    
    def to_message(self) -> str:
        """تبدیل به پیام قابل نمایش"""
        msg = f"📊 **آمار دکمه: {self.button_name}**\n\n"
        msg += f"🖱️ کلیک: {self.clicks:,}\n"
        msg += f"📝 شروع فرم: {self.form_starts:,}\n"
        msg += f"📦 سفارش: {self.orders:,}\n"
        msg += f"💰 درآمد: {self.revenue:,} ریال\n"
        msg += f"📈 نرخ تبدیل: {self.conversion_rate:.2f}%\n"
        return msg


@dataclass
class ButtonCreateDTO:
    """
    DTO برای ایجاد دکمه جدید
    """
    category_id: int
    name: str
    icon: str = ""
    callback_data: Optional[str] = None
    parent_button_id: Optional[int] = None
    has_submenu: bool = False
    has_payment: bool = False
    price_amount: int = 50000
    price_label: str = "هزینه خدمات"
    sort_order: Optional[int] = None
    columns: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        import time
        if self.callback_data is None:
            self.callback_data = f"btn_{self.category_id}_{int(time.time())}"
        return {
            'category_id': self.category_id,
            'name': self.name,
            'icon': self.icon,
            'callback_data': self.callback_data,
            'parent_button_id': self.parent_button_id,
            'has_submenu': 1 if self.has_submenu else 0,
            'has_payment': 1 if self.has_payment else 0,
            'price_amount': self.price_amount,
            'price_label': self.price_label,
            'sort_order': self.sort_order or 0,
            'columns': self.columns,
        }


@dataclass
class ButtonUpdateDTO:
    """
    DTO برای به‌روزرسانی دکمه
    """
    button_id: int
    name: Optional[str] = None
    icon: Optional[str] = None
    callback_data: Optional[str] = None
    has_submenu: Optional[bool] = None
    has_payment: Optional[bool] = None
    price_amount: Optional[int] = None
    price_label: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    columns: Optional[int] = None
    category_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.name is not None:
            result['name'] = self.name
        if self.icon is not None:
            result['icon'] = self.icon
        if self.callback_data is not None:
            result['callback_data'] = self.callback_data
        if self.has_submenu is not None:
            result['has_submenu'] = 1 if self.has_submenu else 0
        if self.has_payment is not None:
            result['has_payment'] = 1 if self.has_payment else 0
        if self.price_amount is not None:
            result['price_amount'] = self.price_amount
        if self.price_label is not None:
            result['price_label'] = self.price_label
        if self.sort_order is not None:
            result['sort_order'] = self.sort_order
        if self.is_active is not None:
            result['is_active'] = 1 if self.is_active else 0
        if self.columns is not None:
            result['columns'] = self.columns
        if self.category_id is not None:
            result['category_id'] = self.category_id
        return result


@dataclass
class ButtonFilterDTO:
    """
    DTO برای فیلترهای جستجوی دکمه‌ها
    """
    category_id: Optional[int] = None
    parent_button_id: Optional[int] = None
    is_active: Optional[bool] = None
    has_submenu: Optional[bool] = None
    has_payment: Optional[bool] = None
    location: Optional[str] = None
    keyword: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.category_id is not None:
            result['category_id'] = self.category_id
        if self.parent_button_id is not None:
            result['parent_button_id'] = self.parent_button_id
        if self.is_active is not None:
            result['is_active'] = self.is_active
        if self.has_submenu is not None:
            result['has_submenu'] = self.has_submenu
        if self.has_payment is not None:
            result['has_payment'] = self.has_payment
        if self.location:
            result['location'] = self.location
        if self.keyword:
            result['keyword'] = self.keyword
        return result


@dataclass
class CategoryDTO:
    """
    DTO برای دسته‌بندی‌ها
    """
    id: Optional[int] = None
    name: str = ""
    icon: str = "📁"
    location: str = "main"
    sort_order: int = 0
    is_active: bool = True
    columns: int = 2
    effective_columns: int = 2
    button_count: int = 0
    created_at: Optional[str] = None
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'CategoryDTO':
        """ایجاد از دیکشنری دیتابیس"""
        from models.category import Category
        
        cat = Category.from_db(data)
        
        return cls(
            id=cat.id,
            name=cat.name,
            icon=cat.icon,
            location=cat.location,
            sort_order=cat.sort_order,
            is_active=cat.is_active,
            columns=cat.columns,
            created_at=cat.created_at.strftime("%Y-%m-%d %H:%M") if cat.created_at else None,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'location': self.location,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'columns': self.columns,
            'effective_columns': self.effective_columns,
            'button_count': self.button_count,
            'created_at': self.created_at,
        }
    
    @property
    def display_name(self) -> str:
        return f"{self.icon} {self.name}"
    
    @property
    def location_label(self) -> str:
        labels = {
            'main': '🏠 منوی اصلی',
            'more': '➕ منوی بیشتر',
            'other': '🔧 دیگر خدمات',
        }
        return labels.get(self.location, self.location)
    
    @property
    def status_text(self) -> str:
        return "🟢 فعال" if self.is_active else "🔴 غیرفعال"
    
    def to_message(self) -> str:
        msg = f"📂 **{self.name}**\n"
        msg += f"🆔 شناسه: {self.id}\n"
        msg += f"📍 مکان: {self.location_label}\n"
        msg += f"📌 وضعیت: {self.status_text}\n"
        msg += f"📊 ستون‌ها: {self.columns} (مؤثر: {self.effective_columns})\n"
        msg += f"🔘 تعداد دکمه‌ها: {self.button_count}\n"
        if self.created_at:
            msg += f"📅 ایجاد: {self.created_at}\n"
        return msg


__all__ = [
    'ButtonDTO',
    'ButtonListDTO',
    'ButtonStatsDTO',
    'ButtonCreateDTO',
    'ButtonUpdateDTO',
    'ButtonFilterDTO',
    'CategoryDTO',
]