# tests/test_services/test_payment_service.py
# تست‌های واحد برای PaymentService

import pytest
import json
from unittest.mock import MagicMock, patch

from services.payment_service import PaymentService


class TestPaymentService:
    """تست‌های PaymentService"""

    @pytest.fixture
    def payment_service(self, db_connection):
        """ایجاد PaymentService با اتصال دیتابیس تست"""
        return PaymentService(db_connection)

    @pytest.fixture
    def sample_payment_data(self):
        """داده‌های نمونه پرداخت موفق از بله"""
        return {
            'successful_payment': {
                'provider_payment_charge_id': 'TRK-123456789',
                'total_amount': 50000,
                'payload': 'dyn_1_123456789_1234567890',
                'payment_id': 'pay_12345',
            }
        }

    @pytest.fixture
    def sample_invoice_data(self):
        """داده‌های نمونه فاکتور"""
        return {
            'title': 'پرداخت هزینه سرویس تست',
            'description': 'پرداخت برای سرویس تست',
            'price_amount': 50000,
            'price_label': 'هزینه خدمات',
            'currency': 'IRT',
        }

    # ============================================================
    # تست‌های create_invoice_data
    # ============================================================

    def test_create_invoice_data_success(self, payment_service, sample_invoice_data):
        """تست ایجاد داده‌های فاکتور با موفقیت"""
        invoice = payment_service.create_invoice_data(
            title=sample_invoice_data['title'],
            description=sample_invoice_data['description'],
            price_amount=sample_invoice_data['price_amount'],
            price_label=sample_invoice_data['price_label'],
        )

        assert invoice is not None
        assert invoice['title'] == sample_invoice_data['title']
        assert invoice['description'] == sample_invoice_data['description']
        assert invoice['currency'] == sample_invoice_data['currency']
        assert len(invoice['prices']) == 1
        assert invoice['prices'][0]['label'] == sample_invoice_data['price_label']
        assert invoice['prices'][0]['amount'] == sample_invoice_data['price_amount']
        assert 'payload' in invoice
        assert invoice['start_parameter'] == 'pay'

    def test_create_invoice_data_with_custom_payload(self, payment_service, sample_invoice_data):
        """تست ایجاد فاکتور با payload سفارشی"""
        custom_payload = 'custom_payload_123'
        invoice = payment_service.create_invoice_data(
            title=sample_invoice_data['title'],
            description=sample_invoice_data['description'],
            price_amount=sample_invoice_data['price_amount'],
            price_label=sample_invoice_data['price_label'],
            payload=custom_payload,
        )

        assert invoice['payload'] == custom_payload

    def test_create_invoice_data_with_min_amount(self, payment_service, sample_invoice_data):
        """تست ایجاد فاکتور با مبلغ کمتر از حداقل (۱۰,۰۰۰ ریال)"""
        invoice = payment_service.create_invoice_data(
            title=sample_invoice_data['title'],
            description=sample_invoice_data['description'],
            price_amount=5000,  # کمتر از ۱۰,۰۰۰
            price_label=sample_invoice_data['price_label'],
        )

        # باید به ۱۰,۰۰۰ افزایش یابد
        assert invoice['prices'][0]['amount'] >= 10000

    def test_create_invoice_data_with_different_currency(self, payment_service, sample_invoice_data):
        """تست ایجاد فاکتور با ارز متفاوت"""
        invoice = payment_service.create_invoice_data(
            title=sample_invoice_data['title'],
            description=sample_invoice_data['description'],
            price_amount=sample_invoice_data['price_amount'],
            price_label=sample_invoice_data['price_label'],
            currency='USD',
        )

        assert invoice['currency'] == 'USD'

    # ============================================================
    # تست‌های create_service_invoice
    # ============================================================

    def test_create_service_invoice(self, payment_service):
        """تست ایجاد فاکتور برای یک سرویس"""
        button_id = 1
        button_name = 'سرویس تست'
        price_amount = 100000
        user_id = 123456789

        invoice = payment_service.create_service_invoice(
            button_name=button_name,
            button_id=button_id,
            price_amount=price_amount,
            user_id=user_id,
        )

        assert invoice is not None
        assert button_name in invoice['title']
        assert button_name in invoice['description']
        assert invoice['prices'][0]['amount'] == price_amount

        # بررسی payload
        payload = invoice['payload']
        assert payload.startswith('dyn_')
        assert str(button_id) in payload
        assert str(user_id) in payload

    def test_create_service_invoice_without_user_id(self, payment_service):
        """تست ایجاد فاکتور برای سرویس بدون user_id"""
        invoice = payment_service.create_service_invoice(
            button_name='سرویس تست',
            button_id=1,
            price_amount=50000,
        )

        assert invoice is not None
        payload = invoice['payload']
        assert 'dyn_1' in payload  # button_id باید باشد

    # ============================================================
    # تست‌های verify_payment
    # ============================================================

    def test_verify_payment_success(self, payment_service, sample_payment_data):
        """تست تأیید پرداخت با موفقیت"""
        result = payment_service.verify_payment(sample_payment_data)

        assert result['is_valid'] is True
        assert result['tracking_code'] == sample_payment_data['successful_payment']['provider_payment_charge_id']
        assert result['total_amount'] == sample_payment_data['successful_payment']['total_amount']
        assert result['payload'] == sample_payment_data['successful_payment']['payload']
        assert result['payment_id'] == sample_payment_data['successful_payment']['payment_id']

    def test_verify_payment_no_data(self, payment_service):
        """تست تأیید پرداخت بدون داده"""
        result = payment_service.verify_payment({})

        assert result['is_valid'] is False
        assert result['error'] == 'No payment data found'

    def test_verify_payment_no_tracking_code(self, payment_service):
        """تست تأیید پرداخت بدون کد رهگیری"""
        data = {
            'successful_payment': {
                'total_amount': 50000,
                'payload': 'test_payload',
            }
        }
        result = payment_service.verify_payment(data)

        assert result['is_valid'] is False
        assert result['error'] == 'No tracking code found'

    def test_verify_payment_zero_amount(self, payment_service):
        """تست تأیید پرداخت با مبلغ صفر"""
        data = {
            'successful_payment': {
                'provider_payment_charge_id': 'TRK-123',
                'total_amount': 0,
                'payload': 'test_payload',
            }
        }
        result = payment_service.verify_payment(data)

        assert result['is_valid'] is False
        assert result['error'] == 'Invalid payment amount'

    # ============================================================
    # تست‌های parse_payment_payload
    # ============================================================

    def test_parse_payment_payload_dynamic(self, payment_service):
        """تست تجزیه payload داینامیک"""
        button_id = 5
        user_id = 123456789
        timestamp = 1234567890
        payload = f'dyn_{button_id}_{user_id}_{timestamp}'

        result = payment_service.parse_payment_payload(payload)

        assert result['is_valid'] is True
        assert result['type'] == 'dynamic'
        assert result['button_id'] == button_id
        assert result['user_id'] == user_id
        assert result['timestamp'] == str(timestamp)

    def test_parse_payment_payload_simple(self, payment_service):
        """تست تجزیه payload ساده"""
        payload = 'pay_1234567890'

        result = payment_service.parse_payment_payload(payload)

        assert result['is_valid'] is True
        assert result['type'] == 'simple'
        assert result['timestamp'] == '1234567890'

    def test_parse_payment_payload_unknown(self, payment_service):
        """تست تجزیه payload ناشناخته"""
        payload = 'unknown_payload'

        result = payment_service.parse_payment_payload(payload)

        assert result['is_valid'] is False
        assert result['type'] == 'unknown'
        assert result['payload'] == payload

    def test_parse_payment_payload_empty(self, payment_service):
        """تست تجزیه payload خالی"""
        result = payment_service.parse_payment_payload(None)

        assert result['is_valid'] is False
        assert result['type'] is None

    # ============================================================
    # تست‌های log_payment
    # ============================================================

    def test_log_payment_success(self, payment_service):
        """تست ثبت لاگ پرداخت با موفقیت"""
        with patch('database.db_stats.log_order_paid') as mock_log:
            result = payment_service.log_payment(
                user_id=123456789,
                order_id=1,
                tracking_code='TRK-123',
                amount=50000,
                status='success'
            )

            assert result is True
            mock_log.assert_called_once_with(1, 123456789, 50000)

    def test_log_payment_failed(self, payment_service):
        """تست ثبت لاگ پرداخت با خطا"""
        with patch('database.db_stats.log_order_paid', side_effect=Exception('DB error')):
            result = payment_service.log_payment(
                user_id=123456789,
                order_id=1,
                tracking_code='TRK-123',
                amount=50000,
            )

            assert result is False

    # ============================================================
    # تست‌های get_payment_summary
    # ============================================================

    def test_get_payment_summary(self, payment_service):
        """تست دریافت خلاصه پرداخت‌های کاربر"""
        user_id = 123456789
        total_payment = 150000
        orders_count = 3

        with patch('database.get_user_total_payment', return_value=total_payment):
            with patch('database.get_user_orders_count', return_value=orders_count):
                summary = payment_service.get_payment_summary(user_id)

                assert summary['user_id'] == user_id
                assert summary['total_paid'] == total_payment
                assert summary['orders_count'] == orders_count
                assert summary['avg_amount'] == total_payment / orders_count

    def test_get_payment_summary_no_orders(self, payment_service):
        """تست دریافت خلاصه پرداخت‌های کاربر بدون سفارش"""
        user_id = 123456789

        with patch('database.get_user_total_payment', return_value=0):
            with patch('database.get_user_orders_count', return_value=0):
                summary = payment_service.get_payment_summary(user_id)

                assert summary['user_id'] == user_id
                assert summary['total_paid'] == 0
                assert summary['orders_count'] == 0
                assert summary['avg_amount'] == 0

    # ============================================================
    # تست‌های get_total_revenue
    # ============================================================

    def test_get_total_revenue(self, payment_service):
        """تست دریافت درآمد کل"""
        dashboard_stats = {
            'total_revenue': 1000000,
            'total_orders': 20,
            'avg_order_value': 50000,
        }

        with patch('database.get_dashboard_stats', return_value=dashboard_stats):
            revenue = payment_service.get_total_revenue()

            assert revenue['total_revenue'] == 1000000
            assert revenue['total_orders'] == 20
            assert revenue['avg_order_value'] == 50000

    def test_get_total_revenue_error(self, payment_service):
        """تست دریافت درآمد کل با خطا"""
        with patch('database.get_dashboard_stats', side_effect=Exception('DB error')):
            revenue = payment_service.get_total_revenue()

            assert revenue['total_revenue'] == 0
            assert revenue['total_orders'] == 0
            assert revenue['avg_order_value'] == 0
            assert 'error' in revenue

    # ============================================================
    # تست‌های get_revenue_by_service
    # ============================================================

    def test_get_revenue_by_service(self, payment_service):
        """تست دریافت درآمد به تفکیک سرویس"""
        expected = [
            {'button_id': 1, 'service_name': 'سرویس اول', 'orders_count': 5, 'revenue': 250000},
            {'button_id': 2, 'service_name': 'سرویس دوم', 'orders_count': 3, 'revenue': 150000},
        ]

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = expected

        with patch.object(payment_service._connection, 'get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            result = payment_service.get_revenue_by_service()

            assert result == expected

    def test_get_revenue_by_service_error(self, payment_service):
        """تست دریافت درآمد به تفکیک سرویس با خطا"""
        with patch.object(payment_service._connection, 'get_cursor', side_effect=Exception('DB error')):
            result = payment_service.get_revenue_by_service()

            assert result == []

    # ============================================================
    # تست‌های verify_webhook_signature
    # ============================================================

    def test_verify_webhook_signature_success(self, payment_service):
        """تست بررسی امضای وب‌هوک با موفقیت"""
        data = {'test': 'data'}
        signature = 'expected_signature'

        with patch('hmac.compare_digest', return_value=True):
            result = payment_service.verify_webhook_signature(data, signature)
            assert result is True

    def test_verify_webhook_signature_fail(self, payment_service):
        """تست بررسی امضای وب‌هوک با شکست"""
        data = {'test': 'data'}
        signature = 'wrong_signature'

        with patch('hmac.compare_digest', return_value=False):
            result = payment_service.verify_webhook_signature(data, signature)
            assert result is False

    # ============================================================
    # تست‌های handle_webhook_payment
    # ============================================================

    def test_handle_webhook_payment_success(self, payment_service):
        """تست پردازش وب‌هوک پرداخت با موفقیت"""
        data = {
            'payment': {
                'tracking_code': 'TRK-123',
                'amount': 50000,
            },
            'user_id': 123456789,
            'order_id': 1,
        }

        with patch('services.order_service.OrderService') as mock_order_service:
            mock_order = MagicMock()
            mock_order.update_status.return_value = True
            mock_order.update_tracking_code.return_value = True
            mock_order_service.return_value = mock_order

            with patch.object(payment_service, 'log_payment', return_value=True):
                result = payment_service.handle_webhook_payment(data)

                assert result['success'] is True
                assert result['order_id'] == 1
                assert result['tracking_code'] == 'TRK-123'
                assert result['amount'] == 50000

    def test_handle_webhook_payment_missing_data(self, payment_service):
        """تست پردازش وب‌هوک با داده‌های ناقص"""
        data = {'payment': {}, 'user_id': 123456789}

        result = payment_service.handle_webhook_payment(data)

        assert result['success'] is False
        assert 'Missing required data' in result['error']

    def test_handle_webhook_payment_missing_tracking(self, payment_service):
        """تست پردازش وب‌هوک بدون کد رهگیری"""
        data = {
            'payment': {'amount': 50000},
            'user_id': 123456789,
            'order_id': 1,
        }

        result = payment_service.handle_webhook_payment(data)

        assert result['success'] is False
        assert 'Missing tracking code' in result['error']

    def test_handle_webhook_payment_update_fail(self, payment_service):
        """تست پردازش وب‌هوک با شکست در به‌روزرسانی سفارش"""
        data = {
            'payment': {
                'tracking_code': 'TRK-123',
                'amount': 50000,
            },
            'user_id': 123456789,
            'order_id': 1,
        }

        with patch('services.order_service.OrderService') as mock_order_service:
            mock_order = MagicMock()
            mock_order.update_status.return_value = False
            mock_order_service.return_value = mock_order

            result = payment_service.handle_webhook_payment(data)

            assert result['success'] is False
            assert 'Failed to update order status' in result['error']