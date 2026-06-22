# repositories/order_repository.py
# ریپازیتوری سفارشات

import json
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from logger_config import logger
from .base_repository import BaseRepository
from models.order import Order, OrderStatus
from utils.error_handler import log_database_error  # ✅ اضافه شد


class OrderRepository(BaseRepository):
    """ریپازیتوری سفارشات - مدیریت عملیات دیتابیس مربوط به سفارشات"""
    
    def __init__(self, connection):
        super().__init__(connection, 'dynamic_orders', 'id')
    
    # ============================================================
    # متدهای پایه
    # ============================================================
    
    def get_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """دریافت سفارش بر اساس شناسه"""
        return super().get_by_id(order_id)
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت تمام سفارشات با صفحه‌بندی (مرتب‌شده بر اساس جدیدترین)"""
        return super().get_all(limit, offset, order_by='created_at DESC')
    
    def get_by_status(self, status: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت سفارشات بر اساس وضعیت"""
        query = """
            SELECT * FROM dynamic_orders 
            WHERE status = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        return self.custom_query(query, [status, limit, offset])
    
    def get_by_user(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت سفارشات یک کاربر"""
        query = """
            SELECT * FROM dynamic_orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        return self.custom_query(query, [user_id, limit, offset])
    
    def get_by_button(self, button_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت سفارشات یک سرویس (دکمه)"""
        query = """
            SELECT * FROM dynamic_orders 
            WHERE button_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        return self.custom_query(query, [button_id, limit, offset])
    
    def get_by_tracking_code(self, tracking_code: str) -> Optional[Dict[str, Any]]:
        """دریافت سفارش بر اساس کد رهگیری"""
        return self.get_by_field('tracking_code', tracking_code)
    
    def count_by_status(self, status: str) -> int:
        """تعداد سفارشات با وضعیت مشخص"""
        query = "SELECT COUNT(*) as count FROM dynamic_orders WHERE status = ?"
        result = self.custom_query_one(query, [status])
        return result.get('count', 0) if result else 0
    
    def count_by_user(self, user_id: int) -> int:
        """تعداد سفارشات یک کاربر"""
        query = "SELECT COUNT(*) as count FROM dynamic_orders WHERE user_id = ?"
        result = self.custom_query_one(query, [user_id])
        return result.get('count', 0) if result else 0
    
    # ============================================================
    # ایجاد و به‌روزرسانی
    # ============================================================
    
    def create(self, user_id: int, button_id: int, order_data: Dict[str, Any],
               payment_amount: int = 0, tracking_code: Optional[str] = None,
               status: str = 'pending') -> Optional[int]:
        """
        ایجاد سفارش جدید
        
        پارامترها:
            user_id: شناسه کاربر
            button_id: شناسه دکمه
            order_data: داده‌های سفارش (پاسخ‌ها و ...)
            payment_amount: مبلغ پرداختی
            tracking_code: کد رهگیری
            status: وضعیت اولیه
        
        بازگشت: شناسه سفارش ایجادشده
        """
        data = {
            'user_id': user_id,
            'button_id': button_id,
            'order_data': json.dumps(order_data, ensure_ascii=False),
            'payment_amount': payment_amount,
            'tracking_code': tracking_code,
            'status': status,
            'created_at': datetime.now().isoformat()
        }
        return self.insert(data)
    
    def update_status(self, order_id: int, new_status: str, user_id: int,
                      note: Optional[str] = None) -> bool:
        """
        تغییر وضعیت سفارش و ثبت در تاریخچه
        
        پارامترها:
            order_id: شناسه سفارش
            new_status: وضعیت جدید
            user_id: شناسه کاربر انجام‌دهنده
            note: یادداشت اختیاری
        """
        # دریافت وضعیت فعلی
        order = self.get_by_id(order_id)
        if not order:
            return False
        
        old_status = order.get('status', 'pending')
        if old_status == new_status:
            return True
        
        # به‌روزرسانی وضعیت
        success = self.update(order_id, {
            'status': new_status,
            'updated_at': datetime.now().isoformat()
        })
        
        if success:
            # افزودن به تاریخچه وضعیت‌ها
            history = order.get('status_history')
            if isinstance(history, str):
                try:
                    history = json.loads(history)
                except Exception as e:
                    log_database_error(
                        f"Error parsing status_history for order {order_id}: {str(e)}",
                        traceback=traceback.format_exc()
                    )
                    history = []
            elif not history:
                history = []
            
            history.append({
                'from': old_status,
                'to': new_status,
                'by': user_id,
                'timestamp': datetime.now().isoformat(),
                'note': note
            })
            
            self.update(order_id, {
                'status_history': json.dumps(history, ensure_ascii=False)
            })
            
            logger.info(f"✅ Order {order_id} status changed from {old_status} to {new_status} by {user_id}")
        
        return success
    
    def add_note(self, order_id: int, note: str, user_id: int) -> bool:
        """
        افزودن یادداشت به سفارش
        
        پارامترها:
            order_id: شناسه سفارش
            note: متن یادداشت
            user_id: شناسه کاربر
        """
        order = self.get_by_id(order_id)
        if not order:
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_note = f"[{timestamp}] {note}"
        
        admin_note = order.get('admin_note', '')
        if admin_note:
            admin_note += f"\n{new_note}"
        else:
            admin_note = new_note
        
        return self.update(order_id, {
            'admin_note': admin_note,
            'updated_at': datetime.now().isoformat()
        })
    
    def delete(self, order_id: int) -> bool:
        """حذف یک سفارش"""
        return super().delete(order_id)
    
    # ============================================================
    # جستجوی پیشرفته
    # ============================================================
    
    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        جستجوی سفارشات بر اساس کلمه کلیدی
        
        پارامترها:
            keyword: کلمه کلیدی (شناسه، کاربر، کد رهگیری، نام)
            limit: حداکثر تعداد نتایج
        
        بازگشت: لیست سفارشات یافت‌شده
        """
        # جستجو در شناسه، کاربر، کد رهگیری
        if keyword.isdigit():
            query = """
                SELECT * FROM dynamic_orders 
                WHERE id = ? OR user_id = ? OR tracking_code LIKE ?
                ORDER BY created_at DESC 
                LIMIT ?
            """
            params = [int(keyword), int(keyword), f"%{keyword}%", limit]
            results = self.custom_query(query, params)
        else:
            # جستجو در order_data (پاسخ‌ها)
            # ابتدا سفارشات را بگیریم و سپس فیلتر کنیم
            all_orders = self.custom_query(
                "SELECT * FROM dynamic_orders ORDER BY created_at DESC LIMIT ?",
                [limit * 5]
            )
            results = []
            keyword_lower = keyword.lower()
            
            for order in all_orders:
                # جستجو در کد رهگیری
                tracking = order.get('tracking_code', '')
                if tracking and keyword_lower in tracking.lower():
                    results.append(order)
                    continue
                
                # جستجو در order_data
                order_data = order.get('order_data', {})
                if isinstance(order_data, str):
                    try:
                        order_data = json.loads(order_data)
                    except Exception as e:
                        log_database_error(
                            f"Error parsing order_data in search for order {order.get('id')}: {str(e)}",
                            traceback=traceback.format_exc()
                        )
                        order_data = {}
                
                # جستجو در پاسخ‌ها
                answers = order_data.get('answers', {})
                found = False
                for q_text, ans in answers.items():
                    if ans and keyword_lower in str(ans).lower():
                        found = True
                        break
                
                if found:
                    results.append(order)
                
                if len(results) >= limit:
                    break
        
        return results[:limit]
    
    def search_advanced(self, filters: Dict[str, Any], limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        جستجوی پیشرفته با فیلترهای متعدد
        
        پارامترها:
            filters: دیکشنری فیلترها شامل:
                - status: وضعیت (یا لیست وضعیت‌ها)
                - user_id: شناسه کاربر
                - button_id: شناسه دکمه
                - start_date: تاریخ شروع (YYYY-MM-DD)
                - end_date: تاریخ پایان (YYYY-MM-DD)
                - min_amount: حداقل مبلغ
                - max_amount: حداکثر مبلغ
                - tracking_code: کد رهگیری
                - has_file: آیا فایل دارد
                - keyword: کلمه کلیدی
            limit: تعداد نتایج
            offset: موقعیت شروع
        
        بازگشت: لیست سفارشات
        """
        conditions = []
        params = []
        
        # فیلتر وضعیت
        if 'status' in filters:
            statuses = filters['status']
            if isinstance(statuses, list):
                placeholders = ','.join(['?' for _ in statuses])
                conditions.append(f"status IN ({placeholders})")
                params.extend(statuses)
            else:
                conditions.append("status = ?")
                params.append(statuses)
        
        # فیلتر کاربر
        if 'user_id' in filters:
            conditions.append("user_id = ?")
            params.append(filters['user_id'])
        
        # فیلتر سرویس
        if 'button_id' in filters:
            conditions.append("button_id = ?")
            params.append(filters['button_id'])
        
        # فیلتر تاریخ
        if 'start_date' in filters:
            conditions.append("date(created_at) >= ?")
            params.append(filters['start_date'])
        if 'end_date' in filters:
            conditions.append("date(created_at) <= ?")
            params.append(filters['end_date'])
        
        # فیلتر مبلغ
        if 'min_amount' in filters:
            conditions.append("payment_amount >= ?")
            params.append(filters['min_amount'])
        if 'max_amount' in filters:
            conditions.append("payment_amount <= ?")
            params.append(filters['max_amount'])
        
        # فیلتر کد رهگیری
        if 'tracking_code' in filters:
            conditions.append("tracking_code LIKE ?")
            params.append(f"%{filters['tracking_code']}%")
        
        # ساخت کوئری
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM dynamic_orders 
            WHERE {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        results = self.custom_query(query, params)
        
        # فیلتر سفارش‌های دارای فایل (در صورت درخواست)
        if 'has_file' in filters and filters['has_file']:
            filtered = []
            for order in results:
                order_data = order.get('order_data', {})
                if isinstance(order_data, str):
                    try:
                        order_data = json.loads(order_data)
                    except Exception as e:
                        log_database_error(
                            f"Error parsing order_data in search_advanced (has_file) for order {order.get('id')}: {str(e)}",
                            traceback=traceback.format_exc()
                        )
                        order_data = {}
                files = order_data.get('files', {})
                if files:
                    filtered.append(order)
            return filtered
        
        # جستجو در پاسخ‌ها (keyword)
        if 'keyword' in filters and filters['keyword']:
            keyword = filters['keyword'].lower()
            filtered = []
            for order in results:
                order_data = order.get('order_data', {})
                if isinstance(order_data, str):
                    try:
                        order_data = json.loads(order_data)
                    except Exception as e:
                        log_database_error(
                            f"Error parsing order_data in search_advanced (keyword) for order {order.get('id')}: {str(e)}",
                            traceback=traceback.format_exc()
                        )
                        order_data = {}
                answers = order_data.get('answers', {})
                found = False
                for q_text, ans in answers.items():
                    if ans and keyword in str(ans).lower():
                        found = True
                        break
                if found:
                    filtered.append(order)
            return filtered
        
        return results
    
    def search_advanced_count(self, filters: Dict[str, Any]) -> int:
        """تعداد نتایج جستجوی پیشرفته"""
        conditions = []
        params = []
        
        # همان فیلترها
        if 'status' in filters:
            statuses = filters['status']
            if isinstance(statuses, list):
                placeholders = ','.join(['?' for _ in statuses])
                conditions.append(f"status IN ({placeholders})")
                params.extend(statuses)
            else:
                conditions.append("status = ?")
                params.append(statuses)
        
        if 'user_id' in filters:
            conditions.append("user_id = ?")
            params.append(filters['user_id'])
        
        if 'button_id' in filters:
            conditions.append("button_id = ?")
            params.append(filters['button_id'])
        
        if 'start_date' in filters:
            conditions.append("date(created_at) >= ?")
            params.append(filters['start_date'])
        if 'end_date' in filters:
            conditions.append("date(created_at) <= ?")
            params.append(filters['end_date'])
        
        if 'min_amount' in filters:
            conditions.append("payment_amount >= ?")
            params.append(filters['min_amount'])
        if 'max_amount' in filters:
            conditions.append("payment_amount <= ?")
            params.append(filters['max_amount'])
        
        if 'tracking_code' in filters:
            conditions.append("tracking_code LIKE ?")
            params.append(f"%{filters['tracking_code']}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT COUNT(*) as count FROM dynamic_orders WHERE {where_clause}"
        
        result = self.custom_query_one(query, params)
        return result.get('count', 0) if result else 0
    
    # ============================================================
    # آمار و گزارش‌ها
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        دریافت آمار کلی سفارشات
        
        بازگشت: دیکشنری شامل:
            - total: تعداد کل
            - total_amount: مجموع مبلغ
            - avg_amount: میانگین مبلغ
            - statuses: تفکیک وضعیت‌ها
            - top_service: بیشترین سرویس
            - total_users: تعداد کاربران
        """
        # آمار کلی
        query = """
            SELECT 
                COUNT(*) as total,
                COALESCE(SUM(payment_amount), 0) as total_amount,
                COALESCE(AVG(payment_amount), 0) as avg_amount
            FROM dynamic_orders
        """
        stats = self.custom_query_one(query) or {}
        
        # تفکیک وضعیت‌ها
        status_query = """
            SELECT status, COUNT(*) as count 
            FROM dynamic_orders 
            GROUP BY status
        """
        statuses = self.custom_query(status_query)
        stats['statuses'] = statuses
        
        # بیشترین سرویس
        service_query = """
            SELECT button_id, COUNT(*) as count 
            FROM dynamic_orders 
            GROUP BY button_id 
            ORDER BY count DESC 
            LIMIT 1
        """
        top_service = self.custom_query_one(service_query)
        stats['top_service_id'] = top_service.get('button_id') if top_service else None
        stats['top_service_count'] = top_service.get('count') if top_service else 0
        
        # تعداد کاربران
        user_query = "SELECT COUNT(DISTINCT user_id) as total_users FROM dynamic_orders"
        user_result = self.custom_query_one(user_query)
        stats['total_users'] = user_result.get('total_users', 0) if user_result else 0
        
        return stats
    
    def get_revenue_by_period(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        دریافت درآمد در بازه زمانی مشخص
        
        پارامترها:
            days: تعداد روزهای اخیر
        
        بازگشت: لیست دیکشنری‌های تاریخ و درآمد
        """
        query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as orders,
                COALESCE(SUM(payment_amount), 0) as revenue
            FROM dynamic_orders 
            WHERE created_at >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at) DESC
        """
        return self.custom_query(query, [days])
    
    def get_user_order_stats(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت آمار سفارشات یک کاربر
        
        بازگشت: دیکشنری شامل total_orders, total_amount, avg_amount, statuses
        """
        query = """
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(payment_amount), 0) as total_amount,
                COALESCE(AVG(payment_amount), 0) as avg_amount
            FROM dynamic_orders 
            WHERE user_id = ?
        """
        stats = self.custom_query_one(query, [user_id]) or {}
        
        status_query = """
            SELECT status, COUNT(*) as count 
            FROM dynamic_orders 
            WHERE user_id = ? 
            GROUP BY status
        """
        statuses = self.custom_query(status_query, [user_id])
        stats['statuses'] = statuses
        
        return stats
    
    def get_orders_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        دریافت سفارشات در بازه زمانی
        
        پارامترها:
            start_date: تاریخ شروع (YYYY-MM-DD)
            end_date: تاریخ پایان (YYYY-MM-DD)
        """
        query = """
            SELECT * FROM dynamic_orders 
            WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?
            ORDER BY created_at DESC
        """
        return self.custom_query(query, [start_date, end_date])
    
    def get_status_history(self, order_id: int) -> List[Dict[str, Any]]:
        """
        دریافت تاریخچه تغییرات وضعیت یک سفارش
        
        پارامترها:
            order_id: شناسه سفارش
        
        بازگشت: لیست تغییرات
        """
        order = self.get_by_id(order_id)
        if not order:
            return []
        
        history = order.get('status_history')
        if isinstance(history, str):
            try:
                return json.loads(history)
            except Exception as e:
                log_database_error(
                    f"Error parsing status_history for order {order_id}: {str(e)}",
                    traceback=traceback.format_exc()
                )
                return []
        return history or []
    
    def get_orders_with_files(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        دریافت سفارشاتی که فایل دارند
        
        پارامترها:
            limit: حداکثر تعداد نتایج
        
        بازگشت: لیست سفارشات دارای فایل
        """
        all_orders = self.custom_query(
            "SELECT * FROM dynamic_orders ORDER BY created_at DESC LIMIT ?",
            [limit * 3]
        )
        
        result = []
        for order in all_orders:
            order_data = order.get('order_data', {})
            if isinstance(order_data, str):
                try:
                    order_data = json.loads(order_data)
                except Exception as e:
                    log_database_error(
                        f"Error parsing order_data in get_orders_with_files for order {order.get('id')}: {str(e)}",
                        traceback=traceback.format_exc()
                    )
                    order_data = {}
            files = order_data.get('files', {})
            if files:
                result.append(order)
            if len(result) >= limit:
                break
        
        return result
    
    def get_orders_by_service_id(self, button_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """دریافت سفارشات یک سرویس با صفحه‌بندی"""
        return self.get_by_button(button_id, limit, offset)


__all__ = [
    'OrderRepository',
]