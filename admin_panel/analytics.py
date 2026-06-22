# admin_panel/analytics.py
# داشبورد تحلیلی و آمار عملکرد دکمه‌ها - نسخه کامل با نمایش گرافیکی و گزارش‌های پیشرفته
# پشتیبانی از فیلترهای پیشرفته (بازه زمانی، نوع سرویس، وضعیت، محدوده مبلغ، کاربر)
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, OWNER_ID, user_states
from database import (
    get_dashboard_stats,
    get_button_stats,
    get_top_buttons,
    get_revenue_by_period,
    get_button_stats_by_date,
    get_top_users,
    get_all_buttons,
    get_button_by_id,
    get_advanced_stats_aggregated,
    get_advanced_stats,
)
from keyboards import admin_main_keyboard
from utils import format_number, format_percent
from datetime import datetime
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error
)


# ==================== توابع کمکی ====================

def _is_owner(user_id):
    """بررسی آیا کاربر OWNER_ID است"""
    return user_id == OWNER_ID


def _build_filter_keyboard(current_filters=None):
    """ساخت کیبورد فیلترهای پیشرفته برای آمار"""
    if current_filters is None:
        current_filters = {}
    
    keyboard = []
    
    # فیلتر بازه زمانی
    period = current_filters.get('period', 'last_30_days')
    period_labels = {
        'today': 'امروز',
        'yesterday': 'دیروز',
        'last_7_days': '۷ روز اخیر',
        'last_30_days': '۳۰ روز اخیر',
        'last_90_days': '۹۰ روز اخیر',
        'this_month': 'این ماه',
        'last_month': 'ماه گذشته',
        'custom': 'سفارشی'
    }
    
    keyboard.append([{"text": f"📅 بازه زمانی: {period_labels.get(period, period)}", "callback_data": "admin_analytics_filter_period"}])
    
    # فیلتر سرویس
    button_id = current_filters.get('button_id')
    if button_id:
        btn = get_button_by_id(button_id)
        service_name = btn['name'] if btn else f"سرویس {button_id}"
        keyboard.append([{"text": f"🔘 سرویس: {service_name}", "callback_data": "admin_analytics_filter_service"}])
    else:
        keyboard.append([{"text": "🔘 همه سرویس‌ها", "callback_data": "admin_analytics_filter_service"}])
    
    # دکمه‌های اعمال و پاک کردن
    keyboard.append([
        {"text": "✅ اعمال فیلترها", "callback_data": "admin_analytics_apply_filters"},
        {"text": "❌ پاک کردن فیلترها", "callback_data": "admin_analytics_clear_filters"}
    ])
    
    keyboard.append([{"text": "🔙 بازگشت به منوی آمار", "callback_data": "admin_analytics"}])
    
    return {"inline_keyboard": keyboard}


# ==================== کیبوردهای تحلیلی ====================

