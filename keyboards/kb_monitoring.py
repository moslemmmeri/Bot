# keyboards/kb_monitoring.py
# کیبوردهای مربوط به بخش مانیتورینگ و نظارت بر سیستم
# شامل: کیبورد اصلی، سلامت، هشدارها، متریک‌ها و گزارش‌ها

from typing import Dict, Any, List, Optional


# ============================================================
# کیبورد اصلی مانیتورینگ
# ============================================================

def monitoring_main_keyboard() -> Dict[str, Any]:
    """
    کیبورد اصلی بخش مانیتورینگ

    بازگشت: کیبورد با گزینه‌های اصلی
    """
    return {
        "inline_keyboard": [
            [{"text": "📊 داشبورد لحظه‌ای", "callback_data": "admin_monitoring"}],
            [{"text": "🏥 بررسی سلامت سرویس‌ها", "callback_data": "admin_monitoring_health"}],
            [{"text": "🚨 مدیریت هشدارها", "callback_data": "admin_monitoring_alerts"}],
            [{"text": "📈 متریک‌های سیستم", "callback_data": "admin_monitoring_metrics"}],
            [{"text": "📄 گزارش‌های دوره‌ای", "callback_data": "admin_monitoring_reports"}],
            [{"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_back"}]
        ]
    }


# ============================================================
# کیبوردهای بخش سلامت (Health)
# ============================================================

def monitoring_health_keyboard() -> Dict[str, Any]:
    """
    کیبورد بخش بررسی سلامت

    بازگشت: کیبورد با گزینه‌های بررسی سلامت
    """
    return {
        "inline_keyboard": [
            [{"text": "🔄 بررسی مجدد همه سرویس‌ها", "callback_data": "admin_monitoring_health"}],
            [{"text": "📊 بازگشت به داشبورد", "callback_data": "admin_monitoring"}],
            [{"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring_main"}],
            [{"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_back"}]
        ]
    }


def monitoring_health_detail_keyboard(service: str) -> Dict[str, Any]:
    """
    کیبورد بررسی جزئیات یک سرویس خاص

    پارامترها:
        service: نام سرویس (database, redis, api, disk)

    بازگشت: کیبورد با گزینه‌های مربوط به سرویس
    """
    return {
        "inline_keyboard": [
            [{"text": f"🔄 بررسی مجدد {service}", "callback_data": f"admin_monitoring_health_{service}"}],
            [{"text": "🔙 بازگشت به بررسی سلامت", "callback_data": "admin_monitoring_health"}],
            [{"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring_main"}]
        ]
    }


# ============================================================
# کیبوردهای بخش هشدارها (Alerts)
# ============================================================

def monitoring_alerts_keyboard(
    has_active_alerts: bool = False,
    has_history: bool = False
) -> Dict[str, Any]:
    """
    کیبورد بخش مدیریت هشدارها

    پارامترها:
        has_active_alerts: آیا هشدار فعال وجود دارد
        has_history: آیا تاریخچه هشدار وجود دارد

    بازگشت: کیبورد با گزینه‌های مدیریت هشدارها
    """
    keyboard = []

    if has_active_alerts:
        keyboard.append([
            {"text": "🚨 مشاهده هشدارهای فعال", "callback_data": "admin_monitoring_alerts_active"}
        ])
        keyboard.append([
            {"text": "✅ حل کردن همه هشدارها", "callback_data": "admin_monitoring_alerts_resolve_all"}
        ])
    else:
        keyboard.append([
            {"text": "✅ هیچ هشدار فعالی وجود ندارد", "callback_data": "admin_none"}
        ])

    if has_history:
        keyboard.append([
            {"text": "📋 تاریخچه هشدارها", "callback_data": "admin_monitoring_alerts_history"}
        ])

    keyboard.append([
        {"text": "🔄 بررسی و ارسال هشدارهای جدید", "callback_data": "admin_monitoring_alerts_check"}
    ])

    keyboard.append([
        {"text": "🔙 بازگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring_main"},
        {"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_back"}
    ])

    return {"inline_keyboard": keyboard}


def monitoring_alert_detail_keyboard(alert_id: int, is_resolved: bool = False) -> Dict[str, Any]:
    """
    کیبورد جزئیات یک هشدار

    پارامترها:
        alert_id: شناسه هشدار
        is_resolved: آیا هشدار حل شده است

    بازگشت: کیبورد با گزینه‌های مدیریت هشدار
    """
    keyboard = []

    if not is_resolved:
        keyboard.append([
            {"text": "✅ حل کردن این هشدار", "callback_data": f"admin_monitoring_alerts_resolve_{alert_id}"}
        ])

    keyboard.append([
        {"text": "🔙 بازگشت به لیست هشدارها", "callback_data": "admin_monitoring_alerts"},
        {"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring_main"}
    ])

    return {"inline_keyboard": keyboard}


