# repositories/base_repository.py
# ریپازیتوری پایه با متدهای CRUD عمومی

import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any, TypeVar, Generic
from database.interfaces import DatabaseConnection
from logger_config import logger
from utils.error_handler import log_database_error, log_general_error  # ✅ اضافه شد

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    کلاس پایه ریپازیتوری با متدهای CRUD عمومی
    برای استفاده توسط ریپازیتوری‌های خاص
    """
    
    def __init__(self, connection: DatabaseConnection, table_name: str, primary_key: str = 'id'):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            table_name: نام جدول
            primary_key: نام کلید اصلی (پیش‌فرض: id)
        """
        self._connection = connection
        self._table_name = table_name
        self._primary_key = primary_key
    
    @property
    def connection(self) -> DatabaseConnection:
        return self._connection
    
    @property
    def table(self) -> str:
        return self._table_name
    
    @property
    def pk(self) -> str:
        return self._primary_key
    
    def _get_columns(self, data: Dict[str, Any]) -> tuple:
        """استخراج ستون‌ها و مقادیر از دیکشنری"""
        columns = []
        values = []
        for key, value in data.items():
            columns.append(key)
            values.append(value)
        return columns, values
    
    def _build_placeholders(self, count: int) -> str:
        """ساخت placeholder برای کوئری"""
        return ', '.join(['?' for _ in range(count)])
    
    def _build_update_string(self, data: Dict[str, Any]) -> tuple:
        """ساخت بخش SET کوئری UPDATE"""
        columns = []
        values = []
        for key, value in data.items():
            if key != self._primary_key:
                columns.append(f"{key} = ?")
                values.append(value)
        return ', '.join(columns), values
    
    def insert(self, data: Dict[str, Any]) -> Optional[int]:
        """
        درج یک رکورد جدید در جدول
        
        پارامترها:
            data: دیکشنری داده‌ها
        
        بازگشت: شناسه رکورد درج‌شده یا None در صورت خطا
        """
        try:
            columns, values = self._get_columns(data)
            placeholders = self._build_placeholders(len(values))
            
            query = f"INSERT INTO {self._table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, values)
                self._connection.commit()
                return cursor.get_lastrowid()
                
        except Exception as e:
            log_database_error(
                f"Error inserting into {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return None
    
    def insert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """
        درج چندین رکورد به صورت دسته‌ای
        
        پارامترها:
            data_list: لیست دیکشنری‌های داده‌ها
        
        بازگشت: تعداد رکوردهای درج‌شده
        """
        if not data_list:
            return 0
        
        try:
            # گرفتن ستون‌ها از اولین رکورد
            columns = list(data_list[0].keys())
            placeholders = self._build_placeholders(len(columns))
            
            values_list = []
            for data in data_list:
                values = [data.get(col) for col in columns]
                values_list.append(tuple(values))
            
            query = f"INSERT INTO {self._table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            with self._connection.get_cursor() as cursor:
                cursor.executemany(query, values_list)
                self._connection.commit()
                return cursor.get_rowcount()
                
        except Exception as e:
            log_database_error(
                f"Error inserting many into {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return 0
    
    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        دریافت یک رکورد بر اساس شناسه
        
        پارامترها:
            record_id: شناسه رکورد
        
        بازگشت: دیکشنری داده‌ها یا None
        """
        try:
            query = f"SELECT * FROM {self._table_name} WHERE {self._primary_key} = ?"
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (record_id,))
                return cursor.fetchone()
        except Exception as e:
            log_database_error(
                f"Error getting by id from {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        دریافت یک رکورد بر اساس یک فیلد خاص
        
        پارامترها:
            field: نام فیلد
            value: مقدار فیلد
        
        بازگشت: دیکشنری داده‌ها یا None
        """
        try:
            query = f"SELECT * FROM {self._table_name} WHERE {field} = ? LIMIT 1"
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (value,))
                return cursor.fetchone()
        except Exception as e:
            log_database_error(
                f"Error getting by field from {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_all(self, limit: int = 100, offset: int = 0, order_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        دریافت تمام رکوردها با صفحه‌بندی
        
        پارامترها:
            limit: تعداد رکوردها
            offset: موقعیت شروع
            order_by: فیلد مرتب‌سازی (اختیاری)
        
        بازگشت: لیست دیکشنری‌های داده‌ها
        """
        try:
            query = f"SELECT * FROM {self._table_name}"
            if order_by:
                query += f" ORDER BY {order_by}"
            query += f" LIMIT ? OFFSET ?"
            
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (limit, offset))
                return cursor.fetchall()
        except Exception as e:
            log_database_error(
                f"Error getting all from {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def count(self, where: Optional[str] = None, params: Optional[List[Any]] = None) -> int:
        """
        دریافت تعداد کل رکوردها
        
        پارامترها:
            where: شرط WHERE (اختیاری)
            params: پارامترهای شرط
        
        بازگشت: تعداد رکوردها
        """
        try:
            query = f"SELECT COUNT(*) as count FROM {self._table_name}"
            if where:
                query += f" WHERE {where}"
            
            with self._connection.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                row = cursor.fetchone()
                return row.get('count', 0) if row else 0
        except Exception as e:
            log_database_error(
                f"Error counting from {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def exists(self, field: str, value: Any) -> bool:
        """
        بررسی وجود رکورد بر اساس یک فیلد
        
        پارامترها:
            field: نام فیلد
            value: مقدار فیلد
        
        بازگشت: True اگر وجود داشته باشد
        """
        try:
            query = f"SELECT 1 FROM {self._table_name} WHERE {field} = ? LIMIT 1"
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (value,))
                return cursor.fetchone() is not None
        except Exception as e:
            log_database_error(
                f"Error checking existence in {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """
        به‌روزرسانی یک رکورد بر اساس شناسه
        
        پارامترها:
            record_id: شناسه رکورد
            data: دیکشنری داده‌های جدید
        
        بازگشت: True در صورت موفقیت
        """
        try:
            set_string, values = self._build_update_string(data)
            if not set_string:
                return True
            
            values.append(record_id)
            query = f"UPDATE {self._table_name} SET {set_string} WHERE {self._primary_key} = ?"
            
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, values)
                self._connection.commit()
                return cursor.get_rowcount() > 0
        except Exception as e:
            log_database_error(
                f"Error updating {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return False
    
    def update_by_field(self, field: str, value: Any, data: Dict[str, Any]) -> int:
        """
        به‌روزرسانی رکوردها بر اساس یک فیلد
        
        پارامترها:
            field: نام فیلد شرط
            value: مقدار فیلد شرط
            data: دیکشنری داده‌های جدید
        
        بازگشت: تعداد رکوردهای به‌روزرسانی‌شده
        """
        try:
            set_string, values = self._build_update_string(data)
            if not set_string:
                return 0
            
            values.append(value)
            query = f"UPDATE {self._table_name} SET {set_string} WHERE {field} = ?"
            
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, values)
                self._connection.commit()
                return cursor.get_rowcount()
        except Exception as e:
            log_database_error(
                f"Error updating by field in {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return 0
    
    def delete(self, record_id: int) -> bool:
        """
        حذف یک رکورد بر اساس شناسه
        
        پارامترها:
            record_id: شناسه رکورد
        
        بازگشت: True در صورت موفقیت
        """
        try:
            query = f"DELETE FROM {self._table_name} WHERE {self._primary_key} = ?"
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (record_id,))
                self._connection.commit()
                return cursor.get_rowcount() > 0
        except Exception as e:
            log_database_error(
                f"Error deleting from {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return False
    
    def delete_by_field(self, field: str, value: Any) -> int:
        """
        حذف رکوردها بر اساس یک فیلد
        
        پارامترها:
            field: نام فیلد شرط
            value: مقدار فیلد شرط
        
        بازگشت: تعداد رکوردهای حذف‌شده
        """
        try:
            query = f"DELETE FROM {self._table_name} WHERE {field} = ?"
            with self._connection.get_cursor() as cursor:
                cursor.execute(query, (value,))
                self._connection.commit()
                return cursor.get_rowcount()
        except Exception as e:
            log_database_error(
                f"Error deleting by field from {self._table_name}: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return 0
    
    def custom_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        اجرای کوئری سفارشی
        
        پارامترها:
            query: کوئری SQL
            params: پارامترهای کوئری (اختیاری)
        
        بازگشت: لیست دیکشنری‌های نتایج
        """
        try:
            with self._connection.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            log_database_error(
                f"Error executing custom query: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def custom_query_one(self, query: str, params: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
        """
        اجرای کوئری سفارشی و دریافت یک نتیجه
        
        پارامترها:
            query: کوئری SQL
            params: پارامترهای کوئری (اختیاری)
        
        بازگشت: دیکشنری نتیجه یا None
        """
        try:
            with self._connection.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchone()
        except Exception as e:
            log_database_error(
                f"Error executing custom query one: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def custom_execute(self, query: str, params: Optional[List[Any]] = None) -> int:
        """
        اجرای کوئری بدون بازگشت نتیجه (INSERT, UPDATE, DELETE)
        
        پارامترها:
            query: کوئری SQL
            params: پارامترهای کوئری (اختیاری)
        
        بازگشت: تعداد ردیف‌های تحت تأثیر
        """
        try:
            with self._connection.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                self._connection.commit()
                return cursor.get_rowcount()
        except Exception as e:
            log_database_error(
                f"Error executing custom execute: {str(e)}",
                traceback=traceback.format_exc()
            )
            self._connection.rollback()
            return 0
    
    def begin_transaction(self):
        """شروع تراکنش"""
        self._connection.begin()
    
    def commit_transaction(self):
        """ثبت تراکنش"""
        self._connection.commit()
    
    def rollback_transaction(self):
        """برگشت تراکنش"""
        self._connection.rollback()


__all__ = [
    'BaseRepository',
]