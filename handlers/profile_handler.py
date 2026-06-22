# handlers/profile_handler.py
# پردازش درخواست‌های پروفایل کاربری و تاریخچه سفارشات

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, Dict, Any
from logger_config import logger
from .base_handler import BaseHandler
from core import user_states


class ProfileHandler(BaseHandler):
    """
    هندلر پروفایل کاربری و تاریخچه سفارشات
    پردازش: نمایش پروفایل، تاریخچه سفارشات، جزئیات سفارش، لغو سفارش، آمار کاربر
    """
    
    # ============================================================
    # متد اصلی پردازش کالبک
    # ============================================================
    
    async def handle(self, update: Dict) -> bool:
        """
        پردازش کالبک‌های مربوط به پروفایل کاربری
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر کالبک پردازش شد
        """
        cb = update.get("callback_query")
        if not cb:
            return False
        
        data = cb.get("data")
        user_id = cb.get("from", {}).get("id")
        chat_id = cb.get("message", {}).get("chat", {}).get("id")
        
        if not user_id or not chat_id or not data:
            return False
        
        # ثبت فعالیت کاربر
        from_user = cb.get("from", {})
        self.upsert_user(
            user_id,
            from_user.get("username"),
            from_user.get("first_name"),
            from_user.get("last_name")
        )
        
        self.log_debug(f"Profile callback received: {data} from user {user_id}")
        
        # ========== کالبک‌های پروفایل ==========
        
        # نمایش پروفایل اصلی
        if data == "profile_main":
            return await self.show_profile(chat_id, user_id)
        
        # نمایش سفارشات
        if data.startswith("profile_orders_"):
            parts = data.split("_")
            if len(parts) >= 3:
                try:
                    target_user_id = int(parts[2])
                    if target_user_id == user_id:
                        return await self.show_orders(chat_id, user_id, 0)
                    else:
                        await self.send_message(chat_id, "⛔ دسترسی غیرمجاز.")
                        return True
                except ValueError:
                    await self.send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
                    return True
        
        # صفحه‌بندی سفارشات
        if data.startswith("profile_orders_page_"):
            try:
                page = int(data.split("_")[-1])
                return await self.show_orders(chat_id, user_id, page)
            except ValueError:
                await self.send_message(chat_id, "❌ شماره صفحه نامعتبر.")
                return True
        
        # بازگشت به لیست سفارشات
        if data == "profile_orders_back":
            return await self.show_orders(chat_id, user_id, 0)
        
        # نمایش جزئیات سفارش
        if data.startswith("profile_order_detail_"):
            try:
                order_id = int(data.split("_")[-1])
                return await self.show_order_detail(chat_id, user_id, order_id)
            except ValueError:
                await self.send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
                return True
        
        # لغو سفارش
        if data.startswith("profile_order_cancel_"):
            try:
                order_id = int(data.split("_")[-1])
                return await self.cancel_order(chat_id, user_id, order_id)
            except ValueError:
                await self.send_message(chat_id, "❌ شناسه سفارش نامعتبر.")
                return True
        
        # نمایش آمار
        if data.startswith("profile_stats_"):
            parts = data.split("_")
            if len(parts) >= 3:
                try:
                    target_user_id = int(parts[2])
                    if target_user_id == user_id:
                        return await self.show_stats(chat_id, user_id)
                    else:
                        await self.send_message(chat_id, "⛔ دسترسی غیرمجاز.")
                        return True
                except ValueError:
                    await self.send_message(chat_id, "❌ شناسه کاربر نامعتبر.")
                    return True
        
        return False
    
    # ============================================================
    # نمایش پروفایل
    # ============================================================
    
    async def show_profile(self, chat_id: int, user_id: int) -> bool:
        """
        نمایش پروفایل کاربری
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True
        """
        try:
            from profile import show_profile as show_profile_func
            return await show_profile_func(chat_id, user_id)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'profile',
                f"Error showing profile: {e}",
                traceback=traceback.format_exc(),
                user_id=user_id,
                chat_id=chat_id
            )
            await self.send_message(chat_id, "❌ خطا در نمایش پروفایل.")
            return True
    
    # ============================================================
    # نمایش سفارشات
    # ============================================================
    
    async def show_orders(self, chat_id: int, user_id: int, page: int = 0) -> bool:
        """
        نمایش لیست سفارشات کاربر
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
            page: شماره صفحه
        
        بازگشت: True
        """
        try:
            from profile import show_profile_orders
            return await show_profile_orders(chat_id, user_id, page)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'profile',
                f"Error showing orders: {e}",
                traceback=traceback.format_exc(),
                user_id=user_id,
                chat_id=chat_id
            )
            await self.send_message(chat_id, "❌ خطا در نمایش تاریخچه سفارشات.")
            return True
    
    # ============================================================
    # نمایش جزئیات سفارش
    # ============================================================
    
    async def show_order_detail(self, chat_id: int, user_id: int, order_id: int) -> bool:
        """
        نمایش جزئیات کامل یک سفارش
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
            order_id: شناسه سفارش
        
        بازگشت: True
        """
        try:
            from profile import show_profile_order_detail
            return await show_profile_order_detail(chat_id, user_id, order_id)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'profile',
                f"Error showing order detail: {e}",
                traceback=traceback.format_exc(),
                user_id=user_id,
                chat_id=chat_id
            )
            await self.send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
            return True
    
    # ============================================================
    # لغو سفارش
    # ============================================================
    
    async def cancel_order(self, chat_id: int, user_id: int, order_id: int) -> bool:
        """
        لغو سفارش در انتظار پرداخت
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
            order_id: شناسه سفارش
        
        بازگشت: True
        """
        try:
            from profile import cancel_profile_order
            return await cancel_profile_order(chat_id, user_id, order_id)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'profile',
                f"Error cancelling order: {e}",
                traceback=traceback.format_exc(),
                user_id=user_id,
                chat_id=chat_id
            )
            await self.send_message(chat_id, "❌ خطا در لغو سفارش.")
            return True
    
    # ============================================================
    # نمایش آمار کاربر
    # ============================================================
    
    async def show_stats(self, chat_id: int, user_id: int) -> bool:
        """
        نمایش آمار کاربر
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True
        """
        try:
            from profile import show_profile_stats
            return await show_profile_stats(chat_id, user_id)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'profile',
                f"Error showing stats: {e}",
                traceback=traceback.format_exc(),
                user_id=user_id,
                chat_id=chat_id
            )
            await self.send_message(chat_id, "❌ خطا در نمایش آمار.")
            return True
    
    # ============================================================
    # پردازش دستور /profile
    # ============================================================
    
    async def handle_command(self, update: Dict) -> bool:
        """
        پردازش دستور /profile
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True
        """
        msg = update.get("message")
        if not msg:
            return False
        
        chat_id = msg.get("chat", {}).get("id")
        user_id = msg.get("from", {}).get("id")
        
        if not user_id or not chat_id:
            return False
        
        # ثبت کاربر
        from_user = msg.get("from", {})
        self.upsert_user(
            user_id,
            from_user.get("username"),
            from_user.get("first_name"),
            from_user.get("last_name")
        )
        
        return await self.show_profile(chat_id, user_id)
    
    # ============================================================
    # پردازش پیام‌های پروفایل (برای آینده)
    # ============================================================
    
    async def handle_message(self, update: Dict) -> bool:
        """
        پردازش پیام‌های مربوط به پروفایل (در صورت نیاز)
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر پیام پردازش شد
        """
        # فعلاً پیام‌های پروفایل پردازش نمی‌شوند
        # می‌توان در آینده برای تکمیل اطلاعات پروفایل از این استفاده کرد
        return False
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    def is_profile_callback(self, data: str) -> bool:
        """بررسی اینکه آیا کالبک مربوط به پروفایل است"""
        return data.startswith("profile_")
    
    def is_orders_callback(self, data: str) -> bool:
        """بررسی اینکه آیا کالبک مربوط به سفارشات است"""
        return data.startswith("profile_orders_") or data.startswith("profile_order_")
    
    def get_order_id_from_callback(self, data: str) -> Optional[int]:
        """استخراج شناسه سفارش از کالبک"""
        try:
            parts = data.split("_")
            if len(parts) >= 4:
                return int(parts[-1])
            return None
        except:
            return None
    
    def get_user_id_from_callback(self, data: str) -> Optional[int]:
        """استخراج شناسه کاربر از کالبک"""
        try:
            parts = data.split("_")
            if len(parts) >= 3:
                return int(parts[2])
            return None
        except:
            return None


__all__ = [
    'ProfileHandler',
]