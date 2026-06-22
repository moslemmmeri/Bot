# database/drivers/sqlite_driver.py
# درایور SQLite برای دیتابیس

import sqlite3
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from logger_config import logger
from config import config
from ..interfaces import (
    DatabaseConnection,
    DatabaseCursor,
    DatabaseDriver,
    ConnectionError,
    QueryError,
    IntegrityError,
    NotFoundError,
)


class SQLiteCursor(DatabaseCursor):
    """پیاده‌سازی Cursor برای SQLite"""
    
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection
        self._cursor = None
        self._lastrowid = None
        self._rowcount = 0
    
    def _ensure_cursor(self) -> sqlite3.Cursor:
        """اطمینان از وجود Cursor"""
        if self._cursor is None:
            self._cursor = self._connection.cursor()
            self._cursor.row_factory = sqlite3.Row
        return self._cursor
    
    def execute(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> 'SQLiteCursor':
        """اجرای کوئری با پارامترها"""
        try:
            cursor = self._ensure_cursor()
            if params:
                if isinstance(params, dict):
                    cursor.execute(query, params)
                else:
                    cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            self._lastrowid = cursor.lastrowid
            self._rowcount = cursor.rowcount
            return self
        except sqlite3.IntegrityError as e:
            logger.error(f"SQLite integrity error: {e}\nQuery: {query}")
            raise IntegrityError(str(e)) from e
        except sqlite3.OperationalError as e:
            logger.error(f"SQLite operational error: {e}\nQuery: {query}")
            raise QueryError(str(e)) from e
        except Exception as e:
            logger.error(f"SQLite execute error: {e}\nQuery: {query}")
            raise QueryError(str(e)) from e
    
    def executemany(self, query: str, params: List[Union[Tuple, Dict]]) -> 'SQLiteCursor':
        """اجرای کوئری با چندین مجموعه پارامتر"""
        try:
            cursor = self._ensure_cursor()
            cursor.executemany(query, params)
            self._lastrowid = cursor.lastrowid
            self._rowcount = cursor.rowcount
            return self
        except sqlite3.IntegrityError as e:
            logger.error(f"SQLite integrity error: {e}\nQuery: {query}")
            raise IntegrityError(str(e)) from e
        except Exception as e:
            logger.error(f"SQLite executemany error: {e}\nQuery: {query}")
            raise QueryError(str(e)) from e
    
    def fetchone(self) -> Optional[Dict]:
        """دریافت یک ردیف"""
        try:
            cursor = self._ensure_cursor()
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"SQLite fetchone error: {e}")
            raise QueryError(str(e)) from e
    
    def fetchall(self) -> List[Dict]:
        """دریافت تمام ردیف‌ها"""
        try:
            cursor = self._ensure_cursor()
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"SQLite fetchall error: {e}")
            raise QueryError(str(e)) from e
    
    def fetchmany(self, size: int) -> List[Dict]:
        """دریافت تعداد مشخصی ردیف"""
        try:
            cursor = self._ensure_cursor()
            rows = cursor.fetchmany(size)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"SQLite fetchmany error: {e}")
            raise QueryError(str(e)) from e
    
    def get_lastrowid(self) -> Optional[int]:
        """دریافت آخرین شناسه‌ی درج‌شده"""
        return self._lastrowid
    
    def get_rowcount(self) -> int:
        """دریافت تعداد ردیف‌های تحت تأثیر"""
        return self._rowcount
    
    def close(self) -> None:
        """بستن Cursor"""
        if self._cursor:
            try:
                self._cursor.close()
            except:
                pass
            self._cursor = None


