# admin_panel/charts.py
# تولید نمودارهای گرافیکی برای داشبورد تحلیلی

import os
import io
import tempfile
import matplotlib
matplotlib.use('Agg')  # استفاده از backend غیرتعاملی برای محیط سرور
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from logger_config import logger
from config import config


# ============================================================
# تنظیمات
# ============================================================

# تنظیمات فونت برای پشتیبانی از فارسی
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.unicode_minus'] = False

# پالت رنگ‌ها
COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
    '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA',
    '#F1948A', '#85929E', '#73C6B6', '#E59866', '#AF7AC5'
]

# پوشه موقت برای ذخیره نمودارها
CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'admin_panel', 'charts')


def ensure_charts_dir():
    """ایجاد پوشه نمودارها در صورت عدم وجود"""
    if not os.path.exists(CHARTS_DIR):
        os.makedirs(CHARTS_DIR)
    return CHARTS_DIR


def clean_old_charts(days: int = 1):
    """حذف نمودارهای قدیمی از پوشه"""
    try:
        cutoff = datetime.now() - timedelta(days=days)
        for filename in os.listdir(CHARTS_DIR):
            filepath = os.path.join(CHARTS_DIR, filename)
            if os.path.isfile(filepath):
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    os.remove(filepath)
                    logger.debug(f"Removed old chart: {filename}")
    except Exception as e:
        logger.warning(f"Error cleaning old charts: {e}")


def _save_chart(fig, filename: str = None) -> str:
    """
    ذخیره نمودار در پوشه و بازگرداندن مسیر فایل
    
    پارامترها:
        fig: شیء Figure matplotlib
        filename: نام فایل (اختیاری)
    
    بازگشت: مسیر فایل ذخیره‌شده
    """
    ensure_charts_dir()
    clean_old_charts()
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"chart_{timestamp}.png"
    
    filepath = os.path.join(CHARTS_DIR, filename)
    
    try:
        fig.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        logger.debug(f"Chart saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving chart: {e}")
        plt.close(fig)
        raise


