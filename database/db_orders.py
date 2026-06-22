# database/db_orders.py
# توابع مربوط به پاسخ‌ها، سفارشات و تنظیمات
# نسخه نهایی اصلاح‌شده با مدیریت خطا و لاگ‌گیری کامل
# رفع SyntaxError در خط ۳۹۴

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from .db_connection import get_db_connection
from logger_config import logger
from utils.error_handler import log_database_error, log_general_error


# ==================== پاسخ‌های کاربران ====================

def save_user_answer(user_id, button_id, question_id, answer):
    """ذخیره پاسخ کاربر با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_answers (user_id, button_id, question_id, answer) VALUES (?, ?, ?, ?)",
                (user_id, button_id, question_id, answer)
            )
            conn.commit()
            logger.debug(f"پاسخ کاربر {user_id} برای سوال {question_id} ذخیره شد.")
    except Exception as e:
        log_database_error(
            f"خطا در ذخیره پاسخ کاربر {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )


def get_user_answers(user_id, button_id):
    """دریافت پاسخ‌های کاربر با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT q.question_text, q.array_name, ua.answer FROM user_answers ua JOIN questions q ON ua.question_id = q.id WHERE ua.user_id = ? AND ua.button_id = ? ORDER BY q.sort_order",
                (user_id, button_id)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"خطا در دریافت پاسخ‌های کاربر {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return []


# ==================== سفارشات ====================

def save_dynamic_order(user_id, button_id, order_data, payment_amount=None, tracking_code=None, status="pending"):
    """ثبت سفارش جدید با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO dynamic_orders 
                   (user_id, button_id, order_data, payment_amount, tracking_code, status) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, button_id, json.dumps(order_data, ensure_ascii=False), payment_amount, tracking_code, status)
            )
            conn.commit()
            order_id = cursor.lastrowid
            logger.info(f"✅ سفارش جدید با id={order_id} برای کاربر {user_id} ثبت شد.")
            return order_id
    except Exception as e:
        log_database_error(
            f"خطا در ثبت سفارش برای کاربر {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return None


def get_dynamic_orders(status=None):
    """
    دریافت لیست سفارشات با مدیریت خطا
    در صورت بروز خطا، لیست خالی برمی‌گرداند و خطا را لاگ می‌کند
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM dynamic_orders WHERE status = ? ORDER BY created_at DESC", (status,))
            else:
                cursor.execute("SELECT * FROM dynamic_orders ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"خطا در دریافت لیست سفارشات: {str(e)}",
            traceback=str(e)
        )
        return []  # بازگرداندن لیست خالی به جای None


