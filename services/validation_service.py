# services/validation_service.py
# سرویس مدیریت اعتبارسنجی - منطق کسب‌وکار مربوط به اعتبارسنجی ورودی‌ها
# شامل: اعتبارسنجی انواع مختلف داده‌ها، اصلاح خودکار، بررسی شرط‌ها

import re
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
from logger_config import logger
from repositories import QuestionRepository
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class ValidationService:
    """سرویس مدیریت اعتبارسنجی - اعتبارسنجی پاسخ‌های کاربران"""
    
    def __init__(self, connection, repository: Optional[QuestionRepository] = None):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            repository: ریپازیتوری سوالات (اختیاری)
        """
        self._connection = connection
        self._repository = repository or QuestionRepository(connection)
    
    # ============================================================
    # اعتبارسنجی اصلی
    # ============================================================
    
    def validate_answer(self, answer: Any, question: Dict) -> Tuple[bool, Optional[str], Any]:
        """
        اعتبارسنجی کامل پاسخ بر اساس تنظیمات سوال
        
        پارامترها:
            answer: پاسخ کاربر
            question: دیکشنری سوال با تنظیمات اعتبارسنجی
        
        بازگشت: (is_valid, error_type, fixed_answer)
        """
        # اصلاح خودکار
        fixed_answer = self.auto_fix(answer, question)
        
        # بررسی اجباری بودن
        if question.get('is_required', 0) == 1:
            if not fixed_answer or (isinstance(fixed_answer, str) and fixed_answer.strip() == ''):
                return False, 'required', fixed_answer
        
        # اگر اعتبارسنجی غیرفعال است
        if question.get('validation_enabled', 0) != 1:
            return True, None, fixed_answer
        
        validation_type = question.get('validation_type', 'none')
        
        # اعتبارسنجی بر اساس نوع
        if validation_type == 'none':
            return True, None, fixed_answer
        
        # ========== اعتبارسنجی متن ==========
        if validation_type == 'text':
            return self._validate_text(fixed_answer, question)
        
        # ========== اعتبارسنجی عدد ==========
        elif validation_type == 'number':
            return self._validate_number(fixed_answer, question)
        
        # ========== اعتبارسنجی عدد اعشاری ==========
        elif validation_type == 'decimal':
            return self._validate_decimal(fixed_answer, question)
        
        # ========== اعتبارسنجی کد ملی ==========
        elif validation_type == 'national_code':
            return self._validate_national_code(fixed_answer, question)
        
        # ========== اعتبارسنجی تلفن همراه ==========
        elif validation_type == 'phone':
            return self._validate_phone(fixed_answer, question)
        
        # ========== اعتبارسنجی تلفن ثابت ==========
        elif validation_type == 'phone_landline':
            return self._validate_phone_landline(fixed_answer, question)
        
        # ========== اعتبارسنجی کدپستی ==========
        elif validation_type == 'postal_code':
            return self._validate_postal_code(fixed_answer, question)
        
        # ========== اعتبارسنجی پلاک خودرو ==========
        elif validation_type == 'plate':
            return self._validate_plate(fixed_answer, question)
        
        # ========== اعتبارسنجی شبا ==========
        elif validation_type == 'iban':
            return self._validate_iban(fixed_answer, question)
        
        # ========== اعتبارسنجی شماره کارت ==========
        elif validation_type == 'card_number':
            return self._validate_card_number(fixed_answer, question)
        
        # ========== اعتبارسنجی ایمیل ==========
        elif validation_type == 'email':
            return self._validate_email(fixed_answer, question)
        
        # ========== اعتبارسنجی URL ==========
        elif validation_type == 'url':
            return self._validate_url(fixed_answer, question)
        
        # ========== اعتبارسنجی تاریخ شمسی ==========
        elif validation_type == 'date':
            return self._validate_date(fixed_answer, question)
        
        # ========== اعتبارسنجی تاریخ میلادی ==========
        elif validation_type == 'date_gregorian':
            return self._validate_date_gregorian(fixed_answer, question)
        
        # ========== اعتبارسنجی زمان ==========
        elif validation_type == 'time':
            return self._validate_time(fixed_answer, question)
        
        # ========== اعتبارسنجی تاریخ و زمان ==========
        elif validation_type == 'datetime':
            return self._validate_datetime(fixed_answer, question)
        
        # ========== اعتبارسنجی متن فارسی ==========
        elif validation_type == 'persian_text':
            return self._validate_persian_text(fixed_answer, question)
        
        # ========== اعتبارسنجی متن انگلیسی ==========
        elif validation_type == 'english_text':
            return self._validate_english_text(fixed_answer, question)
        
        # ========== اعتبارسنجی حروف و اعداد ==========
        elif validation_type == 'alphanumeric':
            return self._validate_alphanumeric(fixed_answer, question)
        
        # ========== اعتبارسنجی فایل ==========
        elif validation_type in ['file', 'image', 'document']:
            return self._validate_file(fixed_answer, question)
        
        # نوع نامعتبر
        return True, None, fixed_answer
    
    # ============================================================
    # اعتبارسنجی‌های خاص
    # ============================================================
    
    def _validate_text(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی متن"""
        if not isinstance(value, str):
            return False, 'invalid_type', value
        
        # محدودیت طول
        if question.get('length_validation_enabled', 0) == 1:
            min_len = question.get('min_length')
            max_len = question.get('max_length')
            
            if min_len and len(value) < min_len:
                return False, 'min_length', value
            if max_len and len(value) > max_len:
                return False, 'max_length', value
        
        # محدودیت کلمه
        if question.get('word_validation_enabled', 0) == 1:
            words = value.split()
            min_words = question.get('min_words')
            max_words = question.get('max_words')
            
            if min_words and len(words) < min_words:
                return False, 'min_words', value
            if max_words and len(words) > max_words:
                return False, 'max_words', value
        
        return True, None, value
    
    def _validate_number(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی عدد"""
        try:
            num = int(str(value).replace(',', '').replace(' ', ''))
        except ValueError:
            return False, 'numeric', value
        
        if question.get('numeric_validation_enabled', 0) == 1:
            min_val = question.get('min_value')
            max_val = question.get('max_value')
            step = question.get('step')
            
            if min_val is not None and num < min_val:
                return False, 'min_value', value
            if max_val is not None and num > max_val:
                return False, 'max_value', value
            if step and step > 0 and num % step != 0:
                return False, 'step', value
        
        return True, None, value
    
    def _validate_decimal(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی عدد اعشاری"""
        try:
            num = float(str(value).replace(',', '').replace(' ', ''))
        except ValueError:
            return False, 'decimal', value
        
        if question.get('numeric_validation_enabled', 0) == 1:
            min_val = question.get('min_value')
            max_val = question.get('max_value')
            
            if min_val is not None and num < min_val:
                return False, 'min_value', value
            if max_val is not None and num > max_val:
                return False, 'max_value', value
        
        return True, None, value
    
    def _validate_national_code(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی کد ملی"""
        value = str(value).strip()
        
        if not value.isdigit() or len(value) != 10:
            return False, 'national_code', value
        
        # کدهای ملی نامعتبر
        invalid_codes = [
            '0000000000', '1111111111', '2222222222', '3333333333',
            '4444444444', '5555555555', '6666666666', '7777777777',
            '8888888888', '9999999999'
        ]
        if value in invalid_codes:
            return False, 'national_code', value
        
        # الگوریتم اعتبارسنجی کد ملی
        check = int(value[9])
        sum_val = sum(int(value[i]) * (10 - i) for i in range(9)) % 11
        
        if sum_val < 2:
            is_valid = check == sum_val
        else:
            is_valid = check == 11 - sum_val
        
        if not is_valid:
            return False, 'national_code', value
        
        return True, None, value
    
    def _validate_phone(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی تلفن همراه"""
        value = str(value).strip()
        
        if not value.isdigit() or len(value) != 11 or not value.startswith('09'):
            return False, 'phone', value
        
        return True, None, value
    
    def _validate_phone_landline(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی تلفن ثابت"""
        value = str(value).strip()
        
        if not value.isdigit() or len(value) not in [10, 11]:
            return False, 'phone_landline', value
        
        return True, None, value
    
    def _validate_postal_code(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی کدپستی"""
        value = str(value).strip()
        
        if not value.isdigit() or len(value) != 10:
            return False, 'postal_code', value
        
        return True, None, value
    
    def _validate_plate(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی پلاک خودرو"""
        pattern = r'^\d{2,3}-\d{2,3}-\d{2}$'
        if not re.match(pattern, str(value).strip()):
            return False, 'plate', value
        
        return True, None, value
    
    def _validate_iban(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی شبا"""
        value = str(value).strip().upper()
        
        if not value.startswith('IR') or len(value) < 24 or len(value) > 26:
            return False, 'iban', value
        
        return True, None, value
    
    def _validate_card_number(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی شماره کارت (الگوریتم Luhn)"""
        value = str(value).strip()
        
        if not value.isdigit() or len(value) != 16:
            return False, 'card_number', value
        
        # الگوریتم Luhn
        total = 0
        for i, digit in enumerate(reversed(value)):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        if total % 10 != 0:
            return False, 'card_number', value
        
        return True, None, value
    
    def _validate_email(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی ایمیل"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, str(value).strip()):
            return False, 'email', value
        
        return True, None, value
    
    def _validate_url(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی URL"""
        pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        if not re.match(pattern, str(value).strip()):
            return False, 'url', value
        
        return True, None, value
    
    def _validate_date(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی تاریخ شمسی"""
        pattern = r'^\d{4}/\d{2}/\d{2}$'
        if not re.match(pattern, str(value).strip()):
            return False, 'date', value
        
        if question.get('date_validation_enabled', 0) == 1:
            min_date = question.get('min_date')
            max_date = question.get('max_date')
            
            if min_date and value < min_date:
                return False, 'min_date', value
            if max_date and value > max_date:
                return False, 'max_date', value
        
        return True, None, value
    
    def _validate_date_gregorian(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی تاریخ میلادی"""
        pattern = r'^\d{4}/\d{2}/\d{2}$'
        if not re.match(pattern, str(value).strip()):
            return False, 'date_gregorian', value
        
        return True, None, value
    
    def _validate_time(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی زمان"""
        pattern = r'^\d{2}:\d{2}$'
        if not re.match(pattern, str(value).strip()):
            return False, 'time', value
        
        try:
            h, m = value.split(':')
            if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
                return False, 'time', value
        except:
            return False, 'time', value
        
        return True, None, value
    
    def _validate_datetime(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی تاریخ و زمان"""
        pattern = r'^\d{4}/\d{2}/\d{2} \d{2}:\d{2}$'
        if not re.match(pattern, str(value).strip()):
            return False, 'datetime', value
        
        return True, None, value
    
    def _validate_persian_text(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی متن فارسی"""
        pattern = r'^[\u0600-\u06FF\s]+$'
        if not re.match(pattern, str(value).strip()):
            return False, 'persian_text', value
        
        return True, None, value
    
    def _validate_english_text(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی متن انگلیسی"""
        pattern = r'^[a-zA-Z\s]+$'
        if not re.match(pattern, str(value).strip()):
            return False, 'english_text', value
        
        return True, None, value
    
    def _validate_alphanumeric(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """اعتبارسنجی حروف و اعداد"""
        pattern = r'^[a-zA-Z0-9\s]+$'
        if not re.match(pattern, str(value).strip()):
            return False, 'alphanumeric', value
        
        return True, None, value
    
    def _validate_file(self, value: str, question: Dict) -> Tuple[bool, Optional[str], str]:
        """
        اعتبارسنجی فایل (برای فایل‌های ارسالی)
        این تابع بررسی‌های اولیه را انجام می‌دهد، اعتبارسنجی دقیق‌تر در dynamic_validation انجام می‌شود
        """
        # اگر مقدار رشته است و با [فایل: شروع می‌شود، معتبر است
        if isinstance(value, str) and value.startswith('[فایل:'):
            return True, None, value
        
        # اگر فایل آپلود شده باشد، نوع آن باید dict باشد
        if isinstance(value, dict):
            return True, None, value
        
        return False, 'file', value
    
    # ============================================================
    # اصلاح خودکار
    # ============================================================
    
    def auto_fix(self, answer: Any, question: Dict) -> Any:
        """
        اصلاح خودکار پاسخ بر اساس تنظیمات
        
        پارامترها:
            answer: پاسخ کاربر
            question: دیکشنری سوال
        
        بازگشت: پاسخ اصلاح‌شده
        """
        if question.get('auto_fix_enabled', 0) != 1:
            return answer
        
        if isinstance(answer, str):
            # حذف فاصله‌های اضافی
            answer = ' '.join(answer.split())
            
            # تبدیل اعداد فارسی به انگلیسی
            persian_to_english = {
                '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
            }
            for p, e in persian_to_english.items():
                answer = answer.replace(p, e)
        
        return answer
    
    # ============================================================
    # شرط‌های نمایش
    # ============================================================
    
    def check_conditional_visibility(self, question: Dict, user_answers: Dict) -> bool:
        """
        بررسی شرط نمایش سوال
        
        پارامترها:
            question: دیکشنری سوال
            user_answers: پاسخ‌های قبلی کاربر
        
        بازگشت: True اگر سوال باید نمایش داده شود
        """
        if question.get('conditional_enabled', 0) != 1:
            return True
        
        cond_on = question.get('conditional_on')
        cond_value = question.get('conditional_value')
        
        if not cond_on or cond_value is None:
            return True
        
        # دریافت سوال مرجع
        ref_question = self._repository.get_by_id(cond_on)
        if not ref_question:
            return True
        
        ref_text = ref_question.get('question_text')
        if not ref_text:
            return True
        
        # بررسی پاسخ کاربر
        user_answer = user_answers.get(ref_text)
        if user_answer is None:
            return False
        
        return str(user_answer) == str(cond_value)
    
    def check_conditions(self, question: Dict, user_answers: Dict) -> bool:
        """
        بررسی تمام شرط‌های یک سوال
        
        پارامترها:
            question: دیکشنری سوال
            user_answers: پاسخ‌های قبلی کاربر
        
        بازگشت: True اگر همه شرط‌ها برقرار باشند
        """
        # بررسی شرط نمایش
        if not self.check_conditional_visibility(question, user_answers):
            return False
        
        # دریافت شرط‌های اضافی از دیتابیس
        conditions = self._repository.get_conditions(question['id'])
        if not conditions:
            return True
        
        results = []
        for cond in conditions:
            ref_question = self._repository.get_by_id(cond['condition_question_id'])
            if not ref_question:
                results.append(True)
                continue
            
            ref_text = ref_question.get('question_text')
            if not ref_text:
                results.append(True)
                continue
            
            user_answer = user_answers.get(ref_text)
            if user_answer is None:
                results.append(False)
                continue
            
            operator = cond.get('condition_operator')
            cond_value = cond.get('condition_value')
            
            if not operator or cond_value is None:
                results.append(True)
                continue
            
            try:
                if operator == "==":
                    result = str(user_answer) == str(cond_value)
                elif operator == "!=":
                    result = str(user_answer) != str(cond_value)
                elif operator == "contains":
                    result = cond_value.lower() in str(user_answer).lower()
                elif operator == "startswith":
                    result = str(user_answer).startswith(cond_value)
                elif operator == ">":
                    result = float(user_answer) > float(cond_value)
                elif operator == "<":
                    result = float(user_answer) < float(cond_value)
                elif operator == ">=":
                    result = float(user_answer) >= float(cond_value)
                elif operator == "<=":
                    result = float(user_answer) <= float(cond_value)
                elif operator == "between":
                    parts = cond_value.split(',')
                    if len(parts) == 2:
                        result = float(parts[0]) <= float(user_answer) <= float(parts[1])
                    else:
                        result = False
                else:
                    result = True
            except (ValueError, TypeError):
                result = False
            
            results.append(result)
        
        if not results:
            return True
        
        # ترکیب نتایج با منطق AND/OR
        if len(results) == 1:
            return results[0]
        
        final_result = results[0]
        for i, cond in enumerate(conditions[:-1]):
            logic = cond.get('logic_operator', 'AND')
            if logic == "AND":
                final_result = final_result and results[i+1]
            elif logic == "OR":
                final_result = final_result or results[i+1]
            else:
                final_result = final_result and results[i+1]
        
        return final_result
    
    # ============================================================
    # دریافت پیام خطا
    # ============================================================
    
    def get_error_message(self, question: Dict, error_type: str) -> str:
        """
        دریافت پیام خطای مناسب بر اساس نوع خطا
        
        پارامترها:
            question: دیکشنری سوال
            error_type: نوع خطا
        
        بازگشت: پیام خطا
        """
        # پیام خطای سفارشی
        custom_error = question.get('validation_error')
        if custom_error:
            return custom_error
        
        # پیام‌های خطای پیش‌فرض
        error_messages = {
            'required': "❌ این سوال اجباری است. لطفاً پاسخ دهید.",
            'min_length': f"❌ حداقل طول {question.get('min_length', 0)} کاراکتر است.",
            'max_length': f"❌ حداکثر طول {question.get('max_length', 0)} کاراکتر است.",
            'min_words': f"❌ حداقل {question.get('min_words', 0)} کلمه وارد کنید.",
            'max_words': f"❌ حداکثر {question.get('max_words', 0)} کلمه وارد کنید.",
            'min_value': f"❌ حداقل مقدار {question.get('min_value', 0)} است.",
            'max_value': f"❌ حداکثر مقدار {question.get('max_value', 0)} است.",
            'step': f"❌ مقدار باید مضربی از {question.get('step', 1)} باشد.",
            'numeric': "❌ لطفاً یک عدد معتبر وارد کنید.",
            'decimal': "❌ لطفاً یک عدد اعشاری معتبر وارد کنید.",
            'national_code': "❌ کد ملی باید ۱۰ رقم معتبر باشد.",
            'phone': "❌ شماره تلفن باید ۱۱ رقم و با ۰۹ شروع شود.",
            'phone_landline': "❌ شماره تلفن ثابت را به درستی وارد کنید.",
            'postal_code': "❌ کدپستی باید ۱۰ رقم باشد.",
            'plate': "❌ فرمت پلاک را به درستی وارد کنید (مثال: ۱۲۳-۴۵۶-۷۸).",
            'iban': "❌ شماره شبا معتبر نیست.",
            'card_number': "❌ شماره کارت باید ۱۶ رقم معتبر باشد.",
            'email': "❌ لطفاً یک ایمیل معتبر وارد کنید.",
            'url': "❌ لطفاً یک آدرس معتبر وارد کنید.",
            'date': "❌ تاریخ را به درستی وارد کنید (مثال: ۱۴۰۳/۰۱/۱۵).",
            'date_gregorian': "❌ تاریخ میلادی را به درستی وارد کنید (مثال: 2024/01/15).",
            'time': "❌ زمان را به درستی وارد کنید (مثال: ۱۴:۳۰).",
            'datetime': "❌ تاریخ و زمان را به درستی وارد کنید.",
            'persian_text': "❌ لطفاً فقط از حروف فارسی استفاده کنید.",
            'english_text': "❌ لطفاً فقط از حروف انگلیسی استفاده کنید.",
            'alphanumeric': "❌ لطفاً فقط از حروف و اعداد استفاده کنید.",
            'min_date': f"❌ تاریخ نباید قبل از {question.get('min_date', '')} باشد.",
            'max_date': f"❌ تاریخ نباید بعد از {question.get('max_date', '')} باشد.",
            'file': "❌ لطفاً یک فایل انتخاب کنید.",
            'invalid_type': "❌ نوع پاسخ نامعتبر است.",
        }
        
        return error_messages.get(error_type, "❌ پاسخ نامعتبر است. لطفاً دوباره تلاش کنید.")
    
    # ============================================================
    # ابزارهای کمکی
    # ============================================================
    
    def get_validation_rules(self, question_id: int) -> Dict:
        """دریافت قوانین اعتبارسنجی یک سوال"""
        return self._repository.get_validation_settings(question_id)
    
    def get_validation_summary(self, question_id: int) -> Dict:
        """دریافت خلاصه وضعیت اعتبارسنجی یک سوال"""
        return self._repository.get_validation_summary(question_id)
    
    def is_answer_valid(self, answer: Any, question_id: int) -> Tuple[bool, Optional[str], Any]:
        """
        بررسی اعتبار پاسخ بر اساس شناسه سوال
        
        پارامترها:
            answer: پاسخ کاربر
            question_id: شناسه سوال
        
        بازگشت: (is_valid, error_type, fixed_answer)
        """
        question = self._repository.get_by_id(question_id)
        if not question:
            return False, 'question_not_found', answer
        
        return self.validate_answer(answer, question)


__all__ = [
    'ValidationService',
]