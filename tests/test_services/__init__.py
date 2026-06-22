# tests/test_services/__init__.py
# پکیج تست‌های سرویس‌ها - لایه Business Logic

"""
پکیج `test_services` شامل تست‌های واحد برای تمام سرویس‌های پروژه است.

سرویس‌های تست‌شده:
- test_order_service: تست‌های OrderService (مدیریت سفارشات)
- test_user_service: تست‌های UserService (مدیریت کاربران)
- test_validation_service: تست‌های ValidationService (اعتبارسنجی)
- test_button_service: تست‌های ButtonService (مدیریت دکمه‌ها)
- test_payment_service: تست‌های PaymentService (مدیریت پرداخت‌ها)
- test_admin_service: تست‌های AdminService (مدیریت ادمین‌ها)
- test_analytics_service: تست‌های AnalyticsService (آمار و تحلیل)
- test_template_service: تست‌های TemplateService (مدیریت الگوها)
- test_backup_service: تست‌های BackupService (پشتیبان‌گیری)
- test_cache_service: تست‌های CacheService (مدیریت کش)
- test_notification_service: تست‌های NotificationService (اعلان‌ها)

اجرای تست‌های این پکیج:
    # اجرای همه تست‌های سرویس‌ها
    pytest tests/test_services/
    
    # اجرای یک فایل خاص
    pytest tests/test_services/test_order_service.py
    
    # اجرای با گزارش پوشش
    pytest tests/test_services/ --cov=services --cov-report=term
"""

# ============================================================
# صادر کردن
# ============================================================

__all__ = []