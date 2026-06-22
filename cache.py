# cache.py
# مدیریت اتصال به Redis و عملیات کش کردن

import asyncio
import json
import hashlib
import time
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Any, Optional, Union
from datetime import timedelta
from config import config
from logger_config import logger
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis-py not installed. Redis cache will be disabled.")


class CacheManager:
    """
    مدیریت کش با استفاده از Redis.
    اگر Redis در دسترس نباشد، یک کش درون‌حافظه‌ی ساده (با احتیاط) استفاده می‌شود.
    """
    
    def __init__(self):
        self._redis = None
        self._enabled = config.REDIS_ENABLED and REDIS_AVAILABLE
        self._default_ttl = config.REDIS_CACHE_TTL
        self._memory_cache = {}  # برای مواقعی که Redis غیرفعال است (فقط برای کلیدهای کوچک)
        self._memory_cache_ttl = {}  # زمان انقضای کش درون‌حافظه
        self._lock = asyncio.Lock()
        
        if self._enabled:
            self._connect()
    
    def _connect(self):
        """اتصال به Redis"""
        try:
            if not REDIS_AVAILABLE:
                self._enabled = False
                return
            
            self._redis = redis.from_url(
                config.get_redis_url(),
                decode_responses=True,
                max_connections=10
            )
            logger.info("✅ Redis connection established successfully.")
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Failed to connect to Redis: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._enabled = False
            self._redis = None
    
    async def _get_redis(self):
        """دریافت کلاینت Redis با بررسی اتصال"""
        if not self._enabled or not self._redis:
            return None
        
        try:
            # بررسی اتصال
            await self._redis.ping()
            return self._redis
        except Exception as e:
            logger.warning(f"Redis connection lost, attempting to reconnect: {e}")
            self._connect()
            if self._redis:
                try:
                    await self._redis.ping()
                    return self._redis
                except:
                    return None
            return None
    
    def _get_memory(self, key: str) -> Optional[Any]:
        """دریافت از کش درون‌حافظه (در صورت عدم دسترسی به Redis)"""
        if key not in self._memory_cache:
            return None
        
        # بررسی انقضا
        if key in self._memory_cache_ttl:
            if time.time() > self._memory_cache_ttl[key]:
                del self._memory_cache[key]
                del self._memory_cache_ttl[key]
                return None
        
        return self._memory_cache[key]
    
    def _set_memory(self, key: str, value: Any, ttl: int):
        """ذخیره در کش درون‌حافظه"""
        self._memory_cache[key] = value
        self._memory_cache_ttl[key] = time.time() + ttl
    
    def _delete_memory(self, key: str):
        """حذف از کش درون‌حافظه"""
        self._memory_cache.pop(key, None)
        self._memory_cache_ttl.pop(key, None)
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """
        تولید کلید یکتا برای کش.
        
        پارامترها:
            prefix: پیشوند کلید
            *args: آرگومان‌های موقعیتی
            **kwargs: آرگومان‌های نام‌دار
        
        بازگشت: کلید تولیدشده
        """
        key_parts = [prefix]
        for arg in args:
            if arg is not None:
                key_parts.append(str(arg))
        
        if kwargs:
            # مرتب‌سازی برای یکنواختی
            sorted_items = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_items if v is not None])
        
        # اگر کلید خیلی طولانی شد، هش بگیر
        raw_key = "_".join(key_parts)
        if len(raw_key) > 200:
            hash_obj = hashlib.md5(raw_key.encode())
            return f"{prefix}_{hash_obj.hexdigest()[:16]}"
        
        return raw_key
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        دریافت مقدار از کش.
        
        پارامترها:
            key: کلید کش
            default: مقدار پیش‌فرض در صورت عدم وجود
        
        بازگشت: مقدار یا default
        """
        try:
            if self._enabled:
                redis_client = await self._get_redis()
                if redis_client:
                    value = await redis_client.get(key)
                    if value is not None:
                        try:
                            return json.loads(value)
                        except:
                            return value
                    return default
            
            # Fallback به کش درون‌حافظه
            return self._get_memory(key) or default
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error getting from cache {key}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        ذخیره مقدار در کش.
        
        پارامترها:
            key: کلید کش
            value: مقدار (JSON Serializable)
            ttl: زمان انقضا به ثانیه (در صورت عدم ارائه، از مقدار پیش‌فرض استفاده می‌شود)
        
        بازگشت: True در صورت موفقیت
        """
        try:
            if ttl is None:
                ttl = self._default_ttl
            
            # سریالایز کردن مقدار
            try:
                serialized = json.dumps(value, ensure_ascii=False)
            except:
                serialized = str(value)
            
            if self._enabled:
                redis_client = await self._get_redis()
                if redis_client:
                    await redis_client.setex(key, ttl, serialized)
                    return True
            
            # Fallback به کش درون‌حافظه
            self._set_memory(key, value, ttl)
            return True
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error setting cache {key}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    async def delete(self, *keys: str) -> int:
        """
        حذف یک یا چند کلید از کش.
        
        پارامترها:
            *keys: کلیدهای مورد نظر
        
        بازگشت: تعداد کلیدهای حذف‌شده
        """
        try:
            deleted = 0
            
            if self._enabled:
                redis_client = await self._get_redis()
                if redis_client:
                    for key in keys:
                        result = await redis_client.delete(key)
                        deleted += result
                else:
                    # حذف از کش درون‌حافظه
                    for key in keys:
                        if key in self._memory_cache:
                            self._delete_memory(key)
                            deleted += 1
            
            return deleted
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error deleting cache keys {keys}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        حذف کلیدهایی که با الگوی مشخص مطابقت دارند.
        
        پارامترها:
            pattern: الگوی کلید (مثلاً "user:*")
        
        بازگشت: تعداد کلیدهای حذف‌شده
        """
        try:
            if self._enabled:
                redis_client = await self._get_redis()
                if redis_client:
                    keys = await redis_client.keys(pattern)
                    if keys:
                        return await redis_client.delete(*keys)
            else:
                # حذف از کش درون‌حافظه (فقط برای کلیدهای ساده)
                if pattern.endswith("*"):
                    prefix = pattern[:-1]
                    to_delete = [k for k in self._memory_cache.keys() if k.startswith(prefix)]
                    for key in to_delete:
                        self._delete_memory(key)
                    return len(to_delete)
            
            return 0
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error deleting pattern from cache: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        بررسی وجود کلید در کش.
        
        پارامترها:
            key: کلید مورد نظر
        
        بازگشت: True اگر کلید وجود داشته باشد
        """
        try:
            if self._enabled:
                redis_client = await self._get_redis()
                if redis_client:
                    return await redis_client.exists(key) > 0
            
            return key in self._memory_cache
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error checking cache existence: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        افزایش مقدار یک کلید عددی.
        
        پارامترها:
            key: کلید مورد نظر
            amount: مقدار افزایش
        
        بازگشت: مقدار جدید یا None در صورت خطا
        """
        try:
            if self._enabled:
                redis_client = await self._get_redis()
                if redis_client:
                    return await redis_client.incrby(key, amount)
            
            # Fallback (همراه با ذخیره در کش درون‌حافظه)
            value = self._get_memory(key) or 0
            new_value = int(value) + amount
            self._set_memory(key, new_value, self._default_ttl)
            return new_value
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error incrementing cache key {key}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    async def get_or_set(self, key: str, func, ttl: Optional[int] = None) -> Any:
        """
        دریافت از کش، در صورت عدم وجود، تابع را اجرا و نتیجه را کش می‌کند.
        
        پارامترها:
            key: کلید کش
            func: تابع async برای اجرا در صورت عدم وجود
            ttl: زمان انقضا (اختیاری)
        
        بازگشت: مقدار
        """
        # ابتدا از کش بخوان
        value = await self.get(key)
        if value is not None:
            return value
        
        # اجرای تابع
        try:
            result = await func()
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error executing func in get_or_set for key {key}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
        
        if result is not None:
            await self.set(key, result, ttl)
        
        return result


# ==================== توابع کمکی سراسری ====================

_cache_manager = None


def get_cache_manager() -> CacheManager:
    """دریافت آبجکت سراسری CacheManager (Singleton)"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# ==================== توابع راحت‌تر برای استفاده ====================

