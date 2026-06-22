# admin_panel/filter_routes.py
# مسیرهای مرحله‌ای انتخاب فیلترهای پیشرفته در پنل مدیریت

from .router import route, extract_params
from .filters import (
    AdvancedFilters,
    DateFilter,
    StatusFilter,
    ServiceFilter,
    AmountFilter,
    UserFilter,
    get_filter_manager,
    get_filter_presets,
    create_filter_from_params,
)
from core import send_message, user_states, OWNER_ID
from database import get_all_buttons, get_dynamic_orders
from logger_config import logger
from keyboards import admin_main_keyboard


# ============================================================
# توابع کمکی
# ============================================================

def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def _get_period_keyboard(current_period: str = None):
    """کیبورد انتخاب دوره زمانی"""
    periods = [
        ('today', 'امروز'),
        ('yesterday', 'دیروز'),
        ('last_7_days', '۷ روز اخیر'),
        ('last_30_days', '۳۰ روز اخیر'),
        ('last_90_days', '۹۰ روز اخیر'),
        ('this_month', 'این ماه'),
        ('last_month', 'ماه گذشته'),
        ('custom', 'سفارشی (انتخاب تاریخ)'),
    ]
    
    keyboard = []
    for period, label in periods:
        selected = "✅ " if period == current_period else ""
        keyboard.append([{"text": f"{selected}{label}", "callback_data": f"admin_filter_period_{period}"}])
    
    keyboard.append([{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}])
    return {"inline_keyboard": keyboard}


def _get_status_keyboard(current_statuses: list = None):
    """کیبورد انتخاب وضعیت سفارش"""
    if current_statuses is None:
        current_statuses = []
    
    statuses = [
        ('pending', '⏳ در انتظار پرداخت'),
        ('paid', '✅ پرداخت شده'),
        ('completed', '✅ تکمیل شده'),
        ('cancelled', '❌ لغو شده'),
    ]
    
    keyboard = []
    for status, label in statuses:
        selected = "✅ " if status in current_statuses else ""
        keyboard.append([{"text": f"{selected}{label}", "callback_data": f"admin_filter_status_toggle_{status}"}])
    
    # دکمه‌های عملیاتی
    keyboard.append([
        {"text": "✅ اعمال", "callback_data": "admin_filter_status_apply"},
        {"text": "❌ پاک کردن همه", "callback_data": "admin_filter_status_clear"}
    ])
    keyboard.append([{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}])
    return {"inline_keyboard": keyboard}


def _get_service_keyboard(current_services: list = None, page: int = 0):
    """کیبورد انتخاب سرویس"""
    if current_services is None:
        current_services = []
    
    all_buttons = get_all_buttons()
    per_page = 8
    total = len(all_buttons)
    start = page * per_page
    end = min(start + per_page, total)
    page_buttons = all_buttons[start:end]
    
    keyboard = []
    for btn in page_buttons:
        selected = "✅ " if btn['id'] in current_services else ""
        icon = "📂" if btn.get('has_submenu', 0) == 1 else "🔘"
        keyboard.append([{"text": f"{selected}{icon} {btn['name']}", "callback_data": f"admin_filter_service_toggle_{btn['id']}"}])
    
    # صفحه‌بندی
    nav_row = []
    if page > 0:
        nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_filter_service_page_{page-1}"})
    if end < total:
        nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_filter_service_page_{page+1}"})
    if nav_row:
        keyboard.append(nav_row)
    
    # دکمه‌های عملیاتی
    keyboard.append([
        {"text": "✅ اعمال", "callback_data": "admin_filter_service_apply"},
        {"text": "❌ پاک کردن همه", "callback_data": "admin_filter_service_clear"}
    ])
    keyboard.append([{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}])
    return {"inline_keyboard": keyboard}


