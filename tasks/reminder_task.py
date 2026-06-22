# tasks/reminder_task.py
# تسک یادآوری سفارشات ناتمام به کاربران
# اصلاح شده با استفاده از messenger برای ارسال همزمان

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from logger_config import logger
from config import config
from database import get_db_connection, get_dynamic_orders, get_user
from core import send_message
from utils.error_handler import (
    log_critical_error,
    log_general_error,
    log_database_error,
    log_api_error
)

# ========== ایمپورت messenger ==========
from messenger import Messenger, get_messenger, send_messages_batch


# ============================================================
# ارسال یادآوری با messenger
# ============================================================

async def _send_reminder(order: dict, user_id: int) -> bool:
    """
    ارسال پیام یادآوری به کاربر با استفاده از messenger
    
    پارامترها:
        order: دیکشنری سفارش
        user_id: شناسه کاربر
    
    بازگشت: True در صورت موفقیت، False در غیر این صورت
    """
    try:
        # دریافت اطلاعات کاربر
        user = get_user(user_id)
        if not user:
            log_general_error(
                f"User {user_id} not found for reminder",
                user_id=user_id
            )
            return False
        
        # استخراج نام کاربر
        first_name = user.get('first_name') or user.get('username') or 'کاربر گرامی'
        
        # استخراج اطلاعات سفارش
        order_id = order.get('id')
        amount = order.get('payment_amount', 0) or 0
        created_at = order.get('created_at', '')
        tracking_code = order.get('tracking_code', 'ندارد')
        
        # دریافت نام سرویس
        from admin_panel.common import get_service_name
        service_name = get_service_name(order.get('button_id'))
        
        # محاسبه زمان گذشته
        try:
            if isinstance(created_at, str):
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_time = created_at
            elapsed_hours = int((datetime.now() - created_time).total_seconds() / 3600)
            elapsed_days = elapsed_hours // 24
            elapsed_hours_display = elapsed_hours % 24
            time_text = f"{elapsed_days} روز و {elapsed_hours_display} ساعت" if elapsed_days > 0 else f"{elapsed_hours} ساعت"
        except Exception as e:
            log_database_error(
                f"Error calculating elapsed time for order {order_id}: {str(e)}",
                traceback=str(e)
            )
            time_text = "چند روز"
        
        # ساخت پیام یادآوری
        msg = (
            f"⏰ **یادآوری سفارش ناتمام**\n\n"
            f"سلام {first_name} عزیز،\n\n"
            f"شما یک سفارش ثبت کرده‌اید که **هنوز پرداخت نشده** است.\n\n"
            f"📋 **جزئیات سفارش:**\n"
            f"  🆔 شناسه: {order_id}\n"
            f"  🔘 سرویس: {service_name}\n"
            f"  💰 مبلغ: {amount:,} ریال\n"
            f"  📅 تاریخ ثبت: {created_at}\n"
            f"  ⏱️  زمان گذشته: {time_text}\n"
            f"  🎫 کد رهگیری: {tracking_code}\n\n"
            f"📌 **نکته:**\n"
            f"برای تکمیل سفارش، لطفاً هرچه سریع‌تر اقدام به پرداخت کنید.\n"
            f"در صورت نیاز به راهنمایی، با پشتیبانی تماس بگیرید.\n\n"
            f"با تشکر از شما 🙏"
        )
        
        # ========== ارسال با messenger ==========
        messenger = get_messenger()
        result = await messenger.send_messages([
            {'chat_id': user_id, 'text': msg}
        ])
        
        if result and len(result) > 0:
            if isinstance(result[0], Exception):
                log_api_error(
                    f"Error sending reminder to user {user_id}: {result[0]}",
                    traceback=str(result[0]),
                    user_id=user_id
                )
                return False
            return True
        
        return False
        
    except Exception as e:
        log_api_error(
            f"Error sending reminder to user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )
        return False


# ============================================================
# اجرای تسک یادآوری با messenger
# ============================================================

async def run_reminder_task():
    """
    اجرای تسک یادآوری سفارشات ناتمام با استفاده از messenger برای ارسال همزمان
    این تابع توسط Scheduler در زمان‌های مشخص فراخوانی می‌شود
    """
    try:
        logger.info("🔄 Starting reminder task with messenger...")
        start_time = datetime.now()
        
        # دریافت تنظیمات
        reminder_after_hours = config.REMINDER_AFTER_HOURS
        reminder_interval_hours = config.REMINDER_INTERVAL_HOURS
        
        # دریافت همه سفارشات
        orders = get_dynamic_orders()
        pending_orders = [o for o in orders if o.get('status') == 'pending']
        
        if not pending_orders:
            logger.info("No pending orders to remind")
            return True
        
        logger.info(f"Found {len(pending_orders)} pending orders")
        
        results = {
            'total': len(pending_orders),
            'reminded': 0,
            'failed': 0,
            'errors': [],
            'orders': []
        }
        
        now = datetime.now()
        
        # ========== فیلتر سفارشات واجد شرایط ==========
        eligible_orders = []
        for order in pending_orders:
            order_id = order.get('id')
            user_id = order.get('user_id')
            created_at = order.get('created_at')
            
            if not user_id or not created_at:
                continue
            
            # محاسبه زمان گذشته از ثبت سفارش
            try:
                if isinstance(created_at, str):
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    created_time = created_at
            except Exception as e:
                log_database_error(
                    f"Invalid created_at for order {order_id}: {str(e)}",
                    traceback=str(e)
                )
                continue
            
            elapsed_hours = (now - created_time).total_seconds() / 3600
            
            # اگر سفارش کمتر از زمان تعیین‌شده ثبت شده، رد کن
            if elapsed_hours < reminder_after_hours:
                continue
            
            # بررسی اینکه آیا یادآوری قبلاً ارسال شده است
            last_reminder = order.get('last_reminder_sent')
            if last_reminder:
                try:
                    last_time = datetime.fromisoformat(last_reminder.replace('Z', '+00:00'))
                    elapsed_since_last = (now - last_time).total_seconds() / 3600
                    if elapsed_since_last < reminder_interval_hours:
                        continue
                except Exception as e:
                    log_database_error(
                        f"Invalid last_reminder_sent for order {order_id}: {str(e)}",
                        traceback=str(e)
                    )
                    continue
            
            eligible_orders.append(order)
        
        if not eligible_orders:
            logger.info("No eligible orders for reminder")
            return True
        
        logger.info(f"Found {len(eligible_orders)} eligible orders for reminder")
        
        # ========== ارسال یادآوری‌ها با messenger (همزمان) ==========
        messenger = get_messenger()
        batch_size = 20  # تعداد پیام‌های همزمان
        
        # ساخت لیست پیام‌ها
        messages = []
        order_map = {}
        
        for order in eligible_orders:
            user_id = order.get('user_id')
            if not user_id:
                continue
            
            # دریافت اطلاعات کاربر
            user = get_user(user_id)
            if not user:
                continue
            
            first_name = user.get('first_name') or user.get('username') or 'کاربر گرامی'
            order_id = order.get('id')
            amount = order.get('payment_amount', 0) or 0
            created_at = order.get('created_at', '')
            tracking_code = order.get('tracking_code', 'ندارد')
            
            from admin_panel.common import get_service_name
            service_name = get_service_name(order.get('button_id'))
            
            try:
                if isinstance(created_at, str):
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    created_time = created_at
                elapsed_hours = int((datetime.now() - created_time).total_seconds() / 3600)
                elapsed_days = elapsed_hours // 24
                elapsed_hours_display = elapsed_hours % 24
                time_text = f"{elapsed_days} روز و {elapsed_hours_display} ساعت" if elapsed_days > 0 else f"{elapsed_hours} ساعت"
            except Exception as e:
                log_database_error(
                    f"Error calculating elapsed time for order {order_id}: {str(e)}",
                    traceback=str(e)
                )
                time_text = "چند روز"
            
            msg = (
                f"⏰ **یادآوری سفارش ناتمام**\n\n"
                f"سلام {first_name} عزیز،\n\n"
                f"شما یک سفارش ثبت کرده‌اید که **هنوز پرداخت نشده** است.\n\n"
                f"📋 **جزئیات سفارش:**\n"
                f"  🆔 شناسه: {order_id}\n"
                f"  🔘 سرویس: {service_name}\n"
                f"  💰 مبلغ: {amount:,} ریال\n"
                f"  📅 تاریخ ثبت: {created_at}\n"
                f"  ⏱️  زمان گذشته: {time_text}\n"
                f"  🎫 کد رهگیری: {tracking_code}\n\n"
                f"📌 **نکته:**\n"
                f"برای تکمیل سفارش، لطفاً هرچه سریع‌تر اقدام به پرداخت کنید.\n"
                f"در صورت نیاز به راهنمایی، با پشتیبانی تماس بگیرید.\n\n"
                f"با تشکر از شما 🙏"
            )
            
            messages.append({'chat_id': user_id, 'text': msg})
            order_map[user_id] = order
        
        if not messages:
            logger.info("No messages to send")
            return True
        
        # ارسال با messenger (تقسیم به دسته‌های کوچک)
        all_results = []
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i+batch_size]
            batch_results = await messenger.send_messages(batch)
            all_results.extend(batch_results)
            
            # تأخیر بین دسته‌ها
            if i + batch_size < len(messages):
                await asyncio.sleep(0.3)
        
        # تحلیل نتایج و بروزرسانی
        success_count = 0
        fail_count = 0
        
        for i, result in enumerate(all_results):
            if i >= len(messages):
                break
            
            msg_data = messages[i]
            user_id = msg_data['chat_id']
            order = order_map.get(user_id)
            
            if isinstance(result, Exception):
                fail_count += 1
                results['errors'].append(f"User {user_id}: {str(result)}")
                logger.error(f"Failed to send reminder to user {user_id}: {result}")
            elif result is not None:
                success_count += 1
                results['reminded'] += 1
                results['orders'].append({
                    'order_id': order.get('id') if order else None,
                    'user_id': user_id,
                    'status': 'sent'
                })
                # بروزرسانی last_reminder_sent
                if order:
                    await _update_reminder_time(order.get('id'))
                logger.info(f"✅ Reminder sent to user {user_id} via messenger")
            else:
                fail_count += 1
                results['errors'].append(f"User {user_id}: No response")
                logger.warning(f"No response for reminder to user {user_id}")
        
        results['failed'] = fail_count
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"✅ Reminder task completed with messenger\n"
            f"   📊 Total pending: {results['total']}\n"
            f"   ✅ Eligible: {len(eligible_orders)}\n"
            f"   ✅ Sent: {results['reminded']}\n"
            f"   ❌ Failed: {results['failed']}\n"
            f"   ⏱️  Time: {elapsed:.2f} seconds"
        )
        
        # ارسال گزارش به OWNER
        if results['reminded'] > 0 or results['failed'] > 0:
            await _notify_owner(results, elapsed)
        
        return True
        
    except Exception as e:
        log_critical_error(
            f"Error in reminder_task: {str(e)}",
            traceback=str(e)
        )
        return False


