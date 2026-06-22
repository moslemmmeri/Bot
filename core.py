# core.py
# توابع مشترک، تنظیمات و متغیرهای سراسری - نسخه اصلاح‌شده با استفاده از texts.py

import aiohttp
import asyncio
import json
import os
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List

from logger_config import logger, ContextLogger
from config import config
from utils.error_handler import (
    log_error as _log_error,
    log_database_error,
    log_api_error,
    log_callback_error,
    log_general_error as _log_general_error,
    log_payment_error,
    log_security_error,
    log_critical_error,
)
# ========== ایمپورت‌های جدید از texts.py ==========
from texts import (
    get_random_welcome,
    get_random_error,
    get_random_success,
    get_random_order_success,
    get_random_payment_success,
    get_random_invalid_option,
    get_random_help,
    get_random_waiting,
    get_random_goodbye,
    get_random_thank_you,
    get_time_greeting,
    get_season_greeting,
)


# ========== تنظیمات از config ==========
TOKEN = config.BOT_TOKEN
OWNER_ID = config.OWNER_ID
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}/"

PAYMENT_PROVIDER_TOKEN = config.PAYMENT_PROVIDER_TOKEN
DEFAULT_PRICE_AMOUNT = config.DEFAULT_PRICE_AMOUNT
DEFAULT_PRICE_LABEL = config.DEFAULT_PRICE_LABEL


# ========== وضعیت کاربران (دیکشنری معمولی - برای سازگاری با کدهای قدیمی) ==========
user_states = {}


# ============================================================
# توابع کمکی برای ثبت خطا (برای سازگاری با کدهای قدیمی که از core.log_error استفاده می‌کنند)
# ============================================================

def log_error(
    error_type: str,
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict] = None,
    traceback: Optional[str] = None,  # alias
) -> None:
    """ثبت خطا (Wrapper برای utils.error_handler.log_error)"""
    if traceback_str is None and traceback is not None:
        traceback_str = traceback
    _log_error(error_type, error_message, traceback_str, user_id, chat_id, data)


def log_general_error(
    error_message: str,
    traceback_str: Optional[str] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    data: Optional[Dict] = None,
    traceback: Optional[str] = None,  # alias
) -> None:
    """ثبت خطای عمومی (Wrapper)"""
    if traceback_str is None and traceback is not None:
        traceback_str = traceback
    _log_general_error(error_message, traceback_str, user_id, chat_id, data)


# ============================================================
# توابع برندینگ (اصلاح‌شده با استفاده از texts.py)
# ============================================================

def get_branded_text(key, default=None):
    """
    دریافت متن برندینگ از دیتابیس یا مقدار پیش‌فرض.
    در صورت نبود مقدار در دیتابیس، از texts.py برای برخی کلیدها استفاده می‌شود.
    """
    try:
        from database import get_setting
        value = get_setting(key)
        if value is not None and value != "":
            return value
    except Exception as e:
        logger.error(f"خطا در دریافت برندینگ برای کلید {key}: {e}")

    # اگر مقدار در دیتابیس نبود، از texts.py استفاده کن (برای برخی کلیدها)
    dynamic_functions = {
        'brand_welcome_text': get_random_welcome,
        'brand_error_message': get_random_error,
        'brand_order_success': get_random_order_success,
        'brand_payment_success': get_random_payment_success,
        'brand_invalid_option': get_random_invalid_option,
        'brand_help_text': get_random_help,
        'brand_waiting_text': get_random_waiting,
        'brand_goodbye_text': get_random_goodbye,
        'brand_thank_you_text': get_random_thank_you,
    }
    if key in dynamic_functions:
        return dynamic_functions[key]()

    # برای سایر کلیدها، از پیش‌فرض‌های ثابت استفاده کن
    defaults = {
        'brand_welcome_text': '👋 به ربات خوش آمدید.\n🌟 لطفاً یکی از گزینه‌ها را انتخاب کنید:',
        'brand_main_menu_title': '🔙 منوی اصلی:',
        'brand_admin_title': '🔐 **پنل مدیریت ربات**\nلطفاً یکی از گزینه‌ها را انتخاب کنید:',
        'brand_order_success': '✅ درخواست شما ثبت شد.\n🙏 به زودی تماس می‌گیریم.',
        'brand_payment_success': '✅ پرداخت موفق و ثبت سفارش.',
        'brand_invalid_option': '⚠️ گزینه نامعتبر است.',
        'brand_error_message': '❌ خطای داخلی رخ داده است. لطفاً دوباره تلاش کنید.',
        'brand_footer_text': '© ۱۴۰۳ - تمامی حقوق محفوظ است',
        'brand_waiting_text': '⏳ لطفاً چند لحظه صبر کنید...',
        'brand_goodbye_text': '👋 خداحافظ! امیدواریم دوباره ببینمتون.',
        'brand_thank_you_text': '🙏 از شما سپاسگزاریم.',
        'brand_help_text': '❓ راهنمای ربات:\nبرای شروع، یکی از گزینه‌های منو را انتخاب کنید.',
    }
    if default is not None:
        return default
    return defaults.get(key, '')