def _get_amount_keyboard(min_amount: int = None, max_amount: int = None):
    """کیبورد تنظیم محدوده مبلغ"""
    keyboard = [
        [{"text": f"💰 حداقل: {min_amount or 'نامشخص'}", "callback_data": "admin_filter_amount_min"}],
        [{"text": f"💰 حداکثر: {max_amount or 'نامشخص'}", "callback_data": "admin_filter_amount_max"}],
        [{"text": "✅ اعمال", "callback_data": "admin_filter_amount_apply"}],
        [{"text": "❌ پاک کردن", "callback_data": "admin_filter_amount_clear"}],
        [{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]
    ]
    return {"inline_keyboard": keyboard}


def _get_preset_keyboard():
    """کیبورد انتخاب فیلترهای از پیش تعیین‌شده"""
    presets = get_filter_presets()
    
    keyboard = []
    for key, filter_obj in presets.items():
        keyboard.append([{"text": f"📌 {filter_obj.name}", "callback_data": f"admin_filter_preset_{key}"}])
    
    keyboard.append([{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}])
    return {"inline_keyboard": keyboard}


# ============================================================
# روت‌های اصلی فیلتر
# ============================================================

@route("admin_filter_menu")
async def admin_filter_menu(update):
    """نمایش منوی اصلی فیلترها"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    # دریافت فیلترهای ذخیره‌شده کاربر
    filter_manager = get_filter_manager()
    saved_filters = filter_manager.get_filters(user_id)
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "📅 فیلتر بر اساس تاریخ", "callback_data": "admin_filter_date"}],
            [{"text": "📌 فیلتر بر اساس وضعیت", "callback_data": "admin_filter_status"}],
            [{"text": "🔘 فیلتر بر اساس سرویس", "callback_data": "admin_filter_service"}],
            [{"text": "💰 فیلتر بر اساس مبلغ", "callback_data": "admin_filter_amount"}],
            [{"text": "👤 فیلتر بر اساس کاربر", "callback_data": "admin_filter_user"}],
            [{"text": "📋 فیلترهای از پیش تعیین‌شده", "callback_data": "admin_filter_presets"}],
        ]
    }
    
    # اضافه کردن فیلترهای ذخیره‌شده
    if saved_filters:
        keyboard["inline_keyboard"].append([{"text": "📂 فیلترهای ذخیره‌شده", "callback_data": "admin_filter_saved"}])
    
    keyboard["inline_keyboard"].append([
        {"text": "✅ اعمال فیلترها", "callback_data": "admin_filter_apply"},
        {"text": "❌ پاک کردن همه فیلترها", "callback_data": "admin_filter_clear_all"}
    ])
    keyboard["inline_keyboard"].append([
        {"text": "💾 ذخیره فیلتر فعلی", "callback_data": "admin_filter_save"},
        {"text": "🔙 برگشت", "callback_data": "admin_analytics"}
    ])
    
    # نمایش خلاصه فیلترهای فعال
    current_filter = user_states.get(user_id, {}).get("advanced_filter")
    if current_filter:
        summary = current_filter.get_summary()
        await send_message(
            chat_id,
            f"🎯 **مدیریت فیلترها**\n\n"
            f"📌 **فیلترهای فعال:**\n{summary}\n\n"
            f"یکی از گزینه‌های زیر را انتخاب کنید:",
            keyboard
        )
    else:
        await send_message(
            chat_id,
            "🎯 **مدیریت فیلترها**\n\n"
            "برای فیلتر کردن داده‌ها، یکی از گزینه‌های زیر را انتخاب کنید:\n"
            "• فیلترهای ترکیبی را می‌توانید با هم استفاده کنید\n"
            "• فیلترها را می‌توانید ذخیره و بعداً استفاده کنید\n\n"
            "📌 **هیچ فیلتری فعال نیست.**",
            keyboard
        )
    return True


# ============================================================
# روت‌های فیلتر تاریخ
# ============================================================

@route("admin_filter_date")
async def admin_filter_date(update):
    """نمایش صفحه انتخاب فیلتر تاریخ"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    current_filter = user_states.get(user_id, {}).get("advanced_filter")
    current_period = current_filter.date.period if current_filter else None
    
    await send_message(
        chat_id,
        "📅 **فیلتر بر اساس تاریخ**\n\n"
        "یکی از دوره‌های زمانی زیر را انتخاب کنید:\n"
        "• انتخاب «سفارشی» برای وارد کردن تاریخ دلخواه",
        _get_period_keyboard(current_period)
    )
    return True


@route("admin_filter_period_")
async def admin_filter_period(update):
    """انتخاب دوره زمانی"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    period = data.split("_")[-1]
    
    # دریافت یا ایجاد فیلتر
    if user_id not in user_states:
        user_states[user_id] = {}
    
    if "advanced_filter" not in user_states[user_id]:
        user_states[user_id]["advanced_filter"] = AdvancedFilters()
    
    current_filter = user_states[user_id]["advanced_filter"]
    
    if period == 'custom':
        # تاریخ سفارشی - از کاربر می‌خواهیم تاریخ را وارد کند
        user_states[user_id]["filter_state"] = "awaiting_start_date"
        await send_message(
            chat_id,
            "📅 **تاریخ سفارشی**\n\n"
            "لطفاً تاریخ شروع را به فرمت **YYYY-MM-DD** وارد کنید:\n"
            "(مثال: 2024-01-15)\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
    
    # تنظیم دوره
    current_filter.date.period = period
    current_filter.date.start_date = None
    current_filter.date.end_date = None
    
    await send_message(
        chat_id,
        f"✅ دوره زمانی به «{current_filter.date.get_label()}» تنظیم شد.",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
    )
    return True


@route("admin_filter_date_custom")
async def admin_filter_date_custom(update):
    """پردازش تاریخ سفارشی (از پیام)"""
    # این تابع از msg_admin صدا زده می‌شود
    pass


# ============================================================
# روت‌های فیلتر وضعیت
# ============================================================

@route("admin_filter_status")
async def admin_filter_status(update):
    """نمایش صفحه انتخاب فیلتر وضعیت"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    current_filter = user_states.get(user_id, {}).get("advanced_filter")
    current_statuses = current_filter.status.statuses if current_filter else []
    
    await send_message(
        chat_id,
        "📌 **فیلتر بر اساس وضعیت سفارش**\n\n"
        "وضعیت‌های مورد نظر را انتخاب کنید:\n"
        "(هر وضعیت را کلیک کنید تا انتخاب/لغو شود)\n"
        "سپس روی «اعمال» کلیک کنید.",
        _get_status_keyboard(current_statuses)
    )
    return True


@route("admin_filter_status_toggle_")
async def admin_filter_status_toggle(update):
    """تغییر انتخاب یک وضعیت"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    status = data.split("_")[-1]
    
    if user_id not in user_states:
        user_states[user_id] = {}
    
    if "advanced_filter" not in user_states[user_id]:
        user_states[user_id]["advanced_filter"] = AdvancedFilters()
    
    current_filter = user_states[user_id]["advanced_filter"]
    
    if status in current_filter.status.statuses:
        current_filter.status.statuses.remove(status)
    else:
        current_filter.status.statuses.append(status)
    
    # نمایش مجدد
    await send_message(
        chat_id,
        f"📌 وضعیت: {', '.join(current_filter.status.statuses) if current_filter.status.statuses else 'هیچ‌کدام'}",
        _get_status_keyboard(current_filter.status.statuses)
    )
    return True


@route("admin_filter_status_apply")
async def admin_filter_status_apply(update):
    """اعمال فیلتر وضعیت"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    await send_message(
        chat_id,
        "✅ فیلتر وضعیت اعمال شد.",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
    )
    return True


