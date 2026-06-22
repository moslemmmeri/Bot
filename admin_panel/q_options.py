# admin_panel/q_options.py
# مدیریت گزینه‌های دکمه‌ای سوالات در پنل ادمین - نسخه async با logging
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states
from database import get_db_connection, get_question_by_id, get_options_by_question
from keyboards import admin_main_keyboard, admin_question_options_keyboard
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error
)


async def handle_option_list(chat_id, user_id, data):
    """نمایش لیست گزینه‌های یک سوال (admin_qopt_list_<question_id>)"""
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
        
        await send_message(chat_id, f"🔘 **گزینه‌های سوال:**\n{q['question_text']}", admin_question_options_keyboard(q_id))
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_option_list for question {q_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش گزینه‌ها.")
        return True


async def handle_option_add(chat_id, user_id, data):
    """شروع فرآیند افزودن گزینه جدید (admin_qopt_add_<question_id>)"""
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
        
        user_states[user_id] = {"state": "admin_add_question_option", "q_id": q_id}
        await send_message(chat_id, f"➕ **افزودن گزینه جدید برای سوال:**\n{q['question_text']}\n\nلطفاً متن گزینه را وارد کنید:")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_option_add for question {q_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع افزودن گزینه.")
        return True


async def handle_option_detail(chat_id, user_id, data):
    """نمایش جزئیات یک گزینه (admin_qopt_<option_id>)"""
    try:
        opt_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه گزینه نامعتبر.")
        return True
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM question_options WHERE id = ?", (opt_id,))
            opt = cursor.fetchone()
        
        if not opt:
            await send_message(chat_id, "❌ گزینه یافت نشد.")
            return True
        
        opt = dict(opt)
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "✏️ ویرایش", "callback_data": f"admin_qopt_edit_{opt_id}"}],
                [{"text": "🗑️ حذف", "callback_data": f"admin_qopt_del_{opt_id}"}],
                [{"text": "🔙 برگشت", "callback_data": f"admin_qopt_list_{opt['question_id']}"}]
            ]
        }
        
        await send_message(chat_id, f"🔘 **{opt['option_text']}**", keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_option_detail for option {opt_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات گزینه.")
        return True


async def handle_option_edit(chat_id, user_id, data):
    """شروع ویرایش گزینه (admin_qopt_edit_<option_id>)"""
    try:
        opt_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه گزینه نامعتبر.")
        return True
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM question_options WHERE id = ?", (opt_id,))
            opt = cursor.fetchone()
        
        if not opt:
            await send_message(chat_id, "❌ گزینه یافت نشد.")
            return True
        
        opt = dict(opt)
        user_states[user_id] = {"state": "admin_edit_question_option", "opt_id": opt_id}
        await send_message(chat_id, f"✏️ **ویرایش گزینه**\nمتن فعلی: {opt['option_text']}\nلطفاً متن جدید را وارد کنید:")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_option_edit for option {opt_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع ویرایش گزینه.")
        return True


async def handle_option_delete(chat_id, user_id, data):
    """حذف گزینه (admin_qopt_del_<option_id>)"""
    try:
        opt_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه گزینه نامعتبر.")
        return True
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT question_id FROM question_options WHERE id = ?", (opt_id,))
            row = cursor.fetchone()
            
            if not row:
                await send_message(chat_id, "❌ گزینه یافت نشد.")
                return True
            
            question_id = row['question_id']
            
            # حذف گزینه
            cursor.execute("DELETE FROM question_options WHERE id = ?", (opt_id,))
            
            # بررسی تعداد گزینه‌های باقی‌مانده
            cursor.execute("SELECT COUNT(*) as count FROM question_options WHERE question_id = ?", (question_id,))
            count_row = cursor.fetchone()
            
            # اگر گزینه‌ای باقی نمانده، needs_button را 0 کن
            if count_row and count_row['count'] == 0:
                cursor.execute("UPDATE questions SET needs_button = 0 WHERE id = ?", (question_id,))
                logger.info(f"نیاز به دکمه برای سوال {question_id} غیرفعال شد (چون گزینه‌ای باقی نمانده است)")
            
            conn.commit()
        
        logger.info(f"گزینه {opt_id} با موفقیت حذف شد (توسط کاربر {user_id})")
        await send_message(chat_id, "✅ گزینه با موفقیت حذف شد.", admin_main_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_option_delete for option {opt_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف گزینه.")
        return True


__all__ = [
    'handle_option_list',
    'handle_option_add',
    'handle_option_detail',
    'handle_option_edit',
    'handle_option_delete',
]