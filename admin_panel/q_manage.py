# admin_panel/q_manage.py
# مدیریت سوالات در پنل ادمین - نسخه اصلاح‌شده با مدیریت user_states
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states
from database import (
    get_question_by_id,
    get_questions_by_button,
    add_question,
    update_question,
    delete_question,
    delete_options_by_question,
    delete_conditions_by_question,
    get_conditions_by_question
)
from keyboards import admin_main_keyboard, admin_questions_keyboard
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error
)


async def handle_question_manage(chat_id, user_id, data):
    """نمایش لیست سوالات یک دکمه (admin_q_manage_<button_id>)"""
    try:
        btn_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True
    
    try:
        # اطمینان از وجود user_id در user_states
        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["current_btn"] = btn_id
        
        keyboard = admin_questions_keyboard(btn_id)
        if not keyboard:
            await send_message(chat_id, "⚠️ هیچ سوالی برای این دکمه تعریف نشده است.")
            return True
        
        await send_message(chat_id, f"❓ **سوالات این دکمه**", keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_manage for button {btn_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در نمایش سوالات: {str(e)}")
        return True


async def handle_question_add_start(chat_id, user_id, data):
    """شروع فرآیند افزودن سوال جدید (admin_q_add_<button_id>)"""
    try:
        btn_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True
    
    try:
        # اطمینان از وجود user_id در user_states
        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["state"] = "admin_add_question_text"
        user_states[user_id]["btn_id"] = btn_id
        
        await send_message(chat_id, "➕ **افزودن سوال جدید**\nلطفاً متن سوال را وارد کنید:")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_add_start for button {btn_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع افزودن سوال.")
        return True


async def handle_question_detail(chat_id, user_id, data):
    """نمایش جزئیات یک سوال (admin_q_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        q = get_question_by_id(q_id)
        if not q:
            await send_message(chat_id, "❌ سوال یافت نشد.")
            return True
        
        # اطمینان از وجود user_id در user_states
        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["current_question_id"] = q_id
        user_states[user_id]["current_btn"] = q['button_id']
        
        conditions = get_conditions_by_question(q_id)
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔘 مدیریت گزینه‌ها", "callback_data": f"admin_qopt_list_{q_id}"}],
                [{"text": "✏️ ویرایش متن", "callback_data": f"admin_q_edit_{q_id}"}],
                [{"text": "🔧 مدیریت اعتبارسنجی", "callback_data": f"admin_q_validation_{q_id}"}],
                [{"text": "🗑️ حذف سوال", "callback_data": f"admin_q_del_{q_id}"}]
            ]
        }
        
        if conditions:
            keyboard["inline_keyboard"].append(
                [{"text": f"🔗 مدیریت شرط‌ها ({len(conditions)} شرط)", "callback_data": f"admin_cond_list_{q_id}"}]
            )
        else:
            keyboard["inline_keyboard"].append(
                [{"text": "➕ افزودن شرط", "callback_data": "admin_condition_add"}]
            )
        
        keyboard["inline_keyboard"].append(
            [{"text": "🔙 برگشت", "callback_data": f"admin_q_manage_{q['button_id']}"}]
        )
        
        msg = f"❓ **{q['question_text']}**\nنوع: {q.get('question_type', 'text')}\nآرایه: {q.get('array_name') or 'ندارد'}\n"
        msg += f"گزینه‌ها: {'دارد' if q.get('needs_button', 0) == 1 else 'ندارد'}\n"
        msg += f"اجباری: {'بله' if q.get('is_required', 0) == 1 else 'خیر'}\n"
        msg += f"اعتبارسنجی: {'فعال' if q.get('validation_enabled', 0) == 1 else 'غیرفعال'}\n"
        
        if conditions:
            msg += f"🔗 تعداد شرط‌ها: {len(conditions)}\n"
            for i, cond in enumerate(conditions):
                ref_q = get_question_by_id(cond['condition_question_id'])
                ref_text = ref_q['question_text'][:20] if ref_q else "نامشخص"
                logic = cond.get('logic_operator', 'AND') if i < len(conditions)-1 else ""
                msg += f"  {i+1}. {ref_text} {cond['condition_operator']} {cond['condition_value']} {logic}\n"
        else:
            msg += "🔗 شرط: ندارد"
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_detail for question {q_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سوال.")
        return True


async def handle_question_delete(chat_id, user_id, data):
    """حذف سوال و گزینه‌ها و شرط‌های آن (admin_q_del_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        q = get_question_by_id(q_id)
        if not q:
            await send_message(chat_id, "❌ سوال یافت نشد.")
            return True
        
        delete_question(q_id)
        delete_options_by_question(q_id)
        delete_conditions_by_question(q_id)
        
        logger.info(f"سوال {q_id} با موفقیت حذف شد (توسط کاربر {user_id})")
        await send_message(chat_id, f"✅ سوال «{q['question_text']}» با موفقیت حذف شد.", admin_main_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_delete for question {q_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف سوال.")
        return True


async def handle_question_edit(chat_id, user_id, data):
    """شروع ویرایش متن سوال (admin_q_edit_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        q = get_question_by_id(q_id)
        if not q:
            await send_message(chat_id, "❌ سوال یافت نشد.")
            return True
        
        # اطمینان از وجود user_id در user_states
        if user_id not in user_states:
            user_states[user_id] = {}
        user_states[user_id]["state"] = "admin_edit_question_text"
        user_states[user_id]["q_id"] = q_id
        
        await send_message(chat_id, f"✏️ **ویرایش متن سوال**\nمتن فعلی: {q['question_text']}\nلطفاً متن جدید را وارد کنید:")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_edit for question {q_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع ویرایش سوال.")
        return True


async def handle_question_back(chat_id, user_id, data):
    """بازگشت به لیست سوالات دکمه (admin_q_back_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        q = get_question_by_id(q_id)
        if not q:
            await send_message(chat_id, "❌ سوال یافت نشد.")
            return True
        
        keyboard = admin_questions_keyboard(q['button_id'])
        if not keyboard:
            await send_message(chat_id, "⚠️ هیچ سوالی برای این دکمه تعریف نشده است.")
            return True
        
        await send_message(chat_id, f"❓ **سوالات این دکمه**", keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_back for question {q_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در بازگشت به لیست سوالات.")
        return True


__all__ = [
    'handle_question_manage',
    'handle_question_add_start',
    'handle_question_detail',
    'handle_question_delete',
    'handle_question_edit',
    'handle_question_back',
]