def get_dynamic_order_by_id(order_id):
    """دریافت سفارش با شناسه با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dynamic_orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log_database_error(
            f"خطا در دریافت سفارش {order_id}: {str(e)}",
            traceback=str(e),
            data={'order_id': order_id}
        )
        return None


def update_order_status(order_id, new_status, user_id, note=None):
    """
    تغییر وضعیت سفارش و ثبت در تاریخچه با مدیریت خطا
    وضعیت‌های مجاز: pending, paid, completed, cancelled, failed, refunded
    """
    valid_statuses = ['pending', 'paid', 'completed', 'cancelled', 'failed', 'refunded']
    if new_status not in valid_statuses:
        logger.warning(f"وضعیت نامعتبر: {new_status}")
        return False

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # دریافت وضعیت فعلی
            cursor.execute("SELECT status FROM dynamic_orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"سفارش {order_id} یافت نشد.")
                return False

            old_status = row['status']
            if old_status == new_status:
                logger.info(f"وضعیت سفارش {order_id} تغییری نکرده است.")
                return True

            # به‌روزرسانی وضعیت
            cursor.execute(
                "UPDATE dynamic_orders SET status = ? WHERE id = ?",
                (new_status, order_id)
            )
            conn.commit()

            # ثبت در تاریخچه وضعیت‌ها (فیلد status_history)
            cursor.execute("SELECT status_history FROM dynamic_orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            history = json.loads(row['status_history']) if row and row['status_history'] else []
            history.append({
                'from': old_status,
                'to': new_status,
                'by': user_id,
                'timestamp': datetime.now().isoformat(),
                'note': note
            })
            cursor.execute(
                "UPDATE dynamic_orders SET status_history = ? WHERE id = ?",
                (json.dumps(history, ensure_ascii=False), order_id)
            )
            conn.commit()

            # ثبت در جدول order_logs
            add_order_log(order_id, user_id, 'status_change', old_status, new_status, note)

            logger.info(f"✅ وضعیت سفارش {order_id} از {old_status} به {new_status} تغییر یافت.")
            return True
            
    except Exception as e:
        log_database_error(
            f"خطا در تغییر وضعیت سفارش {order_id}: {str(e)}",
            traceback=str(e),
            data={'order_id': order_id}
        )
        return False


def delete_order(order_id):
    """حذف سفارش با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # بررسی وجود سفارش
            cursor.execute("SELECT user_id FROM dynamic_orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"سفارش {order_id} یافت نشد.")
                return False

            user_id = row['user_id']

            # ثبت لاگ حذف
            add_order_log(order_id, user_id, 'order_deleted', note=f"سفارش توسط ادمین حذف شد")

            # حذف سفارش
            cursor.execute("DELETE FROM dynamic_orders WHERE id = ?", (order_id,))
            conn.commit()

            logger.info(f"🗑️ سفارش {order_id} حذف شد.")
            return True
            
    except Exception as e:
        log_database_error(
            f"خطا در حذف سفارش {order_id}: {str(e)}",
            traceback=str(e),
            data={'order_id': order_id}
        )
        return False


def search_orders(keyword):
    """جستجوی سفارشات با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if keyword.isdigit():
                cursor.execute('''
                    SELECT * FROM dynamic_orders 
                    WHERE tracking_code LIKE ? OR user_id LIKE ? OR id LIKE ?
                    ORDER BY created_at DESC
                ''', (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                cursor.execute("SELECT * FROM dynamic_orders ORDER BY created_at DESC")
                all_orders = cursor.fetchall()
                results = []
                keyword_lower = keyword.lower()
                for order in all_orders:
                    order_dict = dict(order)
                    try:
                        order_data = json.loads(order_dict.get('order_data', '{}'))
                        answers = order_data.get('answers', {})
                        for q_text, ans in answers.items():
                            if keyword_lower in str(ans).lower():
                                results.append(order_dict)
                                break
                    except Exception as e:
                        log_general_error(
                            f"Error parsing order_data in search for order {order_dict.get('id')}: {str(e)}",
                            traceback=str(e)
                        )
                        continue
                return results
                
    except Exception as e:
        log_database_error(
            f"خطا در جستجوی سفارشات با کلمه {keyword}: {str(e)}",
            traceback=str(e)
        )
        return []


def get_order_stats():
    """دریافت آمار سفارشات با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # تعداد کل و مجموع مبلغ
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(COALESCE(payment_amount, 0)) as total_amount,
                    AVG(COALESCE(payment_amount, 0)) as avg_amount
                FROM dynamic_orders
            ''')
            stats = dict(cursor.fetchone())

            # تفکیک وضعیت‌ها
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM dynamic_orders 
                GROUP BY status
            ''')
            status_rows = cursor.fetchall()
            stats['statuses'] = {row['status']: row['count'] for row in status_rows}

            # بیشترین سرویس
            cursor.execute('''
                SELECT button_id, COUNT(*) as count 
                FROM dynamic_orders 
                GROUP BY button_id 
                ORDER BY count DESC 
                LIMIT 1
            ''')
            top_service = cursor.fetchone()
            if top_service:
                stats['top_service_id'] = top_service['button_id']
                stats['top_service_count'] = top_service['count']
            else:
                stats['top_service_id'] = None
                stats['top_service_count'] = 0

            # تعداد کل کاربران
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) as total_users 
                FROM dynamic_orders
            ''')
            stats['total_users'] = cursor.fetchone()['total_users']

            return stats
            
    except Exception as e:
        log_database_error(
            f"خطا در دریافت آمار سفارشات: {str(e)}",
            traceback=str(e)
        )
        return {
            'total': 0,
            'total_amount': 0,
            'avg_amount': 0,
            'statuses': {},
            'top_service_id': None,
            'top_service_count': 0,
            'total_users': 0
        }


def add_order_note(order_id, note, user_id):
    """افزودن یادداشت به سفارش با مدیریت خطا"""
    try:
        if not note or note.strip() == "":
            return False

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # بررسی وجود سفارش
            cursor.execute("SELECT admin_note FROM dynamic_orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"سفارش {order_id} یافت نشد.")
                return False

            # اضافه کردن یادداشت جدید به انتهای یادداشت‌های قبلی
            old_note = row['admin_note'] or ""
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            new_note = f"{old_note}\n[{timestamp}] {note}" if old_note else f"[{timestamp}] {note}"

            cursor.execute(
                "UPDATE dynamic_orders SET admin_note = ? WHERE id = ?",
                (new_note, order_id)
            )
            conn.commit()

            # ثبت در جدول order_logs
            add_order_log(order_id, user_id, 'note_added', note=note)

            logger.info(f"📝 یادداشت به سفارش {order_id} اضافه شد.")
            return True
            
    except Exception as e:
        log_database_error(
            f"خطا در افزودن یادداشت به سفارش {order_id}: {str(e)}",
            traceback=str(e),
            data={'order_id': order_id}
        )
        return False


def add_order_log(order_id, user_id, action, old_value=None, new_value=None, note=None):
    """ثبت لاگ سفارش با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO order_logs (order_id, user_id, action, old_value, new_value, note) VALUES (?, ?, ?, ?, ?, ?)",
                (order_id, user_id, action, old_value, new_value, note)
            )
            conn.commit()
            logger.debug(f"لاگ سفارش {order_id} ثبت شد: {action}")
    except Exception as e:
        log_database_error(
            f"خطا در ثبت لاگ سفارش {order_id}: {str(e)}",
            traceback=str(e),
            data={'order_id': order_id}
        )


def get_order_logs(order_id):
    """دریافت لاگ‌های سفارش با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM order_logs 
                WHERE order_id = ? 
                ORDER BY created_at DESC
            ''', (order_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"خطا در دریافت لاگ‌های سفارش {order_id}: {str(e)}",
            traceback=str(e),
            data={'order_id': order_id}
        )
        return []


