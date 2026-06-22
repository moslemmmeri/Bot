# services/cache_service.py
# سرویس مدیریت کش (Cache) - رابط کاربری برای استفاده از کش در سایر سرویس‌ها
# شامل: مدیریت کش کاربران، دکمه‌ها، دسته‌بندی‌ها، سفارشات، تنظیمات و برندینگ

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any, Callable, Awaitable
from logger_config import logger
from cache import CacheManager, get_cache_manager
from cache_keys import CacheKeys, CacheKeyBuilder
from config import config
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class CacheService:
    """
    سرویس مدیریت کش - رابط کاربری برای کش کردن داده‌ها
    استفاده از این سرویس در سایر سرویس‌ها برای افزایش عملکرد
    """
    
    def __init__(self, connection, cache_manager: Optional[CacheManager] = None):
        """
        پارامترها:
            connection: اتصال به دیتابیس (برای سازگاری با سایر سرویس‌ها)
            cache_manager: مدیر کش (در صورت عدم ارائه، از نمونه سراسری استفاده می‌شود)
        """
        self._connection = connection
        self._cache = cache_manager or get_cache_manager()
        self._enabled = self._cache._enabled
        self._default_ttl = config.REDIS_CACHE_TTL
    
    @property
    def enabled(self) -> bool:
        """آیا کش فعال است"""
        return self._enabled
    
    # ============================================================
    # متدهای عمومی کش
    # ============================================================
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        دریافت مقدار از کش
        
        پارامترها:
            key: کلید کش
            default: مقدار پیش‌فرض در صورت عدم وجود
        
        بازگشت: مقدار یا default
        """
        if not self._enabled:
            return default
        return await self._cache.get(key, default)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        ذخیره مقدار در کش
        
        پارامترها:
            key: کلید کش
            value: مقدار
            ttl: زمان انقضا (ثانیه)
        
        بازگشت: True در صورت موفقیت
        """
        if not self._enabled:
            return False
        return await self._cache.set(key, value, ttl)
    
    async def delete(self, *keys: str) -> int:
        """
        حذف یک یا چند کلید از کش
        
        پارامترها:
            *keys: کلیدهای مورد نظر
        
        بازگشت: تعداد کلیدهای حذف‌شده
        """
        if not self._enabled:
            return 0
        return await self._cache.delete(*keys)
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        حذف کلیدهایی که با الگوی مشخص مطابقت دارند
        
        پارامترها:
            pattern: الگوی کلید
        
        بازگشت: تعداد کلیدهای حذف‌شده
        """
        if not self._enabled:
            return 0
        return await self._cache.delete_pattern(pattern)
    
    async def exists(self, key: str) -> bool:
        """
        بررسی وجود کلید در کش
        
        پارامترها:
            key: کلید مورد نظر
        
        بازگشت: True اگر کلید وجود داشته باشد
        """
        if not self._enabled:
            return False
        return await self._cache.exists(key)
    
    async def get_or_set(self, key: str, func: Callable[[], Awaitable[Any]], ttl: Optional[int] = None) -> Any:
        """
        دریافت از کش، در صورت عدم وجود، تابع را اجرا و نتیجه را کش می‌کند
        
        پارامترها:
            key: کلید کش
            func: تابع async برای اجرا در صورت عدم وجود
            ttl: زمان انقضا (اختیاری)
        
        بازگشت: مقدار
        """
        if not self._enabled:
            return await func()
        return await self._cache.get_or_set(key, func, ttl)
    
    # ============================================================
    # کش کاربران
    # ============================================================
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات کاربر از کش"""
        key = CacheKeyBuilder.user(user_id)
        return await self.get(key)
    
    async def set_user(self, user_id: int, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """ذخیره اطلاعات کاربر در کش"""
        key = CacheKeyBuilder.user(user_id)
        return await self.set(key, data, ttl)
    
    async def delete_user(self, user_id: int) -> bool:
        """حذف اطلاعات کاربر از کش"""
        key = CacheKeyBuilder.user(user_id)
        deleted = await self.delete(key)
        return deleted > 0
    
    async def invalidate_users(self) -> int:
        """پاک کردن کش همه کاربران"""
        return await self.delete_pattern("user:*")
    
    # ============================================================
    # کش دکمه‌ها
    # ============================================================
    
    async def get_button(self, button_id: int) -> Optional[Dict[str, Any]]:
        """دریافت دکمه از کش"""
        key = CacheKeyBuilder.button(button_id)
        return await self.get(key)
    
    async def set_button(self, button_id: int, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """ذخیره دکمه در کش"""
        key = CacheKeyBuilder.button(button_id)
        return await self.set(key, data, ttl)
    
    async def delete_button(self, button_id: int) -> bool:
        """حذف دکمه از کش"""
        key = CacheKeyBuilder.button(button_id)
        deleted = await self.delete(key)
        return deleted > 0
    
    async def get_buttons_by_location(self, location: str) -> Optional[List[Dict[str, Any]]]:
        """دریافت دکمه‌های یک مکان از کش"""
        key = CacheKeyBuilder.build(CacheKeys.BUTTONS_BY_LOCATION, location=location)
        return await self.get(key)
    
    async def set_buttons_by_location(self, location: str, data: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """ذخیره دکمه‌های یک مکان در کش"""
        key = CacheKeyBuilder.build(CacheKeys.BUTTONS_BY_LOCATION, location=location)
        return await self.set(key, data, ttl)
    
    async def invalidate_buttons(self) -> int:
        """پاک کردن کش همه دکمه‌ها"""
        return await self.delete_pattern("button:*")
    
    async def invalidate_buttons_by_location(self, location: str) -> int:
        """پاک کردن کش دکمه‌های یک مکان"""
        key = CacheKeyBuilder.build(CacheKeys.BUTTONS_BY_LOCATION, location=location)
        return await self.delete(key)
    
    # ============================================================
    # کش دسته‌بندی‌ها
    # ============================================================
    
    async def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """دریافت دسته‌بندی از کش"""
        key = CacheKeyBuilder.category(category_id)
        return await self.get(key)
    
    async def set_category(self, category_id: int, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """ذخیره دسته‌بندی در کش"""
        key = CacheKeyBuilder.category(category_id)
        return await self.set(key, data, ttl)
    
    async def delete_category(self, category_id: int) -> bool:
        """حذف دسته‌بندی از کش"""
        key = CacheKeyBuilder.category(category_id)
        deleted = await self.delete(key)
        return deleted > 0
    
    async def get_categories_all(self) -> Optional[List[Dict[str, Any]]]:
        """دریافت همه دسته‌بندی‌ها از کش"""
        key = CacheKeys.CATEGORIES_ALL
        return await self.get(key)
    
    async def set_categories_all(self, data: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """ذخیره همه دسته‌بندی‌ها در کش"""
        key = CacheKeys.CATEGORIES_ALL
        return await self.set(key, data, ttl)
    
    async def invalidate_categories(self) -> int:
        """پاک کردن کش همه دسته‌بندی‌ها"""
        return await self.delete_pattern("category:*")
    
    # ============================================================
    # کش سفارشات
    # ============================================================
    
    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """دریافت سفارش از کش"""
        key = CacheKeyBuilder.order(order_id)
        return await self.get(key)
    
    async def set_order(self, order_id: int, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """ذخیره سفارش در کش"""
        key = CacheKeyBuilder.order(order_id)
        return await self.set(key, data, ttl)
    
    async def delete_order(self, order_id: int) -> bool:
        """حذف سفارش از کش"""
        key = CacheKeyBuilder.order(order_id)
        deleted = await self.delete(key)
        return deleted > 0
    
    async def get_orders_by_status(self, status: str) -> Optional[List[Dict[str, Any]]]:
        """دریافت سفارشات بر اساس وضعیت از کش"""
        key = CacheKeyBuilder.build(CacheKeys.ORDERS_BY_STATUS, status=status)
        return await self.get(key)
    
    async def set_orders_by_status(self, status: str, data: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """ذخیره سفارشات بر اساس وضعیت در کش"""
        key = CacheKeyBuilder.build(CacheKeys.ORDERS_BY_STATUS, status=status)
        return await self.set(key, data, ttl)
    
    async def get_orders_by_user(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """دریافت سفارشات یک کاربر از کش"""
        key = CacheKeyBuilder.build(CacheKeys.ORDERS_BY_USER, user_id=user_id)
        return await self.get(key)
    
    async def set_orders_by_user(self, user_id: int, data: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """ذخیره سفارشات یک کاربر در کش"""
        key = CacheKeyBuilder.build(CacheKeys.ORDERS_BY_USER, user_id=user_id)
        return await self.set(key, data, ttl)
    
    async def invalidate_orders(self) -> int:
        """پاک کردن کش همه سفارشات"""
        return await self.delete_pattern("order:*")
    
    async def invalidate_orders_by_status(self, status: str) -> int:
        """پاک کردن کش سفارشات با وضعیت خاص"""
        key = CacheKeyBuilder.build(CacheKeys.ORDERS_BY_STATUS, status=status)
        return await self.delete(key)
    
    # ============================================================
    # کش تنظیمات
    # ============================================================
    
    async def get_setting(self, key: str) -> Optional[str]:
        """دریافت تنظیمات از کش"""
        cache_key = CacheKeyBuilder.setting(key)
        return await self.get(cache_key)
    
    async def set_setting(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """ذخیره تنظیمات در کش"""
        cache_key = CacheKeyBuilder.setting(key)
        return await self.set(cache_key, value, ttl)
    
    async def delete_setting(self, key: str) -> bool:
        """حذف تنظیمات از کش"""
        cache_key = CacheKeyBuilder.setting(key)
        deleted = await self.delete(cache_key)
        return deleted > 0
    
    async def get_settings_all(self) -> Optional[Dict[str, str]]:
        """دریافت همه تنظیمات از کش"""
        key = CacheKeys.SETTINGS_ALL
        return await self.get(key)
    
    async def set_settings_all(self, data: Dict[str, str], ttl: Optional[int] = None) -> bool:
        """ذخیره همه تنظیمات در کش"""
        key = CacheKeys.SETTINGS_ALL
        return await self.set(key, data, ttl)
    
    async def invalidate_settings(self) -> int:
        """پاک کردن کش تنظیمات"""
        return await self.delete_pattern("setting:*")
    
    # ============================================================
    # کش برندینگ
    # ============================================================
    
    async def get_branding(self, key: str) -> Optional[str]:
        """دریافت متن برندینگ از کش"""
        cache_key = CacheKeyBuilder.branding(key)
        return await self.get(cache_key)
    
    async def set_branding(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """ذخیره متن برندینگ در کش"""
        cache_key = CacheKeyBuilder.branding(key)
        return await self.set(cache_key, value, ttl)
    
    async def delete_branding(self, key: str) -> bool:
        """حذف متن برندینگ از کش"""
        cache_key = CacheKeyBuilder.branding(key)
        deleted = await self.delete(cache_key)
        return deleted > 0
    
    async def get_branding_all(self) -> Optional[Dict[str, str]]:
        """دریافت همه متون برندینگ از کش"""
        key = CacheKeys.BRANDING_ALL
        return await self.get(key)
    
    async def set_branding_all(self, data: Dict[str, str], ttl: Optional[int] = None) -> bool:
        """ذخیره همه متون برندینگ در کش"""
        key = CacheKeys.BRANDING_ALL
        return await self.set(key, data, ttl)
    
    async def invalidate_branding(self) -> int:
        """پاک کردن کش برندینگ"""
        return await self.delete_pattern("branding:*")
    
    # ============================================================
    # کش آمار
    # ============================================================
    
    async def get_stats_dashboard(self) -> Optional[Dict[str, Any]]:
        """دریافت آمار داشبورد از کش"""
        key = CacheKeys.STATS_DASHBOARD
        return await self.get(key)
    
    async def set_stats_dashboard(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """ذخیره آمار داشبورد در کش"""
        key = CacheKeys.STATS_DASHBOARD
        return await self.set(key, data, ttl)
    
    async def invalidate_stats(self) -> int:
        """پاک کردن کش آمار"""
        return await self.delete_pattern("stats:*")
    
    # ============================================================
    # کش کاربران (ادمین‌ها)
    # ============================================================
    
    async def get_admin(self, user_id: int) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات ادمین از کش"""
        key = CacheKeyBuilder.admin(user_id)
        return await self.get(key)
    
    async def set_admin(self, user_id: int, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """ذخیره اطلاعات ادمین در کش"""
        key = CacheKeyBuilder.admin(user_id)
        return await self.set(key, data, ttl)
    
    async def delete_admin(self, user_id: int) -> bool:
        """حذف اطلاعات ادمین از کش"""
        key = CacheKeyBuilder.admin(user_id)
        deleted = await self.delete(key)
        return deleted > 0
    
    async def get_admins_all(self) -> Optional[List[Dict[str, Any]]]:
        """دریافت لیست همه ادمین‌ها از کش"""
        key = CacheKeys.ADMINS_ALL
        return await self.get(key)
    
    async def set_admins_all(self, data: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """ذخیره لیست همه ادمین‌ها در کش"""
        key = CacheKeys.ADMINS_ALL
        return await self.set(key, data, ttl)
    
    async def invalidate_admins(self) -> int:
        """پاک کردن کش ادمین‌ها"""
        return await self.delete_pattern("admin:*")
    
    # ============================================================
    # کش نسخه‌سازی (Versioning)
    # ============================================================
    
    async def get_versions(self, button_id: int) -> Optional[List[Dict[str, Any]]]:
        """دریافت لیست نسخه‌های یک دکمه از کش"""
        key = CacheKeyBuilder.build(CacheKeys.VERSIONS_BY_BUTTON, button_id=button_id)
        return await self.get(key)
    
    async def set_versions(self, button_id: int, data: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """ذخیره لیست نسخه‌های یک دکمه در کش"""
        key = CacheKeyBuilder.build(CacheKeys.VERSIONS_BY_BUTTON, button_id=button_id)
        return await self.set(key, data, ttl)
    
    async def invalidate_versions(self, button_id: Optional[int] = None) -> int:
        """پاک کردن کش نسخه‌ها"""
        if button_id:
            key = CacheKeyBuilder.build(CacheKeys.VERSIONS_BY_BUTTON, button_id=button_id)
            return await self.delete(key)
        return await self.delete_pattern("versions:*")
    
    # ============================================================
    # کش ستون‌های منو
    # ============================================================
    
    async def get_effective_columns(self, button_id: Optional[int] = None,
                                   category_id: Optional[int] = None) -> Optional[int]:
        """دریافت ستون‌های مؤثر از کش"""
        key = CacheKeyBuilder.effective_columns(button_id, category_id)
        return await self.get(key)
    
    async def set_effective_columns(self, value: int, button_id: Optional[int] = None,
                                   category_id: Optional[int] = None, ttl: Optional[int] = None) -> bool:
        """ذخیره ستون‌های مؤثر در کش"""
        key = CacheKeyBuilder.effective_columns(button_id, category_id)
        return await self.set(key, value, ttl)
    
    async def invalidate_columns(self) -> int:
        """پاک کردن کش ستون‌ها"""
        return await self.delete_pattern("columns:*")
    
    # ============================================================
    # کش قیمت‌ها
    # ============================================================
    
    async def get_button_price(self, button_id: int) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات قیمت دکمه از کش"""
        key = CacheKeyBuilder.build(CacheKeys.BUTTON_PRICE, button_id=button_id)
        return await self.get(key)
    
    async def set_button_price(self, button_id: int, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """ذخیره اطلاعات قیمت دکمه در کش"""
        key = CacheKeyBuilder.build(CacheKeys.BUTTON_PRICE, button_id=button_id)
        return await self.set(key, data, ttl)
    
    async def invalidate_prices(self) -> int:
        """پاک کردن کش قیمت‌ها"""
        return await self.delete_pattern("price:*")
    
    # ============================================================
    # متدهای عمومی برای بی‌اعتبارسازی گروهی
    # ============================================================
    
    async def invalidate_all(self) -> Dict[str, int]:
        """
        پاک کردن همه کش‌ها (به جز Rate Limit)
        
        بازگشت: دیکشنری شامل تعداد کلیدهای حذف‌شده برای هر الگو
        """
        patterns = [
            "user:*",
            "button:*",
            "category:*",
            "order:*",
            "setting:*",
            "branding:*",
            "stats:*",
            "admin:*",
            "versions:*",
            "columns:*",
            "price:*",
            "option:*",
            "question:*",
            "validation:*",
            "error:*",
        ]
        
        result = {}
        total = 0
        for pattern in patterns:
            count = await self.delete_pattern(pattern)
            result[pattern] = count
            total += count
        
        result['total'] = total
        logger.info(f"🧹 همه کش‌ها پاکسازی شدند. {total} کلید حذف شد.")
        return result
    
    async def invalidate_cache_by_prefix(self, prefix: str) -> int:
        """
        پاک کردن کلیدهایی که با پیشوند مشخص شروع می‌شوند
        
        پارامترها:
            prefix: پیشوند (مثلاً "user" یا "button")
        
        بازگشت: تعداد کلیدهای حذف‌شده
        """
        return await self.delete_pattern(f"{prefix}:*")
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کش
        
        بازگشت: دیکشنری شامل وضعیت کش
        """
        try:
            if not self._enabled:
                return {'enabled': False, 'message': 'Cache is disabled'}
            
            redis = await self._cache._get_redis()
            if not redis:
                return {'enabled': True, 'connected': False, 'message': 'Redis not connected'}
            
            keys = await redis.keys("*")
            return {
                'enabled': True,
                'connected': True,
                'total_keys': len(keys),
                'key_count_by_pattern': {
                    'user': len([k for k in keys if k.startswith('user:')]),
                    'button': len([k for k in keys if k.startswith('button:')]),
                    'category': len([k for k in keys if k.startswith('category:')]),
                    'order': len([k for k in keys if k.startswith('order:')]),
                    'setting': len([k for k in keys if k.startswith('setting:')]),
                    'branding': len([k for k in keys if k.startswith('branding:')]),
                    'stats': len([k for k in keys if k.startswith('stats:')]),
                    'admin': len([k for k in keys if k.startswith('admin:')]),
                    'other': len([k for k in keys if not any(k.startswith(p) for p in ['user:', 'button:', 'category:', 'order:', 'setting:', 'branding:', 'stats:', 'admin:'])])
                }
            }
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error getting cache stats: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {'enabled': self._enabled, 'error': str(e)}
    
    async def clear_all(self) -> bool:
        """
        پاک کردن کامل کش (هشدار!)
        
        بازگشت: True در صورت موفقیت
        """
        if not self._enabled:
            return False
        
        try:
            redis = await self._cache._get_redis()
            if not redis:
                return False
            
            await redis.flushdb()
            logger.warning("🗑️ همه کش‌ها پاک شدند (flushdb)")
            return True
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error clearing all cache: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False


__all__ = [
    'CacheService',
]