# database/db_logs.py
# مدیریت لاگ‌های خطا و رویدادهای سیستمی - ثبت، دریافت و آمار خطاها
# نسخه اصلاح‌شده با یکپارچگی کامل با utils/error_handler و ContextLogger

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from logger_config import logger, ContextLogger
from .db_connection import get_db_connection

# ایمپورت از utils/error_handler برای ثبت یکپارچه خطاها
from utils.error_handler import (
    log_error as base_log_error,
    get_traceback,
)


# ==================== ثبت خطا (Wrapper برای utils/error_handler) ====================

def log_error(
    error_type: str,
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None
) -> None:
    """
    ثبت یک خطا با استفاده از utils/error_handler
    این تابع به‌عنوان wrapper عمل می‌کند تا وابستگی به utils در سطح database حفظ شود.
    """
    # اگر traceback_str ارائه نشده، از get_traceback استفاده کن
    if traceback_str is None:
        traceback_str = get_traceback()

    # فراخوانی تابع اصلی ثبت خطا از utils
    base_log_error(
        error_type=error_type,
        error_message=error_message,
        traceback_str=traceback_str,
        user_id=user_id,
        chat_id=chat_id,
        data=data,
        context_logger=context_logger
    )


def log_database_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None
) -> None:
    """ثبت خطای مربوط به دیتابیس"""
    log_error('database', error_message, traceback_str, user_id, chat_id, data, context_logger)


def log_api_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None
) -> None:
    """ثبت خطای مربوط به API"""
    log_error('api', error_message, traceback_str, user_id, chat_id, data, context_logger)


def log_callback_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None
) -> None:
    """ثبت خطای مربوط به پردازش کالبک"""
    log_error('callback', error_message, traceback_str, user_id, chat_id, data, context_logger)


def log_general_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None
) -> None:
    """ثبت خطای عمومی"""
    log_error('general', error_message, traceback_str, user_id, chat_id, data, context_logger)


def log_payment_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None
) -> None:
    """ثبت خطای مربوط به پرداخت"""
    log_error('payment', error_message, traceback_str, user_id, chat_id, data, context_logger)


def log_security_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None
) -> None:
    """ثبت خطای امنیتی"""
    log_error('security', error_message, traceback_str, user_id, chat_id, data, context_logger)


def log_critical_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict[str, Any]] = None,
    context_logger: Optional[ContextLogger] = None
) -> None:
    """ثبت خطای بحرانی"""
    log_error('critical', error_message, traceback_str, user_id, chat_id, data, context_logger)


# ==================== دریافت خطاها ====================

def get_error_logs(
    limit: int = 20,
    offset: int = 0,
    error_type: Optional[str] = None,
    is_resolved: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    order_by: str = "created_at DESC"
) -> List[Dict[str, Any]]:
    """
    دریافت لیست خطاها با صفحه‌بندی و فیلترهای اختیاری.

    پارامترها:
        limit: تعداد خطاها در هر صفحه
        offset: موقعیت شروع
        error_type: نوع خطا (اختیاری)
        is_resolved: وضعیت حل‌شدن (0/1) (اختیاری)
        start_date: تاریخ شروع (اختیاری)
        end_date: تاریخ پایان (اختیاری)
        order_by: ترتیب مرتب‌سازی (پیش‌فرض: created_at DESC)

    بازگشت: لیست خطاها
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if error_type:
                conditions.append("error_type = ?")
                params.append(error_type)

            if is_resolved is not None:
                conditions.append("is_resolved = ?")
                params.append(is_resolved)

            if start_date:
                conditions.append("DATE(created_at) >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("DATE(created_at) <= ?")
                params.append(end_date)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"""
                SELECT * FROM error_logs
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, (*params, limit, offset))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                item = dict(row)
                if item.get('data'):
                    try:
                        item['data'] = json.loads(item['data'])
                    except:
                        pass
                result.append(item)
            return result
    except Exception as e:
        # ثبت خطا با استفاده از خودمان (برای جلوگیری از حلقه بی‌نهایت)
        logger.error(f"Error in get_error_logs: {e}", exc_info=True)
        return []