# ============================================================
# توابع کمکی برای دریافت متون پویا (جدید)
# ============================================================

def get_welcome_text_with_time() -> str:
    """دریافت پیام خوش‌آمدگویی همراه با زمان روز و فصل"""
    time_greeting = get_time_greeting()
    season_greeting = get_season_greeting()
    welcome = get_random_welcome()
    return f"{time_greeting}\n\n{season_greeting}\n\n{welcome}"


# توابع اصلی با استفاده از get_branded_text
def get_welcome_text():
    return get_branded_text('brand_welcome_text')


def get_main_menu_title():
    return get_branded_text('brand_main_menu_title')


def get_admin_title():
    return get_branded_text('brand_admin_title')


def get_order_success_text():
    return get_branded_text('brand_order_success')


def get_payment_success_text():
    return get_branded_text('brand_payment_success')


def get_invalid_option_text():
    return get_branded_text('brand_invalid_option')


def get_error_message_text():
    return get_branded_text('brand_error_message')


def get_footer_text():
    return get_branded_text('brand_footer_text')


# توابع جدید برای متونی که قبلاً وجود نداشتند
def get_waiting_text():
    return get_branded_text('brand_waiting_text')


def get_goodbye_text():
    return get_branded_text('brand_goodbye_text')


def get_thank_you_text():
    return get_branded_text('brand_thank_you_text')


def get_help_text():
    return get_branded_text('brand_help_text')


# ============================================================
# توابع کمکی برای منوها
# ============================================================

def get_main_menu_with_admin(user_id: int) -> Dict:
    """
    دریافت کیبورد منوی اصلی با دکمه مدیریت در صورت نیاز
    """
    try:
        from database import is_admin
        from keyboards import main_menu_keyboard, admin_panel_button
        
        if user_id == OWNER_ID or is_admin(user_id):
            return admin_panel_button(main_menu_keyboard())
        return main_menu_keyboard()
    except Exception as e:
        log_general_error(
            f"Error in get_main_menu_with_admin for user {user_id}: {str(e)}",
            traceback_str=traceback.format_exc(),
            user_id=user_id
        )
        from keyboards import main_menu_keyboard
        return main_menu_keyboard()


# ============================================================
# توابع کمکی API
# ============================================================

