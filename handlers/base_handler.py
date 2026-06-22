# handlers/base_handler.py
# کلاس پایه برای تمام هندلرها
# شامل توابع مشترک و کمکی برای پردازش درخواست‌ها
# اصلاح شده: متد log_error اکنون از پارامتر traceback پشتیبانی می‌کند

import traceback
from typing import Optional, Dict, Any, List
from logger_config import logger
from core import send_message, send_photo, send_document
from database import upsert_user
from utils.error_handler import log_general_error, log_database_error


class BaseHandler:
    """
    کلاس پایه برای تمام هندلرها
    شامل توابع مشترک و کمکی برای پردازش درخواست‌ها
    """
    
    def __init__(self, connection, services):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            services: دیکشنری سرویس‌های موجود
        """
        self._connection = connection
        self._services = services
    
    @property
    def connection(self):
        return self._connection
    
    @property
    def services(self):
        return self._services
    
    # ============================================================
    # توابع کمکی برای ارسال پیام
    # ============================================================
    
    async def send_message(self, chat_id: int, text: str, keyboard: Optional[Dict] = None) -> Any:
        """ارسال پیام به کاربر"""
        return await send_message(chat_id, text, keyboard)
    
    async def send_photo(self, chat_id: int, file_id: str, caption: str = "") -> Any:
        """ارسال عکس به کاربر"""
        return await send_photo(chat_id, file_id, caption)
    
    async def send_document(self, chat_id: int, file_id: str = None, 
                           file_path: str = None, caption: str = "") -> Any:
        """ارسال فایل به کاربر"""
        return await send_document(chat_id, file_id, file_path, caption)
    
    # ============================================================
    # توابع کمکی برای ثبت کاربر
    # ============================================================
    
    def upsert_user(self, user_id: int, username: Optional[str] = None,
                   first_name: Optional[str] = None,
                   last_name: Optional[str] = None) -> None:
        """ثبت یا به‌روزرسانی اطلاعات کاربر"""
        try:
            upsert_user(user_id, username, first_name, last_name)
        except Exception as e:
            log_database_error(
                f"Error upserting user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
    
    def extract_user_info(self, update: Dict) -> tuple:
        """
        استخراج اطلاعات کاربر از آپدیت
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: (user_id, chat_id, username, first_name, last_name)
        """
        user_id = None
        chat_id = None
        username = None
        first_name = None
        last_name = None
        
        # استخراج از callback_query
        cb = update.get("callback_query")
        if cb:
            from_user = cb.get("from", {})
            user_id = from_user.get("id")
            username = from_user.get("username")
            first_name = from_user.get("first_name")
            last_name = from_user.get("last_name")
            chat_id = cb.get("message", {}).get("chat", {}).get("id")
            return user_id, chat_id, username, first_name, last_name
        
        # استخراج از message
        msg = update.get("message")
        if msg:
            from_user = msg.get("from", {})
            user_id = from_user.get("id")
            username = from_user.get("username")
            first_name = from_user.get("first_name")
            last_name = from_user.get("last_name")
            chat_id = msg.get("chat", {}).get("id")
            return user_id, chat_id, username, first_name, last_name
        
        return None, None, None, None, None
    
    def get_user_id_from_update(self, update: Dict) -> Optional[int]:
        """استخراج شناسه کاربر از آپدیت"""
        cb = update.get("callback_query")
        if cb:
            return cb.get("from", {}).get("id")
        
        msg = update.get("message")
        if msg:
            return msg.get("from", {}).get("id")
        
        return None
    
    def get_chat_id_from_update(self, update: Dict) -> Optional[int]:
        """استخراج شناسه چت از آپدیت"""
        cb = update.get("callback_query")
        if cb:
            return cb.get("message", {}).get("chat", {}).get("id")
        
        msg = update.get("message")
        if msg:
            return msg.get("chat", {}).get("id")
        
        return None
    
    def get_callback_data(self, update: Dict) -> Optional[str]:
        """استخراج داده کالبک از آپدیت"""
        cb = update.get("callback_query")
        if cb:
            return cb.get("data")
        return None
    
    def get_message_text(self, update: Dict) -> Optional[str]:
        """استخراج متن پیام از آپدیت"""
        msg = update.get("message")
        if msg:
            return msg.get("text", "").strip()
        return None
    
    # ============================================================
    # توابع کمکی برای بررسی دسترسی
    # ============================================================
    
    def is_owner(self, user_id: int) -> bool:
        """بررسی مالک بودن کاربر"""
        from config import config
        return user_id == config.OWNER_ID
    
    def is_admin(self, user_id: int) -> bool:
        """بررسی ادمین بودن کاربر"""
        from database import is_admin as db_is_admin
        return db_is_admin(user_id)
    
    def can_access_admin(self, user_id: int) -> bool:
        """بررسی دسترسی کاربر به پنل مدیریت"""
        return self.is_owner(user_id) or self.is_admin(user_id)
    
    # ============================================================
    # توابع کمکی برای کاربران
    # ============================================================
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر"""
        try:
            from services.user_service import UserService
            user_service = self._services.get('user')
            if user_service:
                return user_service.get_user(user_id)
            
            # Fallback به تابع مستقیم
            from database import get_user
            return get_user(user_id)
        except Exception as e:
            log_general_error(
                f"Error in get_user for user_id {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return None
    
    def get_user_display_name(self, user_id: int) -> str:
        """دریافت نام قابل نمایش کاربر"""
        try:
            from services.user_service import UserService
            user_service = self._services.get('user')
            if user_service:
                return user_service.get_user_display_name(user_id)
            
            # Fallback
            user = self.get_user(user_id)
            if not user:
                return 'کاربر ناشناس'
            
            first_name = user.get('first_name')
            last_name = user.get('last_name')
            username = user.get('username')
            
            if first_name and last_name:
                return f"{first_name} {last_name}"
            elif first_name:
                return first_name
            elif username:
                return f"@{username}"
            return f"کاربر {user_id}"
        except Exception as e:
            log_general_error(
                f"Error in get_user_display_name for user_id {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return f"کاربر {user_id}"
    
    # ============================================================
    # توابع کمکی برای منوها
    # ============================================================
    
    def get_main_menu_with_admin(self, user_id: int) -> Dict:
        """دریافت منوی اصلی با دکمه مدیریت در صورت نیاز"""
        from core import get_main_menu_with_admin
        return get_main_menu_with_admin(user_id)
    
    def get_welcome_text(self) -> str:
        """دریافت متن خوش‌آمدگویی"""
        from core import get_welcome_text
        return get_welcome_text()
    
    def get_main_menu_title(self) -> str:
        """دریافت عنوان منوی اصلی"""
        from core import get_main_menu_title
        return get_main_menu_title()
    
    def get_error_message(self) -> str:
        """دریافت پیام خطا"""
        from core import get_error_message_text
        return get_error_message_text()
    
    # ============================================================
    # توابع کمکی برای لاگ - اصلاح شده برای پذیرش traceback
    # ============================================================
    
    def log_error(self, error_type: str, error_message: str, 
                 traceback_str: Optional[str] = None,
                 user_id: Optional[int] = None,
                 chat_id: Optional[int] = None,
                 data: Optional[Dict] = None,
                 traceback: Optional[str] = None) -> None:
        """
        ثبت خطا - این متد هم پارامتر traceback و هم traceback_str را می‌پذیرد
        
        پارامترها:
            error_type: نوع خطا
            error_message: پیام خطا
            traceback_str: رشته traceback (اختیاری)
            user_id: شناسه کاربر (اختیاری)
            chat_id: شناسه چت (اختیاری)
            data: داده‌های اضافی (اختیاری)
            traceback: alias برای traceback_str (سازگاری با کدهای جدید)
        """
        # اگر traceback ارائه شده و traceback_str None است، از traceback استفاده کن
        if traceback_str is None and traceback is not None:
            traceback_str = traceback
        
        from core import log_error as core_log_error
        core_log_error(error_type, error_message, traceback_str, user_id, chat_id, data)
    
    def log_info(self, message: str) -> None:
        """ثبت اطلاعات در لاگ"""
        logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """ثبت هشدار در لاگ"""
        logger.warning(message)
    
    def log_debug(self, message: str) -> None:
        """ثبت دیباگ در لاگ"""
        logger.debug(message)
    
    # ============================================================
    # توابع کمکی برای وضعیت کاربران
    # ============================================================
    
    def get_user_state(self, user_id: int) -> Dict:
        """دریافت وضعیت کاربر از user_states"""
        from core import user_states
        return user_states.get(user_id, {"state": "main"})
    
    def set_user_state(self, user_id: int, state: Dict) -> None:
        """تنظیم وضعیت کاربر"""
        from core import user_states
        user_states[user_id] = state
    
    def clear_user_state(self, user_id: int) -> None:
        """پاک کردن وضعیت کاربر"""
        from core import user_states
        if user_id in user_states:
            user_states[user_id] = {"state": "main"}
    
    def get_user_answer(self, user_id: int, key: str, default=None):
        """دریافت پاسخ کاربر از user_states"""
        state = self.get_user_state(user_id)
        return state.get(key, default)
    
    def set_user_answer(self, user_id: int, key: str, value) -> None:
        """ذخیره پاسخ کاربر در user_states"""
        state = self.get_user_state(user_id)
        state[key] = value
        self.set_user_state(user_id, state)
    
    # ============================================================
    # توابع کمکی برای کیبوردها
    # ============================================================
    
    def get_keyboard(self, keyboard_func, *args, **kwargs) -> Dict:
        """دریافت کیبورد از تابع کیبورد"""
        try:
            return keyboard_func(*args, **kwargs)
        except Exception as e:
            log_general_error(
                f"Error getting keyboard from {keyboard_func.__name__}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {"inline_keyboard": []}
    
    # ============================================================
    # توابع کمکی برای پرداخت
    # ============================================================
    
    def get_default_price(self) -> int:
        """دریافت مبلغ پیش‌فرض"""
        from config import config
        return config.DEFAULT_PRICE_AMOUNT
    
    def get_default_price_label(self) -> str:
        """دریافت برچسب مبلغ پیش‌فرض"""
        from config import config
        return config.DEFAULT_PRICE_LABEL
    
    # ============================================================
    # متدهای انتزاعی برای پیاده‌سازی در زیرکلاس‌ها
    # ============================================================
    
    async def handle(self, update: Dict) -> bool:
        """
        متد اصلی پردازش درخواست (باید در زیرکلاس‌ها پیاده‌سازی شود)
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر پردازش شد
        """
        raise NotImplementedError("Subclasses must implement handle()")
    
    async def handle_message(self, update: Dict) -> bool:
        """
        پردازش پیام (اختیاری - می‌تواند در زیرکلاس‌ها بازنویسی شود)
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر پردازش شد
        """
        return False
    
    async def handle_callback(self, update: Dict) -> bool:
        """
        پردازش کالبک (اختیاری - می‌تواند در زیرکلاس‌ها بازنویسی شود)
        
        پارامترها:
            update: دیکشنری آپدیت
        
        بازگشت: True اگر پردازش شد
        """
        return False


__all__ = [
    'BaseHandler',
]