# admin_panel/chart_routes.py
# مسیرهای جدید نمایش نمودارهای گرافیکی در پنل مدیریت

from .router import route, extract_params
from .charts import (
    ChartManager,
    create_revenue_chart,
    create_orders_pie_chart,
    create_conversion_chart,
    create_combined_dashboard,
    prepare_revenue_data,
    prepare_orders_by_service,
    prepare_conversion_data,
)
from core import send_message, send_photo, OWNER_ID
from database import get_dynamic_orders, get_all_buttons, get_dashboard_stats
from logger_config import logger
import os


# ============================================================
# تابع کمکی
# ============================================================

def _is_owner(user_id: int) -> bool:
    """بررسی آیا کاربر OWNER_ID است"""
    return user_id == OWNER_ID


def _get_chart_filename(chart_type: str, suffix: str = "") -> str:
    """تولید نام فایل نمودار"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if suffix:
        return f"chart_{chart_type}_{suffix}_{timestamp}.png"
    return f"chart_{chart_type}_{timestamp}.png"


# ============================================================
# روت‌های نمایش نمودارها
# ============================================================

@route("admin_chart_revenue")
async def admin_chart_revenue(update):
    """نمایش نمودار درآمد روزانه (admin_chart_revenue)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        await send_message(chat_id, "⏳ در حال تولید نمودار درآمد... لطفاً صبر کنید.")
        
        # دریافت داده‌ها
        orders = get_dynamic_orders()
        if not orders:
            await send_message(chat_id, "📊 هیچ سفارشی برای نمایش وجود ندارد.")
            return True
        
        # تولید نمودار
        chart_manager = ChartManager()
        filepath = chart_manager.create_revenue_chart(orders, days=30, title="درآمد روزانه (۳۰ روز اخیر)")
        
        if filepath and os.path.exists(filepath):
            await send_photo(chat_id, file_path=filepath, caption="📊 **نمودار درآمد روزانه**\n۳۰ روز اخیر")
            # حذف فایل بعد از ارسال
            try:
                os.remove(filepath)
            except:
                pass
        else:
            await send_message(chat_id, "❌ خطا در تولید نمودار درآمد.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in admin_chart_revenue: {e}", exc_info=True)
        await send_message(chat_id, f"❌ خطا در تولید نمودار: {str(e)}")
        return True


@route("admin_chart_orders_pie")
async def admin_chart_orders_pie(update):
    """نمایش نمودار دایره‌ای سفارشات (admin_chart_orders_pie)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        await send_message(chat_id, "⏳ در حال تولید نمودار سفارشات... لطفاً صبر کنید.")
        
        # دریافت داده‌ها
        orders = get_dynamic_orders()
        if not orders:
            await send_message(chat_id, "📊 هیچ سفارشی برای نمایش وجود ندارد.")
            return True
        
        # تولید نمودار
        chart_manager = ChartManager()
        filepath = chart_manager.create_orders_pie(orders, title="سفارشات به تفکیک سرویس")
        
        if filepath and os.path.exists(filepath):
            await send_photo(chat_id, file_path=filepath, caption="📊 **نمودار سفارشات به تفکیک سرویس**")
            try:
                os.remove(filepath)
            except:
                pass
        else:
            await send_message(chat_id, "❌ خطا در تولید نمودار سفارشات.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in admin_chart_orders_pie: {e}", exc_info=True)
        await send_message(chat_id, f"❌ خطا در تولید نمودار: {str(e)}")
        return True


@route("admin_chart_conversion")
async def admin_chart_conversion(update):
    """نمایش نمودار نرخ تبدیل دکمه‌ها (admin_chart_conversion)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        await send_message(chat_id, "⏳ در حال تولید نمودار نرخ تبدیل... لطفاً صبر کنید.")
        
        # دریافت داده‌ها
        buttons = get_all_buttons()
        if not buttons:
            await send_message(chat_id, "📊 هیچ دکمه‌ای برای نمایش وجود ندارد.")
            return True
        
        # تولید نمودار
        chart_manager = ChartManager()
        filepath = chart_manager.create_conversion_chart(buttons, title="نرخ تبدیل دکمه‌ها")
        
        if filepath and os.path.exists(filepath):
            await send_photo(chat_id, file_path=filepath, caption="📊 **نمودار نرخ تبدیل دکمه‌ها**")
            try:
                os.remove(filepath)
            except:
                pass
        else:
            await send_message(chat_id, "❌ خطا در تولید نمودار نرخ تبدیل.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in admin_chart_conversion: {e}", exc_info=True)
        await send_message(chat_id, f"❌ خطا در تولید نمودار: {str(e)}")
        return True


