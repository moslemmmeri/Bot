# handlers/__init__.py
# پکیج هندلرها - لایه پردازش درخواست‌ها (Presentation Layer)

"""
پکیج هندلرها (Handlers)

این پکیج شامل کلاس‌ها و توابعی است که درخواست‌های ورودی از بله API را پردازش می‌کنند.
هندلرها بین لایه‌های Presentation (دریافت درخواست) و Service (منطق کسب‌وکار) قرار می‌گیرند.

هندلرهای موجود:
- BaseHandler: کلاس پایه برای تمام هندلرها
- MessageHandler: پردازش پیام‌های متنی و دستورات
- CallbackHandler: پردازش کالبک‌های دکمه‌های شیشه‌ای
- AdminHandler: پردازش درخواست‌های پنل مدیریت
- DynamicHandler: پردازش فرم‌های داینامیک سرویس‌ها
- ProfileHandler: پردازش درخواست‌های پروفایل کاربری
- HelpHandler: پردازش درخواست‌های راهنما
"""

# ============================================================
# ایمپورت هندلرها
# ============================================================

from .base_handler import BaseHandler
from .message_handler import MessageHandler
from .callback_handler import CallbackHandler
from .admin_handler import AdminHandler
from .dynamic_handler import DynamicHandler
from .profile_handler import ProfileHandler
from .help_handler import HelpHandler


# ============================================================
# کلاس اصلی توزیع‌کننده
# ============================================================

class MainHandler:
    """
    توزیع‌کننده اصلی درخواست‌ها
    مسئول تشخیص نوع درخواست و هدایت آن به هندلر مناسب
    """
    
    def __init__(self, connection, services):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            services: دیکشنری سرویس‌های موجود
        """
        self._connection = connection
        self._services = services
        
        # ایجاد هندلرها با dependencies
        self.message_handler = MessageHandler(connection, services)
        self.callback_handler = CallbackHandler(connection, services)
        self.admin_handler = AdminHandler(connection, services)
        self.dynamic_handler = DynamicHandler(connection, services)
        self.profile_handler = ProfileHandler(connection, services)
        self.help_handler = HelpHandler(connection, services)
    
    async def handle(self, update: dict) -> bool:
        """
        توزیع آپدیت به هندلر مناسب
        
        پارامترها:
            update: دیکشنری آپدیت دریافتی از بله
        
        بازگشت: True اگر آپدیت پردازش شد
        """
        # ========== پرداخت (قبل از پرداخت) ==========
        if "pre_checkout_query" in update:
            return await self.callback_handler.handle_pre_checkout(update)
        
        # ========== Callback Query ==========
        if "callback_query" in update:
            cb = update.get("callback_query", {})
            data = cb.get("data", "")
            
            # پنل مدیریت
            if data == "admin_panel" or data.startswith("admin_"):
                return await self.admin_handler.handle(update)
            
            # پروفایل کاربری
            if data.startswith("profile_"):
                return await self.profile_handler.handle(update)
            
            # راهنما
            if data.startswith("help_"):
                return await self.help_handler.handle(update)
            
            # پردازش توسط هندلرهای عمومی
            if await self.callback_handler.handle(update):
                return True
            
            # پردازش توسط هندلر داینامیک
            if await self.dynamic_handler.handle_callback(update):
                return True
            
            return False
        
        # ========== Message ==========
        if "message" in update:
            msg = update.get("message", {})
            text = msg.get("text", "").strip()
            
            # دستورات
            if text == "/start":
                return await self.message_handler.handle_start(update)
            
            if text == "/help":
                return await self.help_handler.handle_command(update)
            
            if text == "/profile":
                return await self.profile_handler.handle_command(update)
            
            if text == "/cancel":
                return await self.message_handler.handle_cancel(update)
            
            # پرداخت موفق
            if "successful_payment" in msg:
                return await self.dynamic_handler.handle_payment(update)
            
            # پنل مدیریت (برای پیام‌ها)
            if await self.admin_handler.handle_message(update):
                return True
            
            # پردازش توسط هندلر داینامیک
            if await self.dynamic_handler.handle_message(update):
                return True
            
            # پردازش توسط هندلر پیام
            return await self.message_handler.handle(update)
        
        return False


# ============================================================
# تابع Factory برای ایجاد هندلر اصلی
# ============================================================

def create_main_handler(connection, services) -> MainHandler:
    """
    ایجاد هندلر اصلی با dependencies مورد نیاز
    
    پارامترها:
        connection: اتصال به دیتابیس
        services: دیکشنری سرویس‌ها
    
    بازگشت: آبجکت MainHandler
    """
    return MainHandler(connection, services)


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # هندلرها
    'BaseHandler',
    'MessageHandler',
    'CallbackHandler',
    'AdminHandler',
    'DynamicHandler',
    'ProfileHandler',
    'HelpHandler',
    # کلاس اصلی
    'MainHandler',
    'create_main_handler',
]