def analytics_main_keyboard():
    """کیبورد اصلی بخش آمار و تحلیل"""
    return {
        "inline_keyboard": [
            [{"text": "📊 داشبورد کلی", "callback_data": "admin_analytics_dashboard"}],
            [{"text": "🏆 دکمه‌های برتر", "callback_data": "admin_analytics_top_buttons"}],
            [{"text": "📈 آمار دوره‌ای", "callback_data": "admin_analytics_period"}],
            [{"text": "👥 کاربران برتر", "callback_data": "admin_analytics_top_users"}],
            [{"text": "🎯 فیلترهای پیشرفته", "callback_data": "admin_analytics_filters"}],
            [{"text": "📊 نمودارهای تحلیلی", "callback_data": "admin_chart_custom"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


def analytics_button_select_keyboard():
    """کیبورد انتخاب دکمه برای مشاهده‌ی آمار"""
    try:
        buttons = get_all_buttons()
        keyboard = []
        
        if not buttons:
            keyboard.append([{"text": "❌ هیچ دکمه‌ای یافت نشد", "callback_data": "admin_none"}])
        else:
            for btn in buttons:
                icon = "📂" if btn.get('has_submenu', 0) == 1 else "🔘"
                keyboard.append([
                    {"text": f"{icon} {btn['name']}", "callback_data": f"admin_analytics_btn_{btn['id']}"}
                ])
        
        keyboard.append([{"text": "🔙 برگشت به آمار", "callback_data": "admin_analytics"}])
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in analytics_button_select_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری دکمه‌ها", "callback_data": "admin_analytics"}]]}


def analytics_button_stats_keyboard(button_id):
    """کیبورد آمار یک دکمه با گزینه‌های بیشتر"""
    return {
        "inline_keyboard": [
            [{"text": "📊 آمار روزانه (۳۰ روز)", "callback_data": f"admin_analytics_btn_daily_{button_id}"}],
            [{"text": "🔙 برگشت به لیست دکمه‌ها", "callback_data": "admin_analytics_buttons"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


def analytics_filter_period_keyboard(current_period=None):
    """کیبورد انتخاب بازه زمانی"""
    if current_period is None:
        current_period = 'last_30_days'
    
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
        keyboard.append([{"text": f"{selected}{label}", "callback_data": f"admin_analytics_period_{period}"}])
    
    keyboard.append([{"text": "🔙 بازگشت به فیلترها", "callback_data": "admin_analytics_filters"}])
    return {"inline_keyboard": keyboard}


def analytics_filter_service_keyboard(selected_service=None, page=0):
    """کیبورد انتخاب سرویس برای فیلتر"""
    try:
        buttons = get_all_buttons()
        per_page = 8
        total = len(buttons)
        start = page * per_page
        end = min(start + per_page, total)
        page_buttons = buttons[start:end]
        
        keyboard = []
        for btn in page_buttons:
            selected = "✅ " if btn['id'] == selected_service else ""
            icon = "📂" if btn.get('has_submenu', 0) == 1 else "🔘"
            keyboard.append([{"text": f"{selected}{icon} {btn['name']}", "callback_data": f"admin_analytics_service_{btn['id']}"}])
        
        # صفحه‌بندی
        nav_row = []
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_analytics_service_page_{page-1}"})
        if end < total:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_analytics_service_page_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)
        
        keyboard.append([{"text": "🔙 بازگشت به فیلترها", "callback_data": "admin_analytics_filters"}])
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in analytics_filter_service_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری سرویس‌ها", "callback_data": "admin_analytics_filters"}]]}


# ==================== هندلر اصلی ====================

async def handle_analytics(chat_id, user_id):
    """
    نمایش منوی اصلی بخش آمار و تحلیل
    """
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        await send_message(
            chat_id,
            "📊 **داشبورد تحلیلی و آمار**\n\n"
            "از این بخش می‌توانید:\n"
            "• آمار کلی ربات را مشاهده کنید\n"
            "• عملکرد هر دکمه را بررسی کنید\n"
            "• دکمه‌های پربازدید را شناسایی کنید\n"
            "• روند درآمد را در بازه‌های زمانی مختلف ببینید\n"
            "• کاربران برتر را بشناسید\n"
            "• از فیلترهای پیشرفته برای تحلیل دقیق‌تر استفاده کنید",
            analytics_main_keyboard()
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش صفحه آمار.")
        return True


# ==================== داشبورد کلی ====================

async def handle_analytics_dashboard(chat_id, user_id):
    """
    نمایش داشبورد کلی با آمارهای مهم
    """
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        stats = get_dashboard_stats()
        
        msg = "📊 **داشبورد کلی ربات**\n\n"
        msg += f"👥 **کاربران:**\n"
        msg += f"  • کل کاربران: {format_number(stats.get('total_users', 0))}\n\n"
        
        msg += f"💰 **درآمد:**\n"
        msg += f"  • کل درآمد: {format_number(stats.get('total_revenue', 0))} ریال\n"
        msg += f"  • تعداد سفارشات: {format_number(stats.get('total_orders', 0))}\n"
        msg += f"  • میانگین هر سفارش: {format_number(stats.get('avg_order_value', 0))} ریال\n\n"
        
        msg += f"📈 **تعاملات:**\n"
        msg += f"  • کلیک روی دکمه‌ها: {format_number(stats.get('total_clicks', 0))}\n"
        msg += f"  • شروع فرم: {format_number(stats.get('total_form_starts', 0))}\n"
        msg += f"  • نرخ تبدیل کلی: {format_percent(stats.get('overall_conversion', 0))}\n\n"
        
        # محاسبه نرخ تبدیل فرم به سفارش
        form_starts = stats.get('total_form_starts', 0)
        orders = stats.get('total_orders', 0)
        form_to_order_rate = 0
        if form_starts > 0:
            form_to_order_rate = (orders / form_starts) * 100
        
        msg += f"📊 **نرخ‌های تبدیل:**\n"
        msg += f"  • کلیک → شروع فرم: {format_percent((form_starts / stats.get('total_clicks', 1)) * 100 if stats.get('total_clicks', 0) > 0 else 0)}\n"
        msg += f"  • شروع فرم → سفارش: {format_percent(form_to_order_rate)}\n"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "📈 آمار دوره‌ای", "callback_data": "admin_analytics_period"}],
                [{"text": "🏆 دکمه‌های برتر", "callback_data": "admin_analytics_top_buttons"}],
                [{"text": "🎯 فیلترهای پیشرفته", "callback_data": "admin_analytics_filters"}],
                [{"text": "📊 نمودارهای تحلیلی", "callback_data": "admin_chart_custom"}],
                [{"text": "🔙 برگشت به منوی آمار", "callback_data": "admin_analytics"}]
            ]
        }
        
        await send_message(chat_id, msg, keyboard)
        logger.info(f"داشبورد تحلیلی برای کاربر {user_id} نمایش داده شد.")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_dashboard: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش داشبورد.")
        return True


# ==================== آمار یک دکمه خاص ====================

async def handle_analytics_buttons_list(chat_id, user_id):
    """
    نمایش لیست دکمه‌ها برای انتخاب و مشاهده‌ی آمار
    """
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        keyboard = analytics_button_select_keyboard()
        await send_message(
            chat_id,
            "🔘 **انتخاب دکمه برای مشاهده‌ی آمار**\n\n"
            "لطفاً دکمه‌ای که می‌خواهید آمار آن را ببینید انتخاب کنید:",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_buttons_list: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست دکمه‌ها.")
        return True


async def handle_analytics_button_stats(chat_id, user_id, data):
    """
    نمایش آمار کامل یک دکمه (admin_analytics_btn_<button_id>)
    """
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        button_id = int(data.split("_")[-1])
        button = get_button_by_id(button_id)
        
        if not button:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        stats = get_button_stats(button_id)
        
        msg = f"📊 **آمار دکمه: {button['name']}**\n"
        msg += f"🆔 شناسه: {button_id}\n"
        msg += f"📂 دسته‌بندی: {button.get('category_name', 'نامشخص')}\n\n"
        
        msg += f"📌 **تعاملات:**\n"
        msg += f"  • کلیک: {format_number(stats.get('clicks', 0))}\n"
        msg += f"  • شروع فرم: {format_number(stats.get('form_starts', 0))}\n"
        msg += f"  • سفارش: {format_number(stats.get('orders', 0))}\n\n"
        
        msg += f"💰 **درآمد:**\n"
        msg += f"  • کل درآمد: {format_number(stats.get('revenue', 0))} ریال\n"
        msg += f"  • میانگین هر سفارش: "
        orders = stats.get('orders', 0)
        revenue = stats.get('revenue', 0)
        if orders > 0:
            msg += f"{format_number(revenue / orders)} ریال\n"
        else:
            msg += "۰ ریال\n"
        msg += f"  • نرخ تبدیل: {format_percent(stats.get('conversion_rate', 0))}\n\n"
        
        # وضعیت دکمه
        status_text = "🟢 فعال" if button.get('is_active', 1) == 1 else "🔴 غیرفعال"
        payment_text = "💰 فعال" if button.get('has_payment', 0) == 1 else "💳 غیرفعال"
        submenu_text = "📂 دارد" if button.get('has_submenu', 0) == 1 else "📄 ندارد"
        
        msg += f"⚙️ **وضعیت:**\n"
        msg += f"  • وضعیت: {status_text}\n"
        msg += f"  • پرداخت: {payment_text}\n"
        msg += f"  • زیرمنو: {submenu_text}\n"
        if button.get('has_payment', 0) == 1:
            msg += f"  • مبلغ: {format_number(button.get('price_amount', 0))} ریال\n"
        
        keyboard = analytics_button_stats_keyboard(button_id)
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_button_stats for button {button_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش آمار دکمه.")
        return True


async def handle_analytics_button_daily(chat_id, user_id, data):
    """
    نمایش آمار روزانه یک دکمه در ۳۰ روز اخیر (admin_analytics_btn_daily_<button_id>)
    """
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        button_id = int(data.split("_")[-1])
        button = get_button_by_id(button_id)
        
        if not button:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        daily_stats = get_button_stats_by_date(button_id, 30)
        
        if not daily_stats:
            await send_message(
                chat_id,
                f"📊 **آمار روزانه {button['name']}**\n\n"
                "هیچ داده‌ای برای ۳۰ روز اخیر یافت نشد.",
                analytics_button_stats_keyboard(button_id)
            )
            return True
        
        msg = f"📊 **آمار روزانه {button['name']} (۳۰ روز اخیر)**\n\n"
        
        # خلاصه
        total_clicks = sum(d.get('clicks', 0) for d in daily_stats)
        total_orders = sum(d.get('orders', 0) for d in daily_stats)
        total_revenue = sum(d.get('revenue', 0) for d in daily_stats)
        
        msg += f"📌 **جمع کل:**\n"
        msg += f"  • کلیک: {format_number(total_clicks)}\n"
        msg += f"  • سفارش: {format_number(total_orders)}\n"
        msg += f"  • درآمد: {format_number(total_revenue)} ریال\n\n"
        
        # نمایش ۷ روز اخیر
        msg += "📅 **۷ روز اخیر:**\n"
        for i, day in enumerate(daily_stats[:7]):
            date = day.get('date', '')
            clicks = day.get('clicks', 0)
            orders = day.get('orders', 0)
            revenue = day.get('revenue', 0)
            
            if clicks > 0 or orders > 0:
                msg += f"  • {date}: {clicks} کلیک | {orders} سفارش | {format_number(revenue)} ریال\n"
        
        if len(daily_stats) > 7:
            msg += f"\n... و {len(daily_stats) - 7} روز دیگر"
        
        keyboard = analytics_button_stats_keyboard(button_id)
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_button_daily for button {button_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش آمار روزانه.")
        return True


# ==================== دکمه‌های برتر ====================

async def handle_analytics_top_buttons(chat_id, user_id):
    """
    نمایش دکمه‌های برتر بر اساس معیارهای مختلف
    """
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🏆 بر اساس تعداد سفارش", "callback_data": "admin_analytics_top_orders"}],
                [{"text": "💰 بر اساس درآمد", "callback_data": "admin_analytics_top_revenue"}],
                [{"text": "👆 بر اساس کلیک", "callback_data": "admin_analytics_top_clicks"}],
                [{"text": "📈 بر اساس نرخ تبدیل", "callback_data": "admin_analytics_top_conversion"}],
                [{"text": "🔙 برگشت", "callback_data": "admin_analytics"}]
            ]
        }
        
        await send_message(
            chat_id,
            "🏆 **دکمه‌های برتر**\n\n"
            "لطفاً معیار مورد نظر را انتخاب کنید:\n"
            "(با استفاده از فیلترهای پیشرفته می‌توانید بازه زمانی را نیز مشخص کنید)",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_top_buttons: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش دکمه‌های برتر.")
        return True


async def _show_top_buttons(chat_id, user_id, sort_by, title):
    """
    تابع کمکی برای نمایش دکمه‌های برتر بر اساس معیار مشخص
    """
    try:
        # دریافت فیلترهای کاربر
        user_filters = user_states.get(user_id, {}).get("analytics_filters", {})
        start_date = user_filters.get('start_date')
        end_date = user_filters.get('end_date')
        
        top_buttons = get_top_buttons(limit=10, sort_by=sort_by, start_date=start_date, end_date=end_date)
        
        if not top_buttons:
            await send_message(
                chat_id,
                f"🏆 **{title}**\n\nهیچ داده‌ای یافت نشد.",
                {
                    "inline_keyboard": [
                        [{"text": "🔙 برگشت", "callback_data": "admin_analytics_top_buttons"}]
                    ]
                }
            )
            return True
        
        msg = f"🏆 **{title}**\n\n"
        if start_date or end_date:
            msg += f"📅 بازه: {start_date or 'از ابتدا'} تا {end_date or 'تا امروز'}\n\n"
        
        msg += "رتبه | نام دکمه | آمار\n"
        msg += "─" * 30 + "\n"
        
        labels = {
            'orders': 'سفارش',
            'revenue': 'درآمد (ریال)',
            'clicks': 'کلیک',
            'conversion_rate': 'نرخ تبدیل'
        }
        label = labels.get(sort_by, 'آمار')
        
        for i, btn in enumerate(top_buttons, 1):
            name = btn.get('button_name', 'نامشخص')[:20]
            value = btn.get(sort_by, 0)
            
            if sort_by == 'conversion_rate':
                value = f"{value}%"
            elif sort_by == 'revenue':
                value = format_number(value)
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            msg += f"{medal} {name}: {value} {label}\n"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 برگشت به معیارها", "callback_data": "admin_analytics_top_buttons"}],
                [{"text": "🎯 تغییر فیلترها", "callback_data": "admin_analytics_filters"}],
                [{"text": "🔙 برگشت به منوی آمار", "callback_data": "admin_analytics"}]
            ]
        }
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in _show_top_buttons for {sort_by}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش دکمه‌های برتر.")
        return True


async def handle_analytics_top_orders(chat_id, user_id, data):
    """نمایش دکمه‌های برتر بر اساس تعداد سفارش"""
    return await _show_top_buttons(chat_id, user_id, 'orders', 'دکمه‌های پرفروش')


async def handle_analytics_top_revenue(chat_id, user_id, data):
    """نمایش دکمه‌های برتر بر اساس درآمد"""
    return await _show_top_buttons(chat_id, user_id, 'revenue', 'دکمه‌های پرسود')


async def handle_analytics_top_clicks(chat_id, user_id, data):
    """نمایش دکمه‌های برتر بر اساس کلیک"""
    return await _show_top_buttons(chat_id, user_id, 'clicks', 'دکمه‌های پربازدید')


async def handle_analytics_top_conversion(chat_id, user_id, data):
    """نمایش دکمه‌های برتر بر اساس نرخ تبدیل"""
    return await _show_top_buttons(chat_id, user_id, 'conversion_rate', 'دکمه‌های با بهترین نرخ تبدیل')


# ==================== آمار دوره‌ای ====================

async def handle_analytics_period(chat_id, user_id):
    """
    نمایش آمار درآمد در ۳۰ روز اخیر با قابلیت فیلتر
    """
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        # دریافت فیلترهای کاربر
        user_filters = user_states.get(user_id, {}).get("analytics_filters", {})
        start_date = user_filters.get('start_date')
        end_date = user_filters.get('end_date')
        button_id = user_filters.get('button_id')
        
        if start_date and end_date:
            period_stats = get_revenue_by_period(
                start_date=start_date,
                end_date=end_date,
                button_id=button_id
            )
        else:
            period_stats = get_revenue_by_period(
                days=30,
                button_id=button_id
            )
        
        if not period_stats:
            await send_message(
                chat_id,
                "📈 **آمار دوره‌ای**\n\n"
                "هیچ داده‌ای برای این دوره یافت نشد.",
                {
                    "inline_keyboard": [
                        [{"text": "🎯 تنظیم فیلترها", "callback_data": "admin_analytics_filters"}],
                        [{"text": "🔙 برگشت", "callback_data": "admin_analytics"}]
                    ]
                }
            )
            return True
        
        msg = "📈 **آمار دوره‌ای**\n\n"
        
        if start_date or end_date:
            msg += f"📅 بازه: {start_date or 'از ابتدا'} تا {end_date or 'تا امروز'}\n"
        else:
            msg += "📅 ۳۰ روز اخیر\n"
        
        if button_id:
            btn = get_button_by_id(button_id)
            msg += f"🔘 سرویس: {btn['name'] if btn else 'همه'}\n"
        
        msg += "\n"
        
        # محاسبه مجموع
        total_revenue = sum(d.get('revenue', 0) for d in period_stats)
        total_orders = sum(d.get('orders', 0) for d in period_stats)
        
        msg += f"📊 **جمع کل:**\n"
        msg += f"  • درآمد کل: {format_number(total_revenue)} ریال\n"
        msg += f"  • تعداد سفارش: {format_number(total_orders)}\n"
        
        days = len(period_stats)
        if days > 0:
            msg += f"  • میانگین روزانه: {format_number(total_revenue / days)} ریال\n\n"
        
        # نمایش ۱۰ روز اخیر
        msg += "📅 **۱۰ روز اخیر:**\n"
        for day in period_stats[:10]:
            date = day.get('date', '')
            orders = day.get('orders', 0)
            revenue = day.get('revenue', 0)
            if orders > 0 or revenue > 0:
                msg += f"  • {date}: {format_number(revenue)} ریال ({orders} سفارش)\n"
        
        if len(period_stats) > 10:
            msg += f"\n... و {len(period_stats) - 10} روز دیگر"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🎯 تنظیم فیلترها", "callback_data": "admin_analytics_filters"}],
                [{"text": "📊 مشاهده‌ی جزئیات بیشتر", "callback_data": "admin_analytics_buttons"}],
                [{"text": "🔙 برگشت به منوی آمار", "callback_data": "admin_analytics"}]
            ]
        }
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_period: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش آمار دوره‌ای.")
        return True


# ==================== کاربران برتر ====================

async def handle_analytics_top_users(chat_id, user_id):
    """
    نمایش کاربرانی که بیشترین سفارش یا بیشترین مبلغ پرداختی را داشته‌اند
    """
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        top_users = get_top_users(limit=10)
        
        if not top_users:
            await send_message(
                chat_id,
                "👥 **کاربران برتر**\n\n"
                "هنوز هیچ کاربری سفارش پرداخت‌شده‌ای ثبت نکرده است.",
                {
                    "inline_keyboard": [
                        [{"text": "🔙 برگشت", "callback_data": "admin_analytics"}]
                    ]
                }
            )
            return True
        
        msg = "👥 **کاربران برتر (بر اساس مبلغ پرداختی)**\n\n"
        msg += "رتبه | شناسه کاربر | تعداد سفارش | مبلغ کل\n"
        msg += "─" * 40 + "\n"
        
        for i, user in enumerate(top_users, 1):
            user_id_val = user.get('user_id', 'نامشخص')
            order_count = user.get('order_count', 0)
            total_spent = user.get('total_spent', 0)
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            msg += f"{medal} {user_id_val}: {order_count} سفارش | {format_number(total_spent)} ریال\n"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "👥 مدیریت کاربران", "callback_data": "admin_users"}],
                [{"text": "🔙 برگشت به منوی آمار", "callback_data": "admin_analytics"}]
            ]
        }
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_top_users: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش کاربران برتر.")
        return True