@route("admin_filter_status_clear")
async def admin_filter_status_clear(update):
    """پاک کردن فیلتر وضعیت"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    if user_id in user_states and "advanced_filter" in user_states[user_id]:
        user_states[user_id]["advanced_filter"].status.statuses = []
    
    await send_message(
        chat_id,
        "✅ فیلتر وضعیت پاک شد.",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
    )
    return True


# ============================================================
# روت‌های فیلتر سرویس
# ============================================================

@route("admin_filter_service")
async def admin_filter_service(update):
    """نمایش صفحه انتخاب فیلتر سرویس"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    current_filter = user_states.get(user_id, {}).get("advanced_filter")
    current_services = current_filter.service.button_ids if current_filter else []
    
    await send_message(
        chat_id,
        "🔘 **فیلتر بر اساس سرویس**\n\n"
        "سرویس‌های مورد نظر را انتخاب کنید:\n"
        "(هر سرویس را کلیک کنید تا انتخاب/لغو شود)\n"
        "سپس روی «اعمال» کلیک کنید.",
        _get_service_keyboard(current_services)
    )
    return True


@route("admin_filter_service_toggle_")
async def admin_filter_service_toggle(update):
    """تغییر انتخاب یک سرویس"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        service_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سرویس نامعتبر.")
        return True
    
    if user_id not in user_states:
        user_states[user_id] = {}
    
    if "advanced_filter" not in user_states[user_id]:
        user_states[user_id]["advanced_filter"] = AdvancedFilters()
    
    current_filter = user_states[user_id]["advanced_filter"]
    
    if service_id in current_filter.service.button_ids:
        current_filter.service.button_ids.remove(service_id)
    else:
        current_filter.service.button_ids.append(service_id)
    
    # نمایش مجدد
    await send_message(
        chat_id,
        f"🔘 سرویس‌های انتخاب‌شده: {len(current_filter.service.button_ids)}",
        _get_service_keyboard(current_filter.service.button_ids)
    )
    return True


@route("admin_filter_service_page_")
async def admin_filter_service_page(update):
    """صفحه‌بندی سرویس‌ها"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        page = int(data.split("_")[-1])
    except ValueError:
        page = 0
    
    current_filter = user_states.get(user_id, {}).get("advanced_filter")
    current_services = current_filter.service.button_ids if current_filter else []
    
    await send_message(
        chat_id,
        f"🔘 **سرویس‌ها - صفحه {page + 1}**",
        _get_service_keyboard(current_services, page)
    )
    return True


