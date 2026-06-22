# tests/test_repositories/test_order_repository.py
# تست‌های واحد برای OrderRepository

import pytest
import json
from datetime import datetime, timedelta

from repositories.order_repository import OrderRepository


class TestOrderRepository:
    """تست‌های OrderRepository"""

    @pytest.fixture
    def order_repo(self, db_connection):
        """ایجاد OrderRepository با اتصال دیتابیس تست"""
        return OrderRepository(db_connection)

    @pytest.fixture
    def sample_order_data(self):
        """داده‌های نمونه سفارش"""
        return {
            'user_id': 123456789,
            'button_id': 1,
            'order_data': {
                'answers': {
                    'نام کامل': 'علی محمدی',
                    'شماره تماس': '09123456789',
                },
                'fullname': 'علی محمدی',
            },
            'payment_amount': 50000,
            'tracking_code': 'TRK-12345',
            'status': 'pending',
        }

    # ============================================================
    # تست‌های ایجاد سفارش
    # ============================================================

    def test_create_order_success(self, order_repo, sample_order_data):
        """تست ایجاد سفارش با موفقیت"""
        order_id = order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            tracking_code=sample_order_data['tracking_code'],
            status=sample_order_data['status'],
        )

        assert order_id is not None
        assert order_id > 0

        # دریافت سفارش ایجادشده
        order = order_repo.get_by_id(order_id)
        assert order is not None
        assert order['user_id'] == sample_order_data['user_id']
        assert order['button_id'] == sample_order_data['button_id']
        assert order['tracking_code'] == sample_order_data['tracking_code']
        assert order['status'] == sample_order_data['status']

    def test_create_order_without_tracking(self, order_repo, sample_order_data):
        """تست ایجاد سفارش بدون کد رهگیری"""
        order_id = order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            status='pending',
        )

        assert order_id is not None
        order = order_repo.get_by_id(order_id)
        assert order['tracking_code'] is None

    # ============================================================
    # تست‌های دریافت سفارش
    # ============================================================

    def test_get_by_id(self, order_repo, sample_order_data):
        """تست دریافت سفارش با شناسه"""
        order_id = order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        order = order_repo.get_by_id(order_id)
        assert order is not None
        assert order['id'] == order_id

    def test_get_by_id_not_found(self, order_repo):
        """تست دریافت سفارش ناموجود"""
        order = order_repo.get_by_id(99999)
        assert order is None

    def test_get_by_status(self, order_repo, sample_order_data):
        """تست دریافت سفارشات بر اساس وضعیت"""
        # ایجاد سفارش با وضعیت‌های مختلف
        statuses = ['pending', 'paid', 'completed']
        for status in statuses:
            order_repo.create(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'],
                status=status,
            )

        pending_orders = order_repo.get_by_status('pending')
        assert len(pending_orders) >= 1

        paid_orders = order_repo.get_by_status('paid')
        assert len(paid_orders) >= 1

    def test_get_by_user(self, order_repo, sample_order_data):
        """تست دریافت سفارشات یک کاربر"""
        # ایجاد چند سفارش برای یک کاربر
        for i in range(3):
            order_repo.create(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'] + i,
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'] + (i * 10000),
            )

        orders = order_repo.get_by_user(sample_order_data['user_id'])
        assert len(orders) == 3

        # بررسی مرتب‌سازی (جدیدترین اول)
        assert orders[0]['created_at'] >= orders[1]['created_at']

    def test_get_by_button(self, order_repo, sample_order_data):
        """تست دریافت سفارشات یک سرویس"""
        button_id = 5
        for i in range(3):
            order_repo.create(
                user_id=sample_order_data['user_id'] + i,
                button_id=button_id,
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'],
            )

        orders = order_repo.get_by_button(button_id)
        assert len(orders) == 3

    def test_get_by_tracking_code(self, order_repo, sample_order_data):
        """تست دریافت سفارش با کد رهگیری"""
        tracking = 'TRK-UNIQUE-123'
        order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            tracking_code=tracking,
        )

        order = order_repo.get_by_tracking_code(tracking)
        assert order is not None
        assert order['tracking_code'] == tracking

    def test_count_by_status(self, order_repo, sample_order_data):
        """تست شمارش سفارشات بر اساس وضعیت"""
        # ایجاد سفارش با وضعیت‌های مختلف
        statuses = ['pending', 'paid']
        for status in statuses:
            for _ in range(2):
                order_repo.create(
                    user_id=sample_order_data['user_id'],
                    button_id=sample_order_data['button_id'],
                    order_data=sample_order_data['order_data'],
                    payment_amount=sample_order_data['payment_amount'],
                    status=status,
                )

        pending_count = order_repo.count_by_status('pending')
        assert pending_count >= 2

        paid_count = order_repo.count_by_status('paid')
        assert paid_count >= 2

    def test_count_by_user(self, order_repo, sample_order_data):
        """تست شمارش سفارشات یک کاربر"""
        for i in range(5):
            order_repo.create(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'],
            )

        count = order_repo.count_by_user(sample_order_data['user_id'])
        assert count == 5

    # ============================================================
    # تست‌های به‌روزرسانی سفارش
    # ============================================================

    def test_update_status(self, order_repo, sample_order_data):
        """تست تغییر وضعیت سفارش"""
        order_id = order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            status='pending',
        )

        result = order_repo.update_status(
            order_id=order_id,
            new_status='paid',
            user_id=sample_order_data['user_id'],
            note='تست تغییر وضعیت',
        )

        assert result is True

        order = order_repo.get_by_id(order_id)
        assert order['status'] == 'paid'

        # بررسی تاریخچه وضعیت
        history = order_repo.get_status_history(order_id)
        assert len(history) >= 1
        assert history[-1]['from'] == 'pending'
        assert history[-1]['to'] == 'paid'

    def test_add_note(self, order_repo, sample_order_data):
        """تست افزودن یادداشت به سفارش"""
        order_id = order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        note = 'یادداشت تست'
        result = order_repo.add_note(
            order_id=order_id,
            note=note,
            user_id=sample_order_data['user_id'],
        )

        assert result is True

        order = order_repo.get_by_id(order_id)
        assert note in order['admin_note']

    def test_delete_order(self, order_repo, sample_order_data):
        """تست حذف سفارش"""
        order_id = order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        result = order_repo.delete(order_id)
        assert result is True

        order = order_repo.get_by_id(order_id)
        assert order is None

    # ============================================================
    # تست‌های جستجو
    # ============================================================

    def test_search_orders_by_keyword(self, order_repo, sample_order_data):
        """تست جستجوی سفارشات با کلمه کلیدی"""
        # ایجاد سفارش با کد رهگیری مشخص
        order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            tracking_code='SEARCH-12345',
        )

        results = order_repo.search('SEARCH')
        assert len(results) >= 1

    def test_search_orders_by_user_id(self, order_repo, sample_order_data):
        """تست جستجوی سفارشات با شناسه کاربر"""
        order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        results = order_repo.search(str(sample_order_data['user_id']))
        assert len(results) >= 1

    def test_search_advanced_with_filters(self, order_repo, sample_order_data):
        """تست جستجوی پیشرفته با فیلترها"""
        # ایجاد سفارشات با مشخصات مختلف
        for i in range(5):
            order_repo.create(
                user_id=sample_order_data['user_id'] + i,
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=10000 * (i + 1),
                status='paid' if i % 2 == 0 else 'pending',
            )

        filters = {
            'status': 'paid',
            'min_amount': 20000,
            'max_amount': 40000,
        }

        results = order_repo.search_advanced(filters)
        # حداقل یک سفارش باید با این فیلترها مطابقت داشته باشد
        assert len(results) >= 1

    def test_search_advanced_count(self, order_repo, sample_order_data):
        """تست تعداد نتایج جستجوی پیشرفته"""
        filters = {'status': 'pending'}
        count = order_repo.search_advanced_count(filters)
        assert isinstance(count, int)

    # ============================================================
    # تست‌های آمار و گزارشات
    # ============================================================

    def test_get_stats(self, order_repo, sample_order_data):
        """تست دریافت آمار سفارشات"""
        # ایجاد سفارشات با وضعیت‌های مختلف
        statuses = ['pending', 'paid', 'completed']
        for status in statuses:
            for _ in range(2):
                order_repo.create(
                    user_id=sample_order_data['user_id'],
                    button_id=sample_order_data['button_id'],
                    order_data=sample_order_data['order_data'],
                    payment_amount=50000,
                    status=status,
                )

        stats = order_repo.get_stats()
        assert stats['total'] >= 6
        assert stats['total_amount'] >= 300000
        assert 'statuses' in stats
        assert stats['statuses']['pending'] >= 2

    def test_get_revenue_by_period(self, order_repo, sample_order_data):
        """تست دریافت درآمد در بازه زمانی"""
        # ایجاد سفارشات با تاریخ‌های مختلف
        today = datetime.now().date()
        for i in range(3):
            order_repo.create(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=10000 * (i + 1),
                status='paid',
            )

        revenue = order_repo.get_revenue_by_period(days=30)
        assert len(revenue) >= 1

    def test_get_user_order_stats(self, order_repo, sample_order_data):
        """تست دریافت آمار سفارشات یک کاربر"""
        for i in range(3):
            order_repo.create(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=10000 * (i + 1),
                status='paid' if i % 2 == 0 else 'pending',
            )

        stats = order_repo.get_user_order_stats(sample_order_data['user_id'])
        assert stats['total_orders'] == 3
        assert stats['total_amount'] >= 60000
        assert 'statuses' in stats

    def test_get_orders_by_date_range(self, order_repo, sample_order_data):
        """تست دریافت سفارشات در بازه زمانی"""
        today = datetime.now().date()
        start_date = today.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')

        order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        orders = order_repo.get_orders_by_date_range(start_date, end_date)
        assert len(orders) >= 1

    def test_get_orders_with_files(self, order_repo, sample_order_data):
        """تست دریافت سفارشات دارای فایل"""
        # ایجاد سفارش با فایل
        order_data_with_file = sample_order_data['order_data'].copy()
        order_data_with_file['files'] = {
            'فایل': {'file_id': '123', 'type': 'document'}
        }

        order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=order_data_with_file,
            payment_amount=sample_order_data['payment_amount'],
        )

        orders = order_repo.get_orders_with_files(limit=10)
        assert len(orders) >= 1

    # ============================================================
    # تست‌های تاریخچه وضعیت
    # ============================================================

    def test_get_status_history(self, order_repo, sample_order_data):
        """تست دریافت تاریخچه تغییرات وضعیت"""
        order_id = order_repo.create(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            status='pending',
        )

        # تغییر وضعیت چند بار
        order_repo.update_status(order_id, 'paid', sample_order_data['user_id'])
        order_repo.update_status(order_id, 'completed', sample_order_data['user_id'])

        history = order_repo.get_status_history(order_id)
        assert len(history) >= 2
        assert history[0]['from'] == 'pending'
        assert history[0]['to'] == 'paid'
        assert history[1]['from'] == 'paid'
        assert history[1]['to'] == 'completed'