# ==================== فیلترهای پیشرفته ====================

async def handle_analytics_filters(chat_id, user_id):
    """
    نمایش منوی فیلترهای پیشرفته برای آمار
    """
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_filters = user_states.get(user_id, {}).get("analytics_filters", {})
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "📅 تنظیم بازه زمانی", "callback_data": "admin_analytics_filter_period"}],
                [{"text": "🔘 تنظیم سرویس", "callback_data": "admin_analytics_filter_service"}],
                [{"text": "✅ اعمال فیلترها", "callback_data": "admin_analytics_apply_filters"}],
                [{"text": "❌ پاک کردن فیلترها", "callback_data": "admin_analytics_clear_filters"}],
                [{"text": "🔙 برگشت به منوی آمار", "callback_data": "admin_analytics"}]
            ]
        }
        
        # نمایش خلاصه فیلترها
        period = user_filters.get('period', 'last_30_days')
        period_labels = {
            'today': 'امروز',
            'yesterday': 'دیروز',
            'last_7_days': '۷ روز اخیر',
            'last_30_days': '۳۰ روز اخیر',
            'last_90_days': '۹۰ روز اخیر',
            'this_month': 'این ماه',
            'last_month': 'ماه گذشته',
            'custom': 'سفارشی'
        }
        
        button_id = user_filters.get('button_id')
        service_text = "همه"
        if button_id:
            btn = get_button_by_id(button_id)
            service_text = btn['name'] if btn else f"سرویس {button_id}"
        
        msg = (
            f"🎯 **فیلترهای پیشرفته آمار**\n\n"
            f"📌 **فیلترهای فعال:**\n"
            f"  • بازه زمانی: {period_labels.get(period, period)}\n"
            f"  • سرویس: {service_text}\n"
        )
        
        if user_filters.get('start_date') or user_filters.get('end_date'):
            msg += f"  • تاریخ سفارشی: {user_filters.get('start_date', '...')} تا {user_filters.get('end_date', '...')}\n"
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_filters: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش فیلترها.")
        return True


