# utils/text_helpers.py
# توابع کمکی برای پردازش متن
# شامل: کوتاه‌سازی، اعتبارسنجی، تولید کد، پاک‌سازی و ...

import re
import json
import random
import string
import hashlib
from typing import Optional, List, Union, Any, Dict
from unicodedata import normalize


# ============================================================
# کوتاه‌سازی و فرمت‌بندی متن
# ============================================================

def truncate_text(text: Union[str, Any], max_length: int = 50, suffix: str = "...") -> str:
    """
    کوتاه‌سازی متن به طول مشخص

    پارامترها:
        text: متن ورودی
        max_length: حداکثر طول
        suffix: پسوند انتهایی

    بازگشت: متن کوتاه‌شده
    """
    if not text:
        return ""
    
    text = str(text)
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: Union[str, Any]) -> str:
    """
    پاک‌سازی متن (حذف فضاهای اضافی، خطوط خالی، ...)

    پارامترها:
        text: متن ورودی

    بازگشت: متن پاک‌شده
    """
    if not text:
        return ""
    
    text = str(text)
    # حذف فضاهای اضافی
    text = ' '.join(text.split())
    # حذف خطوط خالی
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    return text.strip()


def normalize_text(text: Union[str, Any]) -> str:
    """
    نرمال‌سازی متن (تبدیل به حروف کوچک، حذف علائم اضافی)

    پارامترها:
        text: متن ورودی

    بازگشت: متن نرمال‌شده
    """
    if not text:
        return ""
    
    text = str(text)
    # تبدیل به حروف کوچک
    text = text.lower()
    # حذف فضاهای اضافی
    text = ' '.join(text.split())
    return text.strip()


def remove_extra_spaces(text: Union[str, Any]) -> str:
    """
    حذف فضاهای اضافی از متن

    پارامترها:
        text: متن ورودی

    بازگشت: متن بدون فضاهای اضافی
    """
    if not text:
        return ""
    
    text = str(text)
    return ' '.join(text.split())


def escape_markdown(text: Union[str, Any]) -> str:
    """
    Escape کردن کاراکترهای ویژه Markdown

    پارامترها:
        text: متن ورودی

    بازگشت: متن escaped
    """
    if not text:
        return ""
    
    text = str(text)
    # کاراکترهای ویژه Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def unescape_markdown(text: Union[str, Any]) -> str:
    """
    برگرداندن متن escaped Markdown

    پارامترها:
        text: متن escaped

    بازگشت: متن اصلی
    """
    if not text:
        return ""
    
    text = str(text)
    # برگرداندن کاراکترهای escaped
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(f'\\{char}', char)
    
    return text


