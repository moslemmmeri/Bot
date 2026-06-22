# handlers/message_handler.py
# پردازش پیام‌های متنی و دستورات کاربران

import traceback
from typing import Optional, Dict, Any
from logger_config import logger
from core import user_states
from .base_handler import BaseHandler
from utils.error_handler import log_general_error

# ========== ایمپورت‌های جدید از texts.py و core.py ==========
from texts import (
    get_random_welcome,
    get_random_error,
    get_random_success,
    get_random_goodbye,
    get_random_waiting,
    get_random_help,
    get_random_thank_you,
    get_time_greeting,
    get_season_greeting,
)
from core import get_welcome_text_with_time, get_waiting_text, get_goodbye_text, get_help_text


class MessageHandler(BaseHandler):
    """
    هندلر پیام‌های متنی و دستورات کاربران
    پردازش: /start, /cancel, پیام‌های معمولی و مدیریت وضعیت‌های مختلف
    """
    
    async def handle(self, update: Dict) -> bool:
        """
        پردازش پیام‌های متنی
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر پیام پردازش شد
        """
        try:
            msg = update.get("message")
            if not msg:
                return False
            
            chat_id = msg.get("chat", {}).get("id")
            user_id = msg.get("from", {}).get("id")
            text = msg.get("text", "").strip()
            
            if not user_id or not chat_id:
                return False
            
            # ثبت اطلاعات کاربر
            from_user = msg.get("from", {})
            self.upsert_user(
                user_id,
                from_user.get("username"),
                from_user.get("first_name"),
                from_user.get("last_name")
            )
            
            # ========== دستور /start ==========
            if text == "/start":
                return await self.handle_start(update)
            
            # ========== دستور /help ==========
            if text == "/help":
                from .help_handler import HelpHandler
                help_handler = HelpHandler(self._connection, self._services)
                return await help_handler.handle_command(update)
            
            # ========== دستور /profile ==========
            if text == "/profile":
                from .profile_handler import ProfileHandler
                profile_handler = ProfileHandler(self._connection, self._services)
                return await profile_handler.handle_command(update)
            
            # ========== دستور /cancel ==========
            if text == "/cancel":
                return await self.handle_cancel(update)
            
            # ========== پردازش پیام در وضعیت‌های مختلف ==========
            # بررسی وضعیت کاربر
            state_info = self.get_user_state(user_id)
            current_state = state_info.get("state", "main")
            
            # اگر کاربر در وضعیت مدیریت است
            if current_state.startswith("admin_"):
                from .admin_handler import AdminHandler
                admin_handler = AdminHandler(self._connection, self._services)
                return await admin_handler.handle_message(update)
            
            # اگر کاربر در وضعیت فرم داینامیک است
            if current_state in ["dynamic_awaiting_answer", "dynamic_awaiting_option", "dynamic_awaiting_payment"]:
                from .dynamic_handler import DynamicHandler
                dynamic_handler = DynamicHandler(self._connection, self._services)
                return await dynamic_handler.handle_message(update)
            
            # ========== پیام‌های معمولی ==========
            # اگر کاربر در منوی اصلی است
            if current_state == "main":
                keyboard = self.get_main_menu_with_admin(user_id)
                random_message = get_random_help() + "\n\n🌟 لطفاً از دکمه‌های منو استفاده کنید."
                await self.send_message(chat_id, random_message, keyboard)
                return True
            
            # اگر کاربر در وضعیت نامشخص است
            error_msg = get_random_error() + "\n\n🔄 لطفاً طبق راهنمایی ربات پیش بروید."
            await self.send_message(
                chat_id,
                error_msg,
                self.get_main_menu_with_admin(user_id)
            )
            self.clear_user_state(user_id)
            return True
            
        except Exception as e:
            self.log_error(
                'general',
                f"Error in MessageHandler.handle: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id if 'user_id' in locals() else None,
                chat_id=chat_id if 'chat_id' in locals() else None,
                data={'text': text} if 'text' in locals() else None
            )
            if 'chat_id' in locals() and 'user_id' in locals():
                from core import send_message
                await send_message(chat_id, get_random_error())
            return True
    
    # ============================================================
    # پردازش دستورات خاص
    # ============================================================
    
    async def handle_start(self, update: Dict) -> bool:
        """
        پردازش دستور /start
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True
        """
        try:
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
            
            # پاک کردن وضعیت قبلی
            self.clear_user_state(user_id)
            
            # نمایش منوی اصلی
            keyboard = self.get_main_menu_with_admin(user_id)
            
            # ========== استفاده از پیام خوش‌آمدگویی پویا ==========
            welcome_text = get_welcome_text_with_time()
            
            await self.send_message(chat_id, welcome_text, keyboard)
            self.log_info(f"User {user_id} started the bot")
            return True
        except Exception as e:
            self.log_error(
                'general',
                f"Error in handle_start: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id if 'user_id' in locals() else None,
                chat_id=chat_id if 'chat_id' in locals() else None
            )
            return True
    
    async def handle_cancel(self, update: Dict) -> bool:
        """
        پردازش دستور /cancel - لغو عملیات جاری
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True
        """
        try:
            msg = update.get("message")
            if not msg:
                return False
            
            chat_id = msg.get("chat", {}).get("id")
            user_id = msg.get("from", {}).get("id")
            
            if not user_id or not chat_id:
                return False
            
            # پاک کردن وضعیت کاربر
            self.clear_user_state(user_id)
            
            # نمایش منوی اصلی
            keyboard = self.get_main_menu_with_admin(user_id)
            
            # ========== استفاده از پیام‌های پویا ==========
            goodbye = get_random_goodbye()
            welcome = get_random_welcome()
            
            await self.send_message(
                chat_id,
                f"✅ عملیات جاری لغو شد.\n\n{goodbye}\n\n{welcome}",
                keyboard
            )
            self.log_info(f"User {user_id} cancelled current operation")
            return True
        except Exception as e:
            self.log_error(
                'general',
                f"Error in handle_cancel: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id if 'user_id' in locals() else None,
                chat_id=chat_id if 'chat_id' in locals() else None
            )
            return True
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    def is_admin_command(self, text: str) -> bool:
        """بررسی اینکه آیا پیام یک دستور مدیریت است"""
        admin_commands = ['/admin', '/stats', '/dashboard']
        return text in admin_commands
    
    def is_cancel_command(self, text: str) -> bool:
        """بررسی اینکه آیا پیام دستور لغو است"""
        return text == "/cancel"
    
    def is_help_command(self, text: str) -> bool:
        """بررسی اینکه آیا پیام دستور راهنما است"""
        return text == "/help"
    
    def is_profile_command(self, text: str) -> bool:
        """بررسی اینکه آیا پیام دستور پروفایل است"""
        return text == "/profile"
    
    def is_start_command(self, text: str) -> bool:
        """بررسی اینکه آیا پیام دستور شروع است"""
        return text == "/start"


__all__ = [
    'MessageHandler',
]