async def send_message(chat_id: int, text: str, keyboard: Optional[Dict] = None) -> Optional[Dict]:
    """ارسال پیام متنی به‌صورت ناهمگام با ثبت کامل خطاهای API"""
    url = BASE_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)

    ctx_logger = ContextLogger("api.send_message", context={"chat_id": chat_id})

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=config.HTTP_TIMEOUT) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    ctx_logger.error(f"send_message error {resp.status}: {error_text}")
                    log_api_error(
                        f"send_message: {resp.status} - {error_text}",
                        traceback_str=None,
                        user_id=chat_id,
                        data={'status': resp.status, 'response': error_text[:500]},
                        context_logger=ctx_logger
                    )
                    return None
        except asyncio.TimeoutError as e:
            ctx_logger.error(f"send_message timeout for chat {chat_id}")
            log_api_error(
                f"send_message timeout: {str(e)}",
                traceback_str=None,
                user_id=chat_id,
                data={'timeout': config.HTTP_TIMEOUT},
                context_logger=ctx_logger
            )
            return None
        except aiohttp.ClientError as e:
            ctx_logger.error(f"send_message client error: {e}")
            log_api_error(
                f"send_message client error: {str(e)}",
                traceback_str=None,
                user_id=chat_id,
                data={'error_type': type(e).__name__},
                context_logger=ctx_logger
            )
            return None
        except Exception as e:
            ctx_logger.error(f"send_message unexpected error: {e}")
            log_api_error(
                f"send_message unexpected error: {str(e)}",
                traceback_str=None,
                user_id=chat_id,
                context_logger=ctx_logger
            )
            return None


async def send_photo(chat_id: int, file_id: str, caption: str = "") -> Optional[Dict]:
    """ارسال عکس به‌صورت ناهمگام با ثبت کامل خطاهای API"""
    url = BASE_URL + "sendPhoto"
    payload = {"chat_id": chat_id, "photo": file_id}
    if caption:
        payload["caption"] = caption

    ctx_logger = ContextLogger("api.send_photo", context={"chat_id": chat_id})

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=config.HTTP_TIMEOUT) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    ctx_logger.error(f"send_photo error {resp.status}: {error_text}")
                    log_api_error(
                        f"send_photo: {resp.status} - {error_text}",
                        traceback_str=None,
                        user_id=chat_id,
                        data={'status': resp.status, 'response': error_text[:500]},
                        context_logger=ctx_logger
                    )
                    return None
        except asyncio.TimeoutError as e:
            ctx_logger.error(f"send_photo timeout for chat {chat_id}")
            log_api_error(
                f"send_photo timeout: {str(e)}",
                traceback_str=None,
                user_id=chat_id,
                data={'timeout': config.HTTP_TIMEOUT},
                context_logger=ctx_logger
            )
            return None
        except aiohttp.ClientError as e:
            ctx_logger.error(f"send_photo client error: {e}")
            log_api_error(
                f"send_photo client error: {str(e)}",
                traceback_str=None,
                user_id=chat_id,
                data={'error_type': type(e).__name__},
                context_logger=ctx_logger
            )
            return None
        except Exception as e:
            ctx_logger.error(f"send_photo unexpected error: {e}")
            log_api_error(
                f"send_photo unexpected error: {str(e)}",
                traceback_str=None,
                user_id=chat_id,
                context_logger=ctx_logger
            )
            return None


