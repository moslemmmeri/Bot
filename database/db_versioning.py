# database/db_versioning.py
# مدیریت نسخه‌سازی (Versioning) و بازگردانی (Rollback) دکمه‌ها
# ذخیره‌ی اسنپ‌شات کامل از دکمه، سوالات، گزینه‌ها و شرط‌ها

import json
from logger_config import logger
from .db_connection import get_db_connection
from .db_questions import (
    get_questions_by_button,
    get_options_by_question,
    get_conditions_by_question,
    add_question,
    add_question_option,
    add_condition,
    delete_questions_by_button,
    delete_options_by_question,
    delete_conditions_by_question
)
from .db_buttons import get_button_by_id, update_button


# ==================== توابع کمکی (سریالایز و دیسریالایز) ====================

def _serialize_button_snapshot(button_id):
    """
    گرفتن اسنپ‌شات کامل از یک دکمه:
    - اطلاعات خود دکمه
    - لیست تمام سوالات با گزینه‌ها و شرط‌هایشان
    """
    button = get_button_by_id(button_id)
    if not button:
        return None

    # حذف فیلدهای اضافی که نباید ذخیره شوند (مانند created_at که دوباره تولید می‌شود)
    button_data = {
        'name': button['name'],
        'icon': button.get('icon', ''),
        'callback_data': button.get('callback_data', ''),
        'has_submenu': button.get('has_submenu', 0),
        'has_payment': button.get('has_payment', 0),
        'price_amount': button.get('price_amount', 50000),
        'price_label': button.get('price_label', 'هزینه خدمات'),
        'price_type': button.get('price_type', 'fixed'),
        'min_price': button.get('min_price'),
        'max_price': button.get('max_price'),
        'sort_order': button.get('sort_order', 0),
        'is_active': button.get('is_active', 1),
        'category_id': button['category_id'],
        'parent_button_id': button.get('parent_button_id'),
        'columns': button.get('columns')
    }

    questions = get_questions_by_button(button_id)
    questions_data = []

    for q in questions:
        # داده‌های سوال (به جز id و button_id و created_at که دوباره ساخته می‌شوند)
        q_data = {
            'question_text': q['question_text'],
            'question_type': q.get('question_type', 'text'),
            'validation_rule': q.get('validation_rule'),
            'error_message': q.get('error_message'),
            'needs_button': q.get('needs_button', 0),
            'array_name': q.get('array_name'),
            'sort_order': q.get('sort_order', 0),
            'is_active': q.get('is_active', 1),
            'is_required': q.get('is_required', 0),
            'validation_enabled': q.get('validation_enabled', 0),
            'validation_type': q.get('validation_type', 'none'),
            'length_validation_enabled': q.get('length_validation_enabled', 0),
            'min_length': q.get('min_length'),
            'max_length': q.get('max_length'),
            'word_validation_enabled': q.get('word_validation_enabled', 0),
            'min_words': q.get('min_words'),
            'max_words': q.get('max_words'),
            'numeric_validation_enabled': q.get('numeric_validation_enabled', 0),
            'min_value': q.get('min_value'),
            'max_value': q.get('max_value'),
            'step': q.get('step'),
            'date_validation_enabled': q.get('date_validation_enabled', 0),
            'min_date': q.get('min_date'),
            'max_date': q.get('max_date'),
            'future_only': q.get('future_only', 0),
            'past_only': q.get('past_only', 0),
            'weekdays_only': q.get('weekdays_only', 0),
            'file_validation_enabled': q.get('file_validation_enabled', 0),
            'allowed_formats': q.get('allowed_formats'),
            'max_file_size': q.get('max_file_size'),
            'min_file_size': q.get('min_file_size'),
            'max_files': q.get('max_files'),
            'dimensions_enabled': q.get('dimensions_enabled', 0),
            'required_width': q.get('required_width'),
            'required_height': q.get('required_height'),
            'aspect_ratio': q.get('aspect_ratio'),
            'pattern_validation_enabled': q.get('pattern_validation_enabled', 0),
            'regex_pattern': q.get('regex_pattern'),
            'starts_with': q.get('starts_with'),
            'ends_with': q.get('ends_with'),
            'contains_validation_enabled': q.get('contains_validation_enabled', 0),
            'contains': q.get('contains'),
            'not_contains': q.get('not_contains'),
            'forbidden_words': q.get('forbidden_words'),
            'required_words': q.get('required_words'),
            'conditional_enabled': q.get('conditional_enabled', 0),
            'conditional_on': q.get('conditional_on'),
            'conditional_value': q.get('conditional_value'),
            'auto_fix_enabled': q.get('auto_fix_enabled', 0),
            'validation_error': q.get('validation_error'),
            'validation_hint': q.get('validation_hint')
        }

        # گزینه‌های سوال
        options = get_options_by_question(q['id'])
        options_data = [{
            'option_text': opt['option_text'],
            'callback_data': opt.get('callback_data', ''),
            'sort_order': opt.get('sort_order', 0),
            'is_active': opt.get('is_active', 1)
        } for opt in options]

        # شرط‌های سوال
        conditions = get_conditions_by_question(q['id'])
        conditions_data = [{
            'condition_question_id': cond['condition_question_id'],
            'condition_operator': cond['condition_operator'],
            'condition_value': cond['condition_value'],
            'logic_operator': cond.get('logic_operator', 'AND'),
            'sort_order': cond.get('sort_order', 0),
            'is_active': cond.get('is_active', 1)
        } for cond in conditions]

        questions_data.append({
            'data': q_data,
            'options': options_data,
            'conditions': conditions_data
        })

    return {
        'button': button_data,
        'questions': questions_data
    }


