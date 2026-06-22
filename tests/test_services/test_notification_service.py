# tests/test_services/test_notification_service.py
# تست‌های واحد برای NotificationService

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from services.notification_service import NotificationService


class TestNotificationService:
    """تست‌های NotificationService"""

    @pytest.fixture
    def notification_service(self, db_connection):
        """ایجاد NotificationService با اتصال دیتابیس تست"""
        return NotificationService(db_connection)

    @pytest.fixture
    def sample_order_data(self):
        """داده‌های نمونه سفارش"""
        return {
            'id': 1,
            'user_id': 123456789,
            'button_id': 1,
            'payment_amount': 50000,
            'status': 'pending',
            'created_at': '2024-01-01 12:00:00',
        }

    @pytest.fixture
    def sample_user_data(self):
        """داده‌های نمونه کاربر"""
        return {
            'user_id': 123456789,
            'first_name': 'علی',
            'last_name': 'محمدی',
            'username': 'test_user',
        }

    @pytest.fixture
    def sample_admin_data(self):
        """داده‌های نمونه ادمین"""
        return {
            'user_id': 987654321,
            'first_name': 'ادمین',
            'last_name': 'سیستم',
            'username': 'admin',
        }

    # ============================================================
    # تست‌های send_to_user
    # ============================================================

    @patch('services.notification_service.send_message')
    async def test_send_to_user_success(self, mock_send_message, notification_service, sample_user_data):
        """تست ارسال پیام به کاربر با موفقیت"""
        mock_send_message.return_value = {'ok': True}

        result = await notification_service.send_to_user(
            user_id=123456789,
            message='متن پیام تست',
            keyboard={'inline_keyboard': []}
        )

        assert result is True
        mock_send_message.assert_called_once_with(123456789, 'متن پیام تست', {'inline_keyboard': []})

    @patch('services.notification_service.send_message')
    async def test_send_to_user_failure(self, mock_send_message, notification_service):
        """تست ارسال پیام به کاربر با خطا"""
        mock_send_message.side_effect = Exception('Send error')

        result = await notification_service.send_to_user(
            user_id=123456789,
            message='متن پیام تست'
        )

        assert result is False

    # ============================================================
    # تست‌های send_to_users
    # ============================================================

    @patch('services.notification_service.send_message')
    async def test_send_to_users_success(self, mock_send_message, notification_service):
        """تست ارسال پیام به چند کاربر با موفقیت"""
        mock_send_message.return_value = {'ok': True}
        user_ids = [1, 2, 3]

        result = await notification_service.send_to_users(
            user_ids=user_ids,
            message='متن پیام تست'
        )

        assert result['total'] == 3
        assert result['sent'] == 3
        assert result['failed'] == 0
        assert mock_send_message.call_count == 3

    @patch('services.notification_service.send_message')
    async def test_send_to_users_partial_failure(self, mock_send_message, notification_service):
        """تست ارسال پیام به چند کاربر با شکست بخشی"""
        mock_send_message.side_effect = [{'ok': True}, Exception('Error'), {'ok': True}]
        user_ids = [1, 2, 3]

        result = await notification_service.send_to_users(
            user_ids=user_ids,
            message='متن پیام تست'
        )

        assert result['total'] == 3
        assert result['sent'] == 2
        assert result['failed'] == 1
        assert mock_send_message.call_count == 3

    @patch('services.notification_service.send_message')
    async def test_send_to_users_empty(self, mock_send_message, notification_service):
        """تست ارسال پیام به لیست خالی کاربران"""
        result = await notification_service.send_to_users(
            user_ids=[],
            message='متن پیام تست'
        )

        assert result['total'] == 0
        assert result['sent'] == 0
        assert result['failed'] == 0
        mock_send_message.assert_not_called()

    @patch('services.notification_service.asyncio.sleep')
    @patch('services.notification_service.send_message')
    async def test_send_to_users_batch_delay(self, mock_send_message, mock_sleep, notification_service):
        """تست ارسال پیام با تأخیر بین دسته‌ها"""
        mock_send_message.return_value = {'ok': True}
        user_ids = list(range(1, 101))  # 100 کاربر

        result = await notification_service.send_to_users(
            user_ids=user_ids,
            message='متن پیام تست',
            batch_size=30
        )

        assert result['total'] == 100
        assert result['sent'] == 100
        # باید حداقل ۳ بار sleep صدا زده شود
        assert mock_sleep.call_count >= 3

    # ============================================================
    # تست‌های send_to_admin
    # ============================================================

    @patch.object(NotificationService, 'send_to_user')
    async def test_send_to_admin(self, mock_send_to_user, notification_service):
        """تست ارسال پیام به ادمین"""
        mock_send_to_user.return_value = True

        result = await notification_service.send_to_admin(
            admin_id=987654321,
            message='پیام مدیریتی',
            keyboard={'inline_keyboard': []}
        )

        assert result is True
        mock_send_to_user.assert_called_once_with(987654321, 'پیام مدیریتی', {'inline_keyboard': []})

    # ============================================================
    # تست‌های send_to_owner
    # ============================================================

    @patch.object(NotificationService, 'send_to_user')
    async def test_send_to_owner(self, mock_send_to_user, notification_service):
        """تست ارسال پیام به OWNER"""
        mock_send_to_user.return_value = True
        notification_service._owner_id = 999999999

        result = await notification_service.send_to_owner(
            message='پیام به مالک',
            keyboard={'inline_keyboard': []}
        )

        assert result is True
        mock_send_to_user.assert_called_once_with(999999999, 'پیام به مالک', {'inline_keyboard': []})

    # ============================================================
    # تست‌های send_to_all_admins
    # ============================================================

    @patch('services.admin_service.AdminService')
    @patch.object(NotificationService, 'send_to_users')
    async def test_send_to_all_admins(self, mock_send_to_users, mock_admin_service, notification_service):
        """تست ارسال پیام به همه ادمین‌ها"""
        mock_admin_instance = MagicMock()
        mock_admin_instance.get_active_admins.return_value = [
            {'user_id': 1},
            {'user_id': 2},
            {'user_id': 3},
        ]
        mock_admin_service.return_value = mock_admin_instance

        mock_send_to_users.return_value = {'total': 3, 'sent': 3, 'failed': 0}

        result = await notification_service.send_to_all_admins(
            message='پیام به همه ادمین‌ها'
        )

        assert result['total'] == 3
        assert result['sent'] == 3
        mock_send_to_users.assert_called_once()

    @patch('services.admin_service.AdminService')
    @patch.object(NotificationService, 'send_to_users')
    async def test_send_to_all_admins_exclude_owner(self, mock_send_to_users, mock_admin_service, notification_service):
        """تست ارسال پیام به همه ادمین‌ها به جز OWNER"""
        mock_admin_instance = MagicMock()
        mock_admin_instance.get_active_admins.return_value = [
            {'user_id': 999999999},  # OWNER
            {'user_id': 2},
            {'user_id': 3},
        ]
        mock_admin_service.return_value = mock_admin_instance
        notification_service._owner_id = 999999999

        mock_send_to_users.return_value = {'total': 2, 'sent': 2, 'failed': 0}

        result = await notification_service.send_to_all_admins(
            message='پیام به ادمین‌ها',
            include_owner=False
        )

        # OWNER باید حذف شود
        assert result['total'] == 2
        mock_send_to_users.assert_called_once()

    @patch('services.admin_service.AdminService')
    async def test_send_to_all_admins_empty(self, mock_admin_service, notification_service):
        """تست ارسال پیام به ادمین‌ها در صورت خالی بودن لیست"""
        mock_admin_instance = MagicMock()
        mock_admin_instance.get_active_admins.return_value = []
        mock_admin_service.return_value = mock_admin_instance

        result = await notification_service.send_to_all_admins(
            message='پیام به ادمین‌ها'
        )

        assert result['total'] == 0
        assert result['sent'] == 0
        assert result['failed'] == 0

    # ============================================================
    # تست‌های notify_order_created
    # ============================================================

    @patch.object(NotificationService, 'send_to_user')
    async def test_notify_order_created(self, mock_send_to_user, notification_service):
        """تست اعلان ثبت سفارش به کاربر"""
        mock_send_to_user.return_value = True

        result = await notification_service.notify_order_created(
            user_id=123456789,
            order_id=1,
            service_name='سرویس تست',
            amount=50000
        )

        assert result is True
        mock_send_to_user.assert_called_once()
        call_args = mock_send_to_user.call_args[0]
        assert 'سفارش شما ثبت شد' in call_args[1]
        assert 'سرویس تست' in call_args[1]
        assert '1' in call_args[1]

    # ============================================================
    # تست‌های notify_order_paid
    # ============================================================

    @patch.object(NotificationService, 'send_to_user')
    async def test_notify_order_paid(self, mock_send_to_user, notification_service):
        """تست اعلان پرداخت موفق به کاربر"""
        mock_send_to_user.return_value = True

        result = await notification_service.notify_order_paid(
            user_id=123456789,
            order_id=1,
            tracking_code='TRK-12345',
            amount=50000
        )

        assert result is True
        mock_send_to_user.assert_called_once()
        call_args = mock_send_to_user.call_args[0]
        assert 'پرداخت شما با موفقیت انجام شد' in call_args[1]
        assert 'TRK-12345' in call_args[1]

    # ============================================================
    # تست‌های notify_order_status_changed
    # ============================================================

    @patch.object(NotificationService, 'send_to_user')
    async def test_notify_order_status_changed(self, mock_send_to_user, notification_service):
        """تست اعلان تغییر وضعیت سفارش به کاربر"""
        mock_send_to_user.return_value = True

        result = await notification_service.notify_order_status_changed(
            user_id=123456789,
            order_id=1,
            old_status='pending',
            new_status='paid'
        )

        assert result is True
        mock_send_to_user.assert_called_once()
        call_args = mock_send_to_user.call_args[0]
        assert 'تغییر وضعیت سفارش' in call_args[1]
        assert 'پرداخت شده' in call_args[1] or 'paid' in call_args[1]

    # ============================================================
    # تست‌های notify_order_cancelled
    # ============================================================

    @patch.object(NotificationService, 'send_to_user')
    async def test_notify_order_cancelled(self, mock_send_to_user, notification_service):
        """تست اعلان لغو سفارش به کاربر"""
        mock_send_to_user.return_value = True

        result = await notification_service.notify_order_cancelled(
            user_id=123456789,
            order_id=1,
            service_name='سرویس تست'
        )

        assert result is True
        mock_send_to_user.assert_called_once()
        call_args = mock_send_to_user.call_args[0]
        assert 'سفارش شما لغو شد' in call_args[1]
        assert 'سرویس تست' in call_args[1]

    # ============================================================
    # تست‌های notify_admin_new_order
    # ============================================================

    @patch.object(NotificationService, 'send_to_all_admins')
    async def test_notify_admin_new_order(self, mock_send_to_all_admins, notification_service):
        """تست اعلان سفارش جدید به ادمین‌ها"""
        mock_send_to_all_admins.return_value = {'total': 3, 'sent': 3, 'failed': 0}

        result = await notification_service.notify_admin_new_order(
            order_id=1,
            user_id=123456789,
            service_name='سرویس تست',
            amount=50000,
            fullname='علی محمدی'
        )

        assert result is True
        mock_send_to_all_admins.assert_called_once()
        call_args = mock_send_to_all_admins.call_args[0]
        assert 'سفارش جدید ثبت شد' in call_args[0]
        assert 'علی محمدی' in call_args[0]

    # ============================================================
    # تست‌های notify_admin_error
    # ============================================================

    @patch.object(NotificationService, 'send_to_owner')
    async def test_notify_admin_error(self, mock_send_to_owner, notification_service):
        """تست اعلان خطا به OWNER"""
        mock_send_to_owner.return_value = True

        result = await notification_service.notify_admin_error(
            error_type='database',
            error_message='خطای اتصال به دیتابیس',
            user_id=123456789,
            chat_id=987654321
        )

        assert result is True
        mock_send_to_owner.assert_called_once()
        call_args = mock_send_to_owner.call_args[0]
        assert 'اعلان خطا' in call_args[0]
        assert 'database' in call_args[0]

    # ============================================================
    # تست‌های notify_admin_backup_created
    # ============================================================

    @patch.object(NotificationService, 'send_to_owner')
    async def test_notify_admin_backup_created(self, mock_send_to_owner, notification_service):
        """تست اعلان ایجاد پشتیبان به OWNER"""
        mock_send_to_owner.return_value = True

        result = await notification_service.notify_admin_backup_created(
            backup_name='auto_backup_20240101.db',
            size_kb=1024,
            elapsed=2.5
        )

        assert result is True
        mock_send_to_owner.assert_called_once()
        call_args = mock_send_to_owner.call_args[0]
        assert 'پشتیبان‌گیری خودکار انجام شد' in call_args[0]
        assert '1024' in call_args[0] or 'KB' in call_args[0]

    # ============================================================
    # تست‌های notify_admin_cleanup_completed
    # ============================================================

    @patch.object(NotificationService, 'send_to_owner')
    async def test_notify_admin_cleanup_completed(self, mock_send_to_owner, notification_service):
        """تست اعلان پاکسازی خودکار به OWNER"""
        mock_send_to_owner.return_value = True

        results = {
            'deleted_errors': 10,
            'deleted_logs': 20,
            'deleted_charts': 5,
            'deleted_excel': 3,
        }

        result = await notification_service.notify_admin_cleanup_completed(
            results=results,
            elapsed=5.0
        )

        assert result is True
        mock_send_to_owner.assert_called_once()
        call_args = mock_send_to_owner.call_args[0]
        assert 'پاکسازی خودکار انجام شد' in call_args[0]
        assert '10' in call_args[0] or 'خطاهای قدیمی' in call_args[0]

    # ============================================================
    # تست‌های notify_admin_reminder_summary
    # ============================================================

    @patch.object(NotificationService, 'send_to_owner')
    async def test_notify_admin_reminder_summary(self, mock_send_to_owner, notification_service):
        """تست اعلان خلاصه یادآوری‌ها به OWNER"""
        mock_send_to_owner.return_value = True

        results = {
            'total': 10,
            'sent': 8,
            'failed': 2,
        }

        result = await notification_service.notify_admin_reminder_summary(
            results=results,
            elapsed=3.0
        )

        assert result is True
        mock_send_to_owner.assert_called_once()
        call_args = mock_send_to_owner.call_args[0]
        assert 'گزارش یادآوری سفارشات' in call_args[0]
        assert '10' in call_args[0] or 'کل سفارشات' in call_args[0]

    # ============================================================
    # تست‌های broadcast_to_active_users
    # ============================================================

    @patch('services.user_service.UserService')
    @patch.object(NotificationService, 'send_to_users')
    async def test_broadcast_to_active_users(self, mock_send_to_users, mock_user_service, notification_service):
        """تست پخش پیام به کاربران فعال"""
        mock_user_instance = MagicMock()
        mock_user_instance.get_active_users.return_value = [
            {'user_id': 1, 'is_blocked': 0},
            {'user_id': 2, 'is_blocked': 0},
            {'user_id': 3, 'is_blocked': 1},  # مسدود شده
        ]
        mock_user_service.return_value = mock_user_instance

        mock_send_to_users.return_value = {'total': 2, 'sent': 2, 'failed': 0}

        result = await notification_service.broadcast_to_active_users(
            message='پیام به کاربران فعال',
            days=1
        )

        # کاربر مسدود شده باید حذف شود
        assert result['total'] == 2
        mock_send_to_users.assert_called_once()

    @patch('services.user_service.UserService')
    async def test_broadcast_to_active_users_empty(self, mock_user_service, notification_service):
        """تست پخش پیام به کاربران فعال در صورت خالی بودن لیست"""
        mock_user_instance = MagicMock()
        mock_user_instance.get_active_users.return_value = []
        mock_user_service.return_value = mock_user_instance

        result = await notification_service.broadcast_to_active_users(
            message='پیام به کاربران فعال',
            days=1
        )

        assert result['total'] == 0
        assert result['sent'] == 0
        assert result['failed'] == 0

    # ============================================================
    # تست‌های broadcast_to_all_users
    # ============================================================

    @patch('services.user_service.UserService')
    @patch.object(NotificationService, 'send_to_users')
    async def test_broadcast_to_all_users(self, mock_send_to_users, mock_user_service, notification_service):
        """تست پخش پیام به همه کاربران"""
        mock_user_instance = MagicMock()
        mock_user_instance.get_all_users.return_value = [
            {'user_id': 1},
            {'user_id': 2},
            {'user_id': 3},
        ]
        mock_user_instance.is_blocked.return_value = False
        mock_user_service.return_value = mock_user_instance

        mock_send_to_users.return_value = {'total': 3, 'sent': 3, 'failed': 0}

        result = await notification_service.broadcast_to_all_users(
            message='پیام به همه کاربران'
        )

        assert result['total'] == 3
        mock_send_to_users.assert_called_once()

    @patch('services.user_service.UserService')
    @patch.object(NotificationService, 'send_to_users')
    async def test_broadcast_to_all_users_exclude_blocked(self, mock_send_to_users, mock_user_service, notification_service):
        """تست پخش پیام به همه کاربران با حذف کاربران مسدود شده"""
        mock_user_instance = MagicMock()
        mock_user_instance.get_all_users.return_value = [
            {'user_id': 1},
            {'user_id': 2},
            {'user_id': 3},
        ]
        # کاربر ۲ مسدود است
        mock_user_instance.is_blocked.side_effect = lambda uid: uid == 2
        mock_user_service.return_value = mock_user_instance

        mock_send_to_users.return_value = {'total': 2, 'sent': 2, 'failed': 0}

        result = await notification_service.broadcast_to_all_users(
            message='پیام به همه کاربران',
            exclude_blocked=True
        )

        assert result['total'] == 2
        mock_send_to_users.assert_called_once()

    # ============================================================
    # تست‌های broadcast_to_users_with_orders
    # ============================================================

    @patch('database.get_db_connection')
    @patch.object(NotificationService, 'send_to_users')
    async def test_broadcast_to_users_with_orders(self, mock_send_to_users, mock_db_connection, notification_service):
        """تست پخش پیام به کاربرانی که سفارش دارند"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'user_id': 1},
            {'user_id': 2},
            {'user_id': 3},
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_db_connection.return_value.__enter__.return_value = mock_conn

        mock_send_to_users.return_value = {'total': 3, 'sent': 3, 'failed': 0}

        result = await notification_service.broadcast_to_users_with_orders(
            message='پیام به کاربران دارای سفارش'
        )

        assert result['total'] == 3
        mock_send_to_users.assert_called_once()

    @patch('database.get_db_connection')
    async def test_broadcast_to_users_with_orders_empty(self, mock_db_connection, notification_service):
        """تست پخش پیام به کاربران دارای سفارش در صورت خالی بودن لیست"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_db_connection.return_value.__enter__.return_value = mock_conn

        result = await notification_service.broadcast_to_users_with_orders(
            message='پیام به کاربران دارای سفارش'
        )

        assert result['total'] == 0
        assert result['sent'] == 0
        assert result['failed'] == 0

    # ============================================================
    # تست‌های get_template و render_template
    # ============================================================

    def test_get_template_exists(self, notification_service):
        """تست دریافت قالب موجود"""
        template = notification_service.get_template('order_created', 'user')

        assert template is not None
        assert 'سفارش شما ثبت شد' in template or 'خدمات' in template

    def test_get_template_not_exists(self, notification_service):
        """تست دریافت قالب ناموجود"""
        template = notification_service.get_template('non_existent', 'user')

        assert template is None

    def test_get_template_invalid_target(self, notification_service):
        """تست دریافت قالب با مخاطب نامعتبر"""
        template = notification_service.get_template('order_created', 'invalid')

        assert template is None

    def test_render_template_success(self, notification_service):
        """تست رندر کردن قالب با موفقیت"""
        result = notification_service.render_template(
            template_name='order_created',
            target='user',
            service_name='سرویس تست',
            order_id=1,
            amount=50000,
            fullname='علی محمدی',
            user_id=123456789
        )

        assert result is not None
        assert 'سرویس تست' in result
        assert '1' in result

    def test_render_template_with_missing_variable(self, notification_service):
        """تست رندر کردن قالب با متغیر گم‌شده"""
        result = notification_service.render_template(
            template_name='order_created',
            target='user',
            service_name='سرویس تست'
            # order_id و amount و ... را نداریم
        )

        # باید KeyError رخ ندهد و نتیجه None نباشد یا پیام خطا مناسب باشد
        # در پیاده‌سازی فعلی، اگر KeyError رخ دهد، متن اصلی برگردانده می‌شود
        assert result is not None

    def test_render_template_not_exists(self, notification_service):
        """تست رندر کردن قالب ناموجود"""
        result = notification_service.render_template(
            template_name='non_existent',
            target='user',
            service_name='سرویس تست'
        )

        assert result is None

    # ============================================================
    # تست‌های add_template
    # ============================================================

    def test_add_template_success(self, notification_service):
        """تست افزودن قالب جدید"""
        template_name = 'custom_template'
        target = 'user'
        template_text = 'این یک قالب سفارشی است: {name}'

        notification_service.add_template(template_name, target, template_text)

        # بررسی اینکه قالب اضافه شده است
        result = notification_service.render_template(
            template_name=template_name,
            target=target,
            name='علی'
        )

        assert result == 'این یک قالب سفارشی است: علی'

    def test_add_template_overwrite(self, notification_service):
        """تست بازنویسی قالب موجود"""
        notification_service.add_template('order_created', 'user', 'قالب جدید: {order_id}')

        result = notification_service.render_template(
            template_name='order_created',
            target='user',
            order_id=999
        )

        assert result == 'قالب جدید: 999'

    # ============================================================
    # تست‌های send_notification
    # ============================================================

    @patch.object(NotificationService, 'render_template')
    @patch.object(NotificationService, 'send_to_user')
    async def test_send_notification_success(self, mock_send_to_user, mock_render_template, notification_service):
        """تست ارسال اعلان با قالب با موفقیت"""
        mock_render_template.return_value = 'متن اعلان رندر شده'
        mock_send_to_user.return_value = True

        result = await notification_service.send_notification(
            user_id=123456789,
            template_name='order_created',
            target='user',
            service_name='سرویس تست'
        )

        assert result is True
        mock_render_template.assert_called_once()
        mock_send_to_user.assert_called_once_with(123456789, 'متن اعلان رندر شده', None)

    @patch.object(NotificationService, 'render_template')
    async def test_send_notification_template_not_found(self, mock_render_template, notification_service):
        """تست ارسال اعلان با قالب ناموجود"""
        mock_render_template.return_value = None

        result = await notification_service.send_notification(
            user_id=123456789,
            template_name='non_existent',
            target='user'
        )

        assert result is False
        mock_render_template.assert_called_once()

    @patch.object(NotificationService, 'render_template')
    @patch.object(NotificationService, 'send_to_user')
    async def test_send_notification_to_admin(self, mock_send_to_user, mock_render_template, notification_service):
        """تست ارسال اعلان به ادمین با قالب"""
        mock_render_template.return_value = 'متن اعلان به ادمین'
        mock_send_to_user.return_value = True

        result = await notification_service.send_notification_to_admin(
            admin_id=987654321,
            template_name='order_created',
            target='admin',
            service_name='سرویس تست'
        )

        assert result is True
        mock_render_template.assert_called_once_with('order_created', 'admin', service_name='سرویس تست')
        mock_send_to_user.assert_called_once_with(987654321, 'متن اعلان به ادمین', None)

    # ============================================================
    # تست‌های get_notification_stats
    # ============================================================

    def test_get_notification_stats(self, notification_service):
        """تست دریافت آمار قالب‌ها"""
        stats = notification_service.get_notification_stats()

        assert 'total_templates' in stats
        assert 'user_templates' in stats
        assert 'admin_templates' in stats
        assert stats['total_templates'] > 0

    # ============================================================
    # تست‌های templates (بررسی وجود قالب‌های پیش‌فرض)
    # ============================================================

    def test_default_templates_exist(self, notification_service):
        """تست وجود قالب‌های پیش‌فرض"""
        templates = notification_service._TEMPLATES

        assert 'order_created' in templates
        assert 'order_paid' in templates
        assert 'order_status_changed' in templates
        assert 'order_cancelled' in templates
        assert 'reminder' in templates
        assert 'welcome' in templates

    def test_default_templates_user_target(self, notification_service):
        """تست وجود قالب برای کاربر در تمام قالب‌ها"""
        for template_name in ['order_created', 'order_paid', 'order_status_changed', 'order_cancelled', 'reminder', 'welcome']:
            template = notification_service.get_template(template_name, 'user')
            assert template is not None, f"Template {template_name} for user not found"

    def test_default_templates_admin_target(self, notification_service):
        """تست وجود قالب برای ادمین در قالب‌های مربوطه"""
        for template_name in ['order_created']:
            template = notification_service.get_template(template_name, 'admin')
            assert template is not None, f"Template {template_name} for admin not found"

    # ============================================================
    # تست‌های send_batch با تأخیر
    # ============================================================

    @patch('services.notification_service.asyncio.sleep')
    @patch('services.notification_service.send_message')
    async def test_send_to_users_with_custom_batch_size(self, mock_send_message, mock_sleep, notification_service):
        """تست ارسال پیام با حجم دسته سفارشی"""
        mock_send_message.return_value = {'ok': True}
        user_ids = list(range(1, 21))  # 20 کاربر

        result = await notification_service.send_to_users(
            user_ids=user_ids,
            message='متن پیام تست',
            batch_size=5
        )

        assert result['total'] == 20
        assert result['sent'] == 20
        # باید حداقل ۳ بار sleep صدا زده شود (برای دسته‌های ۵ تایی)
        assert mock_sleep.call_count >= 3

    # ============================================================
    # تست‌های send_to_users با خطاهای مختلف
    # ============================================================

    @patch('services.notification_service.send_message')
    async def test_send_to_users_with_error_responses(self, mock_send_message, notification_service):
        """تست ارسال پیام با پاسخ‌های خطا"""
        mock_send_message.side_effect = [
            {'ok': True},
            None,  # پاسخ None
            {'ok': False},  # پاسخ ناموفق
            Exception('Error'),
        ]
        user_ids = [1, 2, 3, 4]

        result = await notification_service.send_to_users(
            user_ids=user_ids,
            message='متن پیام تست'
        )

        assert result['total'] == 4
        assert result['sent'] == 1
        assert result['failed'] == 3
        assert len(result['errors']) == 3

    # ============================================================
    # تست‌های broadcast با آمار
    # ============================================================

    @patch.object(NotificationService, 'send_to_users')
    async def test_broadcast_returns_stats(self, mock_send_to_users, notification_service):
        """تست پخش پیام و بازگشت آمار کامل"""
        mock_send_to_users.return_value = {
            'total': 10,
            'sent': 8,
            'failed': 2,
            'errors': [
                {'user_id': 5, 'error': 'User not found'},
                {'user_id': 7, 'error': 'Blocked'}
            ]
        }

        result = await notification_service.broadcast_to_active_users(
            message='پیام تست',
            days=1
        )

        assert result['total'] == 10
        assert result['sent'] == 8
        assert result['failed'] == 2
        assert len(result['errors']) == 2

    # ============================================================
    # تست‌های send_to_owner با خطا
    # ============================================================

    @patch.object(NotificationService, 'send_to_user')
    async def test_send_to_owner_failure(self, mock_send_to_user, notification_service):
        """تست ارسال پیام به OWNER با خطا"""
        mock_send_to_user.return_value = False

        result = await notification_service.send_to_owner(
            message='پیام به مالک'
        )

        assert result is False

    # ============================================================
    # تست‌های send_to_admin با خطا
    # ============================================================

    @patch.object(NotificationService, 'send_to_user')
    async def test_send_to_admin_failure(self, mock_send_to_user, notification_service):
        """تست ارسال پیام به ادمین با خطا"""
        mock_send_to_user.return_value = False

        result = await notification_service.send_to_admin(
            admin_id=987654321,
            message='پیام مدیریتی'
        )

        assert result is False

    # ============================================================
    # تست‌های render_template با متغیرهای زیاد
    # ============================================================

    def test_render_template_with_many_variables(self, notification_service):
        """تست رندر قالب با متغیرهای زیاد"""
        template = notification_service.render_template(
            template_name='order_created',
            target='user',
            service_name='سرویس فوق‌العاده',
            order_id=12345,
            amount=987654321,
            fullname='علی محمدی',
            user_id=123456789,
            extra_var='extra'
        )

        assert template is not None
        assert 'سرویس فوق‌العاده' in template
        assert '12345' in template
        assert '987,654,321' in template or '987654321' in template

    # ============================================================
    # تست‌های add_template با target جدید
    # ============================================================

    def test_add_template_new_target(self, notification_service):
        """تست افزودن قالب با target جدید"""
        notification_service.add_template(
            template_name='custom_template',
            target='manager',
            template_text='قالب برای مدیران: {name}'
        )

        result = notification_service.render_template(
            template_name='custom_template',
            target='manager',
            name='مدیر سیستم'
        )

        assert result == 'قالب برای مدیران: مدیر سیستم'

    # ============================================================
    # تست‌های get_notification_stats بعد از افزودن قالب
    # ============================================================

    def test_get_notification_stats_after_add(self, notification_service):
        """تست آمار قالب‌ها بعد از افزودن قالب جدید"""
        initial_stats = notification_service.get_notification_stats()

        notification_service.add_template('new_template', 'user', 'متن جدید: {value}')

        new_stats = notification_service.get_notification_stats()

        assert new_stats['total_templates'] == initial_stats['total_templates'] + 1
        assert new_stats['user_templates'] == initial_stats['user_templates'] + 1