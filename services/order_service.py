# services/order_service.py
# سرویس مدیریت سفارشات - منطق کسب‌وکار مربوط به سفارشات

import json
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from logger_config import logger
from repositories import OrderRepository
from models.order import Order, OrderStatus
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class OrderService:
    """سرویس مدیریت سفارشات"""
    
    def __init__(self, connection, repository: Optional[OrderRepository] = None):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            repository: ریپازیتوری سفارشات (اختیاری)
        """
        self._connection = connection
        self._repository = repository or OrderRepository(connection)
    
    # ============================================================
    # عملیات پایه
    # ============================================================
    
    def create_order(self, user_id: int, button_id: int,
                     order_data: Dict[str, Any],
                     payment_amount: int = 0,
                     tracking_code: Optional[str] = None,
                     status: str = 'pending') -> Optional[Dict[str, Any]]:
        """
        ایجاد سفارش جدید
        
        پارامترها:
            user_id: شناسه کاربر
            button_id: شناسه دکمه
            order_data: داده‌های سفارش (پاسخ‌ها و ...)
            payment_amount: مبلغ پرداختی
            tracking_code: کد رهگیری
            status: وضعیت اولیه
        
        بازگشت: دیکشنری سفارش ایجادشده یا None
        """
        try:
            order_id = self._repository.create(
                user_id=user_id,
                button_id=button_id,
                order_data=order_data,
                payment_amount=payment_amount,
                tracking_code=tracking_code,
                status=status
            )
            
            if order_id:
                logger.info(f"✅ Order created: {order_id} by user {user_id}")
                return self.get_order(order_id)
            
            return None
            
        except Exception as e:
            # ✅ ثبت خطای دیتابیس با traceback کامل
            log_database_error(
                f"Error creating order for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return None
    
    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """دریافت سفارش بر اساس شناسه"""
        return self._repository.get_by_id(order_id)
    
    def get_orders(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت لیست سفارشات با صفحه‌بندی"""
        return self._repository.get_all(limit, offset)
    
    def get_orders_by_user(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت سفارشات یک کاربر"""
        return self._repository.get_by_user(user_id, limit, offset)
    
    def get_orders_by_status(self, status: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت سفارشات بر اساس وضعیت"""
        return self._repository.get_by_status(status, limit, offset)
    
    def get_orders_by_button(self, button_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت سفارشات یک سرویس"""
        return self._repository.get_by_button(button_id, limit, offset)
    
    def get_order_by_tracking(self, tracking_code: str) -> Optional[Dict[str, Any]]:
        """دریافت سفارش بر اساس کد رهگیری"""
        return self._repository.get_by_tracking_code(tracking_code)
    
    def count_orders(self) -> int:
        """تعداد کل سفارشات"""
        return self._repository.count()
    
    def count_by_status(self, status: str) -> int:
        """تعداد سفارشات با وضعیت مشخص"""
        return self._repository.count_by_status(status)
    
    def count_by_user(self, user_id: int) -> int:
        """تعداد سفارشات یک کاربر"""
        return self._repository.count_by_user(user_id)
    
    # ============================================================
    # به‌روزرسانی و مدیریت
    # ============================================================
    
    def update_status(self, order_id: int, new_status: str,
                      user_id: int, note: Optional[str] = None) -> bool:
        """
        تغییر وضعیت سفارش
        
        پارامترها:
            order_id: شناسه سفارش
            new_status: وضعیت جدید
            user_id: شناسه کاربر انجام‌دهنده
            note: یادداشت اختیاری
        
        بازگشت: True در صورت موفقیت
        """
        # اعتبارسنجی وضعیت
        valid_statuses = ['pending', 'paid', 'completed', 'cancelled', 'failed', 'refunded']
        if new_status not in valid_statuses:
            logger.warning(f"Invalid status: {new_status}")
            return False
        
        # دریافت سفارش برای بررسی
        order = self.get_order(order_id)
        if not order:
            logger.warning(f"Order {order_id} not found")
            return False
        
        # اگر سفارش تکمیل یا لغو شده، وضعیت قابل تغییر نیست
        current_status = order.get('status', 'pending')
        if current_status in ['completed', 'cancelled']:
            logger.warning(f"Order {order_id} is {current_status}, cannot change status")
            return False
        
        try:
            return self._repository.update_status(order_id, new_status, user_id, note)
        except Exception as e:
            # ✅ ثبت خطای دیتابیس با traceback کامل
            log_database_error(
                f"Error updating order {order_id} status to {new_status}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def add_note(self, order_id: int, note: str, user_id: int) -> bool:
        """افزودن یادداشت به سفارش"""
        if not note or note.strip() == "":
            return False
        
        try:
            return self._repository.add_note(order_id, note, user_id)
        except Exception as e:
            # ✅ ثبت خطای دیتابیس با traceback کامل
            log_database_error(
                f"Error adding note to order {order_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def delete_order(self, order_id: int) -> bool:
        """حذف یک سفارش"""
        order = self.get_order(order_id)
        if not order:
            return False
        
        # فقط سفارشات pending یا cancelled قابل حذف هستند
        status = order.get('status', 'pending')
        if status not in ['pending', 'cancelled']:
            logger.warning(f"Order {order_id} is {status}, cannot delete")
            return False
        
        try:
            return self._repository.delete(order_id)
        except Exception as e:
            # ✅ ثبت خطای دیتابیس با traceback کامل
            log_database_error(
                f"Error deleting order {order_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def cancel_order(self, order_id: int, user_id: int, reason: Optional[str] = None) -> bool:
        """
        لغو یک سفارش
        
        پارامترها:
            order_id: شناسه سفارش
            user_id: شناسه کاربر لغو‌کننده
            reason: دلیل لغو
        """
        order = self.get_order(order_id)
        if not order:
            return False
        
        # فقط سفارشات pending قابل لغو هستند
        if order.get('status') != 'pending':
            logger.warning(f"Order {order_id} is {order.get('status')}, cannot cancel")
            return False
        
        try:
            return self._repository.update_status(order_id, 'cancelled', user_id, reason or 'لغو شده توسط کاربر')
        except Exception as e:
            # ✅ ثبت خطای دیتابیس با traceback کامل
            log_database_error(
                f"Error cancelling order {order_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    # ============================================================
    # جستجو
    # ============================================================
    
    def search_orders(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """جستجوی سفارشات بر اساس کلمه کلیدی"""
        return self._repository.search(keyword, limit)
    
    def search_advanced(self, filters: Dict[str, Any], limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """جستجوی پیشرفته سفارشات"""
        return self._repository.search_advanced(filters, limit, offset)
    
    def search_advanced_count(self, filters: Dict[str, Any]) -> int:
        """تعداد نتایج جستجوی پیشرفته"""
        return self._repository.search_advanced_count(filters)
    
    # ============================================================
    # آمار و گزارش‌ها
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """دریافت آمار کلی سفارشات"""
        return self._repository.get_stats()
    
    def get_revenue_by_period(self, days: int = 30) -> List[Dict[str, Any]]:
        """دریافت درآمد در بازه زمانی مشخص"""
        return self._repository.get_revenue_by_period(days)
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """دریافت آمار سفارشات یک کاربر"""
        return self._repository.get_user_order_stats(user_id)
    
    def get_orders_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """دریافت سفارشات در بازه زمانی"""
        return self._repository.get_orders_by_date_range(start_date, end_date)
    
    def get_status_history(self, order_id: int) -> List[Dict[str, Any]]:
        """دریافت تاریخچه تغییرات وضعیت سفارش"""
        return self._repository.get_status_history(order_id)
    
    def get_orders_with_files(self, limit: int = 50) -> List[Dict[str, Any]]:
        """دریافت سفارشاتی که فایل دارند"""
        return self._repository.get_orders_with_files(limit)
    
    # ============================================================
    # متدهای کاربردی
    # ============================================================
    
    def calculate_total_amount(self, user_id: int) -> int:
        """محاسبه مجموع مبلغ پرداختی یک کاربر"""
        try:
            query = """
                SELECT COALESCE(SUM(payment_amount), 0) as total
                FROM dynamic_orders
                WHERE user_id = ? AND status IN ('paid', 'completed')
            """
            result = self._repository.custom_query_one(query, [user_id])
            return result.get('total', 0) if result else 0
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            log_database_error(
                f"Error calculating total amount for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return 0
    
    def get_last_order(self, user_id: int) -> Optional[Dict[str, Any]]:
        """دریافت آخرین سفارش یک کاربر"""
        try:
            orders = self.get_orders_by_user(user_id, limit=1)
            return orders[0] if orders else None
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            log_database_error(
                f"Error getting last order for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return None
    
    def get_pending_orders(self, hours: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        دریافت سفارشات در انتظار پرداخت
        
        پارامترها:
            hours: (اختیاری) فقط سفارشاتی که بیش از hours ساعت قبل ثبت شده‌اند
        """
        try:
            if hours:
                query = """
                    SELECT * FROM dynamic_orders 
                    WHERE status = 'pending' 
                    AND created_at < datetime('now', '-' || ? || ' hours')
                    ORDER BY created_at ASC
                """
                return self._repository.custom_query(query, [hours])
            else:
                return self.get_orders_by_status('pending')
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            log_database_error(
                f"Error getting pending orders: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_orders_without_tracking(self) -> List[Dict[str, Any]]:
        """دریافت سفارشاتی که کد رهگیری ندارند (اما پرداخت شده‌اند)"""
        try:
            query = """
                SELECT * FROM dynamic_orders 
                WHERE status IN ('paid', 'completed') 
                AND (tracking_code IS NULL OR tracking_code = '')
                ORDER BY created_at DESC
            """
            return self._repository.custom_query(query)
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            log_database_error(
                f"Error getting orders without tracking: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def update_tracking_code(self, order_id: int, tracking_code: str) -> bool:
        """به‌روزرسانی کد رهگیری سفارش"""
        try:
            return self._repository.update(order_id, {'tracking_code': tracking_code})
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            log_database_error(
                f"Error updating tracking code for order {order_id}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def get_orders_summary(self) -> Dict[str, Any]:
        """دریافت خلاصه سفارشات برای داشبورد"""
        try:
            stats = self.get_stats()
            
            # محاسبه تغییرات نسبت به روز قبل
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            today_orders = self.get_orders_by_date_range(
                today.strftime("%Y-%m-%d"),
                today.strftime("%Y-%m-%d")
            )
            yesterday_orders = self.get_orders_by_date_range(
                yesterday.strftime("%Y-%m-%d"),
                yesterday.strftime("%Y-%m-%d")
            )
            
            today_count = len(today_orders)
            yesterday_count = len(yesterday_orders)
            
            growth = 0
            if yesterday_count > 0:
                growth = ((today_count - yesterday_count) / yesterday_count) * 100
            
            return {
                'total_orders': stats.get('total', 0),
                'total_amount': stats.get('total_amount', 0),
                'avg_amount': stats.get('avg_amount', 0),
                'today_orders': today_count,
                'yesterday_orders': yesterday_count,
                'growth_percent': round(growth, 1),
                'pending_orders': stats.get('statuses', {}).get('pending', 0),
                'paid_orders': stats.get('statuses', {}).get('paid', 0),
                'completed_orders': stats.get('statuses', {}).get('completed', 0),
                'cancelled_orders': stats.get('statuses', {}).get('cancelled', 0),
                'total_users': stats.get('total_users', 0),
            }
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            log_general_error(
                f"Error getting orders summary: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {}
    
    def get_recent_orders_with_details(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        دریافت سفارشات اخیر با اطلاعات کامل (نام کاربر، سرویس، ...)
        """
        try:
            orders = self.get_orders(limit, 0)
            
            result = []
            for order in orders:
                order_dict = dict(order)
                
                # اضافه کردن نام کاربر
                from models.order import Order as OrderModel
                order_obj = OrderModel.from_db(order)
                order_dict['fullname'] = order_obj.fullname
                
                # اضافه کردن نام سرویس
                from database import get_button_by_id
                button = get_button_by_id(order.get('button_id'))
                order_dict['service_name'] = button['name'] if button else 'نامشخص'
                
                result.append(order_dict)
            
            return result
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            log_general_error(
                f"Error getting recent orders with details: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_order_status_distribution(self) -> Dict[str, int]:
        """دریافت توزیع وضعیت سفارشات"""
        try:
            stats = self.get_stats()
            return stats.get('statuses', {})
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            log_general_error(
                f"Error getting order status distribution: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {}


__all__ = [
    'OrderService',
]