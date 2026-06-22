# models/enums.py
# تعریف Enumهای مشترک برای کل پروژه

from enum import Enum, IntEnum


# ============================================================
# وضعیت‌های سفارش
# ============================================================

class OrderStatus(IntEnum):
    """وضعیت‌های سفارش"""
    PENDING = 0       # در انتظار پرداخت
    PAID = 1          # پرداخت شده
    COMPLETED = 2     # تکمیل شده
    CANCELLED = 3     # لغو شده
    FAILED = 4        # ناموفق
    REFUNDED = 5      # بازگشت وجه

    @classmethod
    def from_string(cls, value: str):
        """تبدیل از رشته به Enum"""
        mapping = {
            'pending': cls.PENDING,
            'paid': cls.PAID,
            'completed': cls.COMPLETED,
            'cancelled': cls.CANCELLED,
            'failed': cls.FAILED,
            'refunded': cls.REFUNDED,
        }
        return mapping.get(value.lower(), cls.PENDING)

    @property
    def label(self) -> str:
        """برچسب فارسی"""
        labels = {
            self.PENDING: '⏳ در انتظار پرداخت',
            self.PAID: '✅ پرداخت شده',
            self.COMPLETED: '✅ تکمیل شده',
            self.CANCELLED: '❌ لغو شده',
            self.FAILED: '❌ ناموفق',
            self.REFUNDED: '🔄 بازگشت وجه',
        }
        return labels.get(self, 'نامشخص')

    @property
    def icon(self) -> str:
        """آیکون وضعیت"""
        icons = {
            self.PENDING: '⏳',
            self.PAID: '✅',
            self.COMPLETED: '🎉',
            self.CANCELLED: '❌',
            self.FAILED: '❌',
            self.REFUNDED: '🔄',
        }
        return icons.get(self, '❓')


# ============================================================
# نقش‌های کاربری
# ============================================================

class UserRole(IntEnum):
    """نقش‌های کاربری"""
    USER = 0          # کاربر عادی
    ADMIN = 1         # ادمین
    MANAGER = 2       # مدیر
    OBSERVER = 3      # ناظر
    OWNER = 10        # مالک

    @classmethod
    def from_string(cls, value: str):
        """تبدیل از رشته به Enum"""
        mapping = {
            'user': cls.USER,
            'admin': cls.ADMIN,
            'manager': cls.MANAGER,
            'observer': cls.OBSERVER,
            'owner': cls.OWNER,
        }
        return mapping.get(value.lower(), cls.USER)

    @property
    def label(self) -> str:
        """برچسب فارسی با آیکون"""
        labels = {
            self.USER: '👤 کاربر',
            self.ADMIN: '🛡️ ادمین',
            self.MANAGER: '📋 مدیر',
            self.OBSERVER: '👁️ ناظر',
            self.OWNER: '👑 مالک',
        }
        return labels.get(self, 'نامشخص')

    @property
    def permissions(self) -> list:
        """مجوزهای نقش"""
        permissions_map = {
            self.USER: [],
            self.ADMIN: [
                'manage_orders', 'manage_buttons', 'manage_categories',
                'manage_questions', 'view_analytics', 'manage_users',
                'manage_admins', 'view_reports', 'export_data'
            ],
            self.MANAGER: [
                'manage_orders', 'view_analytics', 'view_reports',
                'export_data'
            ],
            self.OBSERVER: [
                'view_analytics', 'view_reports'
            ],
            self.OWNER: ['*'],  # همه مجوزها
        }
        return permissions_map.get(self, [])

    def has_permission(self, permission: str) -> bool:
        """بررسی وجود مجوز"""
        if self == self.OWNER:
            return True
        return permission in self.permissions


# ============================================================
# وضعیت کاربر
# ============================================================

class UserStatus(IntEnum):
    """وضعیت کاربر"""
    ACTIVE = 0        # فعال
    BLOCKED = 1       # مسدود شده
    DELETED = 2       # حذف شده

    @classmethod
    def from_string(cls, value: str):
        """تبدیل از رشته به Enum"""
        mapping = {
            'active': cls.ACTIVE,
            'blocked': cls.BLOCKED,
            'deleted': cls.DELETED,
        }
        return mapping.get(value.lower(), cls.ACTIVE)

    @property
    def label(self) -> str:
        """برچسب فارسی با آیکون"""
        labels = {
            self.ACTIVE: '🟢 فعال',
            self.BLOCKED: '🔴 مسدود شده',
            self.DELETED: '🗑️ حذف شده',
        }
        return labels.get(self, 'نامشخص')


