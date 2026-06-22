# tests/test_repositories/test_user_repository.py
# تست‌های واحد برای UserRepository

import pytest
from datetime import datetime, timedelta

from repositories.user_repository import UserRepository


class TestUserRepository:
    """تست‌های UserRepository"""

    @pytest.fixture
    def user_repo(self, db_connection):
        """ایجاد UserRepository با اتصال دیتابیس تست"""
        return UserRepository(db_connection)

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

    def test_get_or_create_new_user(self, user_repo, sample_user_data):
        """تست ایجاد کاربر جدید"""
        user = user_repo.get_or_create(
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
        assert user['first_seen'] is not None
        assert user['last_active'] is not None

    def test_get_or_create_existing_user(self, user_repo, sample_user_data):
        """تست دریافت کاربر موجود"""
        # ایجاد کاربر
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        # دریافت مجدد با اطلاعات جدید
        user = user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username='new_username',
            first_name='نام جدید',
            last_name='نام خانوادگی جدید',
        )

        assert user is not None
        assert user['user_id'] == sample_user_data['user_id']
        # اطلاعات قبلی باید حفظ شود
        assert user['username'] == sample_user_data['username']
        assert user['first_name'] == sample_user_data['first_name']

    def test_get_by_id(self, user_repo, sample_user_data):
        """تست دریافت کاربر با شناسه"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        user = user_repo.get_by_id(sample_user_data['user_id'])
        assert user is not None
        assert user['user_id'] == sample_user_data['user_id']

    def test_get_by_id_not_found(self, user_repo):
        """تست دریافت کاربر ناموجود"""
        user = user_repo.get_by_id(99999)
        assert user is None

    def test_get_by_username(self, user_repo, sample_user_data):
        """تست دریافت کاربر با نام کاربری"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        user = user_repo.get_by_username(sample_user_data['username'])
        assert user is not None
        assert user['user_id'] == sample_user_data['user_id']

    def test_get_by_username_not_found(self, user_repo):
        """تست دریافت کاربر با نام کاربری ناموجود"""
        user = user_repo.get_by_username('non_existent_user')
        assert user is None

    # ============================================================
    # تست‌های به‌روزرسانی
    # ============================================================

    def test_update_last_active(self, user_repo, sample_user_data):
        """تست به‌روزرسانی آخرین فعالیت"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        old_last_active = user_repo.get_by_id(sample_user_data['user_id'])['last_active']
        
        result = user_repo.update_last_active(sample_user_data['user_id'])
        assert result is True

        new_last_active = user_repo.get_by_id(sample_user_data['user_id'])['last_active']
        assert new_last_active != old_last_active

    # ============================================================
    # تست‌های کاربران فعال
    # ============================================================

    def test_get_active_users(self, user_repo, sample_user_data):
        """تست دریافت کاربران فعال"""
        # ایجاد کاربر
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )
        
        # به‌روزرسانی last_active
        user_repo.update_last_active(sample_user_data['user_id'])

        active_users = user_repo.get_active_users(days=1)
        assert len(active_users) >= 1
        assert active_users[0]['user_id'] == sample_user_data['user_id']

    def test_get_active_count(self, user_repo, sample_user_data):
        """تست دریافت تعداد کاربران فعال"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )
        user_repo.update_last_active(sample_user_data['user_id'])

        count = user_repo.get_active_count(days=1)
        assert count >= 1

    # ============================================================
    # تست‌های مسدودیت کاربران
    # ============================================================

    def test_block_user(self, user_repo, sample_user_data):
        """تست مسدود کردن کاربر"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        result = user_repo.block_user(
            user_id=sample_user_data['user_id'],
            reason='تست مسدودیت',
        )

        assert result is True

        user = user_repo.get_by_id(sample_user_data['user_id'])
        assert user['is_blocked'] == 1
        assert user['block_reason'] == 'تست مسدودیت'

    def test_unblock_user(self, user_repo, sample_user_data):
        """تست رفع مسدودیت کاربر"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )
        
        # مسدود کردن
        user_repo.block_user(sample_user_data['user_id'])
        
        # رفع مسدودیت
        result = user_repo.unblock_user(sample_user_data['user_id'])
        assert result is True

        user = user_repo.get_by_id(sample_user_data['user_id'])
        assert user['is_blocked'] == 0
        assert user['block_reason'] is None

    def test_is_blocked(self, user_repo, sample_user_data):
        """تست بررسی مسدود بودن کاربر"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        assert user_repo.is_blocked(sample_user_data['user_id']) is False
        
        user_repo.block_user(sample_user_data['user_id'])
        assert user_repo.is_blocked(sample_user_data['user_id']) is True

    def test_get_blocked_users(self, user_repo, sample_user_data):
        """تست دریافت لیست کاربران مسدود شده"""
        # ایجاد چند کاربر
        for i in range(3):
            user_id = sample_user_data['user_id'] + i
            user_repo.get_or_create(
                user_id=user_id,
                username=f'user_{i}',
            )
            if i % 2 == 0:
                user_repo.block_user(user_id)

        blocked_users = user_repo.get_blocked_users()
        assert len(blocked_users) >= 1

    def test_get_blocked_count(self, user_repo, sample_user_data):
        """تست تعداد کاربران مسدود شده"""
        for i in range(3):
            user_repo.get_or_create(
                user_id=sample_user_data['user_id'] + i,
                username=f'user_{i}',
            )
            if i % 2 == 0:
                user_repo.block_user(user_id)

        count = user_repo.get_blocked_count()
        assert count >= 1

    # ============================================================
    # تست‌های جستجو
    # ============================================================

    def test_search_users(self, user_repo, sample_user_data):
        """تست جستجوی کاربران"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
            first_name=sample_user_data['first_name'],
            last_name=sample_user_data['last_name'],
        )

        # جستجو با نام کاربری
        results = user_repo.search('test_user')
        assert len(results) >= 1

        # جستجو با نام
        results = user_repo.search('علی')
        assert len(results) >= 1

        # جستجو با شناسه
        results = user_repo.search(str(sample_user_data['user_id']))
        assert len(results) >= 1

        # جستجو با نام خانوادگی
        results = user_repo.search('محمدی')
        assert len(results) >= 1

    def test_search_users_with_digit(self, user_repo, sample_user_data):
        """تست جستجوی کاربران با شناسه عددی"""
        user_repo.get_or_create(
            user_id=12345,
            username='user12345',
        )

        results = user_repo.search('12345')
        assert len(results) >= 1
        assert results[0]['user_id'] == 12345 or results[0]['username'] == 'user12345'

    # ============================================================
    # تست‌های آمار
    # ============================================================

    def test_get_total_count(self, user_repo, sample_user_data):
        """تست دریافت تعداد کل کاربران"""
        initial_count = user_repo.get_total_count()
        
        # ایجاد چند کاربر
        for i in range(5):
            user_repo.get_or_create(
                user_id=sample_user_data['user_id'] + i,
                username=f'user_{i}',
            )

        final_count = user_repo.get_total_count()
        assert final_count == initial_count + 5

    def test_get_users_with_stats(self, user_repo, sample_user_data):
        """تست دریافت کاربران با آمار سفارشات"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        # ایجاد چند سفارش برای کاربر
        from repositories.order_repository import OrderRepository
        order_repo = OrderRepository(user_repo.connection)
        for i in range(3):
            order_repo.create(
                user_id=sample_user_data['user_id'],
                button_id=1,
                order_data={'test': 'data'},
                payment_amount=10000 * (i + 1),
                status='paid',
            )

        users = user_repo.get_with_stats(limit=10)
        assert len(users) >= 1
        
        # پیدا کردن کاربر مورد نظر
        target_user = next((u for u in users if u['user_id'] == sample_user_data['user_id']), None)
        assert target_user is not None
        assert target_user['orders_count'] >= 3
        assert target_user['total_payment'] >= 60000

    def test_get_recent_users(self, user_repo, sample_user_data):
        """تست دریافت کاربران جدید (اخیراً ثبت‌شده)"""
        # ایجاد کاربران جدید
        for i in range(3):
            user_repo.get_or_create(
                user_id=sample_user_data['user_id'] + i,
                username=f'new_user_{i}',
            )

        recent_users = user_repo.get_recent_users(limit=10)
        assert len(recent_users) >= 3
        # کاربران جدید باید در ابتدای لیست باشند
        assert recent_users[0]['user_id'] >= sample_user_data['user_id'] + 2

    def test_get_users_by_role(self, user_repo, sample_user_data):
        """تست دریافت کاربران بر اساس نقش"""
        # ایجاد کاربران
        for i in range(3):
            user_id = sample_user_data['user_id'] + i
            user_repo.get_or_create(
                user_id=user_id,
                username=f'user_{i}',
            )
            if i == 0:
                user_repo.update_role(user_id, 1)  # نقش ادمین

        users = user_repo.get_users_by_role(1)
        assert len(users) >= 1

    # ============================================================
    # تست‌های نقش
    # ============================================================

    def test_update_role(self, user_repo, sample_user_data):
        """تست تغییر نقش کاربر"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        result = user_repo.update_role(
            user_id=sample_user_data['user_id'],
            role=1,
        )

        assert result is True

        user = user_repo.get_by_id(sample_user_data['user_id'])
        assert user['role'] == 1

    # ============================================================
    # تست‌های پیشنهادات نام کاربری
    # ============================================================

    def test_get_username_suggestions(self, user_repo, sample_user_data):
        """تست دریافت پیشنهادات نام کاربری"""
        user_repo.get_or_create(
            user_id=sample_user_data['user_id'],
            username=sample_user_data['username'],
        )

        suggestions = user_repo.get_username_suggestions('test', limit=5)
        assert len(suggestions) >= 1
        assert sample_user_data['username'] in suggestions

    def test_get_username_suggestions_not_found(self, user_repo):
        """تست دریافت پیشنهادات نام کاربری برای عبارت ناموجود"""
        suggestions = user_repo.get_username_suggestions('nonexistentxyz', limit=5)
        assert len(suggestions) == 0

    # ============================================================
    # تست‌های کاربران با فیلتر
    # ============================================================

    def test_get_users_with_filter(self, user_repo, sample_user_data):
        """تست دریافت کاربران با فیلتر"""
        # ایجاد کاربران
        for i in range(5):
            user_id = sample_user_data['user_id'] + i
            user_repo.get_or_create(
                user_id=user_id,
                username=f'user_{i}',
            )
            if i % 2 == 0:
                user_repo.block_user(user_id)

        # فیلتر کاربران مسدود شده
        users = user_repo.custom_query(
            "SELECT * FROM users WHERE is_blocked = 1 LIMIT 10"
        )
        assert len(users) >= 2

    def test_get_users_with_filter_count(self, user_repo, sample_user_data):
        """تست تعداد نتایج فیلتر کاربران"""
        # ایجاد کاربران
        for i in range(5):
            user_repo.get_or_create(
                user_id=sample_user_data['user_id'] + i,
                username=f'user_{i}',
            )

        count = user_repo.count()
        assert count >= 5