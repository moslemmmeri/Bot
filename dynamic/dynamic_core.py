# dynamic/dynamic_core.py
# توابع پایه داینامیک - نسخه async با logging
# با پشتیبانی از مدیریت ستون‌ها (تعداد ستون‌های زیرمنوها)
# اصلاح شده با مدیریت خطا و لاگ‌گیری کامل در دیتابیس

import time
import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import user_states, send_message
from database import (
    get_buttons_by_parent,
    get_button_by_id,
    get_questions_by_button,
    get_options_by_question,
    get_question_by_id,
    get_conditions_by_question,
    get_effective_columns,
)
from keyboards import main_menu_keyboard, chunk_list
from .dynamic_validation import _check_conditions, validate_answer, get_validation_error_message
from utils.error_handler import log_general_error, log_callback_error, log_database_error, log_payment_error


def get_submenu_keyboard(button_id):
    """
    ساخت کیبورد زیرمنوهای یک دکمه با تعداد ستون‌های مناسب
    تعداد ستون‌ها بر اساس اولویت زیر تعیین می‌شود:
    1. تنظیمات اختصاصی دکمه (اگر در جدول buttons ستون columns تنظیم شده باشد)
    2. تنظیمات دسته‌بندی (فیلد columns در جدول categories)
    3. مقدار پیش‌فرض عمومی (default_menu_columns در جدول settings)
    """
    try:
        submenus = get_buttons_by_parent(button_id)
        main_button = get_button_by_id(button_id)
        main_name = main_button['name'] if main_button else None
        
        filtered = []
        for sub in submenus:
            if sub['id'] == button_id:
                continue
            if main_name and sub['name'] == main_name:
                continue
            filtered.append(sub)
        
        if not filtered:
            return None
        
        items = [{"text": sub['name'], "callback_data": sub['callback_data']} for sub in filtered]
        
        # تعیین تعداد ستون‌ها برای این زیرمنو
        # از تنظیمات دکمه والد و دسته‌بندی آن استفاده می‌کنیم
        category_id = main_button['category_id'] if main_button else None
        columns = get_effective_columns(
            button_id=button_id,      # دکمه والد
            category_id=category_id   # دسته‌بندی دکمه والد
        )
        
        # اطمینان از معتبر بودن تعداد ستون‌ها
        if columns < 1:
            columns = 1
        if columns > 8:
            columns = 8
        
        keyboard = []
        # تقسیم به ردیف‌های با تعداد ستون‌های مشخص‌شده
        for row in chunk_list(items, columns):
            keyboard.append(row)
        keyboard.append([{"text": "🔙 برگشت", "callback_data": "back_main"}])
        
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_callback_error(
            f"Error in get_submenu_keyboard for button {button_id}: {str(e)}",
            traceback=traceback.format_exc()  # ✅ traceback کامل
        )
        return None


def get_question_keyboard(question_id):
    """ساخت کیبورد گزینه‌های یک سوال دکمه‌ای"""
    try:
        options = get_options_by_question(question_id)
        if not options:
            return None
        keyboard = []
        for opt in options:
            keyboard.append([{"text": opt['option_text'], "callback_data": opt['callback_data']}])
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_database_error(
            f"Error in get_question_keyboard for question {question_id}: {str(e)}",
            traceback=traceback.format_exc()  # ✅ traceback کامل
        )
        return None


async def _ask_question(user_id, chat_id, question, button_id):
    """پرسش یک سوال از کاربر با نمایش راهنما"""
    try:
        options = get_options_by_question(question['id'])
        
        hint = question.get('validation_hint')
        msg = f"❓ {question['question_text']}"
        if hint:
            msg += f"\n💡 {hint}"
        
        if options:
            keyboard = get_question_keyboard(question['id'])
            if keyboard:
                user_states[user_id]["state"] = "dynamic_awaiting_option"
                await send_message(chat_id, msg, keyboard)
            else:
                user_states[user_id]["state"] = "dynamic_awaiting_answer"
                await send_message(chat_id, f"{msg}\n⚠️ خطا در نمایش گزینه‌ها.")
        else:
            user_states[user_id]["state"] = "dynamic_awaiting_answer"
            await send_message(chat_id, msg)
            
        logger.debug(f"سوال {question['id']} از کاربر {user_id} پرسیده شد.")
        
    except Exception as e:
        log_general_error(
            f"Error in _ask_question: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش سوال.")


async def _process_questions(user_id, chat_id, button_id):
    """پردازش سوالات به ترتیب با در نظر گرفتن شرط‌ها"""
    try:
        state_info = user_states.get(user_id, {})
        idx = state_info.get("question_index", 0)
        answers = state_info.get("answers", {})
        
        questions = get_questions_by_button(button_id)
        
        while idx < len(questions):
            q = questions[idx]
            if _check_conditions(q, answers):
                user_states[user_id]["question_index"] = idx
                await _ask_question(user_id, chat_id, q, button_id)
                return True
            else:
                idx += 1
        
        # اگر به انتها رسیدیم، فرم تکمیل شده است
        if idx >= len(questions):
            await _finalize_answers(user_id, chat_id, button_id)
            return True
        
        return False
        
    except Exception as e:
        log_general_error(
            f"Error in _process_questions for button {button_id}: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در پردازش سوالات.")
        return False


