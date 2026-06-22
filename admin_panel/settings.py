# admin_panel/settings.py
# مدیریت تنظیمات عمومی ربات در پنل مدیریت
# شامل: تنظیم مبلغ پیش‌فرض، تنظیم تعداد ستون‌های پیش‌فرض منو و سایر تنظیمات عمومی

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, OWNER_ID
from database import get_setting, set_setting, get_default_menu_columns, set_default_menu_columns
from keyboards import admin_main_keyboard
from services.permission_service import get_permission_service
from services.state_service import get_state_service
from utils import format_number
from utils.error_handler import log_callback_error, log_general_error, log_security_error


# ==================== توابع کمکی ====================

def _is_owner(user_id):
    """بررسی آیا کاربر OWNER_ID است"""
    return user_id == OWNER_ID


# ==================== کیبوردهای تنظیمات ====================

def settings_main_keyboard(current_price, current_columns):
    """کیبورد اصلی صفحه تنظیمات"""
    return {
        "inline_keyboard": [
            [{"text": f"💰 تنظیم مبلغ پیش‌فرض (فعلی: {format_number(current_price)})", 
              "callback_data": "admin_set_price"}],
            [{"text": f"📊 تنظیم ستون‌های پیش‌فرض (فعلی: {current_columns})", 
              "callback_data": "admin_set_default_columns"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


# ==================== هندلر اصلی ====================

async def handle_settings(chat_id, user_id):
    """
    نمایش صفحه تنظیمات با گزینه‌های مدیریت
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        # دریافت تنظیمات فعلی
        current_price = get_setting("default_price") or "50000"
        current_columns = get_default_menu_columns()
        
        keyboard = settings_main_keyboard(current_price, current_columns)
        
        msg = f"⚙️ **تنظیمات**\n\n"
        msg += f"💰 مبلغ پیش‌فرض فعلی: {format_number(current_price)} ریال\n"
        msg += f"📊 تعداد ستون‌های پیش‌فرض منو: {current_columns}\n\n"
        msg += "تعداد ستون‌ها تعیین می‌کند که دکمه‌های منو در هر ردیف چند ستون داشته باشند.\n"
        msg += "مقدار پیش‌فرض برای دسته‌بندی‌ها و دکمه‌هایی که تنظیمات اختصاصی ندارند، استفاده می‌شود."
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_settings: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش تنظیمات.")
        return True


# ==================== تنظیم مبلغ پیش‌فرض ====================

async def handle_set_price(chat_id, user_id):
    """
    شروع فرآیند تنظیم مبلغ پیش‌فرض
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        state_service = get_state_service()
        await state_service.set_state_field(user_id, "state", "admin_set_price")
        
        await send_message(
            chat_id,
            "💰 **تنظیم مبلغ پیش‌فرض**\n\n"
            "لطفاً مبلغ جدید را به ریال وارد کنید (فقط عدد):\n"
            "(مثال: 100000 برای ۱۰۰,۰۰۰ ریال)\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_set_price: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع تنظیم مبلغ.")
        return True


async def handle_set_price_message(chat_id, user_id, text):
    """
    پردازش پیام تنظیم مبلغ پیش‌فرض
    این تابع از msg_admin.py صدا زده می‌شود
    """
    try:
        price = int(text.replace(",", "").replace(" ", ""))
        if price <= 0:
            await send_message(chat_id, "❌ مبلغ باید بزرگتر از صفر باشد.")
            return True
        
        set_setting("default_price", str(price), "مبلغ پیش‌فرض برای دکمه‌های جدید")
        await send_message(
            chat_id, 
            f"✅ مبلغ پیش‌فرض به {format_number(price)} ریال تنظیم شد.",
            admin_main_keyboard()
        )
        
        state_service = get_state_service()
        await state_service.set_state_field(user_id, "state", "main")
        return True
        
    except ValueError:
        await send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_set_price_message: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم مبلغ.")
        state_service = get_state_service()
        await state_service.set_state_field(user_id, "state", "main")
        return True


# ==================== تنظیم ستون‌های پیش‌فرض ====================

async def handle_set_default_columns(chat_id, user_id):
    """
    شروع فرآیند تنظیم تعداد ستون‌های پیش‌فرض منو
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        state_service = get_state_service()
        await state_service.set_state_field(user_id, "state", "admin_set_default_columns")
        
        await send_message(
            chat_id,
            "📊 **تنظیم تعداد ستون‌های پیش‌فرض منو**\n\n"
            "لطفاً تعداد ستون‌های پیش‌فرض را وارد کنید (۱ تا ۸):\n"
            "(این مقدار زمانی استفاده می‌شود که دسته‌بندی یا دکمه تنظیمات اختصاصی نداشته باشد)\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_set_default_columns: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع تنظیم ستون‌ها.")
        return True


async def handle_set_default_columns_message(chat_id, user_id, text):
    """
    پردازش پیام تنظیم تعداد ستون‌های پیش‌فرض
    این تابع از msg_admin.py صدا زده می‌شود
    """
    try:
        columns = int(text.strip())
        if columns < 1 or columns > 8:
            await send_message(chat_id, "❌ تعداد ستون‌ها باید بین ۱ تا ۸ باشد.")
            return True
        
        set_default_menu_columns(columns)
        
        await send_message(
            chat_id, 
            f"✅ تعداد ستون‌های پیش‌فرض منو به {columns} تنظیم شد.",
            admin_main_keyboard()
        )
        
        state_service = get_state_service()
        await state_service.set_state_field(user_id, "state", "main")
        return True
        
    except ValueError:
        await send_message(chat_id, "❌ لطفاً یک عدد معتبر بین ۱ تا ۸ وارد کنید.")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_set_default_columns_message: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم ستون‌ها.")
        state_service = get_state_service()
        await state_service.set_state_field(user_id, "state", "main")
        return True


# ==================== صادر کردن ====================

__all__ = [
    'handle_settings',
    'handle_set_price',
    'handle_set_price_message',
    'handle_set_default_columns',
    'handle_set_default_columns_message',
]