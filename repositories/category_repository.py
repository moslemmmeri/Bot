# repositories/category_repository.py
# ریپازیتوری دسته‌بندی‌ها

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime
from logger_config import logger
from .base_repository import BaseRepository
from models.category import Category, CategoryLocation
from utils.error_handler import log_database_error  # ✅ اضافه شد


class CategoryRepository(BaseRepository):
    """ریپازیتوری دسته‌بندی‌ها - مدیریت عملیات دیتابیس مربوط به دسته‌بندی‌ها"""
    
    def __init__(self, connection):
        super().__init__(connection, 'categories', 'id')
    
    # ============================================================
    # متدهای پایه
    # ============================================================
    
    def get_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """دریافت دسته‌بندی بر اساس شناسه"""
        try:
            return super().get_by_id(category_id)
        except Exception as e:
            log_database_error(
                f"Error getting category by id {category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_by_location(self, location: str) -> Optional[Dict[str, Any]]:
        """دریافت دسته‌بندی بر اساس مکان (main, more, other)"""
        try:
            return self.get_by_field('location', location)
        except Exception as e:
            log_database_error(
                f"Error getting category by location {location}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت تمام دسته‌بندی‌ها با صفحه‌بندی"""
        try:
            return super().get_all(limit, offset, order_by='sort_order, id')
        except Exception as e:
            log_database_error(
                f"Error getting all categories: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_active(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت دسته‌بندی‌های فعال"""
        try:
            query = """
                SELECT * FROM categories 
                WHERE is_active = 1 
                ORDER BY sort_order, id 
                LIMIT ? OFFSET ?
            """
            return self.custom_query(query, [limit, offset])
        except Exception as e:
            log_database_error(
                f"Error getting active categories: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_all_admin(self) -> List[Dict[str, Any]]:
        """دریافت تمام دسته‌بندی‌ها برای پنل مدیریت (بدون فیلتر)"""
        try:
            query = """
                SELECT * FROM categories 
                WHERE is_active = 1 
                ORDER BY sort_order, id
            """
            return self.custom_query(query)
        except Exception as e:
            log_database_error(
                f"Error getting all categories for admin: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    # ============================================================
    # دریافت دسته‌بندی‌ها با اطلاعات دکمه‌ها
    # ============================================================
    
    def get_with_buttons(self, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        دریافت دسته‌بندی‌هایی که حداقل یک دکمه فعال دارند
        
        پارامترها:
            location: (اختیاری) فیلتر بر اساس مکان
        """
        try:
            if location:
                query = """
                    SELECT DISTINCT c.* FROM categories c
                    INNER JOIN buttons b ON b.category_id = c.id
                    WHERE c.is_active = 1 
                    AND c.location = ?
                    AND b.is_active = 1
                    AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
                    ORDER BY c.sort_order, c.id
                """
                return self.custom_query(query, [location])
            else:
                query = """
                    SELECT DISTINCT c.* FROM categories c
                    INNER JOIN buttons b ON b.category_id = c.id
                    WHERE c.is_active = 1 
                    AND b.is_active = 1
                    AND (b.parent_button_id IS NULL OR b.parent_button_id = 0)
                    ORDER BY c.sort_order, c.id
                """
                return self.custom_query(query)
        except Exception as e:
            log_database_error(
                f"Error getting categories with buttons (location={location}): {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_with_button_count(self) -> List[Dict[str, Any]]:
        """
        دریافت دسته‌بندی‌ها به همراه تعداد دکمه‌های هر کدام
        """
        try:
            query = """
                SELECT 
                    c.*,
                    COUNT(b.id) as button_count,
                    COUNT(CASE WHEN b.has_submenu = 1 THEN 1 END) as submenu_count,
                    COUNT(CASE WHEN b.has_payment = 1 THEN 1 END) as payment_count
                FROM categories c
                LEFT JOIN buttons b ON c.id = b.category_id AND b.is_active = 1
                WHERE c.is_active = 1
                GROUP BY c.id
                ORDER BY c.sort_order, c.id
            """
            return self.custom_query(query)
        except Exception as e:
            log_database_error(
                f"Error getting categories with button count: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_buttons_count(self, category_id: int) -> int:
        """تعداد دکمه‌های فعال یک دسته‌بندی"""
        try:
            query = """
                SELECT COUNT(*) as count FROM buttons 
                WHERE category_id = ? AND is_active = 1 
                AND (parent_button_id IS NULL OR parent_button_id = 0)
            """
            result = self.custom_query_one(query, [category_id])
            return result.get('count', 0) if result else 0
        except Exception as e:
            log_database_error(
                f"Error getting buttons count for category {category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # عملیات ایجاد و به‌روزرسانی
    # ============================================================
    
    def create(self, name: str, icon: str = "📁", location: str = "main",
               sort_order: int = 0, columns: int = 2) -> Optional[int]:
        """
        ایجاد دسته‌بندی جدید
        
        پارامترها:
            name: نام دسته‌بندی
            icon: آیکون
            location: مکان (main, more, other)
            sort_order: ترتیب نمایش
            columns: تعداد ستون‌های پیش‌فرض
        
        بازگشت: شناسه دسته‌بندی ایجادشده
        """
        try:
            data = {
                'name': name,
                'icon': icon,
                'location': location,
                'sort_order': sort_order,
                'is_active': 1,
                'columns': columns,
                'created_at': datetime.now().isoformat()
            }
            return self.insert(data)
        except Exception as e:
            log_database_error(
                f"Error creating category '{name}': {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def update(self, category_id: int, data: Dict[str, Any]) -> bool:
        """به‌روزرسانی دسته‌بندی"""
        try:
            return super().update(category_id, data)
        except Exception as e:
            log_database_error(
                f"Error updating category {category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_name(self, category_id: int, name: str) -> bool:
        """به‌روزرسانی نام دسته‌بندی"""
        try:
            return self.update(category_id, {'name': name})
        except Exception as e:
            log_database_error(
                f"Error updating category name for {category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_icon(self, category_id: int, icon: str) -> bool:
        """به‌روزرسانی آیکون دسته‌بندی"""
        try:
            return self.update(category_id, {'icon': icon})
        except Exception as e:
            log_database_error(
                f"Error updating category icon for {category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_location(self, category_id: int, location: str) -> bool:
        """به‌روزرسانی مکان دسته‌بندی"""
        if location not in ['main', 'more', 'other']:
            return False
        try:
            return self.update(category_id, {'location': location})
        except Exception as e:
            log_database_error(
                f"Error updating category location for {category_id} to {location}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_columns(self, category_id: int, columns: Optional[int]) -> bool:
        """به‌روزرسانی تعداد ستون‌های دسته‌بندی"""
        if columns is not None and (columns < 1 or columns > 8):
            return False
        try:
            return self.update(category_id, {'columns': columns})
        except Exception as e:
            log_database_error(
                f"Error updating category columns for {category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def toggle_active(self, category_id: int) -> bool:
        """تغییر وضعیت فعال/غیرفعال دسته‌بندی"""
        try:
            category = self.get_by_id(category_id)
            if not category:
                return False
            new_status = 0 if category.get('is_active', 1) == 1 else 1
            return self.update(category_id, {'is_active': new_status})
        except Exception as e:
            log_database_error(
                f"Error toggling active status for category {category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_sort_order(self, category_id: int, sort_order: int) -> bool:
        """به‌روزرسانی ترتیب نمایش"""
        try:
            return self.update(category_id, {'sort_order': sort_order})
        except Exception as e:
            log_database_error(
                f"Error updating sort order for category {category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete(self, category_id: int) -> bool:
        """حذف یک دسته‌بندی و تمام دکمه‌های مرتبط با آن"""
        try:
            # دکمه‌ها با ON DELETE CASCADE حذف می‌شوند
            return super().delete(category_id)
        except Exception as e:
            log_database_error(
                f"Error deleting category {category_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # توابع کمکی
    # ============================================================
    
    def get_max_sort_order(self) -> int:
        """دریافت حداکثر sort_order در دسته‌بندی‌ها"""
        try:
            query = "SELECT MAX(sort_order) as max_order FROM categories"
            result = self.custom_query_one(query)
            return result.get('max_order', -1) if result else -1
        except Exception as e:
            log_database_error(
                f"Error getting max sort order: {str(e)}",
                traceback=traceback.format_exc()
            )
            return -1
    
    def get_default_categories(self) -> List[Dict[str, Any]]:
        """
        دریافت دسته‌بندی‌های پیش‌فرض (اصلی)
        """
        try:
            return self.custom_query(
                "SELECT * FROM categories WHERE location IN ('main', 'more', 'other') AND is_active = 1"
            )
        except Exception as e:
            log_database_error(
                f"Error getting default categories: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_category_location_counts(self) -> Dict[str, int]:
        """
        دریافت تعداد دسته‌بندی‌ها در هر مکان
        """
        try:
            query = """
                SELECT location, COUNT(*) as count 
                FROM categories 
                WHERE is_active = 1 
                GROUP BY location
            """
            results = self.custom_query(query)
            return {row['location']: row['count'] for row in results}
        except Exception as e:
            log_database_error(
                f"Error getting category location counts: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {}
    
    def get_categories_with_columns_info(self) -> List[Dict[str, Any]]:
        """
        دریافت دسته‌بندی‌ها با اطلاعات ستون‌ها
        """
        try:
            from database.db_columns import get_effective_columns
            
            categories = self.get_all_admin()
            result = []
            for cat in categories:
                cat_dict = dict(cat)
                cat_dict['effective_columns'] = get_effective_columns(category_id=cat['id'])
                cat_dict['has_custom_columns'] = cat.get('columns') is not None
                result.append(cat_dict)
            
            return result
        except Exception as e:
            log_database_error(
                f"Error getting categories with columns info: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def ensure_default_categories(self) -> None:
        """
        اطمینان از وجود دسته‌بندی‌های پیش‌فرض
        """
        default_categories = [
            {'name': 'منوی اصلی', 'location': 'main', 'icon': '🏠', 'columns': 2},
            {'name': 'منوی بیشتر', 'location': 'more', 'icon': '➕', 'columns': 2},
            {'name': 'دیگر خدمات', 'location': 'other', 'icon': '🔧', 'columns': 2},
        ]
        
        for cat_data in default_categories:
            try:
                existing = self.get_by_location(cat_data['location'])
                if not existing:
                    self.create(
                        name=cat_data['name'],
                        icon=cat_data['icon'],
                        location=cat_data['location'],
                        columns=cat_data['columns']
                    )
                    logger.info(f"✅ Default category created: {cat_data['name']}")
            except Exception as e:
                log_database_error(
                    f"Error ensuring default category '{cat_data['name']}': {str(e)}",
                    traceback=traceback.format_exc()
                )


__all__ = [
    'CategoryRepository',
]