@route("admin_filter_service_apply")
async def admin_filter_service_apply(update):
    """اعمال فیلتر سرویس"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    await send_message(
        chat_id,
        "✅ فیلتر سرویس اعمال شد.",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
    )
    return True


@route("admin_filter_service_clear")
async def admin_filter_service_clear(update):
    """پاک کردن فیلتر سرویس"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    if user_id in user_states and "advanced_filter" in user_states[user_id]:
        user_states[user_id]["advanced_filter"].service.button_ids = []
    
    await send_message(
        chat_id,
        "✅ فیلتر سرویس پاک شد.",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
    )
    return True


# ============================================================
# روت‌های فیلتر مبلغ
# ============================================================

@route("admin_filter_amount")
async def admin_filter_amount(update):
    """نمایش صفحه تنظیم فیلتر مبلغ"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    current_filter = user_states.get(user_id, {}).get("advanced_filter")
    min_amount = current_filter.amount.min_amount if current_filter else None
    max_amount = current_filter.amount.max_amount if current_filter else None
    
    await send_message(
        chat_id,
        f"💰 **فیلتر بر اساس مبلغ**\n\n"
        f"حداقل: {min_amount or 'تنظیم نشده'}\n"
        f"حداکثر: {max_amount or 'تنظیم نشده'}\n\n"
        "برای تنظیم هر کدام، روی دکمه مربوطه کلیک کنید.",
        _get_amount_keyboard(min_amount, max_amount)
    )
    return True


@route("admin_filter_amount_min")
async def admin_filter_amount_min(update):
    """تنظیم حداقل مبلغ"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    user_states[user_id]["filter_state"] = "awaiting_min_amount"
    await send_message(
        chat_id,
        "💰 **تنظیم حداقل مبلغ**\n\n"
        "لطفاً حداقل مبلغ را به ریال وارد کنید (فقط عدد):\n"
        "(مثال: 100000 برای ۱۰۰,۰۰۰ ریال)\n\n"
        "برای انصراف، /cancel را ارسال کنید."
    )
    return True


