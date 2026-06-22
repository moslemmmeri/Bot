# admin_panel/template_routes.py
# ثبت روت‌های مربوط به مدیریت الگوهای سوال در پنل مدیریت
# شامل: ایجاد، ویرایش، حذف، کپی، استخراج و اعمال الگوها

from .router import route, extract_params
from .templates import (
    handle_templates,
    handle_template_list,
    handle_template_detail,
    handle_template_create,
    handle_template_create_empty,
    handle_template_copy,
    handle_template_copy_select,
    handle_template_extract,
    handle_template_extract_btn,
    handle_template_save,
    handle_template_delete,
    handle_template_delete_confirm,
    handle_template_apply,
    handle_template_apply_select,
    handle_template_apply_btn,
    handle_template_apply_confirm,  # این جایگزین handle_template_apply_execute شده
    handle_template_message,
    handle_template_qtype,
    handle_template_qtype_back,
    handle_template_qsetting,
    _get_templates,
    _get_template_by_id,
    _save_template,
    _delete_template,
)
from core import send_message, user_states
from logger_config import logger


# ============================================================
# تابع کمکی برای استخراج شناسه از دیتا
# ============================================================

def _extract_id(data: str, position: int = -1) -> int:
    """استخراج شناسه از دیتا"""
    try:
        return int(data.split("_")[position])
    except (ValueError, IndexError):
        return 0


def _extract_ids(data: str, count: int = 2) -> list:
    """استخراج چند شناسه از دیتا"""
    try:
        parts = data.split("_")
        return [int(p) for p in parts[-count:] if p.isdigit()]
    except (ValueError, IndexError):
        return []


# ============================================================
# روت‌های اصلی مدیریت الگوها
# ============================================================

@route("admin_templates")
async def admin_templates(update):
    """نمایش منوی اصلی مدیریت الگوها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_templates(chat_id, user_id)


# ============================================================
# روت‌های لیست و جزئیات الگوها
# ============================================================

@route("admin_template_list")
async def admin_template_list(update):
    """نمایش لیست الگوها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_template_list(chat_id, user_id, 0)


