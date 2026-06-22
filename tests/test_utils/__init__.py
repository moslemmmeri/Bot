# tests/test_utils/__init__.py
# پکیج تست‌های توابع کمکی (Utility Functions)

"""
پکیج `test_utils` شامل تست‌های واحد برای تمام توابع کمکی در پکیج `utils` است.

توابع تست‌شده:
- test_formatters: تست‌های توابع فرمت‌بندی (اعداد، تاریخ، قیمت، ...)
- test_order_helpers: تست‌های توابع کمکی سفارشات
- test_user_helpers: تست‌های توابع کمکی کاربران
- test_text_helpers: تست‌های توابع پردازش متن

اجرای تست‌های این پکیج:
    # اجرای همه تست‌های توابع کمکی
    pytest tests/test_utils/
    
    # اجرای یک فایل خاص
    pytest tests/test_utils/test_formatters.py
    
    # اجرای با گزارش پوشش
    pytest tests/test_utils/ --cov=utils --cov-report=term
"""

# ============================================================
# صادر کردن
# ============================================================

__all__ = []