@route("admin_filter_amount_max")
async def admin_filter_amount_max(update):
    """تنظیم حداکثر مبلغ"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    user_states[user_id]["filter_state"] = "awaiting_max_amount"
    await send_message(
        chat_id,
        "💰 **تنظیم حداکثر مبلغ**\n\n"
        "لطفاً حداکثر مبلغ را به ریال وارد کنید (فقط عدد):\n"
        "(مثال: 1000000 برای ۱,۰۰۰,۰۰۰ ریال)\n\n"
        "برای انصراف، /cancel را ارسال کنید."
    )
    return True


@route("admin_filter_amount_apply")
async def admin_filter_amount_apply(update):
    """اعمال فیلتر مبلغ"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    await send_message(
        chat_id,
        "✅ فیلتر مبلغ اعمال شد.",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
    )
    return True


@route("admin_filter_amount_clear")
async def admin_filter_amount_clear(update):
    """پاک کردن فیلتر مبلغ"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    if user_id in user_states and "advanced_filter" in user_states[user_id]:
        user_states[user_id]["advanced_filter"].amount.min_amount = None
        user_states[user_id]["advanced_filter"].amount.max_amount = None
    
    await send_message(
        chat_id,
        "✅ فیلتر مبلغ پاک شد.",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
    )
    return True


# ============================================================
# روت‌های فیلتر کاربر
# ============================================================

@route("admin_filter_user")
async def admin_filter_user(update):
    """تنظیم فیلتر کاربر"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    user_states[user_id]["filter_state"] = "awaiting_user_filter"
    await send_message(
        chat_id,
        "👤 **فیلتر بر اساس کاربر**\n\n"
        "لطفاً شناسه کاربری (user_id) یا نام کاربری (username) را وارد کنید:\n"
        "(مثال: 123456789 یا @username)\n\n"
        "برای انصراف، /cancel را ارسال کنید."
    )
    return True


# ============================================================
# روت‌های فیلترهای از پیش تعیین‌شده
# ============================================================

@route("admin_filter_presets")
async def admin_filter_presets(update):
    """نمایش فیلترهای از پیش تعیین‌شده"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    await send_message(
        chat_id,
        "📋 **فیلترهای از پیش تعیین‌شده**\n\n"
        "با انتخاب هر گزینه، فیلترهای مربوطه به‌طور خودکار اعمال می‌شوند:",
        _get_preset_keyboard()
    )
    return True


@route("admin_filter_preset_")
async def admin_filter_preset(update):
    """اعمال یک فیلتر از پیش تعیین‌شده"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    preset_key = data.split("_")[-1]
    presets = get_filter_presets()
    
    if preset_key not in presets:
        await send_message(chat_id, "❌ فیلتر یافت نشد.")
        return True
    
    filter_obj = presets[preset_key]
    
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]["advanced_filter"] = filter_obj
    
    await send_message(
        chat_id,
        f"✅ فیلتر «{filter_obj.name}» اعمال شد.\n\n"
        f"📌 **خلاصه:**\n{filter_obj.get_summary()}",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلترها", "callback_data": "admin_filter_menu"}]]}
    )
    return True


# ============================================================
# روت‌های فیلترهای ذخیره‌شده
# ============================================================