def get_user_order_stats(user_id):
    """دریافت آمار سفارشات کاربر با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(COALESCE(payment_amount, 0)) as total_amount,
                    AVG(COALESCE(payment_amount, 0)) as avg_amount
                FROM dynamic_orders 
                WHERE user_id = ?
            ''', (user_id,))
            stats = dict(cursor.fetchone())

            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM dynamic_orders 
                WHERE user_id = ? 
                GROUP BY status
            ''', (user_id,))
            status_rows = cursor.fetchall()
            stats['statuses'] = {row['status']: row['count'] for row in status_rows}

            # آخرین سفارش
            cursor.execute('''
                SELECT * FROM dynamic_orders 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (user_id,))
            last_order = cursor.fetchone()
            stats['last_order'] = dict(last_order) if last_order else None

            return stats
            
    except Exception as e:
        log_database_error(
            f"خطا در دریافت آمار سفارشات کاربر {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return {
            'total': 0,
            'total_amount': 0,
            'avg_amount': 0,
            'statuses': {},
            'last_order': None
        }


def get_orders_for_reminder(hours=24):
    """دریافت سفارشات برای یادآوری با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM dynamic_orders 
                WHERE status = 'pending' 
                AND created_at < datetime('now', '-' || ? || ' hours')
                AND (last_reminder_sent IS NULL OR last_reminder_sent < datetime('now', '-6 hours'))
                ORDER BY created_at ASC
            """, (hours,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"خطا در دریافت سفارشات برای یادآوری: {str(e)}",
            traceback=str(e)
        )
        return []


def update_reminder_time(order_id):
    """بروزرسانی زمان یادآوری با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE dynamic_orders SET last_reminder_sent = ? WHERE id = ?",
                (datetime.now().isoformat(), order_id)
            )
            conn.commit()
            logger.debug(f"زمان یادآوری سفارش {order_id} بروزرسانی شد.")
            return True
    except Exception as e:
        log_database_error(
            f"خطا در بروزرسانی زمان یادآوری سفارش {order_id}: {str(e)}",
            traceback=str(e),
            data={'order_id': order_id}
        )
        return False


