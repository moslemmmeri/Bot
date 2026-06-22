# handlers/callback_handler.py
# پردازش کالبک‌های دکمه‌های شیشه‌ای

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, Dict, Any
from logger_config import logger
from core import user_states
from .base_handler import BaseHandler
from keyboards import main_menu_keyboard, more_menu_keyboard, other_services_keyboard


class CallbackHandler(BaseHandler):
    """
    هندلر کالبک‌های دکمه‌های شیشه‌ای
    پردازش: بازگشت به منو، منوی بیشتر، دیگر خدمات، و هدایت به هندلرهای تخصصی
    """
    
    # ============================================================
    # متد اصلی پردازش کالبک
    # ============================================================
    
    async def handle(self, update: Dict) -> bool:
        """
        پردازش کالبک‌های دکمه‌های شیشه‌ای
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر کالبک پردازش شد
        """
        try:  # ✅ اضافه شد برای مدیریت خطاهای پیش‌بینی نشده
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
            
            self.log_debug(f"Callback received: {data} from user {user_id}")
            
            # ========== کالبک‌های عمومی ==========
            
            # بازگشت به منوی اصلی
            if data == "back_main":
                return await self._handle_back_main(chat_id, user_id)
            
            # بازگشت به منوی بیشتر
            if data == "back_more":
                return await self._handle_back_more(chat_id, user_id)
            
            # نمایش منوی بیشتر
            if data == "menu_more":
                return await self._handle_menu_more(chat_id, user_id)
            
            # نمایش منوی دیگر خدمات
            if data == "menu_other":
                return await self._handle_menu_other(chat_id, user_id)
            
            # ========== کالبک‌های تخصصی ==========
            
            # پنل مدیریت
            if data == "admin_panel" or data.startswith("admin_"):
                from .admin_handler import AdminHandler
                admin_handler = AdminHandler(self._connection, self._services)
                return await admin_handler.handle(update)
            
            # پروفایل کاربری
            if data.startswith("profile_"):
                from .profile_handler import ProfileHandler
                profile_handler = ProfileHandler(self._connection, self._services)
                return await profile_handler.handle(update)
            
            # راهنما
            if data.startswith("help_"):
                from .help_handler import HelpHandler
                help_handler = HelpHandler(self._connection, self._services)
                return await help_handler.handle(update)
            
            # فرم داینامیک (سرویس‌ها)
            if await self._handle_dynamic(update):
                return True
            
            # ========== کالبک ناشناخته ==========
            await self._handle_unknown(chat_id, user_id)
            return True
            
        except Exception as e:
            # ✅ ثبت خطای پیش‌بینی نشده با traceback کامل
            self.log_error(
                'callback',
                f"Error in CallbackHandler.handle: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id if 'user_id' in locals() else None,
                chat_id=chat_id if 'chat_id' in locals() else None,
                data={'data': data} if 'data' in locals() else None
            )
            # در صورت خطا، سعی می‌کنیم به کاربر پیام خطا بدهیم
            if 'chat_id' in locals() and 'user_id' in locals():
                from core import send_message
                await send_message(chat_id, "❌ خطا در پردازش درخواست. لطفاً دوباره تلاش کنید.")
            return True
    
    # ============================================================
    # پردازش کالبک‌های عمومی
    # ============================================================
    
    async def _handle_back_main(self, chat_id: int, user_id: int) -> bool:
        """
        بازگشت به منوی اصلی
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True
        """
        self.clear_user_state(user_id)
        keyboard = self.get_main_menu_with_admin(user_id)
        welcome_text = self.get_welcome_text()
        
        await self.send_message(chat_id, welcome_text, keyboard)
        self.log_debug(f"User {user_id} returned to main menu")
        return True
    
    async def _handle_back_more(self, chat_id: int, user_id: int) -> bool:
        """
        بازگشت به منوی بیشتر
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True
        """
        keyboard = more_menu_keyboard()
        title = self.get_main_menu_title()
        
        await self.send_message(chat_id, title, keyboard)
        return True
    
    async def _handle_menu_more(self, chat_id: int, user_id: int) -> bool:
        """
        نمایش منوی بیشتر
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True
        """
        keyboard = more_menu_keyboard()
        
        await self.send_message(chat_id, "➕  منوی بیشتر:", keyboard)
        return True
    
    async def _handle_menu_other(self, chat_id: int, user_id: int) -> bool:
        """
        نمایش منوی دیگر خدمات
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True
        """
        keyboard = other_services_keyboard()
        
        await self.send_message(chat_id, "🔧 دیگر خدمات:", keyboard)
        return True
    
    # ============================================================
    # هدایت به هندلرهای تخصصی
    # ============================================================
    
    async def _handle_dynamic(self, update: Dict) -> bool:
        """
        هدایت کالبک به هندلر داینامیک
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر کالبک توسط هندلر داینامیک پردازش شد
        """
        from .dynamic_handler import DynamicHandler
        dynamic_handler = DynamicHandler(self._connection, self._services)
        return await dynamic_handler.handle_callback(update)
    
    async def _handle_admin(self, update: Dict) -> bool:
        """
        هدایت کالبک به هندلر مدیریت
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر کالبک توسط هندلر مدیریت پردازش شد
        """
        from .admin_handler import AdminHandler
        admin_handler = AdminHandler(self._connection, self._services)
        return await admin_handler.handle(update)
    
    async def _handle_profile(self, update: Dict) -> bool:
        """
        هدایت کالبک به هندلر پروفایل
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر کالبک توسط هندلر پروفایل پردازش شد
        """
        from .profile_handler import ProfileHandler
        profile_handler = ProfileHandler(self._connection, self._services)
        return await profile_handler.handle(update)
    
    async def _handle_help(self, update: Dict) -> bool:
        """
        هدایت کالبک به هندلر راهنما
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر کالبک توسط هندلر راهنما پردازش شد
        """
        from .help_handler import HelpHandler
        help_handler = HelpHandler(self._connection, self._services)
        return await help_handler.handle(update)
    
    # ============================================================
    # پردازش کالبک ناشناخته
    # ============================================================
    
    async def _handle_unknown(self, chat_id: int, user_id: int) -> bool:
        """
        پردازش کالبک ناشناخته
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True
        """
        from core import get_invalid_option_text
        
        invalid_text = get_invalid_option_text()
        keyboard = self.get_main_menu_with_admin(user_id)
        
        await self.send_message(chat_id, invalid_text, keyboard)
        self.log_warning(f"Unknown callback from user {user_id}")
        return True
    
    # ============================================================
    # پردازش Pre-Checkout (قبل از پرداخت)
    # ============================================================
    
    async def handle_pre_checkout(self, update: Dict) -> bool:
        """
        پردازش Pre-Checkout Query (قبل از پرداخت)
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True
        """
        try:  # ✅ اضافه شد برای مدیریت خطا
            query = update.get("pre_checkout_query")
            if not query:
                return False
            
            query_id = query.get("id")
            if not query_id:
                return False
            
            from core import answer_pre_checkout_query
            await answer_pre_checkout_query(query_id, True)
            
            self.log_debug(f"Pre-checkout query answered: {query_id}")
            return True
        except Exception as e:
            self.log_error(
                'callback',
                f"Error in handle_pre_checkout: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    def is_admin_callback(self, data: str) -> bool:
        """بررسی اینکه آیا کالبک مربوط به پنل مدیریت است"""
        return data == "admin_panel" or data.startswith("admin_")
    
    def is_profile_callback(self, data: str) -> bool:
        """بررسی اینکه آیا کالبک مربوط به پروفایل است"""
        return data.startswith("profile_")
    
    def is_help_callback(self, data: str) -> bool:
        """بررسی اینکه آیا کالبک مربوط به راهنما است"""
        return data.startswith("help_")
    
    def is_general_callback(self, data: str) -> bool:
        """بررسی اینکه آیا کالبک عمومی است"""
        return data in ["back_main", "back_more", "menu_more", "menu_other"]
    
    def is_dynamic_callback(self, data: str) -> bool:
        """
        بررسی اینکه آیا کالبک مربوط به سرویس داینامیک است
        (با جستجو در دیتابیس)
        """
        try:
            from database import get_button_by_callback, get_option_by_callback
            
            # بررسی دکمه
            button = get_button_by_callback(data)
            if button:
                return True
            
            # بررسی گزینه سوال
            option = get_option_by_callback(data)
            if option:
                return True
            
            return False
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            self.log_error(
                'callback',
                f"Error checking dynamic callback: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False


__all__ = [
    'CallbackHandler',
]