@route("admin_filter_saved")
async def admin_filter_saved(update):
    """نمایش فیلترهای ذخیره‌شده کاربر"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    filter_manager = get_filter_manager()
    saved_filters = filter_manager.get_filters(user_id)
    
    if not saved_filters:
        await send_message(
            chat_id,
            "📂 **فیلترهای ذخیره‌شده**\n\n"
            "هیچ فیلتری ذخیره نشده است.\n"
            "برای ذخیره فیلتر فعلی، از گزینه «ذخیره فیلتر فعلی» استفاده کنید.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
        )
        return True
    
    keyboard = []
    for name, filter_obj in saved_filters.items():
        keyboard.append([{"text": f"📌 {name}", "callback_data": f"admin_filter_load_{name}"}])
        keyboard.append([{"text": f"🗑️ حذف", "callback_data": f"admin_filter_delete_{name}"}])
    
    keyboard.append([{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}])
    
    await send_message(
        chat_id,
        "📂 **فیلترهای ذخیره‌شده**\n\n"
        "برای اعمال هر فیلتر، روی نام آن کلیک کنید:",
        {"inline_keyboard": keyboard}
    )
    return True


@route("admin_filter_load_")
async def admin_filter_load(update):
    """بارگذاری یک فیلتر ذخیره‌شده"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    filter_name = data.split("_", 3)[3]
    filter_manager = get_filter_manager()
    filter_obj = filter_manager.get_filter(user_id, filter_name)
    
    if not filter_obj:
        await send_message(chat_id, "❌ فیلتر یافت نشد.")
        return True
    
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]["advanced_filter"] = filter_obj
    
    await send_message(
        chat_id,
        f"✅ فیلتر «{filter_name}» بارگذاری شد.\n\n"
        f"📌 **خلاصه:**\n{filter_obj.get_summary()}",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلترها", "callback_data": "admin_filter_menu"}]]}
    )
    return True


@route("admin_filter_delete_")
async def admin_filter_delete(update):
    """حذف یک فیلتر ذخیره‌شده"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    filter_name = data.split("_", 3)[3]
    filter_manager = get_filter_manager()
    
    if filter_manager.delete_filter(user_id, filter_name):
        await send_message(chat_id, f"✅ فیلتر «{filter_name}» حذف شد.")
    else:
        await send_message(chat_id, "❌ خطا در حذف فیلتر.")
    
    return await admin_filter_saved(update)


# ============================================================
# روت‌های عملیاتی فیلترها
# ============================================================

@route("admin_filter_apply")
async def admin_filter_apply(update):
    """اعمال همه فیلترهای فعلی و نمایش نتایج"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    current_filter = user_states.get(user_id, {}).get("advanced_filter")
    
    if not current_filter or current_filter.is_empty():
        await send_message(chat_id, "⚠️ هیچ فیلتری انتخاب نشده است.")
        return True
    
    # دریافت سفارشات و اعمال فیلتر
    orders = get_dynamic_orders()
    filtered_orders = current_filter.apply_all(orders)
    
    # ذخیره نتایج فیلتر در user_states
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]["orders_list"] = filtered_orders
    user_states[user_id]["orders_page"] = 0
    
    # نمایش خلاصه
    total = len(orders)
    filtered_count = len(filtered_orders)
    
    await send_message(
        chat_id,
        f"✅ **فیلتر اعمال شد**\n\n"
        f"📊 **نتایج:**\n"
        f"• کل سفارشات: {total}\n"
        f"• سفارشات فیلترشده: {filtered_count}\n\n"
        f"📌 **فیلترهای اعمال‌شده:**\n{current_filter.get_summary()}\n\n"
        f"برای مشاهده نتایج فیلتر شده، به بخش سفارشات بروید.",
        {
            "inline_keyboard": [
                [{"text": "📋 مشاهده سفارشات فیلترشده", "callback_data": "admin_orders"}],
                [{"text": "🔙 بازگشت به فیلترها", "callback_data": "admin_filter_menu"}]
            ]
        }
    )
    return True


