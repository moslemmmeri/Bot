# admin_panel/monitoring/alerts.py
# سیستم هشدار و اعلان‌های خودکار برای شرایط بحرانی
# شامل: سطوح هشدار، تشخیص خودکار، حل کردن، تاریخچه و ارسال به OWNER

import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from logger_config import logger, ContextLogger
from core import send_message, OWNER_ID
from database import get_db_connection
from config import config
from utils.error_handler import log_callback_error, log_general_error, log_database_error


# ============================================================
# تعریف سطوح هشدار
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
    def label(self) -> str:
        labels = {
            AlertLevel.INFO: "اطلاعیه",
            AlertLevel.WARNING: "هشدار",
            AlertLevel.ERROR: "خطا",
            AlertLevel.CRITICAL: "بحرانی",
        }
        return labels.get(self, "نامشخص")


class Alert:
    """مدل هشدار"""
    
    def __init__(
        self,
        alert_id: Optional[int] = None,
        level: AlertLevel = AlertLevel.INFO,
        alert_type: str = "general",
        title: str = "",
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        is_resolved: bool = False,
        resolved_at: Optional[datetime] = None,
        resolved_by: Optional[int] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = alert_id
        self.level = level
        self.type = alert_type
        self.title = title
        self.message = message
        self.details = details or {}
        self.is_resolved = is_resolved
        self.resolved_at = resolved_at
        self.resolved_by = resolved_by
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'alert_level': self.level.value,
            'alert_type': self.type,
            'title': self.title,
            'message': self.message,
            'details': self.details,
            'is_resolved': 1 if self.is_resolved else 0,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        return cls(
            alert_id=data.get('id'),
            level=AlertLevel(data.get('alert_level', 'info')),
            alert_type=data.get('alert_type', 'general'),
            title=data.get('title', ''),
            message=data.get('message', ''),
            details=data.get('details', {}),
            is_resolved=bool(data.get('is_resolved', 0)),
            resolved_at=data.get('resolved_at'),
            resolved_by=data.get('resolved_by'),
            created_at=data.get('created_at'),
        )


# ============================================================
# توابع اصلی هشدارها (با استفاده از ریپازیتوری)
# ============================================================

def get_active_alerts(
    alert_level: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    دریافت هشدارهای فعال از دیتابیس

    پارامترها:
        alert_level: سطح هشدار (اختیاری)
        alert_type: نوع هشدار (اختیاری)
        limit: تعداد نتایج

    بازگشت: لیست هشدارهای فعال
    """
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.get_active_alerts(alert_level, alert_type, limit)
    except Exception as e:
        log_database_error(
            f"Error getting active alerts: {str(e)}",
            traceback=traceback.format_exc()
        )
        return []


def resolve_alert(alert_id: int, resolved_by: int) -> bool:
    """
    حل کردن یک هشدار در دیتابیس

    پارامترها:
        alert_id: شناسه هشدار
        resolved_by: شناسه کاربر حل‌کننده

    بازگشت: True در صورت موفقیت
    """
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.resolve_alert(alert_id, resolved_by)
    except Exception as e:
        log_database_error(
            f"Error resolving alert {alert_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


def get_alert_history(
    limit: int = 50,
    offset: int = 0,
    is_resolved: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    دریافت تاریخچه هشدارها از دیتابیس

    پارامترها:
        limit: تعداد نتایج
        offset: موقعیت شروع
        is_resolved: وضعیت حل شدن (اختیاری)

    بازگشت: لیست هشدارها
    """
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.get_all_alerts(
                is_resolved=is_resolved,
                limit=limit,
                offset=offset
            )
    except Exception as e:
        log_database_error(
            f"Error getting alert history: {str(e)}",
            traceback=traceback.format_exc()
        )
        return []


def get_alert_by_id(alert_id: int) -> Optional[Dict[str, Any]]:
    """
    دریافت یک هشدار بر اساس شناسه

    پارامترها:
        alert_id: شناسه هشدار

    بازگشت: دیکشنری هشدار یا None
    """
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.get_alert_by_id(alert_id)
    except Exception as e:
        log_database_error(
            f"Error getting alert by id {alert_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return None


def save_alert(alert: Alert) -> Optional[int]:
    """
    ذخیره هشدار در دیتابیس

    پارامترها:
        alert: آبجکت هشدار

    بازگشت: شناسه هشدار یا None
    """
    try:
        from repositories.monitoring_repository import MonitoringRepository
        
        with get_db_connection() as conn:
            repo = MonitoringRepository(conn)
            return repo.save_alert(
                alert_level=alert.level.value,
                alert_type=alert.type,
                title=alert.title,
                message=alert.message,
                details=alert.details
            )
    except Exception as e:
        log_database_error(
            f"Error saving alert to DB: {str(e)}",
            traceback=traceback.format_exc()
        )
        return None


# ============================================================
# تشخیص و ارسال هشدارها
# ============================================================

async def check_alerts() -> Dict[str, Any]:
    """
    بررسی شرایط و تشخیص هشدارهای جدید

    بازگشت: دیکشنری شامل نتایج بررسی
    """
    ctx_logger = ContextLogger("monitoring.alerts.check")
    results = {
        'alerts_found': 0,
        'alerts_sent': 0,
        'errors': []
    }

    try:
        # ========== ۱. بررسی تعداد خطاها ==========
        try:
            from database.db_logs import get_error_stats
            error_stats = get_error_stats()
            total_errors = error_stats.get('total', 0)
            unresolved_errors = error_stats.get('unresolved', 0)
            
            # اگر خطاهای حل‌نشده زیاد باشد
            threshold = config.MONITORING_ALERT_THRESHOLD
            if unresolved_errors > threshold:
                alert = Alert(
                    level=AlertLevel.WARNING,
                    alert_type="high_error_rate",
                    title="تعداد خطاهای حل‌نشده بالا",
                    message=f"{unresolved_errors} خطای حل‌نشده در سیستم وجود دارد.",
                    details={
                        'total_errors': total_errors,
                        'unresolved': unresolved_errors,
                        'threshold': threshold
                    }
                )
                alert_id = save_alert(alert)
                if alert_id:
                    results['alerts_found'] += 1
                    await send_alert_message(alert)
                    results['alerts_sent'] += 1
                    
        except Exception as e:
            results['errors'].append(f"Error checking error rate: {str(e)}")
            log_general_error(
                f"Error checking error rate: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        # ========== ۲. بررسی فضای دیسک ==========
        try:
            from admin_panel.monitoring.health import check_disk_usage
            disk = check_disk_usage()
            
            if disk.get('status') == 'warning':
                alert = Alert(
                    level=AlertLevel.WARNING,
                    alert_type="low_disk_space",
                    title="فضای دیسک در حال اتمام",
                    message=disk.get('message', ''),
                    details=disk.get('details', {})
                )
                alert_id = save_alert(alert)
                if alert_id:
                    results['alerts_found'] += 1
                    await send_alert_message(alert)
                    results['alerts_sent'] += 1
                    
            elif disk.get('status') == 'error':
                alert = Alert(
                    level=AlertLevel.CRITICAL,
                    alert_type="critical_disk_space",
                    title="فضای دیسک بسیار کم است",
                    message=disk.get('message', ''),
                    details=disk.get('details', {})
                )
                alert_id = save_alert(alert)
                if alert_id:
                    results['alerts_found'] += 1
                    await send_alert_message(alert)
                    results['alerts_sent'] += 1
                    
        except Exception as e:
            results['errors'].append(f"Error checking disk space: {str(e)}")
            log_general_error(
                f"Error checking disk space: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        # ========== ۳. بررسی قطعی دیتابیس ==========
        try:
            from admin_panel.monitoring.health import check_db_health
            import asyncio
            db_result = await check_db_health()
            
            if db_result.get('status') == 'error':
                alert = Alert(
                    level=AlertLevel.CRITICAL,
                    alert_type="database_connection_failed",
                    title="اتصال به دیتابیس قطع شده است",
                    message=db_result.get('message', ''),
                    details=db_result.get('details', {})
                )
                alert_id = save_alert(alert)
                if alert_id:
                    results['alerts_found'] += 1
                    await send_alert_message(alert)
                    results['alerts_sent'] += 1
                    
        except Exception as e:
            results['errors'].append(f"Error checking database: {str(e)}")
            log_general_error(
                f"Error checking database: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        # ========== ۴. بررسی قطعی Redis ==========
        try:
            from admin_panel.monitoring.health import check_redis_health
            import asyncio
            redis_result = await check_redis_health()
            
            if redis_result.get('status') == 'error' and config.REDIS_ENABLED:
                alert = Alert(
                    level=AlertLevel.WARNING,
                    alert_type="redis_connection_failed",
                    title="اتصال به Redis قطع شده است",
                    message=redis_result.get('message', ''),
                    details=redis_result.get('details', {})
                )
                alert_id = save_alert(alert)
                if alert_id:
                    results['alerts_found'] += 1
                    await send_alert_message(alert)
                    results['alerts_sent'] += 1
                    
        except Exception as e:
            results['errors'].append(f"Error checking Redis: {str(e)}")
            log_general_error(
                f"Error checking Redis: {str(e)}",
                traceback=traceback.format_exc(),
                context_logger=ctx_logger
            )

        logger.info(
            f"✅ Alert check completed: "
            f"found={results['alerts_found']}, "
            f"sent={results['alerts_sent']}, "
            f"errors={len(results['errors'])}"
        )

        return results

    except Exception as e:
        log_callback_error(
            f"Error in check_alerts: {str(e)}",
            traceback=traceback.format_exc(),
            context_logger=ctx_logger
        )
        results['errors'].append(str(e))
        return results


async def send_alert_message(alert: Alert) -> bool:
    """
    ارسال پیام هشدار به OWNER

    پارامترها:
        alert: آبجکت هشدار

    بازگشت: True در صورت موفقیت
    """
    try:
        msg = f"{alert.level.icon} **هشدار: {alert.title}**\n\n"
        msg += f"📌 **سطح:** {alert.level.label}\n"
        msg += f"📌 **نوع:** {alert.type}\n"
        msg += f"📝 **پیام:** {alert.message}\n"
        msg += f"🕐 **زمان:** {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if alert.details:
            msg += f"\n📊 **جزئیات:**\n"
            for key, value in alert.details.items():
                if value is not None and value != "":
                    msg += f"  • {key}: {value}\n"
        
        await send_message(OWNER_ID, msg)
        logger.info(f"📨 Alert sent to OWNER: {alert.title}")
        return True
        
    except Exception as e:
        log_general_error(
            f"Error sending alert message: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


# ============================================================
# توابع مدیریت هشدارها (برای پنل)
# ============================================================

async def handle_alerts(chat_id: int, user_id: int) -> bool:
    """
    نمایش صفحه مدیریت هشدارها

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        from keyboards.kb_monitoring import monitoring_alerts_keyboard
        
        active_alerts = get_active_alerts()
        has_active = len(active_alerts) > 0
        
        keyboard = monitoring_alerts_keyboard(
            has_active_alerts=has_active,
            has_history=True
        )
        
        msg = f"🚨 **مدیریت هشدارها**\n\n"
        
        if active_alerts:
            msg += f"📌 **هشدارهای فعال ({len(active_alerts)}):**\n\n"
            for alert in active_alerts[:10]:
                level = alert.get('alert_level', 'info')
                level_icon = AlertLevel(level).icon if level in ['info', 'warning', 'error', 'critical'] else "ℹ️"
                title = alert.get('title', 'بدون عنوان')
                created_at = alert.get('created_at', '')[:16]
                msg += f"  {level_icon} {title} - {created_at}\n"
            if len(active_alerts) > 10:
                msg += f"  ... و {len(active_alerts) - 10} هشدار دیگر\n"
        else:
            msg += "✅ هیچ هشدار فعالی وجود ندارد.\n"
        
        msg += f"\nبرای حل کردن یک هشدار، روی آن کلیک کنید."
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_alerts: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش هشدارها.")
        return True


async def handle_alert_resolve(chat_id: int, user_id: int, alert_id: int) -> bool:
    """
    حل کردن یک هشدار

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر
        alert_id: شناسه هشدار

    بازگشت: True در صورت موفقیت
    """
    try:
        success = resolve_alert(alert_id, user_id)
        
        if success:
            await send_message(chat_id, f"✅ هشدار #{alert_id} با موفقیت حل شد.")
        else:
            await send_message(chat_id, f"❌ خطا در حل کردن هشدار #{alert_id}.")
        
        return await handle_alerts(chat_id, user_id)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_alert_resolve: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حل کردن هشدار.")
        return True


async def handle_alert_history(chat_id: int, user_id: int) -> bool:
    """
    نمایش تاریخچه هشدارها

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        history = get_alert_history(limit=50)
        
        if not history:
            await send_message(
                chat_id,
                "📋 **تاریخچه هشدارها**\n\n✅ هیچ هشداری در تاریخچه وجود ندارد."
            )
            return True
        
        msg = f"📋 **تاریخچه هشدارها ({len(history)})**\n\n"
        
        for alert in history[:20]:
            level = alert.get('alert_level', 'info')
            level_icon = AlertLevel(level).icon if level in ['info', 'warning', 'error', 'critical'] else "ℹ️"
            title = alert.get('title', 'بدون عنوان')
            created_at = alert.get('created_at', '')[:16]
            is_resolved = alert.get('is_resolved', 0)
            status_icon = "✅" if is_resolved else "⏳"
            
            msg += f"{status_icon} {level_icon} {title} - {created_at}\n"
        
        if len(history) > 20:
            msg += f"\n... و {len(history) - 20} هشدار دیگر"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 بازگشت به هشدارها", "callback_data": "admin_monitoring_alerts"}]
            ]
        }
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_alert_history: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش تاریخچه هشدارها.")
        return True


async def handle_alert_check_now(chat_id: int, user_id: int) -> bool:
    """
    بررسی و ارسال هشدارهای جدید (دستی)

    پارامترها:
        chat_id: شناسه چت
        user_id: شناسه کاربر

    بازگشت: True در صورت موفقیت
    """
    try:
        await send_message(chat_id, "🔄 در حال بررسی هشدارها... لطفاً صبر کنید.")
        
        results = await check_alerts()
        
        msg = f"✅ **بررسی هشدارها انجام شد**\n\n"
        msg += f"📊 هشدارهای جدید: {results['alerts_found']}\n"
        msg += f"📨 ارسال‌شده: {results['alerts_sent']}\n"
        
        if results['errors']:
            msg += f"\n⚠️ خطاها:\n"
            for error in results['errors'][:5]:
                msg += f"  • {error}\n"
        
        await send_message(chat_id, msg)
        return await handle_alerts(chat_id, user_id)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_alert_check_now: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در بررسی هشدارها.")
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'AlertLevel',
    'Alert',
    'get_active_alerts',
    'resolve_alert',
    'get_alert_history',
    'get_alert_by_id',
    'save_alert',
    'check_alerts',
    'send_alert_message',
    'handle_alerts',
    'handle_alert_resolve',
    'handle_alert_history',
    'handle_alert_check_now',
]