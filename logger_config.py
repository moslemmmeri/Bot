# logger_config.py
# تنظیمات لاگ‌گیری پیشرفته با پشتیبانی از چرخش خودکار فایل‌ها (RotatingFileHandler)
# و خروجی همزمان به فایل و کنسول
# نسخه اصلاح‌شده با بهبود ContextLogger و یکپارچگی با سیستم ثبت خطاها

import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Optional, Dict, Any, Callable, Awaitable

from config import config


# ============================================================
# تنظیمات پایه
# ============================================================

LOG_FILE = config.LOG_FILE
LOG_LEVEL = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
MAX_LOG_BYTES = getattr(config, 'LOG_MAX_BYTES', 10 * 1024 * 1024)  # 10 MB
BACKUP_COUNT = getattr(config, 'LOG_BACKUP_COUNT', 5)
LOG_ROTATION_WHEN = getattr(config, 'LOG_ROTATION_WHEN', 'midnight')  # 'midnight', 'D', 'H', 'M'


# ============================================================
# ایجاد پوشه لاگ در صورت عدم وجود
# ============================================================

def ensure_log_dir():
    """ایجاد پوشه‌ی لاگ در صورت عدم وجود"""
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)


# ============================================================
# تنظیمات فرمت لاگ
# ============================================================

DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
JSON_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# فرمت پیش‌فرض
DEFAULT_FORMAT = DETAILED_FORMAT
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================
# تابع تنظیم لاگر
# ============================================================

def setup_logger(name: str = "bot", log_file: Optional[str] = None,
                 level: Optional[int] = None, use_rotation: bool = True) -> logging.Logger:
    """
    تنظیم و ایجاد یک لاگر با قابلیت‌های پیشرفته

    پارامترها:
        name: نام لاگر
        log_file: مسیر فایل لاگ (در صورت عدم ارائه، از config استفاده می‌شود)
        level: سطح لاگ (در صورت عدم ارائه، از config استفاده می‌شود)
        use_rotation: آیا از چرخش خودکار فایل استفاده شود

    بازگشت: آبجکت Logger
    """
    # استفاده از مقادیر پیش‌فرض
    if log_file is None:
        log_file = LOG_FILE

    if level is None:
        level = LOG_LEVEL

    # اطمینان از وجود پوشه
    ensure_log_dir()

    # ایجاد لاگر
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # جلوگیری از اضافه شدن هندلرهای تکراری
    if logger.handlers:
        return logger

    # ========== ایجاد فرمت ==========
    formatter = logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)

    # ========== هندلر فایل (با چرخش خودکار) ==========
    if use_rotation:
        try:
            file_handler = TimedRotatingFileHandler(
                log_file,
                when=LOG_ROTATION_WHEN,
                interval=1,
                backupCount=BACKUP_COUNT,
                encoding='utf-8'
            )
        except Exception:
            # Fallback به RotatingFileHandler بر اساس حجم
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=MAX_LOG_BYTES,
                backupCount=BACKUP_COUNT,
                encoding='utf-8'
            )
    else:
        # هندلر ساده بدون چرخش
        file_handler = logging.FileHandler(log_file, encoding='utf-8')

    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # ========== هندلر کنسول ==========
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ========== لاگ شروع ==========
    logger.info("=" * 60)
    logger.info(f"📋 Logger initialized: {name}")
    logger.info(f"📁 Log file: {log_file}")
    logger.info(f"📊 Log level: {logging.getLevelName(level)}")
    logger.info(f"🔄 Rotation: {'Enabled' if use_rotation else 'Disabled'}")
    logger.info("=" * 60)

    return logger