def split_text_by_length(text: str, max_length: int = 4000) -> List[str]:
    """
    تقسیم متن به بخش‌های با حداکثر طول مشخص (برای ارسال پیام‌های طولانی)

    پارامترها:
        text: متن ورودی
        max_length: حداکثر طول هر بخش

    بازگشت: لیست بخش‌ها
    """
    if not text:
        return []
    
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current = ""
    
    for line in text.split('\n'):
        if len(current) + len(line) + 1 <= max_length:
            if current:
                current += '\n' + line
            else:
                current = line
        else:
            if current:
                parts.append(current)
            current = line
    
    if current:
        parts.append(current)
    
    return parts


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    تقسیم متن به تکه‌های هم‌پوشان

    پارامترها:
        text: متن ورودی
        chunk_size: اندازه هر تکه
        overlap: میزان هم‌پوشانی

    بازگشت: لیست تکه‌ها
    """
    if not text:
        return []
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # سعی کنید در انتهای جمله تقسیم کنید
        if end < len(text):
            # پیدا کردن آخرین نقطه یا علامت سوال
            for sep in ['. ', '! ', '? ', '\n\n', '\n', ' ']:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start:
                    end = last_sep + len(sep)
                    break
        
        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else end
    
    return chunks


# ============================================================
# استخراج اطلاعات از متن
# ============================================================

def extract_hashtags(text: str) -> List[str]:
    """
    استخراج هشتگ‌ها از متن

    پارامترها:
        text: متن ورودی

    بازگشت: لیست هشتگ‌ها (بدون #)
    """
    if not text:
        return []
    
    pattern = r'#([\w\u0600-\u06FF]+)'
    return re.findall(pattern, text)


def extract_mentions(text: str) -> List[str]:
    """
    استخراج منشن‌ها از متن

    پارامترها:
        text: متن ورودی

    بازگشت: لیست منشن‌ها (بدون @)
    """
    if not text:
        return []
    
    pattern = r'@([\w\u0600-\u06FF]+)'
    return re.findall(pattern, text)


def extract_urls(text: str) -> List[str]:
    """
    استخراج URLها از متن

    پارامترها:
        text: متن ورودی

    بازگشت: لیست URLها
    """
    if not text:
        return []
    
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(pattern, text)


def extract_emails(text: str) -> List[str]:
    """
    استخراج ایمیل‌ها از متن

    پارامترها:
        text: متن ورودی

    بازگشت: لیست ایمیل‌ها
    """
    if not text:
        return []
    
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """
    استخراج شماره تلفن‌ها از متن

    پارامترها:
        text: متن ورودی

    بازگشت: لیست شماره تلفن‌ها
    """
    if not text:
        return []
    
    # پشتیبانی از فرمت‌های مختلف
    patterns = [
        r'09\d{9}',  # 09123456789
        r'0\d{2,3}-\d{6,8}',  # 021-12345678
        r'\+98\d{10}',  # +989123456789
        r'\d{4}-\d{3}-\d{4}',  # 1234-567-8901
    ]
    
    phones = []
    for pattern in patterns:
        phones.extend(re.findall(pattern, text))
    
    return phones


# ============================================================
# اعتبارسنجی
# ============================================================

def is_valid_email(email: str) -> bool:
    """
    اعتبارسنجی ایمیل

    پارامترها:
        email: آدرس ایمیل

    بازگشت: True اگر معتبر باشد
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def is_valid_phone(phone: str) -> bool:
    """
    اعتبارسنجی شماره تلفن همراه ایران

    پارامترها:
        phone: شماره تلفن

    بازگشت: True اگر معتبر باشد
    """
    if not phone:
        return False
    
    cleaned = re.sub(r'[^\d]', '', phone)
    pattern = r'^09\d{9}$'
    return bool(re.match(pattern, cleaned))


def is_valid_national_code(code: str) -> bool:
    """
    اعتبارسنجی کد ملی ایران

    پارامترها:
        code: کد ملی

    بازگشت: True اگر معتبر باشد
    """
    if not code:
        return False
    
    cleaned = re.sub(r'[^\d]', '', code)
    
    if len(cleaned) != 10:
        return False
    
    # کدهای ملی نامعتبر
    invalid_codes = [
        '0000000000', '1111111111', '2222222222', '3333333333',
        '4444444444', '5555555555', '6666666666', '7777777777',
        '8888888888', '9999999999'
    ]
    if cleaned in invalid_codes:
        return False
    
    # الگوریتم اعتبارسنجی کد ملی
    check = int(cleaned[9])
    sum_val = sum(int(cleaned[i]) * (10 - i) for i in range(9))
    remainder = sum_val % 11
    
    if remainder < 2:
        return check == remainder
    else:
        return check == 11 - remainder


def is_valid_url(url: str) -> bool:
    """
    اعتبارسنجی URL

    پارامترها:
        url: آدرس وب

    بازگشت: True اگر معتبر باشد
    """
    if not url:
        return False
    
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return bool(re.match(pattern, url.strip()))


def is_valid_uuid(uuid_str: str) -> bool:
    """
    اعتبارسنجی UUID

    پارامترها:
        uuid_str: رشته UUID

    بازگشت: True اگر معتبر باشد
    """
    if not uuid_str:
        return False
    
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_str.lower()))


