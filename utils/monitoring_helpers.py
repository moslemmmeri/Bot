# utils/monitoring_helpers.py
# توابع کمکی برای بخش مانیتورینگ
# شامل: فرمت‌بندی داده‌ها، محاسبات آماری، تبدیل انواع داده و ...

import re
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum


# ============================================================
# کلاس‌های کمکی
# ============================================================

class AlertLevel(str, Enum):
    """سطوح هشدار"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def icon(self) -> str:
        icons = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨",
        }
        return icons.get(self, "ℹ️")

    @property
    def color(self) -> str:
        colors = {
            AlertLevel.INFO: "#3498DB",    # آبی
            AlertLevel.WARNING: "#F39C12", # نارنجی
            AlertLevel.ERROR: "#E74C3C",   # قرمز
            AlertLevel.CRITICAL: "#C0392B", # قرمز تیره
        }
        return colors.get(self, "#3498DB")

    @property
    def label(self) -> str:
        labels = {
            AlertLevel.INFO: "اطلاعیه",
            AlertLevel.WARNING: "هشدار",
            AlertLevel.ERROR: "خطا",
            AlertLevel.CRITICAL: "بحرانی",
        }
        return labels.get(self, "نامشخص")


class MetricType(str, Enum):
    """انواع متریک‌ها"""
    # متریک‌های عملکردی
    API_LATENCY = "api_latency"
    DB_QUERY_TIME = "db_query_time"
    REQUEST_TIME = "request_time"
    
    # متریک‌های سیستمی
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    
    # متریک‌های کاربران
    ACTIVE_USERS = "active_users"
    TOTAL_USERS = "total_users"
    NEW_USERS = "new_users"
    
    # متریک‌های سفارشات
    ORDERS_COUNT = "orders_count"
    REVENUE = "revenue"
    CONVERSION_RATE = "conversion_rate"
    
    # متریک‌های خطاها
    ERROR_COUNT = "error_count"
    ERROR_RATE = "error_rate"
    
    # متریک‌های درخواست‌ها
    REQUESTS_PER_MINUTE = "requests_per_minute"
    TOTAL_REQUESTS = "total_requests"
    
    # متریک‌های دکمه‌ها
    BUTTON_CLICKS = "button_clicks"
    BUTTON_CONVERSION = "button_conversion"

    @property
    def label(self) -> str:
        labels = {
            MetricType.API_LATENCY: "تأخیر API",
            MetricType.DB_QUERY_TIME: "زمان کوئری دیتابیس",
            MetricType.REQUEST_TIME: "زمان درخواست",
            MetricType.CPU_USAGE: "مصرف CPU",
            MetricType.MEMORY_USAGE: "مصرف حافظه",
            MetricType.DISK_USAGE: "مصرف دیسک",
            MetricType.ACTIVE_USERS: "کاربران فعال",
            MetricType.TOTAL_USERS: "کل کاربران",
            MetricType.NEW_USERS: "کاربران جدید",
            MetricType.ORDERS_COUNT: "تعداد سفارشات",
            MetricType.REVENUE: "درآمد",
            MetricType.CONVERSION_RATE: "نرخ تبدیل",
            MetricType.ERROR_COUNT: "تعداد خطاها",
            MetricType.ERROR_RATE: "نرخ خطا",
            MetricType.REQUESTS_PER_MINUTE: "درخواست در دقیقه",
            MetricType.TOTAL_REQUESTS: "کل درخواست‌ها",
            MetricType.BUTTON_CLICKS: "کلیک دکمه‌ها",
            MetricType.BUTTON_CONVERSION: "نرخ تبدیل دکمه‌ها",
        }
        return labels.get(self, self.value.replace('_', ' ').title())

    @property
    def icon(self) -> str:
        icons = {
            MetricType.API_LATENCY: "🌐",
            MetricType.DB_QUERY_TIME: "🗄️",
            MetricType.REQUEST_TIME: "⏱️",
            MetricType.CPU_USAGE: "🖥️",
            MetricType.MEMORY_USAGE: "💾",
            MetricType.DISK_USAGE: "💿",
            MetricType.ACTIVE_USERS: "👥",
            MetricType.TOTAL_USERS: "👤",
            MetricType.NEW_USERS: "🆕",
            MetricType.ORDERS_COUNT: "📦",
            MetricType.REVENUE: "💰",
            MetricType.CONVERSION_RATE: "📈",
            MetricType.ERROR_COUNT: "🚨",
            MetricType.ERROR_RATE: "📊",
            MetricType.REQUESTS_PER_MINUTE: "📨",
            MetricType.TOTAL_REQUESTS: "📋",
            MetricType.BUTTON_CLICKS: "🖱️",
            MetricType.BUTTON_CONVERSION: "🎯",
        }
        return icons.get(self, "📊")


class ReportType(str, Enum):
    """انواع گزارش‌ها"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

    @property
    def label(self) -> str:
        labels = {
            ReportType.DAILY: "روزانه",
            ReportType.WEEKLY: "هفتگی",
            ReportType.MONTHLY: "ماهانه",
            ReportType.CUSTOM: "سفارشی",
        }
        return labels.get(self, self.value)

    @property
    def icon(self) -> str:
        icons = {
            ReportType.DAILY: "📅",
            ReportType.WEEKLY: "📆",
            ReportType.MONTHLY: "📊",
            ReportType.CUSTOM: "📋",
        }
        return icons.get(self, "📄")


