# handlers/help_handler.py
# پردازش درخواست‌های راهنمای کاربر

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, Dict, Any
from logger_config import logger
from .base_handler import BaseHandler
from help import (
    show_help,
    show_help_section,
    handle_help_callback,
    handle_help_command,
    help_main_keyboard,
    help_back_keyboard,
)
from utils.error_handler import log_general_error  # ✅ اضافه شد


class HelpHandler(BaseHandler):
    """
    هندلر راهنمای کاربر
    پردازش: نمایش راهنما، بخش‌های مختلف راهنما، دستور /help
    """
    
    # ============================================================
    # متد اصلی پردازش کالبک
    # ============================================================
    
    async def handle(self, update: Dict) -> bool:
        """
        پردازش کالبک‌های مربوط به راهنما
        
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
        
        self.log_debug(f"Help callback received: {data} from user {user_id}")
        
        # ========== کالبک‌های راهنما ==========
        
        # نمایش بخش‌های راهنما
        if data.startswith("help_"):
            section = data.split("_", 1)[1]  # help_main, help_commands, ...
            return await self.show_help_section(chat_id, section)
        
        return False
    
    # ============================================================
    # نمایش راهنما
    # ============================================================
    
    async def show_help(self, chat_id: int, section: str = "main") -> bool:
        """
        نمایش راهنمای کاربر
        
        پارامترها:
            chat_id: شناسه چت
            section: بخش راهنما (main, commands, payment, support, faq)
        
        بازگشت: True در صورت موفقیت
        """
        try:
            return await show_help(chat_id, section)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'help',
                f"Error showing help: {e}",
                traceback=traceback.format_exc(),
                chat_id=chat_id
            )
            await self.send_message(chat_id, "❌ خطا در نمایش راهنما.")
            return True
    
    async def show_help_section(self, chat_id: int, section: str) -> bool:
        """
        نمایش یک بخش خاص از راهنما
        
        پارامترها:
            chat_id: شناسه چت
            section: نام بخش (main, commands, payment, support, faq)
        
        بازگشت: True در صورت موفقیت
        """
        try:
            return await show_help_section(chat_id, section)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'help',
                f"Error showing help section: {e}",
                traceback=traceback.format_exc(),
                chat_id=chat_id
            )
            await self.send_message(chat_id, "❌ خطا در نمایش بخش راهنما.")
            return True
    
    async def show_help_main(self, chat_id: int) -> bool:
        """
        نمایش منوی اصلی راهنما
        
        پارامترها:
            chat_id: شناسه چت
        
        بازگشت: True در صورت موفقیت
        """
        return await self.show_help(chat_id, "main")
    
    # ============================================================
    # پردازش دستور /help
    # ============================================================
    
    async def handle_command(self, update: Dict) -> bool:
        """
        پردازش دستور /help
        
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
        
        return await self.show_help(chat_id, "main")
    
    # ============================================================
    # پردازش پیام‌های راهنما (برای آینده)
    # ============================================================
    
    async def handle_message(self, update: Dict) -> bool:
        """
        پردازش پیام‌های مربوط به راهنما (در صورت نیاز)
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر پیام پردازش شد
        """
        # فعلاً پیام‌های راهنما پردازش نمی‌شوند
        return False
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    def is_help_callback(self, data: str) -> bool:
        """بررسی اینکه آیا کالبک مربوط به راهنما است"""
        return data.startswith("help_")
    
    def is_help_command(self, text: str) -> bool:
        """بررسی اینکه آیا پیام دستور راهنما است"""
        return text == "/help"
    
    def get_section_from_callback(self, data: str) -> Optional[str]:
        """استخراج نام بخش از کالبک"""
        if data.startswith("help_"):
            return data.split("_", 1)[1]
        return None


__all__ = [
    'HelpHandler',
]