def get_error_log_by_id(error_id: int) -> Optional[Dict[str, Any]]:
    """دریافت جزئیات یک خطا بر اساس شناسه"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM error_logs WHERE id = ?", (error_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('data'):
                    try:
                        result['data'] = json.loads(result['data'])
                    except:
                        pass
                return result
            return None
    except Exception as e:
        logger.error(f"Error in get_error_log_by_id for {error_id}: {e}", exc_info=True)
        return None


def get_total_errors(
    error_type: Optional[str] = None,
    is_resolved: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> int:
    """
    تعداد کل خطاها (با فیلتر اختیاری)

    پارامترها:
        error_type: نوع خطا (اختیاری)
        is_resolved: وضعیت حل‌شدن (0/1) (اختیاری)
        start_date: تاریخ شروع (اختیاری)
        end_date: تاریخ پایان (اختیاری)

    بازگشت: تعداد خطاها
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if error_type:
                conditions.append("error_type = ?")
                params.append(error_type)

            if is_resolved is not None:
                conditions.append("is_resolved = ?")
                params.append(is_resolved)

            if start_date:
                conditions.append("DATE(created_at) >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("DATE(created_at) <= ?")
                params.append(end_date)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            cursor.execute(f"SELECT COUNT(*) as count FROM error_logs WHERE {where_clause}", params)
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        logger.error(f"Error in get_total_errors: {e}", exc_info=True)
        return 0


def get_error_types_with_count() -> List[Dict[str, Any]]:
    """
    دریافت لیست انواع خطاها به همراه تعداد هر کدام.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT error_type, COUNT(*) as count
                FROM error_logs
                GROUP BY error_type
                ORDER BY count DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error in get_error_types_with_count: {e}", exc_info=True)
        return []


def get_error_logs_advanced(
    limit: int = 20,
    offset: int = 0,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    جستجوی پیشرفته خطاها با فیلترهای بیشتر.

    پارامترها:
        limit: تعداد خطاها در هر صفحه
        offset: موقعیت شروع
        filters: دیکشنری فیلترها شامل:
            - error_type: نوع خطا
            - is_resolved: وضعیت حل‌شدن
            - start_date: تاریخ شروع
            - end_date: تاریخ پایان
            - user_id: شناسه کاربر
            - chat_id: شناسه چت
            - search: جستجو در پیام خطا

    بازگشت: لیست خطاها
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if filters:
                if filters.get('error_type'):
                    conditions.append("error_type = ?")
                    params.append(filters['error_type'])

                if filters.get('is_resolved') is not None:
                    conditions.append("is_resolved = ?")
                    params.append(filters['is_resolved'])

                if filters.get('start_date'):
                    conditions.append("DATE(created_at) >= ?")
                    params.append(filters['start_date'])

                if filters.get('end_date'):
                    conditions.append("DATE(created_at) <= ?")
                    params.append(filters['end_date'])

                if filters.get('user_id'):
                    conditions.append("user_id = ?")
                    params.append(filters['user_id'])

                if filters.get('chat_id'):
                    conditions.append("chat_id = ?")
                    params.append(filters['chat_id'])

                if filters.get('search'):
                    conditions.append("error_message LIKE ?")
                    params.append(f"%{filters['search']}%")

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"""
                SELECT * FROM error_logs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, (*params, limit, offset))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                item = dict(row)
                if item.get('data'):
                    try:
                        item['data'] = json.loads(item['data'])
                    except:
                        pass
                result.append(item)
            return result
    except Exception as e:
        logger.error(f"Error in get_error_logs_advanced: {e}", exc_info=True)
        return []


# ==================== مدیریت خطاها ====================

def mark_error_as_resolved(error_id: int, resolved_by: int) -> bool:
    """علامت‌گذاری یک خطا به عنوان حل‌شده."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE error_logs
                SET is_resolved = 1, resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
                WHERE id = ?
            """, (resolved_by, error_id))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"خطا {error_id} توسط {resolved_by} به‌عنوان حل‌شده علامت‌گذاری شد.")
                return True
            return False
    except Exception as e:
        logger.error(f"Error in mark_error_as_resolved for {error_id}: {e}", exc_info=True)
        return False


