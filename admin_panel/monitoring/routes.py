# admin_panel/monitoring/routes.py
# ثبت روت‌های مربوط به مانیتورینگ در پنل مدیریت
# شامل: داشبورد مانیتورینگ، بررسی سلامت، مدیریت هشدارها، متریک‌ها، گزارش‌ها و مستندات

import asyncio
import subprocess
import functools  # <-- اضافه شده برای استفاده از partial
from pathlib import Path

from ..router import route, extract_params
from .dashboard import handle_monitoring
from .health import handle_health_check
from .alerts import (
    handle_alerts,
    handle_alert_resolve,
    handle_alert_history,
    handle_alert_check_now,
)
from .metrics import (
    handle_metrics,
    handle_metrics_collect,
    handle_metrics_summary,
    handle_metrics_cleanup,
)
from .reports import (
    handle_reports,
    handle_report_generate,
    handle_report_view,
    handle_report_delete,
)
from core import send_message
from logger_config import logger
from config import config
from database import is_admin


OWNER_ID = config.OWNER_ID


# ============================================================
# روت‌های اصلی مانیتورینگ
# ============================================================

@route("admin_monitoring")
async def admin_monitoring(update):
    """
    نمایش داشبورد اصلی مانیتورینگ
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_monitoring(chat_id, user_id)


@route("admin_monitoring_health")
async def admin_monitoring_health(update):
    """
    نمایش صفحه بررسی سلامت سرویس‌ها
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_health_check(chat_id, user_id)


@route("admin_monitoring_alerts")
async def admin_monitoring_alerts(update):
    """
    نمایش صفحه مدیریت هشدارها
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_alerts(chat_id, user_id)


@route("admin_monitoring_alerts_resolve_")
async def admin_monitoring_alerts_resolve(update):
    """
    حل کردن یک هشدار (admin_monitoring_alerts_resolve_<alert_id>)
    """
    chat_id, user_id, data = extract_params(update)
    try:
        alert_id = int(data.split("_")[-1])
        return await handle_alert_resolve(chat_id, user_id, alert_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه هشدار نامعتبر.")
        return True


@route("admin_monitoring_alerts_history")
async def admin_monitoring_alerts_history(update):
    """
    نمایش تاریخچه هشدارها
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_alert_history(chat_id, user_id)


@route("admin_monitoring_alerts_check")
async def admin_monitoring_alerts_check(update):
    """
    بررسی و ارسال هشدارهای جدید
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_alert_check_now(chat_id, user_id)


@route("admin_monitoring_metrics")
async def admin_monitoring_metrics(update):
    """
    نمایش صفحه مدیریت متریک‌ها
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_metrics(chat_id, user_id)


@route("admin_monitoring_metrics_collect")
async def admin_monitoring_metrics_collect(update):
    """
    جمع‌آوری متریک‌های جدید
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_metrics_collect(chat_id, user_id)


@route("admin_monitoring_metrics_summary")
async def admin_monitoring_metrics_summary(update):
    """
    نمایش خلاصه متریک‌ها
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_metrics_summary(chat_id, user_id)


