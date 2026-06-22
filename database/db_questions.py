# database/db_questions.py
# توابع مربوط به سوالات، گزینه‌ها، شرط‌ها، اعتبارسنجی و پروفایل‌ها
# نسخه اصلاح‌شده با context manager و پشتیبانی از فیلدهای جدید

import sqlite3
import json
from datetime import datetime
from .db_connection import get_db_connection
from logger_config import logger


# ==================== سوالات ====================

def add_question(
    button_id, 
    question_text, 
    question_type="text", 
    validation_rule=None, 
    error_message=None, 
    needs_button=0, 
    array_name=None, 
    sort_order=0,
    is_required=0,
    validation_enabled=0,
    validation_type='none',
    length_validation_enabled=0,
    min_length=None,
    max_length=None,
    word_validation_enabled=0,
    min_words=None,
    max_words=None,
    numeric_validation_enabled=0,
    min_value=None,
    max_value=None,
    step=None,
    date_validation_enabled=0,
    min_date=None,
    max_date=None,
    future_only=0,
    past_only=0,
    weekdays_only=0,
    file_validation_enabled=0,
    allowed_formats=None,
    max_file_size=None,
    min_file_size=None,
    max_files=None,
    dimensions_enabled=0,
    required_width=None,
    required_height=None,
    aspect_ratio=None,
    pattern_validation_enabled=0,
    regex_pattern=None,
    starts_with=None,
    ends_with=None,
    contains_validation_enabled=0,
    contains=None,
    not_contains=None,
    forbidden_words=None,
    required_words=None,
    conditional_enabled=0,
    conditional_on=None,
    conditional_value=None,
    auto_fix_enabled=0,
    validation_error=None,
    validation_hint=None
):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO questions (
                button_id, question_text, question_type, validation_rule, error_message, 
                needs_button, array_name, sort_order, is_required, validation_enabled,
                validation_type, length_validation_enabled, min_length, max_length,
                word_validation_enabled, min_words, max_words,
                numeric_validation_enabled, min_value, max_value, step,
                date_validation_enabled, min_date, max_date, future_only, past_only, weekdays_only,
                file_validation_enabled, allowed_formats, max_file_size, min_file_size, max_files,
                dimensions_enabled, required_width, required_height, aspect_ratio,
                pattern_validation_enabled, regex_pattern, starts_with, ends_with,
                contains_validation_enabled, contains, not_contains,
                forbidden_words, required_words,
                conditional_enabled, conditional_on, conditional_value,
                auto_fix_enabled, validation_error, validation_hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                button_id, question_text, question_type, validation_rule, error_message,
                needs_button, array_name, sort_order, is_required, validation_enabled,
                validation_type, length_validation_enabled, min_length, max_length,
                word_validation_enabled, min_words, max_words,
                numeric_validation_enabled, min_value, max_value, step,
                date_validation_enabled, min_date, max_date, future_only, past_only, weekdays_only,
                file_validation_enabled, allowed_formats, max_file_size, min_file_size, max_files,
                dimensions_enabled, required_width, required_height, aspect_ratio,
                pattern_validation_enabled, regex_pattern, starts_with, ends_with,
                contains_validation_enabled, contains, not_contains,
                forbidden_words, required_words,
                conditional_enabled, conditional_on, conditional_value,
                auto_fix_enabled, validation_error, validation_hint
            )
        )
        conn.commit()
        question_id = cursor.lastrowid
        logger.debug(f"سوال جدید با id={question_id} برای دکمه {button_id} ایجاد شد.")
        return question_id


