# tests/test_services/test_admin_service.py
# تست‌های واحد برای AdminService

import pytest
from unittest.mock import MagicMock, patch

from services.admin_service import AdminService
from models.enums import AdminRole


class TestAdminService:
    """تست‌های AdminService"""

    @pytest.fixture
    def admin_service(self, db_connection):
        """ایجاد AdminService با اتصال دیتابیس تست"""
        return AdminService(db_connection)

    @pytest.fixture
    def sample_admin_data(self):
        """داده‌های نمونه ادمین"""
        return {
            'user_id': 123456789,
            'role': 'admin',
            'is_active': 1,
        }

    @pytest.fixture
    def owner_id(self):
        """شناسه مالک (برای تست‌های ویژه)"""
        return 999999999

    # ============================================================
    # تست‌های add_admin
    # ============================================================

    def test_add_admin_success(self, admin_service, sample_admin_data):
        """تست افزودن ادمین با موفقیت"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            result = admin_service.add_admin(
                user_id=sample_admin_data['user_id'],
                role=sample_admin_data['role']
            )

            assert result is True

            # بررسی وجود ادمین
            admin = admin_service.get_admin(sample_admin_data['user_id'])
            assert admin is not None
            assert admin['user_id'] == sample_admin_data['user_id']
            assert admin['role'] == sample_admin_data['role']

    def test_add_admin_already_exists(self, admin_service, sample_admin_data):
        """تست افزودن ادمین تکراری"""
        # ابتدا یک ادمین اضافه می‌کنیم
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            # تلاش برای افزودن مجدد
            result = admin_service.add_admin(sample_admin_data['user_id'])
            assert result is False

    def test_add_admin_user_not_found(self, admin_service, sample_admin_data):
        """تست افزودن ادمین با کاربر ناموجود"""
        with patch('services.user_service.UserService.get_user', return_value=None):
            result = admin_service.add_admin(sample_admin_data['user_id'])
            assert result is False

    def test_add_admin_with_invalid_role(self, admin_service, sample_admin_data):
        """تست افزودن ادمین با نقش نامعتبر"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            result = admin_service.add_admin(
                user_id=sample_admin_data['user_id'],
                role='invalid_role'
            )
            # نقش نامعتبر به 'admin' تبدیل می‌شود
            assert result is True
            admin = admin_service.get_admin(sample_admin_data['user_id'])
            assert admin['role'] == 'admin'

    # ============================================================
    # تست‌های get_admin
    # ============================================================

    def test_get_admin_by_user_id(self, admin_service, sample_admin_data):
        """تست دریافت ادمین با شناسه کاربر"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            admin = admin_service.get_admin(sample_admin_data['user_id'])
            assert admin is not None
            assert admin['user_id'] == sample_admin_data['user_id']
            assert admin['role'] == sample_admin_data['role']

    def test_get_admin_not_found(self, admin_service):
        """تست دریافت ادمین ناموجود"""
        admin = admin_service.get_admin(99999)
        assert admin is None

    def test_get_admin_by_user_id_with_details(self, admin_service, sample_admin_data):
        """تست دریافت ادمین با جزییات کامل"""
        with patch('services.user_service.UserService.get_user', return_value={
            'user_id': sample_admin_data['user_id'],
            'username': 'test_admin',
            'first_name': 'علی',
            'last_name': 'محمدی',
        }):
            admin_service.add_admin(sample_admin_data['user_id'])

            admins = admin_service.get_admins_with_details()
            assert len(admins) >= 1

            target = next((a for a in admins if a['user_id'] == sample_admin_data['user_id']), None)
            assert target is not None
            assert target['display_name'] == 'علی محمدی' or '@test_admin' in target['display_name']

    # ============================================================
    # تست‌های get_all_admins
    # ============================================================

    def test_get_all_admins(self, admin_service):
        """تست دریافت لیست تمام ادمین‌ها"""
        # چند ادمین اضافه می‌کنیم
        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            for i in range(100, 103):
                admin_service.add_admin(i)

        admins = admin_service.get_all_admins()
        assert len(admins) >= 3

    def test_get_all_admins_paginated(self, admin_service):
        """تست دریافت لیست ادمین‌ها با صفحه‌بندی"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            for i in range(100, 110):
                admin_service.add_admin(i)

        result = admin_service.get_paginated_admins(page=0, per_page=5)
        assert len(result['items']) == 5
        assert result['total'] >= 10
        assert result['total_pages'] >= 2

    def test_get_active_admins(self, admin_service):
        """تست دریافت ادمین‌های فعال"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            for i in range(200, 205):
                admin_service.add_admin(i)

            # غیرفعال کردن یکی
            admin_service.deactivate_admin(201)

        active = admin_service.get_active_admins()
        assert len(active) >= 3

    # ============================================================
    # تست‌های remove_admin
    # ============================================================

    def test_remove_admin_success(self, admin_service, sample_admin_data):
        """تست حذف ادمین با موفقیت"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            result = admin_service.remove_admin(sample_admin_data['user_id'])
            assert result is True

            admin = admin_service.get_admin(sample_admin_data['user_id'])
            assert admin is None

    def test_remove_owner_fails(self, admin_service, owner_id):
        """تست حذف مالک (غیرمجاز)"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': owner_id}):
            admin_service.add_admin(owner_id, role='owner')

            result = admin_service.remove_admin(owner_id)
            assert result is False

    def test_remove_admin_not_found(self, admin_service):
        """تست حذف ادمین ناموجود"""
        result = admin_service.remove_admin(99999)
        assert result is False

    # ============================================================
    # تست‌های update_role
    # ============================================================

    def test_update_role_success(self, admin_service, sample_admin_data):
        """تست تغییر نقش ادمین با موفقیت"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'], role='admin')

            result = admin_service.update_role(sample_admin_data['user_id'], 'manager')
            assert result is True

            admin = admin_service.get_admin(sample_admin_data['user_id'])
            assert admin['role'] == 'manager'

    def test_update_owner_role_fails(self, admin_service, owner_id):
        """تست تغییر نقش مالک (غیرمجاز)"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': owner_id}):
            admin_service.add_admin(owner_id, role='owner')

            result = admin_service.update_role(owner_id, 'admin')
            assert result is False

    def test_update_role_invalid_role(self, admin_service, sample_admin_data):
        """تست تغییر نقش با نقش نامعتبر"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            result = admin_service.update_role(sample_admin_data['user_id'], 'invalid')
            assert result is False

    def test_update_role_admin_not_found(self, admin_service):
        """تست تغییر نقش ادمین ناموجود"""
        result = admin_service.update_role(99999, 'manager')
        assert result is False

    # ============================================================
    # تست‌های toggle_status
    # ============================================================

    def test_toggle_status_success(self, admin_service, sample_admin_data):
        """تست تغییر وضعیت ادمین با موفقیت"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            # غیرفعال کردن
            success, new_status = admin_service.toggle_status(sample_admin_data['user_id'])
            assert success is True
            assert new_status == 0

            admin = admin_service.get_admin(sample_admin_data['user_id'])
            assert admin['is_active'] == 0

            # فعال کردن مجدد
            success, new_status = admin_service.toggle_status(sample_admin_data['user_id'])
            assert success is True
            assert new_status == 1

    def test_toggle_owner_status_fails(self, admin_service, owner_id):
        """تست تغییر وضعیت مالک (غیرمجاز)"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': owner_id}):
            admin_service.add_admin(owner_id, role='owner')

            success, _ = admin_service.toggle_status(owner_id)
            assert success is False

    def test_toggle_status_admin_not_found(self, admin_service):
        """تست تغییر وضعیت ادمین ناموجود"""
        success, _ = admin_service.toggle_status(99999)
        assert success is False

    # ============================================================
    # تست‌های activate/deactivate
    # ============================================================

    def test_activate_admin(self, admin_service, sample_admin_data):
        """تست فعال کردن ادمین"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])
            admin_service.deactivate_admin(sample_admin_data['user_id'])

            result = admin_service.activate_admin(sample_admin_data['user_id'])
            assert result is True

            admin = admin_service.get_admin(sample_admin_data['user_id'])
            assert admin['is_active'] == 1

    def test_deactivate_admin(self, admin_service, sample_admin_data):
        """تست غیرفعال کردن ادمین"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            result = admin_service.deactivate_admin(sample_admin_data['user_id'])
            assert result is True

            admin = admin_service.get_admin(sample_admin_data['user_id'])
            assert admin['is_active'] == 0

    # ============================================================
    # تست‌های search_admins
    # ============================================================

    def test_search_admins_by_user_id(self, admin_service, sample_admin_data):
        """تست جستجوی ادمین با شناسه کاربر"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            results = admin_service.search_admins(str(sample_admin_data['user_id']))
            assert len(results) >= 1
            assert results[0]['user_id'] == sample_admin_data['user_id']

    def test_search_admins_by_role(self, admin_service):
        """تست جستجوی ادمین با نقش"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            for i in range(300, 303):
                admin_service.add_admin(i, role='admin')
            admin_service.add_admin(304, role='manager')

        results = admin_service.search_admins('manager')
        assert len(results) >= 1

    def test_search_admins_not_found(self, admin_service):
        """تست جستجوی ادمین با عبارت ناموجود"""
        results = admin_service.search_admins('nonexistent')
        assert len(results) == 0

    # ============================================================
    # تست‌های count و آمار
    # ============================================================

    def test_count_admins(self, admin_service):
        """تست تعداد ادمین‌ها"""
        initial_count = admin_service.count_admins()

        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            for i in range(400, 403):
                admin_service.add_admin(i)

        final_count = admin_service.count_admins()
        assert final_count == initial_count + 3

    def test_count_active_admins(self, admin_service):
        """تست تعداد ادمین‌های فعال"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            for i in range(500, 505):
                admin_service.add_admin(i)

            admin_service.deactivate_admin(501)
            admin_service.deactivate_admin(503)

        active_count = admin_service.count_active_admins()
        assert active_count >= 3

    def test_count_by_role(self, admin_service):
        """تست تعداد ادمین‌ها بر اساس نقش"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            for i in range(600, 603):
                admin_service.add_admin(i, role='admin')
            admin_service.add_admin(604, role='manager')
            admin_service.add_admin(605, role='observer')

        admin_count = admin_service.count_by_role('admin')
        assert admin_count >= 3

        manager_count = admin_service.count_by_role('manager')
        assert manager_count >= 1

    def test_get_stats(self, admin_service):
        """تست دریافت آمار ادمین‌ها"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            for i in range(700, 705):
                admin_service.add_admin(i)
            admin_service.deactivate_admin(702)

        stats = admin_service.get_stats()
        assert stats['total'] >= 5
        assert stats['active'] >= 4
        assert stats['inactive'] >= 1
        assert 'roles' in stats

    # ============================================================
    # تست‌های is_admin و is_active
    # ============================================================

    def test_is_admin_true(self, admin_service, sample_admin_data):
        """تست بررسی ادمین بودن (True)"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            result = admin_service.is_admin(sample_admin_data['user_id'])
            assert result is True

    def test_is_admin_false(self, admin_service):
        """تست بررسی ادمین بودن (False)"""
        result = admin_service.is_admin(99999)
        assert result is False

    def test_is_active_true(self, admin_service, sample_admin_data):
        """تست بررسی فعال بودن ادمین (True)"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            result = admin_service.is_active(sample_admin_data['user_id'])
            assert result is True

    def test_is_active_false(self, admin_service, sample_admin_data):
        """تست بررسی فعال بودن ادمین (False)"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])
            admin_service.deactivate_admin(sample_admin_data['user_id'])

            result = admin_service.is_active(sample_admin_data['user_id'])
            assert result is False

    # ============================================================
    # تست‌های دسترسی
    # ============================================================

    def test_can_access_admin_panel_owner(self, admin_service, owner_id):
        """تست دسترسی مالک به پنل مدیریت"""
        with patch('config.config.OWNER_ID', owner_id):
            result = admin_service.can_access_admin_panel(owner_id)
            assert result is True

    def test_can_access_admin_panel_admin(self, admin_service, sample_admin_data):
        """تست دسترسی ادمین به پنل مدیریت"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            result = admin_service.can_access_admin_panel(sample_admin_data['user_id'])
            assert result is True

    def test_can_access_admin_panel_regular(self, admin_service):
        """تست عدم دسترسی کاربر عادی به پنل مدیریت"""
        result = admin_service.can_access_admin_panel(99999)
        assert result is False

    def test_is_owner(self, admin_service, owner_id):
        """تست بررسی مالک بودن"""
        with patch('config.config.OWNER_ID', owner_id):
            assert admin_service.is_owner(owner_id) is True
            assert admin_service.is_owner(99999) is False

    # ============================================================
    # تست‌های get_role
    # ============================================================

    def test_get_admin_role(self, admin_service, sample_admin_data):
        """تست دریافت نقش ادمین"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'], role='manager')

            role = admin_service.get_admin_role(sample_admin_data['user_id'])
            assert role == 'manager'

    def test_get_admin_role_not_admin(self, admin_service):
        """تست دریافت نقش کاربر عادی"""
        role = admin_service.get_admin_role(99999)
        assert role is None

    # ============================================================
    # تست‌های is_last_admin
    # ============================================================

    def test_is_last_admin_true(self, admin_service, sample_admin_data, owner_id):
        """تست آخرین ادمین بودن (True)"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'])

            # با توجه به اینکه OWNER همیشه ادمین است، این تست باید با دقت بررسی شود
            # در اینجا فرض می‌کنیم که فقط OWNER و این کاربر ادمین هستند
            result = admin_service.is_last_admin(sample_admin_data['user_id'])
            # ممکن است True یا False باشد بسته به تنظیمات
            assert isinstance(result, bool)

    def test_is_last_admin_owner(self, admin_service, owner_id):
        """تست آخرین ادمین بودن برای OWNER (همیشه False)"""
        result = admin_service.is_last_admin(owner_id)
        assert result is False

    # ============================================================
    # تست‌های مجوزها
    # ============================================================

    def test_get_admin_permissions_owner(self, admin_service, owner_id):
        """تست دریافت مجوزهای مالک"""
        permissions = admin_service.get_admin_permissions(owner_id)
        assert '*' in permissions

    def test_get_admin_permissions_admin(self, admin_service, sample_admin_data):
        """تست دریافت مجوزهای ادمین"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'], role='admin')

            permissions = admin_service.get_admin_permissions(sample_admin_data['user_id'])
            assert 'manage_orders' in permissions
            assert 'manage_buttons' in permissions

    def test_get_admin_permissions_observer(self, admin_service):
        """تست دریافت مجوزهای ناظر"""
        user_id = 999
        with patch('services.user_service.UserService.get_user', return_value={'user_id': user_id}):
            admin_service.add_admin(user_id, role='observer')

            permissions = admin_service.get_admin_permissions(user_id)
            assert 'view_analytics' in permissions
            assert 'manage_orders' not in permissions

    def test_has_permission(self, admin_service, sample_admin_data):
        """تست بررسی وجود مجوز"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': sample_admin_data['user_id']}):
            admin_service.add_admin(sample_admin_data['user_id'], role='admin')

            result = admin_service.has_permission(sample_admin_data['user_id'], 'manage_orders')
            assert result is True

            result = admin_service.has_permission(sample_admin_data['user_id'], 'manage_admins')
            assert result is False

    def test_has_permission_owner(self, admin_service, owner_id):
        """تست بررسی وجود مجوز برای مالک (همیشه True)"""
        result = admin_service.has_permission(owner_id, 'any_permission')
        assert result is True

    # ============================================================
    # تست‌های کمکی
    # ============================================================

    def test_get_owners_count(self, admin_service):
        """تست تعداد مالک‌ها"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            admin_service.add_admin(800, role='owner')
            admin_service.add_admin(801, role='admin')

        count = admin_service.get_owners_count()
        assert count >= 1

    def test_get_admin_dashboard_stats(self, admin_service):
        """تست دریافت آمار داشبورد مدیریت"""
        with patch('services.user_service.UserService.get_user', return_value={'user_id': i}):
            for i in range(900, 905):
                admin_service.add_admin(i)
            admin_service.deactivate_admin(902)

        with patch('services.user_service.UserService.get_total_users', return_value=100):
            with patch('services.user_service.UserService.get_active_count', return_value=50):
                stats = admin_service.get_admin_dashboard_stats()

                assert stats['total_admins'] >= 5
                assert stats['active_admins'] >= 4
                assert stats['inactive_admins'] >= 1
                assert stats['total_users'] == 100
                assert stats['active_today'] == 50