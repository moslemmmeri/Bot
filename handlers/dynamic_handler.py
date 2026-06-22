# handlers/dynamic_handler.py
# پردازش فرم‌های داینامیک سرویس‌ها

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, Dict, Any
from logger_config import logger
from core import user_states
from .base_handler import BaseHandler
from dynamic import handle_dynamic_callback, handle_dynamic_message, handle_dynamic_payment


class DynamicHandler(BaseHandler):
    """
    هندلر فرم‌های داینامیک سرویس‌ها
    پردازش: کالبک‌های سرویس‌ها، پیام‌های فرم، پرداخت موفق
    """
    
    # ============================================================
    # متد اصلی پردازش کالبک
    # ============================================================
    
    async def handle_callback(self, update: Dict) -> bool:
        """
        پردازش کالبک‌های سرویس‌های داینامیک
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر کالبک پردازش شد
        """
        try:
            return await handle_dynamic_callback(update)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'callback',
                f"Error in dynamic callback: {e}",
                traceback=traceback.format_exc(),
                user_id=self.get_user_id_from_update(update),
                chat_id=self.get_chat_id_from_update(update)
            )
            return False
    
    # ============================================================
    # پردازش پیام‌های فرم
    # ============================================================
    
    async def handle_message(self, update: Dict) -> bool:
        """
        پردازش پیام‌های فرم داینامیک
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر پیام فرم بود
        """
        try:
            return await handle_dynamic_message(update)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'general',
                f"Error in dynamic message: {e}",
                traceback=traceback.format_exc(),
                user_id=self.get_user_id_from_update(update),
                chat_id=self.get_chat_id_from_update(update)
            )
            return False
    
    # ============================================================
    # پردازش پرداخت موفق
    # ============================================================
    
    async def handle_payment(self, update: Dict) -> bool:
        """
        پردازش پرداخت موفق در فرم‌های داینامیک
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر پرداخت پردازش شد
        """
        try:
            return await handle_dynamic_payment(update)
        except Exception as e:
            # ✅ استفاده از traceback کامل
            self.log_error(
                'payment',
                f"Error in dynamic payment: {e}",
                traceback=traceback.format_exc(),
                user_id=self.get_user_id_from_update(update),
                chat_id=self.get_chat_id_from_update(update)
            )
            return False
    
    # ============================================================
    # متدهای کمکی برای بررسی وضعیت کاربر
    # ============================================================
    
    def is_dynamic_state(self, user_id: int) -> bool:
        """
        بررسی اینکه آیا کاربر در حالت فرم داینامیک است
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: True اگر کاربر در حالت فرم باشد
        """
        state = self.get_user_state(user_id)
        state_name = state.get("state", "main")
        return state_name in [
            "dynamic_awaiting_answer",
            "dynamic_awaiting_option",
            "dynamic_awaiting_payment"
        ]
    
    def get_dynamic_state_info(self, user_id: int) -> Dict:
        """
        دریافت اطلاعات کامل وضعیت فرم کاربر
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: دیکشنری وضعیت فرم
        """
        return self.get_user_state(user_id)
    
    def is_dynamic_callback(self, data: str) -> bool:
        """
        بررسی اینکه آیا کالبک مربوط به سرویس داینامیک است
        
        پارامترها:
            data: داده کالبک
        
        بازگشت: True اگر کالبک داینامیک باشد
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
            # ✅ اضافه شدن traceback کامل
            self.log_error(
                'callback',
                f"Error checking dynamic callback: {e}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # متدهای کمکی برای دریافت اطلاعات سرویس
    # ============================================================
    
    def get_button_by_callback(self, callback_data: str) -> Optional[Dict]:
        """دریافت دکمه بر اساس callback_data"""
        try:
            from database import get_button_by_callback
            return get_button_by_callback(callback_data)
        except Exception as e:
            # ✅ اضافه شدن traceback کامل
            self.log_error(
                'database',
                f"Error getting button by callback: {e}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_option_by_callback(self, callback_data: str) -> Optional[Dict]:
        """دریافت گزینه سوال بر اساس callback_data"""
        try:
            from database import get_option_by_callback
            return get_option_by_callback(callback_data)
        except Exception as e:
            # ✅ اضافه شدن traceback کامل
            self.log_error(
                'database',
                f"Error getting option by callback: {e}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_questions_by_button(self, button_id: int) -> list:
        """دریافت سوالات یک دکمه"""
        try:
            from database import get_questions_by_button
            return get_questions_by_button(button_id)
        except Exception as e:
            # ✅ اضافه شدن traceback کامل
            self.log_error(
                'database',
                f"Error getting questions by button: {e}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_button_by_id(self, button_id: int) -> Optional[Dict]:
        """دریافت دکمه بر اساس شناسه"""
        try:
            from database import get_button_by_id
            return get_button_by_id(button_id)
        except Exception as e:
            # ✅ اضافه شدن traceback کامل
            self.log_error(
                'database',
                f"Error getting button by id: {e}",
                traceback=traceback.format_exc()
            )
            return None
    
    # ============================================================
    # متدهای کمکی برای ادامه فرم
    # ============================================================
    
    async def continue_form(self, chat_id: int, user_id: int) -> bool:
        """
        ادامه فرم از وضعیت فعلی کاربر
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True اگر فرم ادامه یافت
        """
        try:
            state = self.get_user_state(user_id)
            button_id = state.get("button_id")
            
            if not button_id:
                await self.send_message(
                    chat_id,
                    "❌ خطا: شناسه سرویس یافت نشد.\nلطفاً دوباره از منو انتخاب کنید.",
                    self.get_main_menu_with_admin(user_id)
                )
                self.clear_user_state(user_id)
                return True
            
            from dynamic.dynamic_core import _process_questions
            return await _process_questions(user_id, chat_id, button_id)
        except Exception as e:
            self.log_error(
                'general',
                f"Error in continue_form: {e}",
                traceback=traceback.format_exc(),
                user_id=user_id,
                chat_id=chat_id
            )
            return False
    
    async def reset_form(self, chat_id: int, user_id: int) -> bool:
        """
        بازنشانی فرم و بازگشت به منوی اصلی
        
        پارامترها:
            chat_id: شناسه چت
            user_id: شناسه کاربر
        
        بازگشت: True
        """
        self.clear_user_state(user_id)
        keyboard = self.get_main_menu_with_admin(user_id)
        welcome_text = self.get_welcome_text()
        
        await self.send_message(
            chat_id,
            "🔄 فرم بازنشانی شد.\n\n" + welcome_text,
            keyboard
        )
        return True


__all__ = [
    'DynamicHandler',
]