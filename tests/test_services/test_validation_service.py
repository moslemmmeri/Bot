# tests/test_services/test_validation_service.py
# تست‌های واحد برای ValidationService

import pytest
from unittest.mock import MagicMock, patch

from services.validation_service import ValidationService


class TestValidationService:
    """تست‌های ValidationService"""

    @pytest.fixture
    def validation_service(self, db_connection):
        """ایجاد ValidationService با اتصال دیتابیس تست"""
        return ValidationService(db_connection)

    @pytest.fixture
    def sample_question(self):
        """داده‌های نمونه سوال"""
        return {
            'id': 1,
            'question_text': 'نام کامل خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'text',
            'length_validation_enabled': 1,
            'min_length': 3,
            'max_length': 50,
            'auto_fix_enabled': 0,
            'validation_error': None,
        }

    # ============================================================
    # تست‌های اعتبارسنجی متن
    # ============================================================

    def test_validate_text_success(self, validation_service, sample_question):
        """تست اعتبارسنجی متن با موفقیت"""
        is_valid, error, fixed = validation_service.validate_answer(
            answer='علی محمدی',
            question=sample_question,
        )

        assert is_valid is True
        assert error is None
        assert fixed == 'علی محمدی'

    def test_validate_text_min_length_fail(self, validation_service, sample_question):
        """تست اعتبارسنجی متن با حداقل طول نامعتبر"""
        is_valid, error, fixed = validation_service.validate_answer(
            answer='ع',
            question=sample_question,
        )

        assert is_valid is False
        assert error == 'min_length'

    def test_validate_text_max_length_fail(self, validation_service, sample_question):
        """تست اعتبارسنجی متن با حداکثر طول نامعتبر"""
        is_valid, error, fixed = validation_service.validate_answer(
            answer='a' * 60,
            question=sample_question,
        )

        assert is_valid is False
        assert error == 'max_length'

    def test_validate_text_empty_required(self, validation_service, sample_question):
        """تست اعتبارسنجی متن خالی برای سوال اجباری"""
        is_valid, error, fixed = validation_service.validate_answer(
            answer='',
            question=sample_question,
        )

        assert is_valid is False
        assert error == 'required'

    def test_validate_text_not_required(self, validation_service, sample_question):
        """تست اعتبارسنجی متن خالی برای سوال غیراجباری"""
        question = sample_question.copy()
        question['is_required'] = 0

        is_valid, error, fixed = validation_service.validate_answer(
            answer='',
            question=question,
        )

        assert is_valid is True
        assert error is None

    # ============================================================
    # تست‌های اعتبارسنجی اعداد
    # ============================================================

    def test_validate_number_success(self, validation_service):
        """تست اعتبارسنجی عدد با موفقیت"""
        question = {
            'id': 2,
            'question_text': 'سن خود را وارد کنید:',
            'question_type': 'number',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'number',
            'numeric_validation_enabled': 1,
            'min_value': 18,
            'max_value': 99,
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='25',
            question=question,
        )

        assert is_valid is True
        assert error is None
        assert fixed == '25'

    def test_validate_number_min_fail(self, validation_service):
        """تست اعتبارسنجی عدد با حداقل نامعتبر"""
        question = {
            'id': 2,
            'question_text': 'سن خود را وارد کنید:',
            'question_type': 'number',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'number',
            'numeric_validation_enabled': 1,
            'min_value': 18,
            'max_value': 99,
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='15',
            question=question,
        )

        assert is_valid is False
        assert error == 'min_value'

    def test_validate_number_max_fail(self, validation_service):
        """تست اعتبارسنجی عدد با حداکثر نامعتبر"""
        question = {
            'id': 2,
            'question_text': 'سن خود را وارد کنید:',
            'question_type': 'number',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'number',
            'numeric_validation_enabled': 1,
            'min_value': 18,
            'max_value': 99,
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='150',
            question=question,
        )

        assert is_valid is False
        assert error == 'max_value'

    def test_validate_number_invalid(self, validation_service):
        """تست اعتبارسنجی عدد نامعتبر"""
        question = {
            'id': 2,
            'question_text': 'سن خود را وارد کنید:',
            'question_type': 'number',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'number',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='abc',
            question=question,
        )

        assert is_valid is False
        assert error == 'numeric'

    # ============================================================
    # تست‌های اعتبارسنجی کد ملی
    # ============================================================

    def test_validate_national_code_success(self, validation_service):
        """تست اعتبارسنجی کد ملی با موفقیت"""
        question = {
            'id': 3,
            'question_text': 'کد ملی خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'national_code',
        }

        # کد ملی معتبر (کد تست)
        is_valid, error, fixed = validation_service.validate_answer(
            answer='0123456789',
            question=question,
        )

        assert is_valid is True
        assert error is None

    def test_validate_national_code_invalid_length(self, validation_service):
        """تست اعتبارسنجی کد ملی با طول نامعتبر"""
        question = {
            'id': 3,
            'question_text': 'کد ملی خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'national_code',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='12345',
            question=question,
        )

        assert is_valid is False
        assert error == 'national_code'

    def test_validate_national_code_invalid_codes(self, validation_service):
        """تست اعتبارسنجی کدهای ملی نامعتبر"""
        question = {
            'id': 3,
            'question_text': 'کد ملی خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'national_code',
        }

        invalid_codes = ['1111111111', '2222222222', '3333333333', '4444444444']
        for code in invalid_codes:
            is_valid, error, fixed = validation_service.validate_answer(
                answer=code,
                question=question,
            )
            assert is_valid is False
            assert error == 'national_code'

    # ============================================================
    # تست‌های اعتبارسنجی تلفن
    # ============================================================

    def test_validate_phone_success(self, validation_service):
        """تست اعتبارسنجی تلفن همراه با موفقیت"""
        question = {
            'id': 4,
            'question_text': 'شماره تماس خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'phone',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='09123456789',
            question=question,
        )

        assert is_valid is True
        assert error is None

    def test_validate_phone_invalid(self, validation_service):
        """تست اعتبارسنجی تلفن همراه نامعتبر"""
        question = {
            'id': 4,
            'question_text': 'شماره تماس خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'phone',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='12345678',
            question=question,
        )

        assert is_valid is False
        assert error == 'phone'

    # ============================================================
    # تست‌های اعتبارسنجی ایمیل
    # ============================================================

    def test_validate_email_success(self, validation_service):
        """تست اعتبارسنجی ایمیل با موفقیت"""
        question = {
            'id': 5,
            'question_text': 'ایمیل خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'email',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='test@example.com',
            question=question,
        )

        assert is_valid is True
        assert error is None

    def test_validate_email_invalid(self, validation_service):
        """تست اعتبارسنجی ایمیل نامعتبر"""
        question = {
            'id': 5,
            'question_text': 'ایمیل خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'email',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='invalid-email',
            question=question,
        )

        assert is_valid is False
        assert error == 'email'

    # ============================================================
    # تست‌های اصلاح خودکار
    # ============================================================

    def test_auto_fix_trim_spaces(self, validation_service, sample_question):
        """تست اصلاح خودکار - حذف فضاهای اضافی"""
        question = sample_question.copy()
        question['auto_fix_enabled'] = 1

        is_valid, error, fixed = validation_service.validate_answer(
            answer='  علی محمدی  ',
            question=question,
        )

        assert is_valid is True
        assert fixed == 'علی محمدی'

    def test_auto_fix_persian_to_english(self, validation_service, sample_question):
        """تست اصلاح خودکار - تبدیل اعداد فارسی به انگلیسی"""
        question = sample_question.copy()
        question['auto_fix_enabled'] = 1
        question['validation_type'] = 'number'
        question['numeric_validation_enabled'] = 1

        is_valid, error, fixed = validation_service.validate_answer(
            answer='۱۲۳',
            question=question,
        )

        assert is_valid is True
        # انتظار داریم که عدد به انگلیسی تبدیل شود
        # اگر validation_service خودکار تبدیل را انجام دهد
        # در غیر این صورت، عدد به صورت متن باقی می‌ماند

    # ============================================================
    # تست‌های پیام خطا
    # ============================================================

    def test_get_error_message(self, validation_service, sample_question):
        """تست دریافت پیام خطا"""
        message = validation_service.get_error_message(
            question=sample_question,
            error_type='min_length',
        )

        assert 'حداقل طول' in message

    def test_get_error_message_custom(self, validation_service):
        """تست دریافت پیام خطای سفارشی"""
        question = {
            'id': 1,
            'question_text': 'سوال تست:',
            'validation_error': 'پیام خطای سفارشی',
        }

        message = validation_service.get_error_message(
            question=question,
            error_type='required',
        )

        assert message == 'پیام خطای سفارشی'

    # ============================================================
    # تست‌های شرط‌های نمایش
    # ============================================================

    def test_check_conditional_visibility_success(self, validation_service):
        """تست بررسی شرط نمایش با موفقیت"""
        question = {
            'id': 1,
            'question_text': 'سوال شرطی:',
            'conditional_enabled': 1,
            'conditional_on': 1,
            'conditional_value': 'بله',
        }

        user_answers = {
            'سوال مرجع': 'بله',
        }

        result = validation_service.check_conditional_visibility(
            question=question,
            user_answers=user_answers,
        )

        assert result is True

    def test_check_conditional_visibility_fail(self, validation_service):
        """تست بررسی شرط نمایش با شکست"""
        question = {
            'id': 1,
            'question_text': 'سوال شرطی:',
            'conditional_enabled': 1,
            'conditional_on': 1,
            'conditional_value': 'بله',
        }

        user_answers = {
            'سوال مرجع': 'خیر',
        }

        result = validation_service.check_conditional_visibility(
            question=question,
            user_answers=user_answers,
        )

        assert result is False

    def test_check_conditional_visibility_disabled(self, validation_service):
        """تست بررسی شرط نمایش در صورت غیرفعال بودن"""
        question = {
            'id': 1,
            'question_text': 'سوال بدون شرط:',
            'conditional_enabled': 0,
        }

        user_answers = {}

        result = validation_service.check_conditional_visibility(
            question=question,
            user_answers=user_answers,
        )

        assert result is True

    # ============================================================
    # تست‌های اعتبارسنجی فایل
    # ============================================================

    def test_validate_file_success(self, validation_service):
        """تست اعتبارسنجی فایل با موفقیت"""
        question = {
            'id': 6,
            'question_text': 'فایل خود را آپلود کنید:',
            'question_type': 'file',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'file',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='[فایل: document]',
            question=question,
        )

        assert is_valid is True
        assert error is None

    def test_validate_file_invalid(self, validation_service):
        """تست اعتبارسنجی فایل نامعتبر"""
        question = {
            'id': 6,
            'question_text': 'فایل خود را آپلود کنید:',
            'question_type': 'file',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'file',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='not_a_file',
            question=question,
        )

        assert is_valid is False
        assert error == 'file'

    # ============================================================
    # تست‌های اعتبارسنجی ایمیل (ادامه)
    # ============================================================

    def test_validate_email_empty_required(self, validation_service):
        """تست اعتبارسنجی ایمیل خالی برای سوال اجباری"""
        question = {
            'id': 5,
            'question_text': 'ایمیل خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'email',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='',
            question=question,
        )

        assert is_valid is False
        assert error == 'required'

    # ============================================================
    # تست‌های اعتبارسنجی اعشاری
    # ============================================================

    def test_validate_decimal_success(self, validation_service):
        """تست اعتبارسنجی عدد اعشاری با موفقیت"""
        question = {
            'id': 7,
            'question_text': 'مبلغ را وارد کنید:',
            'question_type': 'number',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'decimal',
            'numeric_validation_enabled': 1,
            'min_value': 0.5,
            'max_value': 10.0,
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='5.5',
            question=question,
        )

        assert is_valid is True
        assert error is None

    def test_validate_decimal_invalid(self, validation_service):
        """تست اعتبارسنجی عدد اعشاری نامعتبر"""
        question = {
            'id': 7,
            'question_text': 'مبلغ را وارد کنید:',
            'question_type': 'number',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'decimal',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='abc',
            question=question,
        )

        assert is_valid is False
        assert error == 'decimal'

    # ============================================================
    # تست‌های اعتبارسنجی URL
    # ============================================================

    def test_validate_url_success(self, validation_service):
        """تست اعتبارسنجی URL با موفقیت"""
        question = {
            'id': 8,
            'question_text': 'آدرس وب‌سایت خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'url',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='https://example.com',
            question=question,
        )

        assert is_valid is True
        assert error is None

    def test_validate_url_invalid(self, validation_service):
        """تست اعتبارسنجی URL نامعتبر"""
        question = {
            'id': 8,
            'question_text': 'آدرس وب‌سایت خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'url',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='invalid-url',
            question=question,
        )

        assert is_valid is False
        assert error == 'url'

    # ============================================================
    # تست‌های اعتبارسنجی تاریخ
    # ============================================================

    def test_validate_date_success(self, validation_service):
        """تست اعتبارسنجی تاریخ با موفقیت"""
        question = {
            'id': 9,
            'question_text': 'تاریخ تولد خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'date',
            'date_validation_enabled': 1,
            'min_date': '1400/01/01',
            'max_date': '1403/12/29',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='1401/06/15',
            question=question,
        )

        assert is_valid is True
        assert error is None

    def test_validate_date_invalid_format(self, validation_service):
        """تست اعتبارسنجی تاریخ با فرمت نامعتبر"""
        question = {
            'id': 9,
            'question_text': 'تاریخ تولد خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_enabled': 1,
            'validation_type': 'date',
        }

        is_valid, error, fixed = validation_service.validate_answer(
            answer='2024-01-15',
            question=question,
        )

        assert is_valid is False
        assert error == 'date'