# database/drivers/mysql_driver.py
# درایور MySQL برای دیتابیس (با استفاده از aiomysql)

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from logger_config import logger
from config import config

try:
    import aiomysql
    AIOMYSQL_AVAILABLE = True
except ImportError:
    AIOMYSQL_AVAILABLE = False
    logger.warning("aiomysql not installed. MySQL driver will not be available.")

from ..interfaces import (
    DatabaseConnection,
    DatabaseCursor,
    DatabaseDriver,
    ConnectionError,
    QueryError,
    IntegrityError,
    NotFoundError,
)


class MySQLCursor(DatabaseCursor):
    """پیاده‌سازی Cursor برای MySQL (با aiomysql)"""
    
    def __init__(self, connection: aiomysql.Connection, pool: aiomysql.Pool = None):
        self._connection = connection
        self._pool = pool
        self._cursor = None
        self._lastrowid = None
        self._rowcount = 0
        self._result = None
        self._index = 0
        self._dict_cursor = None
    
    async def _ensure_cursor(self) -> aiomysql.DictCursor:
        """اطمینان از وجود Cursor به صورت دیکشنری"""
        if self._dict_cursor is None:
            if self._pool:
                self._connection = await self._pool.acquire()
            self._dict_cursor = await self._connection.cursor(aiomysql.DictCursor)
        return self._dict_cursor
    
    def _convert_params(self, params: Optional[Union[Tuple, Dict]]) -> tuple:
        """تبدیل پارامترها به Tuple برای MySQL"""
        if params is None:
            return ()
        if isinstance(params, dict):
            # MySQL با نام‌های پارامتر پشتیبانی نمی‌کند، فقط position
            return tuple(params.values())
        return tuple(params)
    
    def execute(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> 'MySQLCursor':
        """اجرای کوئری با پارامترها"""
        try:
            loop = asyncio.get_event_loop()
            params_tuple = self._convert_params(params)
            
            if loop.is_running():
                # اگر در حلقه‌ی asyncio هستیم
                cursor = asyncio.run_coroutine_threadsafe(
                    self._ensure_cursor(),
                    loop
                ).result(timeout=30)
                
                asyncio.run_coroutine_threadsafe(
                    cursor.execute(query, params_tuple),
                    loop
                ).result(timeout=30)
                
                self._lastrowid = cursor.lastrowid
                self._rowcount = cursor.rowcount
                self._result = cursor
                self._index = 0
            else:
                # خارج از حلقه
                cursor = asyncio.run(self._ensure_cursor())
                asyncio.run(cursor.execute(query, params_tuple))
                self._lastrowid = cursor.lastrowid
                self._rowcount = cursor.rowcount
                self._result = cursor
                self._index = 0
            
            return self
        except aiomysql.IntegrityError as e:
            logger.error(f"MySQL integrity error: {e}\nQuery: {query}")
            raise IntegrityError(str(e)) from e
        except aiomysql.OperationalError as e:
            logger.error(f"MySQL operational error: {e}\nQuery: {query}")
            raise QueryError(str(e)) from e
        except Exception as e:
            logger.error(f"MySQL execute error: {e}\nQuery: {query}")
            raise QueryError(str(e)) from e
    
    def executemany(self, query: str, params: List[Union[Tuple, Dict]]) -> 'MySQLCursor':
        """اجرای کوئری با چندین مجموعه پارامتر"""
        try:
            loop = asyncio.get_event_loop()
            # تبدیل همه پارامترها به Tuple
            params_list = [self._convert_params(p) for p in params]
            
            if loop.is_running():
                cursor = asyncio.run_coroutine_threadsafe(
                    self._ensure_cursor(),
                    loop
                ).result(timeout=30)
                
                asyncio.run_coroutine_threadsafe(
                    cursor.executemany(query, params_list),
                    loop
                ).result(timeout=30)
                
                self._lastrowid = cursor.lastrowid
                self._rowcount = cursor.rowcount
                self._result = cursor
                self._index = 0
            else:
                cursor = asyncio.run(self._ensure_cursor())
                asyncio.run(cursor.executemany(query, params_list))
                self._lastrowid = cursor.lastrowid
                self._rowcount = cursor.rowcount
                self._result = cursor
                self._index = 0
            
            return self
        except Exception as e:
            logger.error(f"MySQL executemany error: {e}\nQuery: {query}")
            raise QueryError(str(e)) from e
    
    def fetchone(self) -> Optional[Dict]:
        """دریافت یک ردیف"""
        try:
            if not self._result:
                return None
            if self._index > 0:
                # اگر قبلاً fetchone یا fetchall انجام شده، از نتیجه استفاده می‌کنیم
                return None
            loop = asyncio.get_event_loop()
            if loop.is_running():
                row = asyncio.run_coroutine_threadsafe(
                    self._result.fetchone(),
                    loop
                ).result(timeout=30)
            else:
                row = asyncio.run(self._result.fetchone())
            return row
        except Exception as e:
            logger.error(f"MySQL fetchone error: {e}")
            raise QueryError(str(e)) from e
    
    def fetchall(self) -> List[Dict]:
        """دریافت تمام ردیف‌ها"""
        try:
            if not self._result:
                return []
            loop = asyncio.get_event_loop()
            if loop.is_running():
                rows = asyncio.run_coroutine_threadsafe(
                    self._result.fetchall(),
                    loop
                ).result(timeout=30)
            else:
                rows = asyncio.run(self._result.fetchall())
            return rows if rows else []
        except Exception as e:
            logger.error(f"MySQL fetchall error: {e}")
            raise QueryError(str(e)) from e
    
    def fetchmany(self, size: int) -> List[Dict]:
        """دریافت تعداد مشخصی ردیف"""
        try:
            if not self._result:
                return []
            loop = asyncio.get_event_loop()
            if loop.is_running():
                rows = asyncio.run_coroutine_threadsafe(
                    self._result.fetchmany(size),
                    loop
                ).result(timeout=30)
            else:
                rows = asyncio.run(self._result.fetchmany(size))
            return rows if rows else []
        except Exception as e:
            logger.error(f"MySQL fetchmany error: {e}")
            raise QueryError(str(e)) from e
    
    def get_lastrowid(self) -> Optional[int]:
        """دریافت آخرین شناسه‌ی درج‌شده"""
        return self._lastrowid
    
    def get_rowcount(self) -> int:
        """دریافت تعداد ردیف‌های تحت تأثیر"""
        return self._rowcount
    
    def close(self) -> None:
        """بستن Cursor"""
        if self._dict_cursor:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self._dict_cursor.close(),
                        loop
                    ).result(timeout=10)
                else:
                    asyncio.run(self._dict_cursor.close())
            except Exception as e:
                logger.warning(f"Error closing MySQL cursor: {e}")
            self._dict_cursor = None
        
        if self._pool and self._connection:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self._pool.release(self._connection),
                        loop
                    ).result(timeout=10)
                else:
                    asyncio.run(self._pool.release(self._connection))
            except Exception as e:
                logger.warning(f"Error releasing MySQL connection: {e}")
            self._connection = None
        
        self._result = None
        self._index = 0


