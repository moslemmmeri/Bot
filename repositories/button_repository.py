# repositories/button_repository.py
# ریپازیتوری دکمه‌ها

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime
from logger_config import logger
from .base_repository import BaseRepository
from models.button import Button, ButtonType
from utils.error_handler import log_database_error  # ✅ اضافه شد


class ButtonRepository(BaseRepository):
    """ریپازیتوری دکمه‌ها - مدیریت عملیات دیتابیس مربوط به دکمه‌ها"""
    
    def __init__(self, connection):
        super().__init__(connection, 'buttons', 'id')
    
    # ============================================================
    # متدهای پایه
    # ============================================================
    
    def get_by_id(self, button_id: int) -> Optional[Dict[str, Any]]:
        """دریافت دکمه بر اساس شناسه"""
        return super().get_by_id(button_id)
    
    def get_by_callback(self, callback_data: str) -> Optional[Dict[str, Any]]:
        """دریافت دکمه بر اساس callback_data"""
        return self.get_by_field('callback_data', callback_data)
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت تمام دکمه‌ها با صفحه‌بندی"""
        return super().get_all(limit, offset, order_by='sort_order, id')
    
    def get_active(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت دکمه‌های فعال"""
        query = """
            SELECT * FROM buttons 
            WHERE is_active = 1 
            ORDER BY sort_order, id 
            LIMIT ? OFFSET ?
        """
        return self.custom_query(query, [limit, offset])
    
    # ============================================================
    # دریافت دکمه‌ها بر اساس دسته‌بندی
    # ============================================================
    
    def get_by_category(self, category_id: int, include_submenus: bool = False) -> List[Dict[str, Any]]:
        """
        دریافت دکمه‌های یک دسته‌بندی
        
        پارامترها:
            category_id: شناسه دسته‌بندی
            include_submenus: آیا زیرمنوها نیز نمایش داده شوند
        """
        if include_submenus:
            query = """
                SELECT * FROM buttons 
                WHERE category_id = ? AND is_active = 1
                ORDER BY sort_order, id
            """
            return self.custom_query(query, [category_id])
        else:
            query = """
                SELECT * FROM buttons 
                WHERE category_id = ? AND is_active = 1 
                AND (parent_button_id IS NULL OR parent_button_id = 0)
                ORDER BY sort_order, id
            """
            return self.custom_query(query, [category_id])
    
    def get_by_category_admin(self, category_id: int) -> List[Dict[str, Any]]:
        """دریافت دکمه‌های یک دسته‌بندی برای پنل مدیریت (با آیکون نمایشی)"""
        query = """
            SELECT 
                b.*,
                CASE 
                    WHEN b.has_submenu = 1 THEN '📂' 
                    ELSE '📄' 
                END as display_icon
            FROM buttons b
            WHERE b.category_id = ? 
            AND b.is_active = 1 
            AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
            ORDER BY b.sort_order, b.id
        """
        return self.custom_query(query, [category_id])
    
    def get_by_location(self, location: str) -> List[Dict[str, Any]]:
        """
        دریافت دکمه‌های یک مکان خاص (منوی اصلی، بیشتر، دیگر خدمات)
        
        پارامترها:
            location: نام بخش (main, more, other)
        """
        query = """
            SELECT b.* FROM buttons b
            JOIN categories c ON b.category_id = c.id
            WHERE c.location = ? AND b.is_active = 1 
            AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
            ORDER BY b.sort_order, b.id
        """
        return self.custom_query(query, [location])
    
    # ============================================================
    # دریافت زیرمنوها
    # ============================================================
    
    def get_submenus(self, parent_button_id: int) -> List[Dict[str, Any]]:
        """دریافت زیرمنوهای یک دکمه"""
        query = """
            SELECT * FROM buttons 
            WHERE parent_button_id = ? AND is_active = 1 
            ORDER BY sort_order, id
        """
        return self.custom_query(query, [parent_button_id])
    
    def get_all_submenus(self, button_id: int) -> List[Dict[str, Any]]:
        """دریافت لیست تمام زیرمنوهای یک دکمه (فقط نام و شناسه)"""
        query = """
            SELECT id, name FROM buttons 
            WHERE parent_button_id = ? AND is_active = 1
            ORDER BY sort_order, id
        """
        return self.custom_query(query, [button_id])
    
    def get_submenu_count(self, parent_button_id: int) -> int:
        """تعداد زیرمنوهای یک دکمه"""
        query = "SELECT COUNT(*) as count FROM buttons WHERE parent_button_id = ? AND is_active = 1"
        result = self.custom_query_one(query, [parent_button_id])
        return result.get('count', 0) if result else 0
    
    # ============================================================
    # دریافت دکمه‌های دارای ویژگی خاص
    # ============================================================
    
    def get_with_payment(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت دکمه‌هایی که نیاز به پرداخت دارند"""
        query = """
            SELECT * FROM buttons 
            WHERE has_payment = 1 AND is_active = 1
            ORDER BY sort_order, id
            LIMIT ?
        """
        return self.custom_query(query, [limit])
    
    def get_with_submenu(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت دکمه‌هایی که زیرمنو دارند"""
        query = """
            SELECT * FROM buttons 
            WHERE has_submenu = 1 AND is_active = 1
            ORDER BY sort_order, id
            LIMIT ?
        """
        return self.custom_query(query, [limit])
    
    def get_parent_buttons(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """دریافت دکمه‌های والد (بدون parent)"""
        if category_id:
            query = """
                SELECT * FROM buttons 
                WHERE (parent_button_id IS NULL OR parent_button_id = 0)
                AND is_active = 1
                AND category_id = ?
                ORDER BY sort_order, id
            """
            return self.custom_query(query, [category_id])
        else:
            query = """
                SELECT * FROM buttons 
                WHERE (parent_button_id IS NULL OR parent_button_id = 0)
                AND is_active = 1
                ORDER BY sort_order, id
            """
            return self.custom_query(query)
    
    # ============================================================
    # عملیات ایجاد و به‌روزرسانی
    # ============================================================
    
    def create(self, category_id: int, name: str, icon: str = "",
               callback_data: Optional[str] = None,
               parent_button_id: Optional[int] = None,
               has_submenu: bool = False, has_payment: bool = False,
               price_amount: int = 50000, price_label: str = "هزینه خدمات",
               sort_order: int = 0, columns: Optional[int] = None) -> Optional[int]:
        """
        ایجاد دکمه جدید
        
        بازگشت: شناسه دکمه ایجادشده
        """
        import time
        if callback_data is None:
            callback_data = f"btn_{category_id}_{int(time.time())}"
        
        data = {
            'category_id': category_id,
            'name': name,
            'icon': icon,
            'callback_data': callback_data,
            'parent_button_id': parent_button_id,
            'has_submenu': 1 if has_submenu else 0,
            'has_payment': 1 if has_payment else 0,
            'price_amount': price_amount,
            'price_label': price_label,
            'sort_order': sort_order,
            'is_active': 1,
            'columns': columns,
            'created_at': datetime.now().isoformat()
        }
        return self.insert(data)
    
    def update(self, button_id: int, data: Dict[str, Any]) -> bool:
        """به‌روزرسانی دکمه"""
        return super().update(button_id, data)
    
    def update_name(self, button_id: int, name: str) -> bool:
        """به‌روزرسانی نام دکمه"""
        return self.update(button_id, {'name': name})
    
    def update_price(self, button_id: int, price_amount: int, price_label: Optional[str] = None) -> bool:
        """به‌روزرسانی مبلغ دکمه"""
        data = {'price_amount': price_amount}
        if price_label:
            data['price_label'] = price_label
        return self.update(button_id, data)
    
    def toggle_active(self, button_id: int) -> bool:
        """تغییر وضعیت فعال/غیرفعال"""
        button = self.get_by_id(button_id)
        if not button:
            return False
        new_status = 0 if button.get('is_active', 1) == 1 else 1
        return self.update(button_id, {'is_active': new_status})
    
    def toggle_payment(self, button_id: int) -> bool:
        """تغییر وضعیت پرداخت"""
        button = self.get_by_id(button_id)
        if not button:
            return False
        new_status = 0 if button.get('has_payment', 0) == 1 else 1
        return self.update(button_id, {'has_payment': new_status})
    
    def toggle_submenu(self, button_id: int) -> bool:
        """تغییر وضعیت زیرمنو"""
        button = self.get_by_id(button_id)
        if not button:
            return False
        new_status = 0 if button.get('has_submenu', 0) == 1 else 1
        return self.update(button_id, {'has_submenu': new_status})
    
    def update_sort_order(self, button_id: int, sort_order: int) -> bool:
        """به‌روزرسانی ترتیب نمایش"""
        return self.update(button_id, {'sort_order': sort_order})
    
    def update_columns(self, button_id: int, columns: Optional[int]) -> bool:
        """به‌روزرسانی تعداد ستون‌ها"""
        return self.update(button_id, {'columns': columns})
    
    def move_to_category(self, button_id: int, new_category_id: int) -> bool:
        """
        انتقال دکمه به دسته‌بندی دیگر
        (همچنین زیرمنوهای آن نیز منتقل می‌شوند)
        """
        button = self.get_by_id(button_id)
        if not button:
            return False
        
        # به‌روزرسانی دسته‌بندی دکمه
        success = self.update(button_id, {'category_id': new_category_id})
        
        if success:
            # به‌روزرسانی دسته‌بندی زیرمنوها
            submenus = self.get_submenus(button_id)
            for sub in submenus:
                self.update(sub['id'], {'category_id': new_category_id})
        
        return success
    
    def swap_sort_order(self, button_id_1: int, button_id_2: int) -> bool:
        """جابجایی ترتیب نمایش دو دکمه"""
        btn1 = self.get_by_id(button_id_1)
        btn2 = self.get_by_id(button_id_2)
        
        if not btn1 or not btn2:
            return False
        
        order1 = btn1.get('sort_order', 0)
        order2 = btn2.get('sort_order', 0)
        
        self.update(button_id_1, {'sort_order': order2})
        self.update(button_id_2, {'sort_order': order1})
        
        return True
    
    def delete(self, button_id: int) -> bool:
        """حذف یک دکمه و همه زیرمنوهای آن"""
        # حذف زیرمنوها
        submenus = self.get_submenus(button_id)
        for sub in submenus:
            super().delete(sub['id'])
        
        # حذف دکمه اصلی
        return super().delete(button_id)
    
    def delete_duplicate_submenus(self, button_id: int) -> int:
        """
        حذف زیرمنوهای تکراری که نامشان با نام دکمه والد یکسان است
        
        بازگشت: تعداد زیرمنوهای حذف‌شده
        """
        button = self.get_by_id(button_id)
        if not button:
            return 0
        
        main_name = button.get('name', '')
        query = """
            DELETE FROM buttons 
            WHERE parent_button_id = ? AND name = ? AND id != ?
        """
        count = self.custom_execute(query, [button_id, main_name, button_id])
        return count
    
    # ============================================================
    # توابع کمکی
    # ============================================================
    
    def get_max_sort_order(self, category_id: int, parent_id: Optional[int] = None) -> int:
        """دریافت حداکثر sort_order در یک دسته‌بندی"""
        if parent_id:
            query = """
                SELECT MAX(sort_order) as max_order FROM buttons 
                WHERE category_id = ? AND parent_button_id = ?
            """
            result = self.custom_query_one(query, [category_id, parent_id])
        else:
            query = """
                SELECT MAX(sort_order) as max_order FROM buttons 
                WHERE category_id = ? AND (parent_button_id IS NULL OR parent_button_id = 0)
            """
            result = self.custom_query_one(query, [category_id])
        
        return result.get('max_order', -1) if result else -1
    
    def get_buttons_with_stats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        دریافت لیست دکمه‌ها به همراه آمار (تعداد کلیک، سفارش، درآمد)
        """
        query = """
            SELECT 
                b.*,
                COALESCE(SUM(CASE WHEN s.action_type = 'click' THEN 1 ELSE 0 END), 0) as clicks,
                COALESCE(SUM(CASE WHEN s.action_type = 'order_paid' THEN 1 ELSE 0 END), 0) as orders,
                COALESCE(SUM(CASE WHEN s.action_type = 'order_paid' THEN s.amount ELSE 0 END), 0) as revenue
            FROM buttons b
            LEFT JOIN button_stats s ON b.id = s.button_id
            WHERE b.is_active = 1
            GROUP BY b.id
            ORDER BY b.sort_order, b.id
            LIMIT ?
        """
        return self.custom_query(query, [limit])
    
    def get_button_count(self, category_id: Optional[int] = None) -> int:
        """تعداد دکمه‌ها (با فیلتر اختیاری دسته‌بندی)"""
        if category_id:
            query = "SELECT COUNT(*) as count FROM buttons WHERE category_id = ? AND is_active = 1"
            result = self.custom_query_one(query, [category_id])
        else:
            query = "SELECT COUNT(*) as count FROM buttons WHERE is_active = 1"
            result = self.custom_query_one(query)
        return result.get('count', 0) if result else 0


__all__ = [
    'ButtonRepository',
]