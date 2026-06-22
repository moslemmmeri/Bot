# tests/test_repositories/test_button_repository.py
# تست‌های واحد برای ButtonRepository

import pytest
from unittest.mock import MagicMock, patch

from repositories.button_repository import ButtonRepository


class TestButtonRepository:
    """تست‌های ButtonRepository"""

    @pytest.fixture
    def button_repo(self, db_connection):
        """ایجاد ButtonRepository با اتصال دیتابیس تست"""
        return ButtonRepository(db_connection)

    @pytest.fixture
    def sample_category_data(self, db_connection):
        """ایجاد دسته‌بندی نمونه در دیتابیس"""
        with db_connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, location, is_active) VALUES (?, ?, ?)",
                ('دسته تست', 'main', 1)
            )
            category_id = cursor.get_lastrowid()
            return {'id': category_id, 'name': 'دسته تست', 'location': 'main'}

    @pytest.fixture
    def sample_button_data(self, sample_category_data):
        """داده‌های نمونه دکمه"""
        return {
            'category_id': sample_category_data['id'],
            'name': 'سرویس تست',
            'icon': '🔘',
            'callback_data': 'btn_test_123',
            'parent_button_id': None,
            'has_submenu': 0,
            'has_payment': 1,
            'price_amount': 50000,
            'price_label': 'هزینه خدمات',
            'price_type': 'fixed',
            'sort_order': 0,
            'columns': 2,
        }

    # ============================================================
    # تست‌های create
    # ============================================================

    def test_create_button_success(self, button_repo, sample_button_data):
        """تست ایجاد دکمه با موفقیت"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name=sample_button_data['name'],
            icon=sample_button_data['icon'],
            callback_data=sample_button_data['callback_data'],
            has_submenu=sample_button_data['has_submenu'],
            has_payment=sample_button_data['has_payment'],
            price_amount=sample_button_data['price_amount'],
            price_label=sample_button_data['price_label'],
            sort_order=sample_button_data['sort_order'],
            columns=sample_button_data['columns'],
        )

        assert button_id is not None
        assert button_id > 0

        # دریافت دکمه ایجادشده
        button = button_repo.get_by_id(button_id)
        assert button is not None
        assert button['name'] == sample_button_data['name']
        assert button['icon'] == sample_button_data['icon']
        assert button['callback_data'] == sample_button_data['callback_data']
        assert button['category_id'] == sample_button_data['category_id']
        assert button['has_payment'] == sample_button_data['has_payment']
        assert button['price_amount'] == sample_button_data['price_amount']
        assert button['columns'] == sample_button_data['columns']

    def test_create_button_with_parent(self, button_repo, sample_button_data):
        """تست ایجاد دکمه با والد"""
        # ابتدا دکمه والد ایجاد می‌کنیم
        parent_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه والد',
            callback_data='btn_parent',
        )

        # ایجاد زیرمنو
        child_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='زیرمنو',
            callback_data='btn_child',
            parent_button_id=parent_id,
        )

        assert child_id is not None
        button = button_repo.get_by_id(child_id)
        assert button['parent_button_id'] == parent_id

    def test_create_button_with_duplicate_callback(self, button_repo, sample_button_data):
        """تست ایجاد دکمه با callback_data تکراری"""
        button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه ۱',
            callback_data='btn_duplicate',
        )

        # تلاش برای ایجاد دکمه دوم با همان callback_data
        with pytest.raises(Exception):
            button_repo.create(
                category_id=sample_button_data['category_id'],
                name='دکمه ۲',
                callback_data='btn_duplicate',
            )

    def test_create_button_without_callback(self, button_repo, sample_button_data):
        """تست ایجاد دکمه بدون callback_data (خودکار تولید می‌شود)"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه بدون کالبک',
            callback_data=None,
        )

        assert button_id is not None
        button = button_repo.get_by_id(button_id)
        assert button['callback_data'] is not None
        assert button['callback_data'].startswith('btn_')

    # ============================================================
    # تست‌های get_by_id
    # ============================================================

    def test_get_by_id_success(self, button_repo, sample_button_data):
        """تست دریافت دکمه با شناسه"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه تست',
        )

        button = button_repo.get_by_id(button_id)
        assert button is not None
        assert button['id'] == button_id
        assert button['name'] == 'دکمه تست'

    def test_get_by_id_not_found(self, button_repo):
        """تست دریافت دکمه ناموجود"""
        button = button_repo.get_by_id(99999)
        assert button is None

    # ============================================================
    # تست‌های get_by_callback
    # ============================================================

    def test_get_by_callback_success(self, button_repo, sample_button_data):
        """تست دریافت دکمه با callback_data"""
        callback = 'btn_unique_callback_123'
        button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه تست',
            callback_data=callback,
        )

        button = button_repo.get_by_callback(callback)
        assert button is not None
        assert button['callback_data'] == callback

    def test_get_by_callback_not_found(self, button_repo):
        """تست دریافت دکمه با callback_data ناموجود"""
        button = button_repo.get_by_callback('non_existent_callback')
        assert button is None

    # ============================================================
    # تست‌های get_all
    # ============================================================

    def test_get_all_buttons(self, button_repo, sample_button_data):
        """تست دریافت تمام دکمه‌ها"""
        for i in range(3):
            button_repo.create(
                category_id=sample_button_data['category_id'],
                name=f'دکمه {i}',
                callback_data=f'btn_{i}',
            )

        buttons = button_repo.get_all()
        assert len(buttons) >= 3

    def test_get_all_with_pagination(self, button_repo, sample_button_data):
        """تست دریافت تمام دکمه‌ها با صفحه‌بندی"""
        for i in range(10):
            button_repo.create(
                category_id=sample_button_data['category_id'],
                name=f'دکمه {i}',
                callback_data=f'btn_{i}',
            )

        buttons_page_1 = button_repo.get_all(limit=3, offset=0)
        buttons_page_2 = button_repo.get_all(limit=3, offset=3)

        assert len(buttons_page_1) == 3
        assert len(buttons_page_2) == 3
        assert buttons_page_1[0]['id'] != buttons_page_2[0]['id']

    # ============================================================
    # تست‌های get_active
    # ============================================================

    def test_get_active_buttons(self, button_repo, sample_button_data):
        """تست دریافت دکمه‌های فعال"""
        # ایجاد دکمه فعال
        button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه فعال',
            callback_data='btn_active',
            is_active=True,
        )

        # ایجاد دکمه غیرفعال
        button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه غیرفعال',
            callback_data='btn_inactive',
            is_active=False,
        )

        active_buttons = button_repo.get_active()
        # حداقل دکمه فعال باید وجود داشته باشد
        assert len(active_buttons) >= 1
        for btn in active_buttons:
            assert btn['is_active'] == 1

    # ============================================================
    # تست‌های get_by_category
    # ============================================================

    def test_get_by_category(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت دکمه‌های یک دسته‌بندی"""
        for i in range(3):
            button_repo.create(
                category_id=sample_category_data['id'],
                name=f'دکمه {i}',
                callback_data=f'btn_{i}',
            )

        # ایجاد دکمه در دسته‌بندی دیگر
        with button_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, location) VALUES (?, ?)",
                ('دسته دیگر', 'more')
            )
            other_category_id = cursor.get_lastrowid()

        button_repo.create(
            category_id=other_category_id,
            name='دکمه دیگر',
            callback_data='btn_other',
        )

        buttons = button_repo.get_by_category(sample_category_data['id'])
        assert len(buttons) == 3

    def test_get_by_category_with_submenus(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت دکمه‌های یک دسته‌بندی با زیرمنوها"""
        # ایجاد دکمه والد
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
            has_submenu=1,
        )

        # ایجاد زیرمنو
        button_repo.create(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            callback_data='btn_child',
            parent_button_id=parent_id,
        )

        # دریافت بدون زیرمنو
        buttons = button_repo.get_by_category(sample_category_data['id'], include_submenus=False)
        # فقط دکمه والد باید باشد
        assert len(buttons) == 1
        assert buttons[0]['id'] == parent_id

        # دریافت با زیرمنو
        buttons_with_sub = button_repo.get_by_category(sample_category_data['id'], include_submenus=True)
        assert len(buttons_with_sub) == 2

    def test_get_by_category_admin(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت دکمه‌های یک دسته‌بندی برای پنل مدیریت"""
        for i in range(2):
            button_repo.create(
                category_id=sample_category_data['id'],
                name=f'دکمه {i}',
                callback_data=f'btn_{i}',
            )

        buttons = button_repo.get_by_category_admin(sample_category_data['id'])
        assert len(buttons) == 2
        # بررسی وجود display_icon
        for btn in buttons:
            assert 'display_icon' in btn
            assert btn['display_icon'] in ['📂', '📄']

    # ============================================================
    # تست‌های get_by_location
    # ============================================================

    def test_get_by_location(self, button_repo, sample_category_data):
        """تست دریافت دکمه‌های یک مکان خاص"""
        # ایجاد دسته‌بندی main
        with button_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, location, is_active) VALUES (?, ?, ?)",
                ('دسته اصلی', 'main', 1)
            )
            main_category_id = cursor.get_lastrowid()

        # ایجاد دکمه در دسته‌بندی main
        button_repo.create(
            category_id=main_category_id,
            name='دکمه اصلی',
            callback_data='btn_main',
        )

        # ایجاد دسته‌بندی more
        with button_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, location, is_active) VALUES (?, ?, ?)",
                ('دسته بیشتر', 'more', 1)
            )
            more_category_id = cursor.get_lastrowid()

        # ایجاد دکمه در دسته‌بندی more
        button_repo.create(
            category_id=more_category_id,
            name='دکمه بیشتر',
            callback_data='btn_more',
        )

        main_buttons = button_repo.get_by_location('main')
        assert len(main_buttons) >= 1
        assert main_buttons[0]['name'] == 'دکمه اصلی'

        more_buttons = button_repo.get_by_location('more')
        assert len(more_buttons) >= 1
        assert more_buttons[0]['name'] == 'دکمه بیشتر'

    # ============================================================
    # تست‌های زیرمنو
    # ============================================================

    def test_get_submenus(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت زیرمنوهای یک دکمه"""
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
        )

        for i in range(3):
            button_repo.create(
                category_id=sample_category_data['id'],
                name=f'زیرمنو {i}',
                callback_data=f'btn_child_{i}',
                parent_button_id=parent_id,
            )

        submenus = button_repo.get_submenus(parent_id)
        assert len(submenus) == 3

    def test_get_all_submenus(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت لیست تمام زیرمنوهای یک دکمه (فقط نام و شناسه)"""
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
        )

        for i in range(2):
            button_repo.create(
                category_id=sample_category_data['id'],
                name=f'زیرمنو {i}',
                callback_data=f'btn_child_{i}',
                parent_button_id=parent_id,
            )

        submenus = button_repo.get_all_submenus(parent_id)
        assert len(submenus) == 2
        for sub in submenus:
            assert 'id' in sub
            assert 'name' in sub

    def test_get_submenu_count(self, button_repo, sample_button_data, sample_category_data):
        """تست تعداد زیرمنوهای یک دکمه"""
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
        )

        count = button_repo.get_submenu_count(parent_id)
        assert count == 0

        button_repo.create(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            callback_data='btn_child',
            parent_button_id=parent_id,
        )

        count = button_repo.get_submenu_count(parent_id)
        assert count == 1

    # ============================================================
    # تست‌های get_with_payment و get_with_submenu
    # ============================================================

    def test_get_with_payment(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت دکمه‌های دارای پرداخت"""
        button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه با پرداخت',
            callback_data='btn_pay',
            has_payment=1,
        )

        button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه بدون پرداخت',
            callback_data='btn_no_pay',
            has_payment=0,
        )

        payment_buttons = button_repo.get_with_payment(limit=10)
        assert len(payment_buttons) >= 1
        for btn in payment_buttons:
            assert btn['has_payment'] == 1

    def test_get_with_submenu(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت دکمه‌های دارای زیرمنو"""
        button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه با زیرمنو',
            callback_data='btn_sub',
            has_submenu=1,
        )

        button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه بدون زیرمنو',
            callback_data='btn_no_sub',
            has_submenu=0,
        )

        submenu_buttons = button_repo.get_with_submenu(limit=10)
        assert len(submenu_buttons) >= 1
        for btn in submenu_buttons:
            assert btn['has_submenu'] == 1

    # ============================================================
    # تست‌های get_parent_buttons
    # ============================================================

    def test_get_parent_buttons(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت دکمه‌های والد (بدون parent)"""
        # ایجاد دکمه والد
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
        )

        # ایجاد زیرمنو
        button_repo.create(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            callback_data='btn_child',
            parent_button_id=parent_id,
        )

        parents = button_repo.get_parent_buttons()
        # حداقل دکمه والد باید وجود داشته باشد
        assert len(parents) >= 1
        for btn in parents:
            assert btn['parent_button_id'] is None or btn['parent_button_id'] == 0

    def test_get_parent_buttons_by_category(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت دکمه‌های والد در یک دسته‌بندی خاص"""
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
        )

        button_repo.create(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            callback_data='btn_child',
            parent_button_id=parent_id,
        )

        parents = button_repo.get_parent_buttons(category_id=sample_category_data['id'])
        assert len(parents) >= 1
        for btn in parents:
            assert btn['category_id'] == sample_category_data['id']
            assert btn['parent_button_id'] is None or btn['parent_button_id'] == 0

    # ============================================================
    # تست‌های update
    # ============================================================

    def test_update_button_name(self, button_repo, sample_button_data):
        """تست تغییر نام دکمه"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='نام قدیم',
            callback_data='btn_test',
        )

        result = button_repo.update_name(button_id, 'نام جدید')
        assert result is True

        button = button_repo.get_by_id(button_id)
        assert button['name'] == 'نام جدید'

    def test_update_button_price(self, button_repo, sample_button_data):
        """تست تغییر قیمت دکمه"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='سرویس',
            callback_data='btn_test',
            has_payment=1,
            price_amount=50000,
            price_label='قیمت قدیم',
        )

        result = button_repo.update_price(button_id, 100000, 'قیمت جدید')
        assert result is True

        button = button_repo.get_by_id(button_id)
        assert button['price_amount'] == 100000
        assert button['price_label'] == 'قیمت جدید'

    def test_toggle_active(self, button_repo, sample_button_data):
        """تست تغییر وضعیت فعال/غیرفعال"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه',
            callback_data='btn_test',
            is_active=1,
        )

        result = button_repo.toggle_active(button_id)
        assert result is True

        button = button_repo.get_by_id(button_id)
        assert button['is_active'] == 0

        # تغییر مجدد
        result = button_repo.toggle_active(button_id)
        assert result is True
        button = button_repo.get_by_id(button_id)
        assert button['is_active'] == 1

    def test_toggle_payment(self, button_repo, sample_button_data):
        """تست تغییر وضعیت پرداخت"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='سرویس',
            callback_data='btn_test',
            has_payment=0,
        )

        result = button_repo.toggle_payment(button_id)
        assert result is True

        button = button_repo.get_by_id(button_id)
        assert button['has_payment'] == 1

    def test_toggle_submenu(self, button_repo, sample_button_data):
        """تست تغییر وضعیت زیرمنو"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه',
            callback_data='btn_test',
            has_submenu=0,
        )

        result = button_repo.toggle_submenu(button_id)
        assert result is True

        button = button_repo.get_by_id(button_id)
        assert button['has_submenu'] == 1

    def test_update_sort_order(self, button_repo, sample_button_data, sample_category_data):
        """تست به‌روزرسانی ترتیب نمایش"""
        button_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه',
            callback_data='btn_test',
            sort_order=5,
        )

        result = button_repo.update_sort_order(button_id, 10)
        assert result is True

        button = button_repo.get_by_id(button_id)
        assert button['sort_order'] == 10

    def test_update_columns(self, button_repo, sample_button_data):
        """تست به‌روزرسانی ستون‌ها"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه',
            callback_data='btn_test',
            columns=None,
        )

        result = button_repo.update_columns(button_id, 4)
        assert result is True

        button = button_repo.get_by_id(button_id)
        assert button['columns'] == 4

    def test_move_to_category(self, button_repo, sample_button_data, sample_category_data):
        """تست انتقال دکمه به دسته‌بندی دیگر"""
        # ایجاد دسته‌بندی دوم
        with button_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, location, is_active) VALUES (?, ?, ?)",
                ('دسته دوم', 'more', 1)
            )
            category2_id = cursor.get_lastrowid()

        button_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه قابل انتقال',
            callback_data='btn_move',
        )

        result = button_repo.move_to_category(button_id, category2_id)
        assert result is True

        button = button_repo.get_by_id(button_id)
        assert button['category_id'] == category2_id

    def test_move_to_category_with_submenus(self, button_repo, sample_button_data, sample_category_data):
        """تست انتقال دکمه با زیرمنوها به دسته‌بندی دیگر"""
        # ایجاد دسته‌بندی دوم
        with button_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, location, is_active) VALUES (?, ?, ?)",
                ('دسته دوم', 'more', 1)
            )
            category2_id = cursor.get_lastrowid()

        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
        )

        child_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            callback_data='btn_child',
            parent_button_id=parent_id,
        )

        result = button_repo.move_to_category(parent_id, category2_id)
        assert result is True

        parent = button_repo.get_by_id(parent_id)
        child = button_repo.get_by_id(child_id)
        assert parent['category_id'] == category2_id
        assert child['category_id'] == category2_id

    # ============================================================
    # تست‌های swap_sort_order
    # ============================================================

    def test_swap_sort_order(self, button_repo, sample_button_data, sample_category_data):
        """تست جابجایی ترتیب دو دکمه"""
        btn1_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه ۱',
            callback_data='btn_1',
            sort_order=1,
        )

        btn2_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه ۲',
            callback_data='btn_2',
            sort_order=2,
        )

        result = button_repo.swap_sort_order(btn1_id, btn2_id)
        assert result is True

        btn1 = button_repo.get_by_id(btn1_id)
        btn2 = button_repo.get_by_id(btn2_id)
        assert btn1['sort_order'] == 2
        assert btn2['sort_order'] == 1

    # ============================================================
    # تست‌های delete
    # ============================================================

    def test_delete_button(self, button_repo, sample_button_data):
        """تست حذف دکمه"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه برای حذف',
            callback_data='btn_delete',
        )

        result = button_repo.delete(button_id)
        assert result is True

        button = button_repo.get_by_id(button_id)
        assert button is None

    def test_delete_button_with_submenus(self, button_repo, sample_button_data, sample_category_data):
        """تست حذف دکمه با زیرمنوها"""
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
            has_submenu=1,
        )

        child_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            callback_data='btn_child',
            parent_button_id=parent_id,
        )

        result = button_repo.delete(parent_id)
        assert result is True

        parent = button_repo.get_by_id(parent_id)
        child = button_repo.get_by_id(child_id)
        assert parent is None
        assert child is None

    def test_delete_duplicate_submenus(self, button_repo, sample_button_data, sample_category_data):
        """تست حذف زیرمنوهای تکراری"""
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
        )

        # ایجاد زیرمنو با نام مشابه والد
        duplicate_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_duplicate',
            parent_button_id=parent_id,
        )

        count = button_repo.delete_duplicate_submenus(parent_id)
        assert count == 1

        duplicate = button_repo.get_by_id(duplicate_id)
        assert duplicate is None

    # ============================================================
    # تست‌های get_max_sort_order
    # ============================================================

    def test_get_max_sort_order(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت حداکثر sort_order"""
        button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه ۱',
            callback_data='btn_1',
            sort_order=5,
        )

        button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه ۲',
            callback_data='btn_2',
            sort_order=10,
        )

        max_order = button_repo.get_max_sort_order(sample_category_data['id'])
        assert max_order == 10

    def test_get_max_sort_order_with_parent(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت حداکثر sort_order با والد"""
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
        )

        button_repo.create(
            category_id=sample_category_data['id'],
            name='زیرمنو ۱',
            callback_data='btn_child_1',
            parent_button_id=parent_id,
            sort_order=3,
        )

        button_repo.create(
            category_id=sample_category_data['id'],
            name='زیرمنو ۲',
            callback_data='btn_child_2',
            parent_button_id=parent_id,
            sort_order=7,
        )

        max_order = button_repo.get_max_sort_order(sample_category_data['id'], parent_id)
        assert max_order == 7

    # ============================================================
    # تست‌های get_buttons_with_stats
    # ============================================================

    def test_get_buttons_with_stats(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت دکمه‌ها با آمار"""
        button_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه آماری',
            callback_data='btn_stats',
        )

        # ثبت آمار در button_stats
        with button_repo.connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO button_stats (button_id, user_id, action_type, amount) VALUES (?, ?, ?, ?)",
                (button_id, 1, 'click', 0)
            )
            cursor.execute(
                "INSERT INTO button_stats (button_id, user_id, action_type, amount) VALUES (?, ?, ?, ?)",
                (button_id, 2, 'order_paid', 50000)
            )
            button_repo.connection.commit()

        buttons = button_repo.get_buttons_with_stats(limit=10)
        assert len(buttons) >= 1

        target = next((b for b in buttons if b['id'] == button_id), None)
        if target:
            assert 'clicks' in target
            assert 'orders' in target
            assert 'revenue' in target

    # ============================================================
    # تست‌های get_button_count
    # ============================================================

    def test_get_button_count(self, button_repo, sample_button_data, sample_category_data):
        """تست تعداد دکمه‌ها"""
        initial_count = button_repo.get_button_count()

        for i in range(3):
            button_repo.create(
                category_id=sample_category_data['id'],
                name=f'دکمه {i}',
                callback_data=f'btn_{i}',
            )

        final_count = button_repo.get_button_count()
        assert final_count == initial_count + 3

    def test_get_button_count_by_category(self, button_repo, sample_button_data, sample_category_data):
        """تست تعداد دکمه‌های یک دسته‌بندی"""
        for i in range(3):
            button_repo.create(
                category_id=sample_category_data['id'],
                name=f'دکمه {i}',
                callback_data=f'btn_{i}',
            )

        count = button_repo.get_button_count(category_id=sample_category_data['id'])
        assert count == 3

    # ============================================================
    # تست‌های count_submenus
    # ============================================================

    def test_count_submenus(self, button_repo, sample_button_data, sample_category_data):
        """تست تعداد زیرمنوهای یک دکمه"""
        parent_id = button_repo.create(
            category_id=sample_category_data['id'],
            name='والد',
            callback_data='btn_parent',
        )

        count = button_repo.count_submenus(parent_id)
        assert count == 0

        for i in range(2):
            button_repo.create(
                category_id=sample_category_data['id'],
                name=f'زیرمنو {i}',
                callback_data=f'btn_child_{i}',
                parent_button_id=parent_id,
            )

        count = button_repo.count_submenus(parent_id)
        assert count == 2

    # ============================================================
    # تست‌های custom_query
    # ============================================================

    def test_custom_query(self, button_repo, sample_button_data, sample_category_data):
        """تست اجرای کوئری سفارشی"""
        for i in range(3):
            button_repo.create(
                category_id=sample_category_data['id'],
                name=f'دکمه {i}',
                callback_data=f'btn_{i}',
            )

        results = button_repo.custom_query(
            "SELECT * FROM buttons WHERE name LIKE ?",
            ['%دکمه%']
        )
        assert len(results) >= 3

    def test_custom_query_one(self, button_repo, sample_button_data):
        """تست اجرای کوئری سفارشی و دریافت یک نتیجه"""
        button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه تست',
            callback_data='btn_test',
        )

        result = button_repo.custom_query_one(
            "SELECT * FROM buttons WHERE name = ?",
            ['دکمه تست']
        )
        assert result is not None
        assert result['name'] == 'دکمه تست'

    def test_custom_execute(self, button_repo):
        """تست اجرای کوئری بدون بازگشت نتیجه"""
        result = button_repo.custom_execute(
            "DELETE FROM buttons WHERE id = -1"
        )
        # فقط باید بدون خطا اجرا شود
        assert result >= 0

    # ============================================================
    # تست‌های transaction
    # ============================================================

    def test_transaction_commit(self, button_repo, sample_button_data):
        """تست تراکنش با commit"""
        button_repo.begin_transaction()

        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه تراکنش',
            callback_data='btn_trans',
        )

        button_repo.commit_transaction()

        button = button_repo.get_by_id(button_id)
        assert button is not None

    def test_transaction_rollback(self, button_repo, sample_button_data):
        """تست تراکنش با rollback"""
        button_repo.begin_transaction()

        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='دکمه تراکنش',
            callback_data='btn_trans',
        )

        button_repo.rollback_transaction()

        button = button_repo.get_by_id(button_id)
        assert button is None

    # ============================================================
    # تست‌های error handling
    # ============================================================

    def test_create_button_invalid_category(self, button_repo, sample_button_data):
        """تست ایجاد دکمه با دسته‌بندی ناموجود"""
        with pytest.raises(Exception):
            button_repo.create(
                category_id=99999,
                name='دکمه',
                callback_data='btn_test',
            )

    def test_update_button_not_found(self, button_repo):
        """تست به‌روزرسانی دکمه ناموجود"""
        result = button_repo.update(99999, {'name': 'نام جدید'})
        assert result is False

    def test_delete_button_not_found(self, button_repo):
        """تست حذف دکمه ناموجود"""
        result = button_repo.delete(99999)
        assert result is False

    def test_get_max_sort_order_empty(self, button_repo, sample_category_data):
        """تست دریافت حداکثر sort_order در صورت خالی بودن"""
        max_order = button_repo.get_max_sort_order(sample_category_data['id'])
        assert max_order == -1

    # ============================================================
    # تست‌های get_button_price_info
    # ============================================================

    def test_get_button_price_info(self, button_repo, sample_button_data):
        """تست دریافت اطلاعات قیمت دکمه"""
        button_id = button_repo.create(
            category_id=sample_button_data['category_id'],
            name='سرویس',
            callback_data='btn_test',
            has_payment=1,
            price_amount=75000,
            price_label='هزینه ویژه',
            price_type='variable',
            min_price=50000,
            max_price=100000,
        )

        info = button_repo.get_button_price_info(button_id)
        assert info['price_amount'] == 75000
        assert info['price_label'] == 'هزینه ویژه'
        assert info['price_type'] == 'variable'
        assert info['min_price'] == 50000
        assert info['max_price'] == 100000

    def test_get_button_price_info_default(self, button_repo):
        """تست دریافت اطلاعات قیمت دکمه با مقادیر پیش‌فرض"""
        info = button_repo.get_button_price_info(99999)
        assert info['price_amount'] == 50000
        assert info['price_label'] == 'هزینه خدمات'
        assert info['price_type'] == 'fixed'

    # ============================================================
    # تست‌های get_buttons_with_price_type
    # ============================================================

    def test_get_buttons_with_price_type(self, button_repo, sample_button_data, sample_category_data):
        """تست دریافت دکمه‌ها بر اساس نوع قیمت"""
        button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه ثابت',
            callback_data='btn_fixed',
            price_type='fixed',
        )

        button_repo.create(
            category_id=sample_category_data['id'],
            name='دکمه متغیر',
            callback_data='btn_variable',
            price_type='variable',
        )

        fixed_buttons = button_repo.get_buttons_with_price_type('fixed')
        assert len(fixed_buttons) >= 1
        for btn in fixed_buttons:
            assert btn['price_type'] == 'fixed'

        variable_buttons = button_repo.get_buttons_with_price_type('variable')
        assert len(variable_buttons) >= 1
        for btn in variable_buttons:
            assert btn['price_type'] == 'variable'