# admin_panel/error_management.py
# مدیریت متمرکز خطاها و اعلان‌ها (Alert System) در پنل مدیریت
# نسخه اصلاح‌شده با ContextLogger و ثبت کامل traceback

import json
from typing import Optional, Dict, Any, List

from logger_config import ContextLogger
from core import send_message
from database import get_db_connection
from services.permission_service import get_permission_service
from utils import format_datetime, get_error_type_icon
from utils.error_handler import (
    log_error as base_log_error,
    log_callback_error,
    log_general_error,
    log_database_error
)
from database.db_logs import (
    get_errors_by_user as db_get_errors_by_user,
    get_errors_by_chat as db_get_errors_by_chat,
    get_error_count_by_type as db_get_error_count_by_type,
    get_recent_errors as db_get_recent_errors,
    get_error_report as db_get_error_report,
    clean_error_logs_with_retention as db_clean_error_logs_with_retention,
)


# ============================================================
# توابع ثبت خطا (Wrapper)
# ============================================================

def log_error(error_type, error_message, traceback=None, user_id=None, chat_id=None, data=None):
    base_log_error(error_type, error_message, traceback, user_id, chat_id, data)


def log_database_error(error_message, traceback=None, user_id=None, chat_id=None, data=None):
    log_error('database', error_message, traceback, user_id, chat_id, data)


def log_api_error(error_message, traceback=None, user_id=None, chat_id=None, data=None):
    log_error('api', error_message, traceback, user_id, chat_id, data)


def log_callback_error(error_message, traceback=None, user_id=None, chat_id=None, data=None, context_logger=None):
    log_error('callback', error_message, traceback, user_id, chat_id, data, context_logger)


def log_general_error(error_message, traceback=None, user_id=None, chat_id=None, data=None):
    log_error('general', error_message, traceback, user_id, chat_id, data)


def log_payment_error(error_message, traceback=None, user_id=None, chat_id=None, data=None):
    log_error('payment', error_message, traceback, user_id, chat_id, data)


def log_security_error(error_message, traceback=None, user_id=None, chat_id=None, data=None):
    log_error('security', error_message, traceback, user_id, chat_id, data)


def log_critical_error(error_message, traceback=None, user_id=None, chat_id=None, data=None):
    log_error('critical', error_message, traceback, user_id, chat_id, data)


# ============================================================
# توابع دریافت خطاها از دیتابیس
# ============================================================