# ============================================================
# نوع دکمه
# ============================================================

class ButtonType(IntEnum):
    """نوع دکمه"""
    NORMAL = 0        # دکمه عادی
    SUBMENU = 1       # دکمه دارای زیرمنو
    SERVICE = 2       # دکمه سرویس (با پرداخت)

    @classmethod
    def from_db(cls, has_submenu: bool, has_payment: bool) -> 'ButtonType':
        """تبدیل از فیلدهای دیتابیس"""
        if has_submenu:
            return cls.SUBMENU
        elif has_payment:
            return cls.SERVICE
        return cls.NORMAL

    @property
    def label(self) -> str:
        """برچسب فارسی با آیکون"""
        labels = {
            self.NORMAL: '🔘 عادی',
            self.SUBMENU: '📂 زیرمنو',
            self.SERVICE: '💰 سرویس',
        }
        return labels.get(self, 'نامشخص')


# ============================================================
# نوع سوال
# ============================================================

class QuestionType(IntEnum):
    """نوع سوال"""
    TEXT = 0          # متن آزاد
    NUMBER = 1        # عدد
    FILE = 2          # فایل
    BUTTON = 3        # دکمه‌ای (گزینه‌ای)
    DATE = 4          # تاریخ
    YESNO = 5         # بله/خیر
    EMAIL = 6         # ایمیل
    PHONE = 7         # تلفن
    NATIONAL_CODE = 8 # کد ملی
    POSTAL_CODE = 9   # کدپستی
    PLATE = 10        # پلاک خودرو
    IBAN = 11         # شماره شبا
    CARD_NUMBER = 12  # شماره کارت

    @classmethod
    def from_string(cls, value: str):
        """تبدیل از رشته به Enum"""
        mapping = {
            'text': cls.TEXT,
            'number': cls.NUMBER,
            'file': cls.FILE,
            'button': cls.BUTTON,
            'date': cls.DATE,
            'yesno': cls.YESNO,
            'email': cls.EMAIL,
            'phone': cls.PHONE,
            'national_code': cls.NATIONAL_CODE,
            'postal_code': cls.POSTAL_CODE,
            'plate': cls.PLATE,
            'iban': cls.IBAN,
            'card_number': cls.CARD_NUMBER,
        }
        return mapping.get(value.lower(), cls.TEXT)

    @property
    def label(self) -> str:
        """برچسب فارسی با آیکون"""
        labels = {
            self.TEXT: '📝 متن آزاد',
            self.NUMBER: '🔢 عدد',
            self.FILE: '📎 فایل',
            self.BUTTON: '🔘 گزینه‌ای',
            self.DATE: '📅 تاریخ',
            self.YESNO: '✅ بله/خیر',
            self.EMAIL: '📧 ایمیل',
            self.PHONE: '📞 تلفن',
            self.NATIONAL_CODE: '🆔 کد ملی',
            self.POSTAL_CODE: '📮 کدپستی',
            self.PLATE: '🚗 پلاک',
            self.IBAN: '🏦 شبا',
            self.CARD_NUMBER: '💳 شماره کارت',
        }
        return labels.get(self, 'نامشخص')


# ============================================================
# نوع اعتبارسنجی
# ============================================================

