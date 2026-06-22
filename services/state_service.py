# services/state_service.py
# سرویس مدیریت وضعیت کاربران (State Service)
# جایگزین دیکشنری سراسری user_states با استفاده از Redis یا دیتابیس
# پشتیبانی از TTL و fallback به حافظه‌ی درون‌برنامه در صورت عدم دسترسی به Redis

import time
import json
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
from logger_config import logger
from config import config
from cache import CacheManager, get_cache_manager
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class StateService:
    """
    سرویس مدیریت وضعیت کاربران (State Service)
    
    این سرویس جایگزین دیکشنری سراسری `user_states` می‌شود و از Redis برای
    ذخیره‌سازی وضعیت کاربران با قابلیت انقضا (TTL) استفاده می‌کند.
    
    ویژگی‌ها:
    - ذخیره‌سازی وضعیت کاربران در Redis با TTL قابل تنظیم
    - Fallback به حافظه‌ی درون‌برنامه در صورت عدم دسترسی به Redis
    - پشتیبانی از کلیدهای تو در تو (nested keys)
    - قابلیت پاکسازی خودکار وضعیت‌های منقضی‌شده
    - آمارگیری از وضعیت‌های ذخیره‌شده
    
    استفاده:
        state_service = StateService()
        await state_service.set_state(user_id, "main")
        state = await state_service.get_state(user_id)
        await state_service.clear_state(user_id)
    """
    
    # پیشوند کلیدهای Redis برای جلوگیری از تداخل
    STATE_KEY_PREFIX = "user_state:"
    
    # پیشوند برای کلیدهای nested (برای ذخیره‌ی دیکشنری کامل)
    STATE_DATA_KEY_PREFIX = "user_state_data:"
    
    # مقدار پیش‌فرض TTL (ثانیه) - از config یا ۳۶۰۰ ثانیه (۱ ساعت)
    DEFAULT_TTL = getattr(config, 'STATE_TTL', 3600)  # 1 hour
    
    # نوع ذخیره‌سازی: 'redis' یا 'memory'
    STORAGE_TYPE = getattr(config, 'STATE_STORAGE_TYPE', 'redis')
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        مقداردهی اولیه سرویس وضعیت
        
        پارامترها:
            cache_manager: آبجکت CacheManager (در صورت عدم ارائه، از نمونه‌ی سراسری استفاده می‌شود)
        """
        self._cache = cache_manager or get_cache_manager()
        self._enabled = self._cache._enabled  # وضعیت Redis از CacheManager
        self._ttl = self.DEFAULT_TTL
        
        # Fallback به حافظه‌ی درون‌برنامه در صورت عدم دسترسی به Redis
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._memory_expiry: Dict[str, float] = {}  # زمان انقضای هر کلید (timestamp)
        
        # اگر Redis فعال نیست، از حافظه استفاده می‌کنیم
        if not self._enabled:
            logger.warning("⚠️ Redis is disabled. StateService will use in-memory storage (not persistent).")
        
        # آمار
        self._stats = {
            'total_sets': 0,
            'total_gets': 0,
            'total_clears': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'fallback_hits': 0,
        }
        
        logger.info(f"✅ StateService initialized (storage: {'Redis' if self._enabled else 'Memory'}, TTL: {self._ttl}s)")
    
    # ============================================================
    # متدهای اصلی وضعیت
    # ============================================================
    
    async def set_state(self, user_id: int, state: Union[str, Dict, Any], ttl: Optional[int] = None) -> bool:
        """
        ذخیره‌سازی وضعیت کاربر
        
        پارامترها:
            user_id: شناسه کاربر
            state: وضعیت (رشته، دیکشنری یا هر مقدار قابل JSON سریالایز)
            ttl: زمان انقضا به ثانیه (در صورت عدم ارائه، از مقدار پیش‌فرض استفاده می‌شود)
        
        بازگشت: True در صورت موفقیت
        """
        key = self._get_state_key(user_id)
        ttl = ttl or self._ttl
        
        try:
            # سریالایز کردن وضعیت
            serialized = self._serialize_state(state)
            
            # ذخیره در Redis (اگر فعال باشد)
            if self._enabled:
                success = await self._cache.set(key, serialized, ttl)
                if success:
                    self._stats['total_sets'] += 1
                    logger.debug(f"State set for user {user_id} in Redis (TTL: {ttl}s)")
                    return True
                else:
                    logger.warning(f"Failed to set state in Redis for user {user_id}, falling back to memory")
            
            # Fallback به حافظه‌ی درون‌برنامه
            self._memory_store[key] = serialized
            self._memory_expiry[key] = time.time() + ttl
            self._stats['total_sets'] += 1
            logger.debug(f"State set for user {user_id} in memory (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            # ✅ استفاده از log_database_error با traceback کامل
            log_database_error(
                f"Error setting state for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    async def get_state(self, user_id: int, default: Any = None) -> Any:
        """
        دریافت وضعیت کاربر
        
        پارامترها:
            user_id: شناسه کاربر
            default: مقدار پیش‌فرض در صورت عدم وجود وضعیت
        
        بازگشت: وضعیت کاربر یا مقدار پیش‌فرض
        """
        key = self._get_state_key(user_id)
        self._stats['total_gets'] += 1
        
        try:
            # دریافت از Redis (اگر فعال باشد)
            if self._enabled:
                value = await self._cache.get(key)
                if value is not None:
                    self._stats['cache_hits'] += 1
                    logger.debug(f"State retrieved for user {user_id} from Redis")
                    return self._deserialize_state(value)
                else:
                    self._stats['cache_misses'] += 1
            
            # Fallback به حافظه‌ی درون‌برنامه
            if key in self._memory_store:
                # بررسی انقضا
                if key in self._memory_expiry and time.time() > self._memory_expiry[key]:
                    # منقضی شده، حذف کن
                    del self._memory_store[key]
                    del self._memory_expiry[key]
                    self._stats['cache_misses'] += 1
                    logger.debug(f"State expired for user {user_id} in memory")
                    return default
                
                self._stats['fallback_hits'] += 1
                logger.debug(f"State retrieved for user {user_id} from memory (fallback)")
                return self._deserialize_state(self._memory_store[key])
            
            # وضعیت وجود ندارد
            logger.debug(f"No state found for user {user_id}")
            return default
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error getting state for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return default
    
    async def update_state(self, user_id: int, updates: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        به‌روزرسانی بخشی از وضعیت کاربر (برای دیکشنری‌ها)
        
        پارامترها:
            user_id: شناسه کاربر
            updates: دیکشنری تغییرات (کلید-مقدار)
            ttl: زمان انقضا (اختیاری)
        
        بازگشت: True در صورت موفقیت
        
        مثال:
            await state_service.update_state(user_id, {"state": "admin_orders", "page": 2})
        """
        # دریافت وضعیت فعلی
        current_state = await self.get_state(user_id, {})
        
        # اگر وضعیت فعلی دیکشنری نیست، آن را به دیکشنری تبدیل کن
        if not isinstance(current_state, dict):
            current_state = {"_state": current_state} if current_state else {}
        
        # اعمال به‌روزرسانی‌ها
        current_state.update(updates)
        
        # ذخیره‌سازی مجدد
        return await self.set_state(user_id, current_state, ttl)
    
    async def clear_state(self, user_id: int) -> bool:
        """
        پاک کردن وضعیت کاربر
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True در صورت موفقیت
        """
        key = self._get_state_key(user_id)
        self._stats['total_clears'] += 1
        
        try:
            # حذف از Redis (اگر فعال باشد)
            if self._enabled:
                deleted = await self._cache.delete(key)
                if deleted > 0:
                    logger.debug(f"State cleared for user {user_id} from Redis")
            
            # حذف از حافظه
            if key in self._memory_store:
                del self._memory_store[key]
                if key in self._memory_expiry:
                    del self._memory_expiry[key]
                logger.debug(f"State cleared for user {user_id} from memory")
            
            return True
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error clearing state for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    async def exists(self, user_id: int) -> bool:
        """
        بررسی وجود وضعیت برای کاربر
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر وضعیت وجود داشته باشد
        """
        key = self._get_state_key(user_id)
        
        try:
            # بررسی در Redis
            if self._enabled:
                exists = await self._cache.exists(key)
                if exists:
                    return True
            
            # بررسی در حافظه
            if key in self._memory_store:
                # بررسی انقضا
                if key in self._memory_expiry and time.time() > self._memory_expiry[key]:
                    del self._memory_store[key]
                    del self._memory_expiry[key]
                    return False
                return True
            
            return False
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error checking state existence for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    # ============================================================
    # متدهای کمکی برای کار با دیکشنری‌های تو در تو
    # ============================================================
    
    async def get_state_field(self, user_id: int, field: str, default: Any = None) -> Any:
        """
        دریافت یک فیلد خاص از وضعیت کاربر
        
        پارامترها:
            user_id: شناسه کاربر
            field: نام فیلد (برای دیکشنری‌های تو در تو از نقطه استفاده کنید: "order.page")
            default: مقدار پیش‌فرض
        
        بازگشت: مقدار فیلد یا default
        """
        state = await self.get_state(user_id, {})
        if not isinstance(state, dict):
            return default
        
        # پشتیبانی از فیلدهای تو در تو با نقطه
        if '.' in field:
            parts = field.split('.')
            current = state
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current
        
        return state.get(field, default)
    
    async def set_state_field(self, user_id: int, field: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        تنظیم یک فیلد خاص در وضعیت کاربر
        
        پارامترها:
            user_id: شناسه کاربر
            field: نام فیلد (برای دیکشنری‌های تو در تو از نقطه استفاده کنید: "order.page")
            value: مقدار جدید
            ttl: زمان انقضا (اختیاری)
        
        بازگشت: True در صورت موفقیت
        """
        state = await self.get_state(user_id, {})
        if not isinstance(state, dict):
            state = {"_state": state} if state else {}
        
        # پشتیبانی از فیلدهای تو در تو با نقطه
        if '.' in field:
            parts = field.split('.')
            current = state
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            state[field] = value
        
        return await self.set_state(user_id, state, ttl)
    
    # ============================================================
    # متدهای مدیریت گروهی
    # ============================================================
    
    async def clear_all_states(self) -> int:
        """
        پاک کردن تمام وضعیت‌های کاربران (فقط برای مدیریت)
        
        بازگشت: تعداد کلیدهای حذف‌شده
        """
        count = 0
        
        try:
            # حذف از Redis
            if self._enabled:
                pattern = f"{self.STATE_KEY_PREFIX}*"
                deleted = await self._cache.delete_pattern(pattern)
                count += deleted
                logger.info(f"Cleared {deleted} state keys from Redis")
            
            # حذف از حافظه
            count += len(self._memory_store)
            self._memory_store.clear()
            self._memory_expiry.clear()
            logger.info(f"Cleared {count} state keys from memory")
            
            return count
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error clearing all states: {str(e)}",
                traceback=traceback.format_exc()
            )
            return count
    
    async def get_active_users(self) -> list:
        """
        دریافت لیست کاربرانی که وضعیت فعال دارند
        
        بازگشت: لیست شناسه‌های کاربران
        """
        user_ids = []
        
        try:
            # دریافت از Redis
            if self._enabled:
                pattern = f"{self.STATE_KEY_PREFIX}*"
                # از آنجایی که delete_pattern وجود دارد، برای دریافت کلیدها می‌توانیم از متد custom استفاده کنیم
                # یا از redis مستقیم
                redis_client = await self._cache._get_redis()
                if redis_client:
                    keys = await redis_client.keys(pattern)
                    for key in keys:
                        # استخراج user_id از کلید
                        user_id_str = key.replace(self.STATE_KEY_PREFIX, '')
                        if user_id_str.isdigit():
                            user_ids.append(int(user_id_str))
            
            # از حافظه
            for key in self._memory_store.keys():
                if key.startswith(self.STATE_KEY_PREFIX):
                    user_id_str = key.replace(self.STATE_KEY_PREFIX, '')
                    if user_id_str.isdigit():
                        user_id = int(user_id_str)
                        if user_id not in user_ids:
                            user_ids.append(user_id)
            
            return user_ids
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error getting active users: {str(e)}",
                traceback=traceback.format_exc()
            )
            return user_ids
    
    # ============================================================
    # متدهای آمار
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار عملکرد سرویس وضعیت
        
        بازگشت: دیکشنری آمار
        """
        stats = self._stats.copy()
        stats['storage_type'] = 'Redis' if self._enabled else 'Memory'
        stats['ttl'] = self._ttl
        stats['memory_store_size'] = len(self._memory_store)
        stats['enabled'] = self._enabled
        stats['hit_rate'] = (
            (stats['cache_hits'] / max(1, stats['total_gets'])) * 100
            if stats['total_gets'] > 0 else 0
        )
        return stats
    
    def reset_stats(self) -> None:
        """بازنشانی آمار"""
        self._stats = {
            'total_sets': 0,
            'total_gets': 0,
            'total_clears': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'fallback_hits': 0,
        }
    
    # ============================================================
    # متدهای خصوصی (Private Methods)
    # ============================================================
    
    def _get_state_key(self, user_id: int) -> str:
        """تولید کلید یکتا برای وضعیت کاربر"""
        return f"{self.STATE_KEY_PREFIX}{user_id}"
    
    def _serialize_state(self, state: Any) -> Dict[str, Any]:
        """
        سریالایز کردن وضعیت به فرمت قابل ذخیره
        
        اگر وضعیت رشته باشد، به صورت یک دیکشنری با کلید "_state" ذخیره می‌شود
        تا بتواند با دیکشنری‌های دیگر هماهنگ باشد.
        """
        if isinstance(state, str):
            return {
                "_state": state,
                "_type": "str",
                "_timestamp": time.time()
            }
        elif isinstance(state, dict):
            # اطمینان از وجود timestamp
            if "_timestamp" not in state:
                state["_timestamp"] = time.time()
            return state
        else:
            return {
                "_state": state,
                "_type": type(state).__name__,
                "_timestamp": time.time()
            }
    
    def _deserialize_state(self, data: Dict[str, Any]) -> Any:
        """
        دیسریالایز کردن وضعیت از فرمت ذخیره‌شده به فرمت اصلی
        """
        if not data:
            return None
        
        # اگر داده یک دیکشنری با کلید "_state" باشد، مقدار اصلی را برمی‌گرداند
        if "_state" in data:
            # اگر نوع ذخیره شده مشخص شده باشد، به همان نوع تبدیل کن
            state_type = data.get("_type")
            if state_type == "str":
                return str(data["_state"])
            elif state_type == "int":
                try:
                    return int(data["_state"])
                except:
                    return data["_state"]
            elif state_type == "float":
                try:
                    return float(data["_state"])
                except:
                    return data["_state"]
            elif state_type == "bool":
                return bool(data["_state"])
            else:
                return data["_state"]
        
        # در غیر این صورت، خود دیکشنری برگردانده می‌شود
        return data
    
    def _cleanup_expired_memory(self) -> int:
        """
        پاکسازی وضعیت‌های منقضی‌شده از حافظه‌ی درون‌برنامه
        
        بازگشت: تعداد کلیدهای پاک‌شده
        """
        now = time.time()
        expired_keys = [
            key for key, expiry in self._memory_expiry.items()
            if now > expiry
        ]
        
        for key in expired_keys:
            if key in self._memory_store:
                del self._memory_store[key]
            if key in self._memory_expiry:
                del self._memory_expiry[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired states from memory")
        
        return len(expired_keys)


# ============================================================
# آبجکت سراسری (Singleton)
# ============================================================

_state_service: Optional[StateService] = None


def get_state_service() -> StateService:
    """
    دریافت آبجکت سراسری StateService (Singleton)
    
    بازگشت: نمونه‌ی StateService
    """
    global _state_service
    if _state_service is None:
        _state_service = StateService()
    return _state_service


# ============================================================
# توابع راحت‌تر برای استفاده در سایر بخش‌ها
# ============================================================

async def get_user_state(user_id: int, default: Any = None) -> Any:
    """
    دریافت وضعیت کاربر (تابع راحت)
    
    پارامترها:
        user_id: شناسه کاربر
        default: مقدار پیش‌فرض
    
    بازگشت: وضعیت کاربر
    """
    return await get_state_service().get_state(user_id, default)


async def set_user_state(user_id: int, state: Any, ttl: Optional[int] = None) -> bool:
    """
    تنظیم وضعیت کاربر (تابع راحت)
    
    پارامترها:
        user_id: شناسه کاربر
        state: وضعیت جدید
        ttl: زمان انقضا (اختیاری)
    
    بازگشت: True در صورت موفقیت
    """
    return await get_state_service().set_state(user_id, state, ttl)


async def update_user_state(user_id: int, updates: Dict[str, Any], ttl: Optional[int] = None) -> bool:
    """
    به‌روزرسانی بخشی از وضعیت کاربر (تابع راحت)
    
    پارامترها:
        user_id: شناسه کاربر
        updates: دیکشنری تغییرات
        ttl: زمان انقضا (اختیاری)
    
    بازگشت: True در صورت موفقیت
    """
    return await get_state_service().update_state(user_id, updates, ttl)


async def clear_user_state(user_id: int) -> bool:
    """
    پاک کردن وضعیت کاربر (تابع راحت)
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True در صورت موفقیت
    """
    return await get_state_service().clear_state(user_id)


async def user_state_exists(user_id: int) -> bool:
    """
    بررسی وجود وضعیت برای کاربر (تابع راحت)
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True اگر وضعیت وجود داشته باشد
    """
    return await get_state_service().exists(user_id)


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'StateService',
    'get_state_service',
    'get_user_state',
    'set_user_state',
    'update_user_state',
    'clear_user_state',
    'user_state_exists',
]