def get_error_logs(limit=20, offset=0, error_type=None, is_resolved=None, start_date=None, end_date=None):
    """دریافت لیست خطاها با صفحه‌بندی و فیلترهای اختیاری."""
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
            cursor.execute(f"""
                SELECT * FROM error_logs 
                WHERE {where_clause}
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (*params, limit, offset))
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
        log_database_error(f"Error in get_error_logs: {str(e)}", traceback=str(e))
        return []


def get_error_log_by_id(error_id):
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
        log_database_error(f"Error in get_error_log_by_id for {error_id}: {str(e)}", traceback=str(e))
        return None


def get_total_errors(error_type=None, is_resolved=None):
    """تعداد کل خطاها (با فیلتر اختیاری نوع خطا و وضعیت حل‌شدن)"""
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
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            cursor.execute(f"SELECT COUNT(*) as count FROM error_logs WHERE {where_clause}", params)
            row = cursor.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        log_database_error(f"Error in get_total_errors: {str(e)}", traceback=str(e))
        return 0


def get_error_types_with_count():
    """دریافت لیست انواع خطاها به همراه تعداد هر کدام."""
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
        log_database_error(f"Error in get_error_types_with_count: {str(e)}", traceback=str(e))
        return []


def mark_error_as_resolved(error_id, resolved_by):
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
                return True
            return False
    except Exception as e:
        log_database_error(f"Error in mark_error_as_resolved for {error_id}: {str(e)}", traceback=str(e))
        return False


def mark_error_as_unresolved(error_id):
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
                return True
            return False
    except Exception as e:
        log_database_error(f"Error in mark_error_as_unresolved for {error_id}: {str(e)}", traceback=str(e))
        return False


def delete_error_logs(days=30):
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
            return deleted_count
    except Exception as e:
        log_database_error(f"Error in delete_error_logs: {str(e)}", traceback=str(e))
        return 0


def delete_error_log_by_id(error_id):
    """حذف یک خطا بر اساس شناسه"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM error_logs WHERE id = ?", (error_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return True
            return False
    except Exception as e:
        log_database_error(f"Error in delete_error_log_by_id for {error_id}: {str(e)}", traceback=str(e))
        return False


def clear_all_error_logs():
    """پاک کردن تمام خطاها (فقط برای مدیر سیستم)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM error_logs")
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
    except Exception as e:
        log_database_error(f"Error in clear_all_error_logs: {str(e)}", traceback=str(e))
        return 0


def get_error_stats():
    """دریافت آمار کلی خطاها برای داشبورد."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM error_logs")
            total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as unresolved FROM error_logs WHERE is_resolved = 0")
            unresolved = cursor.fetchone()['unresolved']
            cursor.execute("SELECT COUNT(*) as resolved FROM error_logs WHERE is_resolved = 1")
            resolved = cursor.fetchone()['resolved']
            cursor.execute("""
                SELECT id, error_type, error_message, created_at 
                FROM error_logs 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            last_error = cursor.fetchone()
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
        log_database_error(f"Error in get_error_stats: {str(e)}", traceback=str(e))
        return {'total': 0, 'unresolved': 0, 'resolved': 0, 'last_error': None, 'by_type': []}


# ============================================================
# توابع کمکی اضافی (برای رفع خطای Import)
# ============================================================

def get_errors_by_user(user_id: int, limit: int = 20):
    """دریافت خطاهای مربوط به یک کاربر خاص."""
    return db_get_errors_by_user(user_id, limit)


def get_errors_by_chat(chat_id: int, limit: int = 20):
    """دریافت خطاهای مربوط به یک چت خاص."""
    return db_get_errors_by_chat(chat_id, limit)


def get_error_count_by_type(error_type: str):
    """دریافت تعداد خطاهای یک نوع خاص"""
    return db_get_error_count_by_type(error_type)


def get_recent_errors(limit: int = 10):
    """دریافت خطاهای اخیر"""
    return db_get_recent_errors(limit)


def get_error_report(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """دریافت گزارش خطاها در بازه زمانی"""
    return db_get_error_report(start_date, end_date)


def clean_error_logs_with_retention(retention_days: int = 60):
    """پاکسازی خطاها بر اساس تعداد روز نگهداری"""
    return db_clean_error_logs_with_retention(retention_days)


# ============================================================
# کیبوردهای مدیریت خطا (با دکمه مشاهده فایل لاگ)
# ============================================================

def error_management_main_keyboard():
    stats = get_error_stats()
    unresolved = stats.get('unresolved', 0)
    return {
        "inline_keyboard": [
            [{"text": f"📋 لیست خطاها ({stats.get('total', 0)})", "callback_data": "admin_errors_list"}],
            [{"text": f"⚠️ خطاهای حل‌نشده ({unresolved})", "callback_data": "admin_errors_list_unresolved"}],
            [{"text": "📊 آمار خطاها", "callback_data": "admin_errors_stats"}],
            [{"text": "🗑️ پاکسازی خطاهای قدیمی (بیش از ۳۰ روز)", "callback_data": "admin_errors_cleanup"}],
            [{"text": "🗑️ حذف همه خطاها (⚠️ غیرقابل بازگشت)", "callback_data": "admin_errors_clear_all"}],
            # دکمه جدید: مشاهده فایل لاگ
            [{"text": "📄 مشاهده فایل لاگ (bot.log)", "callback_data": "admin_log_viewer"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


def error_list_keyboard(errors, page=0, per_page=10, total=0, show_unresolved=False):
    try:
        keyboard = []
        if not errors:
            keyboard.append([{"text": "❌ هیچ خطایی یافت نشد", "callback_data": "admin_none"}])
        else:
            for err in errors:
                error_id = err.get('id', '?')
                error_type = err.get('error_type', 'general')
                error_message = err.get('error_message', 'بدون پیام')[:30]
                is_resolved = err.get('is_resolved', 0)
                status_icon = "✅" if is_resolved == 1 else "🔴"
                type_icon = get_error_type_icon(error_type)
                keyboard.append([
                    {"text": f"{status_icon} {type_icon} #{error_id} - {error_message}",
                     "callback_data": f"admin_error_detail_{error_id}"}
                ])
        # دکمه‌های صفحه‌بندی
        nav_row = []
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_errors_list_page_{page-1}_{'unresolved' if show_unresolved else 'all'}"})
        if page < total_pages - 1:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_errors_list_page_{page+1}_{'unresolved' if show_unresolved else 'all'}"})
        if nav_row:
            keyboard.append(nav_row)
        keyboard.append([
            {"text": "📊 آمار خطاها", "callback_data": "admin_errors_stats"},
            {"text": "🗑️ پاکسازی قدیمی‌ها", "callback_data": "admin_errors_cleanup"}
        ])
        if show_unresolved:
            keyboard.append([
                {"text": "📋 نمایش همه خطاها", "callback_data": "admin_errors_list"}
            ])
        else:
            keyboard.append([
                {"text": "⚠️ فقط خطاهای حل‌نشده", "callback_data": "admin_errors_list_unresolved"}
            ])
        keyboard.append([
            {"text": "🔙 برگشت به مدیریت خطاها", "callback_data": "admin_errors"}
        ])
        return {"inline_keyboard": keyboard}
    except Exception as e:
        log_general_error(f"Error in error_list_keyboard: {str(e)}", traceback=str(e))
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری خطاها", "callback_data": "admin_errors"}]]}


def error_detail_keyboard(error_id, is_resolved):
    keyboard = []
    if is_resolved == 0:
        keyboard.append([
            {"text": "✅ علامت‌گذاری به عنوان حل‌شده", "callback_data": f"admin_error_resolve_{error_id}"}
        ])
    else:
        keyboard.append([
            {"text": "🔄 بازگشایی (حل‌نشده)", "callback_data": f"admin_error_unresolve_{error_id}"}
        ])
    keyboard.append([
        {"text": "🗑️ حذف این خطا", "callback_data": f"admin_error_delete_{error_id}"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت به لیست", "callback_data": "admin_errors_list"}
    ])
    return {"inline_keyboard": keyboard}


def error_stats_keyboard(stats):
    return {
        "inline_keyboard": [
            [{"text": "📋 مشاهده لیست خطاها", "callback_data": "admin_errors_list"}],
            [{"text": "⚠️ فقط خطاهای حل‌نشده", "callback_data": "admin_errors_list_unresolved"}],
            [{"text": "🗑️ پاکسازی خطاهای قدیمی", "callback_data": "admin_errors_cleanup"}],
            [{"text": "🔙 برگشت", "callback_data": "admin_errors"}]
        ]
    }


def error_cleanup_confirm_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "⚠️ آیا از پاکسازی خطاهای قدیمی‌تر از ۳۰ روز مطمئن هستید؟"}],
            [{"text": "✅ بله، پاکسازی شود", "callback_data": "admin_errors_cleanup_confirm"}],
            [{"text": "❌ خیر، انصراف", "callback_data": "admin_errors"}]
        ]
    }


# ============================================================
# هندلرهای مدیریت خطا (با ContextLogger)
# ============================================================

async def handle_error_management(chat_id: int, user_id: int) -> bool:
    """نمایش منوی اصلی مدیریت خطاها"""
    ctx_logger = ContextLogger("admin_panel.error_management", context={"user_id": user_id, "chat_id": chat_id})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        stats = get_error_stats()
        await send_message(
            chat_id,
            f"🚨 **مدیریت خطاها و اعلان‌ها**\n\n"
            f"📊 **آمار کلی:**\n"
            f"  • کل خطاها: {stats.get('total', 0)}\n"
            f"  • خطاهای حل‌نشده: {stats.get('unresolved', 0)}\n"
            f"  • خطاهای حل‌شده: {stats.get('resolved', 0)}\n\n"
            f"📌 از گزینه‌های زیر برای مدیریت خطاها استفاده کنید:",
            error_management_main_keyboard()
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_management: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در نمایش صفحه مدیریت خطاها.")
        return True


async def handle_error_list(chat_id: int, user_id: int, page: int = 0, show_unresolved: bool = False) -> bool:
    """نمایش لیست خطاها با صفحه‌بندی"""
    ctx_logger = ContextLogger("admin_panel.error_list", context={"user_id": user_id, "chat_id": chat_id, "page": page, "show_unresolved": show_unresolved})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        per_page = 10
        offset = page * per_page

        if show_unresolved:
            errors = get_error_logs(limit=per_page, offset=offset, is_resolved=0)
            total = get_total_errors(is_resolved=0)
        else:
            errors = get_error_logs(limit=per_page, offset=offset)
            total = get_total_errors()

        keyboard = error_list_keyboard(errors, page, per_page, total, show_unresolved)

        title = "🔴 خطاهای حل‌نشده" if show_unresolved else "📋 لیست خطاها"
        await send_message(
            chat_id,
            f"{title}\n\n"
            f"تعداد کل: {total} خطا\n"
            f"صفحه‌ی {page + 1} از {((total + per_page - 1) // per_page) if total > 0 else 1}",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_list: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست خطاها.")
        return True


async def handle_error_detail(chat_id: int, user_id: int, data: str) -> bool:
    """نمایش جزئیات کامل یک خطا (admin_error_detail_<error_id>)"""
    ctx_logger = ContextLogger("admin_panel.error_detail", context={"user_id": user_id, "chat_id": chat_id, "data": data})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        error_id = int(data.split("_")[-1])
        error = get_error_log_by_id(error_id)

        if not error:
            await send_message(chat_id, "❌ خطا یافت نشد.")
            return True

        msg = f"🚨 **جزئیات خطا #{error_id}**\n\n"
        msg += f"🔴 نوع: {error.get('error_type', 'نامشخص')}\n"
        msg += f"📝 پیام: {error.get('error_message', 'بدون پیام')}\n"
        msg += f"⏰ زمان: {format_datetime(error.get('created_at'))}\n"
        msg += f"📌 وضعیت: {'✅ حل‌شده' if error.get('is_resolved', 0) == 1 else '🔴 حل‌نشده'}\n"

        if error.get('user_id'):
            msg += f"👤 کاربر: {error.get('user_id')}\n"
        if error.get('chat_id'):
            msg += f"💬 چت: {error.get('chat_id')}\n"
        if error.get('resolved_by'):
            msg += f"✅ حل‌کننده: {error.get('resolved_by')}\n"
        if error.get('resolved_at'):
            msg += f"📅 زمان حل: {format_datetime(error.get('resolved_at'))}\n"

        if error.get('traceback'):
            msg += f"\n📄 **Traceback:**\n```\n{error.get('traceback', '')[:500]}"
            if len(error.get('traceback', '')) > 500:
                msg += "\n... (ادامه در دیتابیس)"
            msg += "\n```"

        if error.get('data'):
            try:
                data_str = json.dumps(error.get('data'), ensure_ascii=False, indent=2)
                msg += f"\n📊 **داده‌های اضافی:**\n```json\n{data_str[:300]}"
                if len(data_str) > 300:
                    msg += "\n... (ادامه در دیتابیس)"
                msg += "\n```"
            except:
                pass

        keyboard = error_detail_keyboard(error_id, error.get('is_resolved', 0))
        await send_message(chat_id, msg, keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_detail: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات خطا.")
        return True


async def handle_error_resolve(chat_id: int, user_id: int, data: str) -> bool:
    """علامت‌گذاری خطا به عنوان حل‌شده (admin_error_resolve_<error_id>)"""
    ctx_logger = ContextLogger("admin_panel.error_resolve", context={"user_id": user_id, "chat_id": chat_id, "data": data})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        error_id = int(data.split("_")[-1])
        success = mark_error_as_resolved(error_id, user_id)

        if success:
            await send_message(chat_id, f"✅ خطا #{error_id} با موفقیت به عنوان حل‌شده علامت‌گذاری شد.")
        else:
            await send_message(chat_id, f"❌ خطا در علامت‌گذاری خطا #{error_id}.")

        return await handle_error_detail(chat_id, user_id, f"admin_error_detail_{error_id}")
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_resolve: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در علامت‌گذاری خطا.")
        return True


async def handle_error_unresolve(chat_id: int, user_id: int, data: str) -> bool:
    """بازگشایی خطا (حل‌نشده) (admin_error_unresolve_<error_id>)"""
    ctx_logger = ContextLogger("admin_panel.error_unresolve", context={"user_id": user_id, "chat_id": chat_id, "data": data})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        error_id = int(data.split("_")[-1])
        success = mark_error_as_unresolved(error_id)

        if success:
            await send_message(chat_id, f"✅ خطا #{error_id} به حالت حل‌نشده بازگشت.")
        else:
            await send_message(chat_id, f"❌ خطا در بازگشایی خطا #{error_id}.")

        return await handle_error_detail(chat_id, user_id, f"admin_error_detail_{error_id}")
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_unresolve: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در بازگشایی خطا.")
        return True


async def handle_error_delete(chat_id: int, user_id: int, data: str) -> bool:
    """حذف یک خطا (admin_error_delete_<error_id>)"""
    ctx_logger = ContextLogger("admin_panel.error_delete", context={"user_id": user_id, "chat_id": chat_id, "data": data})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        error_id = int(data.split("_")[-1])
        success = delete_error_log_by_id(error_id)

        if success:
            await send_message(chat_id, f"✅ خطا #{error_id} با موفقیت حذف شد.")
        else:
            await send_message(chat_id, f"❌ خطا در حذف خطا #{error_id}.")

        return await handle_error_list(chat_id, user_id, 0, False)
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_delete: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در حذف خطا.")
        return True


async def handle_error_stats(chat_id: int, user_id: int) -> bool:
    """نمایش آمار خطاها"""
    ctx_logger = ContextLogger("admin_panel.error_stats", context={"user_id": user_id, "chat_id": chat_id})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        stats = get_error_stats()
        by_type = stats.get('by_type', [])

        msg = f"📊 **آمار خطاها**\n\n"
        msg += f"📌 کل خطاها: {stats.get('total', 0)}\n"
        msg += f"🔴 حل‌نشده: {stats.get('unresolved', 0)}\n"
        msg += f"✅ حل‌شده: {stats.get('resolved', 0)}\n\n"

        if by_type:
            msg += "📌 **تفکیک بر اساس نوع:**\n"
            for item in by_type:
                error_type = item.get('error_type', 'نامشخص')
                count = item.get('count', 0)
                icon = get_error_type_icon(error_type)
                msg += f"  {icon} {error_type}: {count}\n"
        else:
            msg += "هیچ خطایی ثبت نشده است.\n"

        last_error = stats.get('last_error')
        if last_error:
            msg += f"\n🕐 **آخرین خطا:**\n"
            msg += f"  #{last_error.get('id')} - {last_error.get('error_type')}: {last_error.get('error_message', '')[:40]}"

        keyboard = error_stats_keyboard(stats)
        await send_message(chat_id, msg, keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_stats: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در نمایش آمار خطاها.")
        return True


async def handle_error_cleanup(chat_id: int, user_id: int) -> bool:
    """نمایش تاییدیه پاکسازی خطاهای قدیمی"""
    ctx_logger = ContextLogger("admin_panel.error_cleanup", context={"user_id": user_id, "chat_id": chat_id})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        await send_message(
            chat_id,
            "🗑️ **پاکسازی خطاهای قدیمی**\n\n"
            "⚠️ این عملیات تمام خطاهای ثبت‌شده‌ی قدیمی‌تر از ۳۰ روز را حذف می‌کند.\n"
            "این عملیات قابل بازگشت نیست.\n\n"
            "آیا مطمئن هستید؟",
            error_cleanup_confirm_keyboard()
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_cleanup: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در نمایش تاییدیه پاکسازی.")
        return True


async def handle_error_cleanup_confirm(chat_id: int, user_id: int) -> bool:
    """اجرای پاکسازی خطاهای قدیمی"""
    ctx_logger = ContextLogger("admin_panel.error_cleanup_confirm", context={"user_id": user_id, "chat_id": chat_id})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        deleted = delete_error_logs(30)
        await send_message(
            chat_id,
            f"✅ پاکسازی کامل شد.\n"
            f"تعداد خطاهای حذف‌شده: {deleted}",
            error_management_main_keyboard()
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_cleanup_confirm: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در پاکسازی خطاها.")
        return True


async def handle_error_list_page(chat_id: int, user_id: int, data: str) -> bool:
    """صفحه‌بندی لیست خطاها (admin_errors_list_page_<page>_<type>)"""
    ctx_logger = ContextLogger("admin_panel.error_list_page", context={"user_id": user_id, "chat_id": chat_id, "data": data})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        parts = data.split("_")
        page = int(parts[4]) if len(parts) > 4 else 0
        filter_type = parts[5] if len(parts) > 5 else 'all'
        show_unresolved = (filter_type == 'unresolved')

        return await handle_error_list(chat_id, user_id, page, show_unresolved)
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_list_page: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی.")
        return True


async def handle_error_clear_all(chat_id: int, user_id: int) -> bool:
    """نمایش تاییدیه برای حذف همه خطاها"""
    ctx_logger = ContextLogger("admin_panel.error_clear_all", context={"user_id": user_id, "chat_id": chat_id})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        total = get_total_errors()
        await send_message(
            chat_id,
            f"⚠️ **حذف همه خطاها**\n\n"
            f"این عملیات **همه {total} خطای ثبت‌شده** را به‌طور کامل حذف می‌کند.\n"
            f"این عملیات **غیرقابل بازگشت** است.\n\n"
            f"آیا مطمئن هستید؟",
            {
                "inline_keyboard": [
                    [{"text": f"🗑️ بله، همه {total} خطا حذف شوند", "callback_data": "admin_errors_clear_all_confirm"}],
                    [{"text": "❌ خیر، انصراف", "callback_data": "admin_errors"}]
                ]
            }
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_clear_all: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در نمایش تاییدیه حذف همه خطاها.")
        return True


async def handle_error_clear_all_confirm(chat_id: int, user_id: int) -> bool:
    """اجرای حذف همه خطاها"""
    ctx_logger = ContextLogger("admin_panel.error_clear_all_confirm", context={"user_id": user_id, "chat_id": chat_id})

    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        deleted = clear_all_error_logs()
        await send_message(
            chat_id,
            f"✅ همه خطاها ({deleted} رکورد) با موفقیت حذف شدند.",
            error_management_main_keyboard()
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_error_clear_all_confirm: {str(e)}",
            traceback=str(e),
            user_id=user_id,
            chat_id=chat_id,
            context_logger=ctx_logger
        )
        await send_message(chat_id, "❌ خطا در حذف همه خطاها.")
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'log_error', 'log_database_error', 'log_api_error', 'log_callback_error',
    'log_general_error', 'log_payment_error', 'log_security_error', 'log_critical_error',
    'get_error_logs', 'get_error_log_by_id', 'get_total_errors', 'get_error_types_with_count',
    'mark_error_as_resolved', 'mark_error_as_unresolved',
    'delete_error_logs', 'delete_error_log_by_id', 'clear_all_error_logs',
    'get_error_stats',
    'get_errors_by_user', 'get_errors_by_chat', 'get_error_count_by_type',
    'get_recent_errors', 'get_error_report', 'clean_error_logs_with_retention',
    'handle_error_management', 'handle_error_list', 'handle_error_detail',
    'handle_error_resolve', 'handle_error_unresolve', 'handle_error_delete',
    'handle_error_stats', 'handle_error_cleanup', 'handle_error_cleanup_confirm',
    'handle_error_list_page', 'handle_error_clear_all', 'handle_error_clear_all_confirm',
]