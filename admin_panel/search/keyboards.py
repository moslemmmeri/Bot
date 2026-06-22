# admin_panel/search/keyboards.py
# کیبوردهای جستجوی پیشرفته سفارشات

from typing import List, Dict, Any, Optional
from database import get_all_buttons, get_button_by_id
from utils import get_service_name, format_number, get_fullname_from_order, get_order_status_persian


# ============================================================
# کیبورد اصلی جستجوی پیشرفته
# ============================================================

def advanced_search_main_keyboard() -> Dict:
    """
    کیبورد اصلی جستجوی پیشرفته

    بازگشت: کیبورد با گزینه‌های مختلف جستجو
    """
    return {
        "inline_keyboard": [
            [{"text": "🔍 جستجوی سریع (کلمه کلیدی)", "callback_data": "admin_adv_search_quick"}],
            [{"text": "📅 جستجو بر اساس تاریخ", "callback_data": "admin_adv_search_date"}],
            [{"text": "💰 جستجو بر اساس مبلغ", "callback_data": "admin_adv_search_amount"}],
            [{"text": "📌 جستجو بر اساس وضعیت", "callback_data": "admin_adv_search_status"}],
            [{"text": "🔘 جستجو بر اساس سرویس", "callback_data": "admin_adv_search_service"}],
            [{"text": "👤 جستجو بر اساس کاربر", "callback_data": "admin_adv_search_user"}],
            [{"text": "🎫 جستجو بر اساس کد رهگیری", "callback_data": "admin_adv_search_tracking"}],
            [{"text": "📎 جستجوی سفارشات دارای فایل", "callback_data": "admin_adv_search_has_file"}],
            [{"text": "🔄 بازنشانی جستجو", "callback_data": "admin_adv_search_reset"}],
            [{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}],
            [{"text": "🔙 بازگشت", "callback_data": "admin_back"}]
        ]
    }


# ============================================================
# کیبورد نمایش نتایج
# ============================================================

def search_results_keyboard(
    results: List[Dict],
    page: int = 0,
    per_page: int = 5
) -> Dict:
    """
    کیبورد نمایش نتایج جستجو با صفحه‌بندی

    پارامترها:
        results: لیست سفارشات
        page: شماره صفحه
        per_page: تعداد آیتم در هر صفحه

    بازگشت: کیبورد نتایج
    """
    total = len(results)
    start = page * per_page
    end = min(start + per_page, total)
    page_results = results[start:end]

    keyboard = []

    for order in page_results:
        order_id = order.get('id')
        fullname = get_fullname_from_order(order)
        status = order.get('status', 'pending')
        status_persian = get_order_status_persian(status)
        status_icon = "✅" if status in ['paid', 'completed'] else "⏳" if status == 'pending' else "❌"
        amount = order.get('payment_amount', 0) or 0
        service = get_service_name(order.get('button_id'))

        keyboard.append([
            {"text": f"{status_icon} #{order_id} - {fullname[:12]} - {service[:12]} - {format_number(amount)} ریال",
             "callback_data": f"admin_adv_search_order_{order_id}"}
        ])

    if not results:
        keyboard.append([{"text": "❌ هیچ نتیجه‌ای یافت نشد", "callback_data": "admin_none"}])

    # دکمه‌های صفحه‌بندی
    nav_row = []
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    if page > 0:
        nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_adv_search_page_{page - 1}"})
    if page < total_pages - 1:
        nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_adv_search_page_{page + 1}"})
    if nav_row:
        keyboard.append(nav_row)

    # آمار
    keyboard.append([{"text": f"📊 {total} نتیجه یافت شد", "callback_data": "admin_none"}])

    keyboard.append([
        {"text": "📥 خروجی Excel", "callback_data": "admin_adv_search_export"},
        {"text": "🔙 بازگشت به جستجو", "callback_data": "admin_adv_search"}
    ])

    return {"inline_keyboard": keyboard}


# ============================================================
# کیبورد انتخاب وضعیت
# ============================================================

