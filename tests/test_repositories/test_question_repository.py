# tests/test_repositories/test_question_repository.py
# تست‌های واحد برای QuestionRepository

import pytest
from unittest.mock import MagicMock, patch

from repositories.question_repository import QuestionRepository


class TestQuestionRepository:
    """تست‌های QuestionRepository"""

    @pytest.fixture
    def question_repo(self, db_connection):
        """ایجاد QuestionRepository با اتصال دیتابیس تست"""
        return QuestionRepository(db_connection)

    @pytest.fixture
    def sample_category_data(self, db_connection):
        """ایجاد دسته‌بندی نمونه در دیتابیس"""
        with db_connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, location, is_active) VALUES (?, ?, ?)",
                ('دسته تست', 'main', 1)
            )
            category_id = cursor.get_lastrowid()
            return {'id': category_id, 'name': 'دسته تست'}

    @pytest.fixture
    def sample_button_data(self, sample_category_data, db_connection):
        """ایجاد دکمه نمونه در دیتابیس"""
        with db_connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (sample_category_data['id'], 'دکمه تست', 'btn_test', 1)
            )
            button_id = cursor.get_lastrowid()
            return {'id': button_id, 'name': 'دکمه تست'}

    @pytest.fixture
    def sample_question_data(self, sample_button_data):
        """داده‌های نمونه سوال"""
        return {
            'button_id': sample_button_data['id'],
            'question_text': 'نام کامل خود را وارد کنید:',
            'question_type': 'text',
            'is_required': 1,
            'validation_type': 'text',
            'needs_button': 0,
            'sort_order': 0,
        }

    # ============================================================
    # تست‌های add_question
    # ============================================================

    def test_add_question_success(self, question_repo, sample_question_data):
        """تست ایجاد سوال با موفقیت"""
        question_id = question_repo.create(
            button_id=sample_question_data['button_id'],
            question_text=sample_question_data['question_text'],
            question_type=sample_question_data['question_type'],
            is_required=sample_question_data['is_required'],
            validation_type=sample_question_data['validation_type'],
            needs_button=sample_question_data['needs_button'],
            sort_order=sample_question_data['sort_order'],
        )

        assert question_id is not None
        assert question_id > 0

        question = question_repo.get_by_id(question_id)
        assert question is not None
        assert question['question_text'] == sample_question_data['question_text']
        assert question['question_type'] == sample_question_data['question_type']
        assert question['is_required'] == sample_question_data['is_required']
        assert question['sort_order'] == sample_question_data['sort_order']

    def test_add_question_with_validation_settings(self, question_repo, sample_button_data):
        """تست ایجاد سوال با تنظیمات اعتبارسنجی کامل"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='شماره تماس:',
            question_type='text',
            is_required=1,
            validation_enabled=1,
            validation_type='phone',
            length_validation_enabled=1,
            min_length=11,
            max_length=11,
        )

        assert question_id is not None
        question = question_repo.get_by_id(question_id)
        assert question['validation_enabled'] == 1
        assert question['validation_type'] == 'phone'
        assert question['length_validation_enabled'] == 1
        assert question['min_length'] == 11
        assert question['max_length'] == 11

    def test_add_question_without_button(self, question_repo):
        """تست ایجاد سوال بدون دکمه (باید خطا دهد)"""
        with pytest.raises(Exception):
            question_repo.create(
                button_id=99999,
                question_text='سوال تست',
            )

    # ============================================================
    # تست‌های get_by_id
    # ============================================================

    def test_get_question_by_id_success(self, question_repo, sample_question_data):
        """تست دریافت سوال با شناسه"""
        question_id = question_repo.create(
            button_id=sample_question_data['button_id'],
            question_text=sample_question_data['question_text'],
        )

        question = question_repo.get_by_id(question_id)
        assert question is not None
        assert question['id'] == question_id
        assert question['question_text'] == sample_question_data['question_text']

    def test_get_question_by_id_not_found(self, question_repo):
        """تست دریافت سوال ناموجود"""
        question = question_repo.get_by_id(99999)
        assert question is None

    # ============================================================
    # تست‌های get_by_button
    # ============================================================

    def test_get_questions_by_button(self, question_repo, sample_button_data):
        """تست دریافت سوالات یک دکمه"""
        for i in range(3):
            question_repo.create(
                button_id=sample_button_data['id'],
                question_text=f'سوال {i}',
                sort_order=i,
            )

        questions = question_repo.get_by_button(sample_button_data['id'])
        assert len(questions) == 3
        # بررسی مرتب‌سازی بر اساس sort_order
        assert questions[0]['sort_order'] == 0
        assert questions[1]['sort_order'] == 1
        assert questions[2]['sort_order'] == 2

    def test_get_questions_by_button_inactive(self, question_repo, sample_button_data):
        """تست دریافت سوالات فعال یک دکمه (غیرفعال‌ها نمایش داده نشوند)"""
        question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال فعال',
            is_active=1,
        )
        question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال غیرفعال',
            is_active=0,
        )

        # فقط سوالات فعال
        active_questions = question_repo.get_by_button(sample_button_data['id'])
        assert len(active_questions) == 1
        assert active_questions[0]['question_text'] == 'سوال فعال'

        # همه سوالات (شامل غیرفعال)
        all_questions = question_repo.get_by_button(sample_button_data['id'], include_inactive=True)
        assert len(all_questions) == 2

    def test_get_active_questions(self, question_repo, sample_button_data):
        """تست دریافت سوالات فعال (همان get_by_button با include_inactive=False)"""
        question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۱',
            is_active=1,
        )
        question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۲',
            is_active=0,
        )

        active = question_repo.get_active_questions(sample_button_data['id'])
        assert len(active) == 1
        assert active[0]['question_text'] == 'سوال ۱'

    # ============================================================
    # تست‌های get_previous_questions
    # ============================================================

    def test_get_previous_questions(self, question_repo, sample_button_data):
        """تست دریافت سوالات قبلی یک دکمه"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۱',
            sort_order=1,
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۲',
            sort_order=2,
        )
        q3 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۳',
            sort_order=3,
        )

        # سوالات قبل از سوال ۲
        previous = question_repo.get_previous_questions(sample_button_data['id'], q2)
        assert len(previous) == 1
        assert previous[0]['id'] == q1

        # سوالات قبل از سوال ۳
        previous = question_repo.get_previous_questions(sample_button_data['id'], q3)
        assert len(previous) == 2
        assert previous[0]['id'] == q1
        assert previous[1]['id'] == q2

    def test_get_previous_questions_all(self, question_repo, sample_button_data):
        """تست دریافت تمام سوالات (بدون current_question_id)"""
        for i in range(3):
            question_repo.create(
                button_id=sample_button_data['id'],
                question_text=f'سوال {i}',
                sort_order=i,
            )

        previous = question_repo.get_previous_questions(sample_button_data['id'])
        assert len(previous) == 3

    # ============================================================
    # تست‌های get_next_question
    # ============================================================

    def test_get_next_question(self, question_repo, sample_button_data):
        """تست دریافت سوال بعدی بر اساس ترتیب"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۱',
            sort_order=1,
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۲',
            sort_order=2,
        )
        q3 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۳',
            sort_order=3,
        )

        next_q = question_repo.get_next_question(sample_button_data['id'], 1)
        assert next_q is not None
        assert next_q['id'] == q2

        next_q = question_repo.get_next_question(sample_button_data['id'], 2)
        assert next_q is not None
        assert next_q['id'] == q3

    def test_get_next_question_not_found(self, question_repo, sample_button_data):
        """تست دریافت سوال بعدی در صورت عدم وجود"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۱',
            sort_order=1,
        )

        next_q = question_repo.get_next_question(sample_button_data['id'], 1)
        assert next_q is None

    # ============================================================
    # تست‌های update
    # ============================================================

    def test_update_question_text(self, question_repo, sample_button_data):
        """تست تغییر متن سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='متن قدیم',
        )

        result = question_repo.update_text(question_id, 'متن جدید')
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['question_text'] == 'متن جدید'

    def test_update_question_type(self, question_repo, sample_button_data):
        """تست تغییر نوع سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
            question_type='text',
        )

        result = question_repo.update_type(question_id, 'number')
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['question_type'] == 'number'

    def test_toggle_active(self, question_repo, sample_button_data):
        """تست تغییر وضعیت فعال/غیرفعال سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
            is_active=1,
        )

        result = question_repo.toggle_active(question_id)
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['is_active'] == 0

        result = question_repo.toggle_active(question_id)
        assert result is True
        question = question_repo.get_by_id(question_id)
        assert question['is_active'] == 1

    def test_toggle_required(self, question_repo, sample_button_data):
        """تست تغییر وضعیت اجباری بودن سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
            is_required=0,
        )

        result = question_repo.toggle_required(question_id)
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['is_required'] == 1

    def test_toggle_validation(self, question_repo, sample_button_data):
        """تست تغییر وضعیت یک قابلیت اعتبارسنجی"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
            validation_enabled=0,
        )

        result = question_repo.toggle_validation_feature(question_id, 'validation_enabled')
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['validation_enabled'] == 1

    def test_toggle_validation_invalid_feature(self, question_repo, sample_button_data):
        """تست تغییر وضعیت با ویژگی نامعتبر"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
        )

        result = question_repo.toggle_validation_feature(question_id, 'invalid_feature')
        assert result is False

    def test_update_validation_settings(self, question_repo, sample_button_data):
        """تست به‌روزرسانی تنظیمات اعتبارسنجی"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
        )

        settings = {
            'validation_type': 'email',
            'min_length': 5,
            'max_length': 50,
            'validation_enabled': 1,
        }

        result = question_repo.update_validation_settings(question_id, settings)
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['validation_type'] == 'email'
        assert question['min_length'] == 5
        assert question['max_length'] == 50
        assert question['validation_enabled'] == 1

    # ============================================================
    # تست‌های delete
    # ============================================================

    def test_delete_question(self, question_repo, sample_button_data):
        """تست حذف سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال برای حذف',
        )

        result = question_repo.delete(question_id)
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question is None

    def test_delete_question_with_options(self, question_repo, sample_button_data):
        """تست حذف سوال با گزینه‌های مرتبط"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
            needs_button=1,
        )

        # افزودن گزینه
        option_id = question_repo.add_option(
            question_id=question_id,
            option_text='گزینه ۱',
            callback_data='opt_1',
        )

        # حذف سوال
        result = question_repo.delete(question_id)
        assert result is True

        # گزینه نیز باید حذف شده باشد
        option = question_repo.get_option_by_id(option_id)
        assert option is None

    def test_delete_questions_by_button(self, question_repo, sample_button_data):
        """تست حذف تمام سوالات یک دکمه"""
        for i in range(3):
            question_repo.create(
                button_id=sample_button_data['id'],
                question_text=f'سوال {i}',
            )

        count = question_repo.delete_by_button(sample_button_data['id'])
        assert count == 3

        questions = question_repo.get_by_button(sample_button_data['id'])
        assert len(questions) == 0

    # ============================================================
    # تست‌های گزینه‌ها (Options)
    # ============================================================

    def test_add_option(self, question_repo, sample_button_data):
        """تست افزودن گزینه به سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
        )

        option_id = question_repo.add_option(
            question_id=question_id,
            option_text='گزینه ۱',
            callback_data='opt_1',
            sort_order=1,
        )

        assert option_id is not None
        option = question_repo.get_option_by_id(option_id)
        assert option is not None
        assert option['option_text'] == 'گزینه ۱'
        assert option['callback_data'] == 'opt_1'
        assert option['sort_order'] == 1

        # بررسی اینکه needs_button به‌روز شده است
        question = question_repo.get_by_id(question_id)
        assert question['needs_button'] == 1

    def test_add_option_auto_callback(self, question_repo, sample_button_data):
        """تست افزودن گزینه با callback_data خودکار"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
        )

        option_id = question_repo.add_option(
            question_id=question_id,
            option_text='گزینه ۱',
        )

        option = question_repo.get_option_by_id(option_id)
        assert option['callback_data'] is not None
        assert option['callback_data'].startswith('qopt_')

    def test_get_options(self, question_repo, sample_button_data):
        """تست دریافت گزینه‌های یک سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
        )

        for i in range(3):
            question_repo.add_option(
                question_id=question_id,
                option_text=f'گزینه {i}',
                sort_order=i,
            )

        options = question_repo.get_options(question_id)
        assert len(options) == 3
        # بررسی مرتب‌سازی
        assert options[0]['sort_order'] == 0
        assert options[1]['sort_order'] == 1
        assert options[2]['sort_order'] == 2

    def test_get_option_by_callback(self, question_repo, sample_button_data):
        """تست دریافت گزینه با callback_data"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
        )

        callback = 'opt_custom_callback'
        question_repo.add_option(
            question_id=question_id,
            option_text='گزینه',
            callback_data=callback,
        )

        option = question_repo.get_option_by_callback(callback)
        assert option is not None
        assert option['callback_data'] == callback

    def test_get_option_by_callback_not_found(self, question_repo):
        """تست دریافت گزینه با callback_data ناموجود"""
        option = question_repo.get_option_by_callback('non_existent')
        assert option is None

    def test_update_option(self, question_repo, sample_button_data):
        """تست به‌روزرسانی متن گزینه"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
        )

        option_id = question_repo.add_option(
            question_id=question_id,
            option_text='متن قدیم',
        )

        result = question_repo.update_option(option_id, 'متن جدید')
        assert result is True

        option = question_repo.get_option_by_id(option_id)
        assert option['option_text'] == 'متن جدید'

    def test_delete_option(self, question_repo, sample_button_data):
        """تست حذف گزینه"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
        )

        option_id = question_repo.add_option(
            question_id=question_id,
            option_text='گزینه',
        )

        result = question_repo.delete_option(option_id)
        assert result is True

        option = question_repo.get_option_by_id(option_id)
        assert option is None

    def test_delete_last_option_turns_off_needs_button(self, question_repo, sample_button_data):
        """تست حذف آخرین گزینه و غیرفعال شدن needs_button"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
            needs_button=1,
        )

        option_id = question_repo.add_option(
            question_id=question_id,
            option_text='گزینه',
        )

        # حذف گزینه
        question_repo.delete_option(option_id)

        # needs_button باید 0 شود
        question = question_repo.get_by_id(question_id)
        assert question['needs_button'] == 0

    def test_delete_options_by_question(self, question_repo, sample_button_data):
        """تست حذف تمام گزینه‌های یک سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
        )

        for i in range(3):
            question_repo.add_option(
                question_id=question_id,
                option_text=f'گزینه {i}',
            )

        count = question_repo.delete_options_by_question(question_id)
        assert count == 3

        options = question_repo.get_options(question_id)
        assert len(options) == 0

    # ============================================================
    # تست‌های شرط‌ها (Conditions)
    # ============================================================

    def test_add_condition(self, question_repo, sample_button_data):
        """تست افزودن شرط به سوال"""
        # ایجاد دو سوال
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال مرجع',
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال شرطی',
        )

        condition_id = question_repo.add_condition(
            question_id=q2,
            condition_question_id=q1,
            condition_operator='==',
            condition_value='بله',
            logic_operator='AND',
            sort_order=1,
        )

        assert condition_id is not None
        condition = question_repo.get_condition_by_id(condition_id)
        assert condition is not None
        assert condition['question_id'] == q2
        assert condition['condition_question_id'] == q1
        assert condition['condition_operator'] == '=='
        assert condition['condition_value'] == 'بله'
        assert condition['logic_operator'] == 'AND'
        assert condition['sort_order'] == 1

    def test_get_conditions(self, question_repo, sample_button_data):
        """تست دریافت شرط‌های یک سوال"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال مرجع',
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال شرطی',
        )

        for i in range(2):
            question_repo.add_condition(
                question_id=q2,
                condition_question_id=q1,
                condition_operator='==',
                condition_value=f'مقدار {i}',
                sort_order=i,
            )

        conditions = question_repo.get_conditions(q2)
        assert len(conditions) == 2
        assert conditions[0]['sort_order'] == 0
        assert conditions[1]['sort_order'] == 1

    def test_update_condition(self, question_repo, sample_button_data):
        """تست به‌روزرسانی شرط"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال مرجع',
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال شرطی',
        )

        condition_id = question_repo.add_condition(
            question_id=q2,
            condition_question_id=q1,
            condition_operator='==',
            condition_value='قدیم',
        )

        result = question_repo.update_condition(
            condition_id,
            condition_value='جدید',
            condition_operator='!=',
        )
        assert result is True

        condition = question_repo.get_condition_by_id(condition_id)
        assert condition['condition_value'] == 'جدید'
        assert condition['condition_operator'] == '!='

    def test_delete_condition(self, question_repo, sample_button_data):
        """تست حذف شرط"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال مرجع',
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال شرطی',
        )

        condition_id = question_repo.add_condition(
            question_id=q2,
            condition_question_id=q1,
            condition_operator='==',
            condition_value='مقدار',
        )

        result = question_repo.delete_condition(condition_id)
        assert result is True

        condition = question_repo.get_condition_by_id(condition_id)
        assert condition is None

    def test_delete_conditions_by_question(self, question_repo, sample_button_data):
        """تست حذف تمام شرط‌های یک سوال"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال مرجع',
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال شرطی',
        )

        for i in range(3):
            question_repo.add_condition(
                question_id=q2,
                condition_question_id=q1,
                condition_operator='==',
                condition_value=f'مقدار {i}',
            )

        count = question_repo.delete_conditions_by_question(q2)
        assert count == 3

        conditions = question_repo.get_conditions(q2)
        assert len(conditions) == 0

    # ============================================================
    # تست‌های get_question_logic_operator
    # ============================================================

    def test_get_question_logic_operator_no_conditions(self, question_repo, sample_button_data):
        """تست دریافت منطق ترکیب شرط‌ها در صورت عدم وجود شرط"""
        q = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
        )

        operator = question_repo.get_question_logic_operator(q)
        assert operator is None

    def test_get_question_logic_operator_single_condition(self, question_repo, sample_button_data):
        """تست دریافت منطق ترکیب شرط‌ها با یک شرط"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال مرجع',
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال شرطی',
        )

        question_repo.add_condition(
            question_id=q2,
            condition_question_id=q1,
            condition_operator='==',
            condition_value='مقدار',
        )

        operator = question_repo.get_question_logic_operator(q2)
        assert operator is None

    def test_get_question_logic_operator_multiple_conditions(self, question_repo, sample_button_data):
        """تست دریافت منطق ترکیب شرط‌ها با چند شرط"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال مرجع ۱',
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال مرجع ۲',
        )
        q3 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال شرطی',
        )

        # شرط اول با منطق AND
        question_repo.add_condition(
            question_id=q3,
            condition_question_id=q1,
            condition_operator='==',
            condition_value='مقدار ۱',
            logic_operator='AND',
        )

        # شرط دوم با منطق OR
        question_repo.add_condition(
            question_id=q3,
            condition_question_id=q2,
            condition_operator='==',
            condition_value='مقدار ۲',
            logic_operator='OR',
        )

        # منطق شرط اول (AND) برگردانده می‌شود
        operator = question_repo.get_question_logic_operator(q3)
        assert operator == 'AND'

    # ============================================================
    # تست‌های get_validation_settings
    # ============================================================

    def test_get_validation_settings(self, question_repo, sample_button_data):
        """تست دریافت تنظیمات اعتبارسنجی یک سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
            is_required=1,
            validation_enabled=1,
            validation_type='email',
            min_length=5,
            max_length=50,
        )

        settings = question_repo.get_validation_settings(question_id)
        assert settings is not None
        assert settings['is_required'] == 1
        assert settings['validation_enabled'] == 1
        assert settings['validation_type'] == 'email'
        assert settings['min_length'] == 5
        assert settings['max_length'] == 50

    def test_get_validation_settings_not_found(self, question_repo):
        """تست دریافت تنظیمات اعتبارسنجی سوال ناموجود"""
        settings = question_repo.get_validation_settings(99999)
        assert settings is None

    # ============================================================
    # تست‌های get_validation_summary
    # ============================================================

    def test_get_validation_summary(self, question_repo, sample_button_data):
        """تست دریافت خلاصه وضعیت اعتبارسنجی یک سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
            is_required=1,
            validation_enabled=1,
            length_validation_enabled=1,
        )

        summary = question_repo.get_validation_status_summary(question_id)
        assert summary is not None
        assert summary['is_required'] is True
        assert summary['validation_enabled'] is True
        assert summary['length_validation_enabled'] is True
        assert summary['word_validation_enabled'] is False

    # ============================================================
    # تست‌های enable_all_validations و disable_all_validations
    # ============================================================

    def test_enable_all_validations(self, question_repo, sample_button_data):
        """تست فعال کردن همه قابلیت‌های اعتبارسنجی"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
            validation_enabled=0,
            length_validation_enabled=0,
            word_validation_enabled=0,
            numeric_validation_enabled=0,
        )

        result = question_repo.enable_all_validations(question_id)
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['validation_enabled'] == 1
        assert question['length_validation_enabled'] == 1
        assert question['word_validation_enabled'] == 1
        assert question['numeric_validation_enabled'] == 1

    def test_disable_all_validations(self, question_repo, sample_button_data):
        """تست غیرفعال کردن همه قابلیت‌های اعتبارسنجی"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
            validation_enabled=1,
            length_validation_enabled=1,
            word_validation_enabled=1,
            numeric_validation_enabled=1,
        )

        result = question_repo.disable_all_validations(question_id)
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['validation_enabled'] == 0
        assert question['length_validation_enabled'] == 0
        assert question['word_validation_enabled'] == 0
        assert question['numeric_validation_enabled'] == 0

    # ============================================================
    # تست‌های reset_validation_to_default
    # ============================================================

    def test_reset_validation_to_default(self, question_repo, sample_button_data):
        """تست بازنشانی تنظیمات اعتبارسنجی به حالت پیش‌فرض"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
            is_required=1,
            validation_enabled=1,
            validation_type='email',
            min_length=5,
            max_length=50,
        )

        result = question_repo.reset_validation_to_default(question_id)
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['is_required'] == 0
        assert question['validation_enabled'] == 0
        assert question['validation_type'] == 'none'
        assert question['min_length'] is None
        assert question['max_length'] is None

    # ============================================================
    # تست‌های پروفایل‌های اعتبارسنجی
    # ============================================================

    def test_save_validation_profile(self, question_repo):
        """تست ذخیره پروفایل اعتبارسنجی"""
        settings = {
            'validation_type': 'phone',
            'is_required': 1,
            'min_length': 11,
            'max_length': 11,
        }

        result = question_repo.save_validation_profile('پروفایل تلفن', settings)
        assert result is True

        profile = question_repo.get_validation_profile_by_name('پروفایل تلفن')
        assert profile is not None
        assert profile['settings']['validation_type'] == 'phone'
        assert profile['settings']['is_required'] == 1

    def test_get_validation_profiles(self, question_repo):
        """تست دریافت لیست پروفایل‌های اعتبارسنجی"""
        question_repo.save_validation_profile('پروفایل ۱', {'type': 'text'})
        question_repo.save_validation_profile('پروفایل ۲', {'type': 'number'})

        profiles = question_repo.get_validation_profiles()
        assert len(profiles) >= 2
        names = [p['name'] for p in profiles]
        assert 'پروفایل ۱' in names
        assert 'پروفایل ۲' in names

    def test_apply_validation_profile(self, question_repo, sample_button_data):
        """تست اعمال پروفایل اعتبارسنجی به یک سوال"""
        # ایجاد پروفایل
        settings = {
            'validation_type': 'email',
            'is_required': 1,
            'min_length': 5,
            'max_length': 50,
            'validation_enabled': 1,
        }
        question_repo.save_validation_profile('پروفایل ایمیل', settings)

        # ایجاد سوال
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
        )

        result = question_repo.apply_validation_profile(question_id, 'پروفایل ایمیل')
        assert result is True

        question = question_repo.get_by_id(question_id)
        assert question['validation_type'] == 'email'
        assert question['is_required'] == 1
        assert question['min_length'] == 5
        assert question['max_length'] == 50
        assert question['validation_enabled'] == 1

    def test_apply_validation_profile_not_found(self, question_repo, sample_button_data):
        """تست اعمال پروفایل ناموجود"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال',
        )

        result = question_repo.apply_validation_profile(question_id, 'ناموجود')
        assert result is False

    def test_delete_validation_profile(self, question_repo):
        """تست حذف پروفایل اعتبارسنجی"""
        question_repo.save_validation_profile('پروفایل برای حذف', {'type': 'text'})

        result = question_repo.delete_validation_profile('پروفایل برای حذف')
        assert result is True

        profile = question_repo.get_validation_profile_by_name('پروفایل برای حذف')
        assert profile is None

    # ============================================================
    # تست‌های get_questions_with_options
    # ============================================================

    def test_get_questions_with_options(self, question_repo, sample_button_data):
        """تست دریافت سوالات یک دکمه به همراه گزینه‌ها"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۱',
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال ۲',
            needs_button=1,
        )

        # افزودن گزینه به سوال ۲
        question_repo.add_option(
            question_id=q2,
            option_text='گزینه ۱',
        )
        question_repo.add_option(
            question_id=q2,
            option_text='گزینه ۲',
        )

        questions = question_repo.get_questions_with_options(sample_button_data['id'])
        assert len(questions) == 2

        q2_found = next((q for q in questions if q['id'] == q2), None)
        assert q2_found is not None
        assert len(q2_found['options']) == 2

        q1_found = next((q for q in questions if q['id'] == q1), None)
        assert q1_found is not None
        assert len(q1_found['options']) == 0

    # ============================================================
    # تست‌های get_question_count_by_button
    # ============================================================

    def test_get_question_count_by_button(self, question_repo, sample_button_data):
        """تست تعداد سوالات یک دکمه"""
        for i in range(3):
            question_repo.create(
                button_id=sample_button_data['id'],
                question_text=f'سوال {i}',
            )

        count = question_repo.get_question_count_by_button(sample_button_data['id'])
        assert count == 3

    def test_get_question_count_by_button_with_inactive(self, question_repo, sample_button_data):
        """تست تعداد سوالات فعال یک دکمه (غیرفعال‌ها شمارش نشوند)"""
        question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال فعال',
            is_active=1,
        )
        question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال غیرفعال',
            is_active=0,
        )

        count = question_repo.get_question_count_by_button(sample_button_data['id'])
        assert count == 1

    # ============================================================
    # تست‌های get_options_count
    # ============================================================

    def test_get_options_count(self, question_repo, sample_button_data):
        """تست تعداد گزینه‌های یک سوال"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال با گزینه',
            needs_button=1,
        )

        for i in range(3):
            question_repo.add_option(
                question_id=question_id,
                option_text=f'گزینه {i}',
            )

        count = question_repo.get_options_count(question_id)
        assert count == 3

    def test_get_options_count_zero(self, question_repo, sample_button_data):
        """تست تعداد گزینه‌های یک سوال بدون گزینه"""
        question_id = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال بدون گزینه',
        )

        count = question_repo.get_options_count(question_id)
        assert count == 0

    # ============================================================
    # تست‌های get_conditions_count
    # ============================================================

    def test_get_conditions_count(self, question_repo, sample_button_data):
        """تست تعداد شرط‌های یک سوال"""
        q1 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال مرجع',
        )
        q2 = question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال شرطی',
        )

        for i in range(2):
            question_repo.add_condition(
                question_id=q2,
                condition_question_id=q1,
                condition_operator='==',
                condition_value=f'مقدار {i}',
            )

        count = question_repo.get_conditions_count(q2)
        assert count == 2

    # ============================================================
    # تست‌های custom_query
    # ============================================================

    def test_custom_query(self, question_repo, sample_button_data):
        """تست اجرای کوئری سفارشی"""
        for i in range(3):
            question_repo.create(
                button_id=sample_button_data['id'],
                question_text=f'سوال {i}',
            )

        results = question_repo.custom_query(
            "SELECT * FROM questions WHERE question_text LIKE ?",
            ['%سوال%']
        )
        assert len(results) >= 3

    def test_custom_query_one(self, question_repo, sample_button_data):
        """تست اجرای کوئری سفارشی و دریافت یک نتیجه"""
        question_repo.create(
            button_id=sample_button_data['id'],
            question_text='سوال خاص',
        )

        result = question_repo.custom_query_one(
            "SELECT * FROM questions WHERE question_text = ?",
            ['سوال خاص']
        )
        assert result is not None
        assert result['question_text'] == 'سوال خاص'

    # ============================================================
    # تست‌های error handling
    # ============================================================

    def test_update_question_not_found(self, question_repo):
        """تست به‌روزرسانی سوال ناموجود"""
        result = question_repo.update(99999, {'question_text': 'متن جدید'})
        assert result is False

    def test_delete_question_not_found(self, question_repo):
        """تست حذف سوال ناموجود"""
        result = question_repo.delete(99999)
        assert result is False

    def test_add_option_question_not_found(self, question_repo):
        """تست افزودن گزینه به سوال ناموجود"""
        option_id = question_repo.add_option(
            question_id=99999,
            option_text='گزینه',
        )
        assert option_id is None

    def test_add_condition_question_not_found(self, question_repo):
        """تست افزودن شرط به سوال ناموجود"""
        condition_id = question_repo.add_condition(
            question_id=99999,
            condition_question_id=1,
            condition_operator='==',
            condition_value='مقدار',
        )
        assert condition_id is None

    def test_update_validation_setting_not_found(self, question_repo):
        """تست به‌روزرسانی تنظیمات اعتبارسنجی سوال ناموجود"""
        result = question_repo.update_validation_settings(99999, {'validation_type': 'email'})
        assert result is False