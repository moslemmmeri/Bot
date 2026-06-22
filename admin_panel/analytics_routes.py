# admin_panel/analytics_routes.py
# ثبت روت‌های مربوط به آمار و تحلیل (Analytics) در پنل مدیریت
# شامل: داشبورد کلی، آمار دکمه‌ها، دکمه‌های برتر، آمار دوره‌ای، کاربران برتر و فیلترهای پیشرفته

from .router import route, extract_params
from .analytics import (
    handle_analytics,
    handle_analytics_dashboard,
    handle_analytics_buttons_list,
    handle_analytics_button_stats,
    handle_analytics_button_daily,
    handle_analytics_top_buttons,
    handle_analytics_top_orders,
    handle_analytics_top_revenue,
    handle_analytics_top_clicks,
    handle_analytics_top_conversion,
    handle_analytics_period,
    handle_analytics_top_users,
    handle_analytics_filters,
    handle_analytics_filter_period,
    handle_analytics_period_select,
    handle_analytics_filter_service,
    handle_analytics_service_select,
    handle_analytics_service_page,
    handle_analytics_apply_filters,
    handle_analytics_clear_filters,
    handle_analytics_date_message,
)
from core import send_message
from logger_config import logger


# ========== روت‌های اصلی آمار و تحلیل ==========

@route("admin_analytics")
async def admin_analytics(update):
    """نمایش منوی اصلی بخش آمار و تحلیل"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics(chat_id, user_id)


@route("admin_analytics_dashboard")
async def admin_analytics_dashboard(update):
    """نمایش داشبورد کلی با آمارهای مهم"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_dashboard(chat_id, user_id)


# ========== روت‌های آمار دکمه‌ها ==========

@route("admin_analytics_buttons")
async def admin_analytics_buttons(update):
    """نمایش لیست دکمه‌ها برای انتخاب و مشاهده‌ی آمار"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_buttons_list(chat_id, user_id)


@route("admin_analytics_btn_")
async def admin_analytics_btn(update):
    """نمایش آمار کامل یک دکمه (admin_analytics_btn_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_button_stats(chat_id, user_id, data)


@route("admin_analytics_btn_daily_")
async def admin_analytics_btn_daily(update):
    """نمایش آمار روزانه یک دکمه در ۳۰ روز اخیر (admin_analytics_btn_daily_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_button_daily(chat_id, user_id, data)


# ========== روت‌های دکمه‌های برتر ==========

@route("admin_analytics_top_buttons")
async def admin_analytics_top_buttons(update):
    """نمایش منوی انتخاب معیار برای دکمه‌های برتر"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_top_buttons(chat_id, user_id)


@route("admin_analytics_top_orders")
async def admin_analytics_top_orders(update):
    """نمایش دکمه‌های برتر بر اساس تعداد سفارش"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_top_orders(chat_id, user_id, data)


@route("admin_analytics_top_revenue")
async def admin_analytics_top_revenue(update):
    """نمایش دکمه‌های برتر بر اساس درآمد"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_top_revenue(chat_id, user_id, data)


@route("admin_analytics_top_clicks")
async def admin_analytics_top_clicks(update):
    """نمایش دکمه‌های برتر بر اساس کلیک"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_top_clicks(chat_id, user_id, data)


@route("admin_analytics_top_conversion")
async def admin_analytics_top_conversion(update):
    """نمایش دکمه‌های برتر بر اساس نرخ تبدیل"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_top_conversion(chat_id, user_id, data)


# ========== روت‌های آمار دوره‌ای و کاربران برتر ==========

@route("admin_analytics_period")
async def admin_analytics_period(update):
    """نمایش آمار درآمد در ۳۰ روز اخیر با قابلیت فیلتر"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_period(chat_id, user_id)


@route("admin_analytics_top_users")
async def admin_analytics_top_users(update):
    """نمایش کاربرانی که بیشترین سفارش یا بیشترین مبلغ پرداختی را داشته‌اند"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_top_users(chat_id, user_id)


# ========== روت‌های فیلترهای پیشرفته آمار ==========

@route("admin_analytics_filters")
async def admin_analytics_filters(update):
    """نمایش منوی فیلترهای پیشرفته برای آمار"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_filters(chat_id, user_id)


@route("admin_analytics_filter_period")
async def admin_analytics_filter_period(update):
    """نمایش انتخاب بازه زمانی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_filter_period(chat_id, user_id, data)


@route("admin_analytics_period_")
async def admin_analytics_period_select(update):
    """انتخاب بازه زمانی (admin_analytics_period_<period>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_period_select(chat_id, user_id, data)


@route("admin_analytics_filter_service")
async def admin_analytics_filter_service(update):
    """نمایش انتخاب سرویس برای فیلتر"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_filter_service(chat_id, user_id, 0)


@route("admin_analytics_service_")
async def admin_analytics_service_select(update):
    """انتخاب سرویس برای فیلتر (admin_analytics_service_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_service_select(chat_id, user_id, data)


@route("admin_analytics_service_page_")
async def admin_analytics_service_page(update):
    """صفحه‌بندی سرویس‌ها (admin_analytics_service_page_<page>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_service_page(chat_id, user_id, data)


@route("admin_analytics_apply_filters")
async def admin_analytics_apply_filters(update):
    """اعمال فیلترها و نمایش نتایج"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_apply_filters(chat_id, user_id)


@route("admin_analytics_clear_filters")
async def admin_analytics_clear_filters(update):
    """پاک کردن فیلترها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_analytics_clear_filters(chat_id, user_id)


# ========== صادر کردن ==========

__all__ = [
    'admin_analytics',
    'admin_analytics_dashboard',
    'admin_analytics_buttons',
    'admin_analytics_btn',
    'admin_analytics_btn_daily',
    'admin_analytics_top_buttons',
    'admin_analytics_top_orders',
    'admin_analytics_top_revenue',
    'admin_analytics_top_clicks',
    'admin_analytics_top_conversion',
    'admin_analytics_period',
    'admin_analytics_top_users',
    'admin_analytics_filters',
    'admin_analytics_filter_period',
    'admin_analytics_period_select',
    'admin_analytics_filter_service',
    'admin_analytics_service_select',
    'admin_analytics_service_page',
    'admin_analytics_apply_filters',
    'admin_analytics_clear_filters',
]