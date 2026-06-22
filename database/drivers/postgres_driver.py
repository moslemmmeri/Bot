# database/drivers/postgres_driver.py
# درایور PostgreSQL برای دیتابیس (با استفاده از asyncpg)

import asyncio
import asyncpg
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


class PostgresCursor(DatabaseCursor):
    """پیاده‌سازی Cursor برای PostgreSQL (با asyncpg)"""
    
    def __init__(self, connection: asyncpg.Connection):
        self._connection = connection
        self._lastrowid = None
        self._rowcount = 0
        self._result = None
        self._index = 0
    
    def _convert_row(self, row: Union[asyncpg.Record, Dict]) -> Dict:
        """تبدیل ردیف به دیکشنری"""
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        return dict(row)
    
    def execute(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> 'PostgresCursor':
        """اجرای کوئری با پارامترها"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # اگر در حلقه‌ی asyncio هستیم
                if params:
                    if isinstance(params, dict):
                        self._result = asyncio.run_coroutine_threadsafe(
                            self._connection.fetch(query, **params),
                            loop
                        ).result()
                    else:
                        self._result = asyncio.run_coroutine_threadsafe(
                            self._connection.fetch(query, *params),
                            loop
                        ).result()
                else:
                    self._result = asyncio.run_coroutine_threadsafe(
                        self._connection.fetch(query),
                        loop
                    ).result()
            else:
                # اگر خارج از حلقه هستیم
                if params:
                    if isinstance(params, dict):
                        self._result = asyncio.run(self._connection.fetch(query, **params))
                    else:
                        self._result = asyncio.run(self._connection.fetch(query, *params))
                else:
                    self._result = asyncio.run(self._connection.fetch(query))
            
            self._rowcount = len(self._result) if self._result else 0
            self._index = 0
            
            # دریافت lastrowid (برای INSERT)
            if query.strip().upper().startswith("INSERT") and self._result:
                try:
                    self._lastrowid = self._result[0].get('id') or self._result[0].get('ID')
                except:
                    pass
            
            return self
        except asyncpg.exceptions.UniqueViolationError as e:
            logger.error(f"PostgreSQL unique violation: {e}\nQuery: {query}")
            raise IntegrityError(str(e)) from e
        except asyncpg.exceptions.ForeignKeyViolationError as e:
            logger.error(f"PostgreSQL foreign key violation: {e}\nQuery: {query}")
            raise IntegrityError(str(e)) from e
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"PostgreSQL error: {e}\nQuery: {query}")
            raise QueryError(str(e)) from e
        except Exception as e:
            logger.error(f"PostgreSQL execute error: {e}\nQuery: {query}")
            raise QueryError(str(e)) from e
    
    def executemany(self, query: str, params: List[Union[Tuple, Dict]]) -> 'PostgresCursor':
        """اجرای کوئری با چندین مجموعه پارامتر"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                if params and isinstance(params[0], dict):
                    # برای دیکشنری‌ها
                    self._result = asyncio.run_coroutine_threadsafe(
                        self._connection.fetch(query, *params),
                        loop
                    ).result()
                else:
                    self._result = asyncio.run_coroutine_threadsafe(
                        self._connection.fetch(query, *params),
                        loop
                    ).result()
            else:
                if params and isinstance(params[0], dict):
                    self._result = asyncio.run(self._connection.fetch(query, *params))
                else:
                    self._result = asyncio.run(self._connection.fetch(query, *params))
            
            self._rowcount = len(self._result) if self._result else 0
            self._index = 0
            return self
        except Exception as e:
            logger.error(f"PostgreSQL executemany error: {e}\nQuery: {query}")
            raise QueryError(str(e)) from e
    
    def fetchone(self) -> Optional[Dict]:
        """دریافت یک ردیف"""
        try:
            if not self._result or self._index >= len(self._result):
                return None
            row = self._result[self._index]
            self._index += 1
            return self._convert_row(row)
        except Exception as e:
            logger.error(f"PostgreSQL fetchone error: {e}")
            raise QueryError(str(e)) from e
    
    def fetchall(self) -> List[Dict]:
        """دریافت تمام ردیف‌ها"""
        try:
            if not self._result:
                return []
            remaining = self._result[self._index:]
            self._index = len(self._result)
            return [self._convert_row(row) for row in remaining]
        except Exception as e:
            logger.error(f"PostgreSQL fetchall error: {e}")
            raise QueryError(str(e)) from e
    
    def fetchmany(self, size: int) -> List[Dict]:
        """دریافت تعداد مشخصی ردیف"""
        try:
            if not self._result:
                return []
            end = min(self._index + size, len(self._result))
            rows = self._result[self._index:end]
            self._index = end
            return [self._convert_row(row) for row in rows]
        except Exception as e:
            logger.error(f"PostgreSQL fetchmany error: {e}")
            raise QueryError(str(e)) from e
    
    def get_lastrowid(self) -> Optional[int]:
        """دریافت آخرین شناسه‌ی درج‌شده"""
        return self._lastrowid
    
    def get_rowcount(self) -> int:
        """دریافت تعداد ردیف‌های تحت تأثیر"""
        return self._rowcount
    
    def close(self) -> None:
        """بستن Cursor"""
        self._result = None
        self._index = 0


class PostgresConnection(DatabaseConnection):
    """پیاده‌سازی اتصال برای PostgreSQL (با asyncpg)"""
    
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None):
        self._host = host or config.POSTGRES_HOST
        self._port = port or config.POSTGRES_PORT
        self._database = database or config.POSTGRES_DB
        self._user = user or config.POSTGRES_USER
        self._password = password or config.POSTGRES_PASSWORD
        self._connection: Optional[asyncpg.Connection] = None
        self._is_connected = False
        self._retry_count = config.DB_RETRY_COUNT
        self._retry_delay = config.DB_RETRY_DELAY
    
    def connect(self) -> None:
        """برقراری اتصال به PostgreSQL"""
        if self._is_connected and self._connection:
            return
        
        last_error = None
        for attempt in range(self._retry_count):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self._connection = asyncio.run_coroutine_threadsafe(
                        asyncpg.connect(
                            host=self._host,
                            port=self._port,
                            database=self._database,
                            user=self._user,
                            password=self._password
                        ),
                        loop
                    ).result(timeout=30)
                else:
                    self._connection = asyncio.run(asyncpg.connect(
                        host=self._host,
                        port=self._port,
                        database=self._database,
                        user=self._user,
                        password=self._password
                    ))
                
                self._is_connected = True
                logger.info(f"✅ PostgreSQL connection established: {self._host}:{self._port}/{self._database}")
                return
            except asyncpg.exceptions.PostgresError as e:
                last_error = e
                logger.warning(f"PostgreSQL connection attempt {attempt+1}/{self._retry_count} failed: {e}")
                if attempt < self._retry_count - 1:
                    time.sleep(self._retry_delay)
            except Exception as e:
                last_error = e
                logger.error(f"PostgreSQL connection error: {e}")
                break
        
        raise ConnectionError(f"Failed to connect to PostgreSQL: {last_error}")
    
    def close(self) -> None:
        """بستن اتصال به دیتابیس"""
        if self._connection:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self._connection.close(),
                        loop
                    ).result(timeout=10)
                else:
                    asyncio.run(self._connection.close())
            except Exception as e:
                logger.warning(f"Error closing PostgreSQL connection: {e}")
            self._connection = None
            self._is_connected = False
    
    def _ensure_connection(self) -> asyncpg.Connection:
        """اطمینان از وجود اتصال"""
        if not self._is_connected or not self._connection:
            self.connect()
        return self._connection
    
    def execute(self, query: str, params: Optional[Union[Tuple, Dict]] = None) -> PostgresCursor:
        """اجرای کوئری"""
        conn = self._ensure_connection()
        cursor = PostgresCursor(conn)
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
        """ثبت تغییرات (در PostgreSQL با asyncpg خودکار است)"""
        # در asyncpg commit خودکار است
        pass
    
    def rollback(self) -> None:
        """برگشت تغییرات"""
        # در asyncpg rollback خودکار است
        pass
    
    def get_cursor(self) -> PostgresCursor:
        """دریافت یک Cursor"""
        conn = self._ensure_connection()
        return PostgresCursor(conn)
    
    def get_lastrowid(self) -> Optional[int]:
        """دریافت آخرین شناسه‌ی درج‌شده"""
        # با استفاده از RETURNING در کوئری انجام می‌شود
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


