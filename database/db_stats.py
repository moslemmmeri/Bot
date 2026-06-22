# database/db_stats.py
# آمار و تحلیل عملکرد دکمه‌ها - ثبت رویدادها و دریافت گزارش‌های تحلیلی
# نسخه با پشتیبانی از فیلترهای پیشرفته (بازه زمانی، نوع سرویس، وضعیت، محدوده مبلغ، کاربر)
# اصلاح شده برای رفع circular import: استفاده از db_connection به جای db_core
# استفاده از utils.error_handler برای مدیریت خطاها

from logger_config import logger
from .db_connection import get_db_connection
from datetime import datetime, timedelta
from utils.error_handler import log_database_error, log_general_error


# ==================== ثبت رویدادها ====================

def log_button_action(button_id, user_id, action_type, amount=0):
    """
    ثبت یک رویداد مرتبط با دکمه در جدول button_stats.
    
    پارامترها:
        button_id: شناسه دکمه
        user_id: شناسه کاربر
        action_type: نوع رویداد ('click', 'form_start', 'order_paid')
        amount: مبلغ (فقط برای 'order_paid' استفاده می‌شود)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO button_stats (button_id, user_id, action_type, amount)
                VALUES (?, ?, ?, ?)
            """, (button_id, user_id, action_type, amount))
            conn.commit()
            logger.debug(f"رویداد {action_type} برای دکمه {button_id} توسط کاربر {user_id} ثبت شد.")
    except Exception as e:
        log_database_error(
            f"Error logging button action for button {button_id}, user {user_id}: {str(e)}",
            traceback=str(e),
            user_id=user_id
        )


def log_button_click(button_id, user_id):
    """ثبت کلیک روی دکمه (ساده‌ترین حالت)"""
    log_button_action(button_id, user_id, 'click')


def log_form_start(button_id, user_id):
    """ثبت شروع فرم (زمانی که کاربر اولین سوال را می‌بیند)"""
    log_button_action(button_id, user_id, 'form_start')


def log_order_paid(button_id, user_id, amount):
    """ثبت سفارش پرداخت‌شده برای یک دکمه"""
    log_button_action(button_id, user_id, 'order_paid', amount)


# ==================== دریافت آمار یک دکمه ====================

