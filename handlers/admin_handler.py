# handlers/admin_handler.py
# پردازش درخواست‌های پنل مدیریت

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, Dict, Any
from logger_config import logger
from .base_handler import BaseHandler
from core import user_states
from utils.error_handler import log_general_error  # ✅ اضافه شد


class AdminHandler(BaseHandler):
    """
    هندلر پنل مدیریت
    پردازش: کالبک‌های مدیریت، پیام‌های مدیریت، بررسی دسترسی ادمین
    """
    
    # ============================================================
    # متد اصلی پردازش کالبک
    # ============================================================
    
    async def handle(self, update: Dict) -> bool:
        """
        پردازش کالبک‌های پنل مدیریت
        
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
        
        # بررسی دسترسی ادمین
        if not self.can_access_admin(user_id):
            await self.send_message(chat_id, "⛔ شما دسترسی به پنل مدیریت ندارید.")
            self.log_warning(f"Unauthorized admin access attempt by user {user_id}")
            return True
        
        # پردازش کالبک توسط مسیریاب پنل مدیریت
        try:
            from admin_panel import handle_admin_callback
            return await handle_admin_callback(update)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'callback',
                f"Error in admin callback: {e}",
                traceback=traceback.format_exc(),
                user_id=user_id,
                chat_id=chat_id
            )
            await self.send_message(chat_id, "❌ خطا در پردازش درخواست مدیریت.")
            return True
    
    # ============================================================
    # پردازش پیام‌های مدیریت
    # ============================================================
    
    async def handle_message(self, update: Dict) -> bool:
        """
        پردازش پیام‌های متنی در حالت مدیریت
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر پیام مدیریت بود
        """
        msg = update.get("message")
        if not msg:
            return False
        
        chat_id = msg.get("chat", {}).get("id")
        user_id = msg.get("from", {}).get("id")
        text = msg.get("text", "").strip()
        
        if not user_id or not chat_id:
            return False
        
        # ثبت فعالیت کاربر
        from_user = msg.get("from", {})
        self.upsert_user(
            user_id,
            from_user.get("username"),
            from_user.get("first_name"),
            from_user.get("last_name")
        )
        
        # بررسی دسترسی ادمین
        if not self.can_access_admin(user_id):
            return False
        
        # بررسی وضعیت کاربر - آیا در حالت مدیریت است؟
        state_info = self.get_user_state(user_id)
        current_state = state_info.get("state", "main")
        
        # اگر کاربر در حالت مدیریت نیست، پیام را پردازش نکن
        if not current_state.startswith("admin_"):
            return False
        
        # پردازش پیام توسط ماژول مدیریت
        try:
            from admin_panel import handle_admin_message
            return await handle_admin_message(update)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'general',
                f"Error in admin message: {e}",
                traceback=traceback.format_exc(),
                user_id=user_id,
                chat_id=chat_id
            )
            await self.send_message(chat_id, "❌ خطا در پردازش پیام مدیریت.")
            return True
    
    # ============================================================
    # پردازش کالبک‌های مدیریت (برای هندلرهای دیگر)
    # ============================================================
    
    async def handle_callback(self, update: Dict) -> bool:
        """
        پردازش کالبک‌های مدیریت (همان متد handle)
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر کالبک مدیریت بود
        """
        return await self.handle(update)
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    def is_admin_callback(self, data: str) -> bool:
        """بررسی اینکه آیا کالبک مربوط به پنل مدیریت است"""
        return data == "admin_panel" or data.startswith("admin_")
    
    def is_admin_state(self, user_id: int) -> bool:
        """بررسی اینکه آیا کاربر در حالت مدیریت است"""
        state = self.get_user_state(user_id)
        return state.get("state", "").startswith("admin_")
    
    # ============================================================
    # ورود مستقیم به پنل مدیریت (برای دستور /admin)
    # ============================================================
    
    async def show_admin_panel(self, chat_id: int, user_id: int) -> bool:
        """
        نمایش پنل مدیریت برای ادمین
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True
        """
        # بررسی دسترسی
        if not self.can_access_admin(user_id):
            await self.send_message(chat_id, "⛔ شما دسترسی به پنل مدیریت ندارید.")
            return True
        
        # پاک کردن وضعیت قبلی
        self.clear_user_state(user_id)
        
        # نمایش پنل مدیریت
        from keyboards import admin_main_keyboard
        from core import get_admin_title
        
        admin_title = get_admin_title()
        keyboard = admin_main_keyboard()
        
        await self.send_message(chat_id, admin_title, keyboard)
        self.log_info(f"Admin panel shown to user {user_id}")
        return True
    
    # ============================================================
    # بررسی دسترسی
    # ============================================================
    
    async def check_and_redirect(self, chat_id: int, user_id: int) -> bool:
        """
        بررسی دسترسی ادمین و هدایت به پنل مدیریت در صورت مجاز بودن
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر ادمین است
        """
        if self.can_access_admin(user_id):
            await self.show_admin_panel(chat_id, user_id)
            return True
        
        await self.send_message(chat_id, "⛔ شما دسترسی به پنل مدیریت ندارید.")
        return False


__all__ = [
    'AdminHandler',
]