class ValidationType(Enum):
    """نوع اعتبارسنجی"""
    NONE = "none"
    TEXT = "text"
    NUMBER = "number"
    DECIMAL = "decimal"
    NATIONAL_CODE = "national_code"
    PHONE = "phone"
    PHONE_LANDLINE = "phone_landline"
    POSTAL_CODE = "postal_code"
    PLATE = "plate"
    IBAN = "iban"
    CARD_NUMBER = "card_number"
    EMAIL = "email"
    URL = "url"
    DATE = "date"
    DATE_GREGORIAN = "date_gregorian"
    TIME = "time"
    DATETIME = "datetime"
    PERSIAN_TEXT = "persian_text"
    ENGLISH_TEXT = "english_text"
    ALPHANUMERIC = "alphanumeric"
    JSON = "json"
    FILE = "file"
    IMAGE = "image"
    DOCUMENT = "document"

    @classmethod
    def from_string(cls, value: str):
        """تبدیل از رشته به Enum"""
        mapping = {
            'none': cls.NONE,
            'text': cls.TEXT,
            'number': cls.NUMBER,
            'decimal': cls.DECIMAL,
            'national_code': cls.NATIONAL_CODE,
            'phone': cls.PHONE,
            'phone_landline': cls.PHONE_LANDLINE,
            'postal_code': cls.POSTAL_CODE,
            'plate': cls.PLATE,
            'iban': cls.IBAN,
            'card_number': cls.CARD_NUMBER,
            'email': cls.EMAIL,
            'url': cls.URL,
            'date': cls.DATE,
            'date_gregorian': cls.DATE_GREGORIAN,
            'time': cls.TIME,
            'datetime': cls.DATETIME,
            'persian_text': cls.PERSIAN_TEXT,
            'english_text': cls.ENGLISH_TEXT,
            'alphanumeric': cls.ALPHANUMERIC,
            'json': cls.JSON,
            'file': cls.FILE,
            'image': cls.IMAGE,
            'document': cls.DOCUMENT,
        }
        return mapping.get(value.lower(), cls.NONE)

    @property
    def label(self) -> str:
        """برچسب فارسی"""
        labels = {
            self.NONE: 'بدون اعتبارسنجی',
            self.TEXT: 'متن آزاد',
            self.NUMBER: 'عدد',
            self.DECIMAL: 'عدد اعشاری',
            self.NATIONAL_CODE: 'کد ملی',
            self.PHONE: 'تلفن همراه',
            self.PHONE_LANDLINE: 'تلفن ثابت',
            self.POSTAL_CODE: 'کدپستی',
            self.PLATE: 'پلاک خودرو',
            self.IBAN: 'شماره شبا',
            self.CARD_NUMBER: 'شماره کارت',
            self.EMAIL: 'ایمیل',
            self.URL: 'آدرس وب',
            self.DATE: 'تاریخ شمسی',
            self.DATE_GREGORIAN: 'تاریخ میلادی',
            self.TIME: 'زمان',
            self.DATETIME: 'تاریخ و زمان',
            self.PERSIAN_TEXT: 'متن فارسی',
            self.ENGLISH_TEXT: 'متن انگلیسی',
            self.ALPHANUMERIC: 'حروف و اعداد',
            self.JSON: 'داده JSON',
            self.FILE: 'فایل',
            self.IMAGE: 'تصویر',
            self.DOCUMENT: 'سند',
        }
        return labels.get(self, self.value)


# ============================================================
# نوع خطا
# ============================================================

class ErrorType(Enum):
    """نوع خطا"""
    DATABASE = "database"
    API = "api"
    CALLBACK = "callback"
    GENERAL = "general"
    PAYMENT = "payment"
    SECURITY = "security"
    CRITICAL = "critical"

    @property
    def icon(self) -> str:
        """آیکون نوع خطا"""
        icons = {
            self.DATABASE: '🗄️',
            self.API: '🌐',
            self.CALLBACK: '🔄',
            self.GENERAL: '📌',
            self.PAYMENT: '💰',
            self.SECURITY: '🔒',
            self.CRITICAL: '🚨',
        }
        return icons.get(self, '⚠️')


# ============================================================
# نوع اقدام (برای آمار)
# ============================================================

class ActionType(Enum):
    """نوع اقدام کاربر"""
    CLICK = "click"              # کلیک روی دکمه
    FORM_START = "form_start"    # شروع فرم
    ORDER_PAID = "order_paid"    # سفارش پرداخت شده
    ORDER_CANCELLED = "order_cancelled"  # سفارش لغو شده

    @property
    def label(self) -> str:
        """برچسب فارسی"""
        labels = {
            self.CLICK: 'کلیک روی دکمه',
            self.FORM_START: 'شروع فرم',
            self.ORDER_PAID: 'سفارش پرداخت شده',
            self.ORDER_CANCELLED: 'سفارش لغو شده',
        }
        return labels.get(self, self.value)


# ============================================================
# وضعیت پرداخت
# ============================================================

class PaymentStatus(Enum):
    """وضعیت پرداخت"""
    PENDING = "pending"      # در انتظار پرداخت
    PAID = "paid"            # پرداخت شده
    FAILED = "failed"        # ناموفق
    REFUNDED = "refunded"    # بازگشت وجه

    @property
    def label(self) -> str:
        """برچسب فارسی"""
        labels = {
            self.PENDING: '⏳ در انتظار پرداخت',
            self.PAID: '✅ پرداخت شده',
            self.FAILED: '❌ ناموفق',
            self.REFUNDED: '🔄 بازگشت وجه',
        }
        return labels.get(self, self.value)


# ============================================================
# نقش ادمین (برای پنل مدیریت)
# ============================================================

