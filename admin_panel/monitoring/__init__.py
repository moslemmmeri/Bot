# admin_panel/monitoring/__init__.py
# پکیج مانیتورینگ و نظارت بر سیستم
# شامل: داشبورد لحظه‌ای، بررسی سلامت، سیستم هشدار، جمع‌آوری متریک‌ها، گزارش‌های دوره‌ای و تسک‌های زمان‌بندی‌شده

"""
پکیج `monitoring` شامل ابزارهای جامع برای نظارت و مانیتورینگ ربات است.

زیرماژول‌ها:
- dashboard: داشبورد مانیتورینگ با آمار لحظه‌ای و نمودارهای به‌روز
- health: بررسی سلامت سرویس‌ها (دیتابیس، Redis، API و ...)
- alerts: سیستم هشدار و اعلان‌های خودکار برای شرایط بحرانی
- metrics: جمع‌آوری و ذخیره‌سازی متریک‌های عملکردی
- routes: ثبت روت‌های مربوط به مانیتورینگ در پنل مدیریت
- reports: تولید گزارش‌های دوره‌ای (روزانه، هفتگی، ماهانه)
- tasks: تسک‌های زمان‌بندی‌شده‌ی مانیتورینگ (بررسی دوره‌ای، هشدارها و ...)

استفاده:
    از admin_panel.monitoring import (
        handle_monitoring,
        handle_health_check,
        handle_alerts,
        handle_metrics,
        handle_reports,
    )
"""

# ============================================================
# ایمپورت زیرماژول‌ها
# ============================================================

from . import dashboard
from . import health
from . import alerts
from . import metrics
from . import routes
from . import reports
from . import tasks

# ============================================================
# صادر کردن توابع اصلی از زیرماژول‌ها
# ============================================================

# dashboard
from .dashboard import (
    handle_monitoring,
    get_monitoring_stats,
    get_dashboard_stats,
    get_active_users_stats,
    get_api_latency_stats,
    get_error_rate_stats,
    get_scheduler_status_stats,
)

# health
from .health import (
    handle_health_check,
    run_health_check,
    check_db_health,
    check_redis_health,
    check_bale_api,
    check_disk_usage,
    get_db_size,
    get_system_resources,
)

# alerts
from .alerts import (
    handle_alerts,
    check_alerts,
    send_alert_message,
    get_active_alerts,
    resolve_alert,
    get_alert_history,
    Alert,
    AlertLevel,
)

# metrics
from .metrics import (
    handle_metrics,
    collect_metrics,
    get_metrics_summary,
    get_metrics_by_type,
    cleanup_old_metrics,
    MetricType,
)

# routes (همه روت‌ها به‌صورت خودکار با ایمپورت routes ثبت می‌شوند)
from .routes import (
    admin_monitoring,
    admin_monitoring_health,
    admin_monitoring_alerts,
    admin_monitoring_metrics,
    admin_monitoring_reports,
)

# reports
from .reports import (
    handle_reports,
    generate_daily_report,
    generate_weekly_report,
    generate_monthly_report,
    get_report_history,
    generate_custom_report,
    send_report_to_admin,
)

# tasks
from .tasks import (
    run_monitoring_check,
    run_daily_report,
    run_alert_check,
    run_metrics_cleanup,
    setup_monitoring_tasks,
)


# ============================================================
# __all__ برای کنترل صادرات
# ============================================================

__all__ = [
    # dashboard
    'handle_monitoring',
    'get_monitoring_stats',
    'get_dashboard_stats',
    'get_active_users_stats',
    'get_api_latency_stats',
    'get_error_rate_stats',
    'get_scheduler_status_stats',
    
    # health
    'handle_health_check',
    'run_health_check',
    'check_db_health',
    'check_redis_health',
    'check_bale_api',
    'check_disk_usage',
    'get_db_size',
    'get_system_resources',
    
    # alerts
    'handle_alerts',
    'check_alerts',
    'send_alert_message',
    'get_active_alerts',
    'resolve_alert',
    'get_alert_history',
    'Alert',
    'AlertLevel',
    
    # metrics
    'handle_metrics',
    'collect_metrics',
    'get_metrics_summary',
    'get_metrics_by_type',
    'cleanup_old_metrics',
    'MetricType',
    
    # routes
    'admin_monitoring',
    'admin_monitoring_health',
    'admin_monitoring_alerts',
    'admin_monitoring_metrics',
    'admin_monitoring_reports',
    
    # reports
    'handle_reports',
    'generate_daily_report',
    'generate_weekly_report',
    'generate_monthly_report',
    'get_report_history',
    'generate_custom_report',
    'send_report_to_admin',
    
    # tasks
    'run_monitoring_check',
    'run_daily_report',
    'run_alert_check',
    'run_metrics_cleanup',
    'setup_monitoring_tasks',
]