async def send_document(chat_id: int, file_id: Optional[str] = None,
                        file_path: Optional[str] = None, caption: str = "") -> Optional[Dict]:
    """ارسال فایل (سند) با استفاده از file_id یا file_path به‌صورت ناهمگام"""
    url = BASE_URL + "sendDocument"
    ctx_logger = ContextLogger("api.send_document", context={"chat_id": chat_id})

    if not file_id and not file_path:
        error_msg = "هیچ file_id یا file_path ارائه نشده است"
        ctx_logger.error(error_msg)
        log_api_error(error_msg, traceback_str=None, user_id=chat_id, context_logger=ctx_logger)
        return None

    if file_id:
        payload = {"chat_id": chat_id, "document": file_id}
        if caption:
            payload["caption"] = caption

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, timeout=config.HTTP_TIMEOUT) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        error_text = await resp.text()
                        ctx_logger.error(f"send_document error {resp.status}: {error_text}")
                        log_api_error(
                            f"send_document: {resp.status} - {error_text}",
                            traceback_str=None,
                            user_id=chat_id,
                            data={'status': resp.status, 'response': error_text[:500]},
                            context_logger=ctx_logger
                        )
                        return None
            except asyncio.TimeoutError as e:
                ctx_logger.error(f"send_document timeout for chat {chat_id}")
                log_api_error(
                    f"send_document timeout: {str(e)}",
                    traceback_str=None,
                    user_id=chat_id,
                    data={'timeout': config.HTTP_TIMEOUT},
                    context_logger=ctx_logger
                )
                return None
            except aiohttp.ClientError as e:
                ctx_logger.error(f"send_document client error: {e}")
                log_api_error(
                    f"send_document client error: {str(e)}",
                    traceback_str=None,
                    user_id=chat_id,
                    data={'error_type': type(e).__name__},
                    context_logger=ctx_logger
                )
                return None
            except Exception as e:
                ctx_logger.error(f"send_document unexpected error: {e}")
                log_api_error(
                    f"send_document unexpected error: {str(e)}",
                    traceback_str=None,
                    user_id=chat_id,
                    context_logger=ctx_logger
                )
                return None

    elif file_path:
        if not os.path.exists(file_path):
            error_msg = f"فایل {file_path} وجود ندارد"
            ctx_logger.error(error_msg)
            log_api_error(
                f"send_document file not found: {file_path}",
                traceback_str=None,
                user_id=chat_id,
                data={'file_path': file_path},
                context_logger=ctx_logger
            )
            return None

        async with aiohttp.ClientSession() as session:
            try:
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('chat_id', str(chat_id))
                    data.add_field('document', f, filename=os.path.basename(file_path))
                    if caption:
                        data.add_field('caption', caption)

                    async with session.post(url, data=data, timeout=config.HTTP_TIMEOUT) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        else:
                            error_text = await resp.text()
                            ctx_logger.error(f"send_document upload error {resp.status}: {error_text}")
                            log_api_error(
                                f"send_document upload: {resp.status} - {error_text}",
                                traceback_str=None,
                                user_id=chat_id,
                                data={'status': resp.status, 'response': error_text[:500]},
                                context_logger=ctx_logger
                            )
                            return None
            except asyncio.TimeoutError as e:
                ctx_logger.error(f"send_document upload timeout for chat {chat_id}")
                log_api_error(
                    f"send_document upload timeout: {str(e)}",
                    traceback_str=None,
                    user_id=chat_id,
                    data={'timeout': config.HTTP_TIMEOUT},
                    context_logger=ctx_logger
                )
                return None
            except aiohttp.ClientError as e:
                ctx_logger.error(f"send_document upload client error: {e}")
                log_api_error(
                    f"send_document upload client error: {str(e)}",
                    traceback_str=None,
                    user_id=chat_id,
                    data={'error_type': type(e).__name__},
                    context_logger=ctx_logger
                )
                return None
            except Exception as e:
                ctx_logger.error(f"send_document upload unexpected error: {e}")
                log_api_error(
                    f"send_document upload unexpected error: {str(e)}",
                    traceback_str=None,
                    user_id=chat_id,
                    context_logger=ctx_logger
                )
                return None

    return None


async def send_invoice(chat_id: int, title: str, description: str, payload: str,
                       provider_token: str, currency: str, prices: list,
                       start_parameter: str = "pay") -> Optional[Dict]:
    """ارسال فاکتور پرداخت به‌صورت ناهمگام با ثبت کامل خطاها"""
    url = BASE_URL + "sendInvoice"
    data = {
        "chat_id": chat_id,
        "title": title,
        "description": description,
        "payload": payload,
        "provider_token": provider_token,
        "currency": currency,
        "prices": json.dumps(prices),
        "start_parameter": start_parameter
    }

    ctx_logger = ContextLogger("api.send_invoice", context={"chat_id": chat_id})

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data, timeout=config.HTTP_TIMEOUT) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    ctx_logger.error(f"send_invoice error {resp.status}: {error_text}")
                    log_api_error(
                        f"send_invoice: {resp.status} - {error_text}",
                        traceback_str=None,
                        user_id=chat_id,
                        data={'status': resp.status, 'response': error_text[:500]},
                        context_logger=ctx_logger
                    )
                    return None
        except asyncio.TimeoutError as e:
            ctx_logger.error(f"send_invoice timeout for chat {chat_id}")
            log_api_error(
                f"send_invoice timeout: {str(e)}",
                traceback_str=None,
                user_id=chat_id,
                data={'timeout': config.HTTP_TIMEOUT},
                context_logger=ctx_logger
            )
            return None
        except aiohttp.ClientError as e:
            ctx_logger.error(f"send_invoice client error: {e}")
            log_api_error(
                f"send_invoice client error: {str(e)}",
                traceback_str=None,
                user_id=chat_id,
                data={'error_type': type(e).__name__},
                context_logger=ctx_logger
            )
            return None
        except Exception as e:
            ctx_logger.error(f"send_invoice unexpected error: {e}")
            log_api_error(
                f"send_invoice unexpected error: {str(e)}",
                traceback_str=None,
                user_id=chat_id,
                context_logger=ctx_logger
            )
            return None