class AdminRole(Enum):
    """نقش‌های ادمین"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    OBSERVER = "observer"

    @classmethod
    def from_string(cls, value: str):
        """تبدیل از رشته به Enum"""
        mapping = {
            'owner': cls.OWNER,
            'admin': cls.ADMIN,
            'manager': cls.MANAGER,
            'observer': cls.OBSERVER,
        }
        return mapping.get(value.lower(), cls.ADMIN)

    @property
    def label(self) -> str:
        """برچسب فارسی با آیکون"""
        labels = {
            self.OWNER: '👑 مالک',
            self.ADMIN: '🛡️ ادمین',
            self.MANAGER: '📋 مدیر',
            self.OBSERVER: '👁️ ناظر',
        }
        return labels.get(self, self.value)

    @property
    def permissions(self) -> list:
        """مجوزهای نقش"""
        permissions_map = {
            self.OBSERVER: ['view_analytics'],
            self.MANAGER: ['manage_orders', 'view_analytics'],
            self.ADMIN: ['*'],  # همه مجوزها به جز مدیریت ادمین‌ها
            self.OWNER: ['*'],  # همه مجوزها
        }
        return permissions_map.get(self, [])


# ============================================================
# مکان دسته‌بندی
# ============================================================

class CategoryLocation(Enum):
    """مکان دسته‌بندی در منو"""
    MAIN = "main"
    MORE = "more"
    OTHER = "other"

    @classmethod
    def from_string(cls, value: str):
        """تبدیل از رشته به Enum"""
        mapping = {
            'main': cls.MAIN,
            'more': cls.MORE,
            'other': cls.OTHER,
        }
        return mapping.get(value.lower(), cls.MAIN)

    @property
    def label(self) -> str:
        """برچسب فارسی با آیکون"""
        labels = {
            self.MAIN: '🏠 منوی اصلی',
            self.MORE: '➕ منوی بیشتر',
            self.OTHER: '🔧 دیگر خدمات',
        }
        return labels.get(self, self.value)


# ============================================================
# نوع عملیات لاگ
# ============================================================

class LogAction(Enum):
    """نوع عملیات در لاگ"""
    # سفارشات
    ORDER_CREATED = "order_created"
    ORDER_STATUS_CHANGED = "order_status_changed"
    ORDER_DELETED = "order_deleted"
    ORDER_NOTE_ADDED = "order_note_added"
    
    # کاربران
    USER_REGISTERED = "user_registered"
    USER_BLOCKED = "user_blocked"
    USER_UNBLOCKED = "user_unblocked"
    USER_ROLE_CHANGED = "user_role_changed"
    
    # دکمه‌ها
    BUTTON_CREATED = "button_created"
    BUTTON_UPDATED = "button_updated"
    BUTTON_DELETED = "button_deleted"
    
    # ادمین‌ها
    ADMIN_ADDED = "admin_added"
    ADMIN_REMOVED = "admin_removed"
    ADMIN_ROLE_CHANGED = "admin_role_changed"
    
    # تنظیمات
    SETTINGS_UPDATED = "settings_updated"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"

    @property
    def label(self) -> str:
        """برچسب فارسی"""
        labels = {
            self.ORDER_CREATED: 'ایجاد سفارش',
            self.ORDER_STATUS_CHANGED: 'تغییر وضعیت سفارش',
            self.ORDER_DELETED: 'حذف سفارش',
            self.ORDER_NOTE_ADDED: 'افزودن یادداشت سفارش',
            self.USER_REGISTERED: 'ثبت نام کاربر',
            self.USER_BLOCKED: 'مسدود کردن کاربر',
            self.USER_UNBLOCKED: 'رفع مسدودیت کاربر',
            self.USER_ROLE_CHANGED: 'تغییر نقش کاربر',
            self.BUTTON_CREATED: 'ایجاد دکمه',
            self.BUTTON_UPDATED: 'به‌روزرسانی دکمه',
            self.BUTTON_DELETED: 'حذف دکمه',
            self.ADMIN_ADDED: 'افزودن ادمین',
            self.ADMIN_REMOVED: 'حذف ادمین',
            self.ADMIN_ROLE_CHANGED: 'تغییر نقش ادمین',
            self.SETTINGS_UPDATED: 'به‌روزرسانی تنظیمات',
            self.BACKUP_CREATED: 'ایجاد پشتیبان',
            self.BACKUP_RESTORED: 'بازیابی پشتیبان',
        }
        return labels.get(self, self.value)


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'OrderStatus',
    'UserRole',
    'UserStatus',
    'ButtonType',
    'QuestionType',
    'ValidationType',
    'ErrorType',
    'ActionType',
    'PaymentStatus',
    'AdminRole',
    'CategoryLocation',
    'LogAction',
]