# ============================================================
# توابع کمکی برای دریافت لاگرهای مختلف
# ============================================================

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    دریافت یک لاگر با نام مشخص

    پارامترها:
        name: نام لاگر (در صورت عدم ارائه، 'bot' استفاده می‌شود)

    بازگشت: آبجکت Logger
    """
    if name is None:
        name = "bot"
    return logging.getLogger(name)


def get_service_logger(service_name: str) -> logging.Logger:
    """دریافت لاگر برای سرویس‌ها"""
    return get_logger(f"services.{service_name}")


def get_handler_logger(handler_name: str) -> logging.Logger:
    """دریافت لاگر برای هندلرها"""
    return get_logger(f"handlers.{handler_name}")


def get_repository_logger(repo_name: str) -> logging.Logger:
    """دریافت لاگر برای ریپازیتوری‌ها"""
    return get_logger(f"repositories.{repo_name}")


def get_database_logger() -> logging.Logger:
    """دریافت لاگر برای دیتابیس"""
    return get_logger("database")


def get_api_logger() -> logging.Logger:
    """دریافت لاگر برای API"""
    return get_logger("api")


def get_admin_logger() -> logging.Logger:
    """دریافت لاگر برای پنل مدیریت"""
    return get_logger("admin_panel")


# ============================================================
# کلاس ContextLogger برای لاگ‌گیری با زمینه (Context)
# ============================================================

class ContextLogger:
    """
    لاگر با قابلیت افزودن زمینه (Context) به پیام‌ها
    برای ردیابی بهتر درخواست‌ها و عملیات‌ها

    استفاده:
        logger = ContextLogger("order_service")
        logger.set_context(user_id=123, order_id=456)
        logger.info("Order created successfully")
        # خروجی: [user_id=123] [order_id=456] Order created successfully
    """

    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        """
        پارامترها:
            name: نام لاگر
            context: دیکشنری زمینه اولیه
        """
        self._logger = get_logger(name)
        self._context = context or {}

    def set_context(self, **kwargs) -> None:
        """تنظیم یا به‌روزرسانی زمینه"""
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """پاک کردن زمینه"""
        self._context.clear()

    def get_context(self) -> Dict[str, Any]:
        """دریافت زمینه فعلی"""
        return self._context.copy()

    def with_context(self, **kwargs) -> 'ContextLogger':
        """
        ایجاد یک ContextLogger جدید با زمینه‌های اضافی
        (بدون تغییر در نمونه فعلی)
        """
        new_context = self._context.copy()
        new_context.update(kwargs)
        return ContextLogger(self._logger.name, new_context)

    def _format_message(self, message: str) -> str:
        """افزودن زمینه به پیام"""
        if not self._context:
            return message

        context_str = " ".join(f"[{k}={v}]" for k, v in self._context.items())
        return f"{context_str} {message}"

    def debug(self, message: str, *args, **kwargs) -> None:
        self._logger.debug(self._format_message(message), *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        self._logger.info(self._format_message(message), *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        self._logger.warning(self._format_message(message), *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        self._logger.error(self._format_message(message), *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        self._logger.critical(self._format_message(message), *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        self._logger.exception(self._format_message(message), *args, **kwargs)

    def log(self, level: int, message: str, *args, **kwargs) -> None:
        """ثبت پیام با سطح دلخواه"""
        self._logger.log(level, self._format_message(message), *args, **kwargs)


# ============================================================
# توابع کمکی برای دریافت ContextLogger
# ============================================================

def get_context_logger(name: str, context: Optional[Dict[str, Any]] = None) -> ContextLogger:
    """
    دریافت ContextLogger با نام و زمینه دلخواه

    پارامترها:
        name: نام لاگر
        context: دیکشنری زمینه اولیه

    بازگشت: آبجکت ContextLogger
    """
    return ContextLogger(name, context)


def get_service_context_logger(service_name: str, context: Optional[Dict[str, Any]] = None) -> ContextLogger:
    """دریافت ContextLogger برای سرویس‌ها"""
    return ContextLogger(f"services.{service_name}", context)


def get_handler_context_logger(handler_name: str, context: Optional[Dict[str, Any]] = None) -> ContextLogger:
    """دریافت ContextLogger برای هندلرها"""
    return ContextLogger(f"handlers.{handler_name}", context)


# ============================================================
# ایجاد لاگر پیش‌فرض
# ============================================================

# این لاگر به‌صورت خودکار در زمان import ایجاد می‌شود
logger = setup_logger()


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # توابع اصلی
    'setup_logger',
    'get_logger',
    'get_service_logger',
    'get_handler_logger',
    'get_repository_logger',
    'get_database_logger',
    'get_api_logger',
    'get_admin_logger',
    
    # ContextLogger
    'ContextLogger',
    'get_context_logger',
    'get_service_context_logger',
    'get_handler_context_logger',
    
    # لاگر پیش‌فرض
    'logger',
    
    # تنظیمات
    'LOG_FILE',
    'LOG_LEVEL',
    'MAX_LOG_BYTES',
    'BACKUP_COUNT',
    'LOG_ROTATION_WHEN',
]