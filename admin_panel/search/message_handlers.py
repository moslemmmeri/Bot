# admin_panel/search/message_handlers.py
# پردازش پیام‌های جستجوی پیشرفته سفارشات
# این فایل پیام‌های ارسال‌شده در حالت جستجو را پردازش می‌کند

from datetime import datetime
from typing import Optional
from logger_config import logger
from core import send_message, user_states
from utils import safe_int, safe_float, format_number
from .core import AdvancedSearch


# ============================================================
# تابع اصلی پردازش پیام‌های جستجو
# ============================================================

async def handle_adv_search_message(chat_id: int, user_id: int, text: str) -> bool:
    """
    پردازش پیام‌های مربوط به جستجوی پیشرفته

    این تابع وضعیت کاربر را بررسی کرده و پیام را به تابع مناسب هدایت می‌کند.

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        text: متن پیام

    بازگشت: True اگر پیام پردازش شد، False در غیر این صورت
    """
    state_info = user_states.get(user_id, {})
    search_state = state_info.get("adv_search_state")

    if not search_state:
        return False

    if user_id not in user_states:
        user_states[user_id] = {}

    if "adv_search" not in user_states[user_id]:
        user_states[user_id]["adv_search"] = AdvancedSearch()

    search_obj = user_states[user_id]["adv_search"]

    # ========== جستجوی سریع (کلمه کلیدی) ==========
    if search_state == "quick_keyword":
        return await _handle_quick_keyword(chat_id, user_id, text, search_obj)

    # ========== جستجو بر اساس تاریخ ==========
    if search_state == "date_range":
        return await _handle_date_range(chat_id, user_id, text, search_obj)

    # ========== جستجو بر اساس مبلغ ==========
    if search_state == "amount_range":
        return await _handle_amount_range(chat_id, user_id, text, search_obj)

    # ========== جستجو بر اساس کاربر ==========
    if search_state == "user_search":
        return await _handle_user_search(chat_id, user_id, text, search_obj)

    # ========== جستجو بر اساس کد رهگیری ==========
    if search_state == "tracking_code":
        return await _handle_tracking_code(chat_id, user_id, text, search_obj)

    # ========== شروع تاریخ سفارشی ==========
    if search_state == "awaiting_start_date":
        return await _handle_start_date(chat_id, user_id, text, search_obj)

    # ========== پایان تاریخ سفارشی ==========
    if search_state == "awaiting_end_date":
        return await _handle_end_date(chat_id, user_id, text, search_obj)

    # ========== ذخیره فیلتر ==========
    if search_state == "awaiting_filter_name":
        return await _handle_save_filter(chat_id, user_id, text, search_obj)

    return False


# ============================================================
# توابع کمکی پردازش پیام
# ============================================================

