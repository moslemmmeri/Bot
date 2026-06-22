# tests/test_services/test_template_service.py
# تست‌های واحد برای TemplateService

import pytest
import json
from unittest.mock import MagicMock, patch

from services.template_service import TemplateService


class TestTemplateService:
    """تست‌های TemplateService"""

    @pytest.fixture
    def template_service(self, db_connection):
        """ایجاد TemplateService با اتصال دیتابیس تست"""
        return TemplateService(db_connection)

    @pytest.fixture
    def sample_template_data(self):
        """داده‌های نمونه الگو"""
        return {
            'name': 'الگوی اطلاعات تماس',
            'description': 'الگوی دریافت اطلاعات تماس کاربر',
            'questions_data': [
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
            ],
            'created_by': 123456789
        }

    @pytest.fixture
    def sample_button_data(self):
        """داده‌های نمونه دکمه برای استخراج الگو"""
        return {
            'id': 1,
            'name': 'سرویس تست',
            'category_id': 1,
            'callback_data': 'btn_test',
            'is_active': 1,
        }

    @pytest.fixture
    def sample_questions_data(self):
        """داده‌های نمونه سوالات یک دکمه"""
        return [
            {
                'id': 1,
                'question_text': 'نام کامل:',
                'question_type': 'text',
                'is_required': 1,
                'validation_type': 'text',
                'needs_button': 0,
                'sort_order': 0,
                'options': [],
                'conditions': [],
            },
            {
                'id': 2,
                'question_text': 'شماره تماس:',
                'question_type': 'text',
                'is_required': 1,
                'validation_type': 'phone',
                'needs_button': 0,
                'sort_order': 1,
                'options': [],
                'conditions': [],
            }
        ]

    # ============================================================
    # تست‌های create_template
    # ============================================================

    def test_create_template_success(self, template_service, sample_template_data):
        """تست ایجاد الگوی جدید با موفقیت"""
        with patch.object(template_service, '_get_template_by_name', return_value=None):
            with patch.object(template_service, '_save_template', return_value=1) as mock_save:
                template_id = template_service.create_template(
                    name=sample_template_data['name'],
                    description=sample_template_data['description'],
                    questions_data=sample_template_data['questions_data'],
                    created_by=sample_template_data['created_by']
                )

                assert template_id == 1
                mock_save.assert_called_once()

    def test_create_template_duplicate_name(self, template_service, sample_template_data):
        """تست ایجاد الگو با نام تکراری"""
        with patch.object(template_service, '_get_template_by_name', return_value={'id': 1, 'name': sample_template_data['name']}):
            template_id = template_service.create_template(
                name=sample_template_data['name'],
                description=sample_template_data['description'],
                questions_data=sample_template_data['questions_data'],
                created_by=sample_template_data['created_by']
            )

            assert template_id is None

    def test_create_template_empty_questions(self, template_service, sample_template_data):
        """تست ایجاد الگو با سوالات خالی"""
        template_id = template_service.create_template(
            name=sample_template_data['name'],
            description=sample_template_data['description'],
            questions_data=[],
            created_by=sample_template_data['created_by']
        )

        assert template_id is None

    # ============================================================
    # تست‌های get_template
    # ============================================================

    def test_get_template_by_id(self, template_service):
        """تست دریافت الگو با شناسه"""
        expected_template = {
            'id': 1,
            'name': 'الگوی تست',
            'description': 'توضیحات',
            'questions_data': '[]',
            'created_by': 123,
            'created_at': '2024-01-01 12:00:00',
            'updated_at': '2024-01-01 12:00:00',
        }

        with patch.object(template_service, '_get_template_by_id', return_value=expected_template):
            template = template_service.get_template(1)
            assert template is not None
            assert template['id'] == 1
            assert template['name'] == 'الگوی تست'

    def test_get_template_not_found(self, template_service):
        """تست دریافت الگوی ناموجود"""
        with patch.object(template_service, '_get_template_by_id', return_value=None):
            template = template_service.get_template(999)
            assert template is None

    def test_get_template_by_name(self, template_service):
        """تست دریافت الگو با نام"""
        expected_template = {
            'id': 1,
            'name': 'الگوی تست',
            'description': 'توضیحات',
            'questions_data': '[]',
        }

        with patch.object(template_service, '_get_template_by_name', return_value=expected_template):
            template = template_service.get_template_by_name('الگوی تست')
            assert template is not None
            assert template['name'] == 'الگوی تست'

    # ============================================================
    # تست‌های get_all_templates
    # ============================================================

    def test_get_all_templates(self, template_service):
        """تست دریافت لیست تمام الگوها"""
        expected_templates = [
            {'id': 1, 'name': 'الگوی ۱', 'description': 'توضیحات ۱'},
            {'id': 2, 'name': 'الگوی ۲', 'description': 'توضیحات ۲'},
        ]

        with patch.object(template_service, '_get_templates', return_value=expected_templates):
            templates = template_service.get_all_templates()
            assert len(templates) == 2
            assert templates[0]['name'] == 'الگوی ۱'

    def test_get_templates_count(self, template_service):
        """تست تعداد الگوها"""
        with patch.object(template_service, '_get_templates', return_value=[{}, {}, {}]):
            count = template_service.get_templates_count()
            assert count == 3

    # ============================================================
    # تست‌های update_template
    # ============================================================

    def test_update_template_success(self, template_service, sample_template_data):
        """تست بروزرسانی الگو با موفقیت"""
        with patch.object(template_service, '_get_template_by_id', return_value={'id': 1}):
            with patch.object(template_service, '_get_template_by_name', return_value=None):
                with patch.object(template_service, '_update_template', return_value=True) as mock_update:
                    result = template_service.update_template(
                        template_id=1,
                        name='نام جدید',
                        description='توضیحات جدید',
                        questions_data=sample_template_data['questions_data']
                    )

                    assert result is True
                    mock_update.assert_called_once()

    def test_update_template_not_found(self, template_service, sample_template_data):
        """تست بروزرسانی الگوی ناموجود"""
        with patch.object(template_service, '_get_template_by_id', return_value=None):
            result = template_service.update_template(
                template_id=999,
                name='نام جدید',
                description='توضیحات جدید',
                questions_data=sample_template_data['questions_data']
            )

            assert result is False

    def test_update_template_duplicate_name(self, template_service, sample_template_data):
        """تست بروزرسانی با نام تکراری"""
        with patch.object(template_service, '_get_template_by_id', return_value={'id': 1}):
            with patch.object(template_service, '_get_template_by_name', return_value={'id': 2, 'name': 'نام جدید'}):
                result = template_service.update_template(
                    template_id=1,
                    name='نام جدید',
                    description='توضیحات جدید',
                    questions_data=sample_template_data['questions_data']
                )

                assert result is False

    def test_update_template_empty_questions(self, template_service):
        """تست بروزرسانی با سوالات خالی"""
        with patch.object(template_service, '_get_template_by_id', return_value={'id': 1}):
            result = template_service.update_template(
                template_id=1,
                name='نام جدید',
                description='توضیحات جدید',
                questions_data=[]
            )

            assert result is False

    # ============================================================
    # تست‌های delete_template
    # ============================================================

    def test_delete_template_success(self, template_service):
        """تست حذف الگو با موفقیت"""
        with patch.object(template_service, '_get_template_by_id', return_value={'id': 1}):
            with patch.object(template_service, '_delete_template', return_value=True) as mock_delete:
                result = template_service.delete_template(1)
                assert result is True
                mock_delete.assert_called_once_with(1)

    def test_delete_template_not_found(self, template_service):
        """تست حذف الگوی ناموجود"""
        with patch.object(template_service, '_get_template_by_id', return_value=None):
            result = template_service.delete_template(999)
            assert result is False

    # ============================================================
    # تست‌های copy_template
    # ============================================================

    def test_copy_template_success(self, template_service, sample_template_data):
        """تست کپی الگو با موفقیت"""
        template = {
            'id': 1,
            'name': 'الگوی اصلی',
            'description': 'توضیحات',
            'questions_data': json.dumps(sample_template_data['questions_data']),
            'created_by': 123,
        }

        with patch.object(template_service, '_get_template_by_id', return_value=template):
            with patch.object(template_service, '_get_template_by_name', return_value=None):
                with patch.object(template_service, '_save_template', return_value=2) as mock_save:
                    new_id = template_service.copy_template(
                        template_id=1,
                        new_name='الگوی کپی شده',
                        created_by=456
                    )

                    assert new_id == 2
                    mock_save.assert_called_once()

    def test_copy_template_not_found(self, template_service):
        """تست کپی الگوی ناموجود"""
        with patch.object(template_service, '_get_template_by_id', return_value=None):
            new_id = template_service.copy_template(
                template_id=999,
                new_name='الگوی جدید',
                created_by=123
            )

            assert new_id is None

    def test_copy_template_duplicate_name(self, template_service):
        """تست کپی الگو با نام تکراری"""
        template = {'id': 1, 'name': 'الگوی اصلی', 'questions_data': '[]', 'description': ''}

        with patch.object(template_service, '_get_template_by_id', return_value=template):
            with patch.object(template_service, '_get_template_by_name', return_value={'id': 2}):
                new_id = template_service.copy_template(
                    template_id=1,
                    new_name='الگوی تکراری',
                    created_by=123
                )

                assert new_id is None

    # ============================================================
    # تست‌های extract_from_button
    # ============================================================

    def test_extract_from_button_success(self, template_service, sample_button_data, sample_questions_data):
        """تست استخراج الگو از دکمه با موفقیت"""
        with patch.object(template_service, '_button_repo') as mock_button_repo:
            mock_button_repo.get_by_id.return_value = sample_button_data

            with patch.object(template_service, '_question_repo') as mock_question_repo:
                mock_question_repo.get_by_button.return_value = sample_questions_data
                mock_question_repo.get_options.return_value = []
                mock_question_repo.get_conditions.return_value = []

                with patch.object(template_service, '_get_template_by_name', return_value=None):
                    with patch.object(template_service, '_save_template', return_value=1) as mock_save:
                        template_id = template_service.extract_from_button(
                            button_id=1,
                            template_name='الگوی استخراج شده',
                            description='توضیحات',
                            created_by=123
                        )

                        assert template_id == 1
                        mock_save.assert_called_once()

    def test_extract_from_button_not_found(self, template_service):
        """تست استخراج الگو از دکمه ناموجود"""
        with patch.object(template_service, '_button_repo') as mock_button_repo:
            mock_button_repo.get_by_id.return_value = None

            template_id = template_service.extract_from_button(
                button_id=999,
                template_name='الگوی تست',
                description='توضیحات',
                created_by=123
            )

            assert template_id is None

    def test_extract_from_button_no_questions(self, template_service, sample_button_data):
        """تست استخراج الگو از دکمه بدون سوال"""
        with patch.object(template_service, '_button_repo') as mock_button_repo:
            mock_button_repo.get_by_id.return_value = sample_button_data

            with patch.object(template_service, '_question_repo') as mock_question_repo:
                mock_question_repo.get_by_button.return_value = []

                template_id = template_service.extract_from_button(
                    button_id=1,
                    template_name='الگوی تست',
                    description='توضیحات',
                    created_by=123
                )

                assert template_id is None

    def test_extract_from_button_duplicate_name(self, template_service, sample_button_data, sample_questions_data):
        """تست استخراج الگو با نام تکراری"""
        with patch.object(template_service, '_button_repo') as mock_button_repo:
            mock_button_repo.get_by_id.return_value = sample_button_data

            with patch.object(template_service, '_question_repo') as mock_question_repo:
                mock_question_repo.get_by_button.return_value = sample_questions_data
                mock_question_repo.get_options.return_value = []
                mock_question_repo.get_conditions.return_value = []

                with patch.object(template_service, '_get_template_by_name', return_value={'id': 2}):
                    template_id = template_service.extract_from_button(
                        button_id=1,
                        template_name='الگوی تکراری',
                        description='توضیحات',
                        created_by=123
                    )

                    assert template_id is None

    # ============================================================
    # تست‌های apply_template_to_button
    # ============================================================

    def test_apply_template_to_button_success(self, template_service):
        """تست اعمال الگو به دکمه با موفقیت"""
        template = {
            'id': 1,
            'name': 'الگوی تست',
            'questions_data': json.dumps([
                {
                    'question_text': 'سوال ۱',
                    'question_type': 'text',
                    'is_required': 1,
                    'validation_type': 'text',
                    'needs_button': 0,
                    'sort_order': 0,
                    'options': [],
                    'conditions': [],
                }
            ])
        }

        with patch.object(template_service, '_get_template_by_id', return_value=template):
            with patch.object(template_service, '_button_repo') as mock_button_repo:
                mock_button_repo.get_by_id.return_value = {'id': 1, 'name': 'دکمه تست'}

                with patch.object(template_service, '_question_repo') as mock_question_repo:
                    mock_question_repo.get_by_button.return_value = []
                    mock_question_repo.create.return_value = 1
                    mock_question_repo.add_option.return_value = None
                    mock_question_repo.add_condition.return_value = None

                    result = template_service.apply_template_to_button(
                        template_id=1,
                        button_id=1
                    )

                    assert result is True

    def test_apply_template_to_button_not_found(self, template_service):
        """تست اعمال الگوی ناموجود به دکمه"""
        with patch.object(template_service, '_get_template_by_id', return_value=None):
            result = template_service.apply_template_to_button(
                template_id=999,
                button_id=1
            )

            assert result is False

    def test_apply_template_to_button_no_questions(self, template_service):
        """تست اعمال الگوی بدون سوال به دکمه"""
        template = {
            'id': 1,
            'name': 'الگوی خالی',
            'questions_data': '[]'
        }

        with patch.object(template_service, '_get_template_by_id', return_value=template):
            result = template_service.apply_template_to_button(
                template_id=1,
                button_id=1
            )

            assert result is False

    # ============================================================
    # تست‌های validate_template_data
    # ============================================================

    def test_validate_template_data_success(self, template_service, sample_template_data):
        """تست اعتبارسنجی داده‌های الگو با موفقیت"""
        is_valid, error = template_service.validate_template_data(
            sample_template_data['questions_data']
        )

        assert is_valid is True
        assert error == ""

    def test_validate_template_data_empty(self, template_service):
        """تست اعتبارسنجی داده‌های الگوی خالی"""
        is_valid, error = template_service.validate_template_data([])

        assert is_valid is False
        assert "حداقل یک سوال" in error

    def test_validate_template_data_missing_text(self, template_service):
        """تست اعتبارسنجی سوال بدون متن"""
        questions = [
            {
                'question_text': '',
                'question_type': 'text',
                'is_required': 1,
            }
        ]

        is_valid, error = template_service.validate_template_data(questions)

        assert is_valid is False
        assert "متن ندارد" in error

    def test_validate_template_data_button_without_options(self, template_service):
        """تست اعتبارسنجی سوال دکمه‌ای بدون گزینه"""
        questions = [
            {
                'question_text': 'سوال تست',
                'question_type': 'text',
                'needs_button': 1,
                'options': [],
                'is_required': 1,
            }
        ]

        is_valid, error = template_service.validate_template_data(questions)

        assert is_valid is False
        assert "حداقل ۲ گزینه" in error

    # ============================================================
    # تست‌های get_template_questions_count
    # ============================================================

    def test_get_template_questions_count(self, template_service):
        """تست تعداد سوالات یک الگو"""
        template = {
            'id': 1,
            'questions_data': json.dumps([
                {'question_text': 'سوال ۱'},
                {'question_text': 'سوال ۲'},
                {'question_text': 'سوال ۳'},
            ])
        }

        with patch.object(template_service, '_get_template_by_id', return_value=template):
            count = template_service.get_template_questions_count(1)
            assert count == 3

    def test_get_template_questions_count_not_found(self, template_service):
        """تست تعداد سوالات الگوی ناموجود"""
        with patch.object(template_service, '_get_template_by_id', return_value=None):
            count = template_service.get_template_questions_count(999)
            assert count == 0

    # ============================================================
    # تست‌های search_templates
    # ============================================================

    def test_search_templates_success(self, template_service):
        """تست جستجوی الگوها با موفقیت"""
        templates = [
            {'name': 'الگوی اطلاعات تماس', 'description': 'دریافت اطلاعات تماس'},
            {'name': 'الگوی درخواست خدمات', 'description': 'دریافت درخواست خدمات'},
            {'name': 'الگوی پرداخت', 'description': 'دریافت اطلاعات پرداخت'},
        ]

        with patch.object(template_service, '_get_templates', return_value=templates):
            results = template_service.search_templates('تماس')
            assert len(results) == 1
            assert results[0]['name'] == 'الگوی اطلاعات تماس'

    def test_search_templates_no_result(self, template_service):
        """تست جستجوی الگوها بدون نتیجه"""
        templates = [
            {'name': 'الگوی ۱', 'description': 'توضیحات ۱'},
            {'name': 'الگوی ۲', 'description': 'توضیحات ۲'},
        ]

        with patch.object(template_service, '_get_templates', return_value=templates):
            results = template_service.search_templates('ناموجود')
            assert len(results) == 0

    # ============================================================
    # تست‌های get_template_preview
    # ============================================================

    def test_get_template_preview_success(self, template_service):
        """تست دریافت پیش‌نمایش الگو با موفقیت"""
        template = {
            'id': 1,
            'name': 'الگوی تست',
            'description': 'توضیحات',
            'questions_data': json.dumps([
                {'question_text': 'سوال ۱', 'question_type': 'text'},
                {'question_text': 'سوال ۲', 'question_type': 'text'},
            ]),
            'created_by': 123,
            'created_at': '2024-01-01 12:00:00',
            'updated_at': '2024-01-01 12:00:00',
        }

        with patch.object(template_service, '_get_template_by_id', return_value=template):
            preview = template_service.get_template_preview(1)

            assert preview is not None
            assert preview['id'] == 1
            assert preview['name'] == 'الگوی تست'
            assert preview['question_count'] == 2
            assert len(preview['questions']) == 2

    def test_get_template_preview_not_found(self, template_service):
        """تست دریافت پیش‌نمایش الگوی ناموجود"""
        with patch.object(template_service, '_get_template_by_id', return_value=None):
            preview = template_service.get_template_preview(999)
            assert 'error' in preview

    # ============================================================
    # تست‌های init_default_templates
    # ============================================================

    def test_init_default_templates_when_empty(self, template_service):
        """تست مقداردهی اولیه الگوهای پیش‌فرض در صورت خالی بودن"""
        with patch.object(template_service, '_get_templates', return_value=[]):
            with patch.object(template_service, '_save_template', return_value=1) as mock_save:
                template_service.init_default_templates()

                # حداقل یک الگو باید ذخیره شود
                assert mock_save.call_count >= 1

    def test_init_default_templates_when_existing(self, template_service):
        """تست مقداردهی اولیه الگوهای پیش‌فرض در صورت موجود بودن"""
        with patch.object(template_service, '_get_templates', return_value=[{'id': 1}]):
            with patch.object(template_service, '_save_template') as mock_save:
                template_service.init_default_templates()

                # نباید الگویی ذخیره شود
                mock_save.assert_not_called()

    # ============================================================
    # تست‌های متدهای خصوصی (از طریق متدهای عمومی)
    # ============================================================

    def test_get_template_preview_with_questions_data(self, template_service):
        """تست دریافت پیش‌نمایش با داده‌های سوالات"""
        template = {
            'id': 1,
            'name': 'الگوی تست',
            'description': 'توضیحات',
            'questions_data': json.dumps([
                {'question_text': 'سوال ۱', 'question_type': 'text', 'is_required': 1},
                {'question_text': 'سوال ۲', 'question_type': 'button', 'needs_button': 1},
            ]),
        }

        with patch.object(template_service, '_get_template_by_id', return_value=template):
            preview = template_service.get_template_preview(1)

            assert preview is not None
            assert preview['question_count'] == 2
            assert preview['questions'][0]['question_text'] == 'سوال ۱'
            assert preview['questions'][1]['question_text'] == 'سوال ۲'

    # ============================================================
    # تست‌های error handling
    # ============================================================

    def test_apply_template_to_button_with_existing_questions(self, template_service):
        """تست اعمال الگو به دکمه با سوالات موجود (حذف و جایگزینی)"""
        template = {
            'id': 1,
            'questions_data': json.dumps([
                {'question_text': 'سوال جدید', 'question_type': 'text', 'is_required': 1}
            ])
        }

        with patch.object(template_service, '_get_template_by_id', return_value=template):
            with patch.object(template_service, '_button_repo') as mock_button_repo:
                mock_button_repo.get_by_id.return_value = {'id': 1}

                with patch.object(template_service, '_question_repo') as mock_question_repo:
                    # سوالات موجود
                    mock_question_repo.get_by_button.return_value = [
                        {'id': 10, 'question_text': 'سوال قدیمی'},
                        {'id': 11, 'question_text': 'سوال قدیمی ۲'},
                    ]
                    # متدهای حذف
                    mock_question_repo.delete_options_by_question.return_value = None
                    mock_question_repo.delete_conditions_by_question.return_value = None
                    mock_question_repo.delete.return_value = None
                    # ایجاد سوال جدید
                    mock_question_repo.create.return_value = 20

                    result = template_service.apply_template_to_button(1, 1)

                    assert result is True
                    # بررسی اینکه سوالات قدیمی حذف شده‌اند
                    assert mock_question_repo.delete.call_count >= 2
                    # بررسی اینکه سوال جدید ایجاد شده
                    mock_question_repo.create.assert_called_once()