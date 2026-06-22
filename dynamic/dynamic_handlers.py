# dynamic/dynamic_handlers.py
# توابع اصلی داینامیک - نسخه async با logging و ثبت آمار (کلیک، شروع فرم، سفارش)
# پشتیبانی از قیمت متغیر و پردازش مبلغ ورودی
# اصلاح شده با استفاده از messenger برای ارسال همزمان

import time
import traceback
from typing import Dict, Any, Optional

from logger_config import logger, ContextLogger
from core import user_states, send_message, send_photo, send_document, OWNER_ID
from database import (
    get_button_by_callback,
    get_questions_by_button,
    get_button_by_id,
    save_user_answer,
    get_options_by_question,
    get_option_by_callback,
    get_question_by_id,
    get_validation_settings,
    log_button_click,
    log_form_start,
    log_order_paid,
    upsert_user,
    get_button_price_info,
    validate_price_input,
)
from keyboards import main_menu_keyboard
from .dynamic_core import _process_questions, _ask_question, handle_price_input
from .dynamic_validation import validate_answer, get_validation_error_message, _check_conditions
from utils.error_handler import (
    log_callback_error,
    log_payment_error,
    log_general_error,
    log_database_error,
    log_api_error
)

# ========== ایمپورت‌های جدید از texts.py و core.py ==========
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
from core import get_welcome_text, get_main_menu_title, get_error_message_text, get_order_success_text, get_payment_success_text

# ========== ایمپورت messenger ==========
from messenger import Messenger, get_messenger, send_messages_batch, MessageBuilder


async def _send_dynamic_report(user_id, button_id, order_data):
    """
    ارسال گزارش سفارش پویا به ادمین با استفاده از messenger
    
    پارامترها:
        user_id: شناسه کاربر
        button_id: شناسه دکمه
        order_data: داده‌های سفارش
    """
    try:
        button_info = get_button_by_id(button_id)
        button_name = button_info['name'] if button_info else "نامشخص"

        # ساخت پیام گزارش
        msg = f"✅ **سفارش پویا جدید**\n"
        msg += f"🔘 دکمه: {button_name}\n"
        msg += f"👤 کاربر: {user_id}\n"
        msg += f"💰 مبلغ: {order_data.get('payment_amount', 0)} ریال\n"
        msg += f"🎫 کد رهگیری: {order_data.get('tracking_code', 'ندارد')}\n"
        msg += f"⏰ زمان: {order_data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))}\n\n"
        msg += "📝 **پاسخ‌های کاربر:**\n"

        answers = order_data.get("answers", {})
        files = order_data.get("files", {})

        # ========== ساخت لیست محتوا با MessageBuilder ==========
        builder = MessageBuilder()
        
        # پیام اصلی گزارش
        builder.add_message(OWNER_ID, msg)
        
        # افزودن فایل‌ها
        if answers:
            for question_text, answer in answers.items():
                if question_text in files:
                    file_data = files[question_text]
                    try:
                        if file_data["type"] == "photo":
                            builder.add_photo(OWNER_ID, file_data["file_id"], f"📎 {question_text}")
                        else:
                            builder.add_document(OWNER_ID, file_data["file_id"], f"📎 {question_text}")
                    except Exception as e:
                        log_callback_error(
                            f"خطا در ارسال فایل به ادمین: {str(e)}",
                            traceback=traceback.format_exc(),
                            user_id=user_id
                        )
                else:
                    # پاسخ‌های متنی از قبل در پیام اصلی وجود دارند
                    pass
        
        # ========== ارسال همزمان با messenger ==========
        results = await builder.send()
        
        # بررسی نتایج
        if results:
            success_count = sum(1 for r in results if not isinstance(r, Exception) and r is not None)
            error_count = len(results) - success_count
            if error_count > 0:
                logger.warning(f"⚠️ برخی از پیام‌های گزارش به ادمین با خطا مواجه شدند: {error_count} مورد")
        
        logger.info(f"گزارش سفارش پویا برای کاربر {user_id} به ادمین ارسال شد.")

    except Exception as e:
        log_general_error(
            f"Error in _send_dynamic_report: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id
        )