# ============================================================
# توابع مربوط به قیمت متغیر (در صورت نیاز)
# ============================================================

def get_button_price_info(button_id):
    """دریافت اطلاعات قیمت دکمه با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT price_amount, price_label, price_type, min_price, max_price 
                FROM buttons 
                WHERE id = ?
            """, (button_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {
                'price_amount': 50000,
                'price_label': 'هزینه خدمات',
                'price_type': 'fixed',
                'min_price': None,
                'max_price': None
            }
    except Exception as e:
        log_database_error(
            f"خطا در دریافت اطلاعات قیمت دکمه {button_id}: {str(e)}",
            traceback=str(e)
        )
        return {
            'price_amount': 50000,
            'price_label': 'هزینه خدمات',
            'price_type': 'fixed',
            'min_price': None,
            'max_price': None
        }


def update_button_price(button_id, price_amount=None, price_label=None, price_type=None, min_price=None, max_price=None):
    """به‌روزرسانی اطلاعات قیمت دکمه با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            updates = []
            values = []
            
            if price_amount is not None:
                updates.append("price_amount = ?")
                values.append(price_amount)
            if price_label is not None:
                updates.append("price_label = ?")
                values.append(price_label)
            if price_type is not None:
                updates.append("price_type = ?")
                values.append(price_type)
            if min_price is not None:
                updates.append("min_price = ?")
                values.append(min_price)
            if max_price is not None:
                updates.append("max_price = ?")
                values.append(max_price)
            
            if updates:
                values.append(button_id)
                cursor.execute(f"UPDATE buttons SET {', '.join(updates)} WHERE id = ?", values)
                conn.commit()
                logger.info(f"✅ اطلاعات قیمت دکمه {button_id} به‌روزرسانی شد.")
                return True
            return False
            
    except Exception as e:
        log_database_error(
            f"خطا در به‌روزرسانی قیمت دکمه {button_id}: {str(e)}",
            traceback=str(e)
        )
        return False


# ==================== تنظیمات ====================

def set_setting(key, value, description=None):
    """ذخیره تنظیمات با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value, description, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (key, value, description)
            )
            conn.commit()
            logger.debug(f"تنظیم {key} = {value} ذخیره شد.")
    except Exception as e:
        log_database_error(
            f"خطا در ذخیره تنظیم {key}: {str(e)}",
            traceback=str(e)
        )


def get_setting(key):
    """دریافت تنظیمات با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None
    except Exception as e:
        log_database_error(
            f"خطا در دریافت تنظیم {key}: {str(e)}",
            traceback=str(e)
        )
        return None


def get_all_settings():
    """دریافت همه تنظیمات با مدیریت خطا"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM settings")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"خطا در دریافت همه تنظیمات: {str(e)}",
            traceback=str(e)
        )
        return []


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'save_user_answer',
    'get_user_answers',
    'save_dynamic_order',
    'get_dynamic_orders',
    'get_dynamic_order_by_id',
    'set_setting',
    'get_setting',
    'get_all_settings',
    'add_order_log',
    'update_order_status',
    'delete_order',
    'search_orders',
    'get_order_stats',
    'add_order_note',
    'get_order_logs',
    'get_user_order_stats',
    'get_button_price_info',
    'update_button_price',
    'update_reminder_time',
    'get_orders_for_reminder',
]