@route("admin_filter_clear_all")
async def admin_filter_clear_all(update):
    """پاک کردن همه فیلترها"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    if user_id in user_states:
        user_states[user_id].pop("advanced_filter", None)
        user_states[user_id].pop("orders_list", None)
    
    await send_message(
        chat_id,
        "✅ همه فیلترها پاک شدند.",
        {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
    )
    return True


@route("admin_filter_save")
async def admin_filter_save(update):
    """ذخیره فیلتر فعلی"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    current_filter = user_states.get(user_id, {}).get("advanced_filter")
    
    if not current_filter or current_filter.is_empty():
        await send_message(chat_id, "⚠️ هیچ فیلتری برای ذخیره وجود ندارد.")
        return True
    
    user_states[user_id]["filter_state"] = "awaiting_filter_name"
    await send_message(
        chat_id,
        "💾 **ذخیره فیلتر**\n\n"
        "لطفاً یک نام برای این فیلتر وارد کنید:\n"
        "(مثال: «گزارش ماه گذشته» یا «سفارشات پرداخت‌شده»)\n\n"
        "برای انصراف، /cancel را ارسال کنید."
    )
    return True


# ============================================================
# پردازش پیام‌های فیلتر (از msg_admin)
# ============================================================

async def handle_filter_message(chat_id: int, user_id: int, text: str) -> bool:
    """پردازش پیام‌های مربوط به فیلترها"""
    state_info = user_states.get(user_id, {})
    filter_state = state_info.get("filter_state")
    
    if not filter_state:
        return False
    
    # ========== تاریخ سفارشی ==========
    if filter_state == "awaiting_start_date":
        try:
            # اعتبارسنجی تاریخ
            from datetime import datetime
            datetime.strptime(text, "%Y-%m-%d")
            
            if "advanced_filter" not in user_states[user_id]:
                user_states[user_id]["advanced_filter"] = AdvancedFilters()
            
            user_states[user_id]["advanced_filter"].date.start_date = text
            user_states[user_id]["filter_state"] = "awaiting_end_date"
            
            await send_message(
                chat_id,
                "✅ تاریخ شروع ثبت شد.\n\n"
                "لطفاً تاریخ پایان را به فرمت **YYYY-MM-DD** وارد کنید:\n"
                "(مثال: 2024-01-20)"
            )
            return True
            
        except ValueError:
            await send_message(chat_id, "❌ فرمت تاریخ نامعتبر. لطفاً به فرمت YYYY-MM-DD وارد کنید.")
            return True
    
    if filter_state == "awaiting_end_date":
        try:
            from datetime import datetime
            datetime.strptime(text, "%Y-%m-%d")
            
            if "advanced_filter" not in user_states[user_id]:
                user_states[user_id]["advanced_filter"] = AdvancedFilters()
            
            user_states[user_id]["advanced_filter"].date.end_date = text
            user_states[user_id]["advanced_filter"].date.period = "custom"
            user_states[user_id]["filter_state"] = None
            
            await send_message(
                chat_id,
                f"✅ تاریخ سفارشی تنظیم شد.\n\n"
                f"📅 از {user_states[user_id]['advanced_filter'].date.start_date} تا {text}\n\n"
                f"برای اعمال فیلتر، از گزینه «اعمال فیلترها» استفاده کنید.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
            )
            return True
            
        except ValueError:
            await send_message(chat_id, "❌ فرمت تاریخ نامعتبر. لطفاً به فرمت YYYY-MM-DD وارد کنید.")
            return True
    
    # ========== فیلتر مبلغ ==========
    if filter_state == "awaiting_min_amount":
        try:
            amount = int(text.replace(",", "").replace(" ", ""))
            if amount < 0:
                await send_message(chat_id, "❌ مبلغ نمی‌تواند منفی باشد.")
                return True
            
            if "advanced_filter" not in user_states[user_id]:
                user_states[user_id]["advanced_filter"] = AdvancedFilters()
            
            user_states[user_id]["advanced_filter"].amount.min_amount = amount
            user_states[user_id]["filter_state"] = None
            
            await send_message(
                chat_id,
                f"✅ حداقل مبلغ {amount:,} ریال تنظیم شد.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
            )
            return True
            
        except ValueError:
            await send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.")
            return True
    
    if filter_state == "awaiting_max_amount":
        try:
            amount = int(text.replace(",", "").replace(" ", ""))
            if amount < 0:
                await send_message(chat_id, "❌ مبلغ نمی‌تواند منفی باشد.")
                return True
            
            if "advanced_filter" not in user_states[user_id]:
                user_states[user_id]["advanced_filter"] = AdvancedFilters()
            
            user_states[user_id]["advanced_filter"].amount.max_amount = amount
            user_states[user_id]["filter_state"] = None
            
            await send_message(
                chat_id,
                f"✅ حداکثر مبلغ {amount:,} ریال تنظیم شد.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
            )
            return True
            
        except ValueError:
            await send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.")
            return True
    
    # ========== فیلتر کاربر ==========
    if filter_state == "awaiting_user_filter":
        if "advanced_filter" not in user_states[user_id]:
            user_states[user_id]["advanced_filter"] = AdvancedFilters()
        
        # بررسی آیا شناسه عددی است
        if text.isdigit():
            user_states[user_id]["advanced_filter"].user.user_id = int(text)
            user_states[user_id]["advanced_filter"].user.username = None
        else:
            # نام کاربری (با یا بدون @)
            username = text.lstrip('@')
            user_states[user_id]["advanced_filter"].user.username = username
            user_states[user_id]["advanced_filter"].user.user_id = None
        
        user_states[user_id]["filter_state"] = None
        
        await send_message(
            chat_id,
            f"✅ فیلتر کاربر تنظیم شد.\n\n"
            f"👤 کاربر: {text}",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
        )
        return True
    
    # ========== ذخیره فیلتر ==========
    if filter_state == "awaiting_filter_name":
        if not text or text.strip() == "":
            await send_message(chat_id, "❌ نام نمی‌تواند خالی باشد.")
            return True
        
        current_filter = user_states[user_id].get("advanced_filter")
        if not current_filter:
            await send_message(chat_id, "❌ هیچ فیلتری برای ذخیره وجود ندارد.")
            user_states[user_id]["filter_state"] = None
            return True
        
        filter_manager = get_filter_manager()
        if filter_manager.save_filter(user_id, current_filter, text.strip()):
            await send_message(
                chat_id,
                f"✅ فیلتر «{text}» با موفقیت ذخیره شد.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلتر", "callback_data": "admin_filter_menu"}]]}
            )
        else:
            await send_message(chat_id, "❌ خطا در ذخیره فیلتر.")
        
        user_states[user_id]["filter_state"] = None
        return True
    
    return False


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'admin_filter_menu',
    'admin_filter_date',
    'admin_filter_period',
    'admin_filter_status',
    'admin_filter_status_toggle',
    'admin_filter_status_apply',
    'admin_filter_status_clear',
    'admin_filter_service',
    'admin_filter_service_toggle',
    'admin_filter_service_page',
    'admin_filter_service_apply',
    'admin_filter_service_clear',
    'admin_filter_amount',
    'admin_filter_amount_min',
    'admin_filter_amount_max',
    'admin_filter_amount_apply',
    'admin_filter_amount_clear',
    'admin_filter_user',
    'admin_filter_presets',
    'admin_filter_preset',
    'admin_filter_saved',
    'admin_filter_load',
    'admin_filter_delete',
    'admin_filter_apply',
    'admin_filter_clear_all',
    'admin_filter_save',
    'handle_filter_message',
]