async def handle_dynamic_callback(update):
    """پردازش کالبک‌های داینامیک (دکمه‌های سرویس‌ها و گزینه‌ها)"""
    try:
        cb = update.get("callback_query")
        if not cb:
            return False

        data = cb.get("data")
        user_id = cb.get("from", {}).get("id")
        chat_id = cb.get("message", {}).get("chat", {}).get("id")

        if not user_id or not chat_id or not data:
            return False

        # ثبت فعالیت کاربر
        try:
            from_user = cb.get("from", {})
            upsert_user(user_id, from_user.get("username"), from_user.get("first_name"), from_user.get("last_name"))
        except Exception as e:
            log_database_error(
                f"خطا در ثبت کاربر (کالبک داینامیک): {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )

        # ========== دکمه سرویس ==========
        button = get_button_by_callback(data)
        if button:
            state_info = user_states.get(user_id, {"state": "main"})
            if state_info.get("state") not in ["main", "dynamic_awaiting_answer", "dynamic_awaiting_option"]:
                # ========== استفاده از پیام تصادفی ==========
                await send_message(chat_id, get_random_waiting() + "\n\n⚠️ لطفاً فرم فعلی را تکمیل کنید.")
                return True

            # ثبت کلیک روی دکمه
            log_button_click(button['id'], user_id)

            if button.get('has_submenu', 0) == 1:
                from .dynamic_core import get_submenu_keyboard
                sub_keyboard = get_submenu_keyboard(button['id'])
                if sub_keyboard:
                    await send_message(chat_id, f"📋 **{button['name']}**", sub_keyboard)
                    return True
                else:
                    await send_message(chat_id, get_random_error() + "\n\n⚠️ این دکمه زیرمنو دارد اما هیچ زیرمنویی تعریف نشده.")
                    return True

            questions = get_questions_by_button(button['id'])
            if not questions:
                await send_message(chat_id, get_random_error() + "\n\n⚠️ این سرویس هنوز تنظیم نشده است.")
                return True

            # ثبت شروع فرم
            log_form_start(button['id'], user_id)

            user_states[user_id] = {
                "state": "dynamic_awaiting_answer",
                "button_id": button['id'],
                "question_index": 0,
                "answers": {},
                "files": {},
                "order_data": {
                    "service_type": "dynamic",
                    "button_name": button['name'],
                    "button_id": button['id']
                }
            }
            await _process_questions(user_id, chat_id, button['id'])
            return True

        # ========== گزینه دکمه‌ای سوال ==========
        option = get_option_by_callback(data)
        if option:
            state_info = user_states.get(user_id, {"state": "main"})
            if state_info.get("state") != "dynamic_awaiting_option":
                await send_message(chat_id, get_random_error() + "\n\n⚠️ خطا در پردازش.")
                return True

            q_id = option['question_id']
            button_id = state_info.get("button_id")
            answers = state_info.get("answers", {})
            q = get_question_by_id(q_id)

            if q:
                is_valid, error_type, fixed_answer = validate_answer(option['option_text'], q)
                if not is_valid:
                    error_msg = get_validation_error_message(q, error_type)
                    await send_message(chat_id, error_msg)
                    return True

                question_text = q.get('question_text', f'سوال {q_id}')
                answers[question_text] = fixed_answer
                save_user_answer(user_id, button_id, q_id, fixed_answer)
                user_states[user_id]["answers"] = answers

                idx = state_info.get("question_index", 0) + 1
                user_states[user_id]["question_index"] = idx
                await _process_questions(user_id, chat_id, button_id)
            return True

        return False

    except Exception as e:
        log_callback_error(
            f"Error in handle_dynamic_callback: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id if 'user_id' in locals() else None,
            chat_id=chat_id if 'chat_id' in locals() else None
        )
        return False


async def handle_dynamic_message(update):
    """پردازش پیام‌های متنی و فایل‌های ارسالی در فرم‌های داینامیک"""
    try:
        msg = update.get("message")
        if not msg:
            return False

        chat_id = msg.get("chat", {}).get("id")
        user_id = msg.get("from", {}).get("id")

        if not user_id or not chat_id:
            return False

        # ثبت فعالیت کاربر
        try:
            from_user = msg.get("from", {})
            upsert_user(user_id, from_user.get("username"), from_user.get("first_name"), from_user.get("last_name"))
        except Exception as e:
            log_database_error(
                f"خطا در ثبت کاربر (پیام داینامیک): {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )

        state_info = user_states.get(user_id, {"state": "main"})
        logger.debug(f"وضعیت کاربر {user_id} در handle_dynamic_message: {state_info.get('state')}")

        # ========== پردازش مبلغ برای قیمت متغیر ==========
        if state_info.get("state") == "dynamic_awaiting_price":
            button_id = state_info.get("button_id")
            if not button_id:
                await send_message(chat_id, get_random_error() + "\n\n❌ خطا در پردازش مبلغ.")
                user_states[user_id] = {"state": "main"}
                return True

            text = msg.get("text", "").strip()
            if not text:
                await send_message(chat_id, get_random_error() + "\n\n❌ لطفاً یک عدد معتبر وارد کنید.")
                return True

            return await handle_price_input(user_id, chat_id, button_id, text)

        if state_info.get("state") != "dynamic_awaiting_answer":
            return False

        button_id = state_info.get("button_id")
        idx = state_info.get("question_index", 0)
        answers = state_info.get("answers", {})

        if not button_id:
            await send_message(chat_id, get_random_error() + "\n\n❌ خطا.", main_menu_keyboard())
            user_states[user_id] = {"state": "main"}
            return True

        questions = get_questions_by_button(button_id)
        if idx >= len(questions):
            await send_message(chat_id, get_random_error() + "\n\n❌ خطا.", main_menu_keyboard())
            user_states[user_id] = {"state": "main"}
            return True

        q = questions[idx]

        # بررسی اینکه آیا سوال گزینه‌های دکمه‌ای دارد
        options = get_options_by_question(q['id'])
        if options:
            await send_message(
                chat_id,
                get_random_invalid_option() + f"\n\n⚠️ لطفاً از دکمه‌های زیر برای پاسخ به سوال استفاده کنید:\n{q['question_text']}"
            )
            return True

        # دریافت فایل یا متن
        file_id = None
        file_type = None
        text = msg.get("text", "").strip()

        if "document" in msg:
            file_id = msg["document"]["file_id"]
            file_type = "document"
        elif "photo" in msg:
            file_id = msg["photo"][-1]["file_id"]
            file_type = "photo"

        # ========== پردازش فایل ==========
        if file_id:
            validation_type = q.get('validation_type', 'none')
            if validation_type in ['image', 'file', 'document']:
                if q.get('file_validation_enabled', 0) == 1:
                    # بررسی فرمت فایل
                    allowed = q.get('allowed_formats')
                    if allowed:
                        file_name = msg.get('document', {}).get('file_name', '')
                        if file_name:
                            ext = file_name.split('.')[-1].lower()
                            if ext not in [f.strip() for f in allowed.split(',')]:
                                error_msg = get_validation_error_message(q, 'file_format')
                                await send_message(chat_id, error_msg)
                                return True

                    # بررسی حجم فایل
                    file_size = msg.get('document', {}).get('file_size', 0)
                    max_size = q.get('max_file_size', 0)
                    min_size = q.get('min_file_size', 0)

                    if max_size and file_size > max_size * 1024:
                        error_msg = get_validation_error_message(q, 'file_size_max')
                        await send_message(chat_id, error_msg)
                        return True
                    if min_size and file_size < min_size * 1024:
                        error_msg = get_validation_error_message(q, 'file_size_min')
                        await send_message(chat_id, error_msg)
                        return True

            question_text = q.get('question_text', f'سوال {idx+1}')
            answers[question_text] = f"[فایل: {file_type}]"
            user_states[user_id]["answers"] = answers

            if "files" not in user_states[user_id]:
                user_states[user_id]["files"] = {}
            user_states[user_id]["files"][question_text] = {"file_id": file_id, "type": file_type}

            save_user_answer(user_id, button_id, q['id'], f"[فایل: {file_type}]")

        # ========== پردازش متن ==========
        elif text:
            is_valid, error_type, fixed_answer = validate_answer(text, q)
            if not is_valid:
                error_msg = get_validation_error_message(q, error_type)
                await send_message(chat_id, error_msg)
                return True

            question_text = q.get('question_text', f'سوال {idx+1}')
            answers[question_text] = fixed_answer
            user_states[user_id]["answers"] = answers
            save_user_answer(user_id, button_id, q['id'], fixed_answer)
        else:
            # ========== استفاده از پیام تصادفی ==========
            await send_message(
                chat_id,
                get_random_error() + f"\n\n❌ لطفاً پاسخ خود را به صورت متن یا فایل ارسال کنید:\n{q['question_text']}"
            )
            return True

        # حرکت به سوال بعدی
        idx += 1
        user_states[user_id]["question_index"] = idx
        await _process_questions(user_id, chat_id, button_id)
        return True

    except Exception as e:
        log_general_error(
            f"Error in handle_dynamic_message: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id if 'user_id' in locals() else None,
            chat_id=chat_id if 'chat_id' in locals() else None
        )
        return False


async def handle_dynamic_payment(update):
    """پردازش پرداخت موفق در فرم‌های داینامیک و ثبت آمار"""
    try:
        msg = update.get("message")
        if not msg or "successful_payment" not in msg:
            return False

        payment = msg["successful_payment"]
        user_id = msg.get("from", {}).get("id")
        chat_id = msg.get("chat", {}).get("id")

        if not user_id or not chat_id:
            return False

        # ثبت فعالیت کاربر
        try:
            from_user = msg.get("from", {})
            upsert_user(user_id, from_user.get("username"), from_user.get("first_name"), from_user.get("last_name"))
        except Exception as e:
            log_database_error(
                f"خطا در ثبت کاربر (پرداخت): {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )

        state_info = user_states.get(user_id, {"state": "main"})
        if state_info.get("state") != "dynamic_awaiting_payment":
            logger.warning(f"وضعیت کاربر {user_id} برای پرداخت مناسب نیست: {state_info.get('state')}")
            return False

        button_id = state_info.get("button_id")
        order_data = state_info.get("order_data", {})

        if not button_id or not order_data:
            await send_message(chat_id, get_random_error() + "\n\n❌ خطا.", main_menu_keyboard())
            user_states[user_id] = {"state": "main"}
            return True

        from database import save_dynamic_order

        tracking = payment.get("provider_payment_charge_id", "ندارد")
        amount = payment.get("total_amount", 0)
        order_data["payment_confirmed"] = True
        order_data["payment_amount"] = amount
        order_data["tracking_code"] = tracking
        order_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

        save_dynamic_order(
            user_id,
            button_id,
            order_data,
            payment_amount=order_data["payment_amount"],
            tracking_code=tracking,
            status="paid"
        )

        # ثبت سفارش پرداخت‌شده در آمار
        log_order_paid(button_id, user_id, amount)

        await _send_dynamic_report(user_id, button_id, order_data)
        
        # ========== استفاده از پیام پرداخت موفق تصادفی ==========
        success_msg = get_random_payment_success()
        await send_message(chat_id, success_msg, main_menu_keyboard())
        user_states[user_id] = {"state": "main"}

        logger.info(f"پرداخت موفق برای کاربر {user_id} با کد رهگیری {tracking}")
        return True

    except Exception as e:
        log_payment_error(
            f"Error in handle_dynamic_payment: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id if 'user_id' in locals() else None,
            chat_id=chat_id if 'chat_id' in locals() else None
        )
        return False


__all__ = [
    'handle_dynamic_callback',
    'handle_dynamic_message',
    'handle_dynamic_payment',
    '_send_dynamic_report',
]