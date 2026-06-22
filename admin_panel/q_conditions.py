# admin_panel/q_conditions.py
# مدیریت شرط‌های سوالات در پنل ادمین - نسخه async با logging
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states
from database import (
    get_question_by_id,
    get_previous_questions,
    add_condition,
    get_conditions_by_question,
    get_condition_by_id,
    update_condition,
    delete_condition,
    delete_conditions_by_question,
    add_question,
    get_questions_by_button
)
from keyboards import (
    admin_main_keyboard,
    admin_questions_keyboard,
    condition_operator_keyboard,
    logic_operator_keyboard
)
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error
)
from datetime import datetime


async def handle_condition_add_start(chat_id, user_id):
    """شروع فرآیند افزودن شرط جدید"""
    try:
        q_id = user_states.get(user_id, {}).get("current_question_id")
        if not q_id:
            q_id = user_states.get(user_id, {}).get("condition_question_id")
        
        if not q_id:
            await send_message(chat_id, "❌ خطا: شناسه سوال یافت نشد. لطفاً ابتدا از جزئیات سوال وارد شوید.")
            user_states[user_id] = {"state": "main"}
            return True
        
        q = get_question_by_id(q_id)
        if not q:
            await send_message(chat_id, "❌ سوال یافت نشد.")
            return True
        
        previous_questions = get_previous_questions(q['button_id'], q_id)
        if not previous_questions:
            await send_message(chat_id, "❌ هیچ سوال قبلی برای شرط وجود ندارد.")
            return True
        
        keyboard = []
        for pq in previous_questions:
            keyboard.append([{"text": f"{pq['question_text'][:30]}", "callback_data": f"admin_cond_ref_{pq['id']}"}])
        keyboard.append([{"text": "🔙 انصراف", "callback_data": "admin_back"}])
        
        user_states[user_id]["state"] = "admin_add_condition_ref"
        user_states[user_id]["condition_question_id"] = q_id
        await send_message(chat_id, "🔹 **انتخاب سوال مرجع برای شرط جدید**\nلطفاً سوال مرجع را انتخاب کنید:", {"inline_keyboard": keyboard})
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_add_start: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع افزودن شرط.")
        return True


