# repositories/__init__.py
# پکیج ریپازیتوری‌ها - لایه دسترسی به داده
# شامل ریپازیتوری‌های تمام موجودیت‌های دیتابیس

from .base_repository import BaseRepository
from .user_repository import UserRepository
from .order_repository import OrderRepository
from .button_repository import ButtonRepository
from .category_repository import CategoryRepository
from .question_repository import QuestionRepository
from .admin_repository import AdminRepository
from .monitoring_repository import MonitoringRepository

# تابع Factory برای ایجاد ریپازیتوری‌ها با اتصال به دیتابیس


def create_repositories(connection):
    """
    ایجاد تمام ریپازیتوری‌ها با یک اتصال دیتابیس مشترک
    
    پارامترها:
        connection: اتصال به دیتابیس
    
    بازگشت: دیکشنری شامل تمام ریپازیتوری‌ها
    """
    return {
        'user': UserRepository(connection),
        'order': OrderRepository(connection),
        'button': ButtonRepository(connection),
        'category': CategoryRepository(connection),
        'question': QuestionRepository(connection),
        'admin': AdminRepository(connection),
        'monitoring': MonitoringRepository(connection),
    }


__all__ = [
    # ریپازیتوری‌ها
    'BaseRepository',
    'UserRepository',
    'OrderRepository',
    'ButtonRepository',
    'CategoryRepository',
    'QuestionRepository',
    'AdminRepository',
    'MonitoringRepository',
    # توابع کمکی
    'create_repositories',
]