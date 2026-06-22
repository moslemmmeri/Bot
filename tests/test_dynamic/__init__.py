# tests/test_dynamic/__init__.py
# پکیج تست‌های ماژول داینامیک (Dynamic Module)

"""
پکیج `test_dynamic` شامل تست‌های واحد برای ماژول داینامیک است که مسئول پردازش فرم‌های پویا،
سوالات شرطی، اعتبارسنجی و پرداخت‌های مرتبط با سرویس‌ها می‌باشد.

ماژول‌های تست‌شده:
- test_validation: تست‌های اعتبارسنجی داینامیک (dynamic_validation.py)
- test_core: تست‌های توابع پایه داینامیک (dynamic_core.py)
- test_handlers: تست‌های هندلرهای داینامیک (dynamic_handlers.py)

اجرای تست‌های این پکیج:
    # اجرای همه تست‌های ماژول داینامیک
    pytest tests/test_dynamic/
    
    # اجرای یک فایل خاص
    pytest tests/test_dynamic/test_validation.py
    
    # اجرای با گزارش پوشش
    pytest tests/test_dynamic/ --cov=dynamic --cov-report=term
"""

# ============================================================
# صادر کردن
# ============================================================

__all__ = []