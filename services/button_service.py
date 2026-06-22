# services/button_service.py
# سرویس مدیریت دکمه‌ها - منطق کسب‌وکار مربوط به دکمه‌ها و ساختار منو

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime
from logger_config import logger
from repositories import ButtonRepository, CategoryRepository
from database.db_columns import get_effective_columns
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class ButtonService:
    """سرویس مدیریت دکمه‌ها"""
    
    def __init__(self, connection, repository: Optional[ButtonRepository] = None):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            repository: ریپازیتوری دکمه‌ها (اختیاری)
        """
        self._connection = connection
        self._repository = repository or ButtonRepository(connection)
        self._category_repo = CategoryRepository(connection)
    
    # ============================================================
    # عملیات پایه
    # ============================================================
    
    def get_button(self, button_id: int) -> Optional[Dict[str, Any]]:
        """دریافت دکمه بر اساس شناسه"""
        return self._repository.get_by_id(button_id)
    
    def get_button_by_callback(self, callback_data: str) -> Optional[Dict[str, Any]]:
        """دریافت دکمه بر اساس callback_data"""
        return self._repository.get_by_callback(callback_data)
    
    def get_all_buttons(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت تمام دکمه‌ها"""
        return self._repository.get_all(limit, offset)
    
    def get_active_buttons(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت دکمه‌های فعال"""
        return self._repository.get_active(limit, offset)
    
    # ============================================================
    # دریافت بر اساس دسته‌بندی
    # ============================================================
    
    def get_buttons_by_category(self, category_id: int, include_submenus: bool = False) -> List[Dict[str, Any]]:
        """دریافت دکمه‌های یک دسته‌بندی"""
        return self._repository.get_by_category(category_id, include_submenus)
    
    def get_buttons_by_location(self, location: str) -> List[Dict[str, Any]]:
        """دریافت دکمه‌های یک مکان خاص (main, more, other)"""
        return self._repository.get_by_location(location)
    
    def get_category_buttons_with_columns(self, category_id: int) -> List[Dict[str, Any]]:
        """
        دریافت دکمه‌های یک دسته‌بندی با اطلاعات ستون‌ها
        """
        buttons = self.get_buttons_by_category(category_id)
        result = []
        for btn in buttons:
            btn_dict = dict(btn)
            btn_dict['effective_columns'] = get_effective_columns(
                button_id=btn['id'],
                category_id=category_id
            )
            result.append(btn_dict)
        return result
    
    # ============================================================
    # مدیریت زیرمنوها
    # ============================================================
    
    def get_submenus(self, parent_button_id: int) -> List[Dict[str, Any]]:
        """دریافت زیرمنوهای یک دکمه"""
        return self._repository.get_submenus(parent_button_id)
    
    def get_submenu_count(self, parent_button_id: int) -> int:
        """تعداد زیرمنوهای یک دکمه"""
        return self._repository.get_submenu_count(parent_button_id)
    
    def has_submenus(self, button_id: int) -> bool:
        """بررسی وجود زیرمنو برای یک دکمه"""
        return self.get_submenu_count(button_id) > 0
    
    def get_menu_structure(self, location: str) -> List[Dict[str, Any]]:
        """
        دریافت ساختار کامل منو (دسته‌بندی‌ها و دکمه‌های آنها)
        
        پارامترها:
            location: مکان منو (main, more, other)
        
        بازگشت: لیست دسته‌بندی‌ها با دکمه‌هایشان
        """
        categories = self._category_repo.get_by_location(location)
        if not categories:
            return []
        
        result = []
        for cat in categories:
            cat_dict = dict(cat)
            buttons = self.get_buttons_by_category(cat['id'])
            cat_dict['buttons'] = buttons
            cat_dict['effective_columns'] = get_effective_columns(
                category_id=cat['id']
            )
            result.append(cat_dict)
        
        return result
    
    # ============================================================
    # ایجاد و به‌روزرسانی
    # ============================================================
    
    def create_button(self, category_id: int, name: str, icon: str = "",
                      callback_data: Optional[str] = None,
                      parent_button_id: Optional[int] = None,
                      has_submenu: bool = False, has_payment: bool = False,
                      price_amount: int = 50000, price_label: str = "هزینه خدمات",
                      sort_order: Optional[int] = None,
                      columns: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        ایجاد دکمه جدید
        
        بازگشت: دیکشنری دکمه ایجادشده
        """
        # بررسی وجود دسته‌بندی
        category = self._category_repo.get_by_id(category_id)
        if not category:
            logger.warning(f"Category {category_id} not found")
            return None
        
        # محاسبه sort_order خودکار
        if sort_order is None:
            sort_order = self._repository.get_max_sort_order(category_id, parent_button_id) + 1
        
        try:
            button_id = self._repository.create(
                category_id=category_id,
                name=name,
                icon=icon,
                callback_data=callback_data,
                parent_button_id=parent_button_id,
                has_submenu=has_submenu,
                has_payment=has_payment,
                price_amount=price_amount,
                price_label=price_label,
                sort_order=sort_order,
                columns=columns
            )
            
            if button_id:
                # اگر والد وجود دارد، has_submenu والد را به‌روزرسانی کن
                if parent_button_id:
                    self._repository.update(parent_button_id, {'has_submenu': 1})
                
                logger.info(f"✅ Button created: {name} (id={button_id})")
                return self.get_button(button_id)
            
            return None
        except Exception as e:
            log_database_error(
                f"Error creating button: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def create_submenu(self, parent_button_id: int, name: str,
                       callback_data: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        ایجاد زیرمنو
        
        پارامترها:
            parent_button_id: شناسه دکمه والد
            name: نام زیرمنو
            callback_data: داده کالبک (اختیاری)
        
        بازگشت: دیکشنری زیرمنو ایجادشده
        """
        parent = self.get_button(parent_button_id)
        if not parent:
            logger.warning(f"Parent button {parent_button_id} not found")
            return None
        
        # زیرمنوها در همان دسته‌بندی والد ایجاد می‌شوند
        category_id = parent.get('category_id')
        
        try:
            return self.create_button(
                category_id=category_id,
                name=name,
                callback_data=callback_data,
                parent_button_id=parent_button_id,
                has_submenu=False,
                has_payment=False,
                sort_order=self._repository.get_max_sort_order(category_id, parent_button_id) + 1
            )
        except Exception as e:
            log_database_error(
                f"Error creating submenu: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def update_button(self, button_id: int, data: Dict[str, Any]) -> bool:
        """به‌روزرسانی دکمه"""
        try:
            return self._repository.update(button_id, data)
        except Exception as e:
            log_database_error(
                f"Error updating button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_button_name(self, button_id: int, name: str) -> bool:
        """به‌روزرسانی نام دکمه"""
        try:
            return self._repository.update_name(button_id, name)
        except Exception as e:
            log_database_error(
                f"Error updating button name {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_button_price(self, button_id: int, price_amount: int,
                           price_label: Optional[str] = None) -> bool:
        """به‌روزرسانی مبلغ دکمه"""
        try:
            return self._repository.update_price(button_id, price_amount, price_label)
        except Exception as e:
            log_database_error(
                f"Error updating button price {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def toggle_button_active(self, button_id: int) -> bool:
        """تغییر وضعیت فعال/غیرفعال دکمه"""
        try:
            return self._repository.toggle_active(button_id)
        except Exception as e:
            log_database_error(
                f"Error toggling active status for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def toggle_button_payment(self, button_id: int) -> bool:
        """تغییر وضعیت پرداخت دکمه"""
        try:
            return self._repository.toggle_payment(button_id)
        except Exception as e:
            log_database_error(
                f"Error toggling payment for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def toggle_button_submenu(self, button_id: int) -> bool:
        """تغییر وضعیت زیرمنو دکمه"""
        try:
            return self._repository.toggle_submenu(button_id)
        except Exception as e:
            log_database_error(
                f"Error toggling submenu for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete_button(self, button_id: int) -> bool:
        """حذف دکمه و همه زیرمنوهای آن"""
        button = self.get_button(button_id)
        if not button:
            return False
        
        # ذخیره اطلاعات برای لاگ
        button_name = button.get('name')
        parent_id = button.get('parent_button_id')
        
        try:
            success = self._repository.delete(button_id)
            
            if success:
                # اگر والد بود و زیرمنویی ندارد، has_submenu را غیرفعال کن
                if parent_id:
                    submenu_count = self.get_submenu_count(parent_id)
                    if submenu_count == 0:
                        self._repository.update(parent_id, {'has_submenu': 0})
                
                logger.info(f"🗑️ Button deleted: {button_name} (id={button_id})")
            
            return success
        except Exception as e:
            log_database_error(
                f"Error deleting button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete_submenu(self, submenu_id: int) -> bool:
        """حذف یک زیرمنو"""
        submenu = self.get_button(submenu_id)
        if not submenu:
            return False
        
        parent_id = submenu.get('parent_button_id')
        try:
            success = self._repository.delete(submenu_id)
            
            if success and parent_id:
                # بررسی اینکه آیا زیرمنوی دیگری باقی مانده است
                if self.get_submenu_count(parent_id) == 0:
                    self._repository.update(parent_id, {'has_submenu': 0})
            
            return success
        except Exception as e:
            log_database_error(
                f"Error deleting submenu {submenu_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def move_button(self, button_id: int, new_category_id: int) -> bool:
        """انتقال دکمه به دسته‌بندی دیگر"""
        try:
            return self._repository.move_to_category(button_id, new_category_id)
        except Exception as e:
            log_database_error(
                f"Error moving button {button_id} to category {new_category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def swap_sort_order(self, button_id_1: int, button_id_2: int) -> bool:
        """جابجایی ترتیب نمایش دو دکمه"""
        try:
            return self._repository.swap_sort_order(button_id_1, button_id_2)
        except Exception as e:
            log_database_error(
                f"Error swapping sort order for {button_id_1} and {button_id_2}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_sort_order(self, button_id: int, sort_order: int) -> bool:
        """به‌روزرسانی ترتیب نمایش"""
        try:
            return self._repository.update_sort_order(button_id, sort_order)
        except Exception as e:
            log_database_error(
                f"Error updating sort order for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # مدیریت ستون‌ها
    # ============================================================
    
    def get_button_columns(self, button_id: int) -> Optional[int]:
        """دریافت ستون‌های اختصاصی دکمه"""
        button = self.get_button(button_id)
        return button.get('columns') if button else None
    
    def get_effective_columns(self, button_id: int) -> int:
        """دریافت ستون‌های مؤثر دکمه"""
        button = self.get_button(button_id)
        if not button:
            return 2
        
        return get_effective_columns(
            button_id=button_id,
            category_id=button.get('category_id')
        )
    
    def set_button_columns(self, button_id: int, columns: Optional[int]) -> bool:
        """تنظیم ستون‌های اختصاصی دکمه"""
        try:
            return self._repository.update_columns(button_id, columns)
        except Exception as e:
            log_database_error(
                f"Error setting columns for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # روش‌های کمکی برای منو
    # ============================================================
    
    def get_menu_keyboard_data(self, location: str) -> Dict[str, Any]:
        """
        دریافت داده‌های کیبورد برای یک منو
        
        پارامترها:
            location: مکان منو (main, more, other)
        
        بازگشت: دیکشنری شامل buttons, columns و metadata
        """
        buttons = self.get_buttons_by_location(location)
        
        # محاسبه ستون‌های مؤثر برای هر دکمه
        button_data = []
        for btn in buttons:
            effective = get_effective_columns(
                button_id=btn['id'],
                category_id=btn['category_id']
            )
            btn_dict = dict(btn)
            btn_dict['effective_columns'] = effective
            button_data.append(btn_dict)
        
        # دریافت دسته‌بندی مربوطه
        category = self._category_repo.get_by_location(location)
        category_columns = get_effective_columns(category_id=category['id']) if category else 2
        
        return {
            'buttons': button_data,
            'category_columns': category_columns,
            'total_buttons': len(button_data),
            'has_submenu_buttons': len([b for b in button_data if b.get('has_submenu', 0) == 1])
        }
    
    def get_button_tree(self, location: str) -> List[Dict[str, Any]]:
        """
        دریافت ساختار درختی کامل منو
        
        پارامترها:
            location: مکان منو
        
        بازگشت: لیست درختی دکمه‌ها با زیرمنوهایشان
        """
        categories = self._category_repo.get_by_location(location)
        result = []
        
        for cat in categories:
            cat_dict = {
                'id': cat['id'],
                'name': cat['name'],
                'icon': cat.get('icon', '📁'),
                'columns': cat.get('columns', 2),
                'buttons': []
            }
            
            buttons = self.get_buttons_by_category(cat['id'])
            for btn in buttons:
                btn_dict = dict(btn)
                if btn.get('has_submenu', 0) == 1:
                    btn_dict['submenus'] = self.get_submenus(btn['id'])
                else:
                    btn_dict['submenus'] = []
                cat_dict['buttons'].append(btn_dict)
            
            result.append(cat_dict)
        
        return result
    
    # ============================================================
    # آمار
    # ============================================================
    
    def get_button_count(self, category_id: Optional[int] = None) -> int:
        """تعداد دکمه‌ها"""
        return self._repository.get_button_count(category_id)
    
    def get_buttons_with_stats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت دکمه‌ها با آمار کلیک و سفارش"""
        return self._repository.get_buttons_with_stats(limit)
    
    def get_service_usage(self) -> List[Dict[str, Any]]:
        """
        دریافت آمار استفاده از سرویس‌ها (دکمه‌ها)
        
        بازگشت: لیست دکمه‌ها با تعداد استفاده و درآمد
        """
        try:
            query = """
                SELECT 
                    b.id,
                    b.name,
                    COUNT(CASE WHEN s.action_type = 'click' THEN 1 END) as clicks,
                    COUNT(CASE WHEN s.action_type = 'form_start' THEN 1 END) as form_starts,
                    COUNT(CASE WHEN s.action_type = 'order_paid' THEN 1 END) as orders,
                    COALESCE(SUM(CASE WHEN s.action_type = 'order_paid' THEN s.amount ELSE 0 END), 0) as revenue
                FROM buttons b
                LEFT JOIN button_stats s ON b.id = s.button_id
                WHERE b.is_active = 1
                GROUP BY b.id
                ORDER BY revenue DESC
            """
            with self._connection.get_cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            log_database_error(
                f"Error getting service usage: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_service_rankings(self, sort_by: str = 'orders', limit: int = 10) -> List[Dict[str, Any]]:
        """
        دریافت رتبه‌بندی سرویس‌ها
        
        پارامترها:
            sort_by: معیار مرتب‌سازی (orders, revenue, clicks, conversion_rate)
            limit: تعداد نتایج
        
        بازگشت: لیست سرویس‌های رتبه‌بندی‌شده
        """
        try:
            services = self.get_service_usage()
            
            # محاسبه نرخ تبدیل برای هر سرویس
            for s in services:
                clicks = s.get('clicks', 0)
                orders = s.get('orders', 0)
                s['conversion_rate'] = (orders / clicks * 100) if clicks > 0 else 0
            
            # مرتب‌سازی
            sort_map = {
                'orders': 'orders',
                'revenue': 'revenue',
                'clicks': 'clicks',
                'conversion_rate': 'conversion_rate'
            }
            sort_key = sort_map.get(sort_by, 'orders')
            services.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
            
            return services[:limit]
        except Exception as e:
            log_general_error(
                f"Error getting service rankings: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    # ============================================================
    # متدهای کمکی برای پنل مدیریت
    # ============================================================
    
    def get_admin_button_tree(self) -> List[Dict[str, Any]]:
        """
        دریافت ساختار درختی برای پنل مدیریت
        
        بازگشت: لیست درختی دسته‌بندی‌ها با دکمه‌ها و زیرمنوها
        """
        try:
            categories = self._category_repo.get_all_admin()
            result = []
            
            for cat in categories:
                cat_dict = dict(cat)
                buttons = self._repository.get_by_category_admin(cat['id'])
                
                for btn in buttons:
                    if btn.get('has_submenu', 0) == 1:
                        btn['submenus'] = self.get_submenus(btn['id'])
                    else:
                        btn['submenus'] = []
                
                cat_dict['buttons'] = buttons
                cat_dict['button_count'] = len(buttons)
                result.append(cat_dict)
            
            return result
        except Exception as e:
            log_database_error(
                f"Error getting admin button tree: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_category_options(self) -> List[Dict[str, Any]]:
        """
        دریافت گزینه‌های دسته‌بندی برای انتخاب در فرم‌ها
        
        بازگشت: لیست دسته‌بندی‌ها با شناسه و نام
        """
        categories = self._category_repo.get_all_admin()
        return [{'id': cat['id'], 'name': cat['name'], 'location': cat.get('location', 'main')} for cat in categories]
    
    def get_parent_options(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        دریافت گزینه‌های دکمه‌های والد برای انتخاب در فرم‌ها
        
        پارامترها:
            category_id: (اختیاری) فیلتر بر اساس دسته‌بندی
        
        بازگشت: لیست دکمه‌های والد
        """
        try:
            if category_id:
                buttons = self._repository.get_parent_buttons(category_id)
            else:
                buttons = self._repository.get_parent_buttons()
            
            return [{'id': btn['id'], 'name': btn['name']} for btn in buttons]
        except Exception as e:
            log_database_error(
                f"Error getting parent options: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []


__all__ = [
    'ButtonService',
]