# tests/test_services/test_cache_service.py
# تست‌های واحد برای CacheService

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from services.cache_service import CacheService


class TestCacheService:
    """تست‌های CacheService"""

    @pytest.fixture
    def mock_cache_manager(self):
        """ایجاد Mock برای CacheManager"""
        mock = MagicMock()
        mock._enabled = True
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.delete_pattern = AsyncMock(return_value=2)
        mock.exists = AsyncMock(return_value=False)
        mock.get_or_set = AsyncMock(return_value=None)
        mock.incr = AsyncMock(return_value=5)
        return mock

    @pytest.fixture
    def cache_service(self, mock_cache_manager):
        """ایجاد CacheService با Mock CacheManager"""
        return CacheService(connection=None, cache_manager=mock_cache_manager)

    @pytest.fixture
    def cache_service_disabled(self, mock_cache_manager):
        """ایجاد CacheService با کش غیرفعال"""
        mock_cache_manager._enabled = False
        return CacheService(connection=None, cache_manager=mock_cache_manager)

    @pytest.fixture
    def sample_user_data(self):
        """داده‌های نمونه کاربر"""
        return {
            'user_id': 123456789,
            'username': 'test_user',
            'first_name': 'علی',
            'last_name': 'محمدی',
            'is_blocked': 0,
        }

    @pytest.fixture
    def sample_button_data(self):
        """داده‌های نمونه دکمه"""
        return {
            'id': 1,
            'name': 'سرویس تست',
            'category_id': 1,
            'callback_data': 'btn_test',
            'is_active': 1,
        }

    @pytest.fixture
    def sample_order_data(self):
        """داده‌های نمونه سفارش"""
        return {
            'id': 1,
            'user_id': 123456789,
            'button_id': 1,
            'payment_amount': 50000,
            'status': 'pending',
        }

    @pytest.fixture
    def sample_category_data(self):
        """داده‌های نمونه دسته‌بندی"""
        return {
            'id': 1,
            'name': 'دسته تست',
            'location': 'main',
            'is_active': 1,
        }

    # ============================================================
    # تست‌های متدهای عمومی
    # ============================================================

    async def test_get_when_enabled(self, cache_service, mock_cache_manager):
        """تست get وقتی کش فعال است"""
        mock_cache_manager.get.return_value = {'key': 'value'}

        result = await cache_service.get('test_key')

        assert result == {'key': 'value'}
        mock_cache_manager.get.assert_called_once_with('test_key')

    async def test_get_when_disabled(self, cache_service_disabled, mock_cache_manager):
        """تست get وقتی کش غیرفعال است"""
        result = await cache_service_disabled.get('test_key', default={'default': True})

        assert result == {'default': True}
        mock_cache_manager.get.assert_not_called()

    async def test_set_when_enabled(self, cache_service, mock_cache_manager):
        """تست set وقتی کش فعال است"""
        result = await cache_service.set('test_key', {'value': 123}, ttl=60)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('test_key', {'value': 123}, 60)

    async def test_set_when_disabled(self, cache_service_disabled, mock_cache_manager):
        """تست set وقتی کش غیرفعال است"""
        result = await cache_service_disabled.set('test_key', {'value': 123})

        assert result is False
        mock_cache_manager.set.assert_not_called()

    async def test_delete_when_enabled(self, cache_service, mock_cache_manager):
        """تست delete وقتی کش فعال است"""
        result = await cache_service.delete('key1', 'key2')

        assert result == 2
        mock_cache_manager.delete.assert_called_once_with('key1', 'key2')

    async def test_delete_when_disabled(self, cache_service_disabled, mock_cache_manager):
        """تست delete وقتی کش غیرفعال است"""
        result = await cache_service_disabled.delete('key1', 'key2')

        assert result == 0
        mock_cache_manager.delete.assert_not_called()

    async def test_delete_pattern_when_enabled(self, cache_service, mock_cache_manager):
        """تست delete_pattern وقتی کش فعال است"""
        result = await cache_service.delete_pattern('user:*')

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('user:*')

    async def test_delete_pattern_when_disabled(self, cache_service_disabled, mock_cache_manager):
        """تست delete_pattern وقتی کش غیرفعال است"""
        result = await cache_service_disabled.delete_pattern('user:*')

        assert result == 0
        mock_cache_manager.delete_pattern.assert_not_called()

    async def test_exists_when_enabled(self, cache_service, mock_cache_manager):
        """تست exists وقتی کش فعال است"""
        mock_cache_manager.exists.return_value = True

        result = await cache_service.exists('test_key')

        assert result is True
        mock_cache_manager.exists.assert_called_once_with('test_key')

    async def test_exists_when_disabled(self, cache_service_disabled, mock_cache_manager):
        """تست exists وقتی کش غیرفعال است"""
        result = await cache_service_disabled.exists('test_key')

        assert result is False
        mock_cache_manager.exists.assert_not_called()

    async def test_get_or_set_when_enabled(self, cache_service, mock_cache_manager):
        """تست get_or_set وقتی کش فعال است"""
        async def func():
            return {'computed': 'value'}

        mock_cache_manager.get_or_set.return_value = {'computed': 'value'}

        result = await cache_service.get_or_set('test_key', func, ttl=60)

        assert result == {'computed': 'value'}
        mock_cache_manager.get_or_set.assert_called_once_with('test_key', func, 60)

    async def test_get_or_set_when_disabled(self, cache_service_disabled, mock_cache_manager):
        """تست get_or_set وقتی کش غیرفعال است"""
        async def func():
            return {'computed': 'value'}

        result = await cache_service_disabled.get_or_set('test_key', func)

        assert result == {'computed': 'value'}
        mock_cache_manager.get_or_set.assert_not_called()

    # ============================================================
    # تست‌های کش کاربران
    # ============================================================

    async def test_get_user_success(self, cache_service, mock_cache_manager, sample_user_data):
        """تست دریافت کاربر از کش"""
        mock_cache_manager.get.return_value = sample_user_data

        result = await cache_service.get_user(123456789)

        assert result == sample_user_data
        mock_cache_manager.get.assert_called_once_with('user:123456789')

    async def test_get_user_not_found(self, cache_service, mock_cache_manager):
        """تست دریافت کاربر ناموجود از کش"""
        mock_cache_manager.get.return_value = None

        result = await cache_service.get_user(123456789)

        assert result is None
        mock_cache_manager.get.assert_called_once_with('user:123456789')

    async def test_set_user_success(self, cache_service, mock_cache_manager, sample_user_data):
        """تست ذخیره کاربر در کش"""
        result = await cache_service.set_user(123456789, sample_user_data, ttl=300)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('user:123456789', sample_user_data, 300)

    async def test_delete_user_success(self, cache_service, mock_cache_manager):
        """تست حذف کاربر از کش"""
        result = await cache_service.delete_user(123456789)

        assert result is True
        mock_cache_manager.delete.assert_called_once_with('user:123456789')

    async def test_invalidate_users(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش همه کاربران"""
        result = await cache_service.invalidate_users()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('user:*')

    # ============================================================
    # تست‌های کش دکمه‌ها
    # ============================================================

    async def test_get_button_success(self, cache_service, mock_cache_manager, sample_button_data):
        """تست دریافت دکمه از کش"""
        mock_cache_manager.get.return_value = sample_button_data

        result = await cache_service.get_button(1)

        assert result == sample_button_data
        mock_cache_manager.get.assert_called_once_with('button:1')

    async def test_set_button_success(self, cache_service, mock_cache_manager, sample_button_data):
        """تست ذخیره دکمه در کش"""
        result = await cache_service.set_button(1, sample_button_data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('button:1', sample_button_data, None)

    async def test_delete_button_success(self, cache_service, mock_cache_manager):
        """تست حذف دکمه از کش"""
        result = await cache_service.delete_button(1)

        assert result is True
        mock_cache_manager.delete.assert_called_once_with('button:1')

    async def test_get_buttons_by_location(self, cache_service, mock_cache_manager):
        """تست دریافت دکمه‌های یک مکان از کش"""
        mock_cache_manager.get.return_value = [{'id': 1, 'name': 'دکمه ۱'}]

        result = await cache_service.get_buttons_by_location('main')

        assert result == [{'id': 1, 'name': 'دکمه ۱'}]
        mock_cache_manager.get.assert_called_once_with('buttons:location:main')

    async def test_set_buttons_by_location(self, cache_service, mock_cache_manager):
        """تست ذخیره دکمه‌های یک مکان در کش"""
        data = [{'id': 1, 'name': 'دکمه ۱'}]
        result = await cache_service.set_buttons_by_location('main', data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('buttons:location:main', data, None)

    async def test_invalidate_buttons(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش همه دکمه‌ها"""
        result = await cache_service.invalidate_buttons()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('button:*')

    async def test_invalidate_buttons_by_location(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش دکمه‌های یک مکان"""
        result = await cache_service.invalidate_buttons_by_location('main')

        assert result == 2
        mock_cache_manager.delete.assert_called_once_with('buttons:location:main')

    # ============================================================
    # تست‌های کش دسته‌بندی‌ها
    # ============================================================

    async def test_get_category_success(self, cache_service, mock_cache_manager, sample_category_data):
        """تست دریافت دسته‌بندی از کش"""
        mock_cache_manager.get.return_value = sample_category_data

        result = await cache_service.get_category(1)

        assert result == sample_category_data
        mock_cache_manager.get.assert_called_once_with('category:1')

    async def test_set_category_success(self, cache_service, mock_cache_manager, sample_category_data):
        """تست ذخیره دسته‌بندی در کش"""
        result = await cache_service.set_category(1, sample_category_data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('category:1', sample_category_data, None)

    async def test_delete_category_success(self, cache_service, mock_cache_manager):
        """تست حذف دسته‌بندی از کش"""
        result = await cache_service.delete_category(1)

        assert result is True
        mock_cache_manager.delete.assert_called_once_with('category:1')

    async def test_get_categories_all(self, cache_service, mock_cache_manager):
        """تست دریافت همه دسته‌بندی‌ها از کش"""
        mock_cache_manager.get.return_value = [{'id': 1, 'name': 'دسته ۱'}]

        result = await cache_service.get_categories_all()

        assert result == [{'id': 1, 'name': 'دسته ۱'}]
        mock_cache_manager.get.assert_called_once_with('categories:all')

    async def test_set_categories_all(self, cache_service, mock_cache_manager):
        """تست ذخیره همه دسته‌بندی‌ها در کش"""
        data = [{'id': 1, 'name': 'دسته ۱'}]
        result = await cache_service.set_categories_all(data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('categories:all', data, None)

    async def test_invalidate_categories(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش همه دسته‌بندی‌ها"""
        result = await cache_service.invalidate_categories()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('category:*')

    # ============================================================
    # تست‌های کش سفارشات
    # ============================================================

    async def test_get_order_success(self, cache_service, mock_cache_manager, sample_order_data):
        """تست دریافت سفارش از کش"""
        mock_cache_manager.get.return_value = sample_order_data

        result = await cache_service.get_order(1)

        assert result == sample_order_data
        mock_cache_manager.get.assert_called_once_with('order:1')

    async def test_set_order_success(self, cache_service, mock_cache_manager, sample_order_data):
        """تست ذخیره سفارش در کش"""
        result = await cache_service.set_order(1, sample_order_data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('order:1', sample_order_data, None)

    async def test_delete_order_success(self, cache_service, mock_cache_manager):
        """تست حذف سفارش از کش"""
        result = await cache_service.delete_order(1)

        assert result is True
        mock_cache_manager.delete.assert_called_once_with('order:1')

    async def test_get_orders_by_status(self, cache_service, mock_cache_manager):
        """تست دریافت سفارشات بر اساس وضعیت از کش"""
        mock_cache_manager.get.return_value = [{'id': 1, 'status': 'pending'}]

        result = await cache_service.get_orders_by_status('pending')

        assert result == [{'id': 1, 'status': 'pending'}]
        mock_cache_manager.get.assert_called_once_with('orders:status:pending')

    async def test_set_orders_by_status(self, cache_service, mock_cache_manager):
        """تست ذخیره سفارشات بر اساس وضعیت در کش"""
        data = [{'id': 1, 'status': 'pending'}]
        result = await cache_service.set_orders_by_status('pending', data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('orders:status:pending', data, None)

    async def test_get_orders_by_user(self, cache_service, mock_cache_manager):
        """تست دریافت سفارشات یک کاربر از کش"""
        mock_cache_manager.get.return_value = [{'id': 1, 'user_id': 123}]

        result = await cache_service.get_orders_by_user(123)

        assert result == [{'id': 1, 'user_id': 123}]
        mock_cache_manager.get.assert_called_once_with('orders:user:123')

    async def test_set_orders_by_user(self, cache_service, mock_cache_manager):
        """تست ذخیره سفارشات یک کاربر در کش"""
        data = [{'id': 1, 'user_id': 123}]
        result = await cache_service.set_orders_by_user(123, data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('orders:user:123', data, None)

    async def test_invalidate_orders(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش همه سفارشات"""
        result = await cache_service.invalidate_orders()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('order:*')

    async def test_invalidate_orders_by_status(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش سفارشات با وضعیت خاص"""
        result = await cache_service.invalidate_orders_by_status('pending')

        assert result == 2
        mock_cache_manager.delete.assert_called_once_with('orders:status:pending')

    # ============================================================
    # تست‌های کش تنظیمات
    # ============================================================

    async def test_get_setting(self, cache_service, mock_cache_manager):
        """تست دریافت تنظیمات از کش"""
        mock_cache_manager.get.return_value = 'test_value'

        result = await cache_service.get_setting('test_key')

        assert result == 'test_value'
        mock_cache_manager.get.assert_called_once_with('setting:test_key')

    async def test_set_setting(self, cache_service, mock_cache_manager):
        """تست ذخیره تنظیمات در کش"""
        result = await cache_service.set_setting('test_key', 'test_value')

        assert result is True
        mock_cache_manager.set.assert_called_once_with('setting:test_key', 'test_value', None)

    async def test_delete_setting(self, cache_service, mock_cache_manager):
        """تست حذف تنظیمات از کش"""
        result = await cache_service.delete_setting('test_key')

        assert result is True
        mock_cache_manager.delete.assert_called_once_with('setting:test_key')

    async def test_get_settings_all(self, cache_service, mock_cache_manager):
        """تست دریافت همه تنظیمات از کش"""
        mock_cache_manager.get.return_value = {'key1': 'value1'}

        result = await cache_service.get_settings_all()

        assert result == {'key1': 'value1'}
        mock_cache_manager.get.assert_called_once_with('settings:all')

    async def test_set_settings_all(self, cache_service, mock_cache_manager):
        """تست ذخیره همه تنظیمات در کش"""
        data = {'key1': 'value1'}
        result = await cache_service.set_settings_all(data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('settings:all', data, None)

    async def test_invalidate_settings(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش تنظیمات"""
        result = await cache_service.invalidate_settings()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('setting:*')

    # ============================================================
    # تست‌های کش برندینگ
    # ============================================================

    async def test_get_branding(self, cache_service, mock_cache_manager):
        """تست دریافت متن برندینگ از کش"""
        mock_cache_manager.get.return_value = 'متن برندینگ'

        result = await cache_service.get_branding('brand_welcome_text')

        assert result == 'متن برندینگ'
        mock_cache_manager.get.assert_called_once_with('branding:brand_welcome_text')

    async def test_set_branding(self, cache_service, mock_cache_manager):
        """تست ذخیره متن برندینگ در کش"""
        result = await cache_service.set_branding('brand_welcome_text', 'متن جدید')

        assert result is True
        mock_cache_manager.set.assert_called_once_with('branding:brand_welcome_text', 'متن جدید', None)

    async def test_delete_branding(self, cache_service, mock_cache_manager):
        """تست حذف متن برندینگ از کش"""
        result = await cache_service.delete_branding('brand_welcome_text')

        assert result is True
        mock_cache_manager.delete.assert_called_once_with('branding:brand_welcome_text')

    async def test_get_branding_all(self, cache_service, mock_cache_manager):
        """تست دریافت همه متون برندینگ از کش"""
        mock_cache_manager.get.return_value = {'welcome': 'متن خوش‌آمدگویی'}

        result = await cache_service.get_branding_all()

        assert result == {'welcome': 'متن خوش‌آمدگویی'}
        mock_cache_manager.get.assert_called_once_with('branding:all')

    async def test_set_branding_all(self, cache_service, mock_cache_manager):
        """تست ذخیره همه متون برندینگ در کش"""
        data = {'welcome': 'متن خوش‌آمدگویی'}
        result = await cache_service.set_branding_all(data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('branding:all', data, None)

    async def test_invalidate_branding(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش برندینگ"""
        result = await cache_service.invalidate_branding()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('branding:*')

    # ============================================================
    # تست‌های کش آمار
    # ============================================================

    async def test_get_stats_dashboard(self, cache_service, mock_cache_manager):
        """تست دریافت آمار داشبورد از کش"""
        mock_cache_manager.get.return_value = {'total_users': 100}

        result = await cache_service.get_stats_dashboard()

        assert result == {'total_users': 100}
        mock_cache_manager.get.assert_called_once_with('stats:dashboard')

    async def test_set_stats_dashboard(self, cache_service, mock_cache_manager):
        """تست ذخیره آمار داشبورد در کش"""
        data = {'total_users': 100}
        result = await cache_service.set_stats_dashboard(data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('stats:dashboard', data, None)

    async def test_invalidate_stats(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش آمار"""
        result = await cache_service.invalidate_stats()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('stats:*')

    # ============================================================
    # تست‌های کش ادمین‌ها
    # ============================================================

    async def test_get_admin(self, cache_service, mock_cache_manager):
        """تست دریافت ادمین از کش"""
        mock_cache_manager.get.return_value = {'user_id': 123, 'role': 'admin'}

        result = await cache_service.get_admin(123)

        assert result == {'user_id': 123, 'role': 'admin'}
        mock_cache_manager.get.assert_called_once_with('admin:123')

    async def test_set_admin(self, cache_service, mock_cache_manager):
        """تست ذخیره ادمین در کش"""
        data = {'user_id': 123, 'role': 'admin'}
        result = await cache_service.set_admin(123, data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('admin:123', data, None)

    async def test_delete_admin(self, cache_service, mock_cache_manager):
        """تست حذف ادمین از کش"""
        result = await cache_service.delete_admin(123)

        assert result is True
        mock_cache_manager.delete.assert_called_once_with('admin:123')

    async def test_get_admins_all(self, cache_service, mock_cache_manager):
        """تست دریافت لیست همه ادمین‌ها از کش"""
        mock_cache_manager.get.return_value = [{'user_id': 123, 'role': 'admin'}]

        result = await cache_service.get_admins_all()

        assert result == [{'user_id': 123, 'role': 'admin'}]
        mock_cache_manager.get.assert_called_once_with('admins:all')

    async def test_set_admins_all(self, cache_service, mock_cache_manager):
        """تست ذخیره لیست همه ادمین‌ها در کش"""
        data = [{'user_id': 123, 'role': 'admin'}]
        result = await cache_service.set_admins_all(data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('admins:all', data, None)

    async def test_invalidate_admins(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش ادمین‌ها"""
        result = await cache_service.invalidate_admins()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('admin:*')

    # ============================================================
    # تست‌های کش نسخه‌سازی
    # ============================================================

    async def test_get_versions(self, cache_service, mock_cache_manager):
        """تست دریافت نسخه‌های یک دکمه از کش"""
        mock_cache_manager.get.return_value = [{'version_number': 1}]

        result = await cache_service.get_versions(1)

        assert result == [{'version_number': 1}]
        mock_cache_manager.get.assert_called_once_with('versions:button:1')

    async def test_set_versions(self, cache_service, mock_cache_manager):
        """تست ذخیره نسخه‌های یک دکمه در کش"""
        data = [{'version_number': 1}]
        result = await cache_service.set_versions(1, data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('versions:button:1', data, None)

    async def test_invalidate_versions_all(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش همه نسخه‌ها"""
        result = await cache_service.invalidate_versions()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('versions:*')

    async def test_invalidate_versions_by_button(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش نسخه‌های یک دکمه"""
        result = await cache_service.invalidate_versions(button_id=1)

        assert result == 2
        mock_cache_manager.delete.assert_called_once_with('versions:button:1')

    # ============================================================
    # تست‌های کش ستون‌ها
    # ============================================================

    async def test_get_effective_columns(self, cache_service, mock_cache_manager):
        """تست دریافت ستون‌های مؤثر از کش"""
        mock_cache_manager.get.return_value = 3

        result = await cache_service.get_effective_columns(button_id=1, category_id=1)

        assert result == 3
        mock_cache_manager.get.assert_called_once_with('columns:effective:1:1')

    async def test_set_effective_columns(self, cache_service, mock_cache_manager):
        """تست ذخیره ستون‌های مؤثر در کش"""
        result = await cache_service.set_effective_columns(3, button_id=1, category_id=1)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('columns:effective:1:1', 3, None)

    async def test_invalidate_columns(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش ستون‌ها"""
        result = await cache_service.invalidate_columns()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('columns:*')

    # ============================================================
    # تست‌های invalidate_all
    # ============================================================

    async def test_invalidate_all(self, cache_service, mock_cache_manager):
        """تست پاک کردن همه کش‌ها"""
        mock_cache_manager.delete_pattern.return_value = 5

        result = await cache_service.invalidate_all()

        # حداقل ۶ الگو باید پاک شوند
        assert mock_cache_manager.delete_pattern.call_count >= 5
        assert result['total'] >= 10

    async def test_invalidate_all_with_disabled_cache(self, cache_service_disabled, mock_cache_manager):
        """تست پاک کردن همه کش‌ها وقتی کش غیرفعال است"""
        result = await cache_service_disabled.invalidate_all()

        assert result['total'] == 0
        mock_cache_manager.delete_pattern.assert_not_called()

    # ============================================================
    # تست‌های invalidate_cache_by_prefix
    # ============================================================

    async def test_invalidate_cache_by_prefix(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش با پیشوند"""
        result = await cache_service.invalidate_cache_by_prefix('user')

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('user:*')

    async def test_invalidate_cache_by_prefix_disabled(self, cache_service_disabled, mock_cache_manager):
        """تست پاک کردن کش با پیشوند وقتی کش غیرفعال است"""
        result = await cache_service_disabled.invalidate_cache_by_prefix('user')

        assert result == 0
        mock_cache_manager.delete_pattern.assert_not_called()

    # ============================================================
    # تست‌های get_stats
    # ============================================================

    async def test_get_stats_when_enabled(self, cache_service, mock_cache_manager):
        """تست دریافت آمار کش وقتی فعال است"""
        mock_redis = MagicMock()
        mock_redis.keys.return_value = ['user:1', 'button:1', 'category:1', 'order:1', 'other:1']
        mock_cache_manager._cache._get_redis = AsyncMock(return_value=mock_redis)

        result = await cache_service.get_stats()

        assert result['enabled'] is True
        assert result['connected'] is True
        assert result['total_keys'] == 5
        assert 'user' in result['key_count_by_pattern']
        assert 'button' in result['key_count_by_pattern']

    async def test_get_stats_when_disabled(self, cache_service_disabled):
        """تست دریافت آمار کش وقتی غیرفعال است"""
        result = await cache_service_disabled.get_stats()

        assert result['enabled'] is False
        assert result['message'] == 'Cache is disabled'

    async def test_get_stats_redis_not_connected(self, cache_service, mock_cache_manager):
        """تست دریافت آمار کش وقتی Redis متصل نیست"""
        mock_cache_manager._cache._get_redis = AsyncMock(return_value=None)

        result = await cache_service.get_stats()

        assert result['enabled'] is True
        assert result['connected'] is False

    async def test_get_stats_error(self, cache_service, mock_cache_manager):
        """تست دریافت آمار کش با خطا"""
        mock_cache_manager._cache._get_redis = AsyncMock(side_effect=Exception('Connection error'))

        result = await cache_service.get_stats()

        assert 'error' in result

    # ============================================================
    # تست‌های clear_all
    # ============================================================

    async def test_clear_all_when_enabled(self, cache_service, mock_cache_manager):
        """تست پاک کردن کامل کش وقتی فعال است"""
        mock_redis = MagicMock()
        mock_redis.flushdb = AsyncMock(return_value=True)
        mock_cache_manager._cache._get_redis = AsyncMock(return_value=mock_redis)

        result = await cache_service.clear_all()

        assert result is True
        mock_redis.flushdb.assert_called_once()

    async def test_clear_all_when_disabled(self, cache_service_disabled):
        """تست پاک کردن کامل کش وقتی غیرفعال است"""
        result = await cache_service_disabled.clear_all()

        assert result is False

    async def test_clear_all_redis_not_connected(self, cache_service, mock_cache_manager):
        """تست پاک کردن کامل کش وقتی Redis متصل نیست"""
        mock_cache_manager._cache._get_redis = AsyncMock(return_value=None)

        result = await cache_service.clear_all()

        assert result is False

    async def test_clear_all_error(self, cache_service, mock_cache_manager):
        """تست پاک کردن کامل کش با خطا"""
        mock_cache_manager._cache._get_redis = AsyncMock(side_effect=Exception('Redis error'))

        result = await cache_service.clear_all()

        assert result is False

    # ============================================================
    # تست‌های کش قیمت‌ها
    # ============================================================

    async def test_get_button_price(self, cache_service, mock_cache_manager):
        """تست دریافت اطلاعات قیمت دکمه از کش"""
        mock_cache_manager.get.return_value = {'price_amount': 50000, 'price_type': 'fixed'}

        result = await cache_service.get_button_price(1)

        assert result == {'price_amount': 50000, 'price_type': 'fixed'}
        mock_cache_manager.get.assert_called_once_with('price:button:1')

    async def test_set_button_price(self, cache_service, mock_cache_manager):
        """تست ذخیره اطلاعات قیمت دکمه در کش"""
        data = {'price_amount': 50000, 'price_type': 'fixed'}
        result = await cache_service.set_button_price(1, data)

        assert result is True
        mock_cache_manager.set.assert_called_once_with('price:button:1', data, None)

    async def test_invalidate_prices(self, cache_service, mock_cache_manager):
        """تست پاک کردن کش قیمت‌ها"""
        result = await cache_service.invalidate_prices()

        assert result == 2
        mock_cache_manager.delete_pattern.assert_called_once_with('price:*')