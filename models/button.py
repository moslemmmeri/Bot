# models/button.py
# مدل دکمه

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import IntEnum, Enum


class ButtonType(IntEnum):
    """نوع دکمه"""
    NORMAL = 0        # دکمه عادی
    SUBMENU = 1       # دکمه دارای زیرمنو
    SERVICE = 2       # دکمه سرویس (با پرداخت)


@dataclass
class Button:
    """مدل دکمه"""
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
    created_at: Optional[datetime] = None
    
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
    def button_type(self) -> ButtonType:
        """نوع دکمه"""
        if self.has_submenu:
            return ButtonType.SUBMENU
        elif self.has_payment:
            return ButtonType.SERVICE
        return ButtonType.NORMAL
    
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
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'Button':
        """ایجاد از دیکشنری دیتابیس"""
        return cls(
            id=data.get('id'),
            category_id=data.get('category_id', 0),
            parent_button_id=data.get('parent_button_id'),
            name=data.get('name', ''),
            icon=data.get('icon', ''),
            callback_data=data.get('callback_data', ''),
            has_submenu=bool(data.get('has_submenu', 0)),
            has_payment=bool(data.get('has_payment', 0)),
            price_amount=data.get('price_amount', 50000),
            price_label=data.get('price_label', 'هزینه خدمات'),
            sort_order=data.get('sort_order', 0),
            is_active=bool(data.get('is_active', 1)),
            columns=data.get('columns'),
            created_at=data.get('created_at')
        )
    
    def to_db(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای ذخیره در دیتابیس"""
        return {
            'category_id': self.category_id,
            'parent_button_id': self.parent_button_id,
            'name': self.name,
            'icon': self.icon,
            'callback_data': self.callback_data,
            'has_submenu': 1 if self.has_submenu else 0,
            'has_payment': 1 if self.has_payment else 0,
            'price_amount': self.price_amount,
            'price_label': self.price_label,
            'sort_order': self.sort_order,
            'is_active': 1 if self.is_active else 0,
            'columns': self.columns,
        }
    
    def toggle_active(self) -> None:
        """تغییر وضعیت فعال/غیرفعال"""
        self.is_active = not self.is_active
    
    def toggle_payment(self) -> None:
        """تغییر وضعیت پرداخت"""
        self.has_payment = not self.has_payment
    
    def toggle_submenu(self) -> None:
        """تغییر وضعیت زیرمنو"""
        self.has_submenu = not self.has_submenu


# ============================================================
# توابع کمکی
# ============================================================

def create_button(category_id: int, name: str, parent_button_id: Optional[int] = None,
                  icon: str = "", callback_data: Optional[str] = None,
                  has_submenu: bool = False, has_payment: bool = False,
                  price_amount: int = 50000, price_label: str = "هزینه خدمات",
                  sort_order: int = 0, columns: Optional[int] = None) -> Button:
    """ایجاد دکمه جدید"""
    import time
    if callback_data is None:
        callback_data = f"btn_{category_id}_{int(time.time())}"
    
    return Button(
        category_id=category_id,
        parent_button_id=parent_button_id,
        name=name,
        icon=icon,
        callback_data=callback_data,
        has_submenu=has_submenu,
        has_payment=has_payment,
        price_amount=price_amount,
        price_label=price_label,
        sort_order=sort_order,
        is_active=True,
        columns=columns,
        created_at=datetime.now()
    )


def create_submenu(parent_button_id: int, category_id: int, name: str,
                   callback_data: Optional[str] = None) -> Button:
    """ایجاد زیرمنو"""
    return create_button(
        category_id=category_id,
        parent_button_id=parent_button_id,
        name=name,
        callback_data=callback_data,
        has_submenu=False,
        has_payment=False,
        sort_order=0
    )


def button_from_callback(callback_data: str) -> Button:
    """ایجاد دکمه از روی callback_data (برای استفاده در پردازش)"""
    # این تابع فقط برای ایجاد یک دکمه موقت استفاده می‌شود
    # داده‌های واقعی از دیتابیس خوانده می‌شوند
    return Button(
        name=callback_data,
        callback_data=callback_data
    )


__all__ = [
    'Button',
    'ButtonType',
    'create_button',
    'create_submenu',
    'button_from_callback',
]