# ============================================================
# کیبوردهای بخش متریک‌ها (Metrics)
# ============================================================

def monitoring_metrics_keyboard() -> Dict[str, Any]:
    """
    کیبورد بخش مدیریت متریک‌ها

    بازگشت: کیبورد با گزینه‌های متریک‌ها
    """
    return {
        "inline_keyboard": [
            [{"text": "🔄 جمع‌آوری متریک‌های جدید", "callback_data": "admin_monitoring_metrics_collect"}],
            [{"text": "📊 خلاصه متریک‌ها", "callback_data": "admin_monitoring_metrics_summary"}],
            [{"text": "🗑️ پاکسازی متریک‌های قدیمی", "callback_data": "admin_monitoring_metrics_cleanup"}],
            [{"text": "📈 نمایش نمودار متریک‌ها", "callback_data": "admin_monitoring_metrics_chart"}],
            [{"text": "🔙 بازگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring_main"}],
            [{"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_back"}]
        ]
    }


def monitoring_metrics_type_keyboard(metric_types: List[str]) -> Dict[str, Any]:
    """
    کیبورد انتخاب نوع متریک برای نمایش

    پارامترها:
        metric_types: لیست انواع متریک‌های موجود

    بازگشت: کیبورد با گزینه‌های انواع متریک
    """
    keyboard = []
    for metric_type in metric_types[:10]:  # حداکثر ۱۰ نوع
        # تبدیل نوع متریک به نام خوانا
        type_name = metric_type.replace('_', ' ').title()
        keyboard.append([
            {"text": f"📊 {type_name}", "callback_data": f"admin_monitoring_metrics_type_{metric_type}"}
        ])

    if len(metric_types) > 10:
        keyboard.append([
            {"text": f"... و {len(metric_types) - 10} نوع دیگر", "callback_data": "admin_none"}
        ])

    keyboard.append([
        {"text": "🔙 بازگشت به متریک‌ها", "callback_data": "admin_monitoring_metrics"}
    ])

    return {"inline_keyboard": keyboard}


# ============================================================
# کیبوردهای بخش گزارش‌ها (Reports)
# ============================================================

def monitoring_reports_keyboard(
    has_reports: bool = False,
    reports_count: int = 0
) -> Dict[str, Any]:
    """
    کیبورد بخش مدیریت گزارش‌ها

    پارامترها:
        has_reports: آیا گزارشی وجود دارد
        reports_count: تعداد گزارش‌ها

    بازگشت: کیبورد با گزینه‌های گزارش‌ها
    """
    keyboard = []

    keyboard.append([
        {"text": "📝 تولید گزارش روزانه", "callback_data": "admin_monitoring_reports_generate_daily"},
        {"text": "📝 تولید گزارش هفتگی", "callback_data": "admin_monitoring_reports_generate_weekly"}
    ])

    keyboard.append([
        {"text": "📝 تولید گزارش ماهانه", "callback_data": "admin_monitoring_reports_generate_monthly"}
    ])

    if has_reports:
        keyboard.append([
            {"text": f"📋 مشاهده گزارش‌ها ({reports_count})", "callback_data": "admin_monitoring_reports_list"}
        ])

    keyboard.append([
        {"text": "🔙 بازگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring_main"},
        {"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_back"}
    ])

    return {"inline_keyboard": keyboard}


def monitoring_reports_list_keyboard(
    reports: List[Dict[str, Any]],
    page: int = 0,
    per_page: int = 5,
    total: int = 0
) -> Dict[str, Any]:
    """
    کیبورد لیست گزارش‌ها با صفحه‌بندی

    پارامترها:
        reports: لیست گزارش‌ها
        page: شماره صفحه
        per_page: تعداد آیتم در هر صفحه
        total: تعداد کل گزارش‌ها

    بازگشت: کیبورد با لیست گزارش‌ها
    """
    keyboard = []

    if not reports:
        keyboard.append([
            {"text": "❌ هیچ گزارشی یافت نشد", "callback_data": "admin_none"}
        ])
    else:
        for report in reports:
            report_id = report.get('id')
            report_type = report.get('report_type', 'نامشخص')
            created_at = report.get('created_at', 'نامشخص')[:16]
            status = report.get('status', 'pending')

            status_icon = "✅" if status == 'completed' else "⏳" if status == 'pending' else "❌"
            type_labels = {
                'daily': '📅 روزانه',
                'weekly': '📅 هفتگی',
                'monthly': '📅 ماهانه',
                'custom': '📅 سفارشی'
            }
            type_label = type_labels.get(report_type, report_type)

            keyboard.append([
                {"text": f"{status_icon} {type_label} - {created_at}",
                 "callback_data": f"admin_monitoring_reports_view_{report_id}"}
            ])
            keyboard.append([
                {"text": f"  🗑️ حذف", "callback_data": f"admin_monitoring_reports_delete_{report_id}"}
            ])

    # دکمه‌های صفحه‌بندی
    nav_row = []
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    if page > 0:
        nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_monitoring_reports_page_{page-1}"})
    if page < total_pages - 1:
        nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_monitoring_reports_page_{page+1}"})
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([
        {"text": "📝 تولید گزارش جدید", "callback_data": "admin_monitoring_reports_generate_daily"}
    ])

    keyboard.append([
        {"text": "🔙 بازگشت به گزارش‌ها", "callback_data": "admin_monitoring_reports"},
        {"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring_main"}
    ])

    return {"inline_keyboard": keyboard}