def get_button_stats(button_id):
    """
    دریافت آمار کامل یک دکمه:
    - تعداد کلیک‌ها
    - تعداد شروع فرم
    - تعداد سفارش‌های پرداخت‌شده
    - مجموع درآمد
    - نرخ تبدیل (تعداد سفارش / تعداد کلیک)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # آمار کلیک
            cursor.execute("SELECT COUNT(*) as count FROM button_stats WHERE button_id = ? AND action_type = 'click'", (button_id,))
            clicks = cursor.fetchone()['count']
            
            # آمار شروع فرم
            cursor.execute("SELECT COUNT(*) as count FROM button_stats WHERE button_id = ? AND action_type = 'form_start'", (button_id,))
            starts = cursor.fetchone()['count']
            
            # آمار سفارشات پرداخت‌شده
            cursor.execute("""
                SELECT 
                    COUNT(*) as orders,
                    COALESCE(SUM(amount), 0) as revenue
                FROM button_stats 
                WHERE button_id = ? AND action_type = 'order_paid'
            """, (button_id,))
            row = cursor.fetchone()
            orders = row['orders']
            revenue = row['revenue']
            
            # محاسبه نرخ تبدیل (درصد)
            conversion_rate = 0
            if clicks > 0:
                conversion_rate = round((orders / clicks) * 100, 2)
            
            return {
                'button_id': button_id,
                'clicks': clicks,
                'form_starts': starts,
                'orders': orders,
                'revenue': revenue,
                'conversion_rate': conversion_rate
            }
    except Exception as e:
        log_database_error(
            f"Error getting button stats for button {button_id}: {str(e)}",
            traceback=str(e)
        )
        return {
            'button_id': button_id,
            'clicks': 0,
            'form_starts': 0,
            'orders': 0,
            'revenue': 0,
            'conversion_rate': 0
        }


def get_button_stats_with_filter(button_id, start_date=None, end_date=None):
    """
    دریافت آمار یک دکمه با فیلتر بازه زمانی
    
    پارامترها:
        button_id: شناسه دکمه
        start_date: تاریخ شروع (اختیاری)
        end_date: تاریخ پایان (اختیاری)
    
    بازگشت: دیکشنری آمار
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            conditions = ["button_id = ?"]
            params = [button_id]
            
            if start_date:
                conditions.append("DATE(created_at) >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("DATE(created_at) <= ?")
                params.append(end_date)
            
            where_clause = " AND ".join(conditions)
            
            # آمار کلیک
            cursor.execute(f"""
                SELECT COUNT(*) as count FROM button_stats 
                WHERE {where_clause} AND action_type = 'click'
            """, params)
            clicks = cursor.fetchone()['count']
            
            # آمار شروع فرم
            cursor.execute(f"""
                SELECT COUNT(*) as count FROM button_stats 
                WHERE {where_clause} AND action_type = 'form_start'
            """, params)
            starts = cursor.fetchone()['count']
            
            # آمار سفارشات پرداخت‌شده
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as orders,
                    COALESCE(SUM(amount), 0) as revenue
                FROM button_stats 
                WHERE {where_clause} AND action_type = 'order_paid'
            """, params)
            row = cursor.fetchone()
            orders = row['orders']
            revenue = row['revenue']
            
            conversion_rate = 0
            if clicks > 0:
                conversion_rate = round((orders / clicks) * 100, 2)
            
            return {
                'button_id': button_id,
                'clicks': clicks,
                'form_starts': starts,
                'orders': orders,
                'revenue': revenue,
                'conversion_rate': conversion_rate
            }
    except Exception as e:
        log_database_error(
            f"Error getting button stats with filter for button {button_id}: {str(e)}",
            traceback=str(e)
        )
        return {
            'button_id': button_id,
            'clicks': 0,
            'form_starts': 0,
            'orders': 0,
            'revenue': 0,
            'conversion_rate': 0
        }


# ==================== دکمه‌های برتر با فیلتر ====================

def get_top_buttons(limit=10, sort_by='orders', start_date=None, end_date=None):
    """
    دریافت لیست دکمه‌های برتر بر اساس معیارهای مختلف با فیلتر بازه زمانی.
    
    پارامترها:
        limit: تعداد دکمه‌های برگشتی
        sort_by: معیار مرتب‌سازی ('clicks', 'form_starts', 'orders', 'revenue', 'conversion_rate')
        start_date: تاریخ شروع (اختیاری)
        end_date: تاریخ پایان (اختیاری)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # شرط بازه زمانی
            date_condition = ""
            date_params = []
            if start_date:
                date_condition += " AND DATE(created_at) >= ?"
                date_params.append(start_date)
            if end_date:
                date_condition += " AND DATE(created_at) <= ?"
                date_params.append(end_date)
            
            # دریافت تمام دکمه‌ها
            cursor.execute("SELECT id, name FROM buttons WHERE is_active = 1")
            buttons = cursor.fetchall()
            
            results = []
            for btn in buttons:
                # آمار کلیک
                cursor.execute(f"""
                    SELECT COUNT(*) as count FROM button_stats 
                    WHERE button_id = ? AND action_type = 'click' {date_condition}
                """, (btn['id'], *date_params))
                clicks = cursor.fetchone()['count']
                
                # آمار شروع فرم
                cursor.execute(f"""
                    SELECT COUNT(*) as count FROM button_stats 
                    WHERE button_id = ? AND action_type = 'form_start' {date_condition}
                """, (btn['id'], *date_params))
                starts = cursor.fetchone()['count']
                
                # آمار سفارشات پرداخت‌شده
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as orders,
                        COALESCE(SUM(amount), 0) as revenue
                    FROM button_stats 
                    WHERE button_id = ? AND action_type = 'order_paid' {date_condition}
                """, (btn['id'], *date_params))
                row = cursor.fetchone()
                orders = row['orders']
                revenue = row['revenue']
                
                conversion_rate = 0
                if clicks > 0:
                    conversion_rate = round((orders / clicks) * 100, 2)
                
                results.append({
                    'button_id': btn['id'],
                    'button_name': btn['name'],
                    'clicks': clicks,
                    'form_starts': starts,
                    'orders': orders,
                    'revenue': revenue,
                    'conversion_rate': conversion_rate
                })
            
            # مرتب‌سازی بر اساس معیار انتخاب‌شده
            sort_map = {
                'clicks': 'clicks',
                'form_starts': 'form_starts',
                'orders': 'orders',
                'revenue': 'revenue',
                'conversion_rate': 'conversion_rate'
            }
            sort_key = sort_map.get(sort_by, 'orders')
            results.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
            
            return results[:limit]
    except Exception as e:
        log_database_error(
            f"Error getting top buttons: {str(e)}",
            traceback=str(e)
        )
        return []


# ==================== آمار کلی داشبورد ====================

def get_dashboard_stats():
    """
    دریافت آمار کلی برای داشبورد مدیریت:
    - تعداد کل کاربران
    - تعداد کل سفارشات پرداخت‌شده
    - مجموع درآمد کل
    - میانگین مبلغ هر سفارش
    - تعداد کل کلیک‌ها
    - تعداد کل شروع فرم‌ها
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # تعداد کل کاربران
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone()['count']
            
            # آمار سفارشات پرداخت‌شده
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(amount), 0) as total_revenue,
                    COALESCE(AVG(amount), 0) as avg_order_value
                FROM button_stats 
                WHERE action_type = 'order_paid'
            """)
            row = cursor.fetchone()
            total_orders = row['total_orders']
            total_revenue = row['total_revenue']
            avg_order_value = row['avg_order_value']
            
            # تعداد کل کلیک‌ها
            cursor.execute("SELECT COUNT(*) as count FROM button_stats WHERE action_type = 'click'")
            total_clicks = cursor.fetchone()['count']
            
            # تعداد کل شروع فرم
            cursor.execute("SELECT COUNT(*) as count FROM button_stats WHERE action_type = 'form_start'")
            total_form_starts = cursor.fetchone()['count']
            
            # نرخ تبدیل کلی (سفارش / کلیک)
            overall_conversion = 0
            if total_clicks > 0:
                overall_conversion = round((total_orders / total_clicks) * 100, 2)
            
            return {
                'total_users': total_users,
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'avg_order_value': round(avg_order_value, 0),
                'total_clicks': total_clicks,
                'total_form_starts': total_form_starts,
                'overall_conversion': overall_conversion
            }
    except Exception as e:
        log_database_error(
            f"Error getting dashboard stats: {str(e)}",
            traceback=str(e)
        )
        return {
            'total_users': 0,
            'total_orders': 0,
            'total_revenue': 0,
            'avg_order_value': 0,
            'total_clicks': 0,
            'total_form_starts': 0,
            'overall_conversion': 0
        }


# ==================== آمار دوره‌ای با فیلتر ====================

def get_revenue_by_period(days=30, start_date=None, end_date=None, button_id=None):
    """
    دریافت درآمد در یک دوره‌ی زمانی مشخص با فیلترهای اضافی.
    
    پارامترها:
        days: تعداد روزهای اخیر (در صورت عدم ارائه start_date/end_date)
        start_date: تاریخ شروع (اختیاری)
        end_date: تاریخ پایان (اختیاری)
        button_id: شناسه سرویس (اختیاری)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            conditions = ["action_type = 'order_paid'"]
            params = []
            
            if start_date:
                conditions.append("DATE(created_at) >= ?")
                params.append(start_date)
            elif days:
                conditions.append("created_at >= datetime('now', '-' || ? || ' days')")
                params.append(days)
            
            if end_date:
                conditions.append("DATE(created_at) <= ?")
                params.append(end_date)
            
            if button_id:
                conditions.append("button_id = ?")
                params.append(button_id)
            
            where_clause = " AND ".join(conditions)
            
            cursor.execute(f"""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as orders,
                    COALESCE(SUM(amount), 0) as revenue
                FROM button_stats 
                WHERE {where_clause}
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) DESC
            """, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error getting revenue by period: {str(e)}",
            traceback=str(e)
        )
        return []