class PostgreSQLDriver(DatabaseDriver):
    """درایور PostgreSQL"""
    
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None):
        self._host = host or config.POSTGRES_HOST
        self._port = port or config.POSTGRES_PORT
        self._database = database or config.POSTGRES_DB
        self._user = user or config.POSTGRES_USER
        self._password = password or config.POSTGRES_PASSWORD
        self._driver_name = "postgresql"
    
    def get_connection(self) -> PostgresConnection:
        """دریافت اتصال به دیتابیس"""
        return PostgresConnection(
            host=self._host,
            port=self._port,
            database=self._database,
            user=self._user,
            password=self._password
        )
    
    def get_connection_string(self) -> str:
        """دریافت رشته اتصال"""
        return f"postgresql://{self._user}:{'*' * len(self._password)}@{self._host}:{self._port}/{self._database}"
    
    def get_driver_name(self) -> str:
        """دریافت نام درایور"""
        return self._driver_name
    
    def is_available(self) -> bool:
        """بررسی در دسترس بودن درایور"""
        try:
            import asyncpg
            return True
        except ImportError:
            return False
    
    def get_placeholders(self) -> str:
        """دریافت placeholder برای پارامترها"""
        return "$"  # PostgreSQL از $1, $2, ... استفاده می‌کند


# ============================================================
# توابع کمکی برای سازگاری با کدهای قبلی
# ============================================================

def get_postgres_connection() -> PostgresConnection:
    """دریافت یک اتصال PostgreSQL جدید"""
    return PostgresConnection()


def get_postgres_driver() -> PostgreSQLDriver:
    """دریافت درایور PostgreSQL"""
    return PostgreSQLDriver()


__all__ = [
    'PostgresConnection',
    'PostgresCursor',
    'PostgreSQLDriver',
    'get_postgres_connection',
    'get_postgres_driver',
]