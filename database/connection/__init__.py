# database/connection/__init__.py
# پکیج مدیریت اتصال به دیتابیس
# شامل: مدیریت اتصال، مهاجرت‌ها و مقداردهی اولیه

"""
پکیج `connection` مسئول مدیریت اتصال به دیتابیس، انجام مهاجرت‌ها و مقداردهی اولیه است.

زیرماژول‌ها:
- manager: مدیریت اتصال به دیتابیس (get_db_connection, init_db)
- migrations: مدیریت نسخه‌بندی و مهاجرت دیتابیس
- init: مقداردهی اولیه جداول و داده‌های پیش‌فرض

استفاده:
    from database.connection import get_db_connection, init_db, migrate_to_latest
"""

# ============================================================
# ایمپورت از زیرماژول‌ها
# ============================================================

from .manager import (
    get_db_connection,
    DB_NAME,
    init_db,
    add_validation_columns_if_not_exists,
    add_order_columns_if_not_exists,
    add_price_columns_if_not_exists,
    add_user_block_columns_if_not_exists,
    add_user_extra_columns_if_not_exists,
    create_order_logs_table,
    add_columns_if_not_exists,
    create_question_templates_table,
    get_connection_pool,
    close_connection_pool,
    is_connected,
    get_db_status,
)

from .migrations import (
    MIGRATIONS_TABLE,
    CURRENT_VERSION,
    ensure_migrations_table,
    get_current_version,
    get_applied_migrations,
    record_migration,
    apply_migration,
    migrate_to_version,
    migrate_to_latest,
    get_pending_migrations,
    get_migration_status,
    generate_checksum,
    validate_migration_integrity,
    get_migration_sql,
    reset_migrations,
    force_version,
    run_migrations_if_needed,
)

from .init import (
    create_tables,
    create_default_categories,
    add_owner_to_admins,
    set_default_settings,
    ensure_default_data,
    recreate_database,
    get_table_list,
    get_table_schema,
    get_table_count,
)


# ============================================================
# صادر کردن همه توابع
# ============================================================

__all__ = [
    # manager
    'get_db_connection',
    'DB_NAME',
    'init_db',
    'add_validation_columns_if_not_exists',
    'add_order_columns_if_not_exists',
    'add_price_columns_if_not_exists',
    'add_user_block_columns_if_not_exists',
    'add_user_extra_columns_if_not_exists',
    'create_order_logs_table',
    'add_columns_if_not_exists',
    'create_question_templates_table',
    'get_connection_pool',
    'close_connection_pool',
    'is_connected',
    'get_db_status',
    
    # migrations
    'MIGRATIONS_TABLE',
    'CURRENT_VERSION',
    'ensure_migrations_table',
    'get_current_version',
    'get_applied_migrations',
    'record_migration',
    'apply_migration',
    'migrate_to_version',
    'migrate_to_latest',
    'get_pending_migrations',
    'get_migration_status',
    'generate_checksum',
    'validate_migration_integrity',
    'get_migration_sql',
    'reset_migrations',
    'force_version',
    'run_migrations_if_needed',
    
    # init
    'create_tables',
    'create_default_categories',
    'add_owner_to_admins',
    'set_default_settings',
    'ensure_default_data',
    'recreate_database',
    'get_table_list',
    'get_table_schema',
    'get_table_count',
]