def get_button_stats_by_date(button_id, days=30):
    """
    دریافت آمار یک دکمه در یک دوره‌ی زمانی مشخص.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(CASE WHEN action_type = 'click' THEN 1 END) as clicks,
                    COUNT(CASE WHEN action_type = 'form_start' THEN 1 END) as form_starts,
                    COUNT(CASE WHEN action_type = 'order_paid' THEN 1 END) as orders,
                    COALESCE(SUM(CASE WHEN action_type = 'order_paid' THEN amount ELSE 0 END), 0) as revenue
                FROM button_stats 
                WHERE button_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) DESC
            """, (button_id, days))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error getting button stats by date for button {button_id}: {str(e)}",
            traceback=str(e)
        )
        return []


# ==================== آمار کاربران (سفارش‌دهندگان برتر) ====================

def get_top_users(limit=10, start_date=None, end_date=None):
    """
    دریافت کاربرانی که بیشترین سفارش یا بیشترین مبلغ پرداختی را داشته‌اند.
    
    پارامترها:
        limit: تعداد نتایج
        start_date: تاریخ شروع (اختیاری)
        end_date: تاریخ پایان (اختیاری)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            date_condition = ""
            params = []
            if start_date:
                date_condition += " AND DATE(created_at) >= ?"
                params.append(start_date)
            if end_date:
                date_condition += " AND DATE(created_at) <= ?"
                params.append(end_date)
            
            cursor.execute(f"""
                SELECT 
                    user_id,
                    COUNT(*) as order_count,
                    COALESCE(SUM(amount), 0) as total_spent
                FROM button_stats 
                WHERE action_type = 'order_paid' {date_condition}
                GROUP BY user_id
                ORDER BY total_spent DESC
                LIMIT ?
            """, (*params, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error getting top users: {str(e)}",
            traceback=str(e)
        )
        return []


# ==================== آمار با فیلترهای پیشرفته ====================

def get_advanced_stats(filters):
    """
    دریافت آمار با فیلترهای پیشرفته
    
    پارامترها:
        filters: دیکشنری فیلترها شامل:
            - start_date: تاریخ شروع
            - end_date: تاریخ پایان
            - button_id: شناسه سرویس
            - user_id: شناسه کاربر
            - action_type: نوع اقدام (click, form_start, order_paid)
            - min_amount: حداقل مبلغ
            - max_amount: حداکثر مبلغ
    
    بازگشت: لیست رکوردهای آمار
    """
    try:
        conditions = []
        params = []
        
        if 'start_date' in filters:
            conditions.append("DATE(created_at) >= ?")
            params.append(filters['start_date'])
        
        if 'end_date' in filters:
            conditions.append("DATE(created_at) <= ?")
            params.append(filters['end_date'])
        
        if 'button_id' in filters:
            conditions.append("button_id = ?")
            params.append(filters['button_id'])
        
        if 'user_id' in filters:
            conditions.append("user_id = ?")
            params.append(filters['user_id'])
        
        if 'action_type' in filters:
            conditions.append("action_type = ?")
            params.append(filters['action_type'])
        
        if 'min_amount' in filters:
            conditions.append("amount >= ?")
            params.append(filters['min_amount'])
        
        if 'max_amount' in filters:
            conditions.append("amount <= ?")
            params.append(filters['max_amount'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    id, button_id, user_id, action_type, amount, created_at
                FROM button_stats 
                WHERE {where_clause}
                ORDER BY created_at DESC
            """, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        log_database_error(
            f"Error getting advanced stats: {str(e)}",
            traceback=str(e)
        )
        return []