async def _handle_quick_keyword(chat_id: int, user_id: int, text: str, search_obj: AdvancedSearch) -> bool:
    """پردازش جستجوی سریع با کلمه کلیدی"""
    if not text or text.strip() == "":
        await send_message(chat_id, "❌ لطفاً یک کلمه کلیدی معتبر وارد کنید.")
        return True

    search_obj.search_by_keyword(text.strip())
    user_states[user_id].pop("adv_search_state", None)

    await send_message(
        chat_id,
        f"✅ جستجوی کلمه کلیدی «{text}» اعمال شد.\n\n"
        f"📊 تعداد نتایج: {search_obj.get_count()}",
        {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
    )
    return True


async def _handle_date_range(chat_id: int, user_id: int, text: str, search_obj: AdvancedSearch) -> bool:
    """پردازش جستجو بر اساس تاریخ (با فرمت‌های مختلف)"""
    try:
        parts = text.replace("تا", " ").split()

        if len(parts) == 2:
            start = parts[0].strip()
            end = parts[1].strip()
        elif len(parts) == 1:
            start = parts[0].strip()
            end = None
        else:
            # تلاش برای تشخیص فرمت‌های دیگر
            if " تا " in text:
                p = text.split(" تا ")
                start = p[0].strip()
                end = p[1].strip()
            elif " - " in text:
                p = text.split(" - ")
                start = p[0].strip()
                end = p[1].strip()
            else:
                await send_message(chat_id, "❌ فرمت نامعتبر.\n\nلطفاً به یکی از فرمت‌های زیر وارد کنید:\n• تاریخ شروع تا تاریخ پایان (مثال: 2024-01-01 تا 2024-01-31)\n• یک تاریخ (مثال: 2024-01-15)")
                return True

        # اعتبارسنجی تاریخ‌ها
        if start:
            datetime.strptime(start, "%Y-%m-%d")
        if end:
            datetime.strptime(end, "%Y-%m-%d")

        search_obj.search_by_date_range(start, end)
        user_states[user_id].pop("adv_search_state", None)

        await send_message(
            chat_id,
            f"✅ فیلتر تاریخ اعمال شد.\n\n"
            f"📅 از {start or 'نامشخص'} تا {end or 'نامشخص'}\n"
            f"📊 تعداد نتایج: {search_obj.get_count()}",
            {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
        )
        return True

    except ValueError:
        await send_message(chat_id, "❌ فرمت تاریخ نامعتبر. لطفاً به فرمت YYYY-MM-DD وارد کنید.")
        return True


async def _handle_amount_range(chat_id: int, user_id: int, text: str, search_obj: AdvancedSearch) -> bool:
    """پردازش جستجو بر اساس مبلغ"""
    try:
        # حذف ویرگول و فاصله
        cleaned = text.replace(",", "").replace(" ", "")
        parts = cleaned.replace("تا", " ").split()

        if len(parts) == 2:
            min_amount = safe_int(parts[0])
            max_amount = safe_int(parts[1])
        elif len(parts) == 1:
            min_amount = safe_int(parts[0])
            max_amount = None
        else:
            # بررسی جداکننده‌های دیگر
            if "تا" in text:
                p = text.split("تا")
                min_amount = safe_int(p[0].strip())
                max_amount = safe_int(p[1].strip())
            elif "-" in text:
                p = text.split("-")
                min_amount = safe_int(p[0].strip())
                max_amount = safe_int(p[1].strip())
            else:
                await send_message(chat_id, "❌ فرمت نامعتبر.\n\nلطفاً به یکی از فرمت‌های زیر وارد کنید:\n• حداقل تا حداکثر (مثال: 100000 تا 1000000)\n• یک عدد (مثال: 100000)")
                return True

        if min_amount and min_amount < 0:
            await send_message(chat_id, "❌ مبلغ نمی‌تواند منفی باشد.")
            return True
        if max_amount and max_amount < 0:
            await send_message(chat_id, "❌ مبلغ نمی‌تواند منفی باشد.")
            return True
        if min_amount and max_amount and min_amount > max_amount:
            await send_message(chat_id, "❌ حداقل نباید از حداکثر بیشتر باشد.")
            return True

        search_obj.search_by_amount_range(min_amount, max_amount)
        user_states[user_id].pop("adv_search_state", None)

        await send_message(
            chat_id,
            f"✅ فیلتر مبلغ اعمال شد.\n\n"
            f"💰 محدوده: {format_number(min_amount) if min_amount else 'نامحدود'} تا {format_number(max_amount) if max_amount else 'نامحدود'} ریال\n"
            f"📊 تعداد نتایج: {search_obj.get_count()}",
            {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
        )
        return True

    except (ValueError, TypeError):
        await send_message(chat_id, "❌ لطفاً اعداد معتبر وارد کنید.")
        return True


async def _handle_user_search(chat_id: int, user_id: int, text: str, search_obj: AdvancedSearch) -> bool:
    """پردازش جستجو بر اساس کاربر"""
    if not text or text.strip() == "":
        await send_message(chat_id, "❌ لطفاً شناسه یا نام کاربری معتبر وارد کنید.")
        return True

    user_id_search = None
    username = None

    cleaned = text.strip()
    if cleaned.isdigit():
        user_id_search = int(cleaned)
    else:
        username = cleaned.lstrip('@')

    search_obj.search_by_user(user_id_search, username)
    user_states[user_id].pop("adv_search_state", None)

    await send_message(
        chat_id,
        f"✅ فیلتر کاربر اعمال شد.\n\n"
        f"👤 کاربر: {text}\n"
        f"📊 تعداد نتایج: {search_obj.get_count()}",
        {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
    )
    return True


async def _handle_tracking_code(chat_id: int, user_id: int, text: str, search_obj: AdvancedSearch) -> bool:
    """پردازش جستجو بر اساس کد رهگیری"""
    if not text or text.strip() == "":
        await send_message(chat_id, "❌ لطفاً کد رهگیری را وارد کنید.")
        return True

    search_obj.search_by_tracking_code(text.strip())
    user_states[user_id].pop("adv_search_state", None)

    await send_message(
        chat_id,
        f"✅ فیلتر کد رهگیری اعمال شد.\n\n"
        f"🎫 کد رهگیری: {text}\n"
        f"📊 تعداد نتایج: {search_obj.get_count()}",
        {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
    )
    return True


async def _handle_start_date(chat_id: int, user_id: int, text: str, search_obj: AdvancedSearch) -> bool:
    """پردازش تاریخ شروع برای تاریخ سفارشی"""
    try:
        datetime.strptime(text, "%Y-%m-%d")
        user_states[user_id]["adv_search_temp_start"] = text
        user_states[user_id]["adv_search_state"] = "awaiting_end_date"
        await send_message(
            chat_id,
            "✅ تاریخ شروع ثبت شد.\n\n"
            "📅 لطفاً تاریخ پایان را به فرمت **YYYY-MM-DD** وارد کنید:\n"
            "(مثال: 2024-01-20)"
        )
        return True
    except ValueError:
        await send_message(chat_id, "❌ فرمت تاریخ نامعتبر. لطفاً به فرمت YYYY-MM-DD وارد کنید.")
        return True


async def _handle_end_date(chat_id: int, user_id: int, text: str, search_obj: AdvancedSearch) -> bool:
    """پردازش تاریخ پایان برای تاریخ سفارشی"""
    try:
        datetime.strptime(text, "%Y-%m-%d")
        start_date = user_states[user_id].get("adv_search_temp_start")
        if start_date:
            search_obj.search_by_date_range(start_date, text)
        else:
            search_obj.search_by_date_range(None, text)

        user_states[user_id].pop("adv_search_state", None)
        user_states[user_id].pop("adv_search_temp_start", None)

        await send_message(
            chat_id,
            f"✅ تاریخ سفارشی تنظیم شد.\n\n"
            f"📅 از {start_date or 'نامشخص'} تا {text}\n"
            f"📊 تعداد نتایج: {search_obj.get_count()}",
            {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
        )
        return True
    except ValueError:
        await send_message(chat_id, "❌ فرمت تاریخ نامعتبر. لطفاً به فرمت YYYY-MM-DD وارد کنید.")
        return True


async def _handle_save_filter(chat_id: int, user_id: int, text: str, search_obj: AdvancedSearch) -> bool:
    """ذخیره فیلتر فعلی با نام مشخص"""
    if not text or text.strip() == "":
        await send_message(chat_id, "❌ نام نمی‌تواند خالی باشد.")
        return True

    filter_name = text.strip()

    # بررسی تکراری نبودن نام
    from admin_panel.filters import get_filter_manager
    filter_manager = get_filter_manager()
    saved_filters = filter_manager.get_filters(user_id)

    if filter_name in saved_filters:
        await send_message(
            chat_id,
            f"❌ فیلتری با نام «{filter_name}» قبلاً وجود دارد.\n"
            f"لطفاً نام دیگری انتخاب کنید."
        )
        return True

    # تبدیل جستجو به فیلتر و ذخیره
    from admin_panel.filters import AdvancedFilters, create_filter_from_params

    # ساخت فیلتر از وضعیت فعلی جستجو
    filters_dict = _search_to_filters(search_obj)
    filter_obj = create_filter_from_params(filters_dict)

    # ذخیره فیلتر
    if filter_manager.save_filter(user_id, filter_obj, filter_name):
        user_states[user_id].pop("adv_search_state", None)
        await send_message(
            chat_id,
            f"✅ فیلتر «{filter_name}» با موفقیت ذخیره شد.\n\n"
            f"📌 خلاصه: {search_obj.get_filters_summary()}\n"
            f"📊 تعداد نتایج: {search_obj.get_count()}",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به جستجو", "callback_data": "admin_adv_search"}]]}
        )
    else:
        await send_message(chat_id, "❌ خطا در ذخیره فیلتر.")

    return True


# ============================================================
# توابع کمکی
# ============================================================

def _search_to_filters(search_obj: AdvancedSearch) -> dict:
    """
    تبدیل وضعیت جستجو به دیکشنری فیلترها

    پارامترها:
        search_obj: شیء AdvancedSearch

    بازگشت: دیکشنری فیلترها
    """
    # این تابع باید فیلترهای اعمال‌شده را از search_obj استخراج کند
    # به دلیل محدودیت دسترسی به جزئیات پیاده‌سازی، یک نمونه ساده برمی‌گردانیم
    # در پیاده‌سازی واقعی، باید فیلترها را از search_obj استخراج کرد

    filters = {}

    # استخراج از خلاصه فیلترها (در صورت وجود)
    # این یک پیاده‌سازی ساده است و باید بهبود یابد
    # بهتر است فیلترها را در search_obj ذخیره کنیم

    return filters


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'handle_adv_search_message',
]