class SQLiteConnection(DatabaseConnection):
    """پیاده‌سازی اتصال برای SQLite"""
    
    def __init__(self, db_path: str = None):
        self._db_path = db_path or config.SQLITE_DB_PATH
        self._connection: Optional[sqlite3.Connection] = None
        self._is_connected = False
        self._retry_count = config.DB_RETRY_COUNT
        self._retry_delay = config.DB_RETRY_DELAY
    
    def connect(self) -> None:
        """برقراری اتصال به دیتابیس SQLite"""
        if self._is_connected and self._connection:
            return
        
        # ایجاد پوشه‌ی دیتابیس در صورت عدم وجود
        db_dir = os.path.dirname(self._db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        last_error = None
        for attempt in range(self._retry_count):
            try:
                self._connection = sqlite3.connect(
                    self._db_path,
                    timeout=20,
                    check_same_thread=False
                )
                self._connection.row_factory = sqlite3.Row
                self._connection.execute("PRAGMA foreign_keys = ON")
                self._connection.execute("PRAGMA journal_mode = WAL")
                self._connection.execute("PRAGMA synchronous = NORMAL")
                self._connection.execute("PRAGMA cache_size = 10000")
                self._is_connected = True
                logger.info(f"✅ SQLite connection established: {self._db_path}")
                return
            except sqlite3.OperationalError as e:
                last_error = e
                logger.warning(f"SQLite connection attempt {attempt+1}/{self._retry_count} failed: {e}")
                if attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
            except Exception as e:
                last_error = e
                logger.error(f"SQLite connection error: {e}")
                break
        
        raise ConnectionError(f"Failed to connect to SQLite: {last_error}")
    
    def close(self) -> None:
        """بستن اتصال به دیتابیس"""
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                logger.warning(f"Error closing SQLite connection: {e}")
            self._connection = None
            self._is_connected = False
    
    def _ensure_connection(self) -> sqlite3.Connection:
        """اطمینان از وجود اتصال"""
        if not self._is_connected or not self._connection:
            self.connect()
        return self._connection
    
    def execute(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> SQLiteCursor:
        """اجرای کوئری"""
        conn = self._ensure_connection()
        cursor = SQLiteCursor(conn)
        return cursor.execute(query, params)
    
    def fetchone(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> Optional[Dict]:
        """دریافت یک ردیف"""
        with self.execute(query, params) as cursor:
            return cursor.fetchone()
    
    def fetchall(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> List[Dict]:
        """دریافت تمام ردیف‌ها"""
        with self.execute(query, params) as cursor:
            return cursor.fetchall()
    
    def commit(self) -> None:
        """ثبت تغییرات"""
        if self._connection:
            try:
                self._connection.commit()
            except Exception as e:
                logger.error(f"SQLite commit error: {e}")
                raise QueryError(str(e)) from e
    
    def rollback(self) -> None:
        """برگشت تغییرات"""
        if self._connection:
            try:
                self._connection.rollback()
            except Exception as e:
                logger.error(f"SQLite rollback error: {e}")
                raise QueryError(str(e)) from e
    
    def get_cursor(self) -> SQLiteCursor:
        """دریافت یک Cursor"""
        conn = self._ensure_connection()
        return SQLiteCursor(conn)
    
    def get_lastrowid(self) -> Optional[int]:
        """دریافت آخرین شناسه‌ی درج‌شده"""
        if self._connection:
            return self._connection.lastrowid
        return None
    
    def get_rowcount(self) -> int:
        """دریافت تعداد ردیف‌های تحت تأثیر آخرین کوئری"""
        if self._connection:
            try:
                return self._connection.total_changes
            except:
                pass
        return 0
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


class SQLiteDriver(DatabaseDriver):
    """درایور SQLite"""
    
    def __init__(self, db_path: str = None):
        self._db_path = db_path or config.SQLITE_DB_PATH
        self._driver_name = "sqlite"
    
    def get_connection(self) -> SQLiteConnection:
        """دریافت اتصال به دیتابیس"""
        return SQLiteConnection(self._db_path)
    
    def get_connection_string(self) -> str:
        """دریافت رشته اتصال"""
        return f"sqlite:///{self._db_path}"
    
    def get_driver_name(self) -> str:
        """دریافت نام درایور"""
        return self._driver_name
    
    def is_available(self) -> bool:
        """بررسی در دسترس بودن درایور"""
        try:
            import sqlite3
            return True
        except ImportError:
            return False
    
    def get_placeholders(self) -> str:
        """دریافت placeholder برای پارامترها"""
        return "?"  # SQLite از ? استفاده می‌کند


# ============================================================
# توابع کمکی برای سازگاری با کدهای قبلی
# ============================================================

def get_sqlite_connection() -> SQLiteConnection:
    """دریافت یک اتصال SQLite جدید"""
    return SQLiteConnection()


def get_sqlite_driver() -> SQLiteDriver:
    """دریافت درایور SQLite"""
    return SQLiteDriver()


__all__ = [
    'SQLiteConnection',
    'SQLiteCursor',
    'SQLiteDriver',
    'get_sqlite_connection',
    'get_sqlite_driver',
]