# tests/test_repositories/test_category_repository.py
# تست‌های واحد برای CategoryRepository

import pytest
from unittest.mock import MagicMock, patch

from repositories.category_repository import CategoryRepository


class TestCategoryRepository:
    """تست‌های CategoryRepository"""

    @pytest.fixture
    def category_repo(self, db_connection):
        """ایجاد CategoryRepository با اتصال دیتابیس تست"""
        return CategoryRepository(db_connection)

    @pytest.fixture
    def sample_category_data(self):
        """داده‌های نمونه دسته‌بندی"""
        return {
            'name': 'دسته تست',
            'icon': '📁',
            'location': 'main',
            'sort_order': 0,
            'columns': 2,
        }

    # ============================================================
    # تست‌های create
    # ============================================================

    def test_create_category_success(self, category_repo, sample_category_data):
        """تست ایجاد دسته‌بندی با موفقیت"""
        category_id = category_repo.create(
            name=sample_category_data['name'],
            icon=sample_category_data['icon'],
            location=sample_category_data['location'],
            sort_order=sample_category_data['sort_order'],
            columns=sample_category_data['columns'],
        )

        assert category_id is not None
        assert category_id > 0

        # دریافت دسته‌بندی ایجادشده
        category = category_repo.get_by_id(category_id)
        assert category is not None
        assert category['name'] == sample_category_data['name']
        assert category['icon'] == sample_category_data['icon']
        assert category['location'] == sample_category_data['location']
        assert category['sort_order'] == sample_category_data['sort_order']
        assert category['columns'] == sample_category_data['columns']
        assert category['is_active'] == 1

    def test_create_category_with_defaults(self, category_repo):
        """تست ایجاد دسته‌بندی با مقادیر پیش‌فرض"""
        category_id = category_repo.create(
            name='دسته پیش‌فرض',
        )

        assert category_id is not None
        category = category_repo.get_by_id(category_id)
        assert category['icon'] == '📁'
        assert category['location'] == 'main'
        assert category['sort_order'] == 0
        assert category['columns'] == 2

    def test_create_category_without_name(self, category_repo):
        """تست ایجاد دسته‌بندی بدون نام (باید خطا دهد)"""
        with pytest.raises(Exception):
            category_repo.create(name=None)

    # ============================================================
    # تست‌های get_by_id
    # ============================================================

    def test_get_by_id_success(self, category_repo, sample_category_data):
        """تست دریافت دسته‌بندی با شناسه"""
        category_id = category_repo.create(
            name=sample_category_data['name'],
        )

        category = category_repo.get_by_id(category_id)
        assert category is not None
        assert category['id'] == category_id
        assert category['name'] == sample_category_data['name']

    def test_get_by_id_not_found(self, category_repo):
        """تست دریافت دسته‌بندی ناموجود"""
        category = category_repo.get_by_id(99999)
        assert category is None

    # ============================================================
    # تست‌های get_by_location
    # ============================================================

    def test_get_by_location_success(self, category_repo, sample_category_data):
        """تست دریافت دسته‌بندی بر اساس مکان"""
        category_repo.create(
            name='دسته اصلی',
            location='main',
        )
        category_repo.create(
            name='دسته بیشتر',
            location='more',
        )
        category_repo.create(
            name='دسته دیگر',
            location='other',
        )

        main_category = category_repo.get_by_location('main')
        assert main_category is not None
        assert main_category['location'] == 'main'
        assert main_category['name'] == 'دسته اصلی'

        more_category = category_repo.get_by_location('more')
        assert more_category is not None
        assert more_category['location'] == 'more'
        assert more_category['name'] == 'دسته بیشتر'

    def test_get_by_location_not_found(self, category_repo):
        """تست دریافت دسته‌بندی با مکان ناموجود"""
        category = category_repo.get_by_location('invalid')
        assert category is None

    # ============================================================
    # تست‌های get_all
    # ============================================================

    def test_get_all_categories(self, category_repo, sample_category_data):
        """تست دریافت تمام دسته‌بندی‌ها"""
        for i in range(3):
            category_repo.create(
                name=f'دسته {i}',
                location='main' if i % 2 == 0 else 'more',
            )

        categories = category_repo.get_all()
        assert len(categories) >= 3

    def test_get_all_with_pagination(self, category_repo):
        """تست دریافت تمام دسته‌بندی‌ها با صفحه‌بندی"""
        for i in range(10):
            category_repo.create(
                name=f'دسته {i}',
            )

        page_1 = category_repo.get_all(limit=3, offset=0)
        page_2 = category_repo.get_all(limit=3, offset=3)

        assert len(page_1) == 3
        assert len(page_2) == 3
        assert page_1[0]['id'] != page_2[0]['id']

    def test_get_all_with_order(self, category_repo):
        """تست دریافت تمام دسته‌بندی‌ها با مرتب‌سازی"""
        category_repo.create(name='دسته ۱', sort_order=10)
        category_repo.create(name='دسته ۲', sort_order=5)
        category_repo.create(name='دسته ۳', sort_order=1)

        categories = category_repo.get_all(order_by='sort_order')
        # باید بر اساس sort_order صعودی مرتب شده باشد
        assert categories[0]['sort_order'] == 1
        assert categories[1]['sort_order'] == 5
        assert categories[2]['sort_order'] == 10

    # ============================================================
    # تست‌های get_active
    # ============================================================

    def test_get_active_categories(self, category_repo):
        """تست دریافت دسته‌بندی‌های فعال"""
        category_repo.create(name='دسته فعال ۱', is_active=True)
        category_repo.create(name='دسته فعال ۲', is_active=True)
        category_repo.create(name='دسته غیرفعال', is_active=False)

        active = category_repo.get_active()
        assert len(active) >= 2
        for cat in active:
            assert cat['is_active'] == 1

    # ============================================================
    # تست‌های get_all_admin
    # ============================================================

    def test_get_all_admin(self, category_repo):
        """تست دریافت همه دسته‌بندی‌ها برای پنل مدیریت"""
        for i in range(5):
            category_repo.create(name=f'دسته {i}')

        categories = category_repo.get_all_admin()
        assert len(categories) == 5

    # ============================================================
    # تست‌های get_with_buttons
    # ============================================================

    def test_get_with_buttons(self, category_repo):
        """تست دریافت دسته‌بندی‌هایی که حداقل یک دکمه دارند"""
        # ایجاد دسته‌بندی با دکمه
        cat1_id = category_repo.create(name='دسته با دکمه')
        with category_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat1_id, 'دکمه تست', 'btn_test', 1)
            )
            category_repo.connection.commit()

        # ایجاد دسته‌بندی بدون دکمه
        cat2_id = category_repo.create(name='دسته بدون دکمه')

        categories = category_repo.get_with_buttons()
        assert len(categories) >= 1
        # باید دسته‌بندی با دکمه برگردد
        cat_ids = [c['id'] for c in categories]
        assert cat1_id in cat_ids
        assert cat2_id not in cat_ids

    def test_get_with_buttons_by_location(self, category_repo):
        """تست دریافت دسته‌بندی‌های دارای دکمه بر اساس مکان"""
        # ایجاد دسته‌بندی main با دکمه
        cat1_id = category_repo.create(name='دسته main', location='main')
        with category_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat1_id, 'دکمه main', 'btn_main', 1)
            )
            category_repo.connection.commit()

        # ایجاد دسته‌بندی more با دکمه
        cat2_id = category_repo.create(name='دسته more', location='more')
        with category_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat2_id, 'دکمه more', 'btn_more', 1)
            )
            category_repo.connection.commit()

        # ایجاد دسته‌بندی main بدون دکمه
        cat3_id = category_repo.create(name='دسته main خالی', location='main')

        main_categories = category_repo.get_with_buttons(location='main')
        cat_ids = [c['id'] for c in main_categories]
        assert cat1_id in cat_ids
        assert cat3_id not in cat_ids

    # ============================================================
    # تست‌های get_with_button_count
    # ============================================================

    def test_get_with_button_count(self, category_repo):
        """تست دریافت دسته‌بندی‌ها با تعداد دکمه‌ها"""
        cat1_id = category_repo.create(name='دسته ۱')
        cat2_id = category_repo.create(name='دسته ۲')

        # افزودن دکمه به دسته‌بندی ۱
        with category_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat1_id, 'دکمه ۱', 'btn_1', 1)
            )
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat1_id, 'دکمه ۲', 'btn_2', 1)
            )
            category_repo.connection.commit()

        categories = category_repo.get_with_button_count()
        # پیدا کردن دسته‌بندی مورد نظر
        cat1 = next((c for c in categories if c['id'] == cat1_id), None)
        cat2 = next((c for c in categories if c['id'] == cat2_id), None)

        assert cat1 is not None
        assert cat2 is not None
        assert cat1['button_count'] == 2
        assert cat2['button_count'] == 0

    # ============================================================
    # تست‌های get_buttons_count
    # ============================================================

    def test_get_buttons_count(self, category_repo):
        """تست تعداد دکمه‌های فعال یک دسته‌بندی"""
        cat_id = category_repo.create(name='دسته تست')

        with category_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat_id, 'دکمه ۱', 'btn_1', 1)
            )
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat_id, 'دکمه ۲', 'btn_2', 1)
            )
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat_id, 'دکمه غیرفعال', 'btn_inactive', 0)
            )
            category_repo.connection.commit()

        count = category_repo.get_buttons_count(cat_id)
        # فقط دکمه‌های فعال باید شمارش شوند
        assert count == 2

    # ============================================================
    # تست‌های update
    # ============================================================

    def test_update_category_name(self, category_repo, sample_category_data):
        """تست تغییر نام دسته‌بندی"""
        category_id = category_repo.create(
            name='نام قدیم',
            icon='📁',
        )

        result = category_repo.update_name(category_id, 'نام جدید')
        assert result is True

        category = category_repo.get_by_id(category_id)
        assert category['name'] == 'نام جدید'

    def test_update_category_icon(self, category_repo):
        """تست تغییر آیکون دسته‌بندی"""
        category_id = category_repo.create(
            name='دسته',
            icon='📁',
        )

        result = category_repo.update_icon(category_id, '🌟')
        assert result is True

        category = category_repo.get_by_id(category_id)
        assert category['icon'] == '🌟'

    def test_update_category_location(self, category_repo):
        """تست تغییر مکان دسته‌بندی"""
        category_id = category_repo.create(
            name='دسته',
            location='main',
        )

        result = category_repo.update_location(category_id, 'more')
        assert result is True

        category = category_repo.get_by_id(category_id)
        assert category['location'] == 'more'

    def test_update_category_location_invalid(self, category_repo):
        """تست تغییر مکان دسته‌بندی با مقدار نامعتبر"""
        category_id = category_repo.create(name='دسته')

        result = category_repo.update_location(category_id, 'invalid')
        assert result is False

    def test_update_category_columns(self, category_repo):
        """تست تغییر تعداد ستون‌های دسته‌بندی"""
        category_id = category_repo.create(
            name='دسته',
            columns=2,
        )

        result = category_repo.update_columns(category_id, 4)
        assert result is True

        category = category_repo.get_by_id(category_id)
        assert category['columns'] == 4

    def test_update_category_columns_invalid(self, category_repo):
        """تست تغییر تعداد ستون‌ها با مقدار نامعتبر"""
        category_id = category_repo.create(name='دسته')

        result = category_repo.update_columns(category_id, 9)  # بیشتر از ۸
        assert result is False

    def test_toggle_active(self, category_repo):
        """تست تغییر وضعیت فعال/غیرفعال دسته‌بندی"""
        category_id = category_repo.create(
            name='دسته',
            is_active=1,
        )

        result = category_repo.toggle_active(category_id)
        assert result is True

        category = category_repo.get_by_id(category_id)
        assert category['is_active'] == 0

        result = category_repo.toggle_active(category_id)
        assert result is True
        category = category_repo.get_by_id(category_id)
        assert category['is_active'] == 1

    def test_update_sort_order(self, category_repo):
        """تست تغییر ترتیب نمایش دسته‌بندی"""
        category_id = category_repo.create(
            name='دسته',
            sort_order=5,
        )

        result = category_repo.update_sort_order(category_id, 10)
        assert result is True

        category = category_repo.get_by_id(category_id)
        assert category['sort_order'] == 10

    # ============================================================
    # تست‌های delete
    # ============================================================

    def test_delete_category_success(self, category_repo):
        """تست حذف دسته‌بندی با موفقیت"""
        category_id = category_repo.create(name='دسته برای حذف')

        result = category_repo.delete(category_id)
        assert result is True

        category = category_repo.get_by_id(category_id)
        assert category is None

    def test_delete_category_with_buttons(self, category_repo):
        """تست حذف دسته‌بندی با دکمه‌های مرتبط (کاسکید)"""
        cat_id = category_repo.create(name='دسته با دکمه')

        # افزودن دکمه
        with category_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data) VALUES (?, ?, ?)",
                (cat_id, 'دکمه', 'btn_test')
            )
            button_id = cursor.get_lastrowid()
            category_repo.connection.commit()

        result = category_repo.delete(cat_id)
        assert result is True

        # بررسی اینکه دسته‌بندی و دکمه حذف شده‌اند
        category = category_repo.get_by_id(cat_id)
        assert category is None

        # بررسی دکمه
        with category_repo.connection.get_cursor() as cursor:
            cursor.execute("SELECT * FROM buttons WHERE id = ?", (button_id,))
            button = cursor.fetchone()
            assert button is None

    def test_delete_category_not_found(self, category_repo):
        """تست حذف دسته‌بندی ناموجود"""
        result = category_repo.delete(99999)
        assert result is False

    # ============================================================
    # تست‌های get_max_sort_order
    # ============================================================

    def test_get_max_sort_order(self, category_repo):
        """تست دریافت حداکثر sort_order در دسته‌بندی‌ها"""
        category_repo.create(name='دسته ۱', sort_order=3)
        category_repo.create(name='دسته ۲', sort_order=7)
        category_repo.create(name='دسته ۳', sort_order=1)

        max_order = category_repo.get_max_sort_order()
        assert max_order == 7

    def test_get_max_sort_order_empty(self, category_repo):
        """تست دریافت حداکثر sort_order در صورت خالی بودن"""
        max_order = category_repo.get_max_sort_order()
        assert max_order == -1

    # ============================================================
    # تست‌های get_default_categories
    # ============================================================

    def test_get_default_categories(self, category_repo):
        """تست دریافت دسته‌بندی‌های پیش‌فرض"""
        # ایجاد دسته‌بندی‌های اصلی
        category_repo.create(name='منوی اصلی', location='main')
        category_repo.create(name='منوی بیشتر', location='more')
        category_repo.create(name='دیگر خدمات', location='other')

        defaults = category_repo.get_default_categories()
        assert len(defaults) >= 3
        locations = [c['location'] for c in defaults]
        assert 'main' in locations
        assert 'more' in locations
        assert 'other' in locations

    # ============================================================
    # تست‌های get_category_location_counts
    # ============================================================

    def test_get_category_location_counts(self, category_repo):
        """تست تعداد دسته‌بندی‌ها در هر مکان"""
        category_repo.create(name='دسته ۱', location='main')
        category_repo.create(name='دسته ۲', location='main')
        category_repo.create(name='دسته ۳', location='more')
        category_repo.create(name='دسته ۴', location='other')

        counts = category_repo.get_category_location_counts()
        assert counts['main'] == 2
        assert counts['more'] == 1
        assert counts['other'] == 1

    # ============================================================
    # تست‌های get_category_by_name
    # ============================================================

    def test_get_category_by_name(self, category_repo):
        """تست دریافت دسته‌بندی بر اساس نام"""
        category_repo.create(name='دسته خاص', location='main')

        category = category_repo.get_category_by_name('دسته خاص')
        assert category is not None
        assert category['name'] == 'دسته خاص'

    def test_get_category_by_name_with_location(self, category_repo):
        """تست دریافت دسته‌بندی بر اساس نام و مکان"""
        category_repo.create(name='دسته مشترک', location='main')
        category_repo.create(name='دسته مشترک', location='more')

        category = category_repo.get_category_by_name('دسته مشترک', location='main')
        assert category is not None
        assert category['location'] == 'main'

        category = category_repo.get_category_by_name('دسته مشترک', location='more')
        assert category is not None
        assert category['location'] == 'more'

    def test_get_category_by_name_not_found(self, category_repo):
        """تست دریافت دسته‌بندی با نام ناموجود"""
        category = category_repo.get_category_by_name('نام ناموجود')
        assert category is None

    # ============================================================
    # تست‌های get_categories_with_effective_columns
    # ============================================================

    def test_get_categories_with_effective_columns(self, category_repo):
        """تست دریافت دسته‌بندی‌ها با ستون‌های مؤثر"""
        cat1_id = category_repo.create(name='دسته ۱', columns=3)
        cat2_id = category_repo.create(name='دسته ۲', columns=None)

        with patch('database.db_columns.get_effective_columns') as mock_effective:
            mock_effective.side_effect = lambda category_id=None, **kwargs: 3 if category_id == cat1_id else 2

            categories = category_repo.get_categories_with_effective_columns()
            assert len(categories) >= 2

            cat1 = next((c for c in categories if c['id'] == cat1_id), None)
            cat2 = next((c for c in categories if c['id'] == cat2_id), None)

            assert cat1 is not None
            assert cat2 is not None
            assert cat1['effective_columns'] == 3
            assert cat1['has_custom_columns'] is True
            assert cat2['effective_columns'] == 2
            assert cat2['has_custom_columns'] is False

    # ============================================================
    # تست‌های ensure_default_categories
    # ============================================================

    def test_ensure_default_categories_when_empty(self, category_repo):
        """تست ایجاد دسته‌بندی‌های پیش‌فرض در صورت خالی بودن"""
        # حذف همه دسته‌بندی‌ها
        with category_repo.connection.get_cursor() as cursor:
            cursor.execute("DELETE FROM categories")
            category_repo.connection.commit()

        category_repo.ensure_default_categories()

        # بررسی وجود دسته‌بندی‌های پیش‌فرض
        categories = category_repo.get_all()
        assert len(categories) >= 3
        locations = [c['location'] for c in categories]
        assert 'main' in locations
        assert 'more' in locations
        assert 'other' in locations

    def test_ensure_default_categories_when_existing(self, category_repo):
        """تست ایجاد دسته‌بندی‌های پیش‌فرض در صورت موجود بودن"""
        initial_count = len(category_repo.get_all())

        category_repo.ensure_default_categories()

        final_count = len(category_repo.get_all())
        # نباید تغییری کرده باشد
        assert final_count == initial_count

    # ============================================================
    # تست‌های get_category_columns
    # ============================================================

    def test_get_category_columns(self, category_repo):
        """تست دریافت ستون‌های یک دسته‌بندی"""
        cat_id = category_repo.create(name='دسته', columns=4)

        columns = category_repo.get_category_columns(cat_id)
        assert columns == 4

    def test_get_category_columns_not_found(self, category_repo):
        """تست دریافت ستون‌های دسته‌بندی ناموجود"""
        columns = category_repo.get_category_columns(99999)
        assert columns is None

    def test_get_category_columns_default(self, category_repo):
        """تست دریافت ستون‌های دسته‌بندی با مقدار پیش‌فرض None"""
        cat_id = category_repo.create(name='دسته', columns=None)

        columns = category_repo.get_category_columns(cat_id)
        assert columns is None

    # ============================================================
    # تست‌های get_category_location
    # ============================================================

    def test_get_category_location(self, category_repo):
        """تست دریافت مکان دسته‌بندی"""
        cat_id = category_repo.create(name='دسته', location='more')

        location = category_repo.get_category_location(cat_id)
        assert location == 'more'

    def test_get_category_location_not_found(self, category_repo):
        """تست دریافت مکان دسته‌بندی ناموجود"""
        location = category_repo.get_category_location(99999)
        assert location is None

    # ============================================================
    # تست‌های get_category_count
    # ============================================================

    def test_get_category_count(self, category_repo):
        """تست تعداد دسته‌بندی‌ها"""
        initial_count = category_repo.get_category_count()

        for i in range(3):
            category_repo.create(name=f'دسته {i}')

        final_count = category_repo.get_category_count()
        assert final_count == initial_count + 3

    def test_get_category_count_by_location(self, category_repo):
        """تست تعداد دسته‌بندی‌های یک مکان خاص"""
        category_repo.create(name='دسته ۱', location='main')
        category_repo.create(name='دسته ۲', location='main')
        category_repo.create(name='دسته ۳', location='more')

        count = category_repo.get_category_count(location='main')
        assert count == 2

    # ============================================================
    # تست‌های get_category_with_button_count
    # ============================================================

    def test_get_category_with_button_count(self, category_repo):
        """تست دریافت تعداد دکمه‌های یک دسته‌بندی"""
        cat_id = category_repo.create(name='دسته')

        # افزودن دکمه‌ها
        with category_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat_id, 'دکمه ۱', 'btn_1', 1)
            )
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, is_active) VALUES (?, ?, ?, ?)",
                (cat_id, 'دکمه ۲', 'btn_2', 1)
            )
            category_repo.connection.commit()

        count = category_repo.get_category_with_button_count(cat_id)
        assert count == 2

    # ============================================================
    # تست‌های get_all_categories_with_stats
    # ============================================================

    def test_get_all_categories_with_stats(self, category_repo):
        """تست دریافت تمام دسته‌بندی‌ها با آمار"""
        cat1_id = category_repo.create(name='دسته ۱')
        cat2_id = category_repo.create(name='دسته ۲')

        # افزودن دکمه‌ها
        with category_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, has_submenu, has_payment, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                (cat1_id, 'دکمه ۱', 'btn_1', 1, 0, 1)
            )
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, has_submenu, has_payment, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                (cat1_id, 'دکمه ۲', 'btn_2', 0, 1, 1)
            )
            cursor.execute(
                "INSERT INTO buttons (category_id, name, callback_data, has_submenu, has_payment, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                (cat2_id, 'دکمه ۳', 'btn_3', 0, 0, 1)
            )
            category_repo.connection.commit()

        categories = category_repo.get_all_categories_with_stats()
        assert len(categories) >= 2

        cat1 = next((c for c in categories if c['id'] == cat1_id), None)
        cat2 = next((c for c in categories if c['id'] == cat2_id), None)

        assert cat1 is not None
        assert cat2 is not None
        assert cat1['total_buttons'] == 2
        assert cat1['active_buttons'] == 2
        assert cat1['submenu_count'] == 1
        assert cat1['payment_count'] == 1

        assert cat2['total_buttons'] == 1
        assert cat2['active_buttons'] == 1

    # ============================================================
    # تست‌های get_category_locations
    # ============================================================

    def test_get_category_locations(self, category_repo):
        """تست دریافت لیست مکان‌های موجود"""
        category_repo.create(name='دسته ۱', location='main')
        category_repo.create(name='دسته ۲', location='more')
        category_repo.create(name='دسته ۳', location='other')

        locations = category_repo.get_category_locations()
        assert set(locations) == {'main', 'more', 'other'}

    # ============================================================
    # تست‌های custom_query
    # ============================================================

    def test_custom_query(self, category_repo):
        """تست اجرای کوئری سفارشی"""
        for i in range(3):
            category_repo.create(name=f'دسته {i}')

        results = category_repo.custom_query(
            "SELECT * FROM categories WHERE name LIKE ?",
            ['%دسته%']
        )
        assert len(results) >= 3

    def test_custom_query_one(self, category_repo):
        """تست اجرای کوئری سفارشی و دریافت یک نتیجه"""
        category_repo.create(name='دسته خاص')

        result = category_repo.custom_query_one(
            "SELECT * FROM categories WHERE name = ?",
            ['دسته خاص']
        )
        assert result is not None
        assert result['name'] == 'دسته خاص'

    # ============================================================
    # تست‌های transaction
    # ============================================================

    def test_transaction_commit(self, category_repo):
        """تست تراکنش با commit"""
        category_repo.begin_transaction()

        category_id = category_repo.create(name='دسته تراکنش')

        category_repo.commit_transaction()

        category = category_repo.get_by_id(category_id)
        assert category is not None

    def test_transaction_rollback(self, category_repo):
        """تست تراکنش با rollback"""
        category_repo.begin_transaction()

        category_id = category_repo.create(name='دسته تراکنش')

        category_repo.rollback_transaction()

        category = category_repo.get_by_id(category_id)
        assert category is None

    # ============================================================
    # تست‌های error handling
    # ============================================================

    def test_update_category_not_found(self, category_repo):
        """تست به‌روزرسانی دسته‌بندی ناموجود"""
        result = category_repo.update(99999, {'name': 'نام جدید'})
        assert result is False

    def test_get_category_columns_not_found(self, category_repo):
        """تست دریافت ستون‌های دسته‌بندی ناموجود"""
        columns = category_repo.get_category_columns(99999)
        assert columns is None

    def test_update_category_columns_not_found(self, category_repo):
        """تست به‌روزرسانی ستون‌های دسته‌بندی ناموجود"""
        result = category_repo.update_category_columns(99999, 3)
        assert result is False