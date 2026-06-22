# admin_panel/branding.py
# شخصی‌سازی ظاهر و برندینگ ربات - مدیریت متون، پیام‌ها و ظاهر ربات
# نسخه async با logging و ذخیره در دیتابیس
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback
from logger_config import logger
from core import send_message, OWNER_ID, user_states
from database import get_setting, set_setting
from keyboards import admin_main_keyboard
from services.permission_service import get_permission_service
from services.state_service import get_state_service
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_security_error,
    log_database_error
)


# ==================== تنظیمات پیش‌فرض برندینگ ====================

DEFAULT_BRANDING = {
    'brand_welcome_text': '👋 به ربات خوش آمدید.\n🌟 لطفاً یکی از گزینه‌ها را انتخاب کنید:',
    'brand_main_menu_title': '🔙 منوی اصلی:',
    'brand_admin_title': '🔐 **پنل مدیریت ربات**\nلطفاً یکی از گزینه‌ها را انتخاب کنید:',
    'brand_order_success': '✅ درخواست شما ثبت شد.\n🙏 به زودی تماس می‌گیریم.',
    'brand_payment_success': '✅ پرداخت موفق و ثبت سفارش.',
    'brand_invalid_option': '⚠️ گزینه نامعتبر است.',
    'brand_error_message': '❌ خطای داخلی رخ داده است. لطفاً دوباره تلاش کنید.',
    'brand_footer_text': '© ۱۴۰۳ - تمامی حقوق محفوظ است',
}


# ==================== توابع کمکی ====================

def get_branded_text(key: str, default: str = None) -> str:
    """دریافت متن برندینگ از دیتابیس یا مقدار پیش‌فرض"""
    try:
        value = get_setting(key)
        if value:
            return value
    except Exception as e:
        log_database_error(f"Error getting branding for {key}: {str(e)}", traceback=traceback.format_exc())
    
    # بازگشت به مقدار پیش‌فرض
    if default is not None:
        return default
    return DEFAULT_BRANDING.get(key, '')


def get_welcome_text() -> str:
    return get_branded_text('brand_welcome_text')


def get_main_menu_title() -> str:
    return get_branded_text('brand_main_menu_title')


def get_admin_title() -> str:
    return get_branded_text('brand_admin_title')


def get_order_success_text() -> str:
    return get_branded_text('brand_order_success')


def get_payment_success_text() -> str:
    return get_branded_text('brand_payment_success')


def get_invalid_option_text() -> str:
    return get_branded_text('brand_invalid_option')


def get_error_message_text() -> str:
    return get_branded_text('brand_error_message')


def get_footer_text() -> str:
    return get_branded_text('brand_footer_text')


# ==================== کیبوردهای برندینگ ====================