async def handle_condition_ref(chat_id, user_id, data):
    """پردازش انتخاب سوال مرجع (admin_cond_ref_<question_id>)"""
    try:
        ref_q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        user_states[user_id]["condition_ref_id"] = ref_q_id
        user_states[user_id]["state"] = "admin_add_condition_operator"
        await send_message(chat_id, "🔹 **انتخاب عملگر شرط**", condition_operator_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_ref: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب سوال مرجع.")
        return True


async def handle_condition_operator(chat_id, user_id, data):
    """پردازش انتخاب عملگر شرط (admin_cond_op_*)"""
    try:
        operator = data.split("_")[3]
        user_states[user_id]["condition_operator"] = operator
        user_states[user_id]["state"] = "admin_add_condition_value"
        await send_message(chat_id, "🔹 **مقدار شرط**\nلطفاً مقدار مورد نظر را وارد کنید:")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_operator: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب عملگر.")
        return True


async def handle_condition_logic(chat_id, user_id, data):
    """پردازش انتخاب منطق ترکیب شرط‌ها (admin_cond_logic_*)"""
    try:
        logic = data.split("_")[3]
        q_id = user_states.get(user_id, {}).get("condition_question_id")
        ref_id = user_states.get(user_id, {}).get("condition_ref_id")
        operator = user_states.get(user_id, {}).get("condition_operator")
        value = user_states.get(user_id, {}).get("condition_temp_value")
        
        missing = []
        if not q_id: missing.append("شناسه سوال")
        if not ref_id: missing.append("سوال مرجع")
        if not operator: missing.append("عملگر")
        if value is None: missing.append("مقدار")
        
        if missing:
            await send_message(chat_id, f"❌ خطا: اطلاعات زیر یافت نشد: {', '.join(missing)}\nلطفاً دوباره از ابتدا اقدام کنید.")
            user_states[user_id] = {"state": "main"}
            return True
        
        add_condition(q_id, ref_id, operator, value, logic_operator=logic)
        
        user_states[user_id].pop("condition_ref_id", None)
        user_states[user_id].pop("condition_operator", None)
        user_states[user_id].pop("condition_temp_value", None)
        user_states[user_id].pop("condition_question_id", None)
        user_states[user_id]["state"] = "main"
        
        btn_id = user_states.get(user_id, {}).get("current_btn")
        logger.info(f"شرط جدید با موفقیت اضافه شد: سوال {q_id} -> سوال {ref_id} {operator} {value} (منطق: {logic})")
        await send_message(chat_id, f"✅ شرط با موفقیت اضافه شد.", admin_questions_keyboard(btn_id))
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_logic: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در ذخیره شرط: {str(e)}")
        return True


async def handle_condition_delete(chat_id, user_id, data):
    """حذف شرط (admin_cond_del_<condition_id>)"""
    try:
        cond_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه شرط نامعتبر.")
        return True
    
    try:
        cond = get_condition_by_id(cond_id)
        if not cond:
            await send_message(chat_id, "❌ شرط یافت نشد.")
            return True
        
        delete_condition(cond_id)
        btn_id = user_states.get(user_id, {}).get("current_btn")
        logger.info(f"شرط {cond_id} با موفقیت حذف شد (توسط کاربر {user_id})")
        await send_message(chat_id, "✅ شرط با موفقیت حذف شد.", admin_questions_keyboard(btn_id))
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_delete: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف شرط.")
        return True


async def handle_condition_edit_start(chat_id, user_id, data):
    """شروع ویرایش شرط (admin_cond_edit_<condition_id>)"""
    try:
        cond_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه شرط نامعتبر.")
        return True
    
    try:
        cond = get_condition_by_id(cond_id)
        if not cond:
            await send_message(chat_id, "❌ شرط یافت نشد.")
            return True
        
        user_states[user_id]["edit_condition_id"] = cond_id
        q_id = cond['question_id']
        q = get_question_by_id(q_id)
        
        if not q:
            await send_message(chat_id, "❌ سوال یافت نشد.")
            return True
        
        previous_questions = get_previous_questions(q['button_id'], q_id)
        if not previous_questions:
            await send_message(chat_id, "❌ هیچ سوال قبلی برای ویرایش شرط وجود ندارد.")
            return True
        
        keyboard = []
        for pq in previous_questions:
            selected = "✅ " if pq['id'] == cond['condition_question_id'] else ""
            keyboard.append([{"text": f"{selected}{pq['question_text'][:30]}", "callback_data": f"admin_cond_edit_ref_{cond_id}_{pq['id']}"}])
        keyboard.append([{"text": "🔙 انصراف", "callback_data": "admin_back"}])
        
        user_states[user_id]["state"] = "admin_edit_condition_ref"
        await send_message(chat_id, "🔹 **انتخاب سوال مرجع جدید**\nلطفاً سوال مرجع را انتخاب کنید:", {"inline_keyboard": keyboard})
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_edit_start: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع ویرایش شرط.")
        return True


async def handle_condition_edit_ref(chat_id, user_id, data):
    """پردازش انتخاب سوال مرجع جدید برای ویرایش شرط (admin_cond_edit_ref_<cond_id>_<ref_id>)"""
    try:
        parts = data.split("_")
        cond_id = int(parts[4])
        ref_q_id = int(parts[5])
    except (ValueError, IndexError):
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        user_states[user_id]["edit_condition_id"] = cond_id
        user_states[user_id]["condition_ref_id"] = ref_q_id
        user_states[user_id]["state"] = "admin_edit_condition_operator"
        await send_message(chat_id, "🔹 **انتخاب عملگر جدید برای شرط**", condition_operator_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_edit_ref: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب سوال مرجع.")
        return True


async def handle_condition_edit_operator(chat_id, user_id, data):
    """پردازش انتخاب عملگر جدید برای ویرایش شرط (admin_cond_edit_op_*)"""
    try:
        operator = data.split("_")[4]
        cond_id = user_states.get(user_id, {}).get("edit_condition_id")
        
        if not cond_id:
            await send_message(chat_id, "❌ شناسه شرط یافت نشد.")
            return True
        
        update_condition(cond_id, condition_operator=operator)
        user_states[user_id].pop("edit_condition_id", None)
        user_states[user_id]["state"] = "main"
        
        btn_id = user_states.get(user_id, {}).get("current_btn")
        logger.info(f"عملگر شرط {cond_id} به {operator} تغییر یافت (توسط کاربر {user_id})")
        await send_message(chat_id, "✅ عملگر شرط با موفقیت به‌روزرسانی شد.", admin_questions_keyboard(btn_id))
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_edit_operator: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ویرایش عملگر شرط.")
        return True


async def handle_condition_edit_value(chat_id, user_id, data):
    """شروع ویرایش مقدار شرط (admin_cond_edit_value_<condition_id>)"""
    try:
        cond_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه شرط نامعتبر.")
        return True
    
    try:
        user_states[user_id]["edit_condition_id"] = cond_id
        user_states[user_id]["state"] = "admin_edit_condition_value"
        await send_message(chat_id, "🔹 **مقدار جدید شرط**\nلطفاً مقدار جدید را وارد کنید:")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_edit_value: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع ویرایش مقدار شرط.")
        return True


async def handle_condition_list(chat_id, user_id, data):
    """نمایش لیست شرط‌های یک سوال (admin_cond_list_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        conditions = get_conditions_by_question(q_id)
        if not conditions:
            await send_message(chat_id, "❌ هیچ شرطی برای این سوال وجود ندارد.")
            return True
        
        keyboard = []
        for cond in conditions:
            ref_q = get_question_by_id(cond['condition_question_id'])
            ref_text = ref_q['question_text'][:20] if ref_q else "نامشخص"
            keyboard.append([
                {"text": f"{ref_text} {cond['condition_operator']} {cond['condition_value']}",
                 "callback_data": f"admin_cond_detail_{cond['id']}"}
            ])
        
        keyboard.append([
            {"text": "➕ افزودن شرط جدید", "callback_data": "admin_condition_add"}
        ])
        keyboard.append([
            {"text": "🔙 برگشت", "callback_data": f"admin_q_{q_id}"}
        ])
        
        user_states[user_id]["current_question_id"] = q_id
        await send_message(chat_id, "🔗 **لیست شرط‌های این سوال**\nبرای مشاهده جزئیات یا ویرایش هر شرط کلیک کنید:", {"inline_keyboard": keyboard})
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_list: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست شرط‌ها.")
        return True


async def handle_condition_detail(chat_id, user_id, data):
    """نمایش جزئیات یک شرط (admin_cond_detail_<condition_id>)"""
    try:
        cond_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه شرط نامعتبر.")
        return True
    
    try:
        cond = get_condition_by_id(cond_id)
        if not cond:
            await send_message(chat_id, "❌ شرط یافت نشد.")
            return True
        
        ref_q = get_question_by_id(cond['condition_question_id'])
        ref_text = ref_q['question_text'] if ref_q else "نامشخص"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "✏️ ویرایش سوال مرجع", "callback_data": f"admin_cond_edit_{cond_id}"}],
                [{"text": "✏️ ویرایش عملگر", "callback_data": f"admin_cond_edit_op_{cond_id}"}],
                [{"text": "✏️ ویرایش مقدار", "callback_data": f"admin_cond_edit_value_{cond_id}"}],
                [{"text": "🗑️ حذف شرط", "callback_data": f"admin_cond_del_{cond_id}"}],
                [{"text": "🔙 برگشت", "callback_data": f"admin_cond_list_{cond['question_id']}"}]
            ]
        }
        
        msg = f"🔗 **جزئیات شرط**\n"
        msg += f"سوال مرجع: {ref_text}\n"
        msg += f"عملگر: {cond['condition_operator']}\n"
        msg += f"مقدار: {cond['condition_value']}\n"
        msg += f"منطق: {cond.get('logic_operator', 'AND')}"
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_condition_detail: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات شرط.")
        return True


# ========== توابع شرط برای سوال جدید ==========

async def handle_question_condition_skip(chat_id, user_id):
    """ذخیره سوال بدون شرط (admin_question_condition_skip)"""
    try:
        btn_id = user_states.get(user_id, {}).get("btn_id")
        question_text = user_states.get(user_id, {}).get("temp_question_text")
        
        if not btn_id or not question_text:
            await send_message(chat_id, "❌ خطا در افزودن سوال.")
            return True
        
        array_name = f"answer_{btn_id}_{int(datetime.now().timestamp())}"
        add_question(btn_id, question_text, needs_button=0, array_name=array_name)
        
        user_states[user_id].pop("temp_question_text", None)
        user_states[user_id]["state"] = "main"
        
        logger.info(f"سوال جدید بدون شرط اضافه شد: {question_text} (دکمه {btn_id})")
        await send_message(chat_id, f"✅ سوال «{question_text}» با موفقیت افزوده شد.", admin_questions_keyboard(btn_id))
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_condition_skip: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در افزودن سوال.")
        return True


async def handle_question_condition_yes(chat_id, user_id):
    """شروع افزودن شرط برای سوال جدید (admin_condition_yes)"""
    try:
        btn_id = user_states.get(user_id, {}).get("btn_id")
        question_text = user_states.get(user_id, {}).get("temp_question_text")
        
        if not btn_id or not question_text:
            await send_message(chat_id, "❌ خطا.")
            return True
        
        previous_questions = get_previous_questions(btn_id, None)
        if not previous_questions:
            await send_message(chat_id, "❌ هیچ سوال قبلی برای شرط وجود ندارد. سوال بدون شرط ذخیره می‌شود.")
            array_name = f"answer_{btn_id}_{int(datetime.now().timestamp())}"
            add_question(btn_id, question_text, needs_button=0, array_name=array_name)
            user_states[user_id].pop("temp_question_text", None)
            user_states[user_id]["state"] = "main"
            await send_message(chat_id, f"✅ سوال «{question_text}» با موفقیت افزوده شد.", admin_questions_keyboard(btn_id))
            return True
        
        keyboard = []
        for pq in previous_questions:
            keyboard.append([{"text": f"{pq['question_text'][:30]}", "callback_data": f"admin_q_condition_ref_{pq['id']}"}])
        keyboard.append([{"text": "🔙 انصراف", "callback_data": "admin_back"}])
        
        user_states[user_id]["state"] = "admin_question_condition_ref"
        await send_message(chat_id, "🔹 **انتخاب سوال مرجع برای شرط**\nلطفاً سوالی که پاسخ آن برای نمایش این سوال بررسی می‌شود را انتخاب کنید:", {"inline_keyboard": keyboard})
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_condition_yes: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا.")
        return True


async def handle_question_condition_no(chat_id, user_id):
    """ذخیره سوال بدون شرط (admin_condition_no)"""
    try:
        btn_id = user_states.get(user_id, {}).get("btn_id")
        question_text = user_states.get(user_id, {}).get("temp_question_text")
        
        if not btn_id or not question_text:
            await send_message(chat_id, "❌ خطا در افزودن سوال.")
            return True
        
        array_name = f"answer_{btn_id}_{int(datetime.now().timestamp())}"
        add_question(btn_id, question_text, needs_button=0, array_name=array_name)
        
        user_states[user_id].pop("temp_question_text", None)
        user_states[user_id]["state"] = "main"
        
        logger.info(f"سوال جدید بدون شرط اضافه شد: {question_text} (دکمه {btn_id})")
        await send_message(chat_id, f"✅ سوال «{question_text}» با موفقیت افزوده شد.", admin_questions_keyboard(btn_id))
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_condition_no: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در افزودن سوال.")
        return True


async def handle_question_condition_ref(chat_id, user_id, data):
    """پردازش انتخاب سوال مرجع برای شرط سوال جدید (admin_q_condition_ref_<question_id>)"""
    try:
        ref_q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        user_states[user_id]["condition_ref_id"] = ref_q_id
        user_states[user_id]["state"] = "admin_question_condition_operator"
        await send_message(chat_id, "🔹 **انتخاب عملگر شرط**\nلطفاً عملگر مورد نظر را انتخاب کنید:", condition_operator_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_condition_ref: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب سوال مرجع.")
        return True


async def handle_question_condition_operator(chat_id, user_id, data):
    """پردازش انتخاب عملگر شرط برای سوال جدید (admin_q_condition_op_*)"""
    try:
        operator = data.split("_")[4]
        user_states[user_id]["condition_operator"] = operator
        user_states[user_id]["state"] = "admin_question_condition_value"
        await send_message(chat_id, "🔹 **مقدار شرط**\nلطفاً مقدار مورد نظر را وارد کنید:")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_condition_operator: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب عملگر.")
        return True


__all__ = [
    'handle_condition_add_start',
    'handle_condition_ref',
    'handle_condition_operator',
    'handle_condition_logic',
    'handle_condition_delete',
    'handle_condition_edit_start',
    'handle_condition_edit_ref',
    'handle_condition_edit_operator',
    'handle_condition_edit_value',
    'handle_condition_list',
    'handle_condition_detail',
    'handle_question_condition_skip',
    'handle_question_condition_yes',
    'handle_question_condition_no',
    'handle_question_condition_ref',
    'handle_question_condition_operator',
]