# ============================================================
# توابع فرمت‌بندی
# ============================================================

def format_metric_value(value: Any, metric_type: Optional[str] = None) -> str:
    """
    فرمت‌بندی مقدار متریک بر اساس نوع آن

    پارامترها:
        value: مقدار متریک
        metric_type: نوع متریک (اختیاری - برای فرمت‌بندی اختصاصی)

    بازگشت: رشته فرمت‌شده
    """
    if value is None:
        return "نامشخص"
    
    # اگر مقدار دیکشنری است، آن را به JSON تبدیل کن
    if isinstance(value, dict):
        try:
            return json.dumps(value, ensure_ascii=False)
        except:
            return str(value)
    
    # اگر مقدار لیست است، تعداد آیتم‌ها را نمایش بده
    if isinstance(value, list):
        return f"{len(value)} آیتم"
    
    # اگر عدد است، با کاما فرمت بده
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            return f"{int(value):,}"
        elif isinstance(value, float):
            return f"{value:,.2f}"
        else:
            return f"{value:,}"
    
    # اگر boolean است
    if isinstance(value, bool):
        return "✅" if value else "❌"
    
    # اگر رشته است
    if isinstance(value, str):
        if len(value) > 100:
            return value[:100] + "..."
        return value
    
    return str(value)


def format_alert_level(level: str) -> str:
    """
    فرمت‌بندی سطح هشدار با آیکون

    پارامترها:
        level: سطح هشدار

    بازگشت: رشته با آیکون
    """
    try:
        alert_level = AlertLevel(level)
        return f"{alert_level.icon} {alert_level.label}"
    except ValueError:
        return f"❓ {level}"


def format_alert_message(alert: Dict[str, Any]) -> str:
    """
    فرمت‌بندی پیام هشدار برای نمایش

    پارامترها:
        alert: دیکشنری هشدار

    بازگشت: رشته فرمت‌شده
    """
    alert_id = alert.get('id', '?')
    level = alert.get('alert_level', 'unknown')
    title = alert.get('title', 'بدون عنوان')
    message = alert.get('message', '')
    created_at = alert.get('created_at', '')
    is_resolved = alert.get('is_resolved', 0)
    
    status_icon = "✅" if is_resolved else "🔴"
    level_icon = AlertLevel(level).icon if level in ['info', 'warning', 'error', 'critical'] else "❓"
    
    lines = [
        f"{status_icon} #{alert_id} - {level_icon} {title}",
        f"   📝 {message[:100]}{'...' if len(message) > 100 else ''}",
        f"   🕐 {format_datetime(created_at)}",
    ]
    
    if is_resolved:
        resolved_at = alert.get('resolved_at')
        resolved_by = alert.get('resolved_by')
        if resolved_at:
            lines.append(f"   ✅ حل شده در {format_datetime(resolved_at)}")
        if resolved_by:
            lines.append(f"   👤 توسط: {resolved_by}")
    
    return "\n".join(lines)