async def handle_analytics_filter_period(chat_id, user_id, data):
    """نمایش انتخاب بازه زمانی"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_filters = user_states.get(user_id, {}).get("analytics_filters", {})
        current_period = user_filters.get('period', 'last_30_days')
        
        await send_message(
            chat_id,
            "📅 **انتخاب بازه زمانی**\n\n"
            "لطفاً بازه زمانی مورد نظر را انتخاب کنید:",
            analytics_filter_period_keyboard(current_period)
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_filter_period: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش بازه زمانی.")
        return True


async def handle_analytics_period_select(chat_id, user_id, data):
    """انتخاب بازه زمانی"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        period = data.split("_")[-1]
        
        if user_id not in user_states:
            user_states[user_id] = {}
        if "analytics_filters" not in user_states[user_id]:
            user_states[user_id]["analytics_filters"] = {}
        
        user_states[user_id]["analytics_filters"]["period"] = period
        
        if period == 'custom':
            user_states[user_id]["analytics_state"] = "awaiting_start_date"
            await send_message(
                chat_id,
                "📅 **تاریخ سفارشی**\n\n"
                "لطفاً تاریخ شروع را به فرمت **YYYY-MM-DD** وارد کنید:\n"
                "(مثال: 2024-01-15)\n\n"
                "برای انصراف، /cancel را ارسال کنید."
            )
            return True
        
        # پاک کردن تاریخ‌های سفارشی
        user_states[user_id]["analytics_filters"].pop("start_date", None)
        user_states[user_id]["analytics_filters"].pop("end_date", None)
        
        await send_message(
            chat_id,
            f"✅ بازه زمانی به «{period}» تنظیم شد.\n\n"
            f"برای اعمال فیلترها، روی «اعمال فیلترها» کلیک کنید.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلترها", "callback_data": "admin_analytics_filters"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_period_select: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب بازه زمانی.")
        return True


async def handle_analytics_filter_service(chat_id, user_id, page=0):
    """نمایش انتخاب سرویس"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_filters = user_states.get(user_id, {}).get("analytics_filters", {})
        selected_service = user_filters.get('button_id')
        
        await send_message(
            chat_id,
            f"🔘 **انتخاب سرویس - صفحه {page + 1}**\n\n"
            "سرویس مورد نظر را انتخاب کنید:",
            analytics_filter_service_keyboard(selected_service, page)
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_filter_service: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب سرویس.")
        return True


async def handle_analytics_service_select(chat_id, user_id, data):
    """انتخاب سرویس برای فیلتر"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        button_id = int(data.split("_")[-1])
        
        if user_id not in user_states:
            user_states[user_id] = {}
        if "analytics_filters" not in user_states[user_id]:
            user_states[user_id]["analytics_filters"] = {}
        
        btn = get_button_by_id(button_id)
        service_name = btn['name'] if btn else f"سرویس {button_id}"
        
        user_states[user_id]["analytics_filters"]["button_id"] = button_id
        
        await send_message(
            chat_id,
            f"✅ سرویس «{service_name}» انتخاب شد.\n\n"
            f"برای اعمال فیلترها، روی «اعمال فیلترها» کلیک کنید.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلترها", "callback_data": "admin_analytics_filters"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_service_select for {button_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب سرویس.")
        return True


async def handle_analytics_service_page(chat_id, user_id, data):
    """صفحه‌بندی سرویس‌ها"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        page = int(data.split("_")[-1])
        await handle_analytics_filter_service(chat_id, user_id, page)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_service_page: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی.")
        return True


async def handle_analytics_apply_filters(chat_id, user_id):
    """اعمال فیلترها و نمایش نتایج"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_filters = user_states.get(user_id, {}).get("analytics_filters", {})
        
        # ساخت خلاصه فیلترها
        period = user_filters.get('period', 'last_30_days')
        period_labels = {
            'today': 'امروز',
            'yesterday': 'دیروز',
            'last_7_days': '۷ روز اخیر',
            'last_30_days': '۳۰ روز اخیر',
            'last_90_days': '۹۰ روز اخیر',
            'this_month': 'این ماه',
            'last_month': 'ماه گذشته',
            'custom': 'سفارشی'
        }
        
        button_id = user_filters.get('button_id')
        service_text = "همه"
        if button_id:
            btn = get_button_by_id(button_id)
            service_text = btn['name'] if btn else f"سرویس {button_id}"
        
        start_date = user_filters.get('start_date')
        end_date = user_filters.get('end_date')
        
        msg = "✅ **فیلترها اعمال شدند.**\n\n"
        msg += f"📌 **فیلترهای اعمال‌شده:**\n"
        msg += f"  • بازه زمانی: {period_labels.get(period, period)}\n"
        msg += f"  • سرویس: {service_text}\n"
        if start_date or end_date:
            msg += f"  • تاریخ سفارشی: {start_date or '...'} تا {end_date or '...'}\n"
        msg += "\nبرای مشاهده نتایج، از گزینه‌های زیر استفاده کنید:"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "📊 مشاهده داشبورد", "callback_data": "admin_analytics_dashboard"}],
                [{"text": "📈 مشاهده آمار دوره‌ای", "callback_data": "admin_analytics_period"}],
                [{"text": "🏆 مشاهده دکمه‌های برتر", "callback_data": "admin_analytics_top_buttons"}],
                [{"text": "🔙 برگشت به فیلترها", "callback_data": "admin_analytics_filters"}]
            ]
        }
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_apply_filters: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در اعمال فیلترها.")
        return True


