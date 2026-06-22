# cache_keys.py
# ثابت‌های کلیدهای کش برای استفاده در سراسر پروژه

import traceback  # ✅ اضافه شد برای traceback کامل
from utils.error_handler import log_general_error  # ✅ اضافه شد


class CacheKeys:
    """ثابت‌های کلیدهای کش برای مدیریت یکپارچه"""
    
    # ============================================
    # کلیدهای کاربران
    # ============================================
    USER = "user:{user_id}"
    USERS_LIST = "users:list:{page}:{limit}"
    USERS_SEARCH = "users:search:{keyword}"
    USER_STATS = "user:stats:{user_id}"
    USER_ORDERS = "user:orders:{user_id}"
    USERS_TOTAL = "users:total"
    USERS_ACTIVE = "users:active:{days}"
    
    # ============================================
    # کلیدهای دکمه‌ها
    # ============================================
    BUTTON = "button:{button_id}"
    BUTTONS_BY_LOCATION = "buttons:location:{location}"
    BUTTONS_BY_CATEGORY = "buttons:category:{category_id}"
    BUTTONS_BY_PARENT = "buttons:parent:{parent_id}"
    ALL_BUTTONS = "buttons:all"
    BUTTON_CALLBACK = "button:callback:{callback_data}"
    BUTTONS_WITH_SUBMENU = "buttons:submenu:{button_id}"
    
    # ============================================
    # کلیدهای دسته‌بندی‌ها
    # ============================================
    CATEGORY = "category:{category_id}"
    CATEGORIES_ALL = "categories:all"
    CATEGORIES_WITH_BUTTONS = "categories:with_buttons:{location}"
    CATEGORIES_ADMIN = "categories:admin"
    CATEGORY_BY_LOCATION = "category:location:{location}"
    CATEGORY_COLUMNS = "category:columns:{category_id}"
    
    # ============================================
    # کلیدهای سوالات
    # ============================================
    QUESTIONS_BY_BUTTON = "questions:button:{button_id}"
    QUESTION = "question:{question_id}"
    OPTIONS_BY_QUESTION = "options:question:{question_id}"
    CONDITIONS_BY_QUESTION = "conditions:question:{question_id}"
    OPTION_BY_CALLBACK = "option:callback:{callback_data}"
    VALIDATION_SETTINGS = "validation:settings:{question_id}"
    
    # ============================================
    # کلیدهای سفارشات
    # ============================================
    ORDERS_ALL = "orders:all"
    ORDERS_BY_STATUS = "orders:status:{status}"
    ORDERS_BY_USER = "orders:user:{user_id}"
    ORDER = "order:{order_id}"
    ORDER_STATS = "orders:stats"
    ORDERS_SEARCH = "orders:search:{keyword}"
    ORDERS_BY_DATE = "orders:date:{date}"
    ORDERS_USER_STATS = "orders:user:stats:{user_id}"
    ORDERS_FILTERED = "orders:filtered:{filter_hash}"
    
    # ============================================
    # کلیدهای تنظیمات
    # ============================================
    SETTING = "setting:{key}"
    SETTINGS_ALL = "settings:all"
    DEFAULT_COLUMNS = "settings:default_menu_columns"
    DEFAULT_PRICE = "settings:default_price"
    
    # ============================================
    # کلیدهای برندینگ
    # ============================================
    BRANDING = "branding:{key}"
    BRANDING_ALL = "branding:all"
    BRANDING_WELCOME = "branding:welcome"
    BRANDING_MAIN_MENU = "branding:main_menu"
    BRANDING_ADMIN = "branding:admin"
    
    # ============================================
    # کلیدهای آمار و تحلیل
    # ============================================
    STATS_DASHBOARD = "stats:dashboard"
    STATS_BUTTON = "stats:button:{button_id}"
    STATS_TOP_BUTTONS = "stats:top:{sort_by}:{limit}"
    STATS_REVENUE_PERIOD = "stats:revenue:{days}"
    STATS_BUTTON_DAILY = "stats:button:daily:{button_id}:{days}"
    STATS_TOP_USERS = "stats:top_users:{limit}"
    
    # ============================================
    # کلیدهای ادمین‌ها
    # ============================================
    ADMINS_ALL = "admins:all"
    ADMIN = "admin:{user_id}"
    ADMIN_STATS = "admins:stats"
    ADMIN_EXISTS = "admin:exists:{user_id}"
    ADMINS_SEARCH = "admins:search:{keyword}"
    ADMIN_ROLE = "admin:role:{user_id}"
    
    # ============================================
    # کلیدهای خطاها
    # ============================================
    ERRORS_ALL = "errors:all"
    ERRORS_BY_TYPE = "errors:type:{error_type}"
    ERROR = "error:{error_id}"
    ERRORS_STATS = "errors:stats"
    ERRORS_UNRESOLVED = "errors:unresolved"
    
    # ============================================
    # کلیدهای نسخه‌سازی (Versioning)
    # ============================================
    VERSIONS_BY_BUTTON = "versions:button:{button_id}"
    VERSION = "version:{button_id}:{version_number}"
    VERSIONS_LATEST = "versions:latest:{button_id}"
    VERSIONS_COUNT = "versions:count:{button_id}"
    
    # ============================================
    # کلیدهای ستون‌های منو
    # ============================================
    EFFECTIVE_COLUMNS = "columns:effective:{button_id}:{category_id}"
    BUTTON_COLUMNS = "columns:button:{button_id}"
    CATEGORY_COLUMNS = "columns:category:{category_id}"
    DEFAULT_MENU_COLUMNS = "columns:default"
    
    # ============================================
    # کلیدهای Rate Limiting
    # ============================================
    RATE_LIMIT = "rate_limit:{user_id}"
    RATE_LIMIT_RESET = "rate_limit:reset:{user_id}"
    
    # ============================================
    # کلیدهای موقت (Temp)
    # ============================================
    TEMP_ORDER = "temp:order:{user_id}"
    TEMP_STATE = "temp:state:{user_id}"
    TEMP_ANSWERS = "temp:answers:{user_id}:{button_id}"
    TEMP_FILES = "temp:files:{user_id}:{button_id}"
    
    # ============================================
    # کلیدهای پرداخت
    # ============================================
    PAYMENT_SESSION = "payment:session:{payload}"
    PAYMENT_PENDING = "payment:pending:{user_id}"
    PAYMENT_VERIFY = "payment:verify:{tracking_code}"
    
    # ============================================
    # کلیدهای تسک‌های زمان‌بندی‌شده
    # ============================================
    SCHEDULER_LAST_RUN = "scheduler:last_run:{task_name}"
    SCHEDULER_LOCK = "scheduler:lock:{task_name}"
    
    # ============================================
    # متدهای کمکی برای تولید کلید
    # ============================================
    
    @staticmethod
    def user(user_id: int) -> str:
        return f"user:{user_id}"
    
    @staticmethod
    def button(button_id: int) -> str:
        return f"button:{button_id}"
    
    @staticmethod
    def category(category_id: int) -> str:
        return f"category:{category_id}"
    
    @staticmethod
    def question(question_id: int) -> str:
        return f"question:{question_id}"
    
    @staticmethod
    def order(order_id: int) -> str:
        return f"order:{order_id}"
    
    @staticmethod
    def setting(key: str) -> str:
        return f"setting:{key}"
    
    @staticmethod
    def branding(key: str) -> str:
        return f"branding:{key}"
    
    @staticmethod
    def admin(user_id: int) -> str:
        return f"admin:{user_id}"
    
    @staticmethod
    def error(error_id: int) -> str:
        return f"error:{error_id}"
    
    @staticmethod
    def version(button_id: int, version_number: int) -> str:
        return f"version:{button_id}:{version_number}"
    
    @staticmethod
    def version_latest(button_id: int) -> str:
        return f"versions:latest:{button_id}"
    
    @staticmethod
    def rate_limit(user_id: int) -> str:
        return f"rate_limit:{user_id}"
    
    @staticmethod
    def temp_order(user_id: int) -> str:
        return f"temp:order:{user_id}"
    
    @staticmethod
    def payment_session(payload: str) -> str:
        return f"payment:session:{payload}"
    
    @staticmethod
    def orders_by_date(date: str) -> str:
        return f"orders:date:{date}"
    
    @staticmethod
    def stats_button(button_id: int) -> str:
        return f"stats:button:{button_id}"
    
    @staticmethod
    def effective_columns(button_id: int = None, category_id: int = None) -> str:
        if button_id and category_id:
            return f"columns:effective:{button_id}:{category_id}"
        elif button_id:
            return f"columns:effective:{button_id}:none"
        elif category_id:
            return f"columns:effective:none:{category_id}"
        return "columns:effective:default"
    
    @staticmethod
    def orders_filtered(filter_hash: str) -> str:
        return f"orders:filtered:{filter_hash}"