def format_report_summary(report: Dict[str, Any]) -> str:
    """
    فرمت‌بندی خلاصه یک گزارش

    پارامترها:
        report: دیکشنری گزارش

    بازگشت: رشته فرمت‌شده
    """
    report_id = report.get('id', '?')
    report_type = report.get('report_type', 'unknown')
    title = report.get('title', 'بدون عنوان')
    status = report.get('status', 'pending')
    created_at = report.get('created_at', '')
    created_by = report.get('created_by', 'نامشخص')
    
    status_icons = {
        'pending': '⏳',
        'completed': '✅',
        'failed': '❌',
    }
    status_icon = status_icons.get(status, '❓')
    
    type_label = ReportType(report_type).label if report_type in ['daily', 'weekly', 'monthly', 'custom'] else report_type
    type_icon = ReportType(report_type).icon if report_type in ['daily', 'weekly', 'monthly', 'custom'] else "📄"
    
    lines = [
        f"{type_icon} #{report_id} - {title}",
        f"   📌 نوع: {type_label}",
        f"   📌 وضعیت: {status_icon} {status}",
        f"   🕐 ایجاد: {format_datetime(created_at)}",
        f"   👤 ایجادکننده: {created_by}",
    ]
    
    return "\n".join(lines)


# ============================================================
# توابع تاریخ و زمان
# ============================================================

def format_datetime(dt: Union[str, datetime, None]) -> str:
    """فرمت‌بندی تاریخ و زمان"""
    if not dt:
        return "نامشخص"
    
    if isinstance(dt, str):
        try:
            if 'T' in dt:
                dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return dt_obj.strftime("%Y-%m-%d %H:%M")
            elif ' ' in dt:
                return dt[:16]
            else:
                return dt
        except:
            return dt[:16] if len(dt) > 16 else dt
    
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    
    return str(dt)


def format_date(dt: Union[str, datetime, None]) -> str:
    """فرمت‌بندی تاریخ (بدون زمان)"""
    if not dt:
        return "نامشخص"
    
    if isinstance(dt, str):
        try:
            if 'T' in dt:
                dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return dt_obj.strftime("%Y-%m-%d")
            elif ' ' in dt:
                return dt[:10]
            else:
                return dt[:10]
        except:
            return dt[:10] if len(dt) >= 10 else dt
    
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    
    return str(dt)


def format_time(dt: Union[str, datetime, None]) -> str:
    """فرمت‌بندی زمان (بدون تاریخ)"""
    if not dt:
        return "نامشخص"
    
    if isinstance(dt, str):
        try:
            if 'T' in dt:
                dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return dt_obj.strftime("%H:%M")
            elif ' ' in dt and len(dt) >= 16:
                return dt[11:16]
            else:
                return dt[:5] if len(dt) >= 5 else dt
        except:
            return dt[:5] if len(dt) >= 5 else dt
    
    if isinstance(dt, datetime):
        return dt.strftime("%H:%M")
    
    return str(dt)


def format_duration(seconds: int) -> str:
    """فرمت‌بندی مدت زمان"""
    if seconds < 60:
        return f"{seconds} ثانیه"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} دقیقه"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ساعت {minutes} دقیقه"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days} روز {hours} ساعت"


