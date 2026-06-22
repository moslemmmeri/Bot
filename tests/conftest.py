# tests/conftest.py
# تنظیمات Fixtureها و پیکربندی pytest برای تست‌های واحد

import os
import sys
import pytest
import sqlite3
import asyncio
import tempfile
from typing import Generator, AsyncGenerator, Dict, Any
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# افزودن مسیر پروژه به PYTHONPATH
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# تنظیم متغیرهای محیطی برای تست
os.environ.setdefault('TESTING', 'true')
os.environ.setdefault('DATABASE_TYPE', 'sqlite')
os.environ.setdefault('SQLITE_DB_PATH', ':memory:')
os.environ.setdefault('REDIS_ENABLED', 'false')
os.environ.setdefault('RATE_LIMIT_ENABLED', 'false')


# ============================================================
# Fixtureهای پایه
# ============================================================

@pytest.fixture(scope='session')
def event_loop() -> Generator:
    """ایجاد event loop برای تست‌های async"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope='function')
def temp_db_path() -> Generator[str, None, None]:
    """ایجاد یک فایل دیتابیس موقت برای هر تست"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp_path = tmp.name
    
    yield tmp_path
    
    # پاک‌سازی بعد از تست
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture(scope='function')
def db_connection(temp_db_path: str) -> Generator[sqlite3.Connection, None, None]:
    """ایجاد اتصال به دیتابیس تست با جدول‌های کامل"""
    # استفاده از دیتابیس موقت به جای :memory: برای پشتیبانی از FK
    conn = sqlite3.connect(temp_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    
    # ایجاد جداول کامل از init_db
    from database.connection.init import create_tables
    from database.connection.manager import get_db_connection
    
    # ایجاد جداول با استفاده از get_db_connection
    with patch('database.connection.manager.DB_NAME', temp_db_path):
        from database.connection.manager import init_db
        init_db()
    
    yield conn
    conn.close()


@pytest.fixture(scope='function')
def mock_cache() -> Generator[MagicMock, None, None]:
    """ایجاد Mock برای CacheManager"""
    with patch('cache.CacheManager') as mock:
        mock_instance = MagicMock()
        mock_instance._enabled = False
        mock_instance.get = AsyncMock(return_value=None)
        mock_instance.set = AsyncMock(return_value=True)
        mock_instance.delete = AsyncMock(return_value=1)
        mock_instance.exists = AsyncMock(return_value=False)
        mock_instance.get_or_set = AsyncMock(return_value=None)
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope='function')
def mock_state_service() -> Generator[MagicMock, None, None]:
    """ایجاد Mock برای StateService"""
    with patch('services.state_service.StateService') as mock:
        mock_instance = MagicMock()
        mock_instance.get_state = AsyncMock(return_value={})
        mock_instance.set_state = AsyncMock(return_value=True)
        mock_instance.update_state = AsyncMock(return_value=True)
        mock_instance.clear_state = AsyncMock(return_value=True)
        mock_instance.exists = AsyncMock(return_value=False)
        mock_instance.get_state_field = AsyncMock(return_value=None)
        mock_instance.set_state_field = AsyncMock(return_value=True)
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope='function')
def mock_permission_service() -> Generator[MagicMock, None, None]:
    """ایجاد Mock برای PermissionService"""
    with patch('services.permission_service.PermissionService') as mock:
        mock_instance = MagicMock()
        mock_instance.is_owner = MagicMock(return_value=False)
        mock_instance.can_access_admin = AsyncMock(return_value=False)
        mock_instance.has_permission = AsyncMock(return_value=False)
        mock_instance.get_user_role = AsyncMock(return_value=None)
        mock_instance.get_user_role_label = AsyncMock(return_value='کاربر عادی')
        mock.return_value = mock_instance
        yield mock_instance


# ============================================================
# Fixtureهای دیتا
# ============================================================

@pytest.fixture(scope='function')
def sample_user_data() -> Dict[str, Any]:
    """داده‌های نمونه کاربر"""
    return {
        'user_id': 123456789,
        'username': 'test_user',
        'first_name': 'علی',
        'last_name': 'محمدی',
        'first_seen': datetime.now().isoformat(),
        'last_active': datetime.now().isoformat(),
        'is_blocked': 0,
        'role': 0,
        'status': 0,
        'language': 'fa',
        'timezone': 'Asia/Tehran',
    }