# ============================================================
# توابع کمکی (بدون تغییر)
# ============================================================

async def _update_reminder_time(order_id: int):
    """
    بروزرسانی زمان آخرین یادآوری در دیتابیس
    
    پارامترها:
        order_id: شناسه سفارش
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE dynamic_orders SET last_reminder_sent = ? WHERE id = ?",
                (datetime.now().isoformat(), order_id)
            )
            conn.commit()
    except Exception as e:
        log_database_error(
            f"Error updating reminder time for order {order_id}: {str(e)}",
            traceback=str(e)
        )


async def _notify_owner(results: dict, elapsed: float):
    """
    ارسال گزارش یادآوری به OWNER
    
    پارامترها:
        results: دیکشنری نتایج
        elapsed: زمان اجرا (ثانیه)
    """
    try:
        from core import send_message, OWNER_ID
        
        msg = (
            f"⏰ **گزارش یادآوری سفارشات**\n\n"
            f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"⏱️  زمان اجرا: {elapsed:.2f} ثانیه\n\n"
            f"📊 **نتایج:**\n"
            f"  📦 کل سفارشات در انتظار: {results['total']}\n"
            f"  ✅ یادآوری ارسال‌شده: {results['reminded']}\n"
            f"  ❌ ناموفق: {results['failed']}\n"
        )
        
        if results['reminded'] > 0:
            msg += f"\n📌 **سفارشات یادآوری‌شده:**\n"
            for order in results['orders'][:10]:  # نمایش ۱۰ مورد اول
                msg += f"  🆔 {order['order_id']} - کاربر {order['user_id']}\n"
            if len(results['orders']) > 10:
                msg += f"  ... و {len(results['orders']) - 10} مورد دیگر\n"
        
        if results['errors']:
            msg += f"\n⚠️ **خطاها:**\n"
            for error in results['errors'][:5]:
                msg += f"  ❌ {error}\n"
            if len(results['errors']) > 5:
                msg += f"  ... و {len(results['errors']) - 5} خطای دیگر\n"
        
        await send_message(OWNER_ID, msg)
        
    except Exception as e:
        log_api_error(
            f"Error sending reminder notification to owner: {str(e)}",
            traceback=str(e),
            user_id=OWNER_ID if 'OWNER_ID' in dir() else None
        )


# ============================================================
# وضعیت یادآوری‌ها (بدون تغییر)
# ============================================================

def get_reminder_status() -> dict:
    """
    دریافت وضعیت یادآوری‌ها
    
    بازگشت: دیکشنری شامل اطلاعات سفارشات نیازمند یادآوری
    """
    try:
        orders = get_dynamic_orders()
        pending_orders = [o for o in orders if o.get('status') == 'pending']
        
        now = datetime.now()
        reminder_after_hours = config.REMINDER_AFTER_HOURS
        
        eligible_orders = []
        for order in pending_orders:
            created_at = order.get('created_at')
            if not created_at:
                continue
            
            try:
                if isinstance(created_at, str):
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    created_time = created_at
                
                elapsed_hours = (now - created_time).total_seconds() / 3600
                
                if elapsed_hours >= reminder_after_hours:
                    last_reminder = order.get('last_reminder_sent')
                    if last_reminder:
                        try:
                            last_time = datetime.fromisoformat(last_reminder.replace('Z', '+00:00'))
                            elapsed_since_last = (now - last_time).total_seconds() / 3600
                            if elapsed_since_last >= config.REMINDER_INTERVAL_HOURS:
                                eligible_orders.append({
                                    'order_id': order.get('id'),
                                    'user_id': order.get('user_id'),
                                    'created_at': created_at,
                                    'elapsed_hours': elapsed_hours,
                                    'last_reminder': last_reminder,
                                    'status': 'eligible'
                                })
                        except Exception as e:
                            log_database_error(
                                f"Error parsing last_reminder for order {order.get('id')}: {str(e)}",
                                traceback=str(e)
                            )
                            eligible_orders.append({
                                'order_id': order.get('id'),
                                'user_id': order.get('user_id'),
                                'created_at': created_at,
                                'elapsed_hours': elapsed_hours,
                                'last_reminder': None,
                                'status': 'eligible'
                            })
                    else:
                        eligible_orders.append({
                            'order_id': order.get('id'),
                            'user_id': order.get('user_id'),
                            'created_at': created_at,
                            'elapsed_hours': elapsed_hours,
                            'last_reminder': None,
                            'status': 'eligible'
                        })
            except Exception as e:
                log_database_error(
                    f"Error processing order {order.get('id')} for reminder status: {str(e)}",
                    traceback=str(e)
                )
                continue
        
        return {
            'total_pending': len(pending_orders),
            'eligible_for_reminder': len(eligible_orders),
            'reminder_after_hours': reminder_after_hours,
            'reminder_interval_hours': config.REMINDER_INTERVAL_HOURS,
            'orders': eligible_orders[:20],
        }
        
    except Exception as e:
        log_general_error(
            f"Error getting reminder status: {str(e)}",
            traceback=str(e)
        )
        return {
            'total_pending': 0,
            'eligible_for_reminder': 0,
            'reminder_after_hours': config.REMINDER_AFTER_HOURS,
            'reminder_interval_hours': config.REMINDER_INTERVAL_HOURS,
            'orders': [],
            'error': str(e)
        }


# ============================================================
# ارسال دستی یادآوری با messenger
# ============================================================

async def send_manual_reminder(order_id: int, user_id: int = None) -> bool:
    """
    ارسال دستی یادآوری برای یک سفارش خاص با messenger
    
    پارامترها:
        order_id: شناسه سفارش
        user_id: شناسه کاربر (اختیاری - اگر داده نشود از سفارش گرفته می‌شود)
    
    بازگشت: True در صورت موفقیت
    """
    try:
        from database import get_dynamic_order_by_id
        
        order = get_dynamic_order_by_id(order_id)
        if not order:
            log_general_error(
                f"Order {order_id} not found for manual reminder"
            )
            return False
        
        target_user_id = user_id or order.get('user_id')
        if not target_user_id:
            log_general_error(
                f"User ID not found for order {order_id}"
            )
            return False
        
        # ========== ارسال با messenger ==========
        success = await _send_reminder(order, target_user_id)
        
        if success:
            await _update_reminder_time(order_id)
            logger.info(f"✅ Manual reminder sent for order {order_id} via messenger")
        else:
            log_general_error(
                f"❌ Manual reminder failed for order {order_id}"
            )
        
        return success
        
    except Exception as e:
        log_critical_error(
            f"Error sending manual reminder for order {order_id}: {str(e)}",
            traceback=str(e)
        )
        return False


__all__ = [
    'run_reminder_task',
    'get_reminder_status',
    'send_manual_reminder',
    '_send_reminder',
    '_update_reminder_time',
    '_notify_owner',
]