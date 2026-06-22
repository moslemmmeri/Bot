# repositories/question_repository.py
# ریپازیتوری سوالات

import json
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime
from logger_config import logger
from .base_repository import BaseRepository
from models.question import Question, QuestionType, ValidationType
from utils.error_handler import log_database_error  # ✅ اضافه شد


class QuestionRepository(BaseRepository):
    """ریپازیتوری سوالات - مدیریت عملیات دیتابیس مربوط به سوالات، گزینه‌ها و شرط‌ها"""
    
    def __init__(self, connection):
        super().__init__(connection, 'questions', 'id')
    
    # ============================================================
    # متدهای پایه سوالات
    # ============================================================
    
    def get_by_id(self, question_id: int) -> Optional[Dict[str, Any]]:
        """دریافت سوال بر اساس شناسه"""
        try:
            return super().get_by_id(question_id)
        except Exception as e:
            log_database_error(
                f"Error getting question by id {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_by_button(self, button_id: int, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        دریافت سوالات یک دکمه
        
        پارامترها:
            button_id: شناسه دکمه
            include_inactive: آیا سوالات غیرفعال نیز نمایش داده شوند
        """
        try:
            if include_inactive:
                query = """
                    SELECT * FROM questions 
                    WHERE button_id = ? 
                    ORDER BY sort_order, id
                """
                return self.custom_query(query, [button_id])
            else:
                query = """
                    SELECT * FROM questions 
                    WHERE button_id = ? AND is_active = 1
                    ORDER BY sort_order, id
                """
                return self.custom_query(query, [button_id])
        except Exception as e:
            log_database_error(
                f"Error getting questions by button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_active_questions(self, button_id: int) -> List[Dict[str, Any]]:
        """دریافت سوالات فعال یک دکمه"""
        return self.get_by_button(button_id, include_inactive=False)
    
    def get_previous_questions(self, button_id: int, current_question_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        دریافت سوالات قبلی یک دکمه (برای شرط‌ها)
        
        پارامترها:
            button_id: شناسه دکمه
            current_question_id: شناسه سوال فعلی (برای حذف آن از لیست)
        """
        try:
            if current_question_id:
                query = """
                    SELECT * FROM questions 
                    WHERE button_id = ? AND id < ? AND is_active = 1
                    ORDER BY sort_order, id
                """
                return self.custom_query(query, [button_id, current_question_id])
            else:
                query = """
                    SELECT * FROM questions 
                    WHERE button_id = ? AND is_active = 1
                    ORDER BY sort_order, id
                """
                return self.custom_query(query, [button_id])
        except Exception as e:
            log_database_error(
                f"Error getting previous questions for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_next_question(self, button_id: int, current_sort_order: int) -> Optional[Dict[str, Any]]:
        """دریافت سوال بعدی بر اساس ترتیب"""
        try:
            query = """
                SELECT * FROM questions 
                WHERE button_id = ? AND sort_order > ? AND is_active = 1
                ORDER BY sort_order ASC
                LIMIT 1
            """
            return self.custom_query_one(query, [button_id, current_sort_order])
        except Exception as e:
            log_database_error(
                f"Error getting next question for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    # ============================================================
    # عملیات ایجاد و به‌روزرسانی سوالات
    # ============================================================
    
    def create(self, button_id: int, question_text: str, question_type: str = "text",
               is_required: bool = False, needs_button: bool = False,
               sort_order: int = 0, **kwargs) -> Optional[int]:
        """
        ایجاد سوال جدید
        
        پارامترها:
            button_id: شناسه دکمه
            question_text: متن سوال
            question_type: نوع سوال
            is_required: اجباری بودن
            needs_button: آیا دکمه‌ای است
            sort_order: ترتیب نمایش
            **kwargs: سایر فیلدهای اعتبارسنجی
        
        بازگشت: شناسه سوال ایجادشده
        """
        try:
            data = {
                'button_id': button_id,
                'question_text': question_text,
                'question_type': question_type,
                'is_required': 1 if is_required else 0,
                'needs_button': 1 if needs_button else 0,
                'sort_order': sort_order,
                'is_active': 1,
                'created_at': datetime.now().isoformat()
            }
            
            # افزودن سایر فیلدها
            validation_fields = [
                'validation_type', 'validation_enabled', 'validation_rule', 'error_message',
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
                'auto_fix_enabled', 'validation_error', 'validation_hint',
                'array_name'
            ]
            
            for field in validation_fields:
                if field in kwargs and kwargs[field] is not None:
                    data[field] = kwargs[field]
            
            return self.insert(data)
        except Exception as e:
            log_database_error(
                f"Error creating question for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def update(self, question_id: int, data: Dict[str, Any]) -> bool:
        """به‌روزرسانی سوال"""
        try:
            return super().update(question_id, data)
        except Exception as e:
            log_database_error(
                f"Error updating question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_text(self, question_id: int, question_text: str) -> bool:
        """به‌روزرسانی متن سوال"""
        try:
            return self.update(question_id, {'question_text': question_text})
        except Exception as e:
            log_database_error(
                f"Error updating question text for {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_type(self, question_id: int, question_type: str) -> bool:
        """به‌روزرسانی نوع سوال"""
        try:
            return self.update(question_id, {'question_type': question_type})
        except Exception as e:
            log_database_error(
                f"Error updating question type for {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def toggle_active(self, question_id: int) -> bool:
        """تغییر وضعیت فعال/غیرفعال سوال"""
        try:
            question = self.get_by_id(question_id)
            if not question:
                return False
            new_status = 0 if question.get('is_active', 1) == 1 else 1
            return self.update(question_id, {'is_active': new_status})
        except Exception as e:
            log_database_error(
                f"Error toggling active status for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def toggle_required(self, question_id: int) -> bool:
        """تغییر وضعیت اجباری بودن سوال"""
        try:
            question = self.get_by_id(question_id)
            if not question:
                return False
            new_status = 0 if question.get('is_required', 0) == 1 else 1
            return self.update(question_id, {'is_required': new_status})
        except Exception as e:
            log_database_error(
                f"Error toggling required status for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def toggle_validation(self, question_id: int, feature: str) -> bool:
        """
        تغییر وضعیت یک قابلیت اعتبارسنجی
        
        پارامترها:
            question_id: شناسه سوال
            feature: نام قابلیت (validation_enabled, length_validation_enabled, ...)
        """
        valid_features = [
            'validation_enabled', 'length_validation_enabled', 'word_validation_enabled',
            'numeric_validation_enabled', 'date_validation_enabled', 'file_validation_enabled',
            'dimensions_enabled', 'pattern_validation_enabled', 'contains_validation_enabled',
            'conditional_enabled', 'auto_fix_enabled'
        ]
        
        if feature not in valid_features:
            return False
        
        try:
            question = self.get_by_id(question_id)
            if not question:
                return False
            
            new_status = 0 if question.get(feature, 0) == 1 else 1
            return self.update(question_id, {feature: new_status})
        except Exception as e:
            log_database_error(
                f"Error toggling validation {feature} for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_validation_type(self, question_id: int, validation_type: str) -> bool:
        """به‌روزرسانی نوع اعتبارسنجی"""
        try:
            return self.update(question_id, {'validation_type': validation_type})
        except Exception as e:
            log_database_error(
                f"Error updating validation type for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update_validation_settings(self, question_id: int, settings: Dict[str, Any]) -> bool:
        """به‌روزرسانی تنظیمات اعتبارسنجی"""
        try:
            return self.update(question_id, settings)
        except Exception as e:
            log_database_error(
                f"Error updating validation settings for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete(self, question_id: int) -> bool:
        """حذف سوال و تمام گزینه‌ها و شرط‌های مرتبط"""
        try:
            # حذف گزینه‌ها
            self._delete_options_by_question(question_id)
            # حذف شرط‌ها
            self._delete_conditions_by_question(question_id)
            # حذف سوال
            return super().delete(question_id)
        except Exception as e:
            log_database_error(
                f"Error deleting question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete_by_button(self, button_id: int) -> int:
        """حذف تمام سوالات یک دکمه"""
        try:
            questions = self.get_by_button(button_id, include_inactive=True)
            count = 0
            for q in questions:
                if self.delete(q['id']):
                    count += 1
            return count
        except Exception as e:
            log_database_error(
                f"Error deleting questions for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # مدیریت گزینه‌ها (برای سوالات دکمه‌ای)
    # ============================================================
    
    def get_options(self, question_id: int) -> List[Dict[str, Any]]:
        """دریافت گزینه‌های یک سوال"""
        try:
            query = """
                SELECT * FROM question_options 
                WHERE question_id = ? AND is_active = 1
                ORDER BY sort_order, id
            """
            return self.custom_query(query, [question_id])
        except Exception as e:
            log_database_error(
                f"Error getting options for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_option_by_callback(self, callback_data: str) -> Optional[Dict[str, Any]]:
        """دریافت گزینه بر اساس callback_data"""
        try:
            query = """
                SELECT * FROM question_options 
                WHERE callback_data = ? AND is_active = 1
                LIMIT 1
            """
            return self.custom_query_one(query, [callback_data])
        except Exception as e:
            log_database_error(
                f"Error getting option by callback {callback_data}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_option_by_id(self, option_id: int) -> Optional[Dict[str, Any]]:
        """دریافت گزینه بر اساس شناسه"""
        try:
            query = "SELECT * FROM question_options WHERE id = ?"
            return self.custom_query_one(query, [option_id])
        except Exception as e:
            log_database_error(
                f"Error getting option by id {option_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def add_option(self, question_id: int, option_text: str,
                   callback_data: Optional[str] = None,
                   sort_order: int = 0) -> Optional[int]:
        """
        افزودن گزینه جدید به سوال
        
        پارامترها:
            question_id: شناسه سوال
            option_text: متن گزینه
            callback_data: داده کالبک (اختیاری)
            sort_order: ترتیب نمایش
        
        بازگشت: شناسه گزینه ایجادشده
        """
        try:
            import time
            if callback_data is None:
                callback_data = f"qopt_{question_id}_{int(time.time())}"
            
            data = {
                'question_id': question_id,
                'option_text': option_text,
                'callback_data': callback_data,
                'sort_order': sort_order,
                'is_active': 1,
                'created_at': datetime.now().isoformat()
            }
            
            # به‌روزرسانی needs_button سوال
            self.update(question_id, {'needs_button': 1})
            
            return self._insert_option(data)
        except Exception as e:
            log_database_error(
                f"Error adding option to question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def _insert_option(self, data: Dict[str, Any]) -> Optional[int]:
        """درج گزینه در دیتابیس"""
        try:
            query = """
                INSERT INTO question_options (question_id, option_text, callback_data, sort_order, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (
                    data['question_id'],
                    data['option_text'],
                    data['callback_data'],
                    data['sort_order'],
                    data['is_active'],
                    data['created_at']
                ))
                self._connection.commit()
                return cursor.get_lastrowid()
        except Exception as e:
            log_database_error(
                f"Error inserting option: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return None
    
    def update_option(self, option_id: int, option_text: str) -> bool:
        """به‌روزرسانی متن گزینه"""
        try:
            query = "UPDATE question_options SET option_text = ? WHERE id = ?"
            return self.custom_execute(query, [option_text, option_id]) > 0
        except Exception as e:
            log_database_error(
                f"Error updating option {option_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete_option(self, option_id: int) -> bool:
        """حذف یک گزینه"""
        try:
            # بررسی تعداد گزینه‌های باقی‌مانده
            option = self.get_option_by_id(option_id)
            if not option:
                return False
            
            question_id = option.get('question_id')
            query = "DELETE FROM question_options WHERE id = ?"
            result = self.custom_execute(query, [option_id])
            
            if result > 0:
                # بررسی اینکه آیا گزینه‌ای باقی مانده است
                remaining = self.get_options(question_id)
                if not remaining:
                    self.update(question_id, {'needs_button': 0})
            
            return result > 0
        except Exception as e:
            log_database_error(
                f"Error deleting option {option_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete_options_by_question(self, question_id: int) -> int:
        """حذف تمام گزینه‌های یک سوال"""
        return self._delete_options_by_question(question_id)
    
    def _delete_options_by_question(self, question_id: int) -> int:
        """حذف تمام گزینه‌های یک سوال (داخلی)"""
        try:
            query = "DELETE FROM question_options WHERE question_id = ?"
            return self.custom_execute(query, [question_id])
        except Exception as e:
            log_database_error(
                f"Error deleting options for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # مدیریت شرط‌ها
    # ============================================================
    
    def get_conditions(self, question_id: int) -> List[Dict[str, Any]]:
        """دریافت شرط‌های یک سوال"""
        try:
            query = """
                SELECT * FROM question_conditions 
                WHERE question_id = ? AND is_active = 1
                ORDER BY sort_order, id
            """
            return self.custom_query(query, [question_id])
        except Exception as e:
            log_database_error(
                f"Error getting conditions for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_condition_by_id(self, condition_id: int) -> Optional[Dict[str, Any]]:
        """دریافت شرط بر اساس شناسه"""
        try:
            query = "SELECT * FROM question_conditions WHERE id = ?"
            return self.custom_query_one(query, [condition_id])
        except Exception as e:
            log_database_error(
                f"Error getting condition by id {condition_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def add_condition(self, question_id: int, condition_question_id: int,
                      condition_operator: str, condition_value: str,
                      logic_operator: str = "AND", sort_order: int = 0) -> Optional[int]:
        """
        افزودن شرط جدید به سوال
        
        پارامترها:
            question_id: شناسه سوال
            condition_question_id: شناسه سوال مرجع
            condition_operator: عملگر شرط (==, !=, contains, ...)
            condition_value: مقدار شرط
            logic_operator: منطق ترکیب (AND, OR)
            sort_order: ترتیب نمایش
        
        بازگشت: شناسه شرط ایجادشده
        """
        try:
            data = {
                'question_id': question_id,
                'condition_question_id': condition_question_id,
                'condition_operator': condition_operator,
                'condition_value': condition_value,
                'logic_operator': logic_operator,
                'sort_order': sort_order,
                'is_active': 1,
                'created_at': datetime.now().isoformat()
            }
            return self._insert_condition(data)
        except Exception as e:
            log_database_error(
                f"Error adding condition to question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def _insert_condition(self, data: Dict[str, Any]) -> Optional[int]:
        """درج شرط در دیتابیس"""
        try:
            query = """
                INSERT INTO question_conditions (
                    question_id, condition_question_id, condition_operator,
                    condition_value, logic_operator, sort_order, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (
                    data['question_id'],
                    data['condition_question_id'],
                    data['condition_operator'],
                    data['condition_value'],
                    data['logic_operator'],
                    data['sort_order'],
                    data['is_active'],
                    data['created_at']
                ))
                self._connection.commit()
                return cursor.get_lastrowid()
        except Exception as e:
            log_database_error(
                f"Error inserting condition: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return None
    
    def update_condition(self, condition_id: int, **kwargs) -> bool:
        """به‌روزرسانی شرط"""
        try:
            valid_fields = [
                'condition_question_id', 'condition_operator', 'condition_value',
                'logic_operator', 'sort_order', 'is_active'
            ]
            
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in valid_fields and value is not None:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if not updates:
                return True
            
            values.append(condition_id)
            query = f"UPDATE question_conditions SET {', '.join(updates)} WHERE id = ?"
            return self.custom_execute(query, values) > 0
        except Exception as e:
            log_database_error(
                f"Error updating condition {condition_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete_condition(self, condition_id: int) -> bool:
        """حذف یک شرط"""
        try:
            query = "DELETE FROM question_conditions WHERE id = ?"
            return self.custom_execute(query, [condition_id]) > 0
        except Exception as e:
            log_database_error(
                f"Error deleting condition {condition_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete_conditions_by_question(self, question_id: int) -> int:
        """حذف تمام شرط‌های یک سوال"""
        return self._delete_conditions_by_question(question_id)
    
    def _delete_conditions_by_question(self, question_id: int) -> int:
        """حذف تمام شرط‌های یک سوال (داخلی)"""
        try:
            query = "DELETE FROM question_conditions WHERE question_id = ?"
            return self.custom_execute(query, [question_id])
        except Exception as e:
            log_database_error(
                f"Error deleting conditions for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    # ============================================================
    # متدهای اعتبارسنجی
    # ============================================================
    
    def get_validation_settings(self, question_id: int) -> Dict[str, Any]:
        """دریافت تنظیمات اعتبارسنجی یک سوال"""
        try:
            query = """
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
            """
            result = self.custom_query_one(query, [question_id])
            return result or {}
        except Exception as e:
            log_database_error(
                f"Error getting validation settings for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {}
    
    def get_validation_summary(self, question_id: int) -> Dict[str, bool]:
        """دریافت خلاصه وضعیت اعتبارسنجی یک سوال"""
        try:
            settings = self.get_validation_settings(question_id)
            return {
                'is_required': bool(settings.get('is_required', 0)),
                'validation_enabled': bool(settings.get('validation_enabled', 0)),
                'length_validation_enabled': bool(settings.get('length_validation_enabled', 0)),
                'word_validation_enabled': bool(settings.get('word_validation_enabled', 0)),
                'numeric_validation_enabled': bool(settings.get('numeric_validation_enabled', 0)),
                'date_validation_enabled': bool(settings.get('date_validation_enabled', 0)),
                'file_validation_enabled': bool(settings.get('file_validation_enabled', 0)),
                'dimensions_enabled': bool(settings.get('dimensions_enabled', 0)),
                'pattern_validation_enabled': bool(settings.get('pattern_validation_enabled', 0)),
                'contains_validation_enabled': bool(settings.get('contains_validation_enabled', 0)),
                'conditional_enabled': bool(settings.get('conditional_enabled', 0)),
                'auto_fix_enabled': bool(settings.get('auto_fix_enabled', 0))
            }
        except Exception as e:
            log_database_error(
                f"Error getting validation summary for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {}
    
    def enable_all_validations(self, question_id: int) -> bool:
        """فعال کردن همه قابلیت‌های اعتبارسنجی"""
        try:
            data = {
                'validation_enabled': 1,
                'length_validation_enabled': 1,
                'word_validation_enabled': 1,
                'numeric_validation_enabled': 1,
                'date_validation_enabled': 1,
                'file_validation_enabled': 1,
                'dimensions_enabled': 1,
                'pattern_validation_enabled': 1,
                'contains_validation_enabled': 1,
                'conditional_enabled': 1,
                'auto_fix_enabled': 1
            }
            return self.update(question_id, data)
        except Exception as e:
            log_database_error(
                f"Error enabling all validations for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def disable_all_validations(self, question_id: int) -> bool:
        """غیرفعال کردن همه قابلیت‌های اعتبارسنجی"""
        try:
            data = {
                'validation_enabled': 0,
                'length_validation_enabled': 0,
                'word_validation_enabled': 0,
                'numeric_validation_enabled': 0,
                'date_validation_enabled': 0,
                'file_validation_enabled': 0,
                'dimensions_enabled': 0,
                'pattern_validation_enabled': 0,
                'contains_validation_enabled': 0,
                'conditional_enabled': 0,
                'auto_fix_enabled': 0
            }
            return self.update(question_id, data)
        except Exception as e:
            log_database_error(
                f"Error disabling all validations for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def reset_validation(self, question_id: int) -> bool:
        """بازنشانی تنظیمات اعتبارسنجی به حالت پیش‌فرض"""
        try:
            data = {
                'is_required': 0,
                'validation_enabled': 0,
                'validation_type': 'none',
                'length_validation_enabled': 0,
                'min_length': None,
                'max_length': None,
                'word_validation_enabled': 0,
                'min_words': None,
                'max_words': None,
                'numeric_validation_enabled': 0,
                'min_value': None,
                'max_value': None,
                'step': None,
                'date_validation_enabled': 0,
                'min_date': None,
                'max_date': None,
                'future_only': 0,
                'past_only': 0,
                'weekdays_only': 0,
                'file_validation_enabled': 0,
                'allowed_formats': None,
                'max_file_size': None,
                'min_file_size': None,
                'max_files': None,
                'dimensions_enabled': 0,
                'required_width': None,
                'required_height': None,
                'aspect_ratio': None,
                'pattern_validation_enabled': 0,
                'regex_pattern': None,
                'starts_with': None,
                'ends_with': None,
                'contains_validation_enabled': 0,
                'contains': None,
                'not_contains': None,
                'forbidden_words': None,
                'required_words': None,
                'conditional_enabled': 0,
                'conditional_on': None,
                'conditional_value': None,
                'auto_fix_enabled': 0,
                'validation_error': None,
                'validation_hint': None
            }
            return self.update(question_id, data)
        except Exception as e:
            log_database_error(
                f"Error resetting validation for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # پروفایل‌های اعتبارسنجی
    # ============================================================
    
    def get_validation_profiles(self) -> List[Dict[str, Any]]:
        """دریافت لیست پروفایل‌های اعتبارسنجی"""
        try:
            query = "SELECT * FROM validation_profiles ORDER BY name"
            return self.custom_query(query)
        except Exception as e:
            log_database_error(
                f"Error getting validation profiles: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_validation_profile_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """دریافت پروفایل بر اساس نام"""
        try:
            query = "SELECT * FROM validation_profiles WHERE name = ?"
            result = self.custom_query_one(query, [name])
            if result and result.get('settings'):
                try:
                    result['settings'] = json.loads(result['settings'])
                except Exception as e:
                    log_database_error(
                        f"Error parsing validation profile settings for {name}: {str(e)}",
                        traceback=traceback.format_exc()
                    )
                    result['settings'] = {}
            return result
        except Exception as e:
            log_database_error(
                f"Error getting validation profile by name {name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def save_validation_profile(self, name: str, settings: Dict[str, Any]) -> bool:
        """
        ذخیره پروفایل اعتبارسنجی جدید
        
        پارامترها:
            name: نام پروفایل
            settings: تنظیمات پروفایل
        """
        try:
            # حذف فیلدهای اضافی
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
            
            filtered_settings = {k: v for k, v in settings.items() if k in valid_fields}
            
            query = """
                INSERT OR REPLACE INTO validation_profiles (name, settings)
                VALUES (?, ?)
            """
            return self.custom_execute(query, [name, json.dumps(filtered_settings, ensure_ascii=False)]) > 0
        except Exception as e:
            log_database_error(
                f"Error saving validation profile {name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def delete_validation_profile(self, name: str) -> bool:
        """حذف پروفایل اعتبارسنجی"""
        try:
            query = "DELETE FROM validation_profiles WHERE name = ?"
            return self.custom_execute(query, [name]) > 0
        except Exception as e:
            log_database_error(
                f"Error deleting validation profile {name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def apply_validation_profile(self, question_id: int, profile_name: str) -> bool:
        """
        اعمال پروفایل اعتبارسنجی به یک سوال
        
        پارامترها:
            question_id: شناسه سوال
            profile_name: نام پروفایل
        """
        try:
            profile = self.get_validation_profile_by_name(profile_name)
            if not profile:
                return False
            
            settings = profile.get('settings', {})
            return self.update_validation_settings(question_id, settings)
        except Exception as e:
            log_database_error(
                f"Error applying validation profile {profile_name} to question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # آمار و اطلاعات
    # ============================================================
    
    def get_question_count(self, button_id: Optional[int] = None) -> int:
        """تعداد سوالات (با فیلتر اختیاری دکمه)"""
        try:
            if button_id:
                query = "SELECT COUNT(*) as count FROM questions WHERE button_id = ? AND is_active = 1"
                result = self.custom_query_one(query, [button_id])
            else:
                query = "SELECT COUNT(*) as count FROM questions WHERE is_active = 1"
                result = self.custom_query_one(query)
            return result.get('count', 0) if result else 0
        except Exception as e:
            log_database_error(
                f"Error getting question count: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_options_count(self, question_id: int) -> int:
        """تعداد گزینه‌های یک سوال"""
        try:
            query = "SELECT COUNT(*) as count FROM question_options WHERE question_id = ? AND is_active = 1"
            result = self.custom_query_one(query, [question_id])
            return result.get('count', 0) if result else 0
        except Exception as e:
            log_database_error(
                f"Error getting options count for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_conditions_count(self, question_id: int) -> int:
        """تعداد شرط‌های یک سوال"""
        try:
            query = "SELECT COUNT(*) as count FROM question_conditions WHERE question_id = ? AND is_active = 1"
            result = self.custom_query_one(query, [question_id])
            return result.get('count', 0) if result else 0
        except Exception as e:
            log_database_error(
                f"Error getting conditions count for question {question_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_questions_with_options(self, button_id: int) -> List[Dict[str, Any]]:
        """
        دریافت سوالات یک دکمه به همراه گزینه‌هایشان
        """
        try:
            questions = self.get_by_button(button_id)
            result = []
            for q in questions:
                q_dict = dict(q)
                q_dict['options'] = self.get_options(q['id'])
                q_dict['conditions'] = self.get_conditions(q['id'])
                result.append(q_dict)
            return result
        except Exception as e:
            log_database_error(
                f"Error getting questions with options for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_questions_with_conditions(self, button_id: int) -> List[Dict[str, Any]]:
        """
        دریافت سوالات یک دکمه به همراه شرط‌هایشان
        """
        try:
            questions = self.get_by_button(button_id)
            result = []
            for q in questions:
                q_dict = dict(q)
                q_dict['conditions'] = self.get_conditions(q['id'])
                result.append(q_dict)
            return result
        except Exception as e:
            log_database_error(
                f"Error getting questions with conditions for button {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []


__all__ = [
    'QuestionRepository',
]