async def answer_pre_checkout_query(pre_checkout_query_id: str, ok: bool, error_message: str = "") -> bool:
    """پاسخ به پرچک‌اوت (قبل از پرداخت) - ناهمگام با ثبت کامل خطاها"""
    url = BASE_URL + "answerPreCheckoutQuery"
    payload = {
        "pre_checkout_query_id": pre_checkout_query_id,
        "ok": ok
    }
    if not ok and error_message:
        payload["error_message"] = error_message

    ctx_logger = ContextLogger("api.answer_pre_checkout",
                               context={"pre_checkout_query_id": pre_checkout_query_id})

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=config.HTTP_TIMEOUT) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    ctx_logger.error(f"answer_pre_checkout_query error {resp.status}: {error_text}")
                    log_api_error(
                        f"answer_pre_checkout_query: {resp.status} - {error_text}",
                        traceback_str=None,
                        data={'status': resp.status, 'response': error_text[:500]},
                        context_logger=ctx_logger
                    )
                return resp.status == 200
        except asyncio.TimeoutError as e:
            ctx_logger.error(f"answer_pre_checkout_query timeout")
            log_api_error(
                f"answer_pre_checkout_query timeout: {str(e)}",
                traceback_str=None,
                data={'timeout': config.HTTP_TIMEOUT},
                context_logger=ctx_logger
            )
            return False
        except aiohttp.ClientError as e:
            ctx_logger.error(f"answer_pre_checkout_query client error: {e}")
            log_api_error(
                f"answer_pre_checkout_query client error: {str(e)}",
                traceback_str=None,
                data={'error_type': type(e).__name__},
                context_logger=ctx_logger
            )
            return False
        except Exception as e:
            ctx_logger.error(f"answer_pre_checkout_query unexpected error: {e}")
            log_api_error(
                f"answer_pre_checkout_query unexpected error: {str(e)}",
                traceback_str=None,
                context_logger=ctx_logger
            )
            return False


async def answer_callback(callback_query_id: str, text: str = "") -> bool:
    """پاسخ به کالبک‌کوئری - ناهمگام با ثبت کامل خطاها"""
    url = BASE_URL + "answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text

    ctx_logger = ContextLogger("api.answer_callback",
                               context={"callback_query_id": callback_query_id})

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=config.HTTP_TIMEOUT) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    ctx_logger.error(f"answer_callback error {resp.status}: {error_text}")
                    log_api_error(
                        f"answer_callback: {resp.status} - {error_text}",
                        traceback_str=None,
                        data={'status': resp.status, 'response': error_text[:500]},
                        context_logger=ctx_logger
                    )
                return resp.status == 200
        except asyncio.TimeoutError as e:
            ctx_logger.error(f"answer_callback timeout")
            log_api_error(
                f"answer_callback timeout: {str(e)}",
                traceback_str=None,
                data={'timeout': config.HTTP_TIMEOUT},
                context_logger=ctx_logger
            )
            return False
        except aiohttp.ClientError as e:
            ctx_logger.error(f"answer_callback client error: {e}")
            log_api_error(
                f"answer_callback client error: {str(e)}",
                traceback_str=None,
                data={'error_type': type(e).__name__},
                context_logger=ctx_logger
            )
            return False
        except Exception as e:
            ctx_logger.error(f"answer_callback unexpected error: {e}")
            log_api_error(
                f"answer_callback unexpected error: {str(e)}",
                traceback_str=None,
                context_logger=ctx_logger
            )
            return False


