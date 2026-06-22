# tests/test_services/test_button_service.py
# تست‌های واحد برای ButtonService

import pytest
from unittest.mock import MagicMock, patch

from services.button_service import ButtonService
from models.button import Button, ButtonType


class TestButtonService:
    """تست‌های ButtonService"""

    @pytest.fixture
    def button_service(self, db_connection):
        """ایجاد ButtonService با اتصال دیتابیس تست"""
        return ButtonService(db_connection)

    @pytest.fixture
    def sample_button_data(self):
        """داده‌های نمونه دکمه"""
        return {
            'category_id': 1,
            'name': 'سرویس تست',
            'icon': '🔘',
            'callback_data': 'btn_test_123',
            'has_submenu': 0,
            'has_payment': 1,
            'price_amount': 50000,
            'price_label': 'هزینه خدمات',
            'price_type': 'fixed',
            'sort_order': 0,
            'columns': 2,
        }

    @pytest.fixture
    def sample_category_data(self):
        """ایجاد دسته‌بندی نمونه در دیتابیس"""
        with db_connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, location, is_active) VALUES (?, ?, ?)",
                ('دسته تست', 'main', 1)
            )
            return {'id': cursor.get_lastrowid()}

    # ============================================================
    # تست‌های ایجاد دکمه
    # ============================================================

    def test_create_button_success(self, button_service, sample_button_data, sample_category_data):
        """تست ایجاد دکمه با موفقیت"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name=sample_button_data['name'],
            icon=sample_button_data['icon'],
            callback_data=sample_button_data['callback_data'],
            has_payment=sample_button_data['has_payment'],
            price_amount=sample_button_data['price_amount'],
            price_label=sample_button_data['price_label'],
        )

        assert button is not None
        assert button['name'] == sample_button_data['name']
        assert button['icon'] == sample_button_data['icon']
        assert button['has_payment'] == sample_button_data['has_payment']
        assert button['price_amount'] == sample_button_data['price_amount']

    def test_create_button_with_submenu(self, button_service, sample_category_data):
        """تست ایجاد دکمه با زیرمنو"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه والد',
            has_submenu=True,
        )

        assert button is not None
        assert button['has_submenu'] == 1
        assert button['button_type'] == 'submenu'

    def test_create_button_with_payment(self, button_service, sample_category_data):
        """تست ایجاد دکمه با پرداخت"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='سرویس پرداختی',
            has_payment=True,
            price_amount=100000,
        )

        assert button is not None
        assert button['has_payment'] == 1
        assert button['price_amount'] == 100000

    def test_create_button_with_parent(self, button_service, sample_category_data):
        """تست ایجاد زیرمنو با والد"""
        parent = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه والد',
        )

        child = button_service.create_button(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            parent_button_id=parent['id'],
        )

        assert child is not None
        assert child['parent_button_id'] == parent['id']
        assert child['is_submenu'] is True

    # ============================================================
    # تست‌های دریافت دکمه
    # ============================================================

    def test_get_button_by_id(self, button_service, sample_category_data):
        """تست دریافت دکمه با شناسه"""
        created = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه تست',
        )

        button = button_service.get_button(created['id'])
        assert button is not None
        assert button['id'] == created['id']
        assert button['name'] == 'دکمه تست'

    def test_get_button_by_callback(self, button_service, sample_category_data):
        """تست دریافت دکمه با callback_data"""
        callback = 'btn_unique_callback'
        created = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه تست',
            callback_data=callback,
        )

        button = button_service.get_button_by_callback(callback)
        assert button is not None
        assert button['id'] == created['id']

    def test_get_button_not_found(self, button_service):
        """تست دریافت دکمه ناموجود"""
        button = button_service.get_button(99999)
        assert button is None

    def test_get_all_buttons(self, button_service, sample_category_data):
        """تست دریافت تمام دکمه‌ها"""
        for i in range(3):
            button_service.create_button(
                category_id=sample_category_data['id'],
                name=f'دکمه {i}',
            )

        buttons = button_service.get_all_buttons()
        assert len(buttons) >= 3

    def test_get_active_buttons(self, button_service, sample_category_data):
        """تست دریافت دکمه‌های فعال"""
        button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه فعال ۱',
            is_active=True,
        )
        button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه غیرفعال',
            is_active=False,
        )

        active = button_service.get_active_buttons()
        assert len(active) >= 1
        for btn in active:
            assert btn['is_active'] == 1

    def test_get_buttons_by_category(self, button_service, sample_category_data):
        """تست دریافت دکمه‌های یک دسته‌بندی"""
        for i in range(3):
            button_service.create_button(
                category_id=sample_category_data['id'],
                name=f'دکمه {i}',
            )

        buttons = button_service.get_buttons_by_category(sample_category_data['id'])
        assert len(buttons) >= 3

    def test_get_buttons_by_location(self, button_service, sample_category_data):
        """تست دریافت دکمه‌های یک مکان"""
        button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه منوی اصلی',
            location='main',
        )

        buttons = button_service.get_buttons_by_location('main')
        assert len(buttons) >= 1

    # ============================================================
    # تست‌های زیرمنو
    # ============================================================

    def test_get_submenus(self, button_service, sample_category_data):
        """تست دریافت زیرمنوهای یک دکمه"""
        parent = button_service.create_button(
            category_id=sample_category_data['id'],
            name='والد',
            has_submenu=True,
        )

        for i in range(2):
            button_service.create_button(
                category_id=sample_category_data['id'],
                name=f'زیرمنو {i}',
                parent_button_id=parent['id'],
            )

        submenus = button_service.get_submenus(parent['id'])
        assert len(submenus) == 2

    def test_has_submenus(self, button_service, sample_category_data):
        """تست بررسی وجود زیرمنو"""
        parent = button_service.create_button(
            category_id=sample_category_data['id'],
            name='والد',
        )

        assert button_service.has_submenus(parent['id']) is False

        button_service.create_button(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            parent_button_id=parent['id'],
        )

        assert button_service.has_submenus(parent['id']) is True

    def test_get_menu_structure(self, button_service, sample_category_data):
        """تست دریافت ساختار کامل منو"""
        # ایجاد دسته‌بندی و دکمه‌ها
        category = button_service._category_repo.get_by_id(sample_category_data['id'])
        structure = button_service.get_menu_structure('main')
        
        assert isinstance(structure, list)

    # ============================================================
    # تست‌های به‌روزرسانی دکمه
    # ============================================================

    def test_update_button_name(self, button_service, sample_category_data):
        """تست تغییر نام دکمه"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='نام قدیم',
        )

        result = button_service.update_button_name(button['id'], 'نام جدید')
        assert result is True

        updated = button_service.get_button(button['id'])
        assert updated['name'] == 'نام جدید'

    def test_update_button_price(self, button_service, sample_category_data):
        """تست تغییر قیمت دکمه"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='سرویس',
            has_payment=True,
            price_amount=50000,
        )

        result = button_service.update_button_price(button['id'], 100000, 'قیمت جدید')
        assert result is True

        updated = button_service.get_button(button['id'])
        assert updated['price_amount'] == 100000
        assert updated['price_label'] == 'قیمت جدید'

    def test_toggle_button_active(self, button_service, sample_category_data):
        """تست تغییر وضعیت فعال/غیرفعال"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه',
            is_active=True,
        )

        result = button_service.toggle_button_active(button['id'])
        assert result is True

        updated = button_service.get_button(button['id'])
        assert updated['is_active'] == 0

        # تغییر مجدد
        button_service.toggle_button_active(button['id'])
        updated = button_service.get_button(button['id'])
        assert updated['is_active'] == 1

    def test_toggle_button_payment(self, button_service, sample_category_data):
        """تست تغییر وضعیت پرداخت"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='سرویس',
            has_payment=False,
        )

        result = button_service.toggle_button_payment(button['id'])
        assert result is True

        updated = button_service.get_button(button['id'])
        assert updated['has_payment'] == 1

    def test_toggle_button_submenu(self, button_service, sample_category_data):
        """تست تغییر وضعیت زیرمنو"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه',
            has_submenu=False,
        )

        result = button_service.toggle_button_submenu(button['id'])
        assert result is True

        updated = button_service.get_button(button['id'])
        assert updated['has_submenu'] == 1

    # ============================================================
    # تست‌های حذف دکمه
    # ============================================================

    def test_delete_button(self, button_service, sample_category_data):
        """تست حذف دکمه"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه برای حذف',
        )

        result = button_service.delete_button(button['id'])
        assert result is True

        deleted = button_service.get_button(button['id'])
        assert deleted is None

    def test_delete_button_with_submenus(self, button_service, sample_category_data):
        """تست حذف دکمه با زیرمنوها"""
        parent = button_service.create_button(
            category_id=sample_category_data['id'],
            name='والد',
            has_submenu=True,
        )

        child = button_service.create_button(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            parent_button_id=parent['id'],
        )

        result = button_service.delete_button(parent['id'])
        assert result is True

        deleted_parent = button_service.get_button(parent['id'])
        assert deleted_parent is None

        deleted_child = button_service.get_button(child['id'])
        assert deleted_child is None

    # ============================================================
    # تست‌های جابجایی و انتقال
    # ============================================================

    def test_move_button_to_category(self, button_service, sample_category_data):
        """تست انتقال دکمه به دسته‌بندی دیگر"""
        # ایجاد دسته‌بندی دوم
        with db_connection.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO categories (name, location, is_active) VALUES (?, ?, ?)",
                ('دسته دوم', 'more', 1)
            )
            category2_id = cursor.get_lastrowid()

        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه قابل انتقال',
        )

        result = button_service.move_button(button['id'], category2_id)
        assert result is True

        updated = button_service.get_button(button['id'])
        assert updated['category_id'] == category2_id

    def test_swap_sort_order(self, button_service, sample_category_data):
        """تست جابجایی ترتیب دو دکمه"""
        btn1 = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه ۱',
            sort_order=1,
        )
        btn2 = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه ۲',
            sort_order=2,
        )

        result = button_service.swap_sort_order(btn1['id'], btn2['id'])
        assert result is True

        updated1 = button_service.get_button(btn1['id'])
        updated2 = button_service.get_button(btn2['id'])
        assert updated1['sort_order'] == 2
        assert updated2['sort_order'] == 1

    # ============================================================
    # تست‌های قیمت
    # ============================================================

    def test_update_button_price_type(self, button_service, sample_category_data):
        """تست تغییر نوع قیمت"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='سرویس با قیمت',
            has_payment=True,
            price_type='fixed',
            price_amount=50000,
        )

        result = button_service.update_button(button['id'], {'price_type': 'variable'})
        assert result is True

        updated = button_service.get_button(button['id'])
        assert updated['price_type'] == 'variable'

    # ============================================================
    # تست‌های ستون‌ها
    # ============================================================

    def test_get_button_columns(self, button_service, sample_category_data):
        """تست دریافت ستون‌های اختصاصی دکمه"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه با ستون',
            columns=3,
        )

        columns = button_service.get_button_columns(button['id'])
        assert columns == 3

    def test_set_button_columns(self, button_service, sample_category_data):
        """تست تنظیم ستون‌های دکمه"""
        button = button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه',
            columns=None,
        )

        result = button_service.set_button_columns(button['id'], 4)
        assert result is True

        updated = button_service.get_button(button['id'])
        assert updated['columns'] == 4

    # ============================================================
    # تست‌های آمار
    # ============================================================

    def test_get_button_count(self, button_service, sample_category_data):
        """تست تعداد دکمه‌ها"""
        for i in range(3):
            button_service.create_button(
                category_id=sample_category_data['id'],
                name=f'دکمه {i}',
            )

        count = button_service.get_button_count(sample_category_data['id'])
        assert count >= 3

    def test_get_buttons_with_stats(self, button_service, sample_category_data):
        """تست دریافت دکمه‌ها با آمار"""
        for i in range(2):
            button_service.create_button(
                category_id=sample_category_data['id'],
                name=f'دکمه {i}',
            )

        buttons = button_service.get_buttons_with_stats(limit=10)
        assert len(buttons) >= 2
        for btn in buttons:
            assert 'clicks' in btn
            assert 'orders' in btn
            assert 'revenue' in btn

    # ============================================================
    # تست‌های ساختار منو
    # ============================================================

    def test_get_menu_keyboard_data(self, button_service, sample_category_data):
        """تست دریافت داده‌های کیبورد منو"""
        button_service.create_button(
            category_id=sample_category_data['id'],
            name='دکمه منو',
            location='main',
        )

        data = button_service.get_menu_keyboard_data('main')
        assert 'buttons' in data
        assert 'category_columns' in data
        assert 'total_buttons' in data

    def test_get_button_tree(self, button_service, sample_category_data):
        """تست دریافت ساختار درختی منو"""
        parent = button_service.create_button(
            category_id=sample_category_data['id'],
            name='والد',
            has_submenu=True,
        )
        button_service.create_button(
            category_id=sample_category_data['id'],
            name='زیرمنو',
            parent_button_id=parent['id'],
        )

        tree = button_service.get_button_tree('main')
        assert isinstance(tree, list)
        if tree:
            assert 'buttons' in tree[0]