def _restore_button_from_snapshot(button_id, snapshot, restored_by):
    """
    بازیابی یک دکمه از روی اسنپ‌شات.
    تمام سوالات، گزینه‌ها و شرط‌های فعلی حذف شده و با داده‌های اسنپ‌شات جایگزین می‌شوند.
    """
    try:
        button_data = snapshot.get('button')
        questions_data = snapshot.get('questions', [])

        if not button_data:
            logger.error(f"اسنپ‌شات دکمه {button_id} فاقد داده‌های اصلی است.")
            return False

        # ۱. به‌روزرسانی اطلاعات اصلی دکمه
        update_button(
            button_id,
            name=button_data.get('name'),
            icon=button_data.get('icon'),
            callback_data=button_data.get('callback_data'),
            has_submenu=button_data.get('has_submenu'),
            has_payment=button_data.get('has_payment'),
            price_amount=button_data.get('price_amount'),
            price_label=button_data.get('price_label'),
            price_type=button_data.get('price_type'),
            min_price=button_data.get('min_price'),
            max_price=button_data.get('max_price'),
            sort_order=button_data.get('sort_order'),
            is_active=button_data.get('is_active'),
            columns=button_data.get('columns')
        )
        
        # به‌روزرسانی category_id و parent_button_id جداگانه
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE buttons 
                SET category_id = ?, parent_button_id = ?
                WHERE id = ?
            """, (button_data.get('category_id'), button_data.get('parent_button_id'), button_id))
            conn.commit()

        # ۲. حذف سوالات، گزینه‌ها و شرط‌های فعلی
        delete_questions_by_button(button_id)

        # ۳. بازآفرینی سوالات جدید
        old_to_new_qid = {}  # نگاشت شناسه‌های قدیمی به جدید برای شرط‌ها

        for q_item in questions_data:
            q_data = q_item['data']
            options_data = q_item.get('options', [])
            conditions_data = q_item.get('conditions', [])

            # ایجاد سوال جدید
            new_q_id = add_question(
                button_id=button_id,
                question_text=q_data.get('question_text', 'سوال بدون متن'),
                question_type=q_data.get('question_type', 'text'),
                validation_rule=q_data.get('validation_rule'),
                error_message=q_data.get('error_message'),
                needs_button=q_data.get('needs_button', 0),
                array_name=q_data.get('array_name'),
                sort_order=q_data.get('sort_order', 0),
                is_required=q_data.get('is_required', 0),
                validation_enabled=q_data.get('validation_enabled', 0),
                validation_type=q_data.get('validation_type', 'none'),
                length_validation_enabled=q_data.get('length_validation_enabled', 0),
                min_length=q_data.get('min_length'),
                max_length=q_data.get('max_length'),
                word_validation_enabled=q_data.get('word_validation_enabled', 0),
                min_words=q_data.get('min_words'),
                max_words=q_data.get('max_words'),
                numeric_validation_enabled=q_data.get('numeric_validation_enabled', 0),
                min_value=q_data.get('min_value'),
                max_value=q_data.get('max_value'),
                step=q_data.get('step'),
                date_validation_enabled=q_data.get('date_validation_enabled', 0),
                min_date=q_data.get('min_date'),
                max_date=q_data.get('max_date'),
                future_only=q_data.get('future_only', 0),
                past_only=q_data.get('past_only', 0),
                weekdays_only=q_data.get('weekdays_only', 0),
                file_validation_enabled=q_data.get('file_validation_enabled', 0),
                allowed_formats=q_data.get('allowed_formats'),
                max_file_size=q_data.get('max_file_size'),
                min_file_size=q_data.get('min_file_size'),
                max_files=q_data.get('max_files'),
                dimensions_enabled=q_data.get('dimensions_enabled', 0),
                required_width=q_data.get('required_width'),
                required_height=q_data.get('required_height'),
                aspect_ratio=q_data.get('aspect_ratio'),
                pattern_validation_enabled=q_data.get('pattern_validation_enabled', 0),
                regex_pattern=q_data.get('regex_pattern'),
                starts_with=q_data.get('starts_with'),
                ends_with=q_data.get('ends_with'),
                contains_validation_enabled=q_data.get('contains_validation_enabled', 0),
                contains=q_data.get('contains'),
                not_contains=q_data.get('not_contains'),
                forbidden_words=q_data.get('forbidden_words'),
                required_words=q_data.get('required_words'),
                conditional_enabled=q_data.get('conditional_enabled', 0),
                conditional_on=q_data.get('conditional_on'),
                conditional_value=q_data.get('conditional_value'),
                auto_fix_enabled=q_data.get('auto_fix_enabled', 0),
                validation_error=q_data.get('validation_error'),
                validation_hint=q_data.get('validation_hint')
            )

            # ذخیره نگاشت برای شرط‌ها
            old_to_new_qid[len(old_to_new_qid) + 1] = new_q_id

            # ایجاد گزینه‌ها
            for opt in options_data:
                add_question_option(
                    question_id=new_q_id,
                    option_text=opt.get('option_text', 'گزینه بدون متن'),
                    callback_data=opt.get('callback_data'),
                    sort_order=opt.get('sort_order', 0)
                )

            # ایجاد شرط‌ها (با نگاشت شناسه‌های قدیمی به جدید)
            for cond in conditions_data:
                old_ref_id = cond.get('condition_question_id')
                new_ref_id = old_to_new_qid.get(old_ref_id, old_ref_id)
                # اگر شرط به سوالی در همین دکمه اشاره دارد، شناسه جدید را جایگزین کن
                # در غیر این صورت (سوال در دکمه‌ی دیگر) همان شناسه را نگه دار

                add_condition(
                    question_id=new_q_id,
                    condition_question_id=new_ref_id,
                    condition_operator=cond.get('condition_operator', '=='),
                    condition_value=cond.get('condition_value', ''),
                    logic_operator=cond.get('logic_operator', 'AND'),
                    sort_order=cond.get('sort_order', 0)
                )

        logger.info(f"✅ دکمه {button_id} با موفقیت از نسخه‌ی {snapshot.get('_version_number', 'نامشخص')} بازیابی شد.")
        return True

    except Exception as e:
        logger.error(f"❌ خطا در بازیابی دکمه {button_id} از اسنپ‌شات: {e}", exc_info=True)
        return False


# ==================== توابع اصلی نسخه‌سازی ====================

def save_button_version(button_id, created_by, note=None):
    """
    ذخیره‌ی نسخه‌ی جدید از دکمه.
    یک اسنپ‌شات کامل گرفته شده و با شماره نسخه‌ی بعدی ذخیره می‌شود.
    
    پارامترها:
        button_id: شناسه دکمه
        created_by: شناسه کاربر (ادمین) که نسخه را ذخیره می‌کند
        note: توضیح اختیاری برای این نسخه
    
    بازگشت: (success, version_number)
    """
    # گرفتن اسنپ‌شات
    snapshot = _serialize_button_snapshot(button_id)
    if not snapshot:
        logger.error(f"دکمه {button_id} یافت نشد.")
        return False, None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # محاسبه شماره نسخه بعدی
        cursor.execute(
            "SELECT MAX(version_number) as max_version FROM button_versions WHERE button_id = ?",
            (button_id,)
        )
        row = cursor.fetchone()
        next_version = (row['max_version'] or 0) + 1
        
        # اضافه کردن شماره نسخه به اسنپ‌شات (برای رجیستر بعدی)
        snapshot['_version_number'] = next_version
        snapshot['_note'] = note
        
        # ذخیره در دیتابیس
        cursor.execute("""
            INSERT INTO button_versions (button_id, version_number, snapshot_data, created_by, note)
            VALUES (?, ?, ?, ?, ?)
        """, (
            button_id,
            next_version,
            json.dumps(snapshot, ensure_ascii=False),
            created_by,
            note
        ))
        conn.commit()
        
        logger.info(f"✅ نسخه {next_version} برای دکمه {button_id} توسط {created_by} ذخیره شد.")
        return True, next_version


def get_button_versions(button_id, limit=20, offset=0):
    """
    دریافت لیست نسخه‌های یک دکمه با صفحه‌بندی.
    مرتب‌شده بر اساس شماره نسخه (نزولی - جدیدترین اول).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, button_id, version_number, created_by, note, created_at
            FROM button_versions
            WHERE button_id = ?
            ORDER BY version_number DESC
            LIMIT ? OFFSET ?
        """, (button_id, limit, offset))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_button_version(button_id, version_number):
    """
    دریافت یک نسخه‌ی خاص از یک دکمه به همراه دیتای کامل آن.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM button_versions
            WHERE button_id = ? AND version_number = ?
        """, (button_id, version_number))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        result = dict(row)
        if result.get('snapshot_data'):
            try:
                result['snapshot_data'] = json.loads(result['snapshot_data'])
            except:
                pass
        return result


def get_latest_version(button_id):
    """
    دریافت آخرین نسخه‌ی ثبت‌شده برای یک دکمه.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM button_versions
            WHERE button_id = ?
            ORDER BY version_number DESC
            LIMIT 1
        """, (button_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        result = dict(row)
        if result.get('snapshot_data'):
            try:
                result['snapshot_data'] = json.loads(result['snapshot_data'])
            except:
                pass
        return result


def get_total_versions(button_id):
    """تعداد کل نسخه‌های ثبت‌شده برای یک دکمه."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM button_versions WHERE button_id = ?",
            (button_id,)
        )
        row = cursor.fetchone()
        return row['count'] if row else 0