def get_advanced_stats_aggregated(filters):
    """
    دریافت آمار تجمیعی با فیلترهای پیشرفته
    
    پارامترها:
        filters: دیکشنری فیلترها (همانند get_advanced_stats)
    
    بازگشت: دیکشنری آمار تجمیعی
    """
    try:
        conditions = []
        params = []
        
        if 'start_date' in filters:
            conditions.append("DATE(created_at) >= ?")
            params.append(filters['start_date'])
        
        if 'end_date' in filters:
            conditions.append("DATE(created_at) <= ?")
            params.append(filters['end_date'])
        
        if 'button_id' in filters:
            conditions.append("button_id = ?")
            params.append(filters['button_id'])
        
        if 'user_id' in filters:
            conditions.append("user_id = ?")
            params.append(filters['user_id'])
        
        if 'min_amount' in filters:
            conditions.append("amount >= ?")
            params.append(filters['min_amount'])
        
        if 'max_amount' in filters:
            conditions.append("amount <= ?")
            params.append(filters['max_amount'])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # آمار کلیک
            cursor.execute(f"""
                SELECT COUNT(*) as count FROM button_stats 
                WHERE {where_clause} AND action_type = 'click'
            """, params)
            clicks = cursor.fetchone()['count']
            
            # آمار شروع فرم
            cursor.execute(f"""
                SELECT COUNT(*) as count FROM button_stats 
                WHERE {where_clause} AND action_type = 'form_start'
            """, params)
            form_starts = cursor.fetchone()['count']
            
            # آمار سفارشات
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as orders,
                    COALESCE(SUM(amount), 0) as revenue,
                    COALESCE(AVG(amount), 0) as avg_amount
                FROM button_stats 
                WHERE {where_clause} AND action_type = 'order_paid'
            """, params)
            row = cursor.fetchone()
            orders = row['orders']
            revenue = row['revenue']
            avg_amount = row['avg_amount']
            
            # تعداد کاربران
            cursor.execute(f"""
                SELECT COUNT(DISTINCT user_id) as users FROM button_stats 
                WHERE {where_clause}
            """, params)
            users = cursor.fetchone()['users']
            
            return {
                'clicks': clicks,
                'form_starts': form_starts,
                'orders': orders,
                'revenue': revenue,
                'avg_amount': round(avg_amount, 0),
                'total_users': users,
                'conversion_rate': round((orders / clicks * 100), 2) if clicks > 0 else 0
            }
    except Exception as e:
        log_database_error(
            f"Error getting advanced stats aggregated: {str(e)}",
            traceback=str(e)
        )
        return {
            'clicks': 0,
            'form_starts': 0,
            'orders': 0,
            'revenue': 0,
            'avg_amount': 0,
            'total_users': 0,
            'conversion_rate': 0
        }


__all__ = [
    'log_button_action',
    'log_button_click',
    'log_form_start',
    'log_order_paid',
    'get_button_stats',
    'get_button_stats_with_filter',
    'get_top_buttons',
    'get_dashboard_stats',
    'get_revenue_by_period',
    'get_button_stats_by_date',
    'get_top_users',
    'get_advanced_stats',
    'get_advanced_stats_aggregated',
]