@route("admin_template_list_page_")
async def admin_template_list_page(update):
    """صفحه‌بندی لیست الگوها (admin_template_list_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        page = int(data.split("_")[-1])
        return await handle_template_list(chat_id, user_id, page)
    except ValueError:
        await send_message(chat_id, "❌ شماره صفحه نامعتبر.")
        return True


@route("admin_template_detail_")
async def admin_template_detail(update):
    """نمایش جزئیات یک الگو (admin_template_detail_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    template_id = _extract_id(data)
    if not template_id:
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True
    return await handle_template_detail(chat_id, user_id, template_id)


# ============================================================
# روت‌های ایجاد الگوی جدید
# ============================================================

@route("admin_template_create")
async def admin_template_create(update):
    """شروع فرآیند ایجاد الگوی جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_template_create(chat_id, user_id)


@route("admin_template_create_empty")
async def admin_template_create_empty(update):
    """ایجاد الگوی خالی جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_template_create_empty(chat_id, user_id)


@route("admin_template_copy")
async def admin_template_copy(update):
    """شروع فرآیند کپی از الگوی موجود"""
    chat_id, user_id, data = extract_params(update)
    return await handle_template_copy(chat_id, user_id)


@route("admin_template_copy_select_")
async def admin_template_copy_select(update):
    """انتخاب الگو برای کپی (admin_template_copy_select_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    template_id = _extract_id(data)
    if not template_id:
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True
    
    template = _get_template_by_id(template_id)
    if not template:
        await send_message(chat_id, "❌ الگو یافت نشد.")
        return True
    
    import json
    questions = json.loads(template.get('questions_data', '[]'))
    
    user_states[user_id] = {
        "state": "admin_template_create_name",
        "template_questions": questions,
        "template_editing": False,
        "template_is_copy": True,
        "template_source_name": template.get('name')
    }
    
    await send_message(
        chat_id,
        f"📋 **کپی از الگوی «{template.get('name')}»**\n\n"
        f"تعداد سوالات: {len(questions)}\n\n"
        f"مرحله ۱: لطفاً نام جدید الگو را وارد کنید:\n"
        f"(برای انصراف، /cancel را ارسال کنید)"
    )
    return True


@route("admin_template_extract")
async def admin_template_extract(update):
    """شروع فرآیند استخراج الگو از دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_template_extract(chat_id, user_id)


@route("admin_template_extract_btn_")
async def admin_template_extract_btn(update):
    """انتخاب دکمه برای استخراج الگو (admin_template_extract_btn_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    button_id = _extract_id(data)
    if not button_id:
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True
    
    from database import get_questions_by_button, get_button_by_id
    
    button = get_button_by_id(button_id)
    if not button:
        await send_message(chat_id, "❌ دکمه یافت نشد.")
        return True
    
    questions = get_questions_by_button(button_id)
    if not questions:
        await send_message(chat_id, "❌ این دکمه هیچ سوالی ندارد.")
        return True
    
    questions_data = []
    for q in questions:
        q_dict = dict(q)
        q_dict.pop('id', None)
        q_dict.pop('button_id', None)
        q_dict.pop('created_at', None)
        
        from database import get_options_by_question
        options = get_options_by_question(q['id'])
        if options:
            q_dict['options'] = [dict(opt) for opt in options]
            for opt in q_dict['options']:
                opt.pop('id', None)
                opt.pop('question_id', None)
                opt.pop('created_at', None)
                opt.pop('is_active', None)
        
        from database import get_conditions_by_question
        conditions = get_conditions_by_question(q['id'])
        if conditions:
            q_dict['conditions'] = [dict(cond) for cond in conditions]
            for cond in q_dict['conditions']:
                cond.pop('id', None)
                cond.pop('question_id', None)
                cond.pop('created_at', None)
                cond.pop('is_active', None)
        
        questions_data.append(q_dict)
    
    user_states[user_id] = {
        "state": "admin_template_create_name",
        "template_questions": questions_data,
        "template_editing": False,
        "template_is_extract": True,
        "template_source_button": button.get('name')
    }
    
    await send_message(
        chat_id,
        f"📥 **استخراج الگو از دکمه «{button.get('name')}»**\n\n"
        f"تعداد سوالات: {len(questions_data)}\n\n"
        f"مرحله ۱: لطفاً نام الگو را وارد کنید:\n"
        f"(برای انصراف، /cancel را ارسال کنید)"
    )
    return True


@route("admin_template_save")
async def admin_template_save(update):
    """ذخیره الگوی در حال ساخت"""
    chat_id, user_id, data = extract_params(update)
    return await handle_template_save(chat_id, user_id)


# ============================================================
# روت‌های حذف الگو
# ============================================================

@route("admin_template_delete_")
async def admin_template_delete(update):
    """شروع فرآیند حذف الگو (admin_template_delete_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    template_id = _extract_id(data)
    if not template_id:
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True
    return await handle_template_delete(chat_id, user_id, template_id)


@route("admin_template_delete_confirm_")
async def admin_template_delete_confirm(update):
    """تایید نهایی حذف الگو (admin_template_delete_confirm_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    template_id = _extract_id(data)
    if not template_id:
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True
    return await handle_template_delete_confirm(chat_id, user_id, template_id)


# ============================================================
# روت‌های ویرایش الگو
# ============================================================

@route("admin_template_edit_")
async def admin_template_edit(update):
    """شروع ویرایش الگو (admin_template_edit_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    template_id = _extract_id(data)
    if not template_id:
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True
    
    template = _get_template_by_id(template_id)
    if not template:
        await send_message(chat_id, "❌ الگو یافت نشد.")
        return True
    
    import json
    questions = json.loads(template.get('questions_data', '[]'))
    
    user_states[user_id] = {
        "state": "admin_template_edit_questions",
        "template_id": template_id,
        "template_name": template.get('name'),
        "template_description": template.get('description', ''),
        "template_questions": questions,
        "template_editing": True,
        "template_edit_index": 0
    }
    
    if questions:
        q = questions[0]
        keyboard = {
            "inline_keyboard": [
                [{"text": "✏️ ویرایش متن سوال", "callback_data": f"admin_template_edit_qtext_{template_id}_0"}],
                [{"text": "🔧 ویرایش تنظیمات", "callback_data": f"admin_template_edit_qsettings_{template_id}_0"}],
                [{"text": "🗑️ حذف سوال", "callback_data": f"admin_template_edit_qdelete_{template_id}_0"}],
                [{"text": "➕ افزودن سوال جدید", "callback_data": f"admin_template_edit_qadd_{template_id}"}],
                [{"text": "➡️ سوال بعدی", "callback_data": f"admin_template_edit_next_{template_id}_0"}],
                [{"text": "💾 ذخیره الگو", "callback_data": f"admin_template_edit_save_{template_id}"}],
                [{"text": "🔙 انصراف", "callback_data": f"admin_template_detail_{template_id}"}]
            ]
        }
        
        msg = (
            f"✏️ **ویرایش الگوی «{template.get('name')}»**\n\n"
            f"📋 سوال {1} از {len(questions)}:\n"
            f"📝 {q.get('question_text', 'بدون متن')}\n"
            f"🔧 نوع: {q.get('question_type', 'text')}\n"
            f"⭐ اجباری: {'بله' if q.get('is_required', 0) == 1 else 'خیر'}\n"
            f"🔘 دکمه‌ای: {'بله' if q.get('needs_button', 0) == 1 else 'خیر'}\n"
        )
        
        await send_message(chat_id, msg, keyboard)
    else:
        keyboard = {
            "inline_keyboard": [
                [{"text": "➕ افزودن سوال جدید", "callback_data": f"admin_template_edit_qadd_{template_id}"}],
                [{"text": "💾 ذخیره الگو", "callback_data": f"admin_template_edit_save_{template_id}"}],
                [{"text": "🔙 انصراف", "callback_data": f"admin_template_detail_{template_id}"}]
            ]
        }
        await send_message(
            chat_id,
            f"✏️ **ویرایش الگوی «{template.get('name')}»**\n\n"
            f"⚠️ این الگو هیچ سوالی ندارد.\n\n"
            f"برای افزودن سوال جدید، روی دکمه زیر کلیک کنید:",
            keyboard
        )
    
    return True


# ============================================================
# روت‌های اعمال الگو به دکمه
# ============================================================

@route("admin_template_apply")
async def admin_template_apply(update):
    """نمایش لیست الگوها برای اعمال به دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_template_apply(chat_id, user_id)


@route("admin_template_apply_select_")
async def admin_template_apply_select(update):
    """انتخاب الگو برای اعمال (admin_template_apply_select_<template_id>)"""
    chat_id, user_id, data = extract_params(update)
    template_id = _extract_id(data)
    if not template_id:
        await send_message(chat_id, "❌ شناسه الگو نامعتبر.")
        return True
    return await handle_template_apply_select(chat_id, user_id, template_id)


@route("admin_template_apply_btn_")
async def admin_template_apply_btn(update):
    """انتخاب دکمه برای اعمال الگو (admin_template_apply_btn_<template_id>_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    ids = _extract_ids(data, 2)
    if len(ids) != 2:
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    template_id, button_id = ids
    return await handle_template_apply_btn(chat_id, user_id, template_id, button_id)


@route("admin_template_apply_confirm_")
async def admin_template_apply_confirm(update):
    """تایید نهایی اعمال الگو به دکمه (admin_template_apply_confirm_<template_id>_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    ids = _extract_ids(data, 2)
    if len(ids) != 2:
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    template_id, button_id = ids
    return await handle_template_apply_confirm(chat_id, user_id, template_id, button_id)


# ============================================================
# روت‌های نوع سوال (برای ساخت الگو)
# ============================================================

@route("admin_template_qtype_")
async def admin_template_qtype(update):
    """انتخاب نوع سوال برای الگو (admin_template_qtype_<type>)"""
    chat_id, user_id, data = extract_params(update)
    qtype = data.split("_")[-1]
    
    state_info = user_states.get(user_id, {})
    if state_info.get("state") != "admin_template_question_type":
        await send_message(chat_id, "❌ خطا در انتخاب نوع سوال.")
        return True
    
    question_text = state_info.get("temp_question_text", "")
    
    user_states[user_id]["temp_question_type"] = qtype
    user_states[user_id]["state"] = "admin_template_question_settings"
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "⭐ اجباری", "callback_data": "admin_template_qsetting_required"}],
            [{"text": "✅ ادامه با تنظیمات پیش‌فرض", "callback_data": "admin_template_qsetting_default"}],
            [{"text": "🔙 بازگشت به انتخاب نوع", "callback_data": "admin_template_qtype_back"}]
        ]
    }
    
    if qtype in ["text", "number", "date"]:
        keyboard["inline_keyboard"].insert(1, [{"text": "📏 تنظیمات اعتبارسنجی", "callback_data": "admin_template_qsetting_validation"}])
    
    if qtype == "button":
        keyboard["inline_keyboard"].insert(1, [{"text": "🔘 افزودن گزینه‌ها", "callback_data": "admin_template_qsetting_options"}])
    
    if qtype == "file":
        keyboard["inline_keyboard"].insert(1, [{"text": "📎 تنظیمات فایل", "callback_data": "admin_template_qsetting_file"}])
    
    await send_message(
        chat_id,
        f"📝 **سوال:** {question_text}\n\n"
        f"🔧 **نوع سوال:** {qtype}\n\n"
        f"تنظیمات سوال را انتخاب کنید:",
        keyboard
    )
    return True


@route("admin_template_qtype_back")
async def admin_template_qtype_back(update):
    """بازگشت به انتخاب نوع سوال"""
    chat_id, user_id, data = extract_params(update)
    
    state_info = user_states.get(user_id, {})
    question_text = state_info.get("temp_question_text", "")
    
    if not question_text:
        await send_message(chat_id, "❌ خطا.")
        return True
    
    user_states[user_id]["state"] = "admin_template_question_type"
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "📝 متن آزاد", "callback_data": "admin_template_qtype_text"}],
            [{"text": "🔢 عدد", "callback_data": "admin_template_qtype_number"}],
            [{"text": "📎 فایل", "callback_data": "admin_template_qtype_file"}],
            [{"text": "🔘 گزینه‌ای (دکمه‌ای)", "callback_data": "admin_template_qtype_button"}],
            [{"text": "📅 تاریخ", "callback_data": "admin_template_qtype_date"}],
            [{"text": "✅ تایید (بله/خیر)", "callback_data": "admin_template_qtype_yesno"}]
        ]
    }
    
    await send_message(
        chat_id,
        f"📝 **سوال:** {question_text}\n\n"
        f"نوع سوال را انتخاب کنید:",
        keyboard
    )
    return True


# ============================================================
# روت‌های تنظیمات سوال (برای ساخت الگو)
# ============================================================

@route("admin_template_qsetting_")
async def admin_template_qsetting(update):
    """پردازش تنظیمات سوال (admin_template_qsetting_<action>)"""
    chat_id, user_id, data = extract_params(update)
    action = data.split("_")[-1]
    
    state_info = user_states.get(user_id, {})
    if state_info.get("state") != "admin_template_question_settings":
        await send_message(chat_id, "❌ خطا.")
        return True
    
    question_text = state_info.get("temp_question_text", "")
    qtype = state_info.get("temp_question_type", "text")
    questions = state_info.get("template_questions", [])
    
    if action == "required":
        user_states[user_id]["temp_required"] = not state_info.get("temp_required", False)
        status = "اجباری" if user_states[user_id]["temp_required"] else "اختیاری"
        await send_message(chat_id, f"✅ سوال به حالت «{status}» تنظیم شد.")
        
        keyboard = {
            "inline_keyboard": [
                [{"text": f"⭐ {'غیرفعال' if state_info.get('temp_required', False) else 'فعال'} کردن اجباری", 
                  "callback_data": "admin_template_qsetting_required"}],
                [{"text": "✅ ادامه با تنظیمات فعلی", "callback_data": "admin_template_qsetting_default"}],
                [{"text": "🔙 بازگشت", "callback_data": "admin_template_qtype_back"}]
            ]
        }
        await send_message(
            chat_id,
            f"📝 **سوال:** {question_text}\n\n"
            f"🔧 **وضعیت:** {status}\n\n"
            f"تنظیمات سوال را انتخاب کنید:",
            keyboard
        )
        return True
    
    if action == "default":
        q_data = {
            'question_text': question_text,
            'question_type': qtype,
            'is_required': 1 if state_info.get("temp_required", False) else 0,
            'needs_button': 1 if qtype == "button" else 0,
            'validation_type': 'text' if qtype == "text" else 'number' if qtype == "number" else 'date' if qtype == "date" else 'none',
            'sort_order': len(questions)
        }
        
        if qtype == "button":
            q_data['options'] = [
                {'option_text': 'گزینه ۱', 'callback_data': f'opt_{len(questions)}_1'},
                {'option_text': 'گزینه ۲', 'callback_data': f'opt_{len(questions)}_2'}
            ]
        
        questions.append(q_data)
        user_states[user_id]["template_questions"] = questions
        user_states[user_id].pop("temp_question_text", None)
        user_states[user_id].pop("temp_question_type", None)
        user_states[user_id].pop("temp_required", None)
        user_states[user_id]["state"] = "admin_template_add_question"
        
        await send_message(
            chat_id,
            f"✅ سوال «{question_text}» با موفقیت به الگو اضافه شد.\n\n"
            f"📋 تعداد سوالات فعلی: {len(questions)}\n\n"
            f"سوال بعدی را وارد کنید (یا «پایان» برای اتمام):"
        )
        return True
    
    if action == "validation":
        user_states[user_id]["state"] = "admin_template_question_validation"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "📏 حداقل طول", "callback_data": "admin_template_qval_min_length"}],
                [{"text": "📏 حداکثر طول", "callback_data": "admin_template_qval_max_length"}],
                [{"text": "🔢 حداقل مقدار", "callback_data": "admin_template_qval_min_value"}],
                [{"text": "🔢 حداکثر مقدار", "callback_data": "admin_template_qval_max_value"}],
                [{"text": "✅ ادامه", "callback_data": "admin_template_qval_done"}],
                [{"text": "🔙 بازگشت", "callback_data": "admin_template_qtype_back"}]
            ]
        }
        
        await send_message(
            chat_id,
            f"📝 **سوال:** {question_text}\n\n"
            f"🔧 **تنظیمات اعتبارسنجی**\n\n"
            f"مقادیر مورد نظر را تنظیم کنید:",
            keyboard
        )
        return True
    
    if action == "options":
        user_states[user_id]["state"] = "admin_template_question_options"
        user_states[user_id]["temp_options"] = []
        user_states[user_id]["temp_option_counter"] = 0
        
        await send_message(
            chat_id,
            f"🔘 **سوال:** {question_text}\n\n"
            f"لطفاً گزینه‌های سوال را وارد کنید:\n"
            f"(هر بار یک گزینه وارد کنید)\n"
            f"برای پایان، «پایان» را وارد کنید.\n\n"
            f"مثال: گزینه ۱"
        )
        return True
    
    if action == "file":
        user_states[user_id]["state"] = "admin_template_question_file"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "📎 فرمت‌های مجاز", "callback_data": "admin_template_qfile_formats"}],
                [{"text": "📏 حداکثر حجم (KB)", "callback_data": "admin_template_qfile_max_size"}],
                [{"text": "✅ ادامه", "callback_data": "admin_template_qfile_done"}],
                [{"text": "🔙 بازگشت", "callback_data": "admin_template_qtype_back"}]
            ]
        }
        
        await send_message(
            chat_id,
            f"📎 **سوال:** {question_text}\n\n"
            f"🔧 **تنظیمات فایل**\n\n"
            f"تنظیمات مربوط به فایل را انتخاب کنید:",
            keyboard
        )
        return True
    
    await send_message(chat_id, "❌ گزینه نامعتبر.")
    return True


# ============================================================
# روت‌های پردازش پیام‌های ساخت الگو (برای msg_admin)
# ============================================================

async def handle_template_route_message(chat_id: int, user_id: int, text: str) -> bool:
    """پردازش پیام‌های مربوط به ساخت الگو"""
    return await handle_template_message(chat_id, user_id, text)


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'admin_templates',
    'admin_template_list',
    'admin_template_list_page',
    'admin_template_detail',
    'admin_template_create',
    'admin_template_create_empty',
    'admin_template_copy',
    'admin_template_copy_select',
    'admin_template_extract',
    'admin_template_extract_btn',
    'admin_template_save',
    'admin_template_delete',
    'admin_template_delete_confirm',
    'admin_template_edit',
    'admin_template_apply',
    'admin_template_apply_select',
    'admin_template_apply_btn',
    'admin_template_apply_confirm',
    'admin_template_qtype',
    'admin_template_qtype_back',
    'admin_template_qsetting',
    'handle_template_route_message',
]