def _get_chart_bytes(fig) -> bytes:
    """تبدیل نمودار به bytes برای ارسال مستقیم"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()


# ============================================================
# توابع تولید نمودار
# ============================================================

def create_revenue_chart(data: List[Dict], title: str = "درآمد روزانه", save: bool = True) -> Tuple[Optional[str], Optional[bytes]]:
    """
    ایجاد نمودار خطی درآمد روزانه
    
    پارامترها:
        data: لیست دیکشنری‌های شامل date و revenue
        title: عنوان نمودار
        save: ذخیره در فایل یا بازگرداندن bytes
    
    بازگشت: (مسیر فایل یا None, bytes یا None)
    """
    try:
        if not data:
            return None, None
        
        dates = [item.get('date') for item in data]
        revenues = [float(item.get('revenue', 0)) for item in data]
        
        # تبدیل تاریخ‌ها به datetime
        date_objects = []
        for d in dates:
            if isinstance(d, str):
                try:
                    date_objects.append(datetime.strptime(d, "%Y-%m-%d"))
                except:
                    date_objects.append(datetime.now())
            else:
                date_objects.append(d)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(date_objects, revenues, marker='o', linewidth=2, color='#2E86C1', markersize=6)
        ax.fill_between(date_objects, revenues, alpha=0.2, color='#2E86C1')
        
        # فرمت محور x
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.xticks(rotation=45)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('تاریخ', fontsize=12)
        ax.set_ylabel('درآمد (ریال)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # نمایش مقادیر روی نقاط
        for i, (x, y) in enumerate(zip(date_objects, revenues)):
            if y > 0:
                ax.annotate(f'{int(y):,}', (x, y), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8)
        
        fig.tight_layout()
        
        if save:
            return _save_chart(fig), None
        else:
            return None, _get_chart_bytes(fig)
        
    except Exception as e:
        logger.error(f"Error creating revenue chart: {e}")
        return None, None


def create_orders_pie_chart(data: List[Dict], title: str = "سفارشات به تفکیک سرویس", save: bool = True) -> Tuple[Optional[str], Optional[bytes]]:
    """
    ایجاد نمودار دایره‌ای سفارشات به تفکیک سرویس
    
    پارامترها:
        data: لیست دیکشنری‌های شامل service_name و count
        title: عنوان نمودار
        save: ذخیره در فایل یا بازگرداندن bytes
    
    بازگشت: (مسیر فایل یا None, bytes یا None)
    """
    try:
        if not data:
            return None, None
        
        # حذف سرویس‌های با تعداد صفر
        filtered = [item for item in data if item.get('count', 0) > 0]
        if not filtered:
            return None, None
        
        labels = [item.get('service_name', 'نامشخص') for item in filtered]
        values = [item.get('count', 0) for item in filtered]
        
        # محدودیت برای نمایش (اگر بیشتر از ۱۰ سرویس باشد، بقیه در "سایر" جمع می‌شوند)
        if len(labels) > 10:
            sorted_data = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
            top_labels = [item[0] for item in sorted_data[:9]]
            top_values = [item[1] for item in sorted_data[:9]]
            other_sum = sum(item[1] for item in sorted_data[9:])
            labels = top_labels + ['سایر']
            values = top_values + [other_sum]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # استفاده از رنگ‌های متنوع
        colors = COLORS[:len(labels)]
        
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 10}
        )
        
        # تنظیم فونت درصدها
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        fig.tight_layout()
        
        if save:
            return _save_chart(fig), None
        else:
            return None, _get_chart_bytes(fig)
        
    except Exception as e:
        logger.error(f"Error creating pie chart: {e}")
        return None, None


def create_conversion_chart(data: List[Dict], title: str = "نرخ تبدیل دکمه‌ها", save: bool = True) -> Tuple[Optional[str], Optional[bytes]]:
    """
    ایجاد نمودار میل‌ای نرخ تبدیل دکمه‌ها
    
    پارامترها:
        data: لیست دیکشنری‌های شامل button_name و conversion_rate
        title: عنوان نمودار
        save: ذخیره در فایل یا بازگرداندن bytes
    
    بازگشت: (مسیر فایل یا None, bytes یا None)
    """
    try:
        if not data:
            return None, None
        
        # حذف دکمه‌های با نرخ صفر
        filtered = [item for item in data if item.get('conversion_rate', 0) > 0]
        if not filtered:
            return None, None
        
        # مرتب‌سازی بر اساس نرخ تبدیل (نزولی)
        sorted_data = sorted(filtered, key=lambda x: x.get('conversion_rate', 0), reverse=True)
        
        # محدودیت برای نمایش
        if len(sorted_data) > 15:
            sorted_data = sorted_data[:15]
        
        names = [item.get('button_name', 'نامشخص') for item in sorted_data]
        rates = [item.get('conversion_rate', 0) for item in sorted_data]
        
        # کوتاه کردن نام‌های بلند
        names = [name[:20] + '...' if len(name) > 20 else name for name in names]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colors = ['#27AE60' if rate >= 30 else '#F39C12' if rate >= 10 else '#E74C3C' for rate in rates]
        
        bars = ax.barh(names, rates, color=colors, edgecolor='white', linewidth=1)
        
        # نمایش مقادیر روی میله‌ها
        for bar, rate in zip(bars, rates):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                   f'{rate:.1f}%', va='center', fontsize=9)
        
        ax.set_xlabel('نرخ تبدیل (%)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.axvline(x=30, color='green', linestyle='--', alpha=0.5, label='هدف (30%)')
        ax.axvline(x=10, color='orange', linestyle='--', alpha=0.5, label='حد متوسط (10%)')
        ax.legend(loc='lower right')
        
        fig.tight_layout()
        
        if save:
            return _save_chart(fig), None
        else:
            return None, _get_chart_bytes(fig)
        
    except Exception as e:
        logger.error(f"Error creating conversion chart: {e}")
        return None, None


def create_user_activity_chart(data: List[Dict], title: str = "فعالیت کاربران", save: bool = True) -> Tuple[Optional[str], Optional[bytes]]:
    """
    ایجاد نمودار فعالیت کاربران (تعداد کاربران فعال روزانه)
    
    پارامترها:
        data: لیست دیکشنری‌های شامل date و active_users
        title: عنوان نمودار
        save: ذخیره در فایل یا بازگرداندن bytes
    
    بازگشت: (مسیر فایل یا None, bytes یا None)
    """
    try:
        if not data:
            return None, None
        
        dates = [item.get('date') for item in data]
        users = [int(item.get('active_users', 0)) for item in data]
        
        # تبدیل تاریخ‌ها به datetime
        date_objects = []
        for d in dates:
            if isinstance(d, str):
                try:
                    date_objects.append(datetime.strptime(d, "%Y-%m-%d"))
                except:
                    date_objects.append(datetime.now())
            else:
                date_objects.append(d)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.bar(date_objects, users, color='#3498DB', alpha=0.7, edgecolor='#2980B9', linewidth=1)
        ax.plot(date_objects, users, marker='o', color='#E74C3C', linewidth=2, markersize=4, alpha=0.8)
        
        # فرمت محور x
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.xticks(rotation=45)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('تاریخ', fontsize=12)
        ax.set_ylabel('تعداد کاربران فعال', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # نمایش میانگین
        avg_users = sum(users) / len(users) if users else 0
        ax.axhline(y=avg_users, color='orange', linestyle='--', alpha=0.7, label=f'میانگین: {avg_users:.0f}')
        ax.legend(loc='upper right')
        
        fig.tight_layout()
        
        if save:
            return _save_chart(fig), None
        else:
            return None, _get_chart_bytes(fig)
        
    except Exception as e:
        logger.error(f"Error creating user activity chart: {e}")
        return None, None


def create_combined_dashboard(stats: Dict) -> Tuple[Optional[str], Optional[bytes]]:
    """
    ایجاد داشبورد ترکیبی با چندین نمودار
    
    پارامترها:
        stats: دیکشنری آماری شامل revenue_data, orders_data, conversion_data
    
    بازگشت: (مسیر فایل یا None, bytes یا None)
    """
    try:
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle('📊 داشبورد تحلیلی ربات', fontsize=18, fontweight='bold')
        
        # ۱. نمودار درآمد (بالا سمت چپ)
        ax1 = fig.add_subplot(2, 2, 1)
        revenue_data = stats.get('revenue_data', [])
        if revenue_data:
            dates = [item.get('date') for item in revenue_data]
            revenues = [float(item.get('revenue', 0)) for item in revenue_data]
            date_objects = []
            for d in dates:
                if isinstance(d, str):
                    try:
                        date_objects.append(datetime.strptime(d, "%Y-%m-%d"))
                    except:
                        date_objects.append(datetime.now())
                else:
                    date_objects.append(d)
            
            ax1.plot(date_objects, revenues, marker='o', linewidth=2, color='#2E86C1', markersize=4)
            ax1.fill_between(date_objects, revenues, alpha=0.2, color='#2E86C1')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//7)))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=30)
            ax1.set_title('درآمد روزانه', fontsize=12, fontweight='bold')
            ax1.set_ylabel('ریال')
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(0.5, 0.5, 'داده‌ای موجود نیست', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('درآمد روزانه', fontsize=12, fontweight='bold')
        
        # ۲. نمودار دایره‌ای (بالا سمت راست)
        ax2 = fig.add_subplot(2, 2, 2)
        orders_data = stats.get('orders_data', [])
        if orders_data:
            filtered = [item for item in orders_data if item.get('count', 0) > 0]
            if filtered:
                labels = [item.get('service_name', 'نامشخص') for item in filtered[:7]]
                values = [item.get('count', 0) for item in filtered[:7]]
                if len(filtered) > 7:
                    other_sum = sum(item.get('count', 0) for item in filtered[7:])
                    labels.append('سایر')
                    values.append(other_sum)
                
                colors = COLORS[:len(labels)]
                ax2.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax2.set_title('سفارشات به تفکیک سرویس', fontsize=12, fontweight='bold')
            else:
                ax2.text(0.5, 0.5, 'داده‌ای موجود نیست', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('سفارشات به تفکیک سرویس', fontsize=12, fontweight='bold')
        else:
            ax2.text(0.5, 0.5, 'داده‌ای موجود نیست', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('سفارشات به تفکیک سرویس', fontsize=12, fontweight='bold')
        
        # ۳. نمودار نرخ تبدیل (پایین سمت چپ)
        ax3 = fig.add_subplot(2, 2, 3)
        conversion_data = stats.get('conversion_data', [])
        if conversion_data:
            filtered = [item for item in conversion_data if item.get('conversion_rate', 0) > 0]
            if filtered:
                sorted_data = sorted(filtered, key=lambda x: x.get('conversion_rate', 0), reverse=True)[:10]
                names = [item.get('button_name', 'نامشخص')[:15] + '...' if len(item.get('button_name', '')) > 15 else item.get('button_name', 'نامشخص') for item in sorted_data]
                rates = [item.get('conversion_rate', 0) for item in sorted_data]
                
                colors = ['#27AE60' if rate >= 30 else '#F39C12' if rate >= 10 else '#E74C3C' for rate in rates]
                ax3.barh(names, rates, color=colors, edgecolor='white', linewidth=1)
                for i, (bar, rate) in enumerate(zip(ax3.patches, rates)):
                    ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                            f'{rate:.1f}%', va='center', fontsize=8)
                ax3.set_xlabel('نرخ تبدیل (%)')
                ax3.set_title('نرخ تبدیل دکمه‌ها (۱۰ مورد برتر)', fontsize=12, fontweight='bold')
                ax3.grid(True, alpha=0.3, axis='x')
            else:
                ax3.text(0.5, 0.5, 'داده‌ای موجود نیست', ha='center', va='center', transform=ax3.transAxes)
                ax3.set_title('نرخ تبدیل دکمه‌ها', fontsize=12, fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'داده‌ای موجود نیست', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('نرخ تبدیل دکمه‌ها', fontsize=12, fontweight='bold')
        
        # ۴. نمودار فعالیت کاربران (پایین سمت راست)
        ax4 = fig.add_subplot(2, 2, 4)
        user_data = stats.get('user_data', [])
        if user_data:
            dates = [item.get('date') for item in user_data]
            users = [int(item.get('active_users', 0)) for item in user_data]
            date_objects = []
            for d in dates:
                if isinstance(d, str):
                    try:
                        date_objects.append(datetime.strptime(d, "%Y-%m-%d"))
                    except:
                        date_objects.append(datetime.now())
                else:
                    date_objects.append(d)
            
            ax4.bar(date_objects, users, color='#3498DB', alpha=0.7, edgecolor='#2980B9', linewidth=1)
            ax4.plot(date_objects, users, marker='o', color='#E74C3C', linewidth=2, markersize=4, alpha=0.8)
            ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax4.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//7)))
            plt.setp(ax4.xaxis.get_majorticklabels(), rotation=30)
            ax4.set_title('کاربران فعال روزانه', fontsize=12, fontweight='bold')
            ax4.set_ylabel('تعداد کاربران')
            ax4.grid(True, alpha=0.3, axis='y')
            
            avg_users = sum(users) / len(users) if users else 0
            ax4.axhline(y=avg_users, color='orange', linestyle='--', alpha=0.7, label=f'میانگین: {avg_users:.0f}')
            ax4.legend(loc='upper right', fontsize=8)
        else:
            ax4.text(0.5, 0.5, 'داده‌ای موجود نیست', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('کاربران فعال روزانه', fontsize=12, fontweight='bold')
        
        fig.tight_layout()
        fig.subplots_adjust(top=0.93)
        
        return _save_chart(fig), None
        
    except Exception as e:
        logger.error(f"Error creating combined dashboard: {e}")
        return None, None


# ============================================================
# توابع کاربردی برای استفاده در پنل مدیریت
# ============================================================

def prepare_revenue_data(orders: List[Dict], days: int = 30) -> List[Dict]:
    """
    آماده‌سازی داده‌های درآمد از لیست سفارشات
    
    پارامترها:
        orders: لیست سفارشات
        days: تعداد روزهای اخیر
    
    بازگشت: لیست دیکشنری‌های تاریخ و درآمد
    """
    from collections import defaultdict
    
    revenue_by_date = defaultdict(int)
    cutoff = datetime.now() - timedelta(days=days)
    
    for order in orders:
        created_at = order.get('created_at')
        if not created_at:
            continue
        
        try:
            if isinstance(created_at, str):
                date_obj = datetime.strptime(created_at[:10], "%Y-%m-%d")
            else:
                date_obj = created_at
        except:
            continue
        
        if date_obj < cutoff:
            continue
        
        amount = order.get('payment_amount') or 0
        if amount > 0:
            date_str = date_obj.strftime("%Y-%m-%d")
            revenue_by_date[date_str] += amount
    
    # تبدیل به لیست مرتب
    result = []
    for date_str, revenue in sorted(revenue_by_date.items()):
        result.append({'date': date_str, 'revenue': revenue})
    
    return result


def prepare_orders_by_service(orders: List[Dict], limit: int = 10) -> List[Dict]:
    """
    آماده‌سازی داده‌های سفارشات به تفکیک سرویس
    
    پارامترها:
        orders: لیست سفارشات
        limit: حداکثر تعداد سرویس‌ها
    
    بازگشت: لیست دیکشنری‌های سرویس و تعداد
    """
    from collections import defaultdict
    from database import get_button_by_id
    
    service_counts = defaultdict(int)
    
    for order in orders:
        button_id = order.get('button_id')
        if button_id:
            service_counts[button_id] += 1
    
    # دریافت نام سرویس‌ها
    result = []
    for button_id, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
        btn = get_button_by_id(button_id)
        name = btn['name'] if btn else f"سرویس {button_id}"
        result.append({'service_name': name, 'count': count})
    
    return result


def prepare_conversion_data(buttons: List[Dict]) -> List[Dict]:
    """
    آماده‌سازی داده‌های نرخ تبدیل برای دکمه‌ها
    
    پارامترها:
        buttons: لیست دکمه‌ها
    
    بازگشت: لیست دیکشنری‌های دکمه و نرخ تبدیل
    """
    from database import get_button_stats
    
    result = []
    for btn in buttons:
        stats = get_button_stats(btn['id'])
        if stats.get('clicks', 0) > 0:
            result.append({
                'button_name': btn['name'],
                'conversion_rate': stats.get('conversion_rate', 0)
            })
    
    return result


# ============================================================
# کلاس ChartManager برای مدیریت یکپارچه
# ============================================================

class ChartManager:
    """مدیریت یکپارچه نمودارها"""
    
    def __init__(self):
        ensure_charts_dir()
    
    def create_revenue_chart(self, orders: List[Dict], days: int = 30, title: str = "درآمد روزانه") -> Optional[str]:
        """ایجاد نمودار درآمد از لیست سفارشات"""
        data = prepare_revenue_data(orders, days)
        if not data:
            logger.warning("No revenue data available for chart")
            return None
        filepath, _ = create_revenue_chart(data, title, save=True)
        return filepath
    
    def create_orders_pie(self, orders: List[Dict], title: str = "سفارشات به تفکیک سرویس") -> Optional[str]:
        """ایجاد نمودار دایره‌ای سفارشات"""
        data = prepare_orders_by_service(orders)
        if not data:
            logger.warning("No order data available for pie chart")
            return None
        filepath, _ = create_orders_pie_chart(data, title, save=True)
        return filepath
    
    def create_conversion_chart(self, buttons: List[Dict], title: str = "نرخ تبدیل دکمه‌ها") -> Optional[str]:
        """ایجاد نمودار نرخ تبدیل"""
        data = prepare_conversion_data(buttons)
        if not data:
            logger.warning("No conversion data available for chart")
            return None
        filepath, _ = create_conversion_chart(data, title, save=True)
        return filepath
    
    def create_combined_dashboard(self, orders: List[Dict], buttons: List[Dict], days: int = 30) -> Optional[str]:
        """ایجاد داشبورد ترکیبی"""
        stats = {
            'revenue_data': prepare_revenue_data(orders, days),
            'orders_data': prepare_orders_by_service(orders),
            'conversion_data': prepare_conversion_data(buttons),
            'user_data': []  # برای آینده
        }
        filepath, _ = create_combined_dashboard(stats)
        return filepath


__all__ = [
    # توابع اصلی
    'create_revenue_chart',
    'create_orders_pie_chart',
    'create_conversion_chart',
    'create_user_activity_chart',
    'create_combined_dashboard',
    # توابع آماده‌سازی
    'prepare_revenue_data',
    'prepare_orders_by_service',
    'prepare_conversion_data',
    # کلاس مدیریت
    'ChartManager',
    # ابزارها
    'ensure_charts_dir',
    'clean_old_charts',
]