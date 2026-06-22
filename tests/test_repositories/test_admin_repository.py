# tests/test_repositories/test_admin_repository.py
# تست‌های واحد برای AdminRepository

import pytest
from unittest.mock import MagicMock, patch

from repositories.admin_repository import AdminRepository


class TestAdminRepository:
    """تست‌های AdminRepository"""

    @pytest.fixture
    def admin_repo(self, db_connection):
        """ایجاد AdminRepository با اتصال دیتابیس تست"""
        return AdminRepository(db_connection)

    @pytest.fixture
    def sample_admin_data(self):
        """داده‌های نمونه ادمین"""
        return {
            'user_id': 123456789,
            'role': 'admin',
            'is_active': 1,
        }

    # ============================================================
    # تست‌های add_admin
    # ============================================================

    def test_add_admin_success(self, admin_repo, sample_admin_data):
        """تست افزودن ادمین با موفقیت"""
        result = admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role=sample_admin_data['role'],
        )

        assert result is True

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin is not None
        assert admin['user_id'] == sample_admin_data['user_id']
        assert admin['role'] == sample_admin_data['role']
        assert admin['is_active'] == 1

    def test_add_admin_duplicate(self, admin_repo, sample_admin_data):
        """تست افزودن ادمین تکراری"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role=sample_admin_data['role'],
        )

        result = admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='manager',
        )

        assert result is False

    def test_add_admin_default_role(self, admin_repo, sample_admin_data):
        """تست افزودن ادمین با نقش پیش‌فرض"""
        result = admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
        )

        assert result is True

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin['role'] == 'admin'

    def test_add_admin_invalid_role(self, admin_repo, sample_admin_data):
        """تست افزودن ادمین با نقش نامعتبر"""
        result = admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='invalid_role',
        )

        assert result is True

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        # نقش نامعتبر به 'admin' تبدیل می‌شود
        assert admin['role'] == 'admin'

    def test_add_admin_with_owner_role(self, admin_repo, sample_admin_data):
        """تست افزودن ادمین با نقش owner"""
        result = admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='owner',
        )

        assert result is True

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin['role'] == 'owner'

    # ============================================================
    # تست‌های get_by_id
    # ============================================================

    def test_get_admin_by_id_success(self, admin_repo, sample_admin_data):
        """تست دریافت ادمین با شناسه کاربر"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role=sample_admin_data['role'],
        )

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin is not None
        assert admin['user_id'] == sample_admin_data['user_id']
        assert admin['role'] == sample_admin_data['role']

    def test_get_admin_by_id_not_found(self, admin_repo):
        """تست دریافت ادمین ناموجود"""
        admin = admin_repo.get_by_id(99999)
        assert admin is None

    # ============================================================
    # تست‌های get_all
    # ============================================================

    def test_get_all_admins(self, admin_repo):
        """تست دریافت تمام ادمین‌ها"""
        for i in range(100, 103):
            admin_repo.add_admin(user_id=i, role='admin')

        admins = admin_repo.get_all()
        assert len(admins) >= 3

    def test_get_all_with_pagination(self, admin_repo):
        """تست دریافت تمام ادمین‌ها با صفحه‌بندی"""
        for i in range(100, 110):
            admin_repo.add_admin(user_id=i)

        page_1 = admin_repo.get_all(limit=3, offset=0)
        page_2 = admin_repo.get_all(limit=3, offset=3)

        assert len(page_1) == 3
        assert len(page_2) == 3
        assert page_1[0]['user_id'] != page_2[0]['user_id']

    # ============================================================
    # تست‌های get_active
    # ============================================================

    def test_get_active_admins(self, admin_repo):
        """تست دریافت ادمین‌های فعال"""
        admin_repo.add_admin(user_id=100, is_active=True)
        admin_repo.add_admin(user_id=101, is_active=True)
        admin_repo.add_admin(user_id=102, is_active=False)

        active = admin_repo.get_active()
        assert len(active) >= 2
        for admin in active:
            assert admin['is_active'] == 1

    # ============================================================
    # تست‌های get_by_role
    # ============================================================

    def test_get_by_role(self, admin_repo):
        """تست دریافت ادمین‌ها بر اساس نقش"""
        admin_repo.add_admin(user_id=100, role='admin')
        admin_repo.add_admin(user_id=101, role='admin')
        admin_repo.add_admin(user_id=102, role='manager')
        admin_repo.add_admin(user_id=103, role='observer')

        admins = admin_repo.get_by_role('admin')
        assert len(admins) >= 2

        managers = admin_repo.get_by_role('manager')
        assert len(managers) >= 1

        observers = admin_repo.get_by_role('observer')
        assert len(observers) >= 1

    # ============================================================
    # تست‌های is_admin
    # ============================================================

    def test_is_admin_true(self, admin_repo, sample_admin_data):
        """تست بررسی ادمین بودن (True)"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role=sample_admin_data['role'],
            is_active=1,
        )

        result = admin_repo.is_admin(sample_admin_data['user_id'])
        assert result is True

    def test_is_admin_false_inactive(self, admin_repo, sample_admin_data):
        """تست بررسی ادمین بودن با کاربر غیرفعال"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role=sample_admin_data['role'],
            is_active=0,
        )

        result = admin_repo.is_admin(sample_admin_data['user_id'])
        assert result is False

    def test_is_admin_false_not_found(self, admin_repo):
        """تست بررسی ادمین بودن کاربر ناموجود"""
        result = admin_repo.is_admin(99999)
        assert result is False

    # ============================================================
    # تست‌های exists
    # ============================================================

    def test_exists_true(self, admin_repo, sample_admin_data):
        """تست بررسی وجود ادمین (True)"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role=sample_admin_data['role'],
            is_active=0,
        )

        result = admin_repo.exists(sample_admin_data['user_id'])
        assert result is True

    def test_exists_false(self, admin_repo):
        """تست بررسی وجود ادمین (False)"""
        result = admin_repo.exists(99999)
        assert result is False

    # ============================================================
    # تست‌های remove_admin
    # ============================================================

    def test_remove_admin_success(self, admin_repo, sample_admin_data):
        """تست حذف ادمین با موفقیت"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role=sample_admin_data['role'],
        )

        result = admin_repo.remove_admin(sample_admin_data['user_id'])
        assert result is True

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin is None

    def test_remove_admin_not_found(self, admin_repo):
        """تست حذف ادمین ناموجود"""
        result = admin_repo.remove_admin(99999)
        assert result is False

    # ============================================================
    # تست‌های update_role
    # ============================================================

    def test_update_role_success(self, admin_repo, sample_admin_data):
        """تست تغییر نقش ادمین با موفقیت"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
        )

        result = admin_repo.update_role(
            user_id=sample_admin_data['user_id'],
            role='manager',
        )
        assert result is True

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin['role'] == 'manager'

    def test_update_role_invalid(self, admin_repo, sample_admin_data):
        """تست تغییر نقش با مقدار نامعتبر"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
        )

        result = admin_repo.update_role(
            user_id=sample_admin_data['user_id'],
            role='invalid',
        )
        assert result is False

    def test_update_role_not_found(self, admin_repo):
        """تست تغییر نقش ادمین ناموجود"""
        result = admin_repo.update_role(99999, 'admin')
        assert result is False

    # ============================================================
    # تست‌های toggle_status
    # ============================================================

    def test_toggle_status_success(self, admin_repo, sample_admin_data):
        """تست تغییر وضعیت ادمین با موفقیت"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
            is_active=1,
        )

        success, new_status = admin_repo.toggle_status(sample_admin_data['user_id'])
        assert success is True
        assert new_status == 0

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin['is_active'] == 0

        # تغییر مجدد
        success, new_status = admin_repo.toggle_status(sample_admin_data['user_id'])
        assert success is True
        assert new_status == 1

    def test_toggle_status_not_found(self, admin_repo):
        """تست تغییر وضعیت ادمین ناموجود"""
        success, new_status = admin_repo.toggle_status(99999)
        assert success is False
        assert new_status is None

    # ============================================================
    # تست‌های activate و deactivate
    # ============================================================

    def test_activate_admin(self, admin_repo, sample_admin_data):
        """تست فعال کردن ادمین"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
            is_active=0,
        )

        result = admin_repo.activate(sample_admin_data['user_id'])
        assert result is True

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin['is_active'] == 1

    def test_deactivate_admin(self, admin_repo, sample_admin_data):
        """تست غیرفعال کردن ادمین"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
            is_active=1,
        )

        result = admin_repo.deactivate(sample_admin_data['user_id'])
        assert result is True

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin['is_active'] == 0

    def test_activate_not_found(self, admin_repo):
        """تست فعال کردن ادمین ناموجود"""
        result = admin_repo.activate(99999)
        assert result is False

    def test_deactivate_not_found(self, admin_repo):
        """تست غیرفعال کردن ادمین ناموجود"""
        result = admin_repo.deactivate(99999)
        assert result is False

    # ============================================================
    # تست‌های search
    # ============================================================

    def test_search_by_user_id(self, admin_repo, sample_admin_data):
        """تست جستجوی ادمین با شناسه کاربر"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
        )

        results = admin_repo.search(str(sample_admin_data['user_id']))
        assert len(results) >= 1
        assert results[0]['user_id'] == sample_admin_data['user_id']

    def test_search_by_role(self, admin_repo):
        """تست جستجوی ادمین با نقش"""
        admin_repo.add_admin(user_id=100, role='admin')
        admin_repo.add_admin(user_id=101, role='manager')
        admin_repo.add_admin(user_id=102, role='observer')

        results = admin_repo.search('manager')
        assert len(results) >= 1

        results = admin_repo.search('admin')
        assert len(results) >= 1

    def test_search_not_found(self, admin_repo):
        """تست جستجوی ادمین با عبارت ناموجود"""
        results = admin_repo.search('nonexistent')
        assert len(results) == 0

    # ============================================================
    # تست‌های get_stats
    # ============================================================

    def test_get_stats(self, admin_repo):
        """تست دریافت آمار ادمین‌ها"""
        admin_repo.add_admin(user_id=100, role='admin', is_active=1)
        admin_repo.add_admin(user_id=101, role='admin', is_active=1)
        admin_repo.add_admin(user_id=102, role='manager', is_active=1)
        admin_repo.add_admin(user_id=103, role='observer', is_active=0)

        stats = admin_repo.get_stats()
        assert stats['total'] >= 4
        assert stats['active'] >= 3
        assert stats['inactive'] >= 1
        assert 'admin' in stats['roles']
        assert 'manager' in stats['roles']
        assert 'observer' in stats['roles']

    # ============================================================
    # تست‌های count
    # ============================================================

    def test_count_admins(self, admin_repo):
        """تست تعداد ادمین‌ها"""
        initial_count = admin_repo.count()

        for i in range(100, 103):
            admin_repo.add_admin(user_id=i)

        final_count = admin_repo.count()
        assert final_count == initial_count + 3

    def test_count_active(self, admin_repo):
        """تست تعداد ادمین‌های فعال"""
        admin_repo.add_admin(user_id=100, is_active=1)
        admin_repo.add_admin(user_id=101, is_active=1)
        admin_repo.add_admin(user_id=102, is_active=0)

        count = admin_repo.count_active()
        assert count >= 2

    def test_count_by_role(self, admin_repo):
        """تست تعداد ادمین‌ها بر اساس نقش"""
        admin_repo.add_admin(user_id=100, role='admin')
        admin_repo.add_admin(user_id=101, role='admin')
        admin_repo.add_admin(user_id=102, role='manager')

        count = admin_repo.count_by_role('admin')
        assert count >= 2

        count = admin_repo.count_by_role('manager')
        assert count >= 1

    # ============================================================
    # تست‌های get_owners, get_admins, get_managers, get_observers
    # ============================================================

    def test_get_owners(self, admin_repo):
        """تست دریافت ادمین‌های با نقش owner"""
        admin_repo.add_admin(user_id=100, role='owner')
        admin_repo.add_admin(user_id=101, role='admin')

        owners = admin_repo.get_owners()
        assert len(owners) >= 1
        for admin in owners:
            assert admin['role'] == 'owner'

    def test_get_admins(self, admin_repo):
        """تست دریافت ادمین‌های با نقش admin"""
        admin_repo.add_admin(user_id=100, role='admin')
        admin_repo.add_admin(user_id=101, role='admin')
        admin_repo.add_admin(user_id=102, role='manager')

        admins = admin_repo.get_admins()
        assert len(admins) >= 2
        for admin in admins:
            assert admin['role'] == 'admin'

    def test_get_managers(self, admin_repo):
        """تست دریافت ادمین‌های با نقش manager"""
        admin_repo.add_admin(user_id=100, role='manager')
        admin_repo.add_admin(user_id=101, role='admin')

        managers = admin_repo.get_managers()
        assert len(managers) >= 1
        for admin in managers:
            assert admin['role'] == 'manager'

    def test_get_observers(self, admin_repo):
        """تست دریافت ادمین‌های با نقش observer"""
        admin_repo.add_admin(user_id=100, role='observer')
        admin_repo.add_admin(user_id=101, role='admin')

        observers = admin_repo.get_observers()
        assert len(observers) >= 1
        for admin in observers:
            assert admin['role'] == 'observer'

    # ============================================================
    # تست‌های get_role
    # ============================================================

    def test_get_role(self, admin_repo, sample_admin_data):
        """تست دریافت نقش ادمین"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='manager',
        )

        role = admin_repo.get_role(sample_admin_data['user_id'])
        assert role == 'manager'

    def test_get_role_not_found(self, admin_repo):
        """تست دریافت نقش کاربر ناموجود"""
        role = admin_repo.get_role(99999)
        assert role is None

    # ============================================================
    # تست‌های is_active
    # ============================================================

    def test_is_active_true(self, admin_repo, sample_admin_data):
        """تست بررسی فعال بودن ادمین (True)"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
            is_active=1,
        )

        result = admin_repo.is_active(sample_admin_data['user_id'])
        assert result is True

    def test_is_active_false(self, admin_repo, sample_admin_data):
        """تست بررسی فعال بودن ادمین (False)"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
            is_active=0,
        )

        result = admin_repo.is_active(sample_admin_data['user_id'])
        assert result is False

    def test_is_active_not_found(self, admin_repo):
        """تست بررسی فعال بودن ادمین ناموجود"""
        result = admin_repo.is_active(99999)
        assert result is False

    # ============================================================
    # تست‌های get_all_with_details
    # ============================================================

    def test_get_all_with_details(self, admin_repo):
        """تست دریافت لیست تمام ادمین‌ها با جزئیات کامل"""
        admin_repo.add_admin(user_id=100, role='admin', is_active=1)
        admin_repo.add_admin(user_id=101, role='manager', is_active=0)

        admins = admin_repo.get_all_with_details()
        assert len(admins) >= 2

        admin_100 = next((a for a in admins if a['user_id'] == 100), None)
        assert admin_100 is not None
        assert admin_100['role'] == 'admin'
        assert admin_100['is_active'] == 1

    # ============================================================
    # تست‌های get_paginated
    # ============================================================

    def test_get_paginated(self, admin_repo):
        """تست دریافت لیست ادمین‌ها با صفحه‌بندی"""
        for i in range(100, 110):
            admin_repo.add_admin(user_id=i)

        result = admin_repo.get_paginated(page=1, per_page=3)
        assert len(result['items']) == 3
        assert result['total'] >= 10
        assert result['page'] == 1
        assert result['per_page'] == 3
        assert result['total_pages'] >= 4

    def test_get_paginated_last_page(self, admin_repo):
        """تست دریافت آخرین صفحه از لیست ادمین‌ها"""
        for i in range(100, 105):
            admin_repo.add_admin(user_id=i)

        result = admin_repo.get_paginated(page=2, per_page=2)
        assert len(result['items']) == 1
        assert result['total'] == 5
        assert result['total_pages'] == 3

    def test_get_paginated_empty(self, admin_repo):
        """تست دریافت لیست خالی با صفحه‌بندی"""
        result = admin_repo.get_paginated(page=0, per_page=10)
        assert len(result['items']) == 0
        assert result['total'] == 0
        assert result['total_pages'] == 0

    # ============================================================
    # تست‌های update_added_at
    # ============================================================

    def test_update_added_at(self, admin_repo, sample_admin_data):
        """تست به‌روزرسانی زمان افزودن ادمین"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
        )

        old_added_at = admin_repo.get_by_id(sample_admin_data['user_id'])['added_at']

        result = admin_repo.update_added_at(sample_admin_data['user_id'])
        assert result is True

        new_added_at = admin_repo.get_by_id(sample_admin_data['user_id'])['added_at']
        assert new_added_at != old_added_at

    def test_update_added_at_not_found(self, admin_repo):
        """تست به‌روزرسانی زمان افزودن ادمین ناموجود"""
        result = admin_repo.update_added_at(99999)
        assert result is False

    # ============================================================
    # تست‌های custom_query
    # ============================================================

    def test_custom_query(self, admin_repo):
        """تست اجرای کوئری سفارشی"""
        admin_repo.add_admin(user_id=100, role='admin')
        admin_repo.add_admin(user_id=101, role='admin')

        results = admin_repo.custom_query(
            "SELECT * FROM admins WHERE role = ?",
            ['admin']
        )
        assert len(results) >= 2

    def test_custom_query_one(self, admin_repo, sample_admin_data):
        """تست اجرای کوئری سفارشی و دریافت یک نتیجه"""
        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
        )

        result = admin_repo.custom_query_one(
            "SELECT * FROM admins WHERE user_id = ?",
            [sample_admin_data['user_id']]
        )
        assert result is not None
        assert result['user_id'] == sample_admin_data['user_id']

    # ============================================================
    # تست‌های transaction
    # ============================================================

    def test_transaction_commit(self, admin_repo, sample_admin_data):
        """تست تراکنش با commit"""
        admin_repo.begin_transaction()

        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
        )

        admin_repo.commit_transaction()

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin is not None

    def test_transaction_rollback(self, admin_repo, sample_admin_data):
        """تست تراکنش با rollback"""
        admin_repo.begin_transaction()

        admin_repo.add_admin(
            user_id=sample_admin_data['user_id'],
            role='admin',
        )

        admin_repo.rollback_transaction()

        admin = admin_repo.get_by_id(sample_admin_data['user_id'])
        assert admin is None

    # ============================================================
    # تست‌های error handling
    # ============================================================

    def test_update_role_not_found_in_update(self, admin_repo):
        """تست به‌روزرسانی نقش با استفاده از update عمومی"""
        result = admin_repo.update(99999, {'role': 'admin'})
        assert result is False

    def test_remove_admin_not_found_in_delete(self, admin_repo):
        """تست حذف ادمین با استفاده از delete عمومی"""
        result = admin_repo.delete(99999)
        assert result is False

    def test_get_by_id_with_invalid_type(self, admin_repo):
        """تست دریافت ادمین با شناسه از نوع نامعتبر"""
        # با شناسه رشته‌ای که عدد نیست
        with pytest.raises(Exception):
            admin_repo.get_by_id('invalid')

    def test_add_admin_with_empty_user_id(self, admin_repo):
        """تست افزودن ادمین با شناسه خالی"""
        with pytest.raises(Exception):
            admin_repo.add_admin(user_id=None)

    # ============================================================
    # تست‌های get_admins_with_details بعد از تغییرات
    # ============================================================

    def test_get_all_with_details_after_updates(self, admin_repo):
        """تست دریافت لیست ادمین‌ها با جزئیات بعد از به‌روزرسانی"""
        admin_repo.add_admin(user_id=100, role='admin', is_active=1)
        admin_repo.update_role(100, 'manager')
        admin_repo.deactivate(100)

        admins = admin_repo.get_all_with_details()
        admin_100 = next((a for a in admins if a['user_id'] == 100), None)
        assert admin_100 is not None
        assert admin_100['role'] == 'manager'
        assert admin_100['is_active'] == 0

    # ============================================================
    # تست‌های get_paginated با صفحه‌بندی دقیق
    # ============================================================

    def test_get_paginated_page_boundaries(self, admin_repo):
        """تست دریافت صفحه‌های مختلف با مرزهای دقیق"""
        for i in range(100, 112):
            admin_repo.add_admin(user_id=i)

        # صفحه ۰: ۱۰ آیتم اول
        result_0 = admin_repo.get_paginated(page=0, per_page=5)
        assert len(result_0['items']) == 5
        assert result_0['page'] == 0
        assert result_0['total_pages'] == 3  # 12/5 = 3 صفحه

        # صفحه ۱: ۵ آیتم بعدی
        result_1 = admin_repo.get_paginated(page=1, per_page=5)
        assert len(result_1['items']) == 5

        # صفحه ۲: ۲ آیتم باقی‌مانده
        result_2 = admin_repo.get_paginated(page=2, per_page=5)
        assert len(result_2['items']) == 2

        # صفحه ۳: خارج از محدوده
        result_3 = admin_repo.get_paginated(page=3, per_page=5)
        assert len(result_3['items']) == 0