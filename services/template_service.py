# services/template_service.py
# سرویس مدیریت الگوهای سوال (Question Templates)
# منطق کسب‌وکار مربوط به ایجاد، ویرایش، حذف، کپی، استخراج و اعمال الگوها

import json
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime
from logger_config import logger
from repositories import QuestionRepository, ButtonRepository
from services.button_service import ButtonService
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class TemplateService:
    """سرویس مدیریت الگوهای سوال"""
    
    def __init__(self, connection, question_repo: Optional[QuestionRepository] = None,
                 button_repo: Optional[ButtonRepository] = None):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            question_repo: ریپازیتوری سوالات (اختیاری)
            button_repo: ریپازیتوری دکمه‌ها (اختیاری)
        """
        self._connection = connection
        self._question_repo = question_repo or QuestionRepository(connection)
        self._button_repo = button_repo or ButtonRepository(connection)
        self._button_service = ButtonService(connection, button_repo)
    
    # ============================================================
    # عملیات پایه
    # ============================================================
    
    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """دریافت یک الگو بر اساس شناسه"""
        return self._get_template_by_id(template_id)
    
    def get_template_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """دریافت یک الگو بر اساس نام"""
        return self._get_template_by_name(name)
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """دریافت لیست تمام الگوها"""
        return self._get_templates()
    
    def get_templates_count(self) -> int:
        """تعداد کل الگوها"""
        return len(self._get_templates())
    
    # ============================================================
    # عملیات CRUD
    # ============================================================
    
    def create_template(self, name: str, description: str,
                        questions_data: List[Dict[str, Any]],
                        created_by: int) -> Optional[int]:
        """
        ایجاد الگوی جدید
        
        پارامترها:
            name: نام الگو
            description: توضیحات الگو
            questions_data: لیست سوالات
            created_by: شناسه کاربر ایجادکننده
        
        بازگشت: شناسه الگو یا None در صورت خطا
        """
        # بررسی تکراری نبودن نام
        existing = self._get_template_by_name(name)
        if existing:
            logger.warning(f"Template with name '{name}' already exists")
            return None
        
        # اعتبارسنجی سوالات
        if not questions_data:
            logger.warning("No questions provided for template")
            return None
        
        return self._save_template(name, description, questions_data, created_by)
    
    def update_template(self, template_id: int, name: str,
                        description: str,
                        questions_data: List[Dict[str, Any]]) -> bool:
        """
        بروزرسانی یک الگو
        
        پارامترها:
            template_id: شناسه الگو
            name: نام جدید
            description: توضیحات جدید
            questions_data: لیست سوالات جدید
        
        بازگشت: True در صورت موفقیت
        """
        # بررسی وجود الگو
        template = self._get_template_by_id(template_id)
        if not template:
            logger.warning(f"Template {template_id} not found")
            return False
        
        # بررسی تکراری نبودن نام (به جز خودش)
        existing = self._get_template_by_name(name)
        if existing and existing['id'] != template_id:
            logger.warning(f"Template with name '{name}' already exists")
            return False
        
        # اعتبارسنجی سوالات
        if not questions_data:
            logger.warning("No questions provided for template")
            return False
        
        return self._update_template(template_id, name, description, questions_data)
    
    def delete_template(self, template_id: int) -> bool:
        """
        حذف یک الگو
        
        پارامترها:
            template_id: شناسه الگو
        
        بازگشت: True در صورت موفقیت
        """
        template = self._get_template_by_id(template_id)
        if not template:
            logger.warning(f"Template {template_id} not found")
            return False
        
        return self._delete_template(template_id)
    
    def copy_template(self, template_id: int, new_name: str,
                      created_by: int) -> Optional[int]:
        """
        کپی یک الگو
        
        پارامترها:
            template_id: شناسه الگوی مبدا
            new_name: نام جدید
            created_by: شناسه کاربر ایجادکننده
        
        بازگشت: شناسه الگوی جدید یا None
        """
        template = self._get_template_by_id(template_id)
        if not template:
            logger.warning(f"Template {template_id} not found")
            return None
        
        # بررسی تکراری نبودن نام
        existing = self._get_template_by_name(new_name)
        if existing:
            logger.warning(f"Template with name '{new_name}' already exists")
            return None
        
        questions_data = json.loads(template.get('questions_data', '[]'))
        description = template.get('description', '')
        
        return self._save_template(new_name, description, questions_data, created_by)
    
    # ============================================================
    # استخراج الگو از دکمه
    # ============================================================
    
    def extract_from_button(self, button_id: int, template_name: str,
                            description: str, created_by: int) -> Optional[int]:
        """
        استخراج الگو از یک دکمه موجود
        
        پارامترها:
            button_id: شناسه دکمه
            template_name: نام الگو
            description: توضیحات الگو
            created_by: شناسه کاربر ایجادکننده
        
        بازگشت: شناسه الگوی ایجادشده یا None
        """
        # بررسی وجود دکمه
        button = self._button_repo.get_by_id(button_id)
        if not button:
            logger.warning(f"Button {button_id} not found")
            return None
        
        # دریافت سوالات دکمه
        questions = self._question_repo.get_by_button(button_id)
        if not questions:
            logger.warning(f"No questions found for button {button_id}")
            return None
        
        # تبدیل سوالات به فرمت الگو
        questions_data = []
        for q in questions:
            q_dict = dict(q)
            # حذف فیلدهای اضافی
            q_dict.pop('id', None)
            q_dict.pop('button_id', None)
            q_dict.pop('created_at', None)
            
            # دریافت گزینه‌ها
            options = self._question_repo.get_options(q['id'])
            if options:
                q_dict['options'] = [dict(opt) for opt in options]
                for opt in q_dict['options']:
                    opt.pop('id', None)
                    opt.pop('question_id', None)
                    opt.pop('created_at', None)
                    opt.pop('is_active', None)
            
            # دریافت شرط‌ها
            conditions = self._question_repo.get_conditions(q['id'])
            if conditions:
                q_dict['conditions'] = [dict(cond) for cond in conditions]
                for cond in q_dict['conditions']:
                    cond.pop('id', None)
                    cond.pop('question_id', None)
                    cond.pop('created_at', None)
                    cond.pop('is_active', None)
            
            questions_data.append(q_dict)
        
        # بررسی تکراری نبودن نام
        existing = self._get_template_by_name(template_name)
        if existing:
            logger.warning(f"Template with name '{template_name}' already exists")
            return None
        
        return self._save_template(template_name, description, questions_data, created_by)
    
    # ============================================================
    # اعمال الگو به دکمه
    # ============================================================
    
    def apply_template_to_button(self, template_id: int, button_id: int) -> bool:
        """
        اعمال یک الگو به یک دکمه (جایگزینی سوالات فعلی)
        
        پارامترها:
            template_id: شناسه الگو
            button_id: شناسه دکمه
        
        بازگشت: True در صورت موفقیت
        """
        # بررسی وجود الگو
        template = self._get_template_by_id(template_id)
        if not template:
            logger.warning(f"Template {template_id} not found")
            return False
        
        # بررسی وجود دکمه
        button = self._button_repo.get_by_id(button_id)
        if not button:
            logger.warning(f"Button {button_id} not found")
            return False
        
        questions_data = json.loads(template.get('questions_data', '[]'))
        if not questions_data:
            logger.warning(f"No questions in template {template_id}")
            return False
        
        try:
            # ۱. حذف سوالات فعلی دکمه
            existing_questions = self._question_repo.get_by_button(button_id, include_inactive=True)
            for q in existing_questions:
                self._question_repo.delete_options_by_question(q['id'])
                self._question_repo.delete_conditions_by_question(q['id'])
                self._question_repo.delete(q['id'])
            
            # ۲. ایجاد سوالات جدید از الگو
            created_count = 0
            for q_data in questions_data:
                # استخراج گزینه‌ها و شرط‌ها
                options = q_data.pop('options', [])
                conditions = q_data.pop('conditions', [])
                
                # ایجاد سوال
                q_id = self._question_repo.create(
                    button_id=button_id,
                    question_text=q_data.get('question_text', 'سوال بدون متن'),
                    question_type=q_data.get('question_type', 'text'),
                    is_required=q_data.get('is_required', 0),
                    needs_button=q_data.get('needs_button', 0),
                    sort_order=q_data.get('sort_order', 0),
                    validation_type=q_data.get('validation_type', 'none'),
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
                    
                    # افزودن گزینه‌ها
                    for opt in options:
                        self._question_repo.add_option(
                            q_id,
                            opt.get('option_text', 'گزینه'),
                            opt.get('callback_data'),
                            opt.get('sort_order', 0)
                        )
                    
                    # افزودن شرط‌ها
                    for cond in conditions:
                        self._question_repo.add_condition(
                            q_id,
                            cond.get('condition_question_id', 0),
                            cond.get('condition_operator', '=='),
                            cond.get('condition_value', ''),
                            cond.get('logic_operator', 'AND'),
                            cond.get('sort_order', 0)
                        )
            
            logger.info(f"✅ Template {template_id} applied to button {button_id} ({created_count} questions)")
            return True
            
        except Exception as e:
            # ✅ استفاده از log_database_error با traceback کامل
            log_database_error(
                f"Error applying template {template_id} to button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # متدهای خصوصی (دسترسی به دیتابیس)
    # ============================================================
    
    def _get_templates(self) -> List[Dict[str, Any]]:
        """دریافت لیست تمام الگوها"""
        from database import get_db_connection
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM question_templates ORDER BY name")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            log_database_error(
                f"Error getting templates: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def _get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """دریافت یک الگو بر اساس شناسه"""
        from database import get_db_connection
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM question_templates WHERE id = ?", (template_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            log_database_error(
                f"Error getting template by id {template_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def _get_template_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """دریافت یک الگو بر اساس نام"""
        from database import get_db_connection
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM question_templates WHERE name = ?", (name,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            log_database_error(
                f"Error getting template by name '{name}': {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def _save_template(self, name: str, description: str,
                       questions_data: List[Dict[str, Any]],
                       created_by: int) -> Optional[int]:
        """ذخیره یک الگوی جدید"""
        from database import get_db_connection
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
                f"Error saving template '{name}': {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def _update_template(self, template_id: int, name: str,
                         description: str,
                         questions_data: List[Dict[str, Any]]) -> bool:
        """بروزرسانی یک الگو"""
        from database import get_db_connection
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
                f"Error updating template {template_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def _delete_template(self, template_id: int) -> bool:
        """حذف یک الگو"""
        from database import get_db_connection
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
                f"Error deleting template {template_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # الگوهای پیش‌فرض
    # ============================================================
    
    def get_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """دریافت الگوهای پیش‌فرض"""
        return {
            'default': {
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
            },
            'contact_basic': {
                'name': 'اطلاعات تماس پایه',
                'description': 'الگوی ساده برای دریافت اطلاعات تماس کاربر',
                'questions': [
                    {
                        'question_text': '👤 نام و نام خانوادگی خود را وارد کنید:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'persian_text',
                        'length_validation_enabled': 1,
                        'min_length': 3,
                        'max_length': 50,
                        'needs_button': 0,
                        'sort_order': 0
                    },
                    {
                        'question_text': '📞 شماره تماس خود را وارد کنید:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'phone',
                        'needs_button': 0,
                        'sort_order': 1
                    },
                    {
                        'question_text': '📧 ایمیل خود را وارد کنید (اختیاری):',
                        'question_type': 'text',
                        'is_required': 0,
                        'validation_type': 'email',
                        'needs_button': 0,
                        'sort_order': 2
                    }
                ]
            },
            'contact_full': {
                'name': 'اطلاعات کامل کاربر',
                'description': 'الگوی کامل برای دریافت اطلاعات کامل کاربر',
                'questions': [
                    {
                        'question_text': '👤 نام و نام خانوادگی:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'persian_text',
                        'length_validation_enabled': 1,
                        'min_length': 3,
                        'max_length': 50,
                        'needs_button': 0,
                        'sort_order': 0
                    },
                    {
                        'question_text': '🆔 کد ملی:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'national_code',
                        'needs_button': 0,
                        'sort_order': 1
                    },
                    {
                        'question_text': '📞 شماره تماس:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'phone',
                        'needs_button': 0,
                        'sort_order': 2
                    },
                    {
                        'question_text': '📧 ایمیل:',
                        'question_type': 'text',
                        'is_required': 0,
                        'validation_type': 'email',
                        'needs_button': 0,
                        'sort_order': 3
                    },
                    {
                        'question_text': '🏠 آدرس:',
                        'question_type': 'text',
                        'is_required': 0,
                        'validation_type': 'text',
                        'length_validation_enabled': 1,
                        'min_length': 5,
                        'needs_button': 0,
                        'sort_order': 4
                    },
                    {
                        'question_text': '📝 توضیحات اضافی:',
                        'question_type': 'text',
                        'is_required': 0,
                        'validation_type': 'text',
                        'needs_button': 0,
                        'sort_order': 5
                    }
                ]
            },
            'vehicle': {
                'name': 'اطلاعات خودرو',
                'description': 'الگوی دریافت اطلاعات خودرو',
                'questions': [
                    {
                        'question_text': '🚗 نوع خودرو:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'text',
                        'needs_button': 1,
                        'sort_order': 0,
                        'options': [
                            {'option_text': 'سواری', 'callback_data': 'vehicle_car'},
                            {'option_text': 'وانت', 'callback_data': 'vehicle_pickup'},
                            {'option_text': 'موتورسیکلت', 'callback_data': 'vehicle_motorcycle'},
                            {'option_text': 'سنگین', 'callback_data': 'vehicle_heavy'}
                        ]
                    },
                    {
                        'question_text': '🔢 شماره پلاک:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'plate',
                        'needs_button': 0,
                        'sort_order': 1
                    },
                    {
                        'question_text': '📅 سال تولید:',
                        'question_type': 'text',
                        'is_required': 0,
                        'validation_type': 'number',
                        'numeric_validation_enabled': 1,
                        'min_value': 1300,
                        'max_value': 1404,
                        'needs_button': 0,
                        'sort_order': 2
                    }
                ]
            },
            'service_request': {
                'name': 'درخواست خدمات',
                'description': 'الگوی دریافت اطلاعات درخواست خدمات',
                'questions': [
                    {
                        'question_text': '👤 نام و نام خانوادگی:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'persian_text',
                        'length_validation_enabled': 1,
                        'min_length': 3,
                        'max_length': 50,
                        'needs_button': 0,
                        'sort_order': 0
                    },
                    {
                        'question_text': '📞 شماره تماس:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'phone',
                        'needs_button': 0,
                        'sort_order': 1
                    },
                    {
                        'question_text': '📋 نوع خدمت مورد نظر:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'text',
                        'needs_button': 1,
                        'sort_order': 2,
                        'options': [
                            {'option_text': 'مشاوره', 'callback_data': 'service_consult'},
                            {'option_text': 'ثبت نام', 'callback_data': 'service_register'},
                            {'option_text': 'پرداخت', 'callback_data': 'service_payment'},
                            {'option_text': 'گزارش', 'callback_data': 'service_report'},
                            {'option_text': 'سایر', 'callback_data': 'service_other'}
                        ]
                    },
                    {
                        'question_text': '📝 توضیحات کامل درخواست:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'text',
                        'length_validation_enabled': 1,
                        'min_length': 10,
                        'needs_button': 0,
                        'sort_order': 3
                    },
                    {
                        'question_text': '📎 فایل ضمیمه (اختیاری):',
                        'question_type': 'file',
                        'is_required': 0,
                        'file_validation_enabled': 1,
                        'allowed_formats': 'pdf,jpg,png,doc,docx',
                        'max_file_size': 5120,
                        'needs_button': 0,
                        'sort_order': 4
                    }
                ]
            },
            'payment': {
                'name': 'پرداخت',
                'description': 'الگوی دریافت اطلاعات برای پرداخت',
                'questions': [
                    {
                        'question_text': '👤 نام پرداخت‌کننده:',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'persian_text',
                        'length_validation_enabled': 1,
                        'min_length': 3,
                        'max_length': 50,
                        'needs_button': 0,
                        'sort_order': 0
                    },
                    {
                        'question_text': '💰 مبلغ پرداختی (ریال):',
                        'question_type': 'text',
                        'is_required': 1,
                        'validation_type': 'number',
                        'numeric_validation_enabled': 1,
                        'min_value': 1000,
                        'needs_button': 0,
                        'sort_order': 1
                    },
                    {
                        'question_text': '📝 توضیحات پرداخت:',
                        'question_type': 'text',
                        'is_required': 0,
                        'validation_type': 'text',
                        'length_validation_enabled': 1,
                        'max_length': 200,
                        'needs_button': 0,
                        'sort_order': 2
                    },
                    {
                        'question_text': '📎 رسید پرداخت (فایل):',
                        'question_type': 'file',
                        'is_required': 1,
                        'file_validation_enabled': 1,
                        'allowed_formats': 'jpg,png,pdf',
                        'max_file_size': 5120,
                        'needs_button': 0,
                        'sort_order': 3
                    }
                ]
            }
        }
    
    def init_default_templates(self) -> None:
        """مقداردهی اولیه الگوهای پیش‌فرض در دیتابیس"""
        try:
            # بررسی اینکه آیا الگویی وجود دارد
            templates = self._get_templates()
            if templates:
                logger.info(f"ℹ️ Found {len(templates)} existing templates, skipping default initialization")
                return
            
            # ایجاد الگوهای پیش‌فرض
            default_templates = self.get_default_templates()
            for key, template in default_templates.items():
                self._save_template(
                    name=template['name'],
                    description=template['description'],
                    questions_data=template['questions'],
                    created_by=1  # سیستم
                )
                logger.info(f"✅ Default template created: {template['name']}")
            
            logger.info(f"✅ All default templates initialized")
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error initializing default templates: {str(e)}",
                traceback=traceback.format_exc()
            )
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    def validate_template_data(self, questions_data: List[Dict[str, Any]]) -> tuple:
        """
        اعتبارسنجی داده‌های الگو
        
        پارامترها:
            questions_data: لیست سوالات
        
        بازگشت: (is_valid, error_message)
        """
        if not questions_data:
            return False, "الگو باید حداقل یک سوال داشته باشد."
        
        for i, q in enumerate(questions_data):
            if not q.get('question_text'):
                return False, f"سوال {i+1} متن ندارد."
            
            # اعتبارسنجی گزینه‌ها
            if q.get('needs_button', 0) == 1:
                options = q.get('options', [])
                if len(options) < 2:
                    return False, f"سوال {i+1} دکمه‌ای است اما حداقل ۲ گزینه ندارد."
                
                for opt in options:
                    if not opt.get('option_text'):
                        return False, f"گزینه‌ای در سوال {i+1} متن ندارد."
        
        return True, ""
    
    def get_template_questions_count(self, template_id: int) -> int:
        """تعداد سوالات یک الگو"""
        template = self._get_template_by_id(template_id)
        if not template:
            return 0
        questions = json.loads(template.get('questions_data', '[]'))
        return len(questions)
    
    def search_templates(self, keyword: str) -> List[Dict[str, Any]]:
        """جستجوی الگوها بر اساس کلمه کلیدی"""
        templates = self._get_templates()
        keyword_lower = keyword.lower()
        results = []
        for tmpl in templates:
            name = tmpl.get('name', '').lower()
            description = tmpl.get('description', '').lower()
            if keyword_lower in name or keyword_lower in description:
                results.append(tmpl)
        return results
    
    def get_template_preview(self, template_id: int) -> Dict[str, Any]:
        """
        دریافت پیش‌نمایش یک الگو
        
        پارامترها:
            template_id: شناسه الگو
        
        بازگشت: دیکشنری شامل اطلاعات الگو و سوالات
        """
        template = self._get_template_by_id(template_id)
        if not template:
            return {'error': 'الگو یافت نشد.'}
        
        questions = json.loads(template.get('questions_data', '[]'))
        return {
            'id': template['id'],
            'name': template.get('name'),
            'description': template.get('description'),
            'created_by': template.get('created_by'),
            'created_at': template.get('created_at'),
            'updated_at': template.get('updated_at'),
            'questions': questions,
            'question_count': len(questions)
        }


__all__ = [
    'TemplateService',
]