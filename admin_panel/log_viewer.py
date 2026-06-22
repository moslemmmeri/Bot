# admin_panel/log_viewer.py
# نمایش و مدیریت فایل لاگ (bot.log) در پنل ادمین
# فقط خطاهای ERROR و CRITICAL نمایش داده می‌شوند

import os
import traceback
from typing import List, Optional
from logger_config import logger
from core import send_message, OWNER_ID
from config import config
from utils.error_handler import log_general_error, log_security_error

LOG_FILE = config.LOG_FILE
MAX_LINES_TO_SHOW = 200  # حداکثر خطوط نمایش داده‌شده


def _read_error_logs(limit: int = MAX_LINES_TO_SHOW) -> List[str]:
    """
    خواندن فایل لاگ و استخراج فقط خطوط حاوی ERROR یا CRITICAL
    بازگشت: لیست خطوط خطا (آخرین‌ها)
    """
    if not os.path.exists(LOG_FILE):
        return ["❌ فایل لاگ وجود ندارد."]

    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # فیلتر خطوط حاوی ERROR یا CRITICAL (حساس به حروف بزرگ/کوچک نیست)
        error_lines = [
            line.strip()
            for line in lines
            if 'ERROR' in line.upper() or 'CRITICAL' in line.upper()
        ]

        # فقط تعداد محدودی از آخرین خطاها
        return error_lines[-limit:] if error_lines else ["✅ هیچ خطایی در لاگ‌ها یافت نشد."]

    except Exception as e:
        log_general_error(f"Error reading log file: {str(e)}", traceback=traceback.format_exc())
        return [f"❌ خطا در خواندن فایل لاگ: {str(e)}"]


def _clear_log_file() -> bool:
    """
    پاک کردن کامل فایل لاگ (حذف و ایجاد مجدد)
    بازگشت: True در صورت موفقیت
    """
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        # ایجاد فایل خالی جدید با همان نام
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("")  # فایل خالی
        logger.info(f"🗑️ فایل لاگ {LOG_FILE} توسط ادمین پاک شد.")
        return True
    except Exception as e:
        log_general_error(f"Error clearing log file: {str(e)}", traceback=traceback.format_exc())
        return False


# ==================== کیبوردها ====================

def log_viewer_main_keyboard() -> dict:
    """کیبورد اصلی بخش مشاهده لاگ"""
    return {
        "inline_keyboard": [
            [{"text": "📄 نمایش خطاهای اخیر", "callback_data": "admin_log_view"}],
            [{"text": "🗑️ پاک کردن فایل لاگ", "callback_data": "admin_log_clear"}],
            [{"text": "🔙 بازگشت به مدیریت خطاها", "callback_data": "admin_errors"}]
        ]
    }


def log_viewer_confirm_keyboard() -> dict:
    """کیبورد تأیید پاک کردن فایل لاگ"""
    return {
        "inline_keyboard": [
            [{"text": "⚠️ آیا از پاک کردن فایل لاگ مطمئن هستید؟"}],
            [{"text": "⚠️ این عمل غیرقابل بازگشت است!"}],
            [{"text": "✅ بله، پاک شود", "callback_data": "admin_log_clear_confirm"}],
            [{"text": "❌ انصراف", "callback_data": "admin_log_viewer"}]
        ]
    }


# ==================== هندلرهای اصلی ====================

async def handle_log_viewer(chat_id: int, user_id: int) -> bool:
    """نمایش منوی اصلی مدیریت لاگ فایل"""
    if user_id != OWNER_ID:
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True

    await send_message(
        chat_id,
        "📄 **مدیریت فایل لاگ (`bot.log`)**\n\n"
        "از این بخش می‌توانید:\n"
        "• خطاهای اخیر (ERROR و CRITICAL) را مشاهده کنید\n"
        "• فایل لاگ را به‌طور کامل پاک کنید\n\n"
        "📌 **توجه:** فقط خطاهای سطح ERROR و CRITICAL نمایش داده می‌شوند.",
        log_viewer_main_keyboard()
    )
    return True


async def handle_log_view(chat_id: int, user_id: int) -> bool:
    """نمایش خطاهای اخیر از فایل لاگ"""
    if user_id != OWNER_ID:
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True

    await send_message(chat_id, "⏳ در حال خواندن فایل لاگ...")

    error_lines = _read_error_logs(limit=MAX_LINES_TO_SHOW)

    if len(error_lines) == 1 and "✅ هیچ خطایی" in error_lines[0]:
        await send_message(chat_id, error_lines[0])
    else:
        # اگر تعداد خطاها زیاد است، پیام را به چند بخش تقسیم کنیم
        msg = "📄 **خطاهای اخیر (ERROR/CRITICAL) از `bot.log`**\n\n"
        msg += f"تعداد خطاهای نمایش‌داده‌شده: {len(error_lines)}\n"
        msg += "─" * 30 + "\n\n"

        # حداکثر ۴۰۰۰ کاراکتر در هر پیام
        chunks = []
        current_chunk = msg
        for line in error_lines:
            if len(current_chunk) + len(line) + 2 > 4000:
                chunks.append(current_chunk)
                current_chunk = ""
            current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

        for i, chunk in enumerate(chunks):
            if i == 0:
                await send_message(chat_id, chunk)
            else:
                await send_message(chat_id, chunk)

        # دکمه بازگشت
        await send_message(
            chat_id,
            "🔙 برای بازگشت به منوی مدیریت لاگ، روی دکمه زیر کلیک کنید:",
            {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "admin_log_viewer"}]]}
        )

    return True


async def handle_log_clear(chat_id: int, user_id: int) -> bool:
    """نمایش تأییدیه پاک کردن فایل لاگ"""
    if user_id != OWNER_ID:
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True

    # بررسی وجود فایل
    if not os.path.exists(LOG_FILE):
        await send_message(chat_id, "❌ فایل لاگ وجود ندارد یا قبلاً حذف شده است.")
        return True

    # نمایش اندازه فایل
    size_kb = os.path.getsize(LOG_FILE) // 1024
    await send_message(
        chat_id,
        f"🗑️ **پاک کردن فایل لاگ**\n\n"
        f"📁 نام فایل: `{LOG_FILE}`\n"
        f"📊 حجم فعلی: {size_kb} KB\n\n"
        f"⚠️ این عمل **غیرقابل بازگشت** است و تمام لاگ‌ها حذف می‌شوند.\n"
        f"آیا مطمئن هستید؟",
        log_viewer_confirm_keyboard()
    )
    return True


async def handle_log_clear_confirm(chat_id: int, user_id: int) -> bool:
    """اجرای پاک کردن فایل لاگ"""
    if user_id != OWNER_ID:
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True

    success = _clear_log_file()
    if success:
        await send_message(chat_id, "✅ فایل لاگ با موفقیت پاک شد.")
    else:
        await send_message(chat_id, "❌ خطا در پاک کردن فایل لاگ.")

    # بازگشت به منوی مدیریت لاگ
    await handle_log_viewer(chat_id, user_id)
    return True