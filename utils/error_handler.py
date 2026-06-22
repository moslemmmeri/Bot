# utils/error_handler.py
# مدیریت متمرکز خطاها - ثبت خطاها در دیتابیس و لاگ فایل
# نسخه اصلاح‌شده با پشتیبانی از traceback کامل، JSON data و ContextLogger
# همچنین سازگاری با پارامتر `traceback` برای کدهای قدیمی

import json
import sys
import traceback
from typing import Optional, Dict, Any, Union
from datetime import datetime
from logger_config import logger, ContextLogger


# ============================================================
# تابع اصلی ثبت خطا
# ============================================================

def log_error(
    error_type: str,
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None,
    traceback: Optional[str] = None,  # alias for traceback_str
) -> None:
    """
    ثبت یک خطا در دیتابیس و لاگ فایل.

    پارامترها:
        error_type: نوع خطا (database, api, callback, general, payment, security, critical)
        error_message: پیام خطا (متن کوتاه)
        traceback_str: جزئیات کامل خطا (اختیاری - در صورت عدم ارائه، از traceback.current گرفته می‌شود)
        user_id: شناسه کاربری که خطا برای او رخ داده (اختیاری)
        chat_id: شناسه چت (اختیاری)
        data: اطلاعات اضافی به صورت دیکشنری (اختیاری)
        context_logger: آبجکت ContextLogger برای افزودن context (اختیاری)
        traceback: alias برای traceback_str (سازگاری با کدهای قدیمی)
    """
    # اگر traceback ارائه شده و traceback_str None است، از آن استفاده کن
    if traceback_str is None and traceback is not None:
        traceback_str = traceback

    try:
        # اگر traceback_str ارائه نشده، از traceback فعلی استفاده کن
        if traceback_str is None:
            traceback_str = traceback.format_exc()
            # اگر traceback خالی بود، از sys.exc_info استفاده کن
            if not traceback_str or traceback_str == "NoneType: None\n":
                exc_type, exc_value, exc_tb = sys.exc_info()
                if exc_tb:
                    traceback_str = ''.join(traceback.format_tb(exc_tb))
                    if exc_value:
                        traceback_str += f"\n{exc_type.__name__}: {exc_value}"
                else:
                    traceback_str = "No traceback available"

        # محدود کردن طول traceback برای جلوگیری از پر شدن دیتابیس
        if traceback_str and len(traceback_str) > 10000:
            traceback_str = traceback_str[:10000] + "\n... (truncated)"

        # تبدیل data به JSON
        data_json = None
        if data:
            try:
                # حذف اطلاعات حساس از data قبل از ذخیره
                safe_data = {k: v for k, v in data.items() if k not in ['password', 'token', 'secret']}
                data_json = json.dumps(safe_data, ensure_ascii=False)
            except Exception as e:
                logger.warning(f"خطا در تبدیل data به JSON: {e}")
                data_json = str(data)[:500]

        # ثبت در دیتابیس
        try:
            from database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO error_logs (
                        error_type, error_message, traceback, user_id, chat_id, data
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (error_type, error_message, traceback_str, user_id, chat_id, data_json))
                conn.commit()
        except Exception as db_error:
            # اگر ثبت در دیتابیس خطا داد، فقط در لاگ فایل ثبت کن
            logger.error(f"❌ خطا در ثبت خطا در دیتابیس: {db_error}")

        # ========== ثبت در لاگ فایل با ContextLogger ==========
        log_message = f"[{error_type}] {error_message}"

        # اگر ContextLogger ارائه شده، از آن استفاده کن
        if context_logger:
            context_logger.error(log_message)
        else:
            # در غیر این صورت، از logger معمولی استفاده کن
            logger.error(log_message)

            # اگر traceback وجود دارد، در لاگ جداگانه ثبت کن
            if traceback_str:
                logger.debug(f"Traceback: {traceback_str}")

            # اگر data وجود دارد، در لاگ جداگانه ثبت کن
            if data:
                logger.debug(f"Data: {data}")

        # اگر خطا بحرانی است، در لاگ بحرانی نیز ثبت کن
        if error_type == 'critical':
            logger.critical(f"🚨 CRITICAL: {error_message}")

    except Exception as e:
        # اگر خود ثبت خطا هم خطا داد، فقط لاگ کن و ادامه بده
        logger.error(f"❌ خطای بحرانی در سیستم ثبت خطا: {e}")
        logger.debug(traceback.format_exc())


# ============================================================
# توابع کمکی برای انواع خطا
# ============================================================

def log_database_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None,
    traceback: Optional[str] = None,
) -> None:
    """ثبت خطای مربوط به دیتابیس"""
    log_error('database', error_message, traceback_str, user_id, chat_id, data, context_logger, traceback)


def log_api_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None,
    traceback: Optional[str] = None,
) -> None:
    """ثبت خطای مربوط به API (ارسال پیام، دریافت آپدیت و ...)"""
    log_error('api', error_message, traceback_str, user_id, chat_id, data, context_logger, traceback)


def log_callback_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None,
    traceback: Optional[str] = None,
) -> None:
    """ثبت خطای مربوط به پردازش کالبک"""
    log_error('callback', error_message, traceback_str, user_id, chat_id, data, context_logger, traceback)


def log_general_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None,
    traceback: Optional[str] = None,
) -> None:
    """ثبت خطای عمومی"""
    log_error('general', error_message, traceback_str, user_id, chat_id, data, context_logger, traceback)


def log_payment_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None,
    traceback: Optional[str] = None,
) -> None:
    """ثبت خطای مربوط به پرداخت"""
    log_error('payment', error_message, traceback_str, user_id, chat_id, data, context_logger, traceback)


def log_security_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None,
    traceback: Optional[str] = None,
) -> None:
    """ثبت خطای امنیتی (تلاش برای دسترسی غیرمجاز و ...)"""
    log_error('security', error_message, traceback_str, user_id, chat_id, data, context_logger, traceback)


def log_critical_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None,
    traceback: Optional[str] = None,
) -> None:
    """ثبت خطای بحرانی (مثل قطعی سرویس)"""
    log_error('critical', error_message, traceback_str, user_id, chat_id, data, context_logger, traceback)


# ============================================================
# توابع راحت‌تر برای استفاده بدون نیاز به import جداگانه
# ============================================================

def get_traceback() -> str:
    """دریافت traceback کامل از استثنای جاری"""
    tb = traceback.format_exc()
    if not tb or tb == "NoneType: None\n":
        exc_type, exc_value, exc_tb = sys.exc_info()
        if exc_tb:
            tb = ''.join(traceback.format_tb(exc_tb))
            if exc_value:
                tb += f"\n{exc_type.__name__}: {exc_value}"
        else:
            tb = "No traceback available"
    return tb


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # تابع اصلی
    'log_error',
    # توابع کمکی
    'log_database_error',
    'log_api_error',
    'log_callback_error',
    'log_general_error',
    'log_payment_error',
    'log_security_error',
    'log_critical_error',
    # توابع راحت
    'get_traceback',
]