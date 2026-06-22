# tests/test_repositories/__init__.py
# پکیج تست‌های ریپازیتوری‌ها - لایه Data Access

"""
پکیج `test_repositories` شامل تست‌های واحد برای تمام ریپازیتوری‌های پروژه است.

ریپازیتوری‌های تست‌شده:
- test_order_repository: تست‌های OrderRepository (مدیریت سفارشات در دیتابیس)
- test_user_repository: تست‌های UserRepository (مدیریت کاربران در دیتابیس)
- test_button_repository: تست‌های ButtonRepository (مدیریت دکمه‌ها در دیتابیس)
- test_category_repository: تست‌های CategoryRepository (مدیریت دسته‌بندی‌ها)
- test_question_repository: تست‌های QuestionRepository (مدیریت سوالات)
- test_admin_repository: تست‌های AdminRepository (مدیریت ادمین‌ها)

اجرای تست‌های این پکیج:
    # اجرای همه تست‌های ریپازیتوری‌ها
    pytest tests/test_repositories/
    
    # اجرای یک فایل خاص
    pytest tests/test_repositories/test_order_repository.py
    
    # اجرای با گزارش پوشش
    pytest tests/test_repositories/ --cov=repositories --cov-report=term
"""

# ============================================================
# صادر کردن
# ============================================================

__all__ = []