def branding_main_keyboard() -> dict:
    """کیبورد اصلی منوی برندینگ"""
    return {
        "inline_keyboard": [
            [{"text": "📋 مشاهده متون فعلی", "callback_data": "admin_branding_view"}],
            [{"text": "✏️ ویرایش متون", "callback_data": "admin_branding_edit"}],
            [{"text": "🔄 بازنشانی به پیش‌فرض", "callback_data": "admin_branding_reset"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


def branding_edit_keyboard() -> dict:
    """کیبورد انتخاب فیلد برای ویرایش"""
    fields = [
        ('brand_welcome_text', '👋 متن خوش‌آمدگویی'),
        ('brand_main_menu_title', '🏠 عنوان منوی اصلی'),
        ('brand_admin_title', '🔐 عنوان پنل مدیریت'),
        ('brand_order_success', '✅ پیام ثبت سفارش'),
        ('brand_payment_success', '💰 پیام پرداخت موفق'),
        ('brand_invalid_option', '⚠️ پیام گزینه نامعتبر'),
        ('brand_error_message', '❌ پیام خطا'),
        ('brand_footer_text', '📌 فوتر (پانوشت)'),
    ]
    keyboard = []
    for key, label in fields:
        keyboard.append([{"text": label, "callback_data": f"admin_branding_edit_{key}"}])
    keyboard.append([{"text": "🔙 بازگشت به برندینگ", "callback_data": "admin_branding"}])
    return {"inline_keyboard": keyboard}


def branding_confirm_keyboard() -> dict:
    """کیبورد تایید برای بازنشانی"""
    return {
        "inline_keyboard": [
            [{"text": "⚠️ آیا از بازنشانی همه متون به پیش‌فرض مطمئن هستید؟"}],
            [{"text": "✅ بله، بازنشانی شود", "callback_data": "admin_branding_reset_confirm"}],
            [{"text": "❌ خیر، انصراف", "callback_data": "admin_branding"}]
        ]
    }


# ==================== توابع اصلی ====================

async def handle_branding(chat_id: int, user_id: int) -> bool:
    """نمایش منوی اصلی برندینگ"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        await send_message(
            chat_id,
            "🎨 **مدیریت برندینگ (شخصی‌سازی ظاهر)**\n\n"
            "در این بخش می‌توانید متون و پیام‌های ربات را شخصی‌سازی کنید.\n"
            "تغییرات بلافاصله اعمال می‌شوند.",
            branding_main_keyboard()
        )
        return True
    except Exception as e:
        log_callback_error(f"Error in handle_branding: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش برندینگ.")
        return True


async def handle_branding_view(chat_id: int, user_id: int) -> bool:
    """نمایش متون برندینگ فعلی"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        msg = "📋 **متون برندینگ فعلی**\n\n"
        for key, default in DEFAULT_BRANDING.items():
            current = get_branded_text(key, default)
            label = key.replace('brand_', '').replace('_', ' ').title()
            msg += f"**{label}:**\n{current}\n\n"

        await send_message(
            chat_id,
            msg,
            {"inline_keyboard": [[{"text": "🔙 بازگشت به برندینگ", "callback_data": "admin_branding"}]]}
        )
        return True
    except Exception as e:
        log_callback_error(f"Error in handle_branding_view: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش متون برندینگ.")
        return True


async def handle_branding_edit(chat_id: int, user_id: int) -> bool:
    """نمایش لیست فیلدهای قابل ویرایش"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        await send_message(
            chat_id,
            "✏️ **ویرایش متون برندینگ**\n\n"
            "لطفاً بخش مورد نظر را انتخاب کنید:",
            branding_edit_keyboard()
        )
        return True
    except Exception as e:
        log_callback_error(f"Error in handle_branding_edit: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش ویرایش برندینگ.")
        return True


async def handle_branding_edit_field(chat_id: int, user_id: int, data: str) -> bool:
    """شروع ویرایش یک فیلد خاص (admin_branding_edit_<key>)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        key = data.split("_", 3)[3]  # admin_branding_edit_<key>
        current = get_branded_text(key, DEFAULT_BRANDING.get(key, ''))

        state_service = get_state_service()
        await state_service.update_state(user_id, {
            "state": "admin_branding_edit",
            "branding_key": key
        })

        await send_message(
            chat_id,
            f"✏️ **ویرایش متن**\n\n"
            f"کلید: `{key}`\n"
            f"متن فعلی:\n{current}\n\n"
            f"لطفاً متن جدید را وارد کنید:\n"
            f"(برای انصراف، /cancel را ارسال کنید)",
            {"inline_keyboard": [[{"text": "🔙 انصراف", "callback_data": "admin_branding"}]]}
        )
        return True
    except Exception as e:
        log_callback_error(f"Error in handle_branding_edit_field: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در شروع ویرایش.")
        return True


async def handle_branding_save(chat_id: int, user_id: int, text: str) -> bool:
    """ذخیره متن جدید برندینگ (از msg_admin صدا زده می‌شود)"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        state_service = get_state_service()
        state_info = await state_service.get_state(user_id, {})
        key = state_info.get("branding_key")

        if not key:
            await send_message(chat_id, "❌ خطا: کلید برندینگ یافت نشد.")
            await state_service.set_state(user_id, {"state": "main"})
            return True

        if not text or text.strip() == "":
            await send_message(chat_id, "❌ متن نمی‌تواند خالی باشد.")
            return True

        # ذخیره در دیتابیس
        set_setting(key, text.strip())
        await send_message(chat_id, f"✅ متن برای `{key}` با موفقیت به‌روزرسانی شد.")

        # پاک کردن وضعیت
        await state_service.set_state(user_id, {"state": "main"})

        # بازگشت به منوی برندینگ
        await handle_branding(chat_id, user_id)
        return True
    except Exception as e:
        log_callback_error(f"Error in handle_branding_save: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در ذخیره متن.")
        await get_state_service().set_state(user_id, {"state": "main"})
        return True


async def handle_branding_reset(chat_id: int, user_id: int) -> bool:
    """نمایش تاییدیه بازنشانی به پیش‌فرض"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        await send_message(
            chat_id,
            "🔄 **بازنشانی متون برندینگ به پیش‌فرض**\n\n"
            "⚠️ **هشدار!**\n"
            "همه متون شخصی‌سازی‌شده به مقادیر پیش‌فرض بازنشانی می‌شوند.\n"
            "این عملیات قابل بازگشت نیست.\n\n"
            "آیا مطمئن هستید؟",
            branding_confirm_keyboard()
        )
        return True
    except Exception as e:
        log_callback_error(f"Error in handle_branding_reset: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در نمایش بازنشانی.")
        return True


async def handle_branding_reset_confirm(chat_id: int, user_id: int) -> bool:
    """اجرای بازنشانی متون به پیش‌فرض"""
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # حذف همه تنظیمات برندینگ از دیتابیس
        for key in DEFAULT_BRANDING.keys():
            try:
                # تنظیم به None یا حذف از دیتابیس (در صورت وجود تابع delete_setting)
                # در اینجا با set_setting(key, None) مقدار را null می‌کنیم
                set_setting(key, None)
            except Exception as e:
                log_database_error(f"Error resetting branding key {key}: {str(e)}", traceback=traceback.format_exc())

        await send_message(
            chat_id,
            "✅ همه متون برندینگ با موفقیت به مقادیر پیش‌فرض بازنشانی شدند.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به برندینگ", "callback_data": "admin_branding"}]]}
        )
        return True
    except Exception as e:
        log_callback_error(f"Error in handle_branding_reset_confirm: {str(e)}", traceback=traceback.format_exc(), user_id=user_id, chat_id=chat_id)
        await send_message(chat_id, "❌ خطا در بازنشانی برندینگ.")
        return True


# ==================== صادر کردن ====================

__all__ = [
    'get_branded_text',
    'get_welcome_text',
    'get_main_menu_title',
    'get_admin_title',
    'get_order_success_text',
    'get_payment_success_text',
    'get_invalid_option_text',
    'get_error_message_text',
    'get_footer_text',
    'handle_branding',
    'handle_branding_view',
    'handle_branding_edit',
    'handle_branding_edit_field',
    'handle_branding_save',
    'handle_branding_reset',
    'handle_branding_reset_confirm',
]