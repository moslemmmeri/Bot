# services/notification_service.py
# سرویس مدیریت اعلان‌ها و پیام‌های سیستمی
# شامل: ارسال اعلان به کاربران، ادمین‌ها، پیام‌های گروهی و قالب‌های پیام
# اصلاح شده با استفاده از messenger برای ارسال همزمان (Batch Sending)

import asyncio
import traceback
from typing import Optional, List, Dict, Any, Callable, Awaitable
from datetime import datetime
from logger_config import logger
from core import send_message
from config import config
from utils.error_handler import log_general_error, log_database_error

# ========== ایمپورت messenger (فقط موارد موجود) ==========
from messenger import (
    Messenger,
    get_messenger,
    MessageBuilder,
)


class NotificationService:
    """
    سرویس مدیریت اعلان‌ها و پیام‌های سیستمی
    مسئول ارسال اعلان‌ها به کاربران و ادمین‌ها برای رویدادهای مختلف
    اصلاح شده با استفاده از messenger برای ارسال همزمان
    """
    
    def __init__(self, connection):
        """
        پارامترها:
            connection: اتصال به دیتابیس
        """
        self._connection = connection
        self._owner_id = config.OWNER_ID
        self._default_batch_size = 50  # تعداد پیام‌های همزمان
        self._messenger = get_messenger()
    
    # ============================================================
    # ارسال پیام به کاربران (با messenger)
    # ============================================================
    
    async def send_to_user(self, user_id: int, message: str, keyboard: Optional[Dict] = None) -> bool:
        """
        ارسال یک پیام به یک کاربر خاص (با messenger)
        
        پارامترها:
            user_id: شناسه کاربر
            message: متن پیام
            keyboard: کیبورد (اختیاری)
        
        بازگشت: True در صورت موفقیت
        """
        try:
            # استفاده از messenger برای ارسال تکی
            result = await self._messenger.send_messages([
                {'chat_id': user_id, 'text': message, 'keyboard': keyboard}
            ])
            
            # بررسی نتیجه
            if result and len(result) > 0:
                if isinstance(result[0], Exception):
                    log_general_error(
                        f"Error sending notification to user {user_id}: {result[0]}",
                        traceback=traceback.format_exc(),
                        user_id=user_id
                    )
                    return False
                return True
            
            return False
            
        except Exception as e:
            log_general_error(
                f"Error sending notification to user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    async def send_to_users(self, user_ids: List[int], message: str,
                           keyboard: Optional[Dict] = None,
                           batch_size: Optional[int] = None) -> Dict[str, Any]:
        """
        ارسال یک پیام به چندین کاربر با messenger (ارسال همزمان)
        
        پارامترها:
            user_ids: لیست شناسه‌های کاربران
            message: متن پیام
            keyboard: کیبورد (اختیاری)
            batch_size: تعداد پیام‌های همزمان (اختیاری)
        
        بازگشت: دیکشنری شامل آمار ارسال
        """
        if not user_ids:
            return {'total': 0, 'sent': 0, 'failed': 0, 'errors': []}
        
        batch_size = batch_size or self._default_batch_size
        
        # ========== استفاده از messenger برای ارسال همزمان ==========
        try:
            # ساخت لیست پیام‌ها
            messages = []
            for user_id in user_ids:
                messages.append({
                    'chat_id': user_id,
                    'text': message,
                    'keyboard': keyboard
                })
            
            # ارسال با messenger (با تقسیم به دسته‌های کوچک)
            all_results = []
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i+batch_size]
                results = await self._messenger.send_messages(batch)
                all_results.extend(results)
                
                # تأخیر بین دسته‌ها برای جلوگیری از محدودیت نرخ
                if i + batch_size < len(messages):
                    await asyncio.sleep(0.3)
            
            # تحلیل نتایج
            sent = 0
            failed = 0
            errors = []
            
            for i, result in enumerate(all_results):
                user_id = user_ids[i] if i < len(user_ids) else None
                if isinstance(result, Exception):
                    failed += 1
                    if user_id:
                        errors.append({'user_id': user_id, 'error': str(result)})
                elif result is not None:
                    sent += 1
                else:
                    failed += 1
                    if user_id:
                        errors.append({'user_id': user_id, 'error': 'No response'})
            
            logger.info(f"📨 Notification sent to {sent}/{len(user_ids)} users via messenger")
            
            return {
                'total': len(user_ids),
                'sent': sent,
                'failed': failed,
                'errors': errors
            }
            
        except Exception as e:
            log_general_error(
                f"Error sending to users via messenger: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total': len(user_ids),
                'sent': 0,
                'failed': len(user_ids),
                'errors': [{'user_id': uid, 'error': str(e)} for uid in user_ids]
            }
    
    # ============================================================
    # ارسال به ادمین‌ها
    # ============================================================
    
    async def send_to_admin(self, admin_id: int, message: str, keyboard: Optional[Dict] = None) -> bool:
        """ارسال پیام به یک ادمین خاص (با messenger)"""
        return await self.send_to_user(admin_id, message, keyboard)
    
    async def send_to_owner(self, message: str, keyboard: Optional[Dict] = None) -> bool:
        """ارسال پیام به OWNER_ID (با messenger)"""
        return await self.send_to_user(self._owner_id, message, keyboard)
    
    async def send_to_all_admins(self, message: str, keyboard: Optional[Dict] = None,
                                include_owner: bool = True) -> Dict[str, Any]:
        """
        ارسال پیام به همه ادمین‌ها با messenger
        
        پارامترها:
            message: متن پیام
            keyboard: کیبورد (اختیاری)
            include_owner: آیا OWNER نیز شامل شود
        
        بازگشت: دیکشنری شامل آمار ارسال
        """
        from services.admin_service import AdminService
        admin_service = AdminService(self._connection)
        
        admins = admin_service.get_active_admins()
        admin_ids = [a['user_id'] for a in admins]
        
        if not include_owner and self._owner_id in admin_ids:
            admin_ids.remove(self._owner_id)
        
        if not admin_ids:
            return {'total': 0, 'sent': 0, 'failed': 0, 'errors': []}
        
        return await self.send_to_users(admin_ids, message, keyboard)
    
    # ============================================================
    # ارسال پیام‌های از پیش تعیین‌شده (Templates)
    # ============================================================
    
    async def notify_order_created(self, user_id: int, order_id: int,
                                   service_name: str, amount: int) -> bool:
        """ارسال اعلان ثبت سفارش به کاربر (با messenger)"""
        message = (
            f"✅ **سفارش شما ثبت شد**\n\n"
            f"🔘 سرویس: {service_name}\n"
            f"🆔 شناسه سفارش: {order_id}\n"
            f"💰 مبلغ: {amount:,} ریال\n\n"
            f"🙏 از اعتماد شما سپاسگزاریم.\n"
            f"به زودی با شما تماس می‌گیریم."
        )
        return await self.send_to_user(user_id, message)
    
    async def notify_order_paid(self, user_id: int, order_id: int,
                                tracking_code: str, amount: int) -> bool:
        """ارسال اعلان پرداخت موفق به کاربر (با messenger)"""
        message = (
            f"✅ **پرداخت شما با موفقیت انجام شد**\n\n"
            f"🆔 شناسه سفارش: {order_id}\n"
            f"🎫 کد رهگیری: {tracking_code}\n"
            f"💰 مبلغ: {amount:,} ریال\n\n"
            f"سفارش شما در صف پردازش قرار گرفت.\n"
            f"به زودی با شما تماس می‌گیریم."
        )
        return await self.send_to_user(user_id, message)
    
    async def notify_order_status_changed(self, user_id: int, order_id: int,
                                         old_status: str, new_status: str) -> bool:
        """ارسال اعلان تغییر وضعیت سفارش به کاربر (با messenger)"""
        from .common import get_order_status_persian
        
        status_map = {
            'pending': '⏳ در انتظار پرداخت',
            'paid': '✅ پرداخت شده',
            'completed': '✅ تکمیل شده',
            'cancelled': '❌ لغو شده',
            'failed': '❌ ناموفق',
            'refunded': '🔄 بازگشت وجه'
        }
        
        old_label = status_map.get(old_status, old_status)
        new_label = status_map.get(new_status, new_status)
        
        message = (
            f"🔄 **تغییر وضعیت سفارش**\n\n"
            f"🆔 شناسه سفارش: {order_id}\n"
            f"📌 وضعیت جدید: {new_label}\n"
            f"📌 وضعیت قبلی: {old_label}\n\n"
            f"برای مشاهده جزئیات، به بخش پروفایل مراجعه کنید."
        )
        return await self.send_to_user(user_id, message)
    
    async def notify_order_cancelled(self, user_id: int, order_id: int,
                                    service_name: str) -> bool:
        """ارسال اعلان لغو سفارش به کاربر (با messenger)"""
        message = (
            f"❌ **سفارش شما لغو شد**\n\n"
            f"🔘 سرویس: {service_name}\n"
            f"🆔 شناسه سفارش: {order_id}\n\n"
            f"در صورت نیاز به راهنمایی، با پشتیبانی تماس بگیرید."
        )
        return await self.send_to_user(user_id, message)
    
    async def notify_admin_new_order(self, order_id: int, user_id: int,
                                    service_name: str, amount: int,
                                    fullname: str) -> bool:
        """
        ارسال اعلان سفارش جدید به ادمین‌ها (با messenger)
        """
        message = (
            f"🆕 **سفارش جدید ثبت شد**\n\n"
            f"👤 کاربر: {fullname} (شناسه: {user_id})\n"
            f"🔘 سرویس: {service_name}\n"
            f"🆔 شناسه سفارش: {order_id}\n"
            f"💰 مبلغ: {amount:,} ریال\n\n"
            f"برای مشاهده جزئیات، به بخش سفارشات مراجعه کنید."
        )
        return await self.send_to_all_admins(message)
    
    async def notify_admin_error(self, error_type: str, error_message: str,
                                user_id: Optional[int] = None,
                                chat_id: Optional[int] = None) -> bool:
        """ارسال اعلان خطا به OWNER (با messenger)"""
        message = (
            f"🚨 **اعلان خطا**\n\n"
            f"🔴 نوع: {error_type}\n"
            f"📝 پیام: {error_message}\n"
        )
        if user_id:
            message += f"👤 کاربر: {user_id}\n"
        if chat_id:
            message += f"💬 چت: {chat_id}\n"
        message += f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_to_owner(message)
    
    async def notify_admin_backup_created(self, backup_name: str, size_kb: int,
                                         elapsed: float) -> bool:
        """ارسال اعلان ایجاد پشتیبان به OWNER (با messenger)"""
        message = (
            f"✅ **پشتیبان‌گیری خودکار انجام شد**\n\n"
            f"📁 فایل: {backup_name}\n"
            f"📊 حجم: {size_kb} KB\n"
            f"⏱️  زمان اجرا: {elapsed:.2f} ثانیه\n"
            f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return await self.send_to_owner(message)
    
    async def notify_admin_cleanup_completed(self, results: Dict[str, int],
                                            elapsed: float) -> bool:
        """ارسال اعلان پاکسازی خودکار به OWNER (با messenger)"""
        message = (
            f"🧹 **پاکسازی خودکار انجام شد**\n\n"
            f"🗑️ خطاهای قدیمی: {results.get('deleted_errors', 0)} مورد\n"
            f"🗑️ لاگ‌های سفارشات: {results.get('deleted_logs', 0)} مورد\n"
            f"🗑️ نمودارهای قدیمی: {results.get('deleted_charts', 0)} مورد\n"
            f"🗑️ فایل‌های Excel قدیمی: {results.get('deleted_excel', 0)} مورد\n"
            f"⏱️  زمان اجرا: {elapsed:.2f} ثانیه\n"
            f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return await self.send_to_owner(message)
    
    async def notify_admin_reminder_summary(self, results: Dict[str, Any],
                                           elapsed: float) -> bool:
        """ارسال خلاصه یادآوری‌ها به OWNER (با messenger)"""
        message = (
            f"⏰ **گزارش یادآوری سفارشات**\n\n"
            f"📦 کل سفارشات در انتظار: {results.get('total', 0)}\n"
            f"✅ یادآوری ارسال‌شده: {results.get('sent', 0)}\n"
            f"❌ ناموفق: {results.get('failed', 0)}\n"
            f"⏱️  زمان اجرا: {elapsed:.2f} ثانیه\n"
            f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return await self.send_to_owner(message)
    
    # ============================================================
    # ارسال پیام‌های گروهی (Broadcast) با messenger
    # ============================================================
    
    async def broadcast_to_active_users(self, message: str,
                                       days: int = 1,
                                       keyboard: Optional[Dict] = None) -> Dict[str, Any]:
        """
        ارسال پیام به کاربران فعال در تعداد روزهای اخیر با messenger
        
        پارامترها:
            message: متن پیام
            days: تعداد روزهای اخیر (پیش‌فرض: ۱ روز)
            keyboard: کیبورد (اختیاری)
        
        بازگشت: دیکشنری شامل آمار ارسال
        """
        from services.user_service import UserService
        user_service = UserService(self._connection)
        
        users = user_service.get_active_users(days)
        user_ids = [u['user_id'] for u in users if not u.get('is_blocked', 0)]
        
        if not user_ids:
            return {'total': 0, 'sent': 0, 'failed': 0, 'errors': []}
        
        return await self.send_to_users(user_ids, message, keyboard)
    
    async def broadcast_to_all_users(self, message: str,
                                    keyboard: Optional[Dict] = None,
                                    exclude_blocked: bool = True) -> Dict[str, Any]:
        """
        ارسال پیام به همه کاربران با messenger
        
        پارامترها:
            message: متن پیام
            keyboard: کیبورد (اختیاری)
            exclude_blocked: آیا کاربران مسدود شده حذف شوند
        
        بازگشت: دیکشنری شامل آمار ارسال
        """
        from services.user_service import UserService
        user_service = UserService(self._connection)
        
        users = user_service.get_all_users(limit=10000)
        user_ids = [u['user_id'] for u in users]
        
        if exclude_blocked:
            user_ids = [uid for uid in user_ids if not user_service.is_blocked(uid)]
        
        if not user_ids:
            return {'total': 0, 'sent': 0, 'failed': 0, 'errors': []}
        
        return await self.send_to_users(user_ids, message, keyboard)
    
    async def broadcast_to_users_with_orders(self, message: str,
                                            keyboard: Optional[Dict] = None) -> Dict[str, Any]:
        """
        ارسال پیام به کاربرانی که حداقل یک سفارش دارند با messenger
        
        پارامترها:
            message: متن پیام
            keyboard: کیبورد (اختیاری)
        
        بازگشت: دیکشنری شامل آمار ارسال
        """
        from database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT user_id FROM dynamic_orders
            """)
            rows = cursor.fetchall()
            user_ids = [row['user_id'] for row in rows]
        
        if not user_ids:
            return {'total': 0, 'sent': 0, 'failed': 0, 'errors': []}
        
        return await self.send_to_users(user_ids, message, keyboard)
    
    # ============================================================
    # ارسال با MessageBuilder (روش پیشرفته‌تر)
    # ============================================================
    
    async def send_builder_messages(self, builder: MessageBuilder) -> List[Any]:
        """
        ارسال پیام‌های ساخته‌شده با MessageBuilder
        
        پارامترها:
            builder: آبجکت MessageBuilder
        
        بازگشت: لیست نتایج ارسال
        """
        try:
            return await builder.send()
        except Exception as e:
            log_general_error(
                f"Error sending builder messages: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def create_builder(self) -> MessageBuilder:
        """
        ایجاد یک MessageBuilder جدید برای ساخت پیام‌های دسته‌ای
        
        بازگشت: آبجکت MessageBuilder
        """
        return MessageBuilder()
    
    # ============================================================
    # مدیریت قالب‌های پیام (Message Templates)
    # ============================================================
    
    _TEMPLATES = {
        'order_created': {
            'user': '✅ **سفارش شما ثبت شد**\n\n🔘 سرویس: {service_name}\n🆔 شناسه سفارش: {order_id}\n💰 مبلغ: {amount:,} ریال\n\n🙏 از اعتماد شما سپاسگزاریم.\nبه زودی با شما تماس می‌گیریم.',
            'admin': '🆕 **سفارش جدید ثبت شد**\n\n👤 کاربر: {fullname} (شناسه: {user_id})\n🔘 سرویس: {service_name}\n🆔 شناسه سفارش: {order_id}\n💰 مبلغ: {amount:,} ریال'
        },
        'order_paid': {
            'user': '✅ **پرداخت شما با موفقیت انجام شد**\n\n🆔 شناسه سفارش: {order_id}\n🎫 کد رهگیری: {tracking_code}\n💰 مبلغ: {amount:,} ریال\n\nسفارش شما در صف پردازش قرار گرفت.'
        },
        'order_status_changed': {
            'user': '🔄 **تغییر وضعیت سفارش**\n\n🆔 شناسه سفارش: {order_id}\n📌 وضعیت جدید: {new_status}\n📌 وضعیت قبلی: {old_status}'
        },
        'order_cancelled': {
            'user': '❌ **سفارش شما لغو شد**\n\n🔘 سرویس: {service_name}\n🆔 شناسه سفارش: {order_id}'
        },
        'reminder': {
            'user': '⏰ **یادآوری سفارش ناتمام**\n\nسلام {first_name} عزیز،\nشما یک سفارش ثبت کرده‌اید که هنوز پرداخت نشده است.\n\n🆔 شناسه سفارش: {order_id}\n💰 مبلغ: {amount:,} ریال\n\nلطفاً هرچه سریع‌تر اقدام به پرداخت کنید.'
        },
        'welcome': {
            'user': '👋 **به ربات خوش آمدید**\n\n{first_name} عزیز،\nاز اینکه به ما پیوستید خوشحالیم.\n\n🌟 برای شروع، یکی از گزینه‌های منو را انتخاب کنید.'
        }
    }
    
    @classmethod
    def get_template(cls, template_name: str, target: str = 'user') -> Optional[str]:
        """دریافت قالب پیام بر اساس نام و مخاطب"""
        template_data = cls._TEMPLATES.get(template_name, {})
        return template_data.get(target)
    
    @classmethod
    def render_template(cls, template_name: str, target: str = 'user',
                       **kwargs) -> Optional[str]:
        """رندر کردن قالب پیام با جایگزینی متغیرها"""
        template = cls.get_template(template_name, target)
        if not template:
            return None
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            log_general_error(
                f"Missing template variable {e} for {template_name}",
                traceback=traceback.format_exc()
            )
            return template
    
    @classmethod
    def add_template(cls, template_name: str, target: str, template_text: str) -> None:
        """افزودن یا به‌روزرسانی یک قالب پیام"""
        if template_name not in cls._TEMPLATES:
            cls._TEMPLATES[template_name] = {}
        cls._TEMPLATES[template_name][target] = template_text
        logger.info(f"✅ Template '{template_name}' for '{target}' updated")
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    async def send_notification(self, user_id: int, template_name: str,
                               target: str = 'user', **kwargs) -> bool:
        """ارسال اعلان با استفاده از قالب (با messenger)"""
        message = self.render_template(template_name, target, **kwargs)
        if not message:
            logger.error(f"Template '{template_name}' for '{target}' not found")
            return False
        
        return await self.send_to_user(user_id, message)
    
    async def send_notification_to_admin(self, admin_id: int, template_name: str,
                                        target: str = 'admin', **kwargs) -> bool:
        """ارسال اعلان به ادمین با استفاده از قالب (با messenger)"""
        return await self.send_notification(admin_id, template_name, target, **kwargs)
    
    def get_notification_stats(self) -> Dict[str, int]:
        """دریافت آمار قالب‌های پیام"""
        return {
            'total_templates': len(self._TEMPLATES),
            'user_templates': sum(1 for t in self._TEMPLATES.values() if 'user' in t),
            'admin_templates': sum(1 for t in self._TEMPLATES.values() if 'admin' in t),
        }


__all__ = [
    'NotificationService',
]