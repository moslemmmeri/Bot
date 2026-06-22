# database/interfaces.py
# کلاس‌های انتزاعی برای اتصال به دیتابیس
# پشتیبانی از SQLite, PostgreSQL, MySQL

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from contextlib import AbstractContextManager


# ============================================================
# استثناهای پایه
# ============================================================

class ConnectionError(Exception):
    """خطا در برقراری اتصال به دیتابیس"""
    pass


class QueryError(Exception):
    """خطا در اجرای کوئری"""
    pass


class IntegrityError(QueryError):
    """خطای یکپارچگی داده (مانند کلید خارجی یا unique)"""
    pass


class NotFoundError(QueryError):
    """رکورد مورد نظر یافت نشد"""
    pass


# ============================================================
# رابط‌های انتزاعی
# ============================================================

class DatabaseCursor(ABC):
    """رابط انتزاعی برای Cursor دیتابیس"""
    
    @abstractmethod
    def execute(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> 'DatabaseCursor':
        """اجرای کوئری با پارامترها"""
        pass
    
    @abstractmethod
    def executemany(self, query: str, params: List[Union[Tuple, Dict]]) -> 'DatabaseCursor':
        """اجرای کوئری با چندین مجموعه پارامتر"""
        pass
    
    @abstractmethod
    def fetchone(self) -> Optional[Dict]:
        """دریافت یک ردیف"""
        pass
    
    @abstractmethod
    def fetchall(self) -> List[Dict]:
        """دریافت تمام ردیف‌ها"""
        pass
    
    @abstractmethod
    def fetchmany(self, size: int) -> List[Dict]:
        """دریافت تعداد مشخصی ردیف"""
        pass
    
    @abstractmethod
    def get_lastrowid(self) -> Optional[int]:
        """دریافت آخرین شناسه‌ی درج‌شده"""
        pass
    
    @abstractmethod
    def get_rowcount(self) -> int:
        """دریافت تعداد ردیف‌های تحت تأثیر"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """بستن Cursor"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DatabaseConnection(ABC):
    """رابط انتزاعی برای اتصال به دیتابیس"""
    
    @abstractmethod
    def connect(self) -> None:
        """برقراری اتصال به دیتابیس"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """بستن اتصال"""
        pass
    
    @abstractmethod
    def execute(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> DatabaseCursor:
        """اجرای کوئری"""
        pass
    
    @abstractmethod
    def fetchone(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> Optional[Dict]:
        """دریافت یک ردیف"""
        pass
    
    @abstractmethod
    def fetchall(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> List[Dict]:
        """دریافت تمام ردیف‌ها"""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """ثبت تغییرات"""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """برگشت تغییرات"""
        pass
    
    @abstractmethod
    def get_cursor(self) -> DatabaseCursor:
        """دریافت یک Cursor"""
        pass
    
    @abstractmethod
    def get_lastrowid(self) -> Optional[int]:
        """دریافت آخرین شناسه‌ی درج‌شده"""
        pass
    
    @abstractmethod
    def get_rowcount(self) -> int:
        """دریافت تعداد ردیف‌های تحت تأثیر آخرین کوئری"""
        pass
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


class DatabaseDriver(ABC):
    """رابط انتزاعی برای درایور دیتابیس"""
    
    @abstractmethod
    def get_connection(self) -> DatabaseConnection:
        """دریافت اتصال به دیتابیس"""
        pass
    
    @abstractmethod
    def get_connection_string(self) -> str:
        """دریافت رشته اتصال"""
        pass
    
    @abstractmethod
    def get_driver_name(self) -> str:
        """دریافت نام درایور"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """بررسی در دسترس بودن درایور"""
        pass
    
    @abstractmethod
    def get_placeholders(self) -> str:
        """دریافت placeholder برای پارامترها (?, $, %s)"""
        pass


__all__ = [
    'DatabaseConnection',
    'DatabaseCursor',
    'DatabaseDriver',
    'ConnectionError',
    'QueryError',
    'IntegrityError',
    'NotFoundError',
]