# ============================================
# کلاس کمکی برای تولید کلید با پارامتر
# ============================================

class CacheKeyBuilder:
    """ساخت کلیدهای کش با پارامترهای دلخواه"""
    
    @staticmethod
    def build(template: str, **kwargs) -> str:
        """
        ساخت کلید از روی قالب با جایگزینی پارامترها.
        
        مثال:
            CacheKeyBuilder.build(CacheKeys.USER, user_id=123)
            -> "user:123"
        """
        try:
            return template.format(**kwargs)
        except Exception as e:
            # ✅ ثبت خطا با traceback کامل
            log_general_error(
                f"Error building cache key from template '{template}': {str(e)}",
                traceback=traceback.format_exc()
            )
            # بازگشت یک کلید پیش‌فرض برای جلوگیری از شکست کامل
            return f"key_error_{hash(template)}"
    
    @staticmethod
    def user(user_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.USER, user_id=user_id)
    
    @staticmethod
    def button(button_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.BUTTON, button_id=button_id)
    
    @staticmethod
    def category(category_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.CATEGORY, category_id=category_id)
    
    @staticmethod
    def question(question_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.QUESTION, question_id=question_id)
    
    @staticmethod
    def order(order_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.ORDER, order_id=order_id)
    
    @staticmethod
    def setting(key: str) -> str:
        return CacheKeyBuilder.build(CacheKeys.SETTING, key=key)
    
    @staticmethod
    def branding(key: str) -> str:
        return CacheKeyBuilder.build(CacheKeys.BRANDING, key=key)
    
    @staticmethod
    def admin(user_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.ADMIN, user_id=user_id)
    
    @staticmethod
    def error(error_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.ERROR, error_id=error_id)
    
    @staticmethod
    def version(button_id: int, version_number: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.VERSION, button_id=button_id, version_number=version_number)
    
    @staticmethod
    def rate_limit(user_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.RATE_LIMIT, user_id=user_id)
    
    @staticmethod
    def temp_order(user_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.TEMP_ORDER, user_id=user_id)
    
    @staticmethod
    def payment_session(payload: str) -> str:
        return CacheKeyBuilder.build(CacheKeys.PAYMENT_SESSION, payload=payload)
    
    @staticmethod
    def stats_button(button_id: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.STATS_BUTTON, button_id=button_id)
    
    @staticmethod
    def orders_by_date(date: str) -> str:
        return CacheKeyBuilder.build(CacheKeys.ORDERS_BY_DATE, date=date)
    
    @staticmethod
    def orders_filtered(filter_hash: str) -> str:
        return CacheKeyBuilder.build(CacheKeys.ORDERS_FILTERED, filter_hash=filter_hash)
    
    @staticmethod
    def users_list(page: int, limit: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.USERS_LIST, page=page, limit=limit)
    
    @staticmethod
    def users_search(keyword: str) -> str:
        return CacheKeyBuilder.build(CacheKeys.USERS_SEARCH, keyword=keyword)
    
    @staticmethod
    def top_buttons(sort_by: str, limit: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.STATS_TOP_BUTTONS, sort_by=sort_by, limit=limit)
    
    @staticmethod
    def revenue_period(days: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.STATS_REVENUE_PERIOD, days=days)
    
    @staticmethod
    def button_daily(button_id: int, days: int) -> str:
        return CacheKeyBuilder.build(CacheKeys.STATS_BUTTON_DAILY, button_id=button_id, days=days)


__all__ = [
    'CacheKeys',
    'CacheKeyBuilder',
]