def restore_button_version(button_id, version_number, restored_by):
    """
    بازگردانی (Rollback) یک دکمه به نسخه‌ی مشخص‌شده.
    
    پارامترها:
        button_id: شناسه دکمه‌ای که باید بازگردانی شود
        version_number: شماره نسخه‌ی مقصد
        restored_by: شناسه کاربر (ادمین) که بازگردانی را انجام می‌دهد
    
    بازگشت: True در صورت موفقیت، False در غیر این صورت
    """
    # دریافت نسخه‌ی مورد نظر
    version = get_button_version(button_id, version_number)
    if not version:
        logger.error(f"نسخه {version_number} برای دکمه {button_id} یافت نشد.")
        return False
    
    snapshot = version.get('snapshot_data')
    if not snapshot:
        logger.error(f"دیتای نسخه {version_number} برای دکمه {button_id} خراب است.")
        return False
    
    # قبل از بازگردانی، یک نسخه‌ی خودکار از وضعیت فعلی ذخیره کن (برای امنیت بیشتر)
    save_button_version(
        button_id,
        restored_by,
        note=f"نسخه‌ی خودکار قبل از بازگردانی به نسخه {version_number}"
    )
    
    # اجرای بازگردانی
    success = _restore_button_from_snapshot(button_id, snapshot, restored_by)
    
    if success:
        # لاگ بازگردانی
        logger.info(f"🔄 دکمه {button_id} توسط {restored_by} به نسخه {version_number} بازگردانی شد.")
        
        # ذخیره یک نسخه‌ی جدید با شماره‌ی بعدی که نشان دهد بازگردانی شده است
        save_button_version(
            button_id,
            restored_by,
            note=f"بازگردانی به نسخه {version_number} (توسط {restored_by})"
        )
    
    return success