def mark_error_as_unresolved(error_id: int) -> bool:
    """بازگشایی خطا (حل‌نشده)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE error_logs
                SET is_resolved = 0, resolved_at = NULL, resolved_by = NULL
                WHERE id = ?
            """, (error_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"خطا {error_id} به حالت حل‌نشده بازگشت.")
                return True
            return False
    except Exception as e:
        logger.error(f"Error in mark_error_as_unresolved for {error_id}: {e}", exc_info=True)
        return False


def delete_error_logs(days: int = 30) -> int:
    """حذف خطاهای قدیمی‌تر از تعداد روز مشخص."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM error_logs
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            deleted_count = cursor.rowcount
            conn.commit()
            if deleted_count > 0:
                logger.info(f"{deleted_count} خطای قدیمی‌تر از {days} روز حذف شدند.")
            return deleted_count
    except Exception as e:
        logger.error(f"Error in delete_error_logs: {e}", exc_info=True)
        return 0


def delete_error_log_by_id(error_id: int) -> bool:
    """حذف یک خطا بر اساس شناسه"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM error_logs WHERE id = ?", (error_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"خطا {error_id} حذف شد.")
                return True
            return False
    except Exception as e:
        logger.error(f"Error in delete_error_log_by_id for {error_id}: {e}", exc_info=True)
        return False


def clear_all_error_logs() -> int:
    """پاک کردن تمام خطاها (فقط برای مدیر سیستم)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM error_logs")
            deleted_count = cursor.rowcount
            conn.commit()
            logger.warning(f"تمام خطاها ({deleted_count} رکورد) حذف شدند.")
            return deleted_count
    except Exception as e:
        logger.error(f"Error in clear_all_error_logs: {e}", exc_info=True)
        return 0


# ==================== آمار خطاها ====================

def get_error_stats() -> Dict[str, Any]:
    """
    دریافت آمار کلی خطاها برای داشبورد:
    - تعداد کل خطاها
    - تعداد خطاهای حل‌نشده
    - تعداد خطاهای حل‌شده
    - آخرین خطای ثبت‌شده
    - تفکیک بر اساس نوع خطا
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # تعداد کل
            cursor.execute("SELECT COUNT(*) as total FROM error_logs")
            total = cursor.fetchone()['total']

            # حل‌نشده
            cursor.execute("SELECT COUNT(*) as unresolved FROM error_logs WHERE is_resolved = 0")
            unresolved = cursor.fetchone()['unresolved']

            # حل‌شده
            cursor.execute("SELECT COUNT(*) as resolved FROM error_logs WHERE is_resolved = 1")
            resolved = cursor.fetchone()['resolved']

            # آخرین خطا
            cursor.execute("""
                SELECT id, error_type, error_message, created_at
                FROM error_logs
                ORDER BY created_at DESC
                LIMIT 1
            """)
            last_error = cursor.fetchone()

            # تفکیک بر اساس نوع
            cursor.execute("""
                SELECT error_type, COUNT(*) as count
                FROM error_logs
                GROUP BY error_type
                ORDER BY count DESC
            """)
            by_type = cursor.fetchall()

            return {
                'total': total,
                'unresolved': unresolved,
                'resolved': resolved,
                'last_error': dict(last_error) if last_error else None,
                'by_type': [dict(row) for row in by_type]
            }
    except Exception as e:
        logger.error(f"Error in get_error_stats: {e}", exc_info=True)
        return {
            'total': 0,
            'unresolved': 0,
            'resolved': 0,
            'last_error': None,
            'by_type': []
        }


# ==================== ابزارهای کمکی ====================