def search_status_keyboard(selected: Optional[List[str]] = None) -> Dict:
    """
    کیبورد انتخاب وضعیت برای جستجو

    پارامترها:
        selected: لیست وضعیت‌های انتخاب‌شده

    بازگشت: کیبورد وضعیت‌ها
    """
    if selected is None:
        selected = []

    statuses = [
        ('pending', '⏳ در انتظار پرداخت'),
        ('paid', '✅ پرداخت شده'),
        ('completed', '✅ تکمیل شده'),
        ('cancelled', '❌ لغو شده'),
        ('failed', '❌ ناموفق'),
        ('refunded', '🔄 بازگشت وجه'),
    ]

    keyboard = []
    for status, label in statuses:
        check = "☑️" if status in selected else "⬜"
        keyboard.append([{"text": f"{check} {label}", "callback_data": f"admin_adv_search_status_toggle_{status}"}])

    keyboard.append([
        {"text": "✅ اعمال", "callback_data": "admin_adv_search_status_apply"},
        {"text": "❌ پاک کردن", "callback_data": "admin_adv_search_status_clear"}
    ])
    keyboard.append([{"text": "🔙 بازگشت", "callback_data": "admin_adv_search"}])

    return {"inline_keyboard": keyboard}


# ============================================================
# کیبورد انتخاب سرویس
# ============================================================

def search_service_keyboard(
    selected: Optional[List[int]] = None,
    page: int = 0,
    per_page: int = 8
) -> Dict:
    """
    کیبورد انتخاب سرویس برای جستجو

    پارامترها:
        selected: لیست شناسه‌های سرویس‌های انتخاب‌شده
        page: شماره صفحه
        per_page: تعداد آیتم در هر صفحه

    بازگشت: کیبورد سرویس‌ها
    """
    if selected is None:
        selected = []

    buttons = get_all_buttons()
    total = len(buttons)
    start = page * per_page
    end = min(start + per_page, total)
    page_buttons = buttons[start:end]

    keyboard = []
    for btn in page_buttons:
        check = "☑️" if btn['id'] in selected else "⬜"
        icon = "📂" if btn.get('has_submenu', 0) == 1 else "🔘"
        keyboard.append([{"text": f"{check} {icon} {btn['name']}", "callback_data": f"admin_adv_search_service_toggle_{btn['id']}"}])

    # صفحه‌بندی
    nav_row = []
    if page > 0:
        nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_adv_search_service_page_{page - 1}"})
    if end < total:
        nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_adv_search_service_page_{page + 1}"})
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([
        {"text": "✅ اعمال", "callback_data": "admin_adv_search_service_apply"},
        {"text": "❌ پاک کردن", "callback_data": "admin_adv_search_service_clear"}
    ])
    keyboard.append([{"text": "🔙 بازگشت", "callback_data": "admin_adv_search"}])

    return {"inline_keyboard": keyboard}


# ============================================================
# کیبوردهای کمکی
# ============================================================

def search_confirm_keyboard() -> Dict:
    """
    کیبورد تایید برای عملیات‌های جستجو (در صورت نیاز)

    بازگشت: کیبورد تایید
    """
    return {
        "inline_keyboard": [
            [{"text": "✅ تایید", "callback_data": "admin_adv_search_confirm"}],
            [{"text": "❌ انصراف", "callback_data": "admin_adv_search"}]
        ]
    }


def search_export_keyboard() -> Dict:
    """
    کیبورد انتخاب نوع خروجی برای نتایج جستجو

    بازگشت: کیبورد خروجی
    """
    return {
        "inline_keyboard": [
            [{"text": "📊 Excel", "callback_data": "admin_adv_search_export_excel"}],
            [{"text": "📋 CSV", "callback_data": "admin_adv_search_export_csv"}],
            [{"text": "📄 JSON", "callback_data": "admin_adv_search_export_json"}],
            [{"text": "🔙 بازگشت", "callback_data": "admin_adv_search_results"}]
        ]
    }


def search_empty_keyboard(message: str = "❌ هیچ نتیجه‌ای یافت نشد") -> Dict:
    """
    کیبورد برای زمانی که نتیجه‌ای وجود ندارد

    پارامترها:
        message: پیام نمایشی

    بازگشت: کیبورد خالی
    """
    return {
        "inline_keyboard": [
            [{"text": message, "callback_data": "admin_none"}],
            [{"text": "🔙 بازگشت به جستجو", "callback_data": "admin_adv_search"}]
        ]
    }


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'advanced_search_main_keyboard',
    'search_results_keyboard',
    'search_status_keyboard',
    'search_service_keyboard',
    'search_confirm_keyboard',
    'search_export_keyboard',
    'search_empty_keyboard',
]