def delete_button_version(version_id):
    """
    حذف یک نسخه‌ی خاص (فقط برای مدیریت).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # گرفتن اطلاعات نسخه برای لاگ
        cursor.execute("SELECT button_id, version_number FROM button_versions WHERE id = ?", (version_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        cursor.execute("DELETE FROM button_versions WHERE id = ?", (version_id,))
        conn.commit()
        
        logger.info(f"🗑️ نسخه {row['version_number']} دکمه {row['button_id']} حذف شد.")
        return True


def delete_old_versions(button_id, keep_count=10):
    """
    حذف نسخه‌های قدیمی‌تر از تعداد مشخص (برای مدیریت حجم دیتابیس).
    پیش‌فرض: فقط ۱۰ نسخه‌ی آخر نگهداری می‌شوند.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # دریافت لیست نسخه‌هایی که باید حذف شوند (به جز keep_count عدد آخر)
        cursor.execute("""
            SELECT id FROM button_versions
            WHERE button_id = ?
            ORDER BY version_number DESC
            LIMIT -1 OFFSET ?
        """, (button_id, keep_count))
        rows = cursor.fetchall()
        
        if not rows:
            return 0
        
        ids_to_delete = [row['id'] for row in rows]
        placeholders = ','.join(['?'] * len(ids_to_delete))
        cursor.execute(f"DELETE FROM button_versions WHERE id IN ({placeholders})", ids_to_delete)
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            logger.info(f"🗑️ {deleted_count} نسخه‌ی قدیمی دکمه {button_id} حذف شدند.")
        return deleted_count


