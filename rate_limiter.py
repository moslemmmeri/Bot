# rate_limiter.py
# محدودیت نرخ درخواست (Rate Limiting) برای جلوگیری از اسپم و سوءاستفاده
# پشتیبانی از Redis برای ذخیره‌سازی توزیع‌شده و Fallback به حافظه درون‌برنامه

import time
import asyncio
import traceback  # ✅ اضافه شد برای traceback کامل
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from config import config
from logger_config import logger
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class RateLimiter:
    """
    مدیریت محدودیت نرخ درخواست برای هر کاربر.
    از Redis برای ذخیره‌سازی توزیع‌شده استفاده می‌کند و در صورت عدم دسترسی،
    به دیکشنری درون‌حافظه با پاکسازی دوره‌ای Fallback می‌کند.
    """
    
    def __init__(self):
        # تنظیمات از config
        self._max_requests = config.RATE_LIMIT_PER_MINUTE
        self._window_seconds = 60  # یک دقیقه
        self._enabled = config.RATE_LIMIT_ENABLED
        
        # تلاش برای استفاده از Redis
        self._redis_enabled = False
        self._redis_client = None
        self._init_redis()
        
        # Fallback به حافظه درون‌برنامه
        self._memory_requests = defaultdict(list)  # {user_id: [timestamp1, timestamp2, ...]}
        self._memory_lock = asyncio.Lock()
        
        # زمان آخرین پاکسازی حافظه
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # هر ۵ دقیقه
        
        # آمار
        self._stats = {
            'total_checks': 0,
            'allowed': 0,
            'blocked': 0,
            'redis_hits': 0,
            'memory_fallback': 0,
        }
        
        logger.info(f"✅ RateLimiter initialized (max: {self._max_requests}/min, enabled: {self._enabled}, redis: {self._redis_enabled})")
    
    def _init_redis(self):
        """مقداردهی اولیه Redis در صورت فعال بودن"""
        if not config.REDIS_ENABLED:
            logger.info("ℹ️ Redis is disabled, RateLimiter will use in-memory storage")
            return
        
        try:
            import redis.asyncio as redis
            self._redis_client = redis.from_url(
                config.get_redis_url(),
                decode_responses=True,
                max_connections=10
            )
            self._redis_enabled = True
            logger.info("✅ Redis connection established for RateLimiter")
        except ImportError:
            logger.warning("⚠️ redis-py not installed. RateLimiter will use in-memory storage")
        except Exception as e:
            log_general_error(
                f"Failed to connect to Redis for RateLimiter: {str(e)}",
                traceback=traceback.format_exc()
            )
            logger.warning("⚠️ Failed to connect to Redis for RateLimiter. Using in-memory storage.")
    
    async def _get_redis(self):
        """دریافت کلاینت Redis با بررسی اتصال"""
        if not self._redis_enabled or not self._redis_client:
            return None
        
        try:
            await self._redis_client.ping()
            return self._redis_client
        except Exception as e:
            log_general_error(
                f"Redis connection lost, falling back to memory: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._redis_enabled = False
            return None
    
    def _get_memory_key(self, user_id: int) -> str:
        """تولید کلید برای حافظه درون‌برنامه"""
        return f"rate_limit:{user_id}"
    
    async def _cleanup_memory_if_needed(self):
        """پاکسازی دوره‌ای حافظه برای جلوگیری از مصرف بیش‌ازحد"""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            async with self._memory_lock:
                # حذف کاربرانی که در ۱۰ دقیقه‌ی اخیر فعالیت نداشته‌اند
                cutoff = now - 600  # ۱۰ دقیقه
                to_remove = []
                for user_id, timestamps in self._memory_requests.items():
                    if not timestamps or max(timestamps) < cutoff:
                        to_remove.append(user_id)
                
                for user_id in to_remove:
                    del self._memory_requests[user_id]
            
            self._last_cleanup = now
            if to_remove:
                logger.debug(f"Cleaned up {len(to_remove)} inactive users from rate limiter memory")
    
    async def is_allowed(self, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر مجاز به ارسال درخواست جدید است یا خیر.
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت:
            True اگر مجاز باشد، False در غیر این صورت
        """
        self._stats['total_checks'] += 1
        
        if not self._enabled:
            self._stats['allowed'] += 1
            return True
        
        # کاربران ویژه (OWNER_ID) محدودیت ندارند
        if user_id == config.OWNER_ID:
            self._stats['allowed'] += 1
            return True
        
        now = time.time()
        window_start = now - self._window_seconds
        
        # ========== تلاش برای استفاده از Redis ==========
        if self._redis_enabled:
            redis_client = await self._get_redis()
            if redis_client:
                try:
                    key = f"rate_limit:{user_id}"
                    
                    # حذف درخواست‌های قدیمی‌تر از پنجره‌ی زمانی
                    await redis_client.zremrangebyscore(key, 0, window_start)
                    
                    # تعداد درخواست‌های باقی‌مانده
                    count = await redis_client.zcard(key)
                    
                    if count >= self._max_requests:
                        self._stats['blocked'] += 1
                        logger.debug(f"Rate limit exceeded for user {user_id}: {count} requests (Redis)")
                        return False
                    
                    # افزودن درخواست جدید
                    await redis_client.zadd(key, {str(now): now})
                    await redis_client.expire(key, self._window_seconds + 10)
                    
                    self._stats['allowed'] += 1
                    self._stats['redis_hits'] += 1
                    return True
                    
                except Exception as e:
                    log_general_error(
                        f"Redis error in rate limiter, falling back to memory: {str(e)}",
                        traceback=traceback.format_exc()
                    )
                    self._redis_enabled = False
        
        # ========== Fallback به حافظه درون‌برنامه ==========
        async with self._memory_lock:
            # پاکسازی دوره‌ای
            await self._cleanup_memory_if_needed()
            
            # حذف درخواست‌های قدیمی‌تر از پنجره‌ی زمانی
            timestamps = self._memory_requests.get(user_id, [])
            timestamps = [t for t in timestamps if t > window_start]
            self._memory_requests[user_id] = timestamps
            
            if len(timestamps) >= self._max_requests:
                self._stats['blocked'] += 1
                logger.debug(f"Rate limit exceeded for user {user_id}: {len(timestamps)} requests (Memory)")
                return False
            
            # افزودن درخواست جدید
            timestamps.append(now)
            self._memory_requests[user_id] = timestamps
            self._stats['allowed'] += 1
            self._stats['memory_fallback'] += 1
            return True
    
    async def get_remaining(self, user_id: int) -> int:
        """
        دریافت تعداد درخواست‌های باقی‌مانده برای کاربر در پنجره‌ی زمانی فعلی.
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت:
            تعداد درخواست‌های باقی‌مانده
        """
        if not self._enabled or user_id == config.OWNER_ID:
            return self._max_requests
        
        now = time.time()
        window_start = now - self._window_seconds
        
        # ========== Redis ==========
        if self._redis_enabled:
            redis_client = await self._get_redis()
            if redis_client:
                try:
                    key = f"rate_limit:{user_id}"
                    await redis_client.zremrangebyscore(key, 0, window_start)
                    count = await redis_client.zcard(key)
                    remaining = self._max_requests - count
                    return max(0, remaining)
                except Exception as e:
                    log_general_error(
                        f"Redis error in get_remaining, falling back to memory: {str(e)}",
                        traceback=traceback.format_exc()
                    )
                    # Fallback به حافظه
        
        # ========== حافظه ==========
        async with self._memory_lock:
            timestamps = self._memory_requests.get(user_id, [])
            timestamps = [t for t in timestamps if t > window_start]
            count = len(timestamps)
            remaining = self._max_requests - count
            return max(0, remaining)
    
    async def get_reset_time(self, user_id: int) -> int:
        """
        دریافت زمان باقی‌مانده تا ریست شدن محدودیت (به ثانیه).
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت:
            تعداد ثانیه‌های باقی‌مانده تا ریست شدن
        """
        if not self._enabled or user_id == config.OWNER_ID:
            return 0
        
        now = time.time()
        
        # ========== Redis ==========
        if self._redis_enabled:
            redis_client = await self._get_redis()
            if redis_client:
                try:
                    key = f"rate_limit:{user_id}"
                    # دریافت قدیمی‌ترین timestamp
                    oldest = await redis_client.zrange(key, 0, 0, withscores=True)
                    if oldest:
                        oldest_time = oldest[0][1]
                        reset_time = oldest_time + self._window_seconds - now
                        return max(0, int(reset_time))
                    return 0
                except Exception as e:
                    log_general_error(
                        f"Redis error in get_reset_time, falling back to memory: {str(e)}",
                        traceback=traceback.format_exc()
                    )
                    # Fallback به حافظه
        
        # ========== حافظه ==========
        async with self._memory_lock:
            timestamps = self._memory_requests.get(user_id, [])
            if not timestamps:
                return 0
            
            oldest = min(timestamps)
            reset_time = oldest + self._window_seconds - now
            return max(0, int(reset_time))
    
    async def reset(self, user_id: int) -> bool:
        """
        بازنشانی محدودیت برای یک کاربر خاص.
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True در صورت موفقیت
        """
        try:
            # ========== Redis ==========
            if self._redis_enabled:
                redis_client = await self._get_redis()
                if redis_client:
                    key = f"rate_limit:{user_id}"
                    await redis_client.delete(key)
            
            # ========== حافظه ==========
            async with self._memory_lock:
                if user_id in self._memory_requests:
                    self._memory_requests[user_id] = []
            
            logger.debug(f"Rate limit reset for user {user_id}")
            return True
            
        except Exception as e:
            log_general_error(
                f"Error resetting rate limit for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار عملکرد RateLimiter
        
        بازگشت: دیکشنری شامل آمار
        """
        stats = self._stats.copy()
        stats['enabled'] = self._enabled
        stats['max_requests'] = self._max_requests
        stats['window_seconds'] = self._window_seconds
        stats['redis_enabled'] = self._redis_enabled
        stats['memory_size'] = len(self._memory_requests)
        stats['block_rate'] = (
            (stats['blocked'] / max(1, stats['total_checks'])) * 100
            if stats['total_checks'] > 0 else 0
        )
        return stats


# ==================== آبجکت سراسری ====================

_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """دریافت آبجکت سراسری RateLimiter (Singleton)"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# ==================== توابع کمکی ====================

async def check_rate_limit(user_id: int) -> tuple:
    """
    بررسی محدودیت نرخ درخواست برای یک کاربر.
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت:
        (is_allowed, remaining, reset_time)
        is_allowed: True اگر مجاز باشد
        remaining: تعداد درخواست‌های باقی‌مانده
        reset_time: زمان باقی‌مانده تا ریست شدن (ثانیه)
    """
    limiter = get_rate_limiter()
    is_allowed = await limiter.is_allowed(user_id)
    remaining = await limiter.get_remaining(user_id)
    reset_time = await limiter.get_reset_time(user_id)
    return is_allowed, remaining, reset_time


async def get_rate_limit_status(user_id: int) -> dict:
    """
    دریافت وضعیت کامل محدودیت نرخ درخواست برای یک کاربر.
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت:
        دیکشنری شامل:
            - enabled: آیا محدودیت فعال است
            - max_requests: حداکثر تعداد درخواست در دقیقه
            - remaining: تعداد درخواست‌های باقی‌مانده
            - reset_time: زمان باقی‌مانده تا ریست شدن (ثانیه)
            - is_allowed: آیا مجاز است
    """
    limiter = get_rate_limiter()
    is_allowed = await limiter.is_allowed(user_id)
    remaining = await limiter.get_remaining(user_id)
    reset_time = await limiter.get_reset_time(user_id)
    
    return {
        "enabled": limiter._enabled,
        "max_requests": limiter._max_requests,
        "remaining": remaining,
        "reset_time": reset_time,
        "is_allowed": is_allowed,
        "redis_enabled": limiter._redis_enabled
    }


async def reset_rate_limit(user_id: int) -> bool:
    """
    بازنشانی محدودیت برای یک کاربر.
    
    پارامترها:
        user_id: شناسه کاربر
    
    بازگشت: True در صورت موفقیت
    """
    limiter = get_rate_limiter()
    return await limiter.reset(user_id)


async def get_rate_limiter_stats() -> Dict[str, Any]:
    """
    دریافت آمار کلی RateLimiter
    
    بازگشت: دیکشنری شامل آمار
    """
    limiter = get_rate_limiter()
    return await limiter.get_stats()


__all__ = [
    'RateLimiter',
    'get_rate_limiter',
    'check_rate_limit',
    'get_rate_limit_status',
    'reset_rate_limit',
    'get_rate_limiter_stats',
]