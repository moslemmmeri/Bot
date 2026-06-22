# models/category.py
# مدل دسته‌بندی

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class CategoryLocation(Enum):
    """مکان‌های دسته‌بندی"""
    MAIN = "main"          # منوی اصلی
    MORE = "more"          # منوی بیشتر
    OTHER = "other"        # دیگر خدمات


@dataclass
class Category:
    """مدل دسته‌بندی"""
    id: Optional[int] = None
    name: str = ""
    icon: str = "📁"
    location: str = "main"
    sort_order: int = 0
    is_active: bool = True
    columns: int = 2
    created_at: Optional[datetime] = None
    
    @property
    def display_name(self) -> str:
        """نام قابل نمایش با آیکون"""
        return f"{self.icon} {self.name}"
    
    @property
    def location_label(self) -> str:
        """برچسب مکان به فارسی"""
        location_map = {
            'main': 'منوی اصلی',
            'more': 'منوی بیشتر',
            'other': 'دیگر خدمات',
        }
        return location_map.get(self.location, self.location)
    
    @property
    def status_text(self) -> str:
        """متن وضعیت به فارسی"""
        return "🟢 فعال" if self.is_active else "🔴 غیرفعال"
    
    @property
    def location_emoji(self) -> str:
        """ایموجی مکان"""
        location_map = {
            'main': '🏠',
            'more': '➕',
            'other': '🔧',
        }
        return location_map.get(self.location, '📌')
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'Category':
        """ایجاد از دیکشنری دیتابیس"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            icon=data.get('icon', '📁'),
            location=data.get('location', 'main'),
            sort_order=data.get('sort_order', 0),
            is_active=bool(data.get('is_active', 1)),
            columns=data.get('columns', 2),
            created_at=data.get('created_at')
        )
    
    def to_db(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای ذخیره در دیتابیس"""
        return {
            'name': self.name,
            'icon': self.icon,
            'location': self.location,
            'sort_order': self.sort_order,
            'is_active': 1 if self.is_active else 0,
            'columns': self.columns,
        }
    
    def toggle_active(self) -> None:
        """تغییر وضعیت فعال/غیرفعال"""
        self.is_active = not self.is_active


# ============================================================
# توابع کمکی
# ============================================================

def create_category(name: str, location: str = "main", icon: str = "📁",
                    sort_order: int = 0, columns: int = 2) -> Category:
    """ایجاد دسته‌بندی جدید"""
    return Category(
        name=name,
        location=location,
        icon=icon,
        sort_order=sort_order,
        is_active=True,
        columns=columns,
        created_at=datetime.now()
    )


def get_default_categories() -> List[Dict[str, Any]]:
    """دریافت دسته‌بندی‌های پیش‌فرض"""
    return [
        {'name': 'منوی اصلی', 'location': 'main', 'icon': '🏠', 'columns': 2},
        {'name': 'منوی بیشتر', 'location': 'more', 'icon': '➕', 'columns': 2},
        {'name': 'دیگر خدمات', 'location': 'other', 'icon': '🔧', 'columns': 2},
    ]


__all__ = [
    'Category',
    'CategoryLocation',
    'create_category',
    'get_default_categories',
]