def get_questions_by_button(button_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE button_id = ? AND is_active = 1 ORDER BY sort_order, id", (button_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_question_by_id(question_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_previous_questions(button_id, current_question_id=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if current_question_id is None:
            cursor.execute(
                "SELECT * FROM questions WHERE button_id = ? AND is_active = 1 ORDER BY sort_order, id",
                (button_id,)
            )
        else:
            cursor.execute(
                "SELECT * FROM questions WHERE button_id = ? AND id < ? AND is_active = 1 ORDER BY sort_order, id",
                (button_id, current_question_id)
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def update_question(question_id, **kwargs):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        updates = []
        values = []
        
        valid_fields = [
            'question_text', 'question_type', 'validation_rule', 'error_message',
            'needs_button', 'array_name', 'sort_order', 'is_active',
            'is_required', 'validation_enabled', 'validation_type',
            'length_validation_enabled', 'min_length', 'max_length',
            'word_validation_enabled', 'min_words', 'max_words',
            'numeric_validation_enabled', 'min_value', 'max_value', 'step',
            'date_validation_enabled', 'min_date', 'max_date', 'future_only', 'past_only', 'weekdays_only',
            'file_validation_enabled', 'allowed_formats', 'max_file_size', 'min_file_size', 'max_files',
            'dimensions_enabled', 'required_width', 'required_height', 'aspect_ratio',
            'pattern_validation_enabled', 'regex_pattern', 'starts_with', 'ends_with',
            'contains_validation_enabled', 'contains', 'not_contains',
            'forbidden_words', 'required_words',
            'conditional_enabled', 'conditional_on', 'conditional_value',
            'auto_fix_enabled', 'validation_error', 'validation_hint'
        ]
        
        for key, value in kwargs.items():
            if key in valid_fields and value is not None:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if updates:
            values.append(question_id)
            cursor.execute(f"UPDATE questions SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
            logger.debug(f"سوال {question_id} به‌روزرسانی شد.")


def delete_question(question_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        logger.debug(f"سوال {question_id} حذف شد.")


def delete_questions_by_button(button_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE button_id = ?", (button_id,))
        conn.commit()
        logger.debug(f"همه سوالات دکمه {button_id} حذف شدند.")


# ==================== شرط‌های چندگانه سوالات ====================

def add_condition(question_id, condition_question_id, condition_operator, condition_value, logic_operator="AND", sort_order=0):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO question_conditions (question_id, condition_question_id, condition_operator, condition_value, logic_operator, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
            (question_id, condition_question_id, condition_operator, condition_value, logic_operator, sort_order)
        )
        conn.commit()
        condition_id = cursor.lastrowid
        logger.debug(f"شرط جدید با id={condition_id} برای سوال {question_id} ایجاد شد.")
        return condition_id


def get_conditions_by_question(question_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM question_conditions WHERE question_id = ? AND is_active = 1 ORDER BY sort_order, id",
            (question_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_condition_by_id(condition_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM question_conditions WHERE id = ?", (condition_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_condition(condition_id, **kwargs):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        updates = []
        values = []
        
        valid_fields = ['condition_question_id', 'condition_operator', 'condition_value', 'logic_operator', 'sort_order', 'is_active']
        
        for key, value in kwargs.items():
            if key in valid_fields and value is not None:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if updates:
            values.append(condition_id)
            cursor.execute(f"UPDATE question_conditions SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
            logger.debug(f"شرط {condition_id} به‌روزرسانی شد.")


def delete_condition(condition_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM question_conditions WHERE id = ?", (condition_id,))
        conn.commit()
        logger.debug(f"شرط {condition_id} حذف شد.")


def delete_conditions_by_question(question_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM question_conditions WHERE question_id = ?", (question_id,))
        conn.commit()
        logger.debug(f"همه شرط‌های سوال {question_id} حذف شدند.")


def get_question_logic_operator(question_id):
    conditions = get_conditions_by_question(question_id)
    if not conditions:
        return None
    if len(conditions) == 1:
        return None
    return conditions[0].get('logic_operator', 'AND')


# ==================== گزینه‌های دکمه‌ای سوالات ====================

def add_question_option(question_id, option_text, callback_data=None, sort_order=0):
    if callback_data is None:
        callback_data = f"qopt_{question_id}_{int(datetime.now().timestamp())}"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO question_options (question_id, option_text, callback_data, sort_order) VALUES (?, ?, ?, ?)",
            (question_id, option_text, callback_data, sort_order)
        )
        conn.commit()
        option_id = cursor.lastrowid
        logger.debug(f"گزینه جدید با id={option_id} برای سوال {question_id} ایجاد شد.")
        return option_id


def get_options_by_question(question_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM question_options WHERE question_id = ? AND is_active = 1 ORDER BY sort_order, id", (question_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_option_by_callback(callback_data):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM question_options WHERE callback_data = ? AND is_active = 1", (callback_data,))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_options_by_question(question_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM question_options WHERE question_id = ?", (question_id,))
        conn.commit()
        logger.debug(f"همه گزینه‌های سوال {question_id} حذف شدند.")


# ==================== توابع مدیریت اعتبارسنجی ====================

def toggle_validation_feature(q_id, feature_name, status):
    valid_features = [
        'is_required', 'validation_enabled',
        'length_validation_enabled', 'word_validation_enabled',
        'numeric_validation_enabled', 'date_validation_enabled',
        'file_validation_enabled', 'dimensions_enabled',
        'pattern_validation_enabled', 'contains_validation_enabled',
        'conditional_enabled', 'auto_fix_enabled'
    ]
    if feature_name not in valid_features:
        return False
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE questions SET {feature_name} = ? WHERE id = ?", (status, q_id))
        conn.commit()
        logger.debug(f"ویژگی {feature_name} برای سوال {q_id} به {status} تغییر یافت.")
        return True


def get_validation_settings(q_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                is_required, validation_enabled, validation_type,
                length_validation_enabled, min_length, max_length,
                word_validation_enabled, min_words, max_words,
                numeric_validation_enabled, min_value, max_value, step,
                date_validation_enabled, min_date, max_date, future_only, past_only, weekdays_only,
                file_validation_enabled, allowed_formats, max_file_size, min_file_size, max_files,
                dimensions_enabled, required_width, required_height, aspect_ratio,
                pattern_validation_enabled, regex_pattern, starts_with, ends_with,
                contains_validation_enabled, contains, not_contains,
                forbidden_words, required_words,
                conditional_enabled, conditional_on, conditional_value,
                auto_fix_enabled, validation_error, validation_hint
            FROM questions WHERE id = ?
        """, (q_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_validation_status_summary(q_id):
    settings = get_validation_settings(q_id)
    if not settings:
        return {}
    return {
        'is_required': settings.get('is_required', 0),
        'validation_enabled': settings.get('validation_enabled', 0),
        'length_validation_enabled': settings.get('length_validation_enabled', 0),
        'word_validation_enabled': settings.get('word_validation_enabled', 0),
        'numeric_validation_enabled': settings.get('numeric_validation_enabled', 0),
        'date_validation_enabled': settings.get('date_validation_enabled', 0),
        'file_validation_enabled': settings.get('file_validation_enabled', 0),
        'dimensions_enabled': settings.get('dimensions_enabled', 0),
        'pattern_validation_enabled': settings.get('pattern_validation_enabled', 0),
        'contains_validation_enabled': settings.get('contains_validation_enabled', 0),
        'conditional_enabled': settings.get('conditional_enabled', 0),
        'auto_fix_enabled': settings.get('auto_fix_enabled', 0)
    }


def is_validation_feature_active(q_id, feature_name):
    settings = get_validation_settings(q_id)
    if not settings:
        return False
    return settings.get(feature_name, 0) == 1


def enable_all_validations(q_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE questions SET
                validation_enabled = 1,
                length_validation_enabled = 1,
                word_validation_enabled = 1,
                numeric_validation_enabled = 1,
                date_validation_enabled = 1,
                file_validation_enabled = 1,
                dimensions_enabled = 1,
                pattern_validation_enabled = 1,
                contains_validation_enabled = 1,
                conditional_enabled = 1,
                auto_fix_enabled = 1
            WHERE id = ?
        """, (q_id,))
        conn.commit()
        logger.info(f"همه اعتبارسنجی‌های سوال {q_id} فعال شدند.")
        return True


def disable_all_validations(q_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE questions SET
                validation_enabled = 0,
                length_validation_enabled = 0,
                word_validation_enabled = 0,
                numeric_validation_enabled = 0,
                date_validation_enabled = 0,
                file_validation_enabled = 0,
                dimensions_enabled = 0,
                pattern_validation_enabled = 0,
                contains_validation_enabled = 0,
                conditional_enabled = 0,
                auto_fix_enabled = 0
            WHERE id = ?
        """, (q_id,))
        conn.commit()
        logger.info(f"همه اعتبارسنجی‌های سوال {q_id} غیرفعال شدند.")
        return True


def reset_validation_to_default(q_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE questions SET
                is_required = 0,
                validation_enabled = 0,
                validation_type = 'none',
                length_validation_enabled = 0,
                min_length = NULL,
                max_length = NULL,
                word_validation_enabled = 0,
                min_words = NULL,
                max_words = NULL,
                numeric_validation_enabled = 0,
                min_value = NULL,
                max_value = NULL,
                step = NULL,
                date_validation_enabled = 0,
                min_date = NULL,
                max_date = NULL,
                future_only = 0,
                past_only = 0,
                weekdays_only = 0,
                file_validation_enabled = 0,
                allowed_formats = NULL,
                max_file_size = NULL,
                min_file_size = NULL,
                max_files = NULL,
                dimensions_enabled = 0,
                required_width = NULL,
                required_height = NULL,
                aspect_ratio = NULL,
                pattern_validation_enabled = 0,
                regex_pattern = NULL,
                starts_with = NULL,
                ends_with = NULL,
                contains_validation_enabled = 0,
                contains = NULL,
                not_contains = NULL,
                forbidden_words = NULL,
                required_words = NULL,
                conditional_enabled = 0,
                conditional_on = NULL,
                conditional_value = NULL,
                auto_fix_enabled = 0,
                validation_error = NULL,
                validation_hint = NULL
            WHERE id = ?
        """, (q_id,))
        conn.commit()
        logger.info(f"تنظیمات اعتبارسنجی سوال {q_id} بازنشانی شد.")
        return True


# ==================== پروفایل‌های اعتبارسنجی ====================

def save_validation_profile(name, settings):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO validation_profiles (name, settings) VALUES (?, ?)",
            (name, json.dumps(settings, ensure_ascii=False))
        )
        conn.commit()
        logger.info(f"پروفایل {name} ذخیره شد.")
        return True


def get_validation_profiles():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM validation_profiles ORDER BY name")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_validation_profile_by_name(name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM validation_profiles WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['settings'] = json.loads(result['settings'])
            return result
        return None


def apply_validation_profile(q_id, profile_name):
    profile = get_validation_profile_by_name(profile_name)
    if not profile:
        return False
    settings = profile['settings']
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        updates = []
        values = []
        valid_fields = [
            'validation_type', 'is_required', 'validation_enabled',
            'length_validation_enabled', 'min_length', 'max_length',
            'word_validation_enabled', 'min_words', 'max_words',
            'numeric_validation_enabled', 'min_value', 'max_value', 'step',
            'date_validation_enabled', 'min_date', 'max_date', 'future_only', 'past_only', 'weekdays_only',
            'file_validation_enabled', 'allowed_formats', 'max_file_size', 'min_file_size', 'max_files',
            'dimensions_enabled', 'required_width', 'required_height', 'aspect_ratio',
            'pattern_validation_enabled', 'regex_pattern', 'starts_with', 'ends_with',
            'contains_validation_enabled', 'contains', 'not_contains',
            'forbidden_words', 'required_words',
            'conditional_enabled', 'conditional_on', 'conditional_value',
            'auto_fix_enabled', 'validation_error', 'validation_hint'
        ]
        
        for key, value in settings.items():
            if key in valid_fields:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if updates:
            values.append(q_id)
            cursor.execute(f"UPDATE questions SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
            logger.info(f"پروفایل {profile_name} برای سوال {q_id} اعمال شد.")
        
        return True


def delete_validation_profile(name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM validation_profiles WHERE name = ?", (name,))
        conn.commit()
        logger.info(f"پروفایل {name} حذف شد.")
        return True


# ==================== توابع کمکی برای الگوها ====================

def get_questions_with_options(button_id):
    """
    دریافت سوالات یک دکمه به همراه گزینه‌هایشان
    """
    questions = get_questions_by_button(button_id)
    result = []
    for q in questions:
        q_dict = dict(q)
        q_dict['options'] = get_options_by_question(q['id'])
        q_dict['conditions'] = get_conditions_by_question(q['id'])
        result.append(q_dict)
    return result


def get_question_count_by_button(button_id):
    """
    تعداد سوالات یک دکمه
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM questions WHERE button_id = ? AND is_active = 1", (button_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0


def get_options_count(question_id):
    """
    تعداد گزینه‌های یک سوال
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM question_options WHERE question_id = ? AND is_active = 1", (question_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0


def get_conditions_count(question_id):
    """
    تعداد شرط‌های یک سوال
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM question_conditions WHERE question_id = ? AND is_active = 1", (question_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0


__all__ = [
    'add_question',
    'get_questions_by_button',
    'get_question_by_id',
    'get_previous_questions',
    'update_question',
    'delete_question',
    'delete_questions_by_button',
    'add_condition',
    'get_conditions_by_question',
    'get_condition_by_id',
    'update_condition',
    'delete_condition',
    'delete_conditions_by_question',
    'get_question_logic_operator',
    'add_question_option',
    'get_options_by_question',
    'get_option_by_callback',
    'delete_options_by_question',
    'toggle_validation_feature',
    'get_validation_settings',
    'get_validation_status_summary',
    'is_validation_feature_active',
    'enable_all_validations',
    'disable_all_validations',
    'reset_validation_to_default',
    'save_validation_profile',
    'get_validation_profiles',
    'get_validation_profile_by_name',
    'apply_validation_profile',
    'delete_validation_profile',
    'get_questions_with_options',
    'get_question_count_by_button',
    'get_options_count',
    'get_conditions_count',
]