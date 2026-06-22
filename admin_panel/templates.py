# admin_panel/templates.py
# مدیریت الگوهای سوال (Question Templates)
# شامل: ایجاد، ویرایش، حذف، کپی، استخراج و اعمال الگوها
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from logger_config import logger
from core import send_message
from database import (
    get_db_connection,
    get_button_by_id,
    get_questions_by_button,
    get_options_by_question,
    get_conditions_by_question,
    add_question,
    add_question_option,
    add_condition,
    delete_question,
    delete_options_by_question,
    delete_conditions_by_question,
)
from keyboards import admin_main_keyboard
from services.permission_service import get_permission_service
from services.state_service import get_state_service
from utils import format_datetime, truncate_text
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error,
    log_security_error
)


# ============================================================
# توابع دیتابیس برای مدیریت الگوها
# ============================================================

def _get_templates() -> List[Dict]:
    """دریافت لیست تمام الگوها"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM question_templates ORDER BY name")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error in _get_templates: {str(e)}",
            traceback=traceback.format_exc()
        )
        return []


def _get_template_by_id(template_id: int) -> Optional[Dict]:
    """دریافت یک الگو بر اساس شناسه"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM question_templates WHERE id = ?", (template_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log_database_error(
            f"Error in _get_template_by_id for {template_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return None


def _get_template_by_name(name: str) -> Optional[Dict]:
    """دریافت یک الگو بر اساس نام"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM question_templates WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        log_database_error(
            f"Error in _get_template_by_name for {name}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return None


def _save_template(name: str, description: str, questions_data: List[Dict], created_by: int) -> Optional[int]:
    """ذخیره یک الگوی جدید"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO question_templates (name, description, questions_data, created_by)
                VALUES (?, ?, ?, ?)
            """, (name, description, json.dumps(questions_data, ensure_ascii=False), created_by))
            conn.commit()
            template_id = cursor.lastrowid
            logger.info(f"✅ Template saved: {name} (id={template_id}) by {created_by}")
            return template_id
    except Exception as e:
        log_database_error(
            f"Error in _save_template: {str(e)}",
            traceback=traceback.format_exc()
        )
        return None


def _update_template(template_id: int, name: str, description: str, questions_data: List[Dict]) -> bool:
    """بروزرسانی یک الگو"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE question_templates 
                SET name = ?, description = ?, questions_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name, description, json.dumps(questions_data, ensure_ascii=False), template_id))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"✅ Template updated: {name} (id={template_id})")
                return True
            return False
    except Exception as e:
        log_database_error(
            f"Error in _update_template for {template_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


def _delete_template(template_id: int) -> bool:
    """حذف یک الگو"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM question_templates WHERE id = ?", (template_id,))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"🗑️ Template deleted: id={template_id}")
                return True
            return False
    except Exception as e:
        log_database_error(
            f"Error in _delete_template for {template_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


# ============================================================
# الگوهای پیش‌فرض
# ============================================================

def _get_default_template() -> Dict:
    return {
        'name': 'الگوی خالی',
        'description': 'یک الگوی خالی برای شروع',
        'questions': [
            {
                'question_text': 'نام کامل خود را وارد کنید:',
                'question_type': 'text',
                'is_required': 1,
                'validation_type': 'text',
                'needs_button': 0,
                'sort_order': 0
            },
            {
                'question_text': 'شماره تماس خود را وارد کنید:',
                'question_type': 'text',
                'is_required': 1,
                'validation_type': 'phone',
                'needs_button': 0,
                'sort_order': 1
            }
        ]
    }


PRESET_TEMPLATES = {
    'default': _get_default_template,
}


def init_default_templates():
    """مقداردهی اولیه الگوهای پیش‌فرض در دیتابیس"""
    try:
        templates = _get_templates()
        if templates:
            logger.info(f"ℹ️ Found {len(templates)} existing templates, skipping default initialization")
            return

        for key, template_func in PRESET_TEMPLATES.items():
            template = template_func()
            _save_template(
                name=template['name'],
                description=template['description'],
                questions_data=template['questions'],
                created_by=1
            )
            logger.info(f"✅ Default template created: {template['name']}")

        logger.info("✅ All default templates initialized")
    except Exception as e:
        log_database_error(
            f"Error in init_default_templates: {str(e)}",
            traceback=traceback.format_exc()
        )


# ============================================================
# کیبوردها
# ============================================================

def templates_main_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "📋 لیست الگوها", "callback_data": "admin_template_list"}],
            [{"text": "➕ ایجاد الگوی جدید", "callback_data": "admin_template_create"}],
            [{"text": "📥 استفاده از الگو در دکمه", "callback_data": "admin_template_apply"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


def templates_list_keyboard(templates: List[Dict], page: int = 0, per_page: int = 5) -> dict:
    total = len(templates)
    start = page * per_page
    end = min(start + per_page, total)
    page_templates = templates[start:end]

    keyboard = []
    for tmpl in page_templates:
        tmpl_id = tmpl.get('id')
        name = tmpl.get('name', 'بدون نام')
        created_at = format_datetime(tmpl.get('created_at'))
        keyboard.append([
            {"text": f"📄 {name} ({created_at})",
             "callback_data": f"admin_template_detail_{tmpl_id}"}
        ])

    if not templates:
        keyboard.append([{"text": "❌ هیچ الگویی یافت نشد", "callback_data": "admin_none"}])
        keyboard.append([{"text": "➕ ایجاد الگوی جدید", "callback_data": "admin_template_create"}])

    nav_row = []
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    if page > 0:
        nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_template_list_page_{page-1}"})
    if page < total_pages - 1:
        nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_template_list_page_{page+1}"})
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([{"text": "🔙 برگشت به مدیریت الگوها", "callback_data": "admin_templates"}])
    return {"inline_keyboard": keyboard}


def template_detail_keyboard(template_id: int) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "✏️ ویرایش", "callback_data": f"admin_template_edit_{template_id}"}],
            [{"text": "🗑️ حذف", "callback_data": f"admin_template_delete_{template_id}"}],
            [{"text": "📥 اعمال به دکمه", "callback_data": f"admin_template_apply_select_{template_id}"}],
            [{"text": "🔙 برگشت به لیست", "callback_data": "admin_template_list"}]
        ]
    }


def template_confirm_keyboard(template_id: int, button_id: int) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "⚠️ آیا از اعمال الگو به این دکمه مطمئن هستید؟"}],
            [{"text": "⚠️ سوالات فعلی دکمه حذف می‌شوند!"}],
            [{"text": "✅ بله، اعمال شود", "callback_data": f"admin_template_apply_confirm_{template_id}_{button_id}"}],
            [{"text": "❌ انصراف", "callback_data": "admin_templates"}]
        ]
    }


# ============================================================
# توابع اصلی مدیریت الگوها
# ============================================================

async def handle_templates(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        templates = _get_templates()
        msg = (
            f"📝 **مدیریت الگوهای سوال**\n\n"
            f"از این بخش می‌توانید:\n"
            f"• ایجاد و ذخیره الگوهای سوال\n"
            f"• استفاده از الگوها برای دکمه‌ها\n"
            f"• ویرایش و حذف الگوها\n\n"
            f"📊 تعداد کل الگوها: {len(templates)}\n\n"
            f"لطفاً گزینه مورد نظر را انتخاب کنید:"
        )
        await send_message(chat_id, msg, templates_main_keyboard())
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_templates: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش مدیریت الگوها.")
        return True


async def handle_template_list(chat_id: int, user_id: int, page: int = 0) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        templates = _get_templates()
        keyboard = templates_list_keyboard(templates, page)
        await send_message(
            chat_id,
            f"📋 **لیست الگوها**\n\nتعداد کل: {len(templates)} الگو\nبرای مشاهده جزئیات هر الگو کلیک کنید:",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_list: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست الگوها.")
        return True


async def handle_template_list_page(chat_id: int, user_id: int, page: int) -> bool:
    return await handle_template_list(chat_id, user_id, page)


async def handle_template_detail(chat_id: int, user_id: int, template_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        template = _get_template_by_id(template_id)
        if not template:
            await send_message(chat_id, "❌ الگو یافت نشد.")
            return True

        questions = json.loads(template.get('questions_data', '[]'))

        msg = (
            f"📄 **جزئیات الگو**\n\n"
            f"📌 نام: {template.get('name')}\n"
            f"📝 توضیحات: {template.get('description', 'بدون توضیح')}\n"
            f"👤 ایجادکننده: {template.get('created_by', 'نامشخص')}\n"
            f"📅 تاریخ ایجاد: {format_datetime(template.get('created_at'))}\n"
            f"📅 آخرین بروزرسانی: {format_datetime(template.get('updated_at'))}\n\n"
            f"📋 **سوالات ({len(questions)} مورد):**\n"
        )

        for i, q in enumerate(questions, 1):
            q_text = q.get('question_text', 'بدون متن')
            is_required = "⭐" if q.get('is_required', 0) == 1 else ""
            has_options = "🔘" if q.get('needs_button', 0) == 1 else ""
            msg += f"  {i}. {q_text} {is_required}{has_options}\n"

        keyboard = template_detail_keyboard(template_id)
        await send_message(chat_id, msg, keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_detail for {template_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات الگو.")
        return True


async def handle_template_create(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        keyboard = {
            "inline_keyboard": [
                [{"text": "🆕 شروع از صفر", "callback_data": "admin_template_create_empty"}],
                [{"text": "📋 کپی از الگوی موجود", "callback_data": "admin_template_copy"}],
                [{"text": "📥 استخراج از دکمه موجود", "callback_data": "admin_template_extract"}],
                [{"text": "🔙 انصراف", "callback_data": "admin_templates"}]
            ]
        }

        await send_message(
            chat_id,
            "➕ **ایجاد الگوی جدید**\n\nچگونه می‌خواهید الگو را ایجاد کنید؟",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_create: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع ایجاد الگو.")
        return True


async def handle_template_create_empty(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        state_service = get_state_service()
        await state_service.update_state(user_id, {
            "state": "admin_template_create_name",
            "template_questions": [],
            "template_editing": False
        })

        await send_message(
            chat_id,
            "➕ **ایجاد الگوی جدید - مرحله ۱**\n\n"
            "لطفاً نام الگو را وارد کنید:\n"
            "(مثال: «اطلاعات تماس پایه»)\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_create_empty: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ایجاد الگو.")
        return True


async def handle_template_copy(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        templates = _get_templates()
        if not templates:
            await send_message(
                chat_id,
                "❌ هیچ الگویی برای کپی وجود ندارد.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "admin_templates"}]]}
            )
            return True

        keyboard = []
        for tmpl in templates:
            keyboard.append([
                {"text": f"📄 {tmpl.get('name')}",
                 "callback_data": f"admin_template_copy_select_{tmpl.get('id')}"}
            ])
        keyboard.append([{"text": "🔙 انصراف", "callback_data": "admin_templates"}])

        await send_message(
            chat_id,
            "📋 **انتخاب الگو برای کپی**\n\nلطفاً الگویی که می‌خواهید کپی کنید را انتخاب کنید:",
            {"inline_keyboard": keyboard}
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_copy: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در کپی الگو.")
        return True


async def handle_template_copy_select(chat_id: int, user_id: int, template_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        template = _get_template_by_id(template_id)
        if not template:
            await send_message(chat_id, "❌ الگو یافت نشد.")
            return True

        questions = json.loads(template.get('questions_data', '[]'))
        state_service = get_state_service()
        await state_service.update_state(user_id, {
            "state": "admin_template_create_name",
            "template_questions": questions,
            "template_editing": False,
            "template_is_copy": True,
            "template_source_name": template.get('name')
        })

        await send_message(
            chat_id,
            f"📋 **کپی از الگوی «{template.get('name')}»**\n\n"
            f"تعداد سوالات: {len(questions)}\n\n"
            f"مرحله ۱: لطفاً نام جدید الگو را وارد کنید:\n"
            f"(برای انصراف، /cancel را ارسال کنید)"
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_copy_select for {template_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب الگو برای کپی.")
        return True


async def handle_template_extract(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        from database import get_all_buttons
        buttons = get_all_buttons()

        if not buttons:
            await send_message(
                chat_id,
                "❌ هیچ دکمه‌ای برای استخراج وجود ندارد.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "admin_templates"}]]}
            )
            return True

        keyboard = []
        for btn in buttons:
            questions = get_questions_by_button(btn['id'])
            if questions:
                icon = "📂" if btn.get('has_submenu', 0) == 1 else "🔘"
                keyboard.append([
                    {"text": f"{icon} {btn['name']} ({len(questions)} سوال)",
                     "callback_data": f"admin_template_extract_btn_{btn['id']}"}
                ])

        if not keyboard:
            await send_message(
                chat_id,
                "❌ هیچ دکمه‌ای با سوال یافت نشد.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "admin_templates"}]]}
            )
            return True

        keyboard.append([{"text": "🔙 انصراف", "callback_data": "admin_templates"}])

        await send_message(
            chat_id,
            "📥 **استخراج الگو از دکمه**\n\nلطفاً دکمه‌ای که می‌خواهید الگوی آن را استخراج کنید انتخاب کنید:",
            {"inline_keyboard": keyboard}
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_extract: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در استخراج الگو.")
        return True


async def handle_template_extract_btn(chat_id: int, user_id: int, button_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

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

            options = get_options_by_question(q['id'])
            if options:
                q_dict['options'] = [dict(opt) for opt in options]
                for opt in q_dict['options']:
                    opt.pop('id', None)
                    opt.pop('question_id', None)
                    opt.pop('created_at', None)
                    opt.pop('is_active', None)

            conditions = get_conditions_by_question(q['id'])
            if conditions:
                q_dict['conditions'] = [dict(cond) for cond in conditions]
                for cond in q_dict['conditions']:
                    cond.pop('id', None)
                    cond.pop('question_id', None)
                    cond.pop('created_at', None)
                    cond.pop('is_active', None)

            questions_data.append(q_dict)

        state_service = get_state_service()
        await state_service.update_state(user_id, {
            "state": "admin_template_create_name",
            "template_questions": questions_data,
            "template_editing": False,
            "template_is_extract": True,
            "template_source_button": button.get('name')
        })

        await send_message(
            chat_id,
            f"📥 **استخراج الگو از دکمه «{button.get('name')}»**\n\n"
            f"تعداد سوالات: {len(questions_data)}\n\n"
            f"مرحله ۱: لطفاً نام الگو را وارد کنید:\n"
            f"(برای انصراف، /cancel را ارسال کنید)"
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_extract_btn for {button_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در استخراج الگو.")
        return True


async def handle_template_save(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        state_service = get_state_service()
        state_info = await state_service.get_state(user_id, {})
        questions = state_info.get("template_questions", [])
        template_name = state_info.get("template_name", "الگوی جدید")
        description = state_info.get("template_description", "")

        if not questions:
            await send_message(chat_id, "❌ هیچ سوالی برای ذخیره وجود ندارد.")
            return True

        template_id = _save_template(template_name, description, questions, user_id)

        if template_id:
            await send_message(
                chat_id,
                f"✅ الگوی «{template_name}» با موفقیت ذخیره شد.\n\n"
                f"📋 تعداد سوالات: {len(questions)}",
                templates_main_keyboard()
            )
            await state_service.set_state(user_id, {"state": "main"})
        else:
            await send_message(chat_id, "❌ خطا در ذخیره الگو.")

        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_save: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ذخیره الگو.")
        return True


async def handle_template_edit(chat_id: int, user_id: int, template_id: int) -> bool:
    """
    شروع ویرایش یک الگو
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        template = _get_template_by_id(template_id)
        if not template:
            await send_message(chat_id, "❌ الگو یافت نشد.")
            return True

        questions = json.loads(template.get('questions_data', '[]'))

        state_service = get_state_service()
        await state_service.update_state(user_id, {
            "state": "admin_template_edit_name",
            "template_id": template_id,
            "template_name": template.get('name'),
            "template_description": template.get('description', ''),
            "template_questions": questions,
        })

        await send_message(
            chat_id,
            f"✏️ **ویرایش الگو: {template.get('name')}**\n\n"
            f"مرحله ۱: نام جدید الگو را وارد کنید:\n"
            f"(برای انصراف، /cancel را ارسال کنید)"
        )
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_template_edit for {template_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع ویرایش الگو.")
        return True


async def handle_template_delete(chat_id: int, user_id: int, template_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        template = _get_template_by_id(template_id)
        if not template:
            await send_message(chat_id, "❌ الگو یافت نشد.")
            return True

        keyboard = {
            "inline_keyboard": [
                [{"text": f"⚠️ آیا از حذف الگوی «{template.get('name')}» مطمئن هستید؟"}],
                [{"text": "✅ بله، حذف شود", "callback_data": f"admin_template_delete_confirm_{template_id}"}],
                [{"text": "❌ انصراف", "callback_data": f"admin_template_detail_{template_id}"}]
            ]
        }

        await send_message(chat_id, f"🗑️ **حذف الگو**\n\nالگوی «{template.get('name')}» حذف خواهد شد.", keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_delete for {template_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف الگو.")
        return True


async def handle_template_delete_confirm(chat_id: int, user_id: int, template_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        template = _get_template_by_id(template_id)
        if not template:
            await send_message(chat_id, "❌ الگو یافت نشد.")
            return True

        success = _delete_template(template_id)

        if success:
            await send_message(
                chat_id,
                f"✅ الگوی «{template.get('name')}» با موفقیت حذف شد.",
                templates_main_keyboard()
            )
        else:
            await send_message(chat_id, "❌ خطا در حذف الگو.")

        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_delete_confirm for {template_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف الگو.")
        return True


# ============================================================
# اعمال الگو به دکمه
# ============================================================

async def handle_template_apply(chat_id: int, user_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        templates = _get_templates()
        if not templates:
            await send_message(
                chat_id,
                "❌ هیچ الگویی موجود نیست.\nابتدا یک الگو ایجاد کنید.",
                {"inline_keyboard": [[{"text": "➕ ایجاد الگو", "callback_data": "admin_template_create"}]]}
            )
            return True

        keyboard = []
        for tmpl in templates:
            keyboard.append([
                {"text": f"📄 {tmpl.get('name')}",
                 "callback_data": f"admin_template_apply_select_{tmpl.get('id')}"}
            ])
        keyboard.append([{"text": "🔙 انصراف", "callback_data": "admin_templates"}])

        await send_message(
            chat_id,
            "📥 **اعمال الگو به دکمه**\n\nالگوی مورد نظر را انتخاب کنید:",
            {"inline_keyboard": keyboard}
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_apply: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در اعمال الگو.")
        return True


async def handle_template_apply_select(chat_id: int, user_id: int, template_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        template = _get_template_by_id(template_id)
        if not template:
            await send_message(chat_id, "❌ الگو یافت نشد.")
            return True

        from database import get_all_buttons
        buttons = get_all_buttons()

        if not buttons:
            await send_message(
                chat_id,
                "❌ هیچ دکمه‌ای برای اعمال الگو وجود ندارد.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "admin_templates"}]]}
            )
            return True

        keyboard = []
        for btn in buttons:
            icon = "📂" if btn.get('has_submenu', 0) == 1 else "🔘"
            questions_count = len(get_questions_by_button(btn['id']))
            keyboard.append([
                {"text": f"{icon} {btn['name']} ({questions_count} سوال فعلی)",
                 "callback_data": f"admin_template_apply_btn_{template_id}_{btn['id']}"}
            ])
        keyboard.append([{"text": "🔙 انصراف", "callback_data": "admin_templates"}])

        await send_message(
            chat_id,
            f"📥 **اعمال الگوی «{template.get('name')}» به دکمه**\n\n"
            f"لطفاً دکمه‌ی مورد نظر را انتخاب کنید:\n"
            f"(سوالات فعلی دکمه حذف می‌شوند)",
            {"inline_keyboard": keyboard}
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_apply_select for {template_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب دکمه.")
        return True


async def handle_template_apply_btn(chat_id: int, user_id: int, template_id: int, button_id: int) -> bool:
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        template = _get_template_by_id(template_id)
        if not template:
            await send_message(chat_id, "❌ الگو یافت نشد.")
            return True

        button = get_button_by_id(button_id)
        if not button:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True

        keyboard = template_confirm_keyboard(template_id, button_id)

        await send_message(
            chat_id,
            f"⚠️ **تایید اعمال الگو**\n\n"
            f"📌 الگو: {template.get('name')}\n"
            f"🔘 دکمه: {button.get('name')}\n\n"
            f"⚠️ **هشدار:**\n"
            f"همه سوالات فعلی دکمه حذف می‌شوند.\n\n"
            f"آیا مطمئن هستید؟",
            keyboard
        )
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_apply_btn for {template_id}->{button_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تایید اعمال الگو.")
        return True


async def handle_template_apply_confirm(chat_id: int, user_id: int, template_id: int, button_id: int) -> bool:
    """
    تایید نهایی اعمال الگو به دکمه (اجرای واقعی)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        template = _get_template_by_id(template_id)
        if not template:
            await send_message(chat_id, "❌ الگو یافت نشد.")
            return True

        button = get_button_by_id(button_id)
        if not button:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True

        questions_data = json.loads(template.get('questions_data', '[]'))

        if not questions_data:
            await send_message(chat_id, "❌ الگو هیچ سوالی ندارد.")
            return True

        # حذف سوالات فعلی دکمه
        existing_questions = get_questions_by_button(button_id)
        for q in existing_questions:
            delete_options_by_question(q['id'])
            delete_conditions_by_question(q['id'])
            delete_question(q['id'])

        # ایجاد سوالات جدید از الگو
        created_count = 0
        for q_data in questions_data:
            options = q_data.pop('options', [])
            conditions = q_data.pop('conditions', [])

            q_id = add_question(
                button_id=button_id,
                question_text=q_data.get('question_text', 'سوال بدون متن'),
                question_type=q_data.get('question_type', 'text'),
                is_required=q_data.get('is_required', 0),
                validation_type=q_data.get('validation_type', 'none'),
                needs_button=q_data.get('needs_button', 0),
                sort_order=q_data.get('sort_order', 0),
                length_validation_enabled=q_data.get('length_validation_enabled', 0),
                min_length=q_data.get('min_length'),
                max_length=q_data.get('max_length'),
                numeric_validation_enabled=q_data.get('numeric_validation_enabled', 0),
                min_value=q_data.get('min_value'),
                max_value=q_data.get('max_value'),
                file_validation_enabled=q_data.get('file_validation_enabled', 0),
                allowed_formats=q_data.get('allowed_formats'),
                max_file_size=q_data.get('max_file_size'),
                validation_error=q_data.get('validation_error'),
                validation_hint=q_data.get('validation_hint'),
            )

            if q_id:
                created_count += 1
                for opt in options:
                    add_question_option(q_id, opt.get('option_text'), opt.get('callback_data'))
                for cond in conditions:
                    add_condition(q_id, cond.get('condition_question_id'),
                                 cond.get('condition_operator', '=='),
                                 cond.get('condition_value', ''))

        await send_message(
            chat_id,
            f"✅ الگوی «{template.get('name')}» با موفقیت به دکمه «{button.get('name')}» اعمال شد.\n\n"
            f"📋 {created_count} سوال جدید ایجاد شد.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به مدیریت الگوها", "callback_data": "admin_templates"}]]}
        )

        logger.info(f"✅ Template {template_id} applied to button {button_id} by {user_id}")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_template_apply_confirm for {template_id}->{button_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در اعمال الگو: {str(e)}")
        return True


async def handle_template_apply_execute(chat_id: int, user_id: int, template_id: int, button_id: int) -> bool:
    """
    تابع alias برای handle_template_apply_confirm (برای سازگاری با کدهای قدیمی)
    """
    return await handle_template_apply_confirm(chat_id, user_id, template_id, button_id)


# ============================================================
# پردازش پیام‌های ساخت الگو
# ============================================================

async def handle_template_message(chat_id: int, user_id: int, text: str) -> bool:
    state_service = get_state_service()
    state_info = await state_service.get_state(user_id, {})
    current_state = state_info.get("state")

    if not current_state:
        return False

    # مرحله ۱: نام الگو
    if current_state == "admin_template_create_name":
        if not text or text.strip() == "":
            await send_message(chat_id, "❌ نام نمی‌تواند خالی باشد.")
            return True

        existing = _get_template_by_name(text.strip())
        if existing:
            await send_message(chat_id, f"❌ الگویی با نام «{text}» قبلاً وجود دارد. لطفاً نام دیگری انتخاب کنید.")
            return True

        await state_service.update_state(user_id, {
            "template_name": text.strip(),
            "state": "admin_template_create_description"
        })

        await send_message(
            chat_id,
            f"✅ نام الگو: {text}\n\n"
            f"مرحله ۲: لطفاً توضیحات الگو را وارد کنید (اختیاری):\n"
            f"(برای رد شدن، «رد شدن» را وارد کنید)"
        )
        return True

    # مرحله ۲: توضیحات
    if current_state == "admin_template_create_description":
        if text.strip().lower() == "رد شدن":
            await state_service.update_state(user_id, {"template_description": ""})
        else:
            await state_service.update_state(user_id, {"template_description": text.strip()})

        await state_service.update_state(user_id, {
            "state": "admin_template_add_question",
            "template_questions": []
        })

        await send_message(
            chat_id,
            f"✅ توضیحات ثبت شد.\n\n"
            f"مرحله ۳: افزودن سوالات به الگو\n\n"
            f"لطفاً متن سوال اول را وارد کنید:\n"
            f"(برای پایان، «پایان» را وارد کنید)\n\n"
            f"📌 نکته: بعد از هر سوال، می‌توانید نوع اعتبارسنجی را انتخاب کنید."
        )
        return True

    # مرحله ۳: افزودن سوالات
    if current_state == "admin_template_add_question":
        if text.strip().lower() == "پایان":
            questions = state_info.get("template_questions", [])
            if not questions:
                await send_message(chat_id, "❌ حداقل یک سوال باید اضافه شود.")
                return True

            template_name = state_info.get("template_name", "الگوی جدید")
            description = state_info.get("template_description", "")

            template_id = _save_template(template_name, description, questions, user_id)

            if template_id:
                await send_message(
                    chat_id,
                    f"✅ الگوی «{template_name}» با {len(questions)} سوال با موفقیت ذخیره شد.",
                    templates_main_keyboard()
                )
                await state_service.set_state(user_id, {"state": "main"})
            else:
                await send_message(chat_id, "❌ خطا در ذخیره الگو.")

            return True

        if not text or text.strip() == "":
            await send_message(chat_id, "❌ متن سوال نمی‌تواند خالی باشد.")
            return True

        await state_service.update_state(user_id, {
            "temp_question_text": text.strip(),
            "state": "admin_template_question_type"
        })

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
            f"📝 **سوال:** {text}\n\nنوع سوال را انتخاب کنید:",
            keyboard
        )
        return True

    # مرحله ویرایش نام الگو
    if current_state == "admin_template_edit_name":
        if not text or text.strip() == "":
            await send_message(chat_id, "❌ نام نمی‌تواند خالی باشد.")
            return True

        existing = _get_template_by_name(text.strip())
        template_id = state_info.get("template_id")
        if existing and existing.get('id') != template_id:
            await send_message(chat_id, f"❌ الگویی با نام «{text}» قبلاً وجود دارد. لطفاً نام دیگری انتخاب کنید.")
            return True

        await state_service.update_state(user_id, {
            "template_name": text.strip(),
            "state": "admin_template_edit_description"
        })

        await send_message(
            chat_id,
            f"✅ نام جدید: {text}\n\n"
            f"مرحله ۲: توضیحات جدید الگو را وارد کنید (اختیاری):\n"
            f"(برای رد شدن، «رد شدن» را وارد کنید)"
        )
        return True

    # مرحله ویرایش توضیحات
    if current_state == "admin_template_edit_description":
        description = "" if text.strip().lower() == "رد شدن" else text.strip()
        template_id = state_info.get("template_id")
        template_name = state_info.get("template_name")
        questions = state_info.get("template_questions", [])

        success = _update_template(template_id, template_name, description, questions)

        if success:
            await send_message(
                chat_id,
                f"✅ الگوی «{template_name}» با موفقیت ویرایش شد.",
                templates_main_keyboard()
            )
        else:
            await send_message(chat_id, "❌ خطا در ویرایش الگو.")

        await state_service.set_state(user_id, {"state": "main"})
        return True

    return False


# ============================================================
# روت‌های نوع سوال و تنظیمات
# ============================================================

async def handle_template_qtype(chat_id: int, user_id: int, data: str) -> bool:
    qtype = data.split("_")[-1]
    state_service = get_state_service()
    state_info = await state_service.get_state(user_id, {})

    if state_info.get("state") != "admin_template_question_type":
        await send_message(chat_id, "❌ خطا در انتخاب نوع سوال.")
        return True

    question_text = state_info.get("temp_question_text", "")

    await state_service.update_state(user_id, {
        "temp_question_type": qtype,
        "state": "admin_template_question_settings"
    })

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


async def handle_template_qtype_back(chat_id: int, user_id: int) -> bool:
    state_service = get_state_service()
    state_info = await state_service.get_state(user_id, {})
    question_text = state_info.get("temp_question_text", "")

    if not question_text:
        await send_message(chat_id, "❌ خطا.")
        return True

    await state_service.set_state_field(user_id, "state", "admin_template_question_type")

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
        f"📝 **سوال:** {question_text}\n\nنوع سوال را انتخاب کنید:",
        keyboard
    )
    return True


async def handle_template_qsetting(chat_id: int, user_id: int, data: str) -> bool:
    action = data.split("_")[-1]
    state_service = get_state_service()
    state_info = await state_service.get_state(user_id, {})

    if state_info.get("state") != "admin_template_question_settings":
        await send_message(chat_id, "❌ خطا.")
        return True

    question_text = state_info.get("temp_question_text", "")
    qtype = state_info.get("temp_question_type", "text")
    questions = state_info.get("template_questions", [])

    if action == "required":
        await state_service.update_state(user_id, {
            "temp_required": not state_info.get("temp_required", False)
        })
        status = "اجباری" if state_info.get("temp_required", False) else "اختیاری"
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
            f"📝 **سوال:** {question_text}\n\n🔧 **وضعیت:** {status}\n\nتنظیمات سوال را انتخاب کنید:",
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
        await state_service.update_state(user_id, {
            "template_questions": questions,
            "temp_question_text": None,
            "temp_question_type": None,
            "temp_required": None,
            "state": "admin_template_add_question"
        })

        await send_message(
            chat_id,
            f"✅ سوال «{question_text}» با موفقیت به الگو اضافه شد.\n\n"
            f"📋 تعداد سوالات فعلی: {len(questions)}\n\n"
            f"سوال بعدی را وارد کنید (یا «پایان» برای اتمام):"
        )
        return True

    if action == "validation":
        await state_service.set_state_field(user_id, "state", "admin_template_question_validation")

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
            f"📝 **سوال:** {question_text}\n\n🔧 **تنظیمات اعتبارسنجی**\n\nمقادیر مورد نظر را تنظیم کنید:",
            keyboard
        )
        return True

    if action == "options":
        await state_service.update_state(user_id, {
            "state": "admin_template_question_options",
            "temp_options": [],
            "temp_option_counter": 0
        })

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
        await state_service.set_state_field(user_id, "state", "admin_template_question_file")

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
            f"📎 **سوال:** {question_text}\n\n🔧 **تنظیمات فایل**\n\nتنظیمات مربوط به فایل را انتخاب کنید:",
            keyboard
        )
        return True

    await send_message(chat_id, "❌ گزینه نامعتبر.")
    return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'handle_templates',
    'handle_template_list',
    'handle_template_list_page',
    'handle_template_detail',
    'handle_template_create',
    'handle_template_create_empty',
    'handle_template_copy',
    'handle_template_copy_select',
    'handle_template_extract',
    'handle_template_extract_btn',
    'handle_template_save',
    'handle_template_edit',
    'handle_template_delete',
    'handle_template_delete_confirm',
    'handle_template_apply',
    'handle_template_apply_select',
    'handle_template_apply_btn',
    'handle_template_apply_confirm',
    'handle_template_apply_execute',
    'handle_template_message',
    'handle_template_qtype',
    'handle_template_qtype_back',
    'handle_template_qsetting',
    'PRESET_TEMPLATES',
    'init_default_templates',
    '_get_templates',
    '_get_template_by_id',
    '_save_template',
    '_delete_template',
]