def human_readable_time(timestamp: Union[int, float, datetime]) -> str:
    """زمان به صورت نسبی (مثلاً ۵ دقیقه پیش)"""
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        return format_datetime(timestamp)
    
    now = datetime.now()
    diff = now - dt
    
    if diff.total_seconds() < 60:
        return "چند لحظه پیش"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() // 60)
        return f"{minutes} دقیقه پیش"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() // 3600)
        return f"{hours} ساعت پیش"
    elif diff.total_seconds() < 604800:
        days = int(diff.total_seconds() // 86400)
        return f"{days} روز پیش"
    elif diff.total_seconds() < 2592000:
        weeks = int(diff.total_seconds() // 604800)
        return f"{weeks} هفته پیش"
    elif diff.total_seconds() < 31536000:
        months = int(diff.total_seconds() // 2592000)
        return f"{months} ماه پیش"
    else:
        years = int(diff.total_seconds() // 31536000)
        return f"{years} سال پیش"


# ============================================================
# توابع محاسبات آماری
# ============================================================

def calculate_average(values: List[Union[int, float]]) -> float:
    """محاسبه میانگین"""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_percentage(part: Union[int, float], total: Union[int, float]) -> float:
    """محاسبه درصد"""
    if total == 0:
        return 0.0
    return (part / total) * 100


def calculate_growth(current: Union[int, float], previous: Union[int, float]) -> float:
    """محاسبه نرخ رشد"""
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def calculate_min_max(values: List[Union[int, float]]) -> Dict[str, Union[int, float]]:
    """محاسبه حداقل و حداکثر"""
    if not values:
        return {'min': 0, 'max': 0}
    return {'min': min(values), 'max': max(values)}


def calculate_stats(values: List[Union[int, float]]) -> Dict[str, float]:
    """محاسبه آمار کامل"""
    if not values:
        return {
            'count': 0,
            'sum': 0.0,
            'avg': 0.0,
            'min': 0.0,
            'max': 0.0,
            'median': 0.0,
        }
    
    sorted_values = sorted(values)
    count = len(values)
    
    return {
        'count': count,
        'sum': sum(values),
        'avg': sum(values) / count,
        'min': min(values),
        'max': max(values),
        'median': sorted_values[count // 2] if count % 2 == 1 else (sorted_values[count//2 - 1] + sorted_values[count//2]) / 2,
    }


# ============================================================
# توابع کمکی برای پردازش داده‌ها
# ============================================================

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """تبدیل ایمن JSON به دیکشنری"""
    if not json_str:
        return default
    try:
        return json.loads(json_str)
    except:
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """تبدیل ایمن دیکشنری به JSON"""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except:
        return default


def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """تبدیل دیکشنری تو در تو به دیکشنری تخت"""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def group_by_key(data: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
    """گروه‌بندی لیست دیکشنری‌ها بر اساس یک کلید"""
    result = {}
    for item in data:
        group_key = item.get(key)
        if group_key is None:
            group_key = 'unknown'
        if group_key not in result:
            result[group_key] = []
        result[group_key].append(item)
    return result


def filter_metrics_by_time(
    metrics: List[Dict[str, Any]],
    hours: int = 24
) -> List[Dict[str, Any]]:
    """
    فیلتر متریک‌ها بر اساس ساعت‌های اخیر

    پارامترها:
        metrics: لیست متریک‌ها
        hours: تعداد ساعت‌های اخیر

    بازگشت: لیست متریک‌های فیلترشده
    """
    if not metrics:
        return []
    
    cutoff = datetime.now() - timedelta(hours=hours)
    filtered = []
    
    for metric in metrics:
        timestamp = metric.get('timestamp')
        if not timestamp:
            continue
        
        try:
            if isinstance(timestamp, str):
                if 'T' in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                elif ' ' in timestamp:
                    dt = datetime.strptime(timestamp[:19], "%Y-%m-%d %H:%M:%S")
                else:
                    dt = datetime.strptime(timestamp[:10], "%Y-%m-%d")
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                continue
        except:
            continue
        
        if dt >= cutoff:
            filtered.append(metric)
    
    return filtered


def get_metric_trend(
    metrics: List[Dict[str, Any]],
    metric_type: str
) -> Dict[str, Any]:
    """
    دریافت روند یک متریک خاص

    پارامترها:
        metrics: لیست متریک‌ها
        metric_type: نوع متریک

    بازگشت: دیکشنری شامل روند
    """
    filtered = [m for m in metrics if m.get('metric_type') == metric_type]
    
    if not filtered:
        return {
            'type': metric_type,
            'count': 0,
            'trend': 'unknown',
            'current': None,
            'previous': None,
            'change': 0,
            'change_percent': 0,
        }
    
    # مرتب‌سازی بر اساس زمان
    sorted_metrics = sorted(filtered, key=lambda x: x.get('timestamp', ''))
    
    current = sorted_metrics[-1]
    previous = sorted_metrics[-2] if len(sorted_metrics) > 1 else None
    
    current_value = current.get('value', 0)
    previous_value = previous.get('value', 0) if previous else 0
    
    change = current_value - previous_value
    change_percent = ((change / previous_value) * 100) if previous_value != 0 else 0
    
    # تعیین روند
    if change > 0:
        trend = 'up'
    elif change < 0:
        trend = 'down'
    else:
        trend = 'stable'
    
    return {
        'type': metric_type,
        'count': len(sorted_metrics),
        'trend': trend,
        'current': current_value,
        'previous': previous_value,
        'change': change,
        'change_percent': change_percent,
    }


# ============================================================
# توابع کمکی برای تولید گزارش
# ============================================================

def generate_report_title(report_type: str) -> str:
    """
    تولید عنوان گزارش بر اساس نوع

    پارامترها:
        report_type: نوع گزارش

    بازگشت: عنوان گزارش
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    titles = {
        'daily': f"گزارش روزانه - {date_str}",
        'weekly': f"گزارش هفتگی - هفته {now.isocalendar()[1]} ({date_str})",
        'monthly': f"گزارش ماهانه - {now.strftime('%B %Y')}",
        'custom': f"گزارش سفارشی - {date_str}",
    }
    return titles.get(report_type, f"گزارش - {date_str}")


def generate_report_content(
    report_type: str,
    stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    تولید محتوای گزارش بر اساس نوع

    پارامترها:
        report_type: نوع گزارش
        stats: آمار و داده‌ها

    بازگشت: محتوای گزارش (دیکشنری)
    """
    now = datetime.now()
    
    content = {
        'generated_at': now.isoformat(),
        'report_type': report_type,
        'date_range': {},
        'summary': {},
        'details': {},
        'charts': {},
    }
    
    # بازه زمانی
    if report_type == 'daily':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        content['date_range'] = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
        }
        content['summary'] = _generate_daily_summary(stats)
        content['details'] = _generate_daily_details(stats)
    
    elif report_type == 'weekly':
        start_date = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        content['date_range'] = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
        }
        content['summary'] = _generate_weekly_summary(stats)
        content['details'] = _generate_weekly_details(stats)
    
    elif report_type == 'monthly':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        content['date_range'] = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
        }
        content['summary'] = _generate_monthly_summary(stats)
        content['details'] = _generate_monthly_details(stats)
    
    else:
        content['summary'] = stats.get('summary', {})
        content['details'] = stats.get('details', {})
    
    return content


def _generate_daily_summary(stats: Dict[str, Any]) -> Dict[str, Any]:
    """تولید خلاصه گزارش روزانه"""
    return {
        'total_orders': stats.get('orders', {}).get('total', 0),
        'total_revenue': stats.get('orders', {}).get('revenue', 0),
        'new_users': stats.get('users', {}).get('new', 0),
        'active_users': stats.get('users', {}).get('active', 0),
        'errors_count': stats.get('errors', {}).get('total', 0),
        'system_status': 'healthy' if stats.get('health', {}).get('overall') == 'ok' else 'warning',
    }


def _generate_daily_details(stats: Dict[str, Any]) -> Dict[str, Any]:
    """تولید جزئیات گزارش روزانه"""
    return {
        'orders_by_status': stats.get('orders', {}).get('by_status', {}),
        'top_services': stats.get('buttons', {}).get('top_5', []),
        'error_breakdown': stats.get('errors', {}).get('by_type', []),
        'system_metrics': stats.get('system', {}),
    }


def _generate_weekly_summary(stats: Dict[str, Any]) -> Dict[str, Any]:
    """تولید خلاصه گزارش هفتگی"""
    return {
        'total_orders': stats.get('orders', {}).get('total', 0),
        'total_revenue': stats.get('orders', {}).get('revenue', 0),
        'new_users': stats.get('users', {}).get('new', 0),
        'active_users_avg': stats.get('users', {}).get('active_avg', 0),
        'errors_count': stats.get('errors', {}).get('total', 0),
        'avg_response_time': stats.get('performance', {}).get('avg_response', 0),
        'system_uptime': stats.get('system', {}).get('uptime', 0),
    }


def _generate_weekly_details(stats: Dict[str, Any]) -> Dict[str, Any]:
    """تولید جزئیات گزارش هفتگی"""
    return {
        'daily_breakdown': stats.get('daily_stats', []),
        'top_services': stats.get('buttons', {}).get('top_10', []),
        'error_trend': stats.get('errors', {}).get('trend', []),
        'user_growth': stats.get('users', {}).get('growth', 0),
        'conversion_rate': stats.get('orders', {}).get('conversion_rate', 0),
    }


def _generate_monthly_summary(stats: Dict[str, Any]) -> Dict[str, Any]:
    """تولید خلاصه گزارش ماهانه"""
    return {
        'total_orders': stats.get('orders', {}).get('total', 0),
        'total_revenue': stats.get('orders', {}).get('revenue', 0),
        'new_users': stats.get('users', {}).get('new', 0),
        'active_users_avg': stats.get('users', {}).get('active_avg', 0),
        'errors_count': stats.get('errors', {}).get('total', 0),
        'avg_response_time': stats.get('performance', {}).get('avg_response', 0),
        'system_uptime': stats.get('system', {}).get('uptime', 0),
        'growth_rate': stats.get('growth', {}).get('rate', 0),
        'total_requests': stats.get('requests', {}).get('total', 0),
    }


def _generate_monthly_details(stats: Dict[str, Any]) -> Dict[str, Any]:
    """تولید جزئیات گزارش ماهانه"""
    return {
        'weekly_breakdown': stats.get('weekly_stats', []),
        'top_services': stats.get('buttons', {}).get('top_10', []),
        'error_trend': stats.get('errors', {}).get('trend', []),
        'user_growth': stats.get('users', {}).get('growth', 0),
        'conversion_rate': stats.get('orders', {}).get('conversion_rate', 0),
        'revenue_trend': stats.get('revenue_trend', []),
        'system_performance': stats.get('performance', {}),
    }


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # کلاس‌های Enum
    'AlertLevel',
    'MetricType',
    'ReportType',
    
    # توابع فرمت‌بندی
    'format_metric_value',
    'format_alert_level',
    'format_alert_message',
    'format_report_summary',
    'format_datetime',
    'format_date',
    'format_time',
    'format_duration',
    'human_readable_time',
    
    # توابع آماری
    'calculate_average',
    'calculate_percentage',
    'calculate_growth',
    'calculate_min_max',
    'calculate_stats',
    
    # توابع پردازش داده
    'safe_json_loads',
    'safe_json_dumps',
    'flatten_dict',
    'group_by_key',
    'filter_metrics_by_time',
    'get_metric_trend',
    
    # توابع تولید گزارش
    'generate_report_title',
    'generate_report_content',
]