# dynamic/dynamic_validation.py
# توابع اعتبارسنجی داینامیک

import re
import traceback  # ✅ اضافه شد برای traceback کامل
from database import get_question_by_id, get_conditions_by_question
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


def check_conditional_visibility(question, user_answers):
    """بررسی شرط نمایش سوال (قابلیت conditional_enabled)"""
    try:
        if question.get('conditional_enabled', 0) != 1:
            return True
        
        cond_on = question.get('conditional_on')
        cond_value = question.get('conditional_value')
        
        if not cond_on or cond_value is None:
            return True
        
        ref_question = get_question_by_id(cond_on)
        if not ref_question:
            return True
        
        ref_question_text = ref_question.get('question_text')
        if not ref_question_text:
            return True
        
        user_answer = user_answers.get(ref_question_text)
        if user_answer is None:
            return False
        
        return user_answer == cond_value
    except Exception as e:
        log_database_error(
            f"Error in check_conditional_visibility: {str(e)}",
            traceback=traceback.format_exc()
        )
        return True  # در صورت خطا، سوال نمایش داده شود


def _check_conditions(question, user_answers):
    """بررسی تمام شرط‌های یک سوال بر اساس پاسخ‌های قبلی کاربر"""
    try:
        conditions = get_conditions_by_question(question['id'])
        if not conditions:
            return True
        
        # بررسی شرط نمایش اضافی
        if not check_conditional_visibility(question, user_answers):
            return False
        
        results = []
        for cond in conditions:
            ref_question = get_question_by_id(cond['condition_question_id'])
            if not ref_question:
                results.append(True)
                continue
            
            ref_question_text = ref_question.get('question_text')
            if not ref_question_text:
                results.append(True)
                continue
            
            user_answer = user_answers.get(ref_question_text)
            if user_answer is None:
                results.append(False)
                continue
            
            operator = cond.get('condition_operator')
            condition_value = cond.get('condition_value')
            if not operator or condition_value is None:
                results.append(True)
                continue
            
            try:
                if operator == "==":
                    result = user_answer == condition_value
                elif operator == "!=":
                    result = user_answer != condition_value
                elif operator == "contains":
                    result = condition_value in user_answer
                elif operator == "startswith":
                    result = user_answer.startswith(condition_value)
                elif operator == ">":
                    result = float(user_answer) > float(condition_value)
                elif operator == "<":
                    result = float(user_answer) < float(condition_value)
                elif operator == ">=":
                    result = float(user_answer) >= float(condition_value)
                elif operator == "<=":
                    result = float(user_answer) <= float(condition_value)
                elif operator == "between":
                    parts = condition_value.split(',')
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
    except Exception as e:
        log_database_error(
            f"Error in _check_conditions for question {question.get('id')}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return True  # در صورت خطا، شرط را رد نکنیم


def auto_fix_answer(answer, question):
    """اصلاح خودکار پاسخ بر اساس تنظیمات"""
    try:
        if question.get('auto_fix_enabled', 0) != 1:
            return answer
        
        if isinstance(answer, str):
            answer = ' '.join(answer.split())
            
            persian_to_english = {
                '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
                '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
            }
            for p, e in persian_to_english.items():
                answer = answer.replace(p, e)
        
        return answer
    except Exception as e:
        log_general_error(
            f"Error in auto_fix_answer: {str(e)}",
            traceback=traceback.format_exc()
        )
        return answer  # در صورت خطا، پاسخ اصلی برگردانده شود


def get_validation_error_message(question, error_type):
    """دریافت پیام خطای مناسب بر اساس نوع خطا"""
    try:
        custom_error = question.get('validation_error')
        if custom_error:
            return custom_error
        
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
            'starts_with': f"❌ پاسخ باید با '{question.get('starts_with', '')}' شروع شود.",
            'ends_with': f"❌ پاسخ باید با '{question.get('ends_with', '')}' پایان یابد.",
            'contains': f"❌ پاسخ باید شامل '{question.get('contains', '')}' باشد.",
            'not_contains': f"❌ پاسخ نباید شامل '{question.get('not_contains', '')}' باشد.",
            'forbidden_words': "❌ پاسخ شامل کلمات ممنوع است.",
            'required_words': "❌ پاسخ باید شامل کلمات الزامی باشد.",
            'future_only': "❌ تاریخ باید در آینده باشد.",
            'past_only': "❌ تاریخ باید در گذشته باشد.",
            'weekdays_only': "❌ تاریخ باید روز کاری باشد.",
            'file_format': f"❌ فرمت فایل مجاز نیست. فرمت‌های مجاز: {question.get('allowed_formats', '')}",
            'file_size_max': f"❌ حجم فایل نباید بیشتر از {question.get('max_file_size', 0)} کیلوبایت باشد.",
            'file_size_min': f"❌ حجم فایل نباید کمتر از {question.get('min_file_size', 0)} کیلوبایت باشد.",
            'file_count': f"❌ حداکثر {question.get('max_files', 1)} فایل مجاز است.",
            'dimensions': "❌ ابعاد عکس مناسب نیست.",
            'aspect_ratio': "❌ نسبت تصویر صحیح نیست.",
            'regex': "❌ فرمت پاسخ صحیح نیست.",
            'file': "❌ لطفاً یک فایل انتخاب کنید."
        }
        
        return error_messages.get(error_type, "❌ پاسخ نامعتبر است. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        log_general_error(
            f"Error in get_validation_error_message: {str(e)}",
            traceback=traceback.format_exc()
        )
        return "❌ خطا در اعتبارسنجی. لطفاً دوباره تلاش کنید."


