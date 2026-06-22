# texts.py
# مدیریت متون پویا، تصادفی و پاسخ‌های متنوع برای بهبود UX/UI
# شامل: پیام‌های خوش‌آمدگویی، خطا، تأیید، راهنما و پاسخ‌های تصادفی

import random
from typing import List, Dict, Optional, Callable
from datetime import datetime
from logger_config import logger


# ============================================================
# متون پویا برای بخش‌های مختلف
# ============================================================

class DynamicTexts:
    """مدیریت متون پویا و تصادفی"""
    
    # ========== پیام‌های خوش‌آمدگویی (تصادفی) ==========
    WELCOME_MESSAGES = [
        "👋 به ربات خوش آمدید! امیدواریم بهترین تجربه را داشته باشید.",
        "🌟 خوش اومدید! اینجا می‌تونید انواع خدمات رو ثبت کنید.",
        "🤗 سلام! خوشحالیم که به جمع ما پیوستید.",
        "🌈 به خانواده بزرگ ما خوش آمدید! منتظر شما هستیم.",
        "✨ سلام! آماده‌اید تا از خدمات ما استفاده کنید؟",
        "🎉 خوش آمدید! با ما همراه باشید.",
        "🌺 سلام! امیدواریم روز خوبی داشته باشید.",
        "💫 خوش اومدید! هر سوالی دارید، با ما در میان بگذارید.",
    ]
    
    # ========== پیام‌های خطا (تصادفی) ==========
    ERROR_MESSAGES = [
        "❌ خطای داخلی رخ داده است. لطفاً دوباره تلاش کنید.",
        "⚠️ مشکلی پیش آمد! لطفاً چند لحظه دیگر دوباره امتحان کنید.",
        "🔴 خطا! تیم فنی در حال بررسی هستند.",
        "😕 متأسفانه خطایی رخ داد. دوباره تلاش کنید.",
        "🚨 خطای سیستمی! لطفاً با پشتیبانی تماس بگیرید.",
    ]
    
    # ========== پیام‌های تأیید (تصادفی) ==========
    SUCCESS_MESSAGES = [
        "✅ عملیات با موفقیت انجام شد! 🎉",
        "🌟 عالی! درخواست شما ثبت شد.",
        "👍 انجام شد! منتظر تأیید باشید.",
        "💪 موفق! به زودی با شما تماس می‌گیریم.",
        "✨ کار شما انجام شد! خوشحالیم که همراه ما هستید.",
    ]
    
    # ========== پیام‌های ثبت سفارش (تصادفی) ==========
    ORDER_SUCCESS_MESSAGES = [
        "✅ درخواست شما ثبت شد.\n🙏 به زودی تماس می‌گیریم.",
        "🎉 سفارش شما با موفقیت ثبت شد! منتظر تماس ما باشید.",
        "📋 سفارش ثبت شد. تیم ما در اسرع وقت با شما تماس می‌گیرد.",
        "✅ ثبت شد! کد پیگیری شما به زودی ارسال می‌شود.",
        "🌟 سفارش شما دریافت شد. از اعتماد شما سپاسگزاریم.",
    ]
    
    # ========== پیام‌های پرداخت موفق (تصادفی) ==========
    PAYMENT_SUCCESS_MESSAGES = [
        "✅ پرداخت موفق و ثبت سفارش.\n🙏 از شما متشکریم.",
        "💰 پرداخت شما با موفقیت انجام شد! سفارش ثبت شد.",
        "🎉 پرداخت موفق! سفارش شما در صف پردازش قرار گرفت.",
        "✅ پرداخت تأیید شد. از شما سپاسگزاریم.",
        "💳 پرداخت انجام شد. کد رهگیری برای شما ارسال می‌شود.",
    ]
    
    # ========== پیام‌های گزینه نامعتبر (تصادفی) ==========
    INVALID_OPTION_MESSAGES = [
        "⚠️ گزینه نامعتبر است. لطفاً از دکمه‌های منو استفاده کنید.",
        "❌ متأسفم! این گزینه موجود نیست.",
        "🤔 گزینه‌ای که انتخاب کردید معتبر نیست. دوباره تلاش کنید.",
        "⚠️ لطفاً یکی از گزینه‌های موجود را انتخاب کنید.",
    ]
    
    # ========== پیام‌های زمان انتظار (تصادفی) ==========
    WAITING_MESSAGES = [
        "⏳ لطفاً چند لحظه صبر کنید...",
        "🔄 در حال پردازش... کمی صبر کنید.",
        "⏰ در حال انجام عملیات... لطفاً شکیبا باشید.",
        "⚙️ پردازش... به زودی نتیجه را مشاهده می‌کنید.",
    ]
    
    # ========== پیام‌های پایان کار (تصادفی) ==========
    GOODBYE_MESSAGES = [
        "👋 خداحافظ! امیدواریم دوباره ببینمتون.",
        "🌟 روز خوبی داشته باشید! به امید دیدار مجدد.",
        "🤗 خوشحال بودیم که همراه ما بودید.",
        "💫 خدا نگهدار! منتظر شما هستیم.",
        "🌺 امیدواریم تجربه خوبی داشتید. باز هم منتظریم.",
    ]
    
    # ========== پیام‌های راهنما (تصادفی) ==========
    HELP_MESSAGES = [
        "❓ راهنمای ربات:\nبرای شروع، یکی از گزینه‌های منو را انتخاب کنید.",
        "📖 راهنما:\nبا انتخاب هر گزینه، مراحل مربوطه توضیح داده می‌شود.",
        "💡 نکته:\nهمیشه می‌توانید از دکمه «راهنما» برای دریافت راهنمایی استفاده کنید.",
    ]
    
    # ========== پیام‌های تشکر (تصادفی) ==========
    THANK_YOU_MESSAGES = [
        "🙏 از شما سپاسگزاریم.",
        "🤗 ممنون از اعتماد شما.",
        "🌟 از اینکه همراه ما هستید، متشکریم.",
        "💪 انرژی مثبت شما باعث پیشرفت ماست. سپاسگزاریم.",
    ]
    
    # ========== پیام‌های خوش‌آمدگویی روزانه ==========
    DAY_GREETINGS = {
        'morning': "🌅 صبح بخیر! روز خوبی داشته باشید.",
        'afternoon': "☀️ ظهر بخیر! امیدواریم روز پرانرژی‌ای داشته باشید.",
        'evening': "🌇 عصر بخیر! خسته نباشید.",
        'night': "🌙 شب بخیر! آرامش و شادی در انتظار شماست.",
    }
    
    # ========== پیام‌های فصلی ==========
    SEASON_GREETINGS = {
        'spring': "🌸 بهار زیباست، مثل حضور شما!",
        'summer': "☀️ تابستان گرم، با انرژی مثبت شما.",
        'autumn': "🍂 پاییز رنگارنگ، مثل روزهای خوب.",
        'winter': "❄️ زمستان سرد، اما دل‌های ما گرم.",
    }
    
    @classmethod
    def get_random(cls, message_list: List[str]) -> str:
        """دریافت یک پیام تصادفی از لیست"""
        if not message_list:
            return ""
        return random.choice(message_list)
    
    @classmethod
    def get_welcome(cls) -> str:
        """دریافت پیام خوش‌آمدگویی تصادفی"""
        # ترکیب با پیام روزانه
        time_greeting = cls.get_time_greeting()
        random_welcome = cls.get_random(cls.WELCOME_MESSAGES)
        return f"{time_greeting}\n\n{random_welcome}"
    
    @classmethod
    def get_time_greeting(cls) -> str:
        """دریافت پیام بر اساس زمان روز"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return cls.DAY_GREETINGS['morning']
        elif 12 <= hour < 17:
            return cls.DAY_GREETINGS['afternoon']
        elif 17 <= hour < 21:
            return cls.DAY_GREETINGS['evening']
        else:
            return cls.DAY_GREETINGS['night']
    
    @classmethod
    def get_season_greeting(cls) -> str:
        """دریافت پیام بر اساس فصل"""
        month = datetime.now().month
        if 3 <= month <= 5:
            return cls.SEASON_GREETINGS['spring']
        elif 6 <= month <= 8:
            return cls.SEASON_GREETINGS['summer']
        elif 9 <= month <= 11:
            return cls.SEASON_GREETINGS['autumn']
        else:
            return cls.SEASON_GREETINGS['winter']
    
    @classmethod
    def get_error(cls) -> str:
        """دریافت پیام خطا تصادفی"""
        return cls.get_random(cls.ERROR_MESSAGES)
    
    @classmethod
    def get_success(cls) -> str:
        """دریافت پیام موفقیت تصادفی"""
        return cls.get_random(cls.SUCCESS_MESSAGES)
    
    @classmethod
    def get_order_success(cls) -> str:
        """دریافت پیام ثبت سفارش تصادفی"""
        return cls.get_random(cls.ORDER_SUCCESS_MESSAGES)
    
    @classmethod
    def get_payment_success(cls) -> str:
        """دریافت پیام پرداخت موفق تصادفی"""
        return cls.get_random(cls.PAYMENT_SUCCESS_MESSAGES)
    
    @classmethod
    def get_invalid_option(cls) -> str:
        """دریافت پیام گزینه نامعتبر تصادفی"""
        return cls.get_random(cls.INVALID_OPTION_MESSAGES)
    
    @classmethod
    def get_waiting(cls) -> str:
        """دریافت پیام زمان انتظار تصادفی"""
        return cls.get_random(cls.WAITING_MESSAGES)
    
    @classmethod
    def get_goodbye(cls) -> str:
        """دریافت پیام خداحافظی تصادفی"""
        return cls.get_random(cls.GOODBYE_MESSAGES)
    
    @classmethod
    def get_help(cls) -> str:
        """دریافت پیام راهنما تصادفی"""
        return cls.get_random(cls.HELP_MESSAGES)
    
    @classmethod
    def get_thank_you(cls) -> str:
        """دریافت پیام تشکر تصادفی"""
        return cls.get_random(cls.THANK_YOU_MESSAGES)
    
    @classmethod
    def get_full_welcome(cls) -> str:
        """دریافت پیام خوش‌آمدگویی کامل (با ترکیب چند پیام)"""
        return (
            f"{cls.get_time_greeting()}\n\n"
            f"{cls.get_random(cls.WELCOME_MESSAGES)}\n\n"
            f"{cls.get_season_greeting()}\n\n"
            f"🌟 برای شروع، یکی از گزینه‌های منو را انتخاب کنید."
        )
    
    @classmethod
    def get_random_with_context(cls, messages: List[str], context: str = "") -> str:
        """
        دریافت پیام تصادفی با زمینه (context)
        
        پارامترها:
            messages: لیست پیام‌ها
            context: زمینه (برای اضافه کردن به پیام)
        """
        message = cls.get_random(messages)
        if context:
            return f"{context}\n\n{message}"
        return message


# ============================================================
# کلاس TextManager برای مدیریت متن‌های کاربر
# ============================================================

class TextManager:
    """مدیریت متن‌های کاربران (با قابلیت ذخیره‌سازی)"""
    
    def __init__(self):
        self._user_texts = {}  # {user_id: {key: value}}
    
    def set_user_text(self, user_id: int, key: str, value: str) -> None:
        """ذخیره متن برای یک کاربر"""
        if user_id not in self._user_texts:
            self._user_texts[user_id] = {}
        self._user_texts[user_id][key] = value
    
    def get_user_text(self, user_id: int, key: str, default: str = None) -> Optional[str]:
        """دریافت متن ذخیره‌شده برای یک کاربر"""
        if user_id in self._user_texts:
            return self._user_texts[user_id].get(key, default)
        return default
    
    def clear_user_texts(self, user_id: int) -> None:
        """پاک کردن تمام متن‌های ذخیره‌شده برای یک کاربر"""
        if user_id in self._user_texts:
            self._user_texts[user_id] = {}
    
    def get_text_with_fallback(self, user_id: int, key: str, 
                               fallback_texts: List[str], default: str = None) -> str:
        """
        دریافت متن با اولویت: ۱- متن ذخیره‌شده کاربر، ۲- تصادفی از لیست، ۳- مقدار پیش‌فرض
        """
        # اول: متن ذخیره‌شده کاربر
        user_text = self.get_user_text(user_id, key)
        if user_text:
            return user_text
        
        # دوم: تصادفی از لیست
        if fallback_texts:
            return random.choice(fallback_texts)
        
        # سوم: مقدار پیش‌فرض
        return default or ""


# ============================================================
# دکوراتورهای متون پویا
# ============================================================

def dynamic_message(message_func: Callable) -> Callable:
    """
    دکوراتور برای تبدیل تابع به تولیدکننده پیام پویا
    
    استفاده:
        @dynamic_message
        def get_welcome():
            return "متن خوش‌آمدگویی"
    """
    def wrapper(*args, **kwargs):
        try:
            result = message_func(*args, **kwargs)
            if isinstance(result, str):
                return result
            return str(result)
        except Exception as e:
            logger.error(f"Error in dynamic_message {message_func.__name__}: {e}")
            return "⚠️ خطا در تولید پیام."
    return wrapper


# ============================================================
# آبجکت سراسری
# ============================================================

_text_manager = None


def get_text_manager() -> TextManager:
    """دریافت آبجکت سراسری TextManager"""
    global _text_manager
    if _text_manager is None:
        _text_manager = TextManager()
    return _text_manager


# ============================================================
# توابع راحت برای استفاده در سایر بخش‌ها
# ============================================================

@dynamic_message
def get_random_welcome() -> str:
    return DynamicTexts.get_welcome()


@dynamic_message
def get_random_full_welcome() -> str:
    return DynamicTexts.get_full_welcome()


@dynamic_message
def get_random_error() -> str:
    return DynamicTexts.get_error()


@dynamic_message
def get_random_success() -> str:
    return DynamicTexts.get_success()


@dynamic_message
def get_random_order_success() -> str:
    return DynamicTexts.get_order_success()


@dynamic_message
def get_random_payment_success() -> str:
    return DynamicTexts.get_payment_success()


@dynamic_message
def get_random_invalid_option() -> str:
    return DynamicTexts.get_invalid_option()


@dynamic_message
def get_random_waiting() -> str:
    return DynamicTexts.get_waiting()


@dynamic_message
def get_random_goodbye() -> str:
    return DynamicTexts.get_goodbye()


@dynamic_message
def get_random_help() -> str:
    return DynamicTexts.get_help()


@dynamic_message
def get_random_thank_you() -> str:
    return DynamicTexts.get_thank_you()


@dynamic_message
def get_time_greeting() -> str:
    return DynamicTexts.get_time_greeting()


@dynamic_message
def get_season_greeting() -> str:
    return DynamicTexts.get_season_greeting()


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # کلاس اصلی
    'DynamicTexts',
    'TextManager',
    'get_text_manager',
    # توابع راحت
    'get_random_welcome',
    'get_random_full_welcome',
    'get_random_error',
    'get_random_success',
    'get_random_order_success',
    'get_random_payment_success',
    'get_random_invalid_option',
    'get_random_waiting',
    'get_random_goodbye',
    'get_random_help',
    'get_random_thank_you',
    'get_time_greeting',
    'get_season_greeting',
    # دکوراتور
    'dynamic_message',
]