def monitoring_report_detail_keyboard(report_id: int) -> Dict[str, Any]:
    """
    کیبورد جزئیات یک گزارش

    پارامترها:
        report_id: شناسه گزارش

    بازگشت: کیبورد با گزینه‌های مدیریت گزارش
    """
    return {
        "inline_keyboard": [
            [{"text": "📥 دانلود گزارش", "callback_data": f"admin_monitoring_reports_download_{report_id}"}],
            [{"text": "🗑️ حذف گزارش", "callback_data": f"admin_monitoring_reports_delete_{report_id}"}],
            [{"text": "🔙 بازگشت به لیست گزارش‌ها", "callback_data": "admin_monitoring_reports_list"}],
            [{"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring_main"}]
        ]
    }


# ============================================================
# کیبوردهای کمکی
# ============================================================

def monitoring_confirm_keyboard(
    action: str,
    action_id: Optional[str] = None,
    confirm_text: str = "✅ تأیید",
    cancel_text: str = "❌ انصراف"
) -> Dict[str, Any]:
    """
    کیبورد تأیید برای عملیات‌های مهم

    پارامترها:
        action: نام عملیات
        action_id: شناسه اختیاری
        confirm_text: متن دکمه تأیید
        cancel_text: متن دکمه انصراف

    بازگشت: کیبورد تأیید
    """
    callback_confirm = f"admin_monitoring_{action}_confirm"
    callback_cancel = f"admin_monitoring_{action}_cancel"

    if action_id:
        callback_confirm = f"admin_monitoring_{action}_confirm_{action_id}"
        callback_cancel = f"admin_monitoring_{action}_cancel_{action_id}"

    return {
        "inline_keyboard": [
            [{"text": confirm_text, "callback_data": callback_confirm}],
            [{"text": cancel_text, "callback_data": callback_cancel}],
            [{"text": "🔙 انصراف", "callback_data": "admin_monitoring_main"}]
        ]
    }


def monitoring_empty_keyboard(message: str = "❌ اطلاعاتی یافت نشد") -> Dict[str, Any]:
    """
    کیبورد برای زمانی که اطلاعاتی وجود ندارد

    پارامترها:
        message: پیام نمایشی

    بازگشت: کیبورد خالی با دکمه بازگشت
    """
    return {
        "inline_keyboard": [
            [{"text": message, "callback_data": "admin_none"}],
            [{"text": "🔙 بازگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring_main"}],
            [{"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_back"}]
        ]
    }


def monitoring_back_keyboard(back_to: str = "admin_monitoring_main") -> Dict[str, Any]:
    """
    کیبورد ساده با دکمه بازگشت

    پارامترها:
        back_to: مقصد دکمه بازگشت

    بازگشت: کیبورد با دکمه بازگشت
    """
    return {
        "inline_keyboard": [
            [{"text": "🔙 بازگشت", "callback_data": back_to}],
            [{"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_back"}]
        ]
    }


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # کیبورد اصلی
    'monitoring_main_keyboard',
    
    # کیبوردهای سلامت
    'monitoring_health_keyboard',
    'monitoring_health_detail_keyboard',
    
    # کیبوردهای هشدارها
    'monitoring_alerts_keyboard',
    'monitoring_alert_detail_keyboard',
    
    # کیبوردهای متریک‌ها
    'monitoring_metrics_keyboard',
    'monitoring_metrics_type_keyboard',
    
    # کیبوردهای گزارش‌ها
    'monitoring_reports_keyboard',
    'monitoring_reports_list_keyboard',
    'monitoring_report_detail_keyboard',
    
    # کیبوردهای کمکی
    'monitoring_confirm_keyboard',
    'monitoring_empty_keyboard',
    'monitoring_back_keyboard',
]