def is_valid_iban(iban: str) -> bool:
    """
    اعتبارسنجی شماره شبا (ایران)

    پارامترها:
        iban: شماره شبا

    بازگشت: True اگر معتبر باشد
    """
    if not iban:
        return False
    
    iban = iban.upper().strip()
    if not iban.startswith('IR') or len(iban) < 24 or len(iban) > 26:
        return False
    
    # اعتبارسنجی ساده با regex
    pattern = r'^IR[0-9]{2}[0-9]{22}$'
    return bool(re.match(pattern, iban))


def is_valid_postal_code(code: str) -> bool:
    """
    اعتبارسنجی کدپستی ایران

    پارامترها:
        code: کدپستی

    بازگشت: True اگر معتبر باشد
    """
    if not code:
        return False
    
    cleaned = re.sub(r'[^\d]', '', code)
    pattern = r'^\d{10}$'
    return bool(re.match(pattern, cleaned))


def is_valid_plate(plate: str) -> bool:
    """
    اعتبارسنجی پلاک خودرو (ساده)

    پارامترها:
        plate: شماره پلاک

    بازگشت: True اگر معتبر باشد
    """
    if not plate:
        return False
    
    # فرمت‌های مختلف پلاک
    patterns = [
        r'^\d{2,3}-\d{2,3}-\d{2}$',
        r'^\d{2,3}\s\d{2,3}\s\d{2}$',
        r'^\d{5,6}$',
    ]
    
    for pattern in patterns:
        if re.match(pattern, plate.strip()):
            return True
    
    return False


def is_valid_card_number(card: str) -> bool:
    """
    اعتبارسنجی شماره کارت بانکی (با الگوریتم Luhn)

    پارامترها:
        card: شماره کارت

    بازگشت: True اگر معتبر باشد
    """
    if not card:
        return False
    
    cleaned = re.sub(r'[^\d]', '', card)
    
    if len(cleaned) != 16:
        return False
    
    # الگوریتم Luhn
    total = 0
    for i, digit in enumerate(reversed(cleaned)):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    
    return total % 10 == 0


# ============================================================
# تولید کد و شناسه
# ============================================================

def generate_random_code(length: int = 8, chars: str = None) -> str:
    """
    تولید کد تصادفی

    پارامترها:
        length: طول کد
        chars: کاراکترهای مجاز (پیش‌فرض: حروف بزرگ و اعداد)

    بازگشت: کد تصادفی
    """
    if chars is None:
        chars = string.ascii_uppercase + string.digits
    
    return ''.join(random.choice(chars) for _ in range(length))


def generate_tracking_code(prefix: str = "TRK", length: int = 8) -> str:
    """
    تولید کد رهگیری

    پارامترها:
        prefix: پیشوند
        length: طول بخش عددی

    بازگشت: کد رهگیری
    """
    code = generate_random_code(length, string.ascii_uppercase + string.digits)
    if prefix:
        return f"{prefix}-{code}"
    return code


def generate_otp(length: int = 6) -> str:
    """
    تولید کد یکبارمصرف (OTP)

    پارامترها:
        length: طول کد

    بازگشت: کد عددی
    """
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def generate_order_id() -> str:
    """
    تولید شناسه سفارش

    بازگشت: شناسه سفارش
    """
    import time
    timestamp = int(time.time() * 1000) % 1000000000000
    random_part = random.randint(1000, 9999)
    return f"ORD-{timestamp}-{random_part}"


def generate_username(base: str = "user") -> str:
    """
    تولید نام کاربری

    پارامترها:
        base: پایه نام کاربری

    بازگشت: نام کاربری
    """
    random_part = random.randint(1000, 9999)
    return f"{base}{random_part}"


