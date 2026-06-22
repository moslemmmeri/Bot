# tests/test_dynamic/test_validation.py
# تست‌های واحد برای اعتبارسنجی داینامیک (dynamic_validation.py)

import pytest
from unittest.mock import MagicMock, patch

from dynamic.dynamic_validation import (
    check_conditional_visibility,
    _check_conditions,
    auto_fix_answer,
    get_validation_error_message,
    validate_answer,
)


class TestDynamicValidation:
    """تست‌های اعتبارسنجی داینامیک"""

    # ============================================================
    # تست‌های check_conditional_visibility
    # ============================================================

    def test_check_conditional_visibility_disabled(self):
        """تست بررسی شرط نمایش وقتی شرط غیرفعال است"""
        question = {
            'id': 1,
            'conditional_enabled': 0,
            'conditional_on': None,
            'conditional_value': None,
        }
        user_answers = {}
        
        result = check_conditional_visibility(question, user_answers)
        assert result is True

    def test_check_conditional_visibility_no_condition(self):
        """تست بررسی شرط نمایش وقتی شرط تعریف نشده است"""
        question = {
            'id': 1,
            'conditional_enabled': 1,
            'conditional_on': None,
            'conditional_value': None,
        }
        user_answers = {}
        
        result = check_conditional_visibility(question, user_answers)
        assert result is True

    def test_check_conditional_visibility_ref_question_not_found(self):
        """تست بررسی شرط نمایش وقتی سوال مرجع وجود ندارد"""
        question = {
            'id': 1,
            'conditional_enabled': 1,
            'conditional_on': 999,
            'conditional_value': 'بله',
        }
        user_answers = {}
        
        with patch('dynamic.dynamic_validation.get_question_by_id', return_value=None):
            result = check_conditional_visibility(question, user_answers)
            assert result is True

    def test_check_conditional_visibility_ref_question_no_text(self):
        """تست بررسی شرط نمایش وقتی سوال مرجع متن ندارد"""
        question = {
            'id': 1,
            'conditional_enabled': 1,
            'conditional_on': 1,
            'conditional_value': 'بله',
        }
        user_answers = {}
        ref_question = {'id': 1, 'question_text': None}
        
        with patch('dynamic.dynamic_validation.get_question_by_id', return_value=ref_question):
            result = check_conditional_visibility(question, user_answers)
            assert result is True

    def test_check_conditional_visibility_user_answer_missing(self):
        """تست بررسی شرط نمایش وقتی پاسخ کاربر وجود ندارد"""
        question = {
            'id': 1,
            'conditional_enabled': 1,
            'conditional_on': 1,
            'conditional_value': 'بله',
        }
        user_answers = {}
        ref_question = {'id': 1, 'question_text': 'سوال مرجع'}
        
        with patch('dynamic.dynamic_validation.get_question_by_id', return_value=ref_question):
            result = check_conditional_visibility(question, user_answers)
            assert result is False

    def test_check_conditional_visibility_matches(self):
        """تست بررسی شرط نمایش وقتی پاسخ مطابق شرط است"""
        question = {
            'id': 1,
            'conditional_enabled': 1,
            'conditional_on': 1,
            'conditional_value': 'بله',
        }
        user_answers = {'سوال مرجع': 'بله'}
        ref_question = {'id': 1, 'question_text': 'سوال مرجع'}
        
        with patch('dynamic.dynamic_validation.get_question_by_id', return_value=ref_question):
            result = check_conditional_visibility(question, user_answers)
            assert result is True

    def test_check_conditional_visibility_not_match(self):
        """تست بررسی شرط نمایش وقتی پاسخ مطابق شرط نیست"""
        question = {
            'id': 1,
            'conditional_enabled': 1,
            'conditional_on': 1,
            'conditional_value': 'بله',
        }
        user_answers = {'سوال مرجع': 'خیر'}
        ref_question = {'id': 1, 'question_text': 'سوال مرجع'}
        
        with patch('dynamic.dynamic_validation.get_question_by_id', return_value=ref_question):
            result = check_conditional_visibility(question, user_answers)
            assert result is False

    # ============================================================
    # تست‌های _check_conditions
    # ============================================================

    def test_check_conditions_no_conditions(self):
        """تست بررسی شرط‌ها وقتی شرطی وجود ندارد"""
        question = {'id': 1}
        user_answers = {}
        
        with patch('dynamic.dynamic_validation.get_conditions_by_question', return_value=[]):
            result = _check_conditions(question, user_answers)
            assert result is True

    def test_check_conditions_with_conditions(self):
        """تست بررسی شرط‌ها با شرط‌های موجود"""
        question = {'id': 1}
        user_answers = {'سوال مرجع': 'بله'}
        conditions = [
            {
                'condition_question_id': 1,
                'condition_operator': '==',
                'condition_value': 'بله',
                'logic_operator': 'AND',
            }
        ]
        ref_question = {'id': 1, 'question_text': 'سوال مرجع'}
        
        with patch('dynamic.dynamic_validation.get_conditions_by_question', return_value=conditions):
            with patch('dynamic.dynamic_validation.get_question_by_id', return_value=ref_question):
                result = _check_conditions(question, user_answers)
                assert result is True

    def test_check_conditions_with_operator_contains(self):
        """تست بررسی شرط با عملگر contains"""
        question = {'id': 1}
        user_answers = {'سوال مرجع': 'این یک پاسخ نمونه است'}
        conditions = [
            {
                'condition_question_id': 1,
                'condition_operator': 'contains',
                'condition_value': 'پاسخ',
                'logic_operator': 'AND',
            }
        ]
        ref_question = {'id': 1, 'question_text': 'سوال مرجع'}
        
        with patch('dynamic.dynamic_validation.get_conditions_by_question', return_value=conditions):
            with patch('dynamic.dynamic_validation.get_question_by_id', return_value=ref_question):
                result = _check_conditions(question, user_answers)
                assert result is True

    def test_check_conditions_with_operator_greater_than(self):
        """تست بررسی شرط با عملگر > (بزرگتر از)"""
        question = {'id': 1}
        user_answers = {'سوال مرجع': '25'}
        conditions = [
            {
                'condition_question_id': 1,
                'condition_operator': '>',
                'condition_value': '18',
                'logic_operator': 'AND',
            }
        ]
        ref_question = {'id': 1, 'question_text': 'سوال مرجع'}
        
        with patch('dynamic.dynamic_validation.get_conditions_by_question', return_value=conditions):
            with patch('dynamic.dynamic_validation.get_question_by_id', return_value=ref_question):
                result = _check_conditions(question, user_answers)
                assert result is True

    def test_check_conditions_with_operator_less_than(self):
        """تست بررسی شرط با عملگر < (کوچکتر از)"""
        question = {'id': 1}
        user_answers = {'سوال مرجع': '15'}
        conditions = [
            {
                'condition_question_id': 1,
                'condition_operator': '<',
                'condition_value': '18',
                'logic_operator': 'AND',
            }
        ]
        ref_question = {'id': 1, 'question_text': 'سوال مرجع'}
        
        with patch('dynamic.dynamic_validation.get_conditions_by_question', return_value=conditions):
            with patch('dynamic.dynamic_validation.get_question_by_id', return_value=ref_question):
                result = _check_conditions(question, user_answers)
                assert result is True

    def test_check_conditions_with_multiple_conditions_and(self):
        """تست بررسی شرط‌های چندگانه با منطق AND"""
        question = {'id': 1}
        user_answers = {'سوال مرجع ۱': 'بله', 'سوال مرجع ۲': 'بله'}
        conditions = [
            {
                'condition_question_id': 1,
                'condition_operator': '==',
                'condition_value': 'بله',
                'logic_operator': 'AND',
            },
            {
                'condition_question_id': 2,
                'condition_operator': '==',
                'condition_value': 'بله',
                'logic_operator': 'AND',
            }
        ]
        
        def mock_get_question(q_id):
            if q_id == 1:
                return {'id': 1, 'question_text': 'سوال مرجع ۱'}
            return {'id': 2, 'question_text': 'سوال مرجع ۲'}
        
        with patch('dynamic.dynamic_validation.get_conditions_by_question', return_value=conditions):
            with patch('dynamic.dynamic_validation.get_question_by_id', side_effect=mock_get_question):
                result = _check_conditions(question, user_answers)
                assert result is True

    def test_check_conditions_with_multiple_conditions_or(self):
        """تست بررسی شرط‌های چندگانه با منطق OR"""
        question = {'id': 1}
        user_answers = {'سوال مرجع ۱': 'خیر', 'سوال مرجع ۲': 'بله'}
        conditions = [
            {
                'condition_question_id': 1,
                'condition_operator': '==',
                'condition_value': 'بله',
                'logic_operator': 'OR',
            },
            {
                'condition_question_id': 2,
                'condition_operator': '==',
                'condition_value': 'بله',
                'logic_operator': 'OR',
            }
        ]
        
        def mock_get_question(q_id):
            if q_id == 1:
                return {'id': 1, 'question_text': 'سوال مرجع ۱'}
            return {'id': 2, 'question_text': 'سوال مرجع ۲'}
        
        with patch('dynamic.dynamic_validation.get_conditions_by_question', return_value=conditions):
            with patch('dynamic.dynamic_validation.get_question_by_id', side_effect=mock_get_question):
                result = _check_conditions(question, user_answers)
                assert result is True

    def test_check_conditions_with_between_operator(self):
        """تست بررسی شرط با عملگر between"""
        question = {'id': 1}
        user_answers = {'سوال مرجع': '25'}
        conditions = [
            {
                'condition_question_id': 1,
                'condition_operator': 'between',
                'condition_value': '18,30',
                'logic_operator': 'AND',
            }
        ]
        ref_question = {'id': 1, 'question_text': 'سوال مرجع'}
        
        with patch('dynamic.dynamic_validation.get_conditions_by_question', return_value=conditions):
            with patch('dynamic.dynamic_validation.get_question_by_id', return_value=ref_question):
                result = _check_conditions(question, user_answers)
                assert result is True

    # ============================================================
    # تست‌های auto_fix_answer
    # ============================================================

    def test_auto_fix_answer_disabled(self):
        """تست اصلاح خودکار وقتی غیرفعال است"""
        question = {'auto_fix_enabled': 0}
        answer = '  متن با فاصله  '
        
        result = auto_fix_answer(answer, question)
        assert result == '  متن با فاصله  '

    def test_auto_fix_answer_trim_spaces(self):
        """تست اصلاح خودکار - حذف فضاهای اضافی"""
        question = {'auto_fix_enabled': 1}
        answer = '  متن با فاصله  '
        
        result = auto_fix_answer(answer, question)
        assert result == 'متن با فاصله'

    def test_auto_fix_answer_persian_to_english(self):
        """تست اصلاح خودکار - تبدیل اعداد فارسی به انگلیسی"""
        question = {'auto_fix_enabled': 1}
        answer = '۱۲۳۴۵۶'
        
        result = auto_fix_answer(answer, question)
        assert result == '123456'

    def test_auto_fix_answer_mixed(self):
        """تست اصلاح خودکار - ترکیب حذف فاصله و تبدیل اعداد"""
        question = {'auto_fix_enabled': 1}
        answer = ' ۱۲۳ ۴۵۶  '
        
        result = auto_fix_answer(answer, question)
        assert result == '123456'

    def test_auto_fix_answer_non_string(self):
        """تست اصلاح خودکار برای مقدار غیررشته‌ای"""
        question = {'auto_fix_enabled': 1}
        answer = 123456
        
        result = auto_fix_answer(answer, question)
        assert result == 123456

    # ============================================================
    # تست‌های get_validation_error_message
    # ============================================================

    def test_get_validation_error_message_custom(self):
        """تست دریافت پیام خطای سفارشی"""
        question = {'validation_error': 'پیام خطای سفارشی'}
        
        result = get_validation_error_message(question, 'required')
        assert result == 'پیام خطای سفارشی'

    def test_get_validation_error_message_required(self):
        """تست دریافت پیام خطای اجباری"""
        question = {}
        
        result = get_validation_error_message(question, 'required')
        assert 'اجباری' in result

    def test_get_validation_error_message_min_length(self):
        """تست دریافت پیام خطای حداقل طول"""
        question = {'min_length': 10}
        
        result = get_validation_error_message(question, 'min_length')
        assert '10' in result

    def test_get_validation_error_message_max_length(self):
        """تست دریافت پیام خطای حداکثر طول"""
        question = {'max_length': 50}
        
        result = get_validation_error_message(question, 'max_length')
        assert '50' in result

    def test_get_validation_error_message_numeric(self):
        """تست دریافت پیام خطای عددی"""
        question = {}
        
        result = get_validation_error_message(question, 'numeric')
        assert 'عدد' in result

    def test_get_validation_error_message_unknown(self):
        """تست دریافت پیام خطای ناشناخته"""
        question = {}
        
        result = get_validation_error_message(question, 'unknown_error')
        assert 'نامعتبر' in result

    # ============================================================
    # تست‌های validate_answer
    # ============================================================

    def test_validate_answer_required_pass(self):
        """تست اعتبارسنجی پاسخ اجباری با موفقیت"""
        question = {'is_required': 1}
        answer = 'پاسخ معتبر'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None
        assert fixed == 'پاسخ معتبر'

    def test_validate_answer_required_fail(self):
        """تست اعتبارسنجی پاسخ اجباری با شکست"""
        question = {'is_required': 1}
        answer = ''
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'required'
        assert fixed == ''

    def test_validate_answer_validation_disabled(self):
        """تست اعتبارسنجی وقتی اعتبارسنجی غیرفعال است"""
        question = {'is_required': 0, 'validation_enabled': 0}
        answer = 'پاسخ نامعتبر'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_text_success(self):
        """تست اعتبارسنجی متن با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'text',
            'length_validation_enabled': 1,
            'min_length': 3,
            'max_length': 10,
        }
        answer = 'متن معتبر'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_text_min_length_fail(self):
        """تست اعتبارسنجی متن با حداقل طول نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'text',
            'length_validation_enabled': 1,
            'min_length': 5,
            'max_length': 10,
        }
        answer = 'abc'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'min_length'

    def test_validate_answer_text_max_length_fail(self):
        """تست اعتبارسنجی متن با حداکثر طول نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'text',
            'length_validation_enabled': 1,
            'min_length': 3,
            'max_length': 5,
        }
        answer = 'abcde fghij'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'max_length'

    def test_validate_answer_number_success(self):
        """تست اعتبارسنجی عدد با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'number',
            'numeric_validation_enabled': 1,
            'min_value': 10,
            'max_value': 100,
        }
        answer = '50'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_number_min_fail(self):
        """تست اعتبارسنجی عدد با حداقل مقدار نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'number',
            'numeric_validation_enabled': 1,
            'min_value': 18,
            'max_value': 99,
        }
        answer = '15'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'min_value'

    def test_validate_answer_number_max_fail(self):
        """تست اعتبارسنجی عدد با حداکثر مقدار نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'number',
            'numeric_validation_enabled': 1,
            'min_value': 18,
            'max_value': 99,
        }
        answer = '150'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'max_value'

    def test_validate_answer_number_invalid(self):
        """تست اعتبارسنجی عدد با مقدار غیرعددی"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'number',
        }
        answer = 'abc'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'numeric'

    def test_validate_answer_decimal_success(self):
        """تست اعتبارسنجی عدد اعشاری با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'decimal',
            'numeric_validation_enabled': 1,
            'min_value': 0.5,
            'max_value': 10.0,
        }
        answer = '5.5'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_decimal_invalid(self):
        """تست اعتبارسنجی عدد اعشاری با مقدار غیرعددی"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'decimal',
        }
        answer = 'abc'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'decimal'

    def test_validate_answer_national_code_success(self):
        """تست اعتبارسنجی کد ملی با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'national_code',
        }
        answer = '0123456789'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_national_code_invalid_length(self):
        """تست اعتبارسنجی کد ملی با طول نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'national_code',
        }
        answer = '12345'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'national_code'

    def test_validate_answer_national_code_invalid_digits(self):
        """تست اعتبارسنجی کد ملی با ارقام نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'national_code',
        }
        answer = '1111111111'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'national_code'

    def test_validate_answer_phone_success(self):
        """تست اعتبارسنجی تلفن همراه با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'phone',
        }
        answer = '09123456789'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_phone_invalid(self):
        """تست اعتبارسنجی تلفن همراه نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'phone',
        }
        answer = '1234567890'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'phone'

    def test_validate_answer_phone_landline_success(self):
        """تست اعتبارسنجی تلفن ثابت با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'phone_landline',
        }
        answer = '0212345678'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_postal_code_success(self):
        """تست اعتبارسنجی کدپستی با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'postal_code',
        }
        answer = '1234567890'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_postal_code_invalid(self):
        """تست اعتبارسنجی کدپستی نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'postal_code',
        }
        answer = '12345'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'postal_code'

    def test_validate_answer_plate_success(self):
        """تست اعتبارسنجی پلاک خودرو با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'plate',
        }
        answer = '123-456-78'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_plate_invalid(self):
        """تست اعتبارسنجی پلاک خودرو نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'plate',
        }
        answer = '123456'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'plate'

    def test_validate_answer_iban_success(self):
        """تست اعتبارسنجی شبا با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'iban',
        }
        answer = 'IR123456789012345678901234'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_iban_invalid(self):
        """تست اعتبارسنجی شبا نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'iban',
        }
        answer = '1234567890'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'iban'

    def test_validate_answer_card_number_success(self):
        """تست اعتبارسنجی شماره کارت با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'card_number',
        }
        # یک شماره کارت معتبر تست (الگوریتم Luhn)
        answer = '6037997377314522'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_card_number_invalid(self):
        """تست اعتبارسنجی شماره کارت نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'card_number',
        }
        answer = '1234567890123456'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'card_number'

    def test_validate_answer_email_success(self):
        """تست اعتبارسنجی ایمیل با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'email',
        }
        answer = 'test@example.com'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_email_invalid(self):
        """تست اعتبارسنجی ایمیل نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'email',
        }
        answer = 'invalid-email'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'email'

    def test_validate_answer_url_success(self):
        """تست اعتبارسنجی URL با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'url',
        }
        answer = 'https://example.com'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_url_invalid(self):
        """تست اعتبارسنجی URL نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'url',
        }
        answer = 'invalid-url'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'url'

    def test_validate_answer_date_success(self):
        """تست اعتبارسنجی تاریخ شمسی با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'date',
            'date_validation_enabled': 1,
            'min_date': '1400/01/01',
            'max_date': '1403/12/29',
        }
        answer = '1401/06/15'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_date_invalid_format(self):
        """تست اعتبارسنجی تاریخ شمسی با فرمت نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'date',
        }
        answer = '2024-01-15'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'date'

    def test_validate_answer_date_gregorian_success(self):
        """تست اعتبارسنجی تاریخ میلادی با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'date_gregorian',
        }
        answer = '2024/01/15'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_time_success(self):
        """تست اعتبارسنجی زمان با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'time',
        }
        answer = '14:30'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_time_invalid(self):
        """تست اعتبارسنجی زمان نامعتبر"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'time',
        }
        answer = '25:70'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'time'

    def test_validate_answer_datetime_success(self):
        """تست اعتبارسنجی تاریخ و زمان با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'datetime',
        }
        answer = '1401/06/15 14:30'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_persian_text_success(self):
        """تست اعتبارسنجی متن فارسی با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'persian_text',
        }
        answer = 'متن فارسی نمونه'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_persian_text_invalid(self):
        """تست اعتبارسنجی متن فارسی با کاراکترهای غیرفارسی"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'persian_text',
        }
        answer = 'متن فارسی با English'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'persian_text'

    def test_validate_answer_english_text_success(self):
        """تست اعتبارسنجی متن انگلیسی با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'english_text',
        }
        answer = 'English text sample'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_english_text_invalid(self):
        """تست اعتبارسنجی متن انگلیسی با کاراکترهای غیرانگلیسی"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'english_text',
        }
        answer = 'English متن'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'english_text'

    def test_validate_answer_alphanumeric_success(self):
        """تست اعتبارسنجی حروف و اعداد با موفقیت"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'alphanumeric',
        }
        answer = 'ABC123 نمونه'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_alphanumeric_invalid(self):
        """تست اعتبارسنجی حروف و اعداد با کاراکترهای غیرمجاز"""
        question = {
            'validation_enabled': 1,
            'validation_type': 'alphanumeric',
        }
        answer = 'ABC@#$%'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'alphanumeric'

    def test_validate_answer_starts_with_success(self):
        """تست اعتبارسنجی شروع با مقدار مشخص - موفقیت"""
        question = {
            'validation_enabled': 1,
            'pattern_validation_enabled': 1,
            'starts_with': 'سلام',
        }
        answer = 'سلام دنیا'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_starts_with_fail(self):
        """تست اعتبارسنجی شروع با مقدار مشخص - شکست"""
        question = {
            'validation_enabled': 1,
            'pattern_validation_enabled': 1,
            'starts_with': 'سلام',
        }
        answer = 'دنیا سلام'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'starts_with'

    def test_validate_answer_ends_with_success(self):
        """تست اعتبارسنجی پایان با مقدار مشخص - موفقیت"""
        question = {
            'validation_enabled': 1,
            'pattern_validation_enabled': 1,
            'ends_with': 'خداحافظ',
        }
        answer = 'سلام خداحافظ'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_ends_with_fail(self):
        """تست اعتبارسنجی پایان با مقدار مشخص - شکست"""
        question = {
            'validation_enabled': 1,
            'pattern_validation_enabled': 1,
            'ends_with': 'خداحافظ',
        }
        answer = 'خداحافظ سلام'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'ends_with'

    def test_validate_answer_contains_success(self):
        """تست اعتبارسنجی شامل مقدار مشخص - موفقیت"""
        question = {
            'validation_enabled': 1,
            'contains_validation_enabled': 1,
            'contains': 'ایران',
        }
        answer = 'من در ایران زندگی می‌کنم'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_contains_fail(self):
        """تست اعتبارسنجی شامل مقدار مشخص - شکست"""
        question = {
            'validation_enabled': 1,
            'contains_validation_enabled': 1,
            'contains': 'ایران',
        }
        answer = 'من در تهران زندگی می‌کنم'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'contains'

    def test_validate_answer_not_contains_success(self):
        """تست اعتبارسنجی شامل نباشد مقدار مشخص - موفقیت"""
        question = {
            'validation_enabled': 1,
            'contains_validation_enabled': 1,
            'not_contains': 'بیگانه',
        }
        answer = 'من ایرانی هستم'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_not_contains_fail(self):
        """تست اعتبارسنجی شامل نباشد مقدار مشخص - شکست"""
        question = {
            'validation_enabled': 1,
            'contains_validation_enabled': 1,
            'not_contains': 'بیگانه',
        }
        answer = 'من بیگانه هستم'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'not_contains'

    def test_validate_answer_forbidden_words_success(self):
        """تست اعتبارسنجی کلمات ممنوع - موفقیت"""
        question = {
            'validation_enabled': 1,
            'contains_validation_enabled': 1,
            'forbidden_words': 'بد,زشت,ناجور',
        }
        answer = 'متن پاک و سالم'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_forbidden_words_fail(self):
        """تست اعتبارسنجی کلمات ممنوع - شکست"""
        question = {
            'validation_enabled': 1,
            'contains_validation_enabled': 1,
            'forbidden_words': 'بد,زشت,ناجور',
        }
        answer = 'این متن بد است'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'forbidden_words'

    def test_validate_answer_required_words_success(self):
        """تست اعتبارسنجی کلمات الزامی - موفقیت"""
        question = {
            'validation_enabled': 1,
            'contains_validation_enabled': 1,
            'required_words': 'سلام,احترام',
        }
        answer = 'سلام با احترام'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_required_words_fail(self):
        """تست اعتبارسنجی کلمات الزامی - شکست"""
        question = {
            'validation_enabled': 1,
            'contains_validation_enabled': 1,
            'required_words': 'سلام,احترام',
        }
        answer = 'بدون کلمات الزامی'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'required_words'

    def test_validate_answer_regex_success(self):
        """تست اعتبارسنجی با الگوی regex - موفقیت"""
        question = {
            'validation_enabled': 1,
            'pattern_validation_enabled': 1,
            'regex_pattern': r'^\d{4}-\d{4}$',
        }
        answer = '1234-5678'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None

    def test_validate_answer_regex_fail(self):
        """تست اعتبارسنجی با الگوی regex - شکست"""
        question = {
            'validation_enabled': 1,
            'pattern_validation_enabled': 1,
            'regex_pattern': r'^\d{4}-\d{4}$',
        }
        answer = '1234'
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'regex'

    def test_validate_answer_auto_fix_applied(self):
        """تست اعتبارسنجی با اصلاح خودکار"""
        question = {
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'text',
            'auto_fix_enabled': 1,
        }
        answer = '  متن با فاصله  '
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is True
        assert error is None
        assert fixed == 'متن با فاصله'

    def test_validate_answer_auto_fix_trim_required(self):
        """تست اعتبارسنجی با اصلاح خودکار و پاسخ خالی"""
        question = {
            'is_required': 1,
            'validation_enabled': 1,
            'auto_fix_enabled': 1,
        }
        answer = '   '
        
        is_valid, error, fixed = validate_answer(answer, question)
        assert is_valid is False
        assert error == 'required'
        assert fixed == ''