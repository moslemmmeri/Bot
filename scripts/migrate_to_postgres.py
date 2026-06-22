# scripts/migrate_to_postgres.py
# اسکریپت مهاجرت از SQLite به PostgreSQL

import os
import sys
import sqlite3
import asyncio
import asyncpg
from datetime import datetime
from typing import Dict, List, Any, Optional

# افزودن مسیر پروژه به sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from logger_config import logger


# ============================================================
# تنظیمات
# ============================================================

BATCH_SIZE = 1000  # تعداد رکورد در هر بچ


# ============================================================
# توابع کمکی
# ============================================================

def get_sqlite_connection() -> sqlite3.Connection:
    """دریافت اتصال به SQLite"""
    conn = sqlite3.connect(config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def get_postgres_connection() -> asyncpg.Connection:
    """دریافت اتصال به PostgreSQL"""
    return await asyncpg.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        database=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD
    )


def get_table_list(conn: sqlite3.Connection) -> List[str]:
    """دریافت لیست تمام جداول دیتابیس"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]


def get_table_schema(conn: sqlite3.Connection, table_name: str) -> List[Dict]:
    """دریافت ساختار یک جدول"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [dict(col) for col in columns]


def get_table_data(conn: sqlite3.Connection, table_name: str, offset: int = 0, limit: int = BATCH_SIZE) -> List[Dict]:
    """دریافت داده‌های یک جدول با صفحه‌بندی"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_table_count(conn: sqlite3.Connection, table_name: str) -> int:
    """دریافت تعداد رکوردهای یک جدول"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    row = cursor.fetchone()
    return row[0] if row else 0


def convert_value(value: Any, sqlite_type: str) -> Any:
    """تبدیل مقدار از SQLite به PostgreSQL"""
    if value is None:
        return None
    
    # تبدیل boolean
    if sqlite_type.upper() == 'INTEGER' and isinstance(value, int):
        return value
    
    # تبدیل تاریخ
    if sqlite_type.upper() in ('TEXT', 'DATETIME'):
        if isinstance(value, str):
            # بررسی فرمت تاریخ SQLite
            try:
                if '-' in value and ':' in value:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                pass
    
    # تبدیل JSON
    if sqlite_type.upper() == 'TEXT' and isinstance(value, str):
        if value.startswith('{') or value.startswith('['):
            try:
                import json
                json.loads(value)
                return value  # JSON معتبر است
            except:
                pass
    
    return value


def get_postgres_type(sqlite_type: str) -> str:
    """تبدیل نوع داده SQLite به PostgreSQL"""
    type_map = {
        'INTEGER': 'INTEGER',
        'REAL': 'REAL',
        'TEXT': 'TEXT',
        'BLOB': 'BYTEA',
        'DATETIME': 'TIMESTAMP',
        'BOOLEAN': 'BOOLEAN',
    }
    return type_map.get(sqlite_type.upper(), 'TEXT')


