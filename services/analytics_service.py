# services/analytics_service.py
# سرویس آمار و تحلیل - منطق کسب‌وکار مربوط به آمار، گزارش‌ها و تحلیل داده‌ها

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from logger_config import logger
from repositories import OrderRepository, ButtonRepository
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class AnalyticsService:
    """سرویس آمار و تحلیل - تولید گزارش‌ها و تحلیل داده‌های ربات"""
    
    def __init__(self, connection, order_repo: Optional[OrderRepository] = None,
                 button_repo: Optional[ButtonRepository] = None):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            order_repo: ریپازیتوری سفارشات (اختیاری)
            button_repo: ریپازیتوری دکمه‌ها (اختیاری)
        """
        self._connection = connection
        self._order_repo = order_repo or OrderRepository(connection)
        self._button_repo = button_repo or ButtonRepository(connection)
    
    # ============================================================
    # داشبورد کلی
    # ============================================================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی برای داشبورد
        
        بازگشت: دیکشنری شامل آمارهای مهم
        """
        try:
            # آمار کاربران
            from services.user_service import UserService
            user_service = UserService(self._connection)
            user_summary = user_service.get_users_summary()
            
            # آمار سفارشات
            order_stats = self._order_repo.get_stats()
            
            # آمار دکمه‌ها
            button_count = self._button_repo.get_button_count()
            
            # نرخ تبدیل کلی
            total_clicks = 0
            total_orders = order_stats.get('total', 0)
            try:
                query = "SELECT COUNT(*) as count FROM button_stats WHERE action_type = 'click'"
                with self._connection.get_cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    total_clicks = result.get('count', 0) if result else 0
            except Exception as e:
                # ✅ ثبت خطا با traceback کامل
                log_database_error(
                    f"Error counting clicks: {str(e)}",
                    traceback=traceback.format_exc()
                )
            
            conversion_rate = (total_orders / total_clicks * 100) if total_clicks > 0 else 0
            
            # درآمد امروز
            today = datetime.now().date().strftime("%Y-%m-%d")
            today_orders = self._order_repo.get_orders_by_date_range(today, today)
            today_revenue = sum(o.get('payment_amount', 0) or 0 for o in today_orders)
            
            return {
                'total_users': user_summary.get('total_users', 0),
                'active_today': user_summary.get('active_today', 0),
                'active_week': user_summary.get('active_week', 0),
                'total_orders': order_stats.get('total', 0),
                'total_revenue': order_stats.get('total_amount', 0),
                'avg_order_value': order_stats.get('avg_amount', 0),
                'today_revenue': today_revenue,
                'today_orders': len(today_orders),
                'total_buttons': button_count,
                'total_clicks': total_clicks,
                'conversion_rate': round(conversion_rate, 2),
                'pending_orders': order_stats.get('statuses', {}).get('pending', 0),
                'paid_orders': order_stats.get('statuses', {}).get('paid', 0),
                'completed_orders': order_stats.get('statuses', {}).get('completed', 0),
                'growth_percent': user_summary.get('growth_percent', 0),
            }
            
        except Exception as e:
            # ✅ استفاده از log_database_error با traceback کامل
            log_database_error(
                f"Error getting dashboard stats: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total_users': 0,
                'active_today': 0,
                'active_week': 0,
                'total_orders': 0,
                'total_revenue': 0,
                'avg_order_value': 0,
                'today_revenue': 0,
                'today_orders': 0,
                'total_buttons': 0,
                'total_clicks': 0,
                'conversion_rate': 0,
                'pending_orders': 0,
                'paid_orders': 0,
                'completed_orders': 0,
                'growth_percent': 0,
            }
    
    # ============================================================
    # آمار سفارشات
    # ============================================================
    
    def get_order_stats(self) -> Dict[str, Any]:
        """دریافت آمار کامل سفارشات"""
        return self._order_repo.get_stats()
    
    def get_revenue_by_period(self, days: int = 30) -> List[Dict[str, Any]]:
        """دریافت درآمد در بازه زمانی مشخص"""
        return self._order_repo.get_revenue_by_period(days)
    
    def get_orders_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """دریافت سفارشات در بازه زمانی"""
        return self._order_repo.get_orders_by_date_range(start_date, end_date)
    
    def get_orders_summary(self) -> Dict[str, Any]:
        """دریافت خلاصه سفارشات"""
        from services.order_service import OrderService
        order_service = OrderService(self._connection, self._order_repo)
        return order_service.get_orders_summary()
    
    # ============================================================
    # آمار دکمه‌ها و سرویس‌ها
    # ============================================================
    
    def get_button_stats(self, button_id: int) -> Dict[str, Any]:
        """
        دریافت آمار یک دکمه
        
        پارامترها:
            button_id: شناسه دکمه
        
        بازگشت: دیکشنری شامل آمار کلیک، شروع فرم، سفارش و درآمد
        """
        return {
            'button_id': button_id,
            **self._get_button_stats(button_id)
        }
    
    def _get_button_stats(self, button_id: int) -> Dict[str, Any]:
        """دریافت آمار یک دکمه (داخلی)"""
        try:
            query = """
                SELECT 
                    COUNT(CASE WHEN action_type = 'click' THEN 1 END) as clicks,
                    COUNT(CASE WHEN action_type = 'form_start' THEN 1 END) as form_starts,
                    COUNT(CASE WHEN action_type = 'order_paid' THEN 1 END) as orders,
                    COALESCE(SUM(CASE WHEN action_type = 'order_paid' THEN amount ELSE 0 END), 0) as revenue
                FROM button_stats
                WHERE button_id = ?
            """
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (button_id,))
                result = cursor.fetchone()
                
            if result:
                result = dict(result)
                clicks = result.get('clicks', 0)
                orders = result.get('orders', 0)
                result['conversion_rate'] = (orders / clicks * 100) if clicks > 0 else 0
                return result
            return {
                'clicks': 0,
                'form_starts': 0,
                'orders': 0,
                'revenue': 0,
                'conversion_rate': 0
            }
        except Exception as e:
            # ✅ استفاده از log_database_error با traceback کامل
            log_database_error(
                f"Error getting button stats for {button_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'clicks': 0,
                'form_starts': 0,
                'orders': 0,
                'revenue': 0,
                'conversion_rate': 0
            }
    
    def get_top_buttons(self, sort_by: str = 'orders', limit: int = 10) -> List[Dict[str, Any]]:
        """
        دریافت دکمه‌های برتر
        
        پارامترها:
            sort_by: معیار مرتب‌سازی (orders, revenue, clicks, conversion_rate)
            limit: تعداد نتایج
        
        بازگشت: لیست دکمه‌های برتر
        """
        all_buttons = self._button_repo.get_all(limit=1000, offset=0)
        result = []
        
        for btn in all_buttons:
            stats = self._get_button_stats(btn['id'])
            result.append({
                'button_id': btn['id'],
                'button_name': btn['name'],
                'category_id': btn.get('category_id'),
                'has_submenu': btn.get('has_submenu', 0),
                'has_payment': btn.get('has_payment', 0),
                **stats
            })
        
        # مرتب‌سازی
        sort_map = {
            'orders': 'orders',
            'revenue': 'revenue',
            'clicks': 'clicks',
            'conversion_rate': 'conversion_rate'
        }
        sort_key = sort_map.get(sort_by, 'orders')
        result.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
        
        return result[:limit]
    
    def get_service_rankings(self, sort_by: str = 'orders', limit: int = 10) -> List[Dict[str, Any]]:
        """دریافت رتبه‌بندی سرویس‌ها"""
        from services.button_service import ButtonService
        button_service = ButtonService(self._connection, self._button_repo)
        return button_service.get_service_rankings(sort_by, limit)
    
    # ============================================================
    # آمار کاربران
    # ============================================================
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """دریافت آمار یک کاربر"""
        from services.user_service import UserService
        user_service = UserService(self._connection)
        return user_service.get_user_stats(user_id)
    
    def get_user_activity(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        دریافت فعالیت‌های یک کاربر در بازه زمانی
        
        پارامترها:
            user_id: شناسه کاربر
            days: تعداد روزهای اخیر
        
        بازگشت: لیست فعالیت‌های کاربر
        """
        try:
            query = """
                SELECT 
                    DATE(created_at) as date,
                    COUNT(CASE WHEN action_type = 'click' THEN 1 END) as clicks,
                    COUNT(CASE WHEN action_type = 'form_start' THEN 1 END) as form_starts,
                    COUNT(CASE WHEN action_type = 'order_paid' THEN 1 END) as orders,
                    COALESCE(SUM(CASE WHEN action_type = 'order_paid' THEN amount ELSE 0 END), 0) as revenue
                FROM button_stats
                WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) DESC
            """
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (user_id, days))
                return cursor.fetchall()
        except Exception as e:
            # ✅ استفاده از log_database_error با traceback کامل
            log_database_error(
                f"Error getting user activity for {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return []
    
    def get_user_orders_stats(self, user_id: int) -> Dict[str, Any]:
        """دریافت آمار سفارشات یک کاربر"""
        from services.order_service import OrderService
        order_service = OrderService(self._connection, self._order_repo)
        return order_service.get_user_stats(user_id)
    
    def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """دریافت کاربران برتر"""
        from services.user_service import UserService
        user_service = UserService(self._connection)
        return user_service.get_top_users(limit)
    
    # ============================================================
    # گزارش‌های دوره‌ای
    # ============================================================
    
    def get_period_report(self, period: str = 'day') -> Dict[str, Any]:
        """
        دریافت گزارش دوره‌ای
        
        پارامترها:
            period: دوره ('day', 'week', 'month')
        
        بازگشت: دیکشنری شامل گزارش دوره‌ای
        """
        now = datetime.now()
        
        if period == 'day':
            start_date = now.strftime("%Y-%m-%d")
            end_date = start_date
            days = 1
        elif period == 'week':
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
            days = 7
        else:  # month
            start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
            days = 30
        
        orders = self._order_repo.get_orders_by_date_range(start_date, end_date)
        total_amount = sum(o.get('payment_amount', 0) or 0 for o in orders)
        paid_orders = [o for o in orders if o.get('status') in ['paid', 'completed']]
        pending_orders = [o for o in orders if o.get('status') == 'pending']
        
        # محاسبه تغییرات نسبت به دوره قبل
        prev_start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
        prev_end = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        prev_orders = self._order_repo.get_orders_by_date_range(prev_start, prev_end)
        prev_amount = sum(o.get('payment_amount', 0) or 0 for o in prev_orders)
        
        growth = ((total_amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0
        
        return {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'days': days,
            'total_orders': len(orders),
            'total_amount': total_amount,
            'paid_orders': len(paid_orders),
            'pending_orders': len(pending_orders),
            'avg_amount': total_amount / len(orders) if len(orders) > 0 else 0,
            'prev_total_amount': prev_amount,
            'growth_percent': round(growth, 1),
            'orders': orders
        }
    
    def get_daily_report(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        دریافت گزارش روزانه
        
        پارامترها:
            date: تاریخ (اختیاری، پیش‌فرض: امروز)
        
        بازگشت: دیکشنری شامل گزارش روزانه
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        orders = self._order_repo.get_orders_by_date_range(date, date)
        total_amount = sum(o.get('payment_amount', 0) or 0 for o in orders)
        
        # تفکیک سرویس‌ها
        service_breakdown = {}
        for order in orders:
            button_id = order.get('button_id')
            if button_id:
                service_breakdown[button_id] = service_breakdown.get(button_id, 0) + 1
        
        # دریافت نام سرویس‌ها
        services = []
        for btn_id, count in service_breakdown.items():
            btn = self._button_repo.get_by_id(btn_id)
            name = btn['name'] if btn else f"سرویس {btn_id}"
            services.append({'service_name': name, 'count': count})
        
        services.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'date': date,
            'total_orders': len(orders),
            'total_amount': total_amount,
            'paid_orders': len([o for o in orders if o.get('status') in ['paid', 'completed']]),
            'pending_orders': len([o for o in orders if o.get('status') == 'pending']),
            'avg_amount': total_amount / len(orders) if len(orders) > 0 else 0,
            'top_services': services[:5],
            'orders': orders
        }
    
    # ============================================================
    # گزارش‌های خروجی
    # ============================================================
    
    def get_export_data(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        دریافت داده‌های خروجی برای Excel/CSV
        
        پارامترها:
            filters: فیلترهای اعمال‌شده (اختیاری)
        
        بازگشت: لیست دیکشنری‌های داده‌های خروجی
        """
        if filters:
            orders = self._order_repo.search_advanced(filters, limit=1000, offset=0)
        else:
            orders = self._order_repo.get_all(limit=1000, offset=0)
        
        result = []
        for order in orders:
            from models.order import Order as OrderModel
            order_obj = OrderModel.from_db(order)
            
            # دریافت نام سرویس
            btn = self._button_repo.get_by_id(order.get('button_id'))
            service_name = btn['name'] if btn else 'نامشخص'
            if btn and btn.get('parent_button_id'):
                parent = self._button_repo.get_by_id(btn['parent_button_id'])
                if parent:
                    service_name = f"{parent['name']} > {btn['name']}"
            
            result.append({
                'id': order.get('id'),
                'user_id': order.get('user_id'),
                'fullname': order_obj.fullname,
                'service_name': service_name,
                'payment_amount': order.get('payment_amount', 0) or 0,
                'status': order_obj.status_text,
                'tracking_code': order.get('tracking_code', ''),
                'created_at': order_obj.created_at_formatted,
                'admin_note': order.get('admin_note', '')
            })
        
        return result
    
    # ============================================================
    # آمار خطاها
    # ============================================================
    
    def get_error_stats(self) -> Dict[str, Any]:
        """دریافت آمار خطاها"""
        from database.db_logs import get_error_stats
        return get_error_stats()
    
    def get_errors_by_type(self) -> List[Dict[str, Any]]:
        """دریافت تفکیک خطاها بر اساس نوع"""
        from database.db_logs import get_error_types_with_count
        return get_error_types_with_count()
    
    # ============================================================
    # گزارش‌های ترکیبی
    # ============================================================
    
    def get_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """
        دریافت گزارش جامع
        
        پارامترها:
            days: تعداد روزهای اخیر
        
        بازگشت: دیکشنری شامل گزارش جامع
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # آمار کلی
        dashboard = self.get_dashboard_stats()
        
        # درآمد روزانه
        revenue_data = self.get_revenue_by_period(days)
        
        # سرویس‌های برتر
        top_services = self.get_top_buttons('orders', 10)
        
        # کاربران برتر
        top_users = self.get_top_users(5)
        
        # آمار وضعیت سفارشات
        order_stats = self.get_order_stats()
        
        return {
            'period': {
                'days': days,
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': dashboard,
            'revenue_data': revenue_data,
            'top_services': top_services,
            'top_users': top_users,
            'order_statuses': order_stats.get('statuses', {}),
            'total_orders': order_stats.get('total', 0),
            'total_revenue': order_stats.get('total_amount', 0),
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


__all__ = [
    'AnalyticsService',
]