def get_errors_by_user(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """دریافت خطاهای مربوط به یک کاربر خاص."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM error_logs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                item = dict(row)
                if item.get('data'):
                    try:
                        item['data'] = json.loads(item['data'])
                    except:
                        pass
                result.append(item)
            return result
    except Exception as e:
        logger.error(f"Error in get_errors_by_user for {user_id}: {e}", exc_info=True)
        return []


def get_errors_by_chat(chat_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """دریافت خطاهای مربوط به یک چت خاص."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM error_logs
                WHERE chat_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (chat_id, limit))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                item = dict(row)
                if item.get('data'):
                    try:
                        item['data'] = json.loads(item['data'])
                    except:
                        pass
                result.append(item)
            return result
    except Exception as e:
        logger.error(f"Error in get_errors_by_chat for {chat_id}: {e}", exc_info=True)
        return []


def get_error_count_by_type(error_type: str) -> int:
    """دریافت تعداد خطاهای یک نوع خاص"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM error_logs WHERE error_type = ?", (error_type,))
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        logger.error(f"Error in get_error_count_by_type for {error_type}: {e}", exc_info=True)
        return 0


def get_recent_errors(limit: int = 10) -> List[Dict[str, Any]]:
    """دریافت خطاهای اخیر"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM error_logs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                item = dict(row)
                if item.get('data'):
                    try:
                        item['data'] = json.loads(item['data'])
                    except:
                        pass
                result.append(item)
            return result
    except Exception as e:
        logger.error(f"Error in get_recent_errors: {e}", exc_info=True)
        return []


def get_error_report(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """دریافت گزارش خطاها در بازه زمانی"""
    try:
        conditions = []
        params = []

        if start_date:
            conditions.append("DATE(created_at) >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(created_at) <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"SELECT COUNT(*) as total FROM error_logs WHERE {where_clause}", params)
            total = cursor.fetchone()['total']

            cursor.execute(f"""
                SELECT error_type, COUNT(*) as count
                FROM error_logs
                WHERE {where_clause}
                GROUP BY error_type
                ORDER BY count DESC
            """, params)
            by_type = cursor.fetchall()

            cursor.execute(f"""
                SELECT is_resolved, COUNT(*) as count
                FROM error_logs
                WHERE {where_clause}
                GROUP BY is_resolved
            """, params)
            by_status = cursor.fetchall()

            return {
                'total': total,
                'by_type': [dict(row) for row in by_type],
                'by_status': [dict(row) for row in by_status],
                'start_date': start_date,
                'end_date': end_date
            }
    except Exception as e:
        logger.error(f"Error in get_error_report: {e}", exc_info=True)
        return {
            'total': 0,
            'by_type': [],
            'by_status': [],
            'start_date': start_date,
            'end_date': end_date
        }


def clean_error_logs_with_retention(retention_days: int = 60) -> int:
    """
    پاکسازی خطاها بر اساس تعداد روز نگهداری (با لاگ کامل)

    پارامترها:
        retention_days: تعداد روزهای نگهداری

    بازگشت: تعداد خطاهای حذف‌شده
    """
    logger.info(f"🔄 شروع پاکسازی خطاهای قدیمی‌تر از {retention_days} روز...")

    before_count = get_total_errors()
    logger.info(f"📊 تعداد خطاهای موجود قبل از پاکسازی: {before_count}")

    deleted = delete_error_logs(retention_days)

    after_count = get_total_errors()
    logger.info(f"📊 تعداد خطاهای موجود بعد از پاکسازی: {after_count}")
    logger.info(f"✅ پاکسازی خطاها انجام شد. {deleted} خطا حذف شدند.")

    return deleted


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'log_error',
    'log_database_error',
    'log_api_error',
    'log_callback_error',
    'log_general_error',
    'log_payment_error',
    'log_security_error',
    'log_critical_error',
    'get_error_logs',
    'get_error_log_by_id',
    'get_total_errors',
    'get_error_types_with_count',
    'get_error_logs_advanced',
    'mark_error_as_resolved',
    'mark_error_as_unresolved',
    'delete_error_logs',
    'delete_error_log_by_id',
    'clear_all_error_logs',
    'get_error_stats',
    'get_errors_by_user',
    'get_errors_by_chat',
    'get_error_count_by_type',
    'get_recent_errors',
    'get_error_report',
    'clean_error_logs_with_retention',
]