async def handle_analytics_clear_filters(chat_id, user_id):
    """پاک کردن فیلترها"""
    try:
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if user_id in user_states:
            user_states[user_id]["analytics_filters"] = {}
            user_states[user_id].pop("analytics_state", None)
        
        await send_message(
            chat_id,
            "✅ همه فیلترها پاک شدند.\n\n"
            "حالا آمارها بدون فیلتر نمایش داده می‌شوند.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلترها", "callback_data": "admin_analytics_filters"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_clear_filters: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در پاک کردن فیلترها.")
        return True


# ==================== پردازش پیام‌های فیلتر تاریخ ====================

async def handle_analytics_date_message(chat_id, user_id, text):
    """پردازش پیام تاریخ سفارشی برای فیلتر"""
    try:
        from datetime import datetime
        
        state_info = user_states.get(user_id, {})
        analytics_state = state_info.get("analytics_state")
        
        if analytics_state == "awaiting_start_date":
            try:
                datetime.strptime(text, "%Y-%m-%d")
                user_states[user_id]["analytics_filters"]["start_date"] = text
                user_states[user_id]["analytics_state"] = "awaiting_end_date"
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
        
        if analytics_state == "awaiting_end_date":
            try:
                datetime.strptime(text, "%Y-%m-%d")
                user_states[user_id]["analytics_filters"]["end_date"] = text
                user_states[user_id]["analytics_filters"]["period"] = "custom"
                user_states[user_id].pop("analytics_state", None)
                await send_message(
                    chat_id,
                    f"✅ تاریخ سفارشی تنظیم شد.\n\n"
                    f"📅 از {user_states[user_id]['analytics_filters']['start_date']} تا {text}\n\n"
                    f"برای اعمال فیلترها، روی «اعمال فیلترها» کلیک کنید.",
                    {"inline_keyboard": [[{"text": "🔙 بازگشت به فیلترها", "callback_data": "admin_analytics_filters"}]]}
                )
                return True
            except ValueError:
                await send_message(chat_id, "❌ فرمت تاریخ نامعتبر. لطفاً به فرمت YYYY-MM-DD وارد کنید.")
                return True
        
        return False
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_analytics_date_message: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در پردازش تاریخ.")
        return True


__all__ = [
    'handle_analytics',
    'handle_analytics_dashboard',
    'handle_analytics_buttons_list',
    'handle_analytics_button_stats',
    'handle_analytics_button_daily',
    'handle_analytics_top_buttons',
    'handle_analytics_top_orders',
    'handle_analytics_top_revenue',
    'handle_analytics_top_clicks',
    'handle_analytics_top_conversion',
    'handle_analytics_period',
    'handle_analytics_top_users',
    'handle_analytics_filters',
    'handle_analytics_filter_period',
    'handle_analytics_period_select',
    'handle_analytics_filter_service',
    'handle_analytics_service_select',
    'handle_analytics_service_page',
    'handle_analytics_apply_filters',
    'handle_analytics_clear_filters',
    'handle_analytics_date_message',
]