class MySQLConnection(DatabaseConnection):
    """پیاده‌سازی اتصال برای MySQL (با aiomysql)"""
    
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None):
        self._host = host or config.MYSQL_HOST
        self._port = port or config.MYSQL_PORT
        self._database = database or config.MYSQL_DB
        self._user = user or config.MYSQL_USER
        self._password = password or config.MYSQL_PASSWORD
        self._pool: Optional[aiomysql.Pool] = None
        self._connection: Optional[aiomysql.Connection] = None
        self._is_connected = False
        self._retry_count = config.DB_RETRY_COUNT
        self._retry_delay = config.DB_RETRY_DELAY
        
        if not AIOMYSQL_AVAILABLE:
            raise ConnectionError("aiomysql is not installed. Please install it with: pip install aiomysql")
    
    def connect(self) -> None:
        """برقراری اتصال به MySQL"""
        if self._is_connected and self._pool:
            return
        
        last_error = None
        for attempt in range(self._retry_count):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self._pool = asyncio.run_coroutine_threadsafe(
                        aiomysql.create_pool(
                            host=self._host,
                            port=self._port,
                            db=self._database,
                            user=self._user,
                            password=self._password,
                            autocommit=True,
                            minsize=1,
                            maxsize=10,
                            pool_recycle=3600,
                            init_command="SET NAMES utf8mb4",
                            charset='utf8mb4'
                        ),
                        loop
                    ).result(timeout=30)
                else:
                    self._pool = asyncio.run(aiomysql.create_pool(
                        host=self._host,
                        port=self._port,
                        db=self._database,
                        user=self._user,
                        password=self._password,
                        autocommit=True,
                        minsize=1,
                        maxsize=10,
                        pool_recycle=3600,
                        init_command="SET NAMES utf8mb4",
                        charset='utf8mb4'
                    ))
                
                self._is_connected = True
                logger.info(f"✅ MySQL connection established: {self._host}:{self._port}/{self._database}")
                return
            except aiomysql.OperationalError as e:
                last_error = e
                logger.warning(f"MySQL connection attempt {attempt+1}/{self._retry_count} failed: {e}")
                if attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
            except Exception as e:
                last_error = e
                logger.error(f"MySQL connection error: {e}")
                break
        
        raise ConnectionError(f"Failed to connect to MySQL: {last_error}")
    
    def close(self) -> None:
        """بستن اتصال به دیتابیس"""
        if self._pool:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self._pool.close(),
                        loop
                    ).result(timeout=10)
                    asyncio.run_coroutine_threadsafe(
                        self._pool.wait_closed(),
                        loop
                    ).result(timeout=10)
                else:
                    asyncio.run(self._pool.close())
                    asyncio.run(self._pool.wait_closed())
            except Exception as e:
                logger.warning(f"Error closing MySQL pool: {e}")
            self._pool = None
            self._is_connected = False
    
    def _ensure_connection(self) -> aiomysql.Pool:
        """اطمینان از وجود اتصال"""
        if not self._is_connected or not self._pool:
            self.connect()
        return self._pool
    
    def execute(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> MySQLCursor:
        """اجرای کوئری"""
        pool = self._ensure_connection()
        # یک کانکشن از پول بگیرید
        loop = asyncio.get_event_loop()
        if loop.is_running():
            conn = asyncio.run_coroutine_threadsafe(
                pool.acquire(),
                loop
            ).result(timeout=30)
        else:
            conn = asyncio.run(pool.acquire())
        
        cursor = MySQLCursor(conn, pool)
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
        """ثبت تغییرات (در MySQL با autocommit=True خودکار است)"""
        pass
    
    def rollback(self) -> None:
        """برگشت تغییرات"""
        pass
    
    def get_cursor(self) -> MySQLCursor:
        """دریافت یک Cursor"""
        pool = self._ensure_connection()
        loop = asyncio.get_event_loop()
        if loop.is_running():
            conn = asyncio.run_coroutine_threadsafe(
                pool.acquire(),
                loop
            ).result(timeout=30)
        else:
            conn = asyncio.run(pool.acquire())
        return MySQLCursor(conn, pool)
    
    def get_lastrowid(self) -> Optional[int]:
        """دریافت آخرین شناسه‌ی درج‌شده"""
        return None
    
    def get_rowcount(self) -> int:
        """دریافت تعداد ردیف‌های تحت تأثیر آخرین کوئری"""
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


class MySQLDriver(DatabaseDriver):
    """درایور MySQL"""
    
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None):
        self._host = host or config.MYSQL_HOST
        self._port = port or config.MYSQL_PORT
        self._database = database or config.MYSQL_DB
        self._user = user or config.MYSQL_USER
        self._password = password or config.MYSQL_PASSWORD
        self._driver_name = "mysql"
    
    def get_connection(self) -> MySQLConnection:
        """دریافت اتصال به دیتابیس"""
        return MySQLConnection(
            host=self._host,
            port=self._port,
            database=self._database,
            user=self._user,
            password=self._password
        )
    
    def get_connection_string(self) -> str:
        """دریافت رشته اتصال"""
        return f"mysql://{self._user}:{'*' * len(self._password)}@{self._host}:{self._port}/{self._database}"
    
    def get_driver_name(self) -> str:
        """دریافت نام درایور"""
        return self._driver_name
    
    def is_available(self) -> bool:
        """بررسی در دسترس بودن درایور"""
        return AIOMYSQL_AVAILABLE
    
    def get_placeholders(self) -> str:
        """دریافت placeholder برای پارامترها"""
        return "%s"  # MySQL از %s استفاده می‌کند


# ============================================================
# توابع کمکی برای سازگاری با کدهای قبلی
# ============================================================

def get_mysql_connection() -> MySQLConnection:
    """دریافت یک اتصال MySQL جدید"""
    return MySQLConnection()


def get_mysql_driver() -> MySQLDriver:
    """دریافت درایور MySQL"""
    return MySQLDriver()


__all__ = [
    'MySQLConnection',
    'MySQLCursor',
    'MySQLDriver',
    'get_mysql_connection',
    'get_mysql_driver',
]