# tests/__init__.py
# پکیج تست‌های واحد (Unit Tests) برای پروژه ربات
# شامل تست‌های سرویس‌ها، ریپازیتوری‌ها، ابزارها و ماژول‌های مختلف

"""
پکیج `tests` شامل تست‌های واحد و یکپارچه برای تمام ماژول‌های پروژه است.

ساختار پکیج:
- conftest.py: تنظیمات fixtureها و پیکربندی pytest
- test_services/: تست‌های سرویس‌ها (Business Logic)
- test_repositories/: تست‌های ریپازیتوری‌ها (Data Access)
- test_utils/: تست‌های توابع کمکی
- test_dynamic/: تست‌های ماژول داینامیک
- test_handlers/: تست‌های هندلرها (در آینده)

اجرای تست‌ها:
    # اجرای همه تست‌ها
    pytest
    
    # اجرای با گزارش پوشش کد
    pytest --cov=. --cov-report=html
    
    # اجرای یک فایل خاص
    pytest tests/test_services/test_order_service.py
    
    # اجرای با جزئیات بیشتر
    pytest -v
"""

# ============================================================
# تنظیمات مسیر برای تست‌ها
# ============================================================

import os
import sys

# افزودن مسیر پروژه به PYTHONPATH برای importهای صحیح
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# تنظیم متغیر محیطی برای تست
os.environ.setdefault('TESTING', 'true')


# ============================================================
# صادر کردن
# ============================================================

__all__ = []