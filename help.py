# help.py
# سیستم راهنمای کاربر برای ربات

import traceback
from typing import Dict, Optional
from logger_config import logger
from core import send_message, get_main_menu_with_admin
from keyboards import main_menu_keyboard
from utils.error_handler import log_general_error

# ========== ایمپورت‌های جدید از texts.py ==========
from texts import (
    get_random_welcome,
    get_random_error,
    get_random_success,
    get_random_help,
    get_random_waiting,
    get_random_goodbye,
    get_random_thank_you,
    get_time_greeting,
    get_season_greeting,
)


# ============================================================
# متون راهنما (با ترکیب با texts.py برای تنوع بیشتر)
# ============================================================

# بخش‌های اصلی راهنما (متون اصلی ثابت هستند اما با توابع texts.py ترکیب می‌شوند)
HELP_SECTIONS = {
    'main': {
        'title': '🤖 راهنمای استفاده از ربات',
        'description': (
            'سلام! 👋\n\n'
            'این ربات به شما امکان می‌دهد تا انواع خدمات را به‌صورت آنلاین ثبت کنید.\n\n'
            '📌 **نحوه استفاده:**\n'
            '• از دکمه‌های منو برای انتخاب سرویس مورد نظر استفاده کنید.\n'
            '• پس از انتخاب، سوالات مربوطه را پاسخ دهید.\n'
            '• در صورت نیاز به پرداخت، فاکتور برای شما ارسال می‌شود.\n'
            '• پس از تکمیل، سفارش شما ثبت و به ادمین ارسال می‌شود.\n\n'
            '📌 **خدمات موجود:**\n'
            '• خدمات مالیاتی\n'
            '• خدمات خودرو\n'
            '• خدمات بیمه\n'
            '• خدمات قضایی\n'
            '• خدمات بانکی\n'
            '• و بسیاری دیگر...\n\n'
            'برای شروع، یکی از گزینه‌های منو را انتخاب کنید.'
        )
    },
    'commands': {
        'title': '📋 دستورات',
        'description': (
            '📌 **دستورات موجود:**\n\n'
            '• /start - شروع مجدد ربات و نمایش منوی اصلی\n'
            '• /help - نمایش این راهنما\n'
            '• /profile - مشاهده پروفایل و تاریخچه سفارشات\n'
            '• /cancel - لغو عملیات جاری (در صورت وجود)\n\n'
            '📌 **دستورات مدیریت (فقط ادمین):**\n'
            '• /admin - ورود به پنل مدیریت (فقط ادمین‌ها)\n'
            '• /stats - مشاهده آمار کلی ربات (فقط OWNER)'
        )
    },
    'payment': {
        'title': '💰 راهنمای پرداخت',
        'description': (
            '💰 **نحوه پرداخت:**\n\n'
            'پس از تکمیل فرم، فاکتور پرداخت برای شما ارسال می‌شود.\n'
            'مراحل پرداخت:\n'
            '1. روی دکمه «پرداخت» کلیک کنید.\n'
            '2. مبلغ مورد نظر را تأیید کنید.\n'
            '3. پرداخت را از طریق درگاه انجام دهید.\n'
            '4. پس از پرداخت موفق، سفارش شما تأیید می‌شود.\n\n'
            '📌 **نکته:**\n'
            '• در صورت بروز مشکل در پرداخت، با پشتیبانی تماس بگیرید.\n'
            '• کد رهگیری پرداخت پس از تأیید به شما نمایش داده می‌شود.'
        )
    },
    'support': {
        'title': '📞 ارتباط با پشتیبانی',
        'description': (
            '📞 **ارتباط با پشتیبانی:**\n\n'
            'در صورت نیاز به راهنمایی یا بروز مشکل، می‌توانید با ادمین ربات در ارتباط باشید.\n\n'
            '📌 **راه‌های ارتباطی:**\n'
            '• ارسال پیام به ادمین: از طریق گزینه «ارسال پیام به ادمین» در منوی اصلی\n'
            '• ایمیل: support@example.com\n'
            '• تلفن: ۰۲۱-XXXX-XXXX\n\n'
            'ساعات پاسخگویی: همه روزه از ۹ صبح تا ۹ شب'
        )
    },
    'faq': {
        'title': '❓ سوالات متداول',
        'description': (
            '❓ **سوالات متداول:**\n\n'
            '**۱. چگونه سرویس جدید ثبت کنم؟**\n'
            'از منوی اصلی، سرویس مورد نظر را انتخاب کنید و مراحل را طی کنید.\n\n'
            '**۲. آیا اطلاعات من محفوظ است؟**\n'
            'بله، تمام اطلاعات شما با رعایت حریم خصوصی ذخیره می‌شود.\n\n'
            '**۳. چقدر طول می‌کشد تا سفارش من پردازش شود؟**\n'
            'معمولاً ظرف ۲۴ ساعت کاری، سفارش شما بررسی و پردازش می‌شود.\n\n'
            '**۴. چگونه می‌توانم سفارش خود را لغو کنم؟**\n'
            'در بخش پروفایل، سفارشات در انتظار پرداخت را می‌توانید لغو کنید.\n\n'
            '**۵. آیا امکان پیگیری سفارش وجود دارد؟**\n'
            'بله، در بخش پروفایل می‌توانید وضعیت تمام سفارشات خود را مشاهده کنید.'
        )
    }
}


# ============================================================
# کیبوردهای راهنما (با پیام‌های پویا)
# ============================================================

