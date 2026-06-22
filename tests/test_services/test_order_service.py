# tests/test_services/test_order_service.py
# تست‌های واحد برای OrderService

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from services.order_service import OrderService
from models.order import Order, OrderStatus


class TestOrderService:
    """تست‌های OrderService"""

    @pytest.fixture
    def order_service(self, db_connection):
        """ایجاد OrderService با اتصال دیتابیس تست"""
        return OrderService(db_connection)

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
        }

    # ============================================================
    # تست‌های ایجاد سفارش
    # ============================================================

    def test_create_order_success(self, order_service, sample_order_data):
        """تست ایجاد سفارش با موفقیت"""
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        assert order_id is not None
        assert 'id' in order_id

        # دریافت سفارش ایجادشده
        order = order_service.get_order(order_id['id'])
        assert order is not None
        assert order['user_id'] == sample_order_data['user_id']
        assert order['button_id'] == sample_order_data['button_id']
        assert order['status'] == 'pending'

    def test_create_order_with_tracking_code(self, order_service, sample_order_data):
        """تست ایجاد سفارش با کد رهگیری"""
        tracking_code = 'TRK-12345'
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            tracking_code=tracking_code,
        )

        assert order_id is not None
        order = order_service.get_order(order_id['id'])
        assert order['tracking_code'] == tracking_code

    def test_create_order_with_custom_status(self, order_service, sample_order_data):
        """تست ایجاد سفارش با وضعیت سفارشی"""
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            status='paid',
        )

        assert order_id is not None
        order = order_service.get_order(order_id['id'])
        assert order['status'] == 'paid'

    # ============================================================
    # تست‌های دریافت سفارش
    # ============================================================

    def test_get_order_by_id(self, order_service, sample_order_data):
        """تست دریافت سفارش با شناسه"""
        # ایجاد سفارش
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        order = order_service.get_order(order_id['id'])
        assert order is not None
        assert order['id'] == order_id['id']

    def test_get_order_not_found(self, order_service):
        """تست دریافت سفارش ناموجود"""
        order = order_service.get_order(99999)
        assert order is None

    def test_get_orders_by_user(self, order_service, sample_order_data):
        """تست دریافت سفارشات یک کاربر"""
        # ایجاد چند سفارش
        for i in range(3):
            order_service.create_order(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'] + (i * 10000),
            )

        orders = order_service.get_orders_by_user(sample_order_data['user_id'])
        assert len(orders) == 3

    def test_get_orders_by_status(self, order_service, sample_order_data):
        """تست دریافت سفارشات بر اساس وضعیت"""
        # ایجاد سفارش با وضعیت‌های مختلف
        statuses = ['pending', 'paid', 'completed']
        for status in statuses:
            order_service.create_order(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'],
                status=status,
            )

        pending_orders = order_service.get_orders_by_status('pending')
        assert len(pending_orders) >= 1

    def test_count_orders(self, order_service, sample_order_data):
        """تست شمارش سفارشات"""
        initial_count = order_service.count_orders()
        
        # ایجاد چند سفارش
        for i in range(5):
            order_service.create_order(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'],
            )

        final_count = order_service.count_orders()
        assert final_count == initial_count + 5

    # ============================================================
    # تست‌های به‌روزرسانی سفارش
    # ============================================================

    def test_update_status_success(self, order_service, sample_order_data):
        """تست تغییر وضعیت سفارش با موفقیت"""
        # ایجاد سفارش
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            status='pending',
        )

        # تغییر وضعیت
        result = order_service.update_status(
            order_id=order_id['id'],
            new_status='paid',
            user_id=sample_order_data['user_id'],
            note='تست تغییر وضعیت',
        )

        assert result is True

        # بررسی تغییر
        order = order_service.get_order(order_id['id'])
        assert order['status'] == 'paid'

    def test_update_status_invalid_status(self, order_service, sample_order_data):
        """تست تغییر وضعیت با وضعیت نامعتبر"""
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        result = order_service.update_status(
            order_id=order_id['id'],
            new_status='invalid_status',
            user_id=sample_order_data['user_id'],
        )

        assert result is False

    def test_update_status_completed_order(self, order_service, sample_order_data):
        """تست تغییر وضعیت سفارش تکمیل‌شده (غیرقابل تغییر)"""
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            status='completed',
        )

        result = order_service.update_status(
            order_id=order_id['id'],
            new_status='paid',
            user_id=sample_order_data['user_id'],
        )

        assert result is False

    def test_add_note_to_order(self, order_service, sample_order_data):
        """تست افزودن یادداشت به سفارش"""
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        note = 'این یک یادداشت تست است'
        result = order_service.add_note(
            order_id=order_id['id'],
            note=note,
            user_id=sample_order_data['user_id'],
        )

        assert result is True

        order = order_service.get_order(order_id['id'])
        assert note in order['admin_note']

    # ============================================================
    # تست‌های حذف سفارش
    # ============================================================

    def test_delete_order_success(self, order_service, sample_order_data):
        """تست حذف سفارش با موفقیت"""
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            status='pending',
        )

        result = order_service.delete_order(order_id['id'])
        assert result is True

        order = order_service.get_order(order_id['id'])
        assert order is None

    def test_delete_paid_order_fails(self, order_service, sample_order_data):
        """تست حذف سفارش پرداخت‌شده (غیرمجاز)"""
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            status='paid',
        )

        result = order_service.delete_order(order_id['id'])
        assert result is False

    # ============================================================
    # تست‌های جستجو
    # ============================================================

    def test_search_orders(self, order_service, sample_order_data):
        """تست جستجوی سفارشات"""
        # ایجاد سفارش با داده‌های مشخص
        order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            tracking_code='SEARCH-12345',
        )

        results = order_service.search_orders('SEARCH')
        assert len(results) >= 1

    def test_search_orders_by_user_id(self, order_service, sample_order_data):
        """تست جستجوی سفارشات بر اساس شناسه کاربر"""
        order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        results = order_service.search_orders(str(sample_order_data['user_id']))
        assert len(results) >= 1

    # ============================================================
    # تست‌های آمار
    # ============================================================

    def test_get_stats(self, order_service, sample_order_data):
        """تست دریافت آمار سفارشات"""
        # ایجاد چند سفارش با وضعیت‌های مختلف
        statuses = ['pending', 'paid', 'completed']
        for status in statuses:
            order_service.create_order(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'],
                status=status,
            )

        stats = order_service.get_stats()
        assert 'total' in stats
        assert 'total_amount' in stats
        assert 'statuses' in stats
        assert stats['total'] >= 3

    def test_get_user_stats(self, order_service, sample_order_data):
        """تست دریافت آمار سفارشات یک کاربر"""
        # ایجاد چند سفارش
        for i in range(3):
            order_service.create_order(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'] + (i * 10000),
            )

        stats = order_service.get_user_stats(sample_order_data['user_id'])
        assert stats['total_orders'] >= 3
        assert stats['total_amount'] >= 150000

    def test_calculate_total_amount(self, order_service, sample_order_data):
        """تست محاسبه مجموع مبلغ پرداختی کاربر"""
        # ایجاد چند سفارش پرداخت‌شده
        for i in range(3):
            order_service.create_order(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'] + (i * 10000),
                status='paid',
            )

        total = order_service.calculate_total_amount(sample_order_data['user_id'])
        assert total > 0

    # ============================================================
    # تست‌های عملیات خاص
    # ============================================================

    def test_get_pending_orders(self, order_service, sample_order_data):
        """تست دریافت سفارشات در انتظار"""
        # ایجاد سفارش در انتظار
        order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
            status='pending',
        )

        pending_orders = order_service.get_pending_orders()
        assert len(pending_orders) >= 1

    def test_get_pending_orders_with_hours(self, order_service, sample_order_data):
        """تست دریافت سفارشات در انتظار با فیلتر ساعت"""
        # این تست نیاز به تنظیم created_at دارد
        # برای سادگی، فقط بررسی می‌کنیم که تابع بدون خطا اجرا شود
        pending_orders = order_service.get_pending_orders(hours=24)
        assert isinstance(pending_orders, list)

    def test_get_last_order(self, order_service, sample_order_data):
        """تست دریافت آخرین سفارش کاربر"""
        # ایجاد چند سفارش
        for i in range(3):
            order_service.create_order(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'] + (i * 10000),
            )

        last_order = order_service.get_last_order(sample_order_data['user_id'])
        assert last_order is not None
        assert last_order['user_id'] == sample_order_data['user_id']

    def test_update_tracking_code(self, order_service, sample_order_data):
        """تست به‌روزرسانی کد رهگیری"""
        order_id = order_service.create_order(
            user_id=sample_order_data['user_id'],
            button_id=sample_order_data['button_id'],
            order_data=sample_order_data['order_data'],
            payment_amount=sample_order_data['payment_amount'],
        )

        new_tracking = 'TRK-NEW-12345'
        result = order_service.update_tracking_code(order_id['id'], new_tracking)
        assert result is True

        order = order_service.get_order(order_id['id'])
        assert order['tracking_code'] == new_tracking

    # ============================================================
    # تست‌های انتزاعی (Abstract)
    # ============================================================

    def test_get_orders_summary(self, order_service, sample_order_data):
        """تست دریافت خلاصه سفارشات"""
        # ایجاد چند سفارش
        for i in range(5):
            order_service.create_order(
                user_id=sample_order_data['user_id'] + i,
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'] + (i * 10000),
                status='paid' if i % 2 == 0 else 'pending',
            )

        summary = order_service.get_orders_summary()
        assert summary['total_orders'] >= 5
        assert 'total_amount' in summary
        assert 'statuses' in summary

    def test_get_recent_orders_with_details(self, order_service, sample_order_data):
        """تست دریافت سفارشات اخیر با جزئیات کامل"""
        # ایجاد چند سفارش
        for i in range(3):
            order_service.create_order(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'] + (i * 10000),
            )

        recent_orders = order_service.get_recent_orders_with_details(limit=5)
        assert len(recent_orders) >= 3
        
        # بررسی وجود نام کاربر و سرویس
        for order in recent_orders:
            assert 'fullname' in order
            assert 'service_name' in order

    def test_get_order_status_distribution(self, order_service, sample_order_data):
        """تست دریافت توزیع وضعیت سفارشات"""
        statuses = ['pending', 'paid', 'completed', 'cancelled']
        for status in statuses:
            order_service.create_order(
                user_id=sample_order_data['user_id'],
                button_id=sample_order_data['button_id'],
                order_data=sample_order_data['order_data'],
                payment_amount=sample_order_data['payment_amount'],
                status=status,
            )

        distribution = order_service.get_order_status_distribution()
        assert isinstance(distribution, dict)
        # حداقل یکی از وضعیت‌ها باید وجود داشته باشد
        assert sum(distribution.values()) >= len(statuses)