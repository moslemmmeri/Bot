# models/question.py
# مدل سوال

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import IntEnum, Enum


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


@dataclass
class Question:
    """مدل سوال"""
    id: Optional[int] = None
    button_id: int = 0
    question_text: str = ""
    question_type: str = "text"
    validation_rule: Optional[str] = None
    error_message: Optional[str] = None
    needs_button: bool = False
    array_name: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    # ========== فیلدهای اعتبارسنجی ==========
    # اجباری
    is_required: bool = False
    
    # اعتبارسنجی کلی
    validation_enabled: bool = False
    validation_type: str = "none"
    
    # محدودیت‌های متن
    length_validation_enabled: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    word_validation_enabled: bool = False
    min_words: Optional[int] = None
    max_words: Optional[int] = None
    
    # اعتبارسنجی عددی
    numeric_validation_enabled: bool = False
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    step: Optional[int] = None
    
    # اعتبارسنجی تاریخ
    date_validation_enabled: bool = False
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    future_only: bool = False
    past_only: bool = False
    weekdays_only: bool = False
    
    # اعتبارسنجی فایل
    file_validation_enabled: bool = False
    allowed_formats: Optional[str] = None
    max_file_size: Optional[int] = None
    min_file_size: Optional[int] = None
    max_files: Optional[int] = None
    
    # اعتبارسنجی ابعاد
    dimensions_enabled: bool = False
    required_width: Optional[int] = None
    required_height: Optional[int] = None
    aspect_ratio: Optional[str] = None
    
    # اعتبارسنجی الگو
    pattern_validation_enabled: bool = False
    regex_pattern: Optional[str] = None
    starts_with: Optional[str] = None
    ends_with: Optional[str] = None
    
    # اعتبارسنجی محتوا
    contains_validation_enabled: bool = False
    contains: Optional[str] = None
    not_contains: Optional[str] = None
    forbidden_words: Optional[str] = None
    required_words: Optional[str] = None
    
    # شرط نمایش
    conditional_enabled: bool = False
    conditional_on: Optional[int] = None
    conditional_value: Optional[str] = None
    
    # اصلاح خودکار
    auto_fix_enabled: bool = False
    
    # پیام‌ها
    validation_error: Optional[str] = None
    validation_hint: Optional[str] = None
    
    # ========== فیلدهای وابسته (از دیتابیس خوانده نمی‌شوند) ==========
    options: List[Dict] = field(default_factory=list)
    conditions: List[Dict] = field(default_factory=list)
    
    @property
    def type_label(self) -> str:
        """برچسب نوع سوال به فارسی"""
        type_map = {
            'text': '📝 متن آزاد',
            'number': '🔢 عدد',
            'file': '📎 فایل',
            'button': '🔘 گزینه‌ای',
            'date': '📅 تاریخ',
            'yesno': '✅ بله/خیر',
            'email': '📧 ایمیل',
            'phone': '📞 تلفن',
            'national_code': '🆔 کد ملی',
            'postal_code': '📮 کدپستی',
        }
        return type_map.get(self.question_type, self.question_type)
    
    @property
    def is_button_question(self) -> bool:
        """آیا سوال دکمه‌ای است"""
        return self.needs_button
    
    @property
    def is_required_text(self) -> str:
        """متن اجباری بودن"""
        return "⭐ اجباری" if self.is_required else "اختیاری"
    
    @property
    def validation_summary(self) -> str:
        """خلاصه اعتبارسنجی"""
        if not self.validation_enabled:
            return "❌ غیرفعال"
        
        parts = []
        if self.validation_type != "none":
            parts.append(f"نوع: {self.validation_type}")
        if self.length_validation_enabled:
            parts.append(f"طول: {self.min_length or 'بدون حداقل'} تا {self.max_length or 'بدون حداکثر'}")
        if self.numeric_validation_enabled:
            parts.append(f"عدد: {self.min_value or 'بدون حداقل'} تا {self.max_value or 'بدون حداکثر'}")
        if self.file_validation_enabled:
            parts.append(f"فایل: {self.allowed_formats or 'همه فرمت‌ها'}")
        
        return " | ".join(parts) if parts else "فعال"
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'Question':
        """ایجاد از دیکشنری دیتابیس"""
        return cls(
            id=data.get('id'),
            button_id=data.get('button_id', 0),
            question_text=data.get('question_text', ''),
            question_type=data.get('question_type', 'text'),
            validation_rule=data.get('validation_rule'),
            error_message=data.get('error_message'),
            needs_button=bool(data.get('needs_button', 0)),
            array_name=data.get('array_name'),
            sort_order=data.get('sort_order', 0),
            is_active=bool(data.get('is_active', 1)),
            created_at=data.get('created_at'),
            # اعتبارسنجی
            is_required=bool(data.get('is_required', 0)),
            validation_enabled=bool(data.get('validation_enabled', 0)),
            validation_type=data.get('validation_type', 'none'),
            length_validation_enabled=bool(data.get('length_validation_enabled', 0)),
            min_length=data.get('min_length'),
            max_length=data.get('max_length'),
            word_validation_enabled=bool(data.get('word_validation_enabled', 0)),
            min_words=data.get('min_words'),
            max_words=data.get('max_words'),
            numeric_validation_enabled=bool(data.get('numeric_validation_enabled', 0)),
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            step=data.get('step'),
            date_validation_enabled=bool(data.get('date_validation_enabled', 0)),
            min_date=data.get('min_date'),
            max_date=data.get('max_date'),
            future_only=bool(data.get('future_only', 0)),
            past_only=bool(data.get('past_only', 0)),
            weekdays_only=bool(data.get('weekdays_only', 0)),
            file_validation_enabled=bool(data.get('file_validation_enabled', 0)),
            allowed_formats=data.get('allowed_formats'),
            max_file_size=data.get('max_file_size'),
            min_file_size=data.get('min_file_size'),
            max_files=data.get('max_files'),
            dimensions_enabled=bool(data.get('dimensions_enabled', 0)),
            required_width=data.get('required_width'),
            required_height=data.get('required_height'),
            aspect_ratio=data.get('aspect_ratio'),
            pattern_validation_enabled=bool(data.get('pattern_validation_enabled', 0)),
            regex_pattern=data.get('regex_pattern'),
            starts_with=data.get('starts_with'),
            ends_with=data.get('ends_with'),
            contains_validation_enabled=bool(data.get('contains_validation_enabled', 0)),
            contains=data.get('contains'),
            not_contains=data.get('not_contains'),
            forbidden_words=data.get('forbidden_words'),
            required_words=data.get('required_words'),
            conditional_enabled=bool(data.get('conditional_enabled', 0)),
            conditional_on=data.get('conditional_on'),
            conditional_value=data.get('conditional_value'),
            auto_fix_enabled=bool(data.get('auto_fix_enabled', 0)),
            validation_error=data.get('validation_error'),
            validation_hint=data.get('validation_hint'),
        )
    
    def to_db(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای ذخیره در دیتابیس"""
        return {
            'button_id': self.button_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'validation_rule': self.validation_rule,
            'error_message': self.error_message,
            'needs_button': 1 if self.needs_button else 0,
            'array_name': self.array_name,
            'sort_order': self.sort_order,
            'is_active': 1 if self.is_active else 0,
            # اعتبارسنجی
            'is_required': 1 if self.is_required else 0,
            'validation_enabled': 1 if self.validation_enabled else 0,
            'validation_type': self.validation_type,
            'length_validation_enabled': 1 if self.length_validation_enabled else 0,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'word_validation_enabled': 1 if self.word_validation_enabled else 0,
            'min_words': self.min_words,
            'max_words': self.max_words,
            'numeric_validation_enabled': 1 if self.numeric_validation_enabled else 0,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'step': self.step,
            'date_validation_enabled': 1 if self.date_validation_enabled else 0,
            'min_date': self.min_date,
            'max_date': self.max_date,
            'future_only': 1 if self.future_only else 0,
            'past_only': 1 if self.past_only else 0,
            'weekdays_only': 1 if self.weekdays_only else 0,
            'file_validation_enabled': 1 if self.file_validation_enabled else 0,
            'allowed_formats': self.allowed_formats,
            'max_file_size': self.max_file_size,
            'min_file_size': self.min_file_size,
            'max_files': self.max_files,
            'dimensions_enabled': 1 if self.dimensions_enabled else 0,
            'required_width': self.required_width,
            'required_height': self.required_height,
            'aspect_ratio': self.aspect_ratio,
            'pattern_validation_enabled': 1 if self.pattern_validation_enabled else 0,
            'regex_pattern': self.regex_pattern,
            'starts_with': self.starts_with,
            'ends_with': self.ends_with,
            'contains_validation_enabled': 1 if self.contains_validation_enabled else 0,
            'contains': self.contains,
            'not_contains': self.not_contains,
            'forbidden_words': self.forbidden_words,
            'required_words': self.required_words,
            'conditional_enabled': 1 if self.conditional_enabled else 0,
            'conditional_on': self.conditional_on,
            'conditional_value': self.conditional_value,
            'auto_fix_enabled': 1 if self.auto_fix_enabled else 0,
            'validation_error': self.validation_error,
            'validation_hint': self.validation_hint,
        }
    
    def set_required(self, required: bool) -> None:
        """تنظیم اجباری بودن"""
        self.is_required = required
    
    def toggle_required(self) -> None:
        """تغییر وضعیت اجباری"""
        self.is_required = not self.is_required
    
    def toggle_validation(self, feature: str) -> None:
        """تغییر وضعیت یک قابلیت اعتبارسنجی"""
        if hasattr(self, feature):
            current = getattr(self, feature)
            setattr(self, feature, not current)
    
    def is_valid_answer(self, answer: str) -> bool:
        """بررسی اعتبار پاسخ (ساده)"""
        if self.is_required and not answer:
            return False
        # اعتبارسنجی‌های بیشتر در dynamic_validation انجام می‌شود
        return True


# ============================================================
# توابع کمکی
# ============================================================

def create_question(button_id: int, question_text: str,
                    question_type: str = "text",
                    is_required: bool = False,
                    needs_button: bool = False,
                    sort_order: int = 0) -> Question:
    """ایجاد سوال جدید"""
    return Question(
        button_id=button_id,
        question_text=question_text,
        question_type=question_type,
        is_required=is_required,
        needs_button=needs_button,
        sort_order=sort_order,
        is_active=True,
        created_at=datetime.now()
    )


def create_text_question(button_id: int, question_text: str,
                         is_required: bool = True,
                         min_length: Optional[int] = None,
                         max_length: Optional[int] = None) -> Question:
    """ایجاد سوال متنی"""
    q = create_question(button_id, question_text, "text", is_required)
    q.validation_type = "text"
    q.validation_enabled = True
    q.length_validation_enabled = True
    q.min_length = min_length
    q.max_length = max_length
    return q


def create_number_question(button_id: int, question_text: str,
                           is_required: bool = True,
                           min_value: Optional[int] = None,
                           max_value: Optional[int] = None) -> Question:
    """ایجاد سوال عددی"""
    q = create_question(button_id, question_text, "number", is_required)
    q.validation_type = "number"
    q.validation_enabled = True
    q.numeric_validation_enabled = True
    q.min_value = min_value
    q.max_value = max_value
    return q


def create_file_question(button_id: int, question_text: str,
                         is_required: bool = True,
                         allowed_formats: Optional[str] = None,
                         max_file_size: Optional[int] = None) -> Question:
    """ایجاد سوال فایل"""
    q = create_question(button_id, question_text, "file", is_required)
    q.validation_type = "file"
    q.validation_enabled = True
    q.file_validation_enabled = True
    q.allowed_formats = allowed_formats or "jpg,png,pdf"
    q.max_file_size = max_file_size or 5120
    return q


def create_button_question(button_id: int, question_text: str,
                           options: List[Dict[str, str]],
                           is_required: bool = True) -> Question:
    """ایجاد سوال دکمه‌ای با گزینه‌ها"""
    q = create_question(button_id, question_text, "button", is_required)
    q.needs_button = True
    q.options = options
    return q


__all__ = [
    'Question',
    'QuestionType',
    'ValidationType',
    'create_question',
    'create_text_question',
    'create_number_question',
    'create_file_question',
    'create_button_question',
]