@pytest.fixture(scope='function')
def sample_button_data() -> Dict[str, Any]:
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
        'is_active': 1,
    }


@pytest.fixture(scope='function')
def sample_order_data() -> Dict[str, Any]:
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
        'status': 'pending',
        'tracking_code': 'TRK-12345',
    }


@pytest.fixture(scope='function')
def sample_question_data() -> Dict[str, Any]:
    """داده‌های نمونه سوال"""
    return {
        'button_id': 1,
        'question_text': 'نام کامل خود را وارد کنید:',
        'question_type': 'text',
        'is_required': 1,
        'validation_type': 'text',
        'needs_button': 0,
        'sort_order': 0,
    }


# ============================================================
# Fixtureهای خدمات
# ============================================================

@pytest.fixture(scope='function')
def user_service(db_connection):
    """ایجاد UserService با اتصال دیتابیس تست"""
    from services.user_service import UserService
    return UserService(db_connection)


@pytest.fixture(scope='function')
def order_service(db_connection):
    """ایجاد OrderService با اتصال دیتابیس تست"""
    from services.order_service import OrderService
    return OrderService(db_connection)


@pytest.fixture(scope='function')
def button_service(db_connection):
    """ایجاد ButtonService با اتصال دیتابیس تست"""
    from services.button_service import ButtonService
    return ButtonService(db_connection)


@pytest.fixture(scope='function')
def validation_service(db_connection):
    """ایجاد ValidationService با اتصال دیتابیس تست"""
    from services.validation_service import ValidationService
    return ValidationService(db_connection)


@pytest.fixture(scope='function')
def payment_service(db_connection):
    """ایجاد PaymentService با اتصال دیتابیس تست"""
    from services.payment_service import PaymentService
    return PaymentService(db_connection)


@pytest.fixture(scope='function')
def admin_service(db_connection):
    """ایجاد AdminService با اتصال دیتابیس تست"""
    from services.admin_service import AdminService
    return AdminService(db_connection)


@pytest.fixture(scope='function')
def analytics_service(db_connection):
    """ایجاد AnalyticsService با اتصال دیتابیس تست"""
    from services.analytics_service import AnalyticsService
    return AnalyticsService(db_connection)


# ============================================================
# Fixtureهای کمکی برای تست‌های شبیه‌سازی
# ============================================================

@pytest.fixture(scope='function')
def mock_message_update() -> Dict[str, Any]:
    """ایجاد آپدیت شبیه‌سازی‌شده پیام"""
    return {
        'message': {
            'message_id': 123,
            'from': {
                'id': 123456789,
                'first_name': 'علی',
                'last_name': 'محمدی',
                'username': 'test_user',
            },
            'chat': {
                'id': 123456789,
            },
            'text': '/start',
            'date': int(datetime.now().timestamp()),
        }
    }


@pytest.fixture(scope='function')
def mock_callback_update() -> Dict[str, Any]:
    """ایجاد آپدیت شبیه‌سازی‌شده کالبک"""
    return {
        'callback_query': {
            'id': '123456789',
            'from': {
                'id': 123456789,
                'first_name': 'علی',
                'last_name': 'محمدی',
                'username': 'test_user',
            },
            'message': {
                'message_id': 123,
                'chat': {
                    'id': 123456789,
                },
                'text': 'متن پیام',
            },
            'data': 'back_main',
        }
    }


# ============================================================
# Fixtureهای پاک‌سازی
# ============================================================

@pytest.fixture(scope='function', autouse=True)
def cleanup_user_states():
    """پاک‌سازی user_states بعد از هر تست"""
    from core import user_states
    original_states = dict(user_states)
    user_states.clear()
    yield
    user_states.clear()
    user_states.update(original_states)


# ============================================================
# پیکربندی pytest
# ============================================================

def pytest_configure(config):
    """پیکربندی pytest برای تست‌ها"""
    # تنظیم نشانه‌های سفارشی
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'event_loop',
    'temp_db_path',
    'db_connection',
    'mock_cache',
    'mock_state_service',
    'mock_permission_service',
    'sample_user_data',
    'sample_button_data',
    'sample_order_data',
    'sample_question_data',
    'user_service',
    'order_service',
    'button_service',
    'validation_service',
    'payment_service',
    'admin_service',
    'analytics_service',
    'mock_message_update',
    'mock_callback_update',
    'cleanup_user_states',
]