def make_slug(text: str, max_length: int = 50) -> str:
    """
    تبدیل متن به slug (برای URL)

    پارامترها:
        text: متن ورودی
        max_length: حداکثر طول

    بازگشت: slug
    """
    if not text:
        return ""
    
    text = text.lower()
    # حذف کاراکترهای غیرمجاز
    text = re.sub(r'[^\w\s-]', '', text)
    # تبدیل فضاها به خط تیره
    text = re.sub(r'[-\s]+', '-', text)
    # حذف خط تیره‌های ابتدا و انتها
    text = text.strip('-')
    
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text


def sanitize_filename(filename: str) -> str:
    """
    پاک‌سازی نام فایل

    پارامترها:
        filename: نام فایل

    بازگشت: نام فایل پاک‌شده
    """
    if not filename:
        return "file"
    
    # حذف کاراکترهای غیرمجاز
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # حذف فضاهای اضافی
    filename = ' '.join(filename.split())
    # محدود کردن طول
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:190] + ('.' + ext if ext else '')
    
    return filename or "file"


# ============================================================
# JSON و سریالایزیشن
# ============================================================

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    تبدیل ایمن JSON به دیکشنری

    پارامترها:
        json_str: رشته JSON
        default: مقدار پیش‌فرض در صورت خطا

    بازگشت: دیکشنری یا مقدار پیش‌فرض
    """
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """
    تبدیل ایمن دیکشنری به JSON

    پارامترها:
        data: داده
        default: مقدار پیش‌فرض در صورت خطا

    بازگشت: رشته JSON
    """
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return default


# ============================================================
# هش و رمزنگاری ساده
# ============================================================

def hash_text(text: str, algorithm: str = 'sha256') -> str:
    """
    هش کردن متن

    پارامترها:
        text: متن ورودی
        algorithm: الگوریتم هش (sha256, md5, sha1)

    بازگشت: هش
    """
    if not text:
        return ""
    
    text = str(text)
    if algorithm == 'md5':
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(text.encode()).hexdigest()
    else:
        return hashlib.sha256(text.encode()).hexdigest()


def mask_text(text: str, visible_start: int = 2, visible_end: int = 2, mask_char: str = '*') -> str:
    """
    ماسک کردن بخشی از متن

    پارامترها:
        text: متن ورودی
        visible_start: تعداد کاراکترهای قابل مشاهده در ابتدا
        visible_end: تعداد کاراکترهای قابل مشاهده در انتها
        mask_char: کاراکتر ماسک

    بازگشت: متن ماسک‌شده
    """
    if not text:
        return ""
    
    text = str(text)
    if len(text) <= visible_start + visible_end:
        return text
    
    start_part = text[:visible_start]
    end_part = text[-visible_end:] if visible_end > 0 else ""
    mask_length = len(text) - visible_start - visible_end
    
    return start_part + (mask_char * mask_length) + end_part


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    # کوتاه‌سازی و پاک‌سازی
    'truncate_text',
    'clean_text',
    'normalize_text',
    'remove_extra_spaces',
    'escape_markdown',
    'unescape_markdown',
    'split_text_by_length',
    'chunk_text',
    
    # استخراج
    'extract_hashtags',
    'extract_mentions',
    'extract_urls',
    'extract_emails',
    'extract_phone_numbers',
    
    # اعتبارسنجی
    'is_valid_email',
    'is_valid_phone',
    'is_valid_national_code',
    'is_valid_url',
    'is_valid_uuid',
    'is_valid_iban',
    'is_valid_postal_code',
    'is_valid_plate',
    'is_valid_card_number',
    
    # تولید
    'generate_random_code',
    'generate_tracking_code',
    'generate_otp',
    'generate_order_id',
    'generate_username',
    'make_slug',
    'sanitize_filename',
    
    # JSON
    'safe_json_loads',
    'safe_json_dumps',
    
    # هش و ماسک
    'hash_text',
    'mask_text',
]