async def _finalize_answers(user_id, chat_id, button_id):
    """نهایی‌سازی پاسخ‌ها و ارسال فاکتور یا ثبت سفارش"""
    try:
        from core import send_invoice, DEFAULT_PRICE_LABEL, DEFAULT_PRICE_AMOUNT, PAYMENT_PROVIDER_TOKEN, OWNER_ID
        from database import save_dynamic_order, get_button_by_id, get_button_price_info
        from .dynamic_handlers import _send_dynamic_report
        
        state_info = user_states.get(user_id, {})
        answers = state_info.get("answers", {})
        order_data = state_info.get("order_data", {})
        order_data["answers"] = answers
        
        files = state_info.get("files", {})
        if files:
            order_data["files"] = files
        
        user_states[user_id]["order_data"] = order_data

        button_info = get_button_by_id(button_id)
        
        # بررسی是否需要 پرداخت
        if button_info and button_info.get('has_payment', 0) == 1:
            # دریافت اطلاعات قیمت (با پشتیبانی از قیمت متغیر)
            price_info = get_button_price_info(button_id)
            price_type = price_info.get('price_type', 'fixed')
            
            if price_type == 'variable':
                # اگر قیمت متغیر است، باید از کاربر مبلغ را بپرسیم
                # برای این کار، یک سوال جدید اضافه می‌کنیم
                # ابتدا بررسی می‌کنیم که آیا قبلاً مبلغ پرسیده شده است
                if 'price_amount' not in answers:
                    # یک سوال موقت برای دریافت مبلغ ایجاد می‌کنیم
                    # با توجه به اینکه این یک مورد خاص است، یک سوال جدید به صورت موقت ایجاد می‌کنیم
                    # اما بهتر است از قبل در طراحی سوالات، سوال مبلغ وجود داشته باشد
                    # در غیر این صورت، یک سوال داینامیک ایجاد می‌کنیم
                    # برای سادگی، در اینجا از کاربر می‌خواهیم مبلغ را وارد کند
                    user_states[user_id]["state"] = "dynamic_awaiting_price"
                    await send_message(
                        chat_id, 
                        f"💰 **مبلغ مورد نظر را به ریال وارد کنید:**\n"
                        f"(حداقل: {price_info.get('min_price', 0):,} - حداکثر: {price_info.get('max_price', 'نامحدود')})"
                    )
                    return True
                else:
                    price_amount = int(answers['price_amount'])
            else:
                price_amount = price_info.get('price_amount', DEFAULT_PRICE_AMOUNT)
                if price_amount < 10000:
                    price_amount = 10000
            
            price_label = price_info.get('price_label', DEFAULT_PRICE_LABEL)
            title = f"پرداخت هزینه {button_info['name']}"
            desc = f"پرداخت برای {button_info['name']}"
            payload = f"dyn_{button_id}_{user_id}_{int(time.time())}"
            prices = [{"label": price_label, "amount": price_amount}]
            
            await send_invoice(chat_id, title, desc, payload, PAYMENT_PROVIDER_TOKEN, "IRT", prices)
            user_states[user_id]["state"] = "dynamic_awaiting_payment"
            
            logger.info(f"فاکتور برای کاربر {user_id} با مبلغ {price_amount} ریال ارسال شد.")
            
        else:
            # بدون پرداخت
            order_data["payment_confirmed"] = True
            order_data["payment_amount"] = 0
            order_data["tracking_code"] = "بدون پرداخت"
            order_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            save_dynamic_order(user_id, button_id, order_data, status="completed")
            await _send_dynamic_report(user_id, button_id, order_data)
            await send_message(chat_id, "✅ درخواست شما ثبت شد.\n🙏 به زودی تماس می‌گیریم.", main_menu_keyboard())
            user_states[user_id] = {"state": "main"}
            
            logger.info(f"سفارش بدون پرداخت برای کاربر {user_id} ثبت شد.")
            
    except Exception as e:
        log_payment_error(
            f"Error in _finalize_answers: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ثبت نهایی سفارش.")
        user_states[user_id] = {"state": "main"}


# ============================================================
# توابع کمکی برای قیمت متغیر
# ============================================================

async def handle_price_input(user_id, chat_id, button_id, price_text):
    """پردازش مبلغ وارد شده برای قیمت متغیر"""
    try:
        from database import get_button_price_info, validate_price_input
        
        price_info = get_button_price_info(button_id)
        is_valid, amount, error_msg = validate_price_input(price_text, button_id)
        
        if not is_valid:
            await send_message(chat_id, error_msg)
            return False
        
        # ذخیره مبلغ در answers
        state_info = user_states.get(user_id, {})
        answers = state_info.get("answers", {})
        answers["price_amount"] = str(amount)
        state_info["answers"] = answers
        user_states[user_id] = state_info
        
        # ادامه فرآیند
        await _process_questions(user_id, chat_id, button_id)
        return True
        
    except Exception as e:
        log_general_error(
            f"Error in handle_price_input: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در پردازش مبلغ.")
        return False


__all__ = [
    'get_submenu_keyboard',
    'get_question_keyboard',
    '_ask_question',
    '_process_questions',
    '_finalize_answers',
    'handle_price_input',
]