async def cache_get(key: str, default: Any = None) -> Any:
    """دریافت از کش"""
    return await get_cache_manager().get(key, default)


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """ذخیره در کش"""
    return await get_cache_manager().set(key, value, ttl)


async def cache_delete(*keys: str) -> int:
    """حذف از کش"""
    return await get_cache_manager().delete(*keys)


async def cache_delete_pattern(pattern: str) -> int:
    """حذف با الگو"""
    return await get_cache_manager().delete_pattern(pattern)


async def cache_exists(key: str) -> bool:
    """بررسی وجود"""
    return await get_cache_manager().exists(key)


async def cache_get_or_set(key: str, func, ttl: Optional[int] = None) -> Any:
    """دریافت یا محاسبه و ذخیره"""
    return await get_cache_manager().get_or_set(key, func, ttl)


# ==================== ثابت‌های کلیدهای کش ====================

class CacheKeys:
    """ثابت‌های کلیدهای کش برای استفاده در سراسر پروژه"""
    
    # کاربران
    USER = "user:{user_id}"
    USERS_LIST = "users:list:{page}:{limit}"
    USERS_SEARCH = "users:search:{keyword}"
    USER_STATS = "user:stats:{user_id}"
    
    # دکمه‌ها
    BUTTON = "button:{button_id}"
    BUTTONS_BY_LOCATION = "buttons:location:{location}"
    BUTTONS_BY_CATEGORY = "buttons:category:{category_id}"
    BUTTONS_BY_PARENT = "buttons:parent:{parent_id}"
    ALL_BUTTONS = "buttons:all"
    
    # دسته‌بندی‌ها
    CATEGORY = "category:{category_id}"
    CATEGORIES_ALL = "categories:all"
    CATEGORIES_WITH_BUTTONS = "categories:with_buttons:{location}"
    CATEGORIES_ADMIN = "categories:admin"
    
    # سوالات
    QUESTIONS_BY_BUTTON = "questions:button:{button_id}"
    QUESTION = "question:{question_id}"
    OPTIONS_BY_QUESTION = "options:question:{question_id}"
    CONDITIONS_BY_QUESTION = "conditions:question:{question_id}"
    
    # سفارشات
    ORDERS_ALL = "orders:all"
    ORDERS_BY_STATUS = "orders:status:{status}"
    ORDER = "order:{order_id}"
    ORDER_STATS = "orders:stats"
    ORDERS_SEARCH = "orders:search:{keyword}"
    
    # تنظیمات
    SETTING = "setting:{key}"
    SETTINGS_ALL = "settings:all"
    DEFAULT_COLUMNS = "settings:default_menu_columns"
    
    # برندینگ
    BRANDING = "branding:{key}"
    BRANDING_ALL = "branding:all"
    
    # آمار
    STATS_DASHBOARD = "stats:dashboard"
    STATS_BUTTON = "stats:button:{button_id}"
    STATS_TOP_BUTTONS = "stats:top:{sort_by}:{limit}"
    STATS_REVENUE_PERIOD = "stats:revenue:{days}"
    
    # ادمین‌ها
    ADMINS_ALL = "admins:all"
    ADMIN = "admin:{user_id}"
    ADMIN_STATS = "admins:stats"
    ADMIN_EXISTS = "admin:exists:{user_id}"
    
    @staticmethod
    def user(user_id: int) -> str:
        return f"user:{user_id}"
    
    @staticmethod
    def button(button_id: int) -> str:
        return f"button:{button_id}"
    
    @staticmethod
    def category(category_id: int) -> str:
        return f"category:{category_id}"
    
    @staticmethod
    def question(question_id: int) -> str:
        return f"question:{question_id}"
    
    @staticmethod
    def order(order_id: int) -> str:
        return f"order:{order_id}"
    
    @staticmethod
    def setting(key: str) -> str:
        return f"setting:{key}"
    
    @staticmethod
    def branding(key: str) -> str:
        return f"branding:{key}"


__all__ = [
    'CacheManager',
    'get_cache_manager',
    'cache_get',
    'cache_set',
    'cache_delete',
    'cache_delete_pattern',
    'cache_exists',
    'cache_get_or_set',
    'CacheKeys',
]