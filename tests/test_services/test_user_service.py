# tests/test_services/test_user_service.py
# تست‌های واحد برای UserService

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from services.user_service import UserService
from models.user import User, UserRole, UserStatus


class TestUserService:
    """تست‌های UserService"""

    @pytest.fixture
    def user_service(self, db_connection):
        """ایجاد UserService با اتصال دیتابیس تست"""
        return UserService(db_connection)

    @pytest.fixture
    def sample_user_data(self):
        """داده‌های نمونه کاربر"""
        return {
            'user_id': 123456789,
            'username': 'test_user',
            'first_name': 'علی',
            'last_name': 'محمدی',
        }

    # ============================================================
    # تست‌های ایجاد و دریافت کاربر
    # ============================================================

    def test_get_or_create_user_new(self, user_service, sample_user_data):
        """تست ایجاد کاربر جدید"""
        user = user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name'],
        )

        assert user is not None
        assert user['user_id'] == sample_user_data['user_id']
        assert user['username'] == sample_user_data['username']
        assert user['first_name'] == sample_user_data['first_name']
        assert user['last_name'] == sample_user_data['last_name']

    def test_get_or_create_user_existing(self, user_service, sample_user_data):
        """تست دریافت کاربر موجود"""
        # ایجاد کاربر
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name'],
        )

        # دریافت مجدد
        user = user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username='new_username',
            first_name='نام جدید',
        )

        assert user is not None
        assert user['user_id'] == sample_user_data['user_id']
        # اطلاعات قبلی باید حفظ شود
        assert user['username'] == sample_user_data['username']
        assert user['first_name'] == sample_user_data['first_name']

    def test_get_user_by_id(self, user_service, sample_user_data):
        """تست دریافت کاربر با شناسه"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        user = user_service.get_user(sample_user_data['user_id'])
        assert user is not None
        assert user['user_id'] == sample_user_data['user_id']

    def test_get_user_not_found(self, user_service):
        """تست دریافت کاربر ناموجود"""
        user = user_service.get_user(99999)
        assert user is None

    def test_get_user_by_username(self, user_service, sample_user_data):
        """تست دریافت کاربر با نام کاربری"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        user = user_service.get_user_by_username(sample_user_data['username'])
        assert user is not None
        assert user['user_id'] == sample_user_data['user_id']

    # ============================================================
    # تست‌های آمار کاربران
    # ============================================================

    def test_get_total_users(self, user_service, sample_user_data):
        """تست دریافت تعداد کل کاربران"""
        initial_count = user_service.get_total_users()
        
        # ایجاد چند کاربر
        for i in range(5):
            user_service.get_or_create_user(
                user_id=sample_user_data['user_id'] + i,
                username=f'user_{i}',
            )

        final_count = user_service.get_total_users()
        assert final_count == initial_count + 5

    def test_get_active_users(self, user_service, sample_user_data):
        """تست دریافت کاربران فعال"""
        # ایجاد کاربر
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )
        
        # به‌روزرسانی last_active
        user_service.update_last_active(sample_user_data['user_id'])

        active_users = user_service.get_active_users(days=1)
        assert len(active_users) >= 1

    def test_get_active_count(self, user_service, sample_user_data):
        """تست دریافت تعداد کاربران فعال"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )
        user_service.update_last_active(sample_user_data['user_id'])

        count = user_service.get_active_count(days=1)
        assert count >= 1

    # ============================================================
    # تست‌های مسدودیت کاربران
    # ============================================================

    def test_block_user(self, user_service, sample_user_data):
        """تست مسدود کردن کاربر"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        result = user_service.block_user(
            user_id=sample_user_data['user_id'],
            reason='تست مسدودیت',
        )

        assert result is True

        user = user_service.get_user(sample_user_data['user_id'])
        assert user['is_blocked'] == 1

    def test_unblock_user(self, user_service, sample_user_data):
        """تست رفع مسدودیت کاربر"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )
        
        # مسدود کردن
        user_service.block_user(sample_user_data['user_id'])
        
        # رفع مسدودیت
        result = user_service.unblock_user(sample_user_data['user_id'])
        assert result is True

        user = user_service.get_user(sample_user_data['user_id'])
        assert user['is_blocked'] == 0

    def test_is_blocked(self, user_service, sample_user_data):
        """تست بررسی مسدود بودن کاربر"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        assert user_service.is_blocked(sample_user_data['user_id']) is False
        
        user_service.block_user(sample_user_data['user_id'])
        assert user_service.is_blocked(sample_user_data['user_id']) is True

    def test_get_blocked_users(self, user_service, sample_user_data):
        """تست دریافت لیست کاربران مسدود شده"""
        # ایجاد کاربران
        for i in range(3):
            user_id = sample_user_data['user_id'] + i
            user_service.get_or_create_user(
                user_id=user_id,
                username=f'user_{i}',
            )
            if i % 2 == 0:
                user_service.block_user(user_id)

        blocked_users = user_service.get_blocked_users()
        assert len(blocked_users) >= 1

    # ============================================================
    # تست‌های جستجو
    # ============================================================

    def test_search_users(self, user_service, sample_user_data):
        """تست جستجوی کاربران"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name'],
        )

        # جستجو با نام کاربری
        results = user_service.search_users('test_user')
        assert len(results) >= 1

        # جستجو با نام
        results = user_service.search_users('علی')
        assert len(results) >= 1

        # جستجو با شناسه
        results = user_service.search_users(str(sample_user_data['user_id']))
        assert len(results) >= 1

    def test_get_users_with_stats(self, user_service, sample_user_data):
        """تست دریافت کاربران با آمار سفارشات"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        results = user_service.get_users_with_stats(limit=10)
        assert isinstance(results, list)
        if results:
            assert 'orders_count' in results[0]
            assert 'total_payment' in results[0]

    # ============================================================
    # تست‌های نقش کاربران
    # ============================================================

    def test_get_user_role(self, user_service, sample_user_data):
        """تست دریافت نقش کاربر"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        role = user_service.get_user_role(sample_user_data['user_id'])
        # نقش پیش‌فرض باید USER باشد
        assert role == 'USER'

    def test_is_admin(self, user_service, sample_user_data):
        """تست بررسی ادمین بودن کاربر"""
        # کاربر عادی
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )
        assert user_service.is_admin(sample_user_data['user_id']) is False

        # با استفاده از patch برای is_admin دیتابیس
        with patch('database.is_admin', return_value=True):
            assert user_service.is_admin(sample_user_data['user_id']) is True

    def test_is_owner(self, user_service, sample_user_data):
        """تست بررسی مالک بودن کاربر"""
        # با استفاده از patch برای config.OWNER_ID
        with patch('config.config.OWNER_ID', sample_user_data['user_id']):
            assert user_service.is_owner(sample_user_data['user_id']) is True

    # ============================================================
    # تست‌های نمایشی
    # ============================================================

    def test_get_user_display_name(self, user_service, sample_user_data):
        """تست دریافت نام نمایشی کاربر"""
        user = user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name'],
        )

        display_name = user_service.get_user_display_name(sample_user_data['user_id'])
        assert display_name == f"{sample_user_data['first_name']} {sample_user_data['last_name']}"

    def test_get_user_display_name_only_first_name(self, user_service, sample_user_data):
        """تست دریافت نام نمایشی با فقط نام کوچک"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
            first_name=sample_user_data['first_name'],
            last_name=None,
        )

        display_name = user_service.get_user_display_name(sample_user_data['user_id'])
        assert display_name == sample_user_data['first_name']

    def test_get_user_display_name_only_username(self, user_service, sample_user_data):
        """تست دریافت نام نمایشی با فقط نام کاربری"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
            first_name=None,
            last_name=None,
        )

        display_name = user_service.get_user_display_name(sample_user_data['user_id'])
        assert display_name == f"@{sample_user_data['username']}"

    # ============================================================
    # تست‌های به‌روزرسانی
    # ============================================================

    def test_update_last_active(self, user_service, sample_user_data):
        """تست به‌روزرسانی آخرین فعالیت"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        old_last_active = user_service.get_user(sample_user_data['user_id'])['last_active']
        
        # به‌روزرسانی
        result = user_service.update_last_active(sample_user_data['user_id'])
        assert result is True

        new_last_active = user_service.get_user(sample_user_data['user_id'])['last_active']
        assert new_last_active != old_last_active

    def test_update_role(self, user_service, sample_user_data):
        """تست تغییر نقش کاربر"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        result = user_service.update_role(
            user_id=sample_user_data['user_id'],
            role=UserRole.ADMIN.value,
        )

        assert result is True
        role = user_service.get_user_role(sample_user_data['user_id'])
        assert role == 'ADMIN'

    # ============================================================
    # تست‌های گروه‌بندی
    # ============================================================

    def test_get_users_by_role(self, user_service, sample_user_data):
        """تست دریافت کاربران بر اساس نقش"""
        # ایجاد کاربران با نقش‌های مختلف
        for i in range(3):
            user_id = sample_user_data['user_id'] + i
            user_service.get_or_create_user(
                user_id=user_id,
                username=f'user_{i}',
            )
            if i == 0:
                user_service.update_role(user_id, UserRole.ADMIN.value)

        users = user_service.get_users_by_role(UserRole.ADMIN.value)
        assert len(users) >= 1

    def test_get_users_summary(self, user_service, sample_user_data):
        """تست دریافت خلاصه کاربران"""
        # ایجاد چند کاربر
        for i in range(5):
            user_service.get_or_create_user(
                user_id=sample_user_data['user_id'] + i,
                username=f'user_{i}',
            )

        summary = user_service.get_users_summary()
        assert 'total_users' in summary
        assert summary['total_users'] >= 5

    def test_get_recent_users(self, user_service, sample_user_data):
        """تست دریافت کاربران جدید"""
        # ایجاد کاربران جدید
        for i in range(3):
            user_service.get_or_create_user(
                user_id=sample_user_data['user_id'] + i,
                username=f'new_user_{i}',
            )

        recent_users = user_service.get_recent_users(limit=10)
        assert len(recent_users) >= 3

    # ============================================================
    # تست‌های امنیتی
    # ============================================================

    def test_can_user_access_admin_owner(self, user_service, sample_user_data):
        """تست دسترسی مالک به پنل مدیریت"""
        with patch('config.config.OWNER_ID', sample_user_data['user_id']):
            result = user_service.can_user_access_admin(sample_user_data['user_id'])
            assert result is True

    def test_can_user_access_admin_admin(self, user_service, sample_user_data):
        """تست دسترسی ادمین به پنل مدیریت"""
        with patch('database.is_admin', return_value=True):
            result = user_service.can_user_access_admin(sample_user_data['user_id'])
            assert result is True

    def test_can_user_access_admin_regular(self, user_service, sample_user_data):
        """تست عدم دسترسی کاربر عادی به پنل مدیریت"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )
        
        with patch('database.is_admin', return_value=False):
            result = user_service.can_user_access_admin(sample_user_data['user_id'])
            assert result is False

    def test_get_user_permissions_owner(self, user_service, sample_user_data):
        """تست دریافت مجوزهای مالک"""
        with patch('config.config.OWNER_ID', sample_user_data['user_id']):
            permissions = user_service.get_user_permissions(sample_user_data['user_id'])
            assert '*' in permissions

    def test_get_user_permissions_admin(self, user_service, sample_user_data):
        """تست دریافت مجوزهای ادمین"""
        with patch('database.is_admin', return_value=True):
            with patch('database.get_user_role', return_value='admin'):
                permissions = user_service.get_user_permissions(sample_user_data['user_id'])
                assert isinstance(permissions, list)

    # ============================================================
    # تست‌های فیلتر پیشرفته
    # ============================================================

    def test_get_users_with_filter(self, user_service, sample_user_data):
        """تست دریافت کاربران با فیلتر"""
        # ایجاد کاربران
        for i in range(5):
            user_id = sample_user_data['user_id'] + i
            user_service.get_or_create_user(
                user_id=user_id,
                username=f'user_{i}',
            )
            if i % 2 == 0:
                user_service.block_user(user_id)

        # فیلتر کاربران مسدود شده
        filters = {'is_blocked': True}
        users = user_service.get_users_with_filter(filters, limit=10)
        assert len(users) >= 2

    def test_get_users_with_filter_count(self, user_service, sample_user_data):
        """تست تعداد نتایج فیلتر کاربران"""
        # ایجاد کاربران
        for i in range(5):
            user_service.get_or_create_user(
                user_id=sample_user_data['user_id'] + i,
                username=f'user_{i}',
            )

        filters = {'active_since': 1}
        count = user_service.get_users_with_filter_count(filters)
        assert isinstance(count, int)

    # ============================================================
    # تست‌های کاربران ویژه
    # ============================================================

    def test_get_user_by_id_or_username(self, user_service, sample_user_data):
        """تست دریافت کاربر با شناسه یا نام کاربری"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        # با شناسه
        user = user_service.get_user_by_id_or_username(str(sample_user_data['user_id']))
        assert user is not None

        # با نام کاربری
        user = user_service.get_user_by_id_or_username(sample_user_data['username'])
        assert user is not None

        # با @username
        user = user_service.get_user_by_id_or_username(f"@{sample_user_data['username']}")
        assert user is not None

    def test_get_user_status(self, user_service, sample_user_data):
        """تست دریافت وضعیت کاربر"""
        user_service.get_or_create_user(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        status = user_service.get_user_status(sample_user_data['user_id'])
        assert status == 'active'

        user_service.block_user(sample_user_data['user_id'])
        status = user_service.get_user_status(sample_user_data['user_id'])
        assert status == 'blocked'

    def test_get_user_by_id_or_username_not_found(self, user_service):
        """تست دریافت کاربر ناموجود"""
        user = user_service.get_user_by_id_or_username('99999')
        assert user is None

        user = user_service.get_user_by_id_or_username('non_existent')
        assert user is None