@route("admin_chart_dashboard")
async def admin_chart_dashboard(update):
    """نمایش داشبورد ترکیبی با چندین نمودار (admin_chart_dashboard)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        await send_message(chat_id, "⏳ در حال تولید داشبورد تحلیلی... لطفاً صبر کنید.")
        
        # دریافت داده‌ها
        orders = get_dynamic_orders()
        buttons = get_all_buttons()
        
        if not orders and not buttons:
            await send_message(chat_id, "📊 هیچ داده‌ای برای نمایش وجود ندارد.")
            return True
        
        # تولید داشبورد
        chart_manager = ChartManager()
        filepath = chart_manager.create_combined_dashboard(orders or [], buttons or [], days=30)
        
        if filepath and os.path.exists(filepath):
            await send_photo(chat_id, file_path=filepath, caption="📊 **داشبورد تحلیلی جامع**\nنمایش درآمد، سفارشات، نرخ تبدیل و فعالیت کاربران")
            try:
                os.remove(filepath)
            except:
                pass
        else:
            await send_message(chat_id, "❌ خطا در تولید داشبورد تحلیلی.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in admin_chart_dashboard: {e}", exc_info=True)
        await send_message(chat_id, f"❌ خطا در تولید داشبورد: {str(e)}")
        return True


@route("admin_chart_custom")
async def admin_chart_custom(update):
    """نمایش نمودار سفارشی با پارامترهای انتخاب‌شده (admin_chart_custom)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        # این بخش می‌تواند با پارامترهای مختلف توسعه یابد
        # فعلاً یک منوی ساده نمایش می‌دهد
        keyboard = {
            "inline_keyboard": [
                [{"text": "📊 درآمد روزانه", "callback_data": "admin_chart_revenue"}],
                [{"text": "🥧 سفارشات به تفکیک سرویس", "callback_data": "admin_chart_orders_pie"}],
                [{"text": "📈 نرخ تبدیل دکمه‌ها", "callback_data": "admin_chart_conversion"}],
                [{"text": "📊 داشبورد جامع", "callback_data": "admin_chart_dashboard"}],
                [{"text": "🔙 برگشت به منوی آمار", "callback_data": "admin_analytics"}]
            ]
        }
        
        await send_message(
            chat_id,
            "📊 **نمودارهای تحلیلی**\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:\n\n"
            "📌 **نکته:** تولید نمودارها ممکن است چند ثانیه طول بکشد.",
            keyboard
        )
        return True
        
    except Exception as e:
        logger.error(f"Error in admin_chart_custom: {e}", exc_info=True)
        await send_message(chat_id, f"❌ خطا: {str(e)}")
        return True


# ============================================================
# روت‌های کمکی برای دریافت داده‌های نمودارها
# ============================================================

@route("admin_chart_data_revenue")
async def admin_chart_data_revenue(update):
    """دریافت داده‌های خام درآمد برای نمودار (admin_chart_data_revenue)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        orders = get_dynamic_orders()
        data = prepare_revenue_data(orders, 30)
        
        if not data:
            await send_message(chat_id, "📊 هیچ داده‌ای برای نمایش وجود ندارد.")
            return True
        
        # ساخت پیام با داده‌ها
        msg = "📊 **داده‌های درآمد روزانه (۳۰ روز اخیر)**\n\n"
        for item in data[:20]:  # نمایش ۲۰ روز اول
            msg += f"📅 {item['date']}: {item['revenue']:,} ریال\n"
        
        if len(data) > 20:
            msg += f"\n... و {len(data) - 20} روز دیگر"
        
        await send_message(chat_id, msg)
        return True
        
    except Exception as e:
        logger.error(f"Error in admin_chart_data_revenue: {e}", exc_info=True)
        await send_message(chat_id, f"❌ خطا: {str(e)}")
        return True


@route("admin_chart_data_orders")
async def admin_chart_data_orders(update):
    """دریافت داده‌های خام سفارشات برای نمودار (admin_chart_data_orders)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        orders = get_dynamic_orders()
        data = prepare_orders_by_service(orders)
        
        if not data:
            await send_message(chat_id, "📊 هیچ داده‌ای برای نمایش وجود ندارد.")
            return True
        
        msg = "📊 **داده‌های سفارشات به تفکیک سرویس**\n\n"
        for item in data:
            msg += f"🔘 {item['service_name']}: {item['count']} سفارش\n"
        
        await send_message(chat_id, msg)
        return True
        
    except Exception as e:
        logger.error(f"Error in admin_chart_data_orders: {e}", exc_info=True)
        await send_message(chat_id, f"❌ خطا: {str(e)}")
        return True


# ============================================================
# روت برای پاکسازی نمودارهای قدیمی
# ============================================================

@route("admin_chart_cleanup")
async def admin_chart_cleanup(update):
    """پاکسازی نمودارهای قدیمی (admin_chart_cleanup)"""
    chat_id, user_id, data = extract_params(update)
    
    if not _is_owner(user_id):
        await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
        return True
    
    try:
        from .charts import CHARTS_DIR, clean_old_charts
        
        if not os.path.exists(CHARTS_DIR):
            await send_message(chat_id, "📁 پوشه‌ی نمودارها وجود ندارد.")
            return True
        
        # شمارش فایل‌ها قبل از پاکسازی
        files_before = len([f for f in os.listdir(CHARTS_DIR) if f.endswith('.png')])
        
        # پاکسازی نمودارهای قدیمی‌تر از ۱ روز
        clean_old_charts(days=1)
        
        # شمارش فایل‌ها بعد از پاکسازی
        files_after = len([f for f in os.listdir(CHARTS_DIR) if f.endswith('.png')])
        
        deleted = files_before - files_after
        await send_message(
            chat_id,
            f"✅ پاکسازی نمودارها انجام شد.\n"
            f"🗑️ تعداد حذف‌شده: {deleted}\n"
            f"📁 تعداد باقی‌مانده: {files_after}"
        )
        return True
        
    except Exception as e:
        logger.error(f"Error in admin_chart_cleanup: {e}", exc_info=True)
        await send_message(chat_id, f"❌ خطا در پاکسازی: {str(e)}")
        return True


# ============================================================
# صادر کردن روت‌ها
# ============================================================

__all__ = [
    'admin_chart_revenue',
    'admin_chart_orders_pie',
    'admin_chart_conversion',
    'admin_chart_dashboard',
    'admin_chart_custom',
    'admin_chart_data_revenue',
    'admin_chart_data_orders',
    'admin_chart_cleanup',
]