@route("admin_monitoring_metrics_cleanup")
async def admin_monitoring_metrics_cleanup(update):
    """
    پاکسازی متریک‌های قدیمی
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_metrics_cleanup(chat_id, user_id)


@route("admin_monitoring_reports")
async def admin_monitoring_reports(update):
    """
    نمایش صفحه مدیریت گزارش‌ها
    """
    chat_id, user_id, data = extract_params(update)
    return await handle_reports(chat_id, user_id)


@route("admin_monitoring_reports_generate_")
async def admin_monitoring_reports_generate(update):
    """
    تولید گزارش جدید (admin_monitoring_reports_generate_<type>)
    که type می‌تواند daily, weekly, monthly باشد
    """
    chat_id, user_id, data = extract_params(update)
    try:
        report_type = data.split("_")[-1]
        if report_type not in ['daily', 'weekly', 'monthly']:
            await send_message(chat_id, "❌ نوع گزارش نامعتبر. گزینه‌ها: daily, weekly, monthly")
            return True
        return await handle_report_generate(chat_id, user_id, report_type)
    except Exception as e:
        await send_message(chat_id, f"❌ خطا در تولید گزارش: {str(e)}")
        return True


@route("admin_monitoring_reports_view_")
async def admin_monitoring_reports_view(update):
    """
    مشاهده یک گزارش (admin_monitoring_reports_view_<report_id>)
    """
    chat_id, user_id, data = extract_params(update)
    try:
        report_id = int(data.split("_")[-1])
        return await handle_report_view(chat_id, user_id, report_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه گزارش نامعتبر.")
        return True


@route("admin_monitoring_reports_delete_")
async def admin_monitoring_reports_delete(update):
    """
    حذف یک گزارش (admin_monitoring_reports_delete_<report_id>)
    """
    chat_id, user_id, data = extract_params(update)
    try:
        report_id = int(data.split("_")[-1])
        return await handle_report_delete(chat_id, user_id, report_id)
    except ValueError:
        await send_message(chat_id, "❌ شناسه گزارش نامعتبر.")
        return True


# ============================================================
# روت‌های مستندات (جدید)
# ============================================================

@route("admin_docs")
async def admin_docs(update):
    """
    نمایش اطلاعات مستندات و لینک دسترسی
    """
    chat_id, user_id, data = extract_params(update)

    if user_id != OWNER_ID and not is_admin(user_id):
        await send_message(chat_id, "⛔ شما دسترسی به این بخش ندارید.")
        return True

    docs_path = Path(__file__).parent.parent.parent / 'docs' / 'build' / 'html'

    msg = f"📚 **مستندات پروژه**\n\n"
    msg += f"📁 مسیر مستندات: `{docs_path}`\n\n"

    if docs_path.exists():
        html_path = docs_path / 'index.html'
        if html_path.exists():
            msg += f"✅ مستندات ساخته شده‌اند.\n"
            msg += f"📄 فایل اصلی: `{html_path}`\n\n"
            msg += f"برای مشاهده، فایل index.html را در مرورگر باز کنید."
        else:
            msg += f"⚠️ فایل index.html یافت نشد.\n"
            msg += f"لطفاً با دستور زیر مستندات را بسازید:\n"
            msg += f"```bash\npython scripts/build_docs.py --all\n```"
    else:
        msg += f"❌ مستندات ساخته نشده‌اند.\n\n"
        msg += f"برای ساخت مستندات، دستور زیر را اجرا کنید:\n"
        msg += f"```bash\npython scripts/build_docs.py --all\n```"

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔄 ساخت مجدد مستندات", "callback_data": "admin_docs_build"}],
            [{"text": "🔙 بازگشت به مانیتورینگ", "callback_data": "admin_monitoring"}]
        ]
    }

    await send_message(chat_id, msg, keyboard)
    return True


@route("admin_docs_build")
async def admin_docs_build(update):
    """
    ساخت مجدد مستندات از پنل مدیریت
    """
    chat_id, user_id, data = extract_params(update)

    if user_id != OWNER_ID and not is_admin(user_id):
        await send_message(chat_id, "⛔ شما دسترسی به این بخش ندارید.")
        return True

    await send_message(chat_id, "⏳ در حال ساخت مستندات... لطفاً صبر کنید.")

    try:
        # استفاده از functools.partial برای ارسال آرگومان‌های capture_output و text به subprocess.run
        func = functools.partial(
            subprocess.run,
            ['python', 'scripts/build_docs.py', '--all'],
            capture_output=True,
            text=True
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, func)

        if result.returncode == 0:
            await send_message(
                chat_id,
                "✅ مستندات با موفقیت ساخته شدند.\n\n"
                "برای مشاهده، فایل `docs/build/html/index.html` را در مرورگر باز کنید.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "admin_docs"}]]}
            )
        else:
            error_msg = result.stderr or result.stdout or "خطای نامشخص"
            await send_message(
                chat_id,
                f"❌ ساخت مستندات با خطا مواجه شد:\n```\n{error_msg[:500]}\n```",
                {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "admin_docs"}]]}
            )
    except Exception as e:
        await send_message(
            chat_id,
            f"❌ خطا در اجرای اسکریپت ساخت مستندات: {str(e)}",
            {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "admin_docs"}]]}
        )

    return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'admin_monitoring',
    'admin_monitoring_health',
    'admin_monitoring_alerts',
    'admin_monitoring_alerts_resolve',
    'admin_monitoring_alerts_history',
    'admin_monitoring_alerts_check',
    'admin_monitoring_metrics',
    'admin_monitoring_metrics_collect',
    'admin_monitoring_metrics_summary',
    'admin_monitoring_metrics_cleanup',
    'admin_monitoring_reports',
    'admin_monitoring_reports_generate',
    'admin_monitoring_reports_view',
    'admin_monitoring_reports_delete',
    'admin_docs',
    'admin_docs_build',
]