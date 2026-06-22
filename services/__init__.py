# services/__init__.py
# پکیج سرویس‌ها - لایه منطق کسب‌وکار (Business Logic Layer)
# این پکیج شامل سرویس‌های مختلف برای مدیریت عملیات اصلی ربات است

from .order_service import OrderService
from .payment_service import PaymentService
from .validation_service import ValidationService
from .button_service import ButtonService
from .user_service import UserService
from .analytics_service import AnalyticsService
from .admin_service import AdminService
from .template_service import TemplateService
from .backup_service import BackupService
from .cache_service import CacheService
from .notification_service import NotificationService

# ========== سرویس جدید مانیتورینگ ==========
from .monitoring_service import MonitoringService


class BaseService:
    def __init__(self, connection, repository=None):
        self._connection = connection
        self._repository = repository
    
    @property
    def connection(self):
        return self._connection
    
    @property
    def repository(self):
        return self._repository


def create_services(connection, repositories=None):
    if repositories is None:
        from repositories import create_repositories
        repositories = create_repositories(connection)
    
    return {
        'order': OrderService(connection, repositories.get('order')),
        'payment': PaymentService(connection),
        'validation': ValidationService(connection),
        'button': ButtonService(connection, repositories.get('button')),
        'user': UserService(connection, repositories.get('user')),
        'analytics': AnalyticsService(connection, repositories.get('order'), repositories.get('button')),
        'admin': AdminService(connection, repositories.get('admin')),
        'template': TemplateService(connection, repositories.get('question')),
        'backup': BackupService(connection),
        'cache': CacheService(connection),
        'notification': NotificationService(connection),
        'monitoring': MonitoringService(connection, repositories.get('monitoring')),
    }


__all__ = [
    'OrderService',
    'PaymentService',
    'ValidationService',
    'ButtonService',
    'UserService',
    'AnalyticsService',
    'AdminService',
    'TemplateService',
    'BackupService',
    'CacheService',
    'NotificationService',
    'MonitoringService',
    'BaseService',
    'create_services',
]