def validate_answer(answer, question):
    """
    اعتبارسنجی کامل پاسخ بر اساس تنظیمات سوال
    بازگشت: (is_valid, error_type, fixed_answer)
    """
    try:
        fixed_answer = auto_fix_answer(answer, question)
        
        if question.get('is_required', 0) == 1:
            if not fixed_answer or (isinstance(fixed_answer, str) and fixed_answer.strip() == ''):
                return False, 'required', fixed_answer
        
        if question.get('validation_enabled', 0) != 1:
            return True, None, fixed_answer
        
        validation_type = question.get('validation_type', 'none')
        
        if validation_type == 'none':
            return True, None, fixed_answer
        
        # اعتبارسنجی متن
        if validation_type == 'text':
            if question.get('length_validation_enabled', 0) == 1:
                min_len = question.get('min_length')
                max_len = question.get('max_length')
                if min_len and len(fixed_answer) < min_len:
                    return False, 'min_length', fixed_answer
                if max_len and len(fixed_answer) > max_len:
                    return False, 'max_length', fixed_answer
            
            if question.get('word_validation_enabled', 0) == 1:
                words = fixed_answer.split()
                min_words = question.get('min_words')
                max_words = question.get('max_words')
                if min_words and len(words) < min_words:
                    return False, 'min_words', fixed_answer
                if max_words and len(words) > max_words:
                    return False, 'max_words', fixed_answer
        
        # اعتبارسنجی عدد
        elif validation_type == 'number':
            try:
                num = int(fixed_answer.replace(',', '').replace(' ', ''))
                if question.get('numeric_validation_enabled', 0) == 1:
                    min_val = question.get('min_value')
                    max_val = question.get('max_value')
                    step = question.get('step')
                    if min_val is not None and num < min_val:
                        return False, 'min_value', fixed_answer
                    if max_val is not None and num > max_val:
                        return False, 'max_value', fixed_answer
                    if step and step > 0 and num % step != 0:
                        return False, 'step', fixed_answer
            except ValueError:
                return False, 'numeric', fixed_answer
        
        # اعتبارسنجی عدد اعشاری
        elif validation_type == 'decimal':
            try:
                num = float(fixed_answer.replace(',', '').replace(' ', ''))
                if question.get('numeric_validation_enabled', 0) == 1:
                    min_val = question.get('min_value')
                    max_val = question.get('max_value')
                    if min_val is not None and num < min_val:
                        return False, 'min_value', fixed_answer
                    if max_val is not None and num > max_val:
                        return False, 'max_value', fixed_answer
            except ValueError:
                return False, 'decimal', fixed_answer
        
        # اعتبارسنجی کد ملی
        elif validation_type == 'national_code':
            if not fixed_answer.isdigit() or len(fixed_answer) != 10:
                return False, 'national_code', fixed_answer
            if fixed_answer in ['0000000000', '1111111111', '2222222222', '3333333333', 
                               '4444444444', '5555555555', '6666666666', '7777777777', 
                               '8888888888', '9999999999']:
                return False, 'national_code', fixed_answer
        
        # اعتبارسنجی تلفن همراه
        elif validation_type == 'phone':
            if not fixed_answer.isdigit() or len(fixed_answer) != 11 or not fixed_answer.startswith('09'):
                return False, 'phone', fixed_answer
        
        # اعتبارسنجی تلفن ثابت
        elif validation_type == 'phone_landline':
            if not fixed_answer.isdigit() or len(fixed_answer) not in [10, 11]:
                return False, 'phone_landline', fixed_answer
        
        # اعتبارسنجی کدپستی
        elif validation_type == 'postal_code':
            if not fixed_answer.isdigit() or len(fixed_answer) != 10:
                return False, 'postal_code', fixed_answer
        
        # اعتبارسنجی پلاک
        elif validation_type == 'plate':
            pattern = r'^\d{3}-\d{3}-\d{2}$'
            if not re.match(pattern, fixed_answer):
                return False, 'plate', fixed_answer
        
        # اعتبارسنجی شبا
        elif validation_type == 'iban':
            if not fixed_answer.startswith('IR') or len(fixed_answer) < 24 or len(fixed_answer) > 26:
                return False, 'iban', fixed_answer
        
        # اعتبارسنجی شماره کارت
        elif validation_type == 'card_number':
            if not fixed_answer.isdigit() or len(fixed_answer) != 16:
                return False, 'card_number', fixed_answer
            try:
                total = 0
                for i, digit in enumerate(reversed(fixed_answer)):
                    n = int(digit)
                    if i % 2 == 1:
                        n *= 2
                        if n > 9:
                            n -= 9
                    total += n
                if total % 10 != 0:
                    return False, 'card_number', fixed_answer
            except Exception:
                return False, 'card_number', fixed_answer
        
        # اعتبارسنجی ایمیل
        elif validation_type == 'email':
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, fixed_answer):
                return False, 'email', fixed_answer
        
        # اعتبارسنجی URL
        elif validation_type == 'url':
            pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
            if not re.match(pattern, fixed_answer):
                return False, 'url', fixed_answer
        
        # اعتبارسنجی تاریخ شمسی
        elif validation_type == 'date':
            pattern = r'^\d{4}/\d{2}/\d{2}$'
            if not re.match(pattern, fixed_answer):
                return False, 'date', fixed_answer
            if question.get('date_validation_enabled', 0) == 1:
                min_date = question.get('min_date')
                max_date = question.get('max_date')
                if min_date and fixed_answer < min_date:
                    return False, 'min_date', fixed_answer
                if max_date and fixed_answer > max_date:
                    return False, 'max_date', fixed_answer
        
        # اعتبارسنجی تاریخ میلادی
        elif validation_type == 'date_gregorian':
            pattern = r'^\d{4}/\d{2}/\d{2}$'
            if not re.match(pattern, fixed_answer):
                return False, 'date_gregorian', fixed_answer
        
        # اعتبارسنجی زمان
        elif validation_type == 'time':
            pattern = r'^\d{2}:\d{2}$'
            if not re.match(pattern, fixed_answer):
                return False, 'time', fixed_answer
            try:
                h, m = fixed_answer.split(':')
                if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
                    return False, 'time', fixed_answer
            except Exception:
                return False, 'time', fixed_answer
        
        # اعتبارسنجی تاریخ و زمان
        elif validation_type == 'datetime':
            pattern = r'^\d{4}/\d{2}/\d{2} \d{2}:\d{2}$'
            if not re.match(pattern, fixed_answer):
                return False, 'datetime', fixed_answer
        
        # اعتبارسنجی متن فارسی
        elif validation_type == 'persian_text':
            pattern = r'^[\u0600-\u06FF\s]+$'
            if not re.match(pattern, fixed_answer):
                return False, 'persian_text', fixed_answer
        
        # اعتبارسنجی متن انگلیسی
        elif validation_type == 'english_text':
            pattern = r'^[a-zA-Z\s]+$'
            if not re.match(pattern, fixed_answer):
                return False, 'english_text', fixed_answer
        
        # اعتبارسنجی حروف و اعداد
        elif validation_type == 'alphanumeric':
            pattern = r'^[a-zA-Z0-9\s]+$'
            if not re.match(pattern, fixed_answer):
                return False, 'alphanumeric', fixed_answer
        
        # اعتبارسنجی شروع با
        if question.get('pattern_validation_enabled', 0) == 1:
            starts_with = question.get('starts_with')
            ends_with = question.get('ends_with')
            regex_pattern = question.get('regex_pattern')
            
            if starts_with and not fixed_answer.startswith(starts_with):
                return False, 'starts_with', fixed_answer
            if ends_with and not fixed_answer.endswith(ends_with):
                return False, 'ends_with', fixed_answer
            if regex_pattern:
                try:
                    if not re.match(regex_pattern, fixed_answer):
                        return False, 'regex', fixed_answer
                except re.error:
                    pass
        
        # اعتبارسنجی محتوا
        if question.get('contains_validation_enabled', 0) == 1:
            contains = question.get('contains')
            not_contains = question.get('not_contains')
            forbidden_words = question.get('forbidden_words')
            required_words = question.get('required_words')
            
            if contains and contains not in fixed_answer:
                return False, 'contains', fixed_answer
            if not_contains and not_contains in fixed_answer:
                return False, 'not_contains', fixed_answer
            if forbidden_words:
                for word in forbidden_words.split(','):
                    if word.strip() in fixed_answer:
                        return False, 'forbidden_words', fixed_answer
            if required_words:
                found = True
                for word in required_words.split(','):
                    if word.strip() not in fixed_answer:
                        found = False
                        break
                if not found:
                    return False, 'required_words', fixed_answer
        
        return True, None, fixed_answer
    except Exception as e:
        log_general_error(
            f"Error in validate_answer: {str(e)}",
            traceback=traceback.format_exc()
        )
        # در صورت خطا، پاسخ قبول شود اما خطا لاگ شود
        return True, None, answer