def get_primary_key(conn: sqlite3.Connection, table_name: str) -> Optional[str]:
    """دریافت کلید اصلی جدول"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        if col[5] == 1:  # pk
            return col[1]
    return None


# ============================================================
= توابع اصلی مهاجرت
# ============================================================

async def create_postgres_tables(conn: asyncpg.Connection, sqlite_conn: sqlite3.Connection):
    """ایجاد جداول در PostgreSQL بر اساس ساختار SQLite"""
    tables = get_table_list(sqlite_conn)
    
    for table in tables:
        schema = get_table_schema(sqlite_conn, table)
        if not schema:
            continue
        
        columns = []
        for col in schema:
            col_name = col['name']
            col_type = get_postgres_type(col['type'])
            is_nullable = '' if col['notnull'] else 'NULL'
            pk = 'PRIMARY KEY' if col['pk'] else ''
            columns.append(f'"{col_name}" {col_type} {is_nullable} {pk}'.strip())
        
        # حذف جدول در صورت وجود
        await conn.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
        
        # ایجاد جدول
        create_query = f'CREATE TABLE "{table}" (\n  ' + ',\n  '.join(columns) + '\n)'
        try:
            await conn.execute(create_query)
            logger.info(f"✅ Table created: {table}")
        except Exception as e:
            logger.error(f"❌ Error creating table {table}: {e}")
            raise


async def migrate_table_data(conn: asyncpg.Connection, sqlite_conn: sqlite3.Connection, table_name: str):
    """انتقال داده‌های یک جدول از SQLite به PostgreSQL"""
    total_rows = get_table_count(sqlite_conn, table_name)
    if total_rows == 0:
        logger.info(f"⏭️ Table {table_name} is empty, skipping.")
        return
    
    schema = get_table_schema(sqlite_conn, table_name)
    columns = [col['name'] for col in schema]
    column_types = {col['name']: col['type'] for col in schema}
    
    # ساخت کوئری INSERT
    column_names = ', '.join([f'"{col}"' for col in columns])
    placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
    insert_query = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders})'
    
    # انتقال داده‌ها به صورت بچ
    offset = 0
    total_migrated = 0
    
    while offset < total_rows:
        rows = get_table_data(sqlite_conn, table_name, offset, BATCH_SIZE)
        if not rows:
            break
        
        # تبدیل داده‌ها
        batch_data = []
        for row in rows:
            converted_row = []
            for col in columns:
                value = row.get(col)
                converted = convert_value(value, column_types.get(col, 'TEXT'))
                converted_row.append(converted)
            batch_data.append(tuple(converted_row))
        
        try:
            await conn.executemany(insert_query, batch_data)
            total_migrated += len(batch_data)
            offset += len(batch_data)
            logger.info(f"📊 {table_name}: migrated {total_migrated}/{total_rows} rows")
        except Exception as e:
            logger.error(f"❌ Error migrating {table_name} batch at offset {offset}: {e}")
            raise
    
    logger.info(f"✅ {table_name}: migrated {total_migrated} rows successfully")


async def migrate_table_sequences(conn: asyncpg.Connection, sqlite_conn: sqlite3.Connection, table_name: str):
    """تنظیم سکانس‌های PostgreSQL برای جدول"""
    pk = get_primary_key(sqlite_conn, table_name)
    if not pk:
        return
    
    # دریافت حداکثر مقدار کلید اصلی
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT MAX({pk}) as max_id FROM {table_name}")
    row = cursor.fetchone()
    max_id = row[0] if row and row[0] else 1
    
    if max_id:
        try:
            sequence_name = f'"{table_name}_{pk}_seq"'
            await conn.execute(f"SELECT setval('{sequence_name}', {max_id})")
            logger.info(f"✅ Sequence {table_name}_{pk}_seq set to {max_id}")
        except Exception as e:
            logger.warning(f"⚠️ Could not set sequence for {table_name}: {e}")


async def run_migration():
    """اجرای کامل مهاجرت"""
    logger.info("=" * 60)
    logger.info("🔄 Starting migration from SQLite to PostgreSQL")
    logger.info("=" * 60)
    
    # اتصال به SQLite
    sqlite_conn = None
    pg_conn = None
    
    try:
        # 1. اتصال به دیتابیس‌ها
        logger.info("📌 Connecting to databases...")
        sqlite_conn = get_sqlite_connection()
        pg_conn = await get_postgres_connection()
        logger.info("✅ Connected to both databases")
        
        # 2. دریافت لیست جداول
        tables = get_table_list(sqlite_conn)
        logger.info(f"📊 Found {len(tables)} tables: {', '.join(tables)}")
        
        # 3. ایجاد جداول در PostgreSQL
        logger.info("\n📌 Creating tables in PostgreSQL...")
        await create_postgres_tables(pg_conn, sqlite_conn)
        logger.info("✅ Tables created successfully")
        
        # 4. انتقال داده‌ها
        logger.info("\n📌 Migrating data...")
        for table in tables:
            logger.info(f"\n🔄 Migrating table: {table}")
            await migrate_table_data(pg_conn, sqlite_conn, table)
        
        # 5. تنظیم سکانس‌ها
        logger.info("\n📌 Setting sequences...")
        for table in tables:
            await migrate_table_sequences(pg_conn, sqlite_conn, table)
        
        # 6. گزارش نهایی
        logger.info("\n" + "=" * 60)
        logger.info("✅ Migration completed successfully!")
        logger.info("=" * 60)
        
        # نمایش خلاصه
        logger.info("\n📊 Summary:")
        for table in tables:
            count = get_table_count(sqlite_conn, table)
            logger.info(f"  - {table}: {count} rows")
        
        logger.info("\n📌 Next steps:")
        logger.info("  1. Update config.DATABASE_TYPE = 'postgresql'")
        logger.info("  2. Restart the bot")
        logger.info("  3. Verify all data is correct")
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}", exc_info=True)
        if pg_conn:
            await pg_conn.execute("ROLLBACK")
        sys.exit(1)
    
    finally:
        # بستن اتصالات
        if sqlite_conn:
            sqlite_conn.close()
            logger.info("🔒 SQLite connection closed")
        
        if pg_conn:
            await pg_conn.close()
            logger.info("🔒 PostgreSQL connection closed")


async def verify_migration():
    """بررسی صحت مهاجرت"""
    logger.info("\n🔍 Verifying migration...")
    
    sqlite_conn = get_sqlite_connection()
    pg_conn = await get_postgres_connection()
    
    try:
        tables = get_table_list(sqlite_conn)
        all_ok = True
        
        for table in tables:
            # تعداد رکوردها
            sqlite_count = get_table_count(sqlite_conn, table)
            
            pg_result = await pg_conn.fetch(f'SELECT COUNT(*) as count FROM "{table}"')
            pg_count = pg_result[0]['count'] if pg_result else 0
            
            if sqlite_count == pg_count:
                logger.info(f"✅ {table}: {sqlite_count} rows (match)")
            else:
                logger.error(f"❌ {table}: SQLite={sqlite_count}, PostgreSQL={pg_count} (mismatch)")
                all_ok = False
        
        if all_ok:
            logger.info("\n✅ All tables verified successfully!")
        else:
            logger.warning("\n⚠️ Some tables have mismatched counts. Please check manually.")
            
    finally:
        sqlite_conn.close()
        await pg_conn.close()


def main():
    """ورودی اصلی اسکریپت"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate SQLite database to PostgreSQL')
    parser.add_argument('--verify', action='store_true', help='Verify migration only')
    parser.add_argument('--dry-run', action='store_true', help='Show what will be migrated without performing migration')
    
    args = parser.parse_args()
    
    if args.verify:
        asyncio.run(verify_migration())
        return
    
    if args.dry_run:
        sqlite_conn = get_sqlite_connection()
        tables = get_table_list(sqlite_conn)
        print("\n📊 Tables to migrate:")
        for table in tables:
            count = get_table_count(sqlite_conn, table)
            schema = get_table_schema(sqlite_conn, table)
            print(f"  - {table}: {count} rows, {len(schema)} columns")
        sqlite_conn.close()
        return
    
    # اجرای مهاجرت
    asyncio.run(run_migration())


if __name__ == "__main__":
    main()