# config.py
# بارگذاری و مدیریت تنظیمات از متغیرهای محیطی

import os
from dotenv import load_dotenv

# بارگذاری فایل .env
load_dotenv()


class Config:
    """تنظیمات اصلی ربات"""
    
    # ============================================
    # تنظیمات اصلی ربات
    # ============================================
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
    DEFAULT_PRICE_AMOUNT = int(os.getenv("DEFAULT_PRICE_AMOUNT", 50000))
    DEFAULT_PRICE_LABEL = os.getenv("DEFAULT_PRICE_LABEL", "هزینه خدمات")
    
    # ============================================
    # تنظیمات دیتابیس
    # ============================================
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "bot_config.db")
    
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "bot_db")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "bot_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_DB = os.getenv("MYSQL_DB", "bot_db")
    MYSQL_USER = os.getenv("MYSQL_USER", "bot_user")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    
    @classmethod
    def get_database_url(cls):
        """دریافت آدرس اتصال به دیتابیس بر اساس نوع"""
        if cls.DATABASE_TYPE == "sqlite":
            return f"sqlite:///{cls.SQLITE_DB_PATH}"
        elif cls.DATABASE_TYPE == "postgresql":
            return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        elif cls.DATABASE_TYPE == "mysql":
            return f"mysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DB}"
        return f"sqlite:///{cls.SQLITE_DB_PATH}"
    
    # ============================================
    # تنظیمات Redis
    # ============================================
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
    REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", 300))
    
    @classmethod
    def get_redis_url(cls):
        """دریافت آدرس اتصال به Redis"""
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
    
    # ============================================
    # تنظیمات Rate Limiting
    # ============================================
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 30))
    
    # ============================================
    # تنظیمات پشتیبان‌گیری
    # ============================================
    BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
    MAX_BACKUP_FILES = int(os.getenv("MAX_BACKUP_FILES", 10))
    BACKUP_SCHEDULE = os.getenv("BACKUP_SCHEDULE", "0 3 * * *")
    
    # ============================================
    # تنظیمات لاگ
    # ============================================
    LOG_FILE = os.getenv("LOG_FILE", "bot.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))  # 10 MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
    LOG_ROTATION_WHEN = os.getenv("LOG_ROTATION_WHEN", "midnight")
    
    # ============================================
    # تنظیمات یادآوری سفارشات
    # ============================================
    REMINDER_INTERVAL_HOURS = int(os.getenv("REMINDER_INTERVAL_HOURS", 6))
    REMINDER_AFTER_HOURS = int(os.getenv("REMINDER_AFTER_HOURS", 24))
    
    # ============================================
    # تنظیمات پاکسازی خودکار
    # ============================================
    ERROR_RETENTION_DAYS = int(os.getenv("ERROR_RETENTION_DAYS", 60))
    LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", 90))
    
    # ============================================
    # تنظیمات برندینگ (پیش‌فرض)
    # ============================================
    BRAND_WELCOME_TEXT = os.getenv("BRAND_WELCOME_TEXT", "👋 به ربات خوش آمدید.\n🌟 لطفاً یکی از گزینه‌ها را انتخاب کنید:")
    BRAND_MAIN_MENU_TITLE = os.getenv("BRAND_MAIN_MENU_TITLE", "🔙 منوی اصلی:")
    BRAND_ADMIN_TITLE = os.getenv("BRAND_ADMIN_TITLE", "🔐 **پنل مدیریت ربات**\nلطفاً یکی از گزینه‌ها را انتخاب کنید:")
    BRAND_ORDER_SUCCESS = os.getenv("BRAND_ORDER_SUCCESS", "✅ درخواست شما ثبت شد.\n🙏 به زودی تماس می‌گیریم.")
    BRAND_PAYMENT_SUCCESS = os.getenv("BRAND_PAYMENT_SUCCESS", "✅ پرداخت موفق و ثبت سفارش.")
    BRAND_INVALID_OPTION = os.getenv("BRAND_INVALID_OPTION", "⚠️ گزینه نامعتبر است.")
    BRAND_ERROR_MESSAGE = os.getenv("BRAND_ERROR_MESSAGE", "❌ خطای داخلی رخ داده است. لطفاً دوباره تلاش کنید.")
    BRAND_FOOTER_TEXT = os.getenv("BRAND_FOOTER_TEXT", "© ۱۴۰۳ - تمامی حقوق محفوظ است")
    
    # ============================================
    # تنظیمات وضعیت کاربران (State Service)
    # ============================================
    STATE_TTL = int(os.getenv("STATE_TTL", 3600))  # زمان انقضای وضعیت کاربر (ثانیه) - پیش‌فرض ۱ ساعت
    STATE_STORAGE_TYPE = os.getenv("STATE_STORAGE_TYPE", "redis")  # redis / memory
    
    # ============================================
    # تنظیمات پیشرفته
    # ============================================
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", 30))
    DB_RETRY_COUNT = int(os.getenv("DB_RETRY_COUNT", 3))
    DB_RETRY_DELAY = int(os.getenv("DB_RETRY_DELAY", 1))
    LOOP_SLEEP_INTERVAL = float(os.getenv("LOOP_SLEEP_INTERVAL", 0.5))
    ERROR_SLEEP_INTERVAL = float(os.getenv("ERROR_SLEEP_INTERVAL", 2))
    
    # ============================================
    # تنظیمات جدید مانیتورینگ (Monitoring)
    # ============================================
    
    # آستانه هشدار خطا (تعداد خطا در ساعت)
    MONITORING_ALERT_THRESHOLD = int(os.getenv("MONITORING_ALERT_THRESHOLD", 50))
    
    # زمان بررسی دوره‌ای مانیتورینگ (ثانیه)
    MONITORING_CHECK_INTERVAL = int(os.getenv("MONITORING_CHECK_INTERVAL", 300))  # ۵ دقیقه
    
    # زمان ارسال گزارش روزانه (فرمت cron)
    MONITORING_REPORT_SCHEDULE = os.getenv("MONITORING_REPORT_SCHEDULE", "0 9 * * *")  # هر روز ساعت ۹ صبح
    
    # تعداد روزهای نگهداری متریک‌ها
    METRICS_RETENTION_DAYS = int(os.getenv("METRICS_RETENTION_DAYS", 30))
    
    # تعداد روزهای نگهداری هشدارها
    ALERTS_RETENTION_DAYS = int(os.getenv("ALERTS_RETENTION_DAYS", 90))
    
    # تعداد روزهای نگهداری گزارش‌ها
    REPORTS_RETENTION_DAYS = int(os.getenv("REPORTS_RETENTION_DAYS", 30))
    
    # آیا مانیتورینگ فعال است؟
    MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    
    # ارسال خودکار هشدارها به OWNER
    MONITORING_AUTO_NOTIFY = os.getenv("MONITORING_AUTO_NOTIFY", "true").lower() == "true"


# ============================================
# آبجکت سراسری برای دسترسی آسان
# ============================================
config = Config()