async def get_updates(offset: int = 0, timeout: int = 30) -> List[Dict]:
    """دریافت آپدیت‌ها از سرور بله - ناهمگام با ثبت کامل خطاها"""
    url = BASE_URL + "getUpdates"
    payload = {"offset": offset, "timeout": timeout}

    ctx_logger = ContextLogger("api.get_updates", context={"offset": offset})

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=timeout + 5) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("result", [])
                else:
                    error_text = await resp.text()
                    ctx_logger.error(f"get_updates error {resp.status}: {error_text}")
                    log_api_error(
                        f"get_updates: {resp.status} - {error_text}",
                        traceback_str=None,
                        data={'status': resp.status, 'response': error_text[:500]},
                        context_logger=ctx_logger
                    )
                    return []
        except asyncio.TimeoutError as e:
            ctx_logger.error(f"get_updates timeout")
            log_api_error(
                f"get_updates timeout: {str(e)}",
                traceback_str=None,
                data={'timeout': timeout},
                context_logger=ctx_logger
            )
            return []
        except aiohttp.ClientError as e:
            ctx_logger.error(f"get_updates client error: {e}")
            log_api_error(
                f"get_updates client error: {str(e)}",
                traceback_str=None,
                data={'error_type': type(e).__name__},
                context_logger=ctx_logger
            )
            return []
        except Exception as e:
            ctx_logger.error(f"get_updates unexpected error: {e}")
            log_api_error(
                f"get_updates unexpected error: {str(e)}",
                traceback_str=None,
                context_logger=ctx_logger
            )
            return []


async def delete_webhook() -> bool:
    """حذف وب‌هوک - ناهمگام با ثبت کامل خطاها"""
    url = BASE_URL + "deleteWebhook"
    ctx_logger = ContextLogger("api.delete_webhook")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, timeout=config.HTTP_TIMEOUT) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("ok", False)
                else:
                    error_text = await resp.text()
                    ctx_logger.error(f"delete_webhook error {resp.status}: {error_text}")
                    log_api_error(
                        f"delete_webhook: {resp.status} - {error_text}",
                        traceback_str=None,
                        data={'status': resp.status, 'response': error_text[:500]},
                        context_logger=ctx_logger
                    )
                    return False
        except asyncio.TimeoutError as e:
            ctx_logger.error(f"delete_webhook timeout")
            log_api_error(
                f"delete_webhook timeout: {str(e)}",
                traceback_str=None,
                data={'timeout': config.HTTP_TIMEOUT},
                context_logger=ctx_logger
            )
            return False
        except aiohttp.ClientError as e:
            ctx_logger.error(f"delete_webhook client error: {e}")
            log_api_error(
                f"delete_webhook client error: {str(e)}",
                traceback_str=None,
                data={'error_type': type(e).__name__},
                context_logger=ctx_logger
            )
            return False
        except Exception as e:
            ctx_logger.error(f"delete_webhook unexpected error: {e}")
            log_api_error(
                f"delete_webhook unexpected error: {str(e)}",
                traceback_str=None,
                context_logger=ctx_logger
            )
            return False


# ============================================================
# توابع صادراتی
# ============================================================

__all__ = [
    'TOKEN',
    'OWNER_ID',
    'BASE_URL',
    'PAYMENT_PROVIDER_TOKEN',
    'DEFAULT_PRICE_AMOUNT',
    'DEFAULT_PRICE_LABEL',
    'user_states',
    'get_branded_text',
    'get_welcome_text',
    'get_welcome_text_with_time',
    'get_main_menu_title',
    'get_admin_title',
    'get_order_success_text',
    'get_payment_success_text',
    'get_invalid_option_text',
    'get_error_message_text',
    'get_footer_text',
    'get_waiting_text',
    'get_goodbye_text',
    'get_thank_you_text',
    'get_help_text',
    'get_main_menu_with_admin',
    'send_message',
    'send_photo',
    'send_document',
    'send_invoice',
    'answer_pre_checkout_query',
    'answer_callback',
    'get_updates',
    'delete_webhook',
    'log_error',
    'log_general_error',
]