def help_main_keyboard() -> Dict:
    """کیبورد اصلی راهنما"""
    return {
        "inline_keyboard": [
            [{"text": "📋 دستورات", "callback_data": "help_commands"}],
            [{"text": "💰 راهنمای پرداخت", "callback_data": "help_payment"}],
            [{"text": "📞 پشتیبانی", "callback_data": "help_support"}],
            [{"text": "❓ سوالات متداول", "callback_data": "help_faq"}],
            [{"text": "🔙 بازگشت به منو", "callback_data": "back_main"}]
        ]
    }


def help_back_keyboard(back_to: str = "help_main") -> Dict:
    """کیبورد بازگشت از بخش‌های راهنما"""
    return {
        "inline_keyboard": [
            [{"text": "🔙 بازگشت به راهنما", "callback_data": back_to}],
            [{"text": "🔙 بازگشت به منو", "callback_data": "back_main"}]
        ]
    }


# ============================================================
# توابع نمایش راهنما (با استفاده از texts.py)
# ============================================================

async def show_help(chat_id: int, section: str = "main") -> bool:
    """
    نمایش راهنمای کاربر
    
    پارامترها:
        chat_id: شناسه چت
        section: بخش راهنما (main, commands, payment, support, faq)
    
    بازگشت: True در صورت موفقیت
    """
    try:
        if section in HELP_SECTIONS:
            section_data = HELP_SECTIONS[section]
            keyboard = help_main_keyboard() if section == "main" else help_back_keyboard()
            
            # ========== ترکیب متن راهنما با پیام‌های پویا ==========
            # افزودن یک پیام تصادفی به ابتدای متن راهنما (برای تنوع)
            random_help = get_random_help()
            
            # افزودن پیام خوش‌آمدگویی تصادفی (اگر بخش اصلی باشد)
            if section == "main":
                welcome_msg = get_random_welcome()
                full_text = f"{welcome_msg}\n\n{section_data['title']}\n\n{section_data['description']}"
            else:
                full_text = f"{random_help}\n\n{section_data['title']}\n\n{section_data['description']}"
            
            await send_message(
                chat_id,
                full_text,
                keyboard
            )
        else:
            # بخش نامعتبر - نمایش اصلی
            await show_help(chat_id, "main")
        
        return True
        
    except Exception as e:
        log_general_error(
            f"Error in show_help: {str(e)}",
            traceback=traceback.format_exc(),
            chat_id=chat_id
        )
        # ========== استفاده از پیام خطای تصادفی ==========
        await send_message(chat_id, get_random_error() + "\n\n❌ خطا در نمایش راهنما.")
        return False


async def show_help_section(chat_id: int, section: str) -> bool:
    """نمایش یک بخش خاص از راهنما (برای کالبک‌ها)"""
    return await show_help(chat_id, section)


# ============================================================
# پردازش کالبک‌های راهنما
# ============================================================

async def handle_help_callback(update: Dict) -> bool:
    """
    پردازش کالبک‌های مربوط به راهنما
    
    پارامترها:
        update: دیکشنری آپدیت
    
    بازگشت: True اگر کالبک پردازش شد
    """
    try:
        cb = update.get("callback_query")
        if not cb:
            return False
        
        data = cb.get("data")
        user_id = cb.get("from", {}).get("id")
        chat_id = cb.get("message", {}).get("chat", {}).get("id")
        
        if not data or not chat_id:
            return False
        
        # ========== نمایش بخش‌های راهنما ==========
        if data.startswith("help_"):
            section = data.split("_", 1)[1]  # help_main, help_commands, ...
            await show_help_section(chat_id, section)
            return True
        
        return False
        
    except Exception as e:
        log_general_error(
            f"Error in handle_help_callback: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id if 'user_id' in locals() else None,
            chat_id=chat_id if 'chat_id' in locals() else None
        )
        return False


# ============================================================
# دستور /help
# ============================================================

async def handle_help_command(chat_id: int) -> bool:
    """پردازش دستور /help"""
    return await show_help(chat_id, "main")


# ============================================================
# تابع کمکی برای افزودن دکمه راهنما به منوها
# ============================================================

def add_help_button_to_menu(keyboard: Dict) -> Dict:
    """
    افزودن دکمه راهنما به منو
    
    پارامترها:
        keyboard: کیبورد موجود
    
    بازگشت: کیبورد با دکمه راهنما
    """
    if "inline_keyboard" in keyboard:
        # بررسی اینکه آیا دکمه راهنما وجود دارد
        for row in keyboard["inline_keyboard"]:
            for btn in row:
                if btn.get("callback_data") == "help_main":
                    return keyboard
        
        # افزودن دکمه راهنما
        keyboard["inline_keyboard"].append([
            {"text": "❓ راهنما", "callback_data": "help_main"}
        ])
    
    return keyboard


# ============================================================
# تابع کمکی برای دریافت پیام راهنمای تصادفی (برای استفاده در سایر بخش‌ها)
# ============================================================

def get_random_help_message() -> str:
    """دریافت یک پیام راهنمای تصادفی (برای استفاده در سایر بخش‌ها)"""
    return get_random_help()


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'show_help',
    'show_help_section',
    'handle_help_callback',
    'handle_help_command',
    'help_main_keyboard',
    'help_back_keyboard',
    'add_help_button_to_menu',
    'HELP_SECTIONS',
    'get_random_help_message',
]