def get_button_version_by_version_id(version_id):
    """
    دریافت یک نسخه بر اساس شناسه رکورد.
    
    پارامترها:
        version_id: شناسه رکورد نسخه
    
    بازگشت: دیکشنری اطلاعات نسخه یا None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM button_versions WHERE id = ?", (version_id,))
        row = cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        if result.get('snapshot_data'):
            try:
                result['snapshot_data'] = json.loads(result['snapshot_data'])
            except:
                pass
        return result


def get_version_count_by_button(button_id):
    """
    تعداد نسخه‌های یک دکمه.
    
    پارامترها:
        button_id: شناسه دکمه
    
    بازگشت: تعداد نسخه‌ها
    """
    return get_total_versions(button_id)


def get_all_versioned_buttons():
    """
    دریافت لیست دکمه‌هایی که حداقل یک نسخه دارند.
    
    بازگشت: لیست دیکشنری‌های دکمه‌ها با تعداد نسخه‌ها
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                b.id,
                b.name,
                COUNT(v.id) as version_count,
                MAX(v.version_number) as latest_version,
                MAX(v.created_at) as latest_version_date
            FROM buttons b
            INNER JOIN button_versions v ON b.id = v.button_id
            WHERE b.is_active = 1
            GROUP BY b.id, b.name
            ORDER BY version_count DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


__all__ = [
    'save_button_version',
    'get_button_versions',
    'get_button_version',
    'get_latest_version',
    'get_total_versions',
    'restore_button_version',
    'delete_button_version',
    'delete_old_versions',
    'get_button_version_by_version_id',
    'get_version_count_by_button',
    'get_all_versioned_buttons',
]