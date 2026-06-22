# tests/test_utils/test_formatters.py
# تست‌های واحد برای توابع فرمت‌بندی در utils/formatters.py

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from utils.formatters import (
    format_number,
    format_percent,
    format_price,
    format_currency,
    format_boolean,
    format_yes_no,
    truncate_number,
    human_readable_size,
    format_datetime,
    format_date,
    format_time,
    format_duration,
    human_readable_time,
    format_phone,
    format_national_code,
    format_tracking_code,
    format_order_status,
    format_ordered_list,
    format_bullet_list,
    format_key_value,
    format_key_value_list,
    safe_int,
    safe_float,
)


class TestFormatters:
    """تست‌های توابع فرمت‌بندی"""

    # ============================================================
    # تست‌های format_number
    # ============================================================

    def test_format_number_integer(self):
        """تست فرمت‌بندی عدد صحیح"""
        assert format_number(1234567) == "1,234,567"
        assert format_number(1000) == "1,000"
        assert format_number(0) == "0"
        assert format_number(-1234) == "-1,234"

    def test_format_number_float(self):
        """تست فرمت‌بندی عدد اعشاری"""
        assert format_number(1234.56) == "1,234.56"
        assert format_number(1000.0) == "1,000"
        assert format_number(0.5) == "0.50"

    def test_format_number_string(self):
        """تست فرمت‌بندی رشته عددی"""
        assert format_number("1234567") == "1,234,567"
        assert format_number("1,234,567") == "1,234,567"
        assert format_number("1234.56") == "1,234.56"

    def test_format_number_decimal(self):
        """تست فرمت‌بندی Decimal"""
        assert format_number(Decimal("1234567.89")) == "1,234,567.89"
        assert format_number(Decimal("1000")) == "1,000"

    def test_format_number_none(self):
        """تست فرمت‌بندی None"""
        assert format_number(None) == "۰"
        assert format_number(None, default="نامشخص") == "نامشخص"

    def test_format_number_invalid(self):
        """تست فرمت‌بندی مقدار نامعتبر"""
        assert format_number("abc") == "۰"
        assert format_number([]) == "۰"

    # ============================================================
    # تست‌های format_percent
    # ============================================================

    def test_format_percent_default(self):
        """تست فرمت‌بندی درصد با تنظیمات پیش‌فرض"""
        assert format_percent(50) == "50.00%"
        assert format_percent(33.333) == "33.33%"
        assert format_percent(0) == "0.00%"
        assert format_percent(-10) == "-10.00%"

    def test_format_percent_with_decimals(self):
        """تست فرمت‌بندی درصد با تعداد رقم اعشار متفاوت"""
        assert format_percent(50, decimals=0) == "50%"
        assert format_percent(33.333, decimals=1) == "33.3%"
        assert format_percent(33.333, decimals=3) == "33.333%"

    def test_format_percent_none(self):
        """تست فرمت‌بندی درصد با None"""
        assert format_percent(None) == "۰%"
        assert format_percent(None, default="نامشخص") == "نامشخص"

    def test_format_percent_invalid(self):
        """تست فرمت‌بندی درصد با مقدار نامعتبر"""
        assert format_percent("abc") == "۰%"

    # ============================================================
    # تست‌های format_price
    # ============================================================

    def test_format_price_default(self):
        """تست فرمت‌بندی قیمت با تنظیمات پیش‌فرض"""
        assert format_price(1234567) == "1,234,567 ریال"
        assert format_price(1000) == "1,000 ریال"
        assert format_price(0) == "۰ ریال"

    def test_format_price_with_currency(self):
        """تست فرمت‌بندی قیمت با واحد پول سفارشی"""
        assert format_price(1234567, currency="تومان") == "1,234,567 تومان"
        assert format_price(1000, currency="$") == "1,000 $"

    def test_format_price_none(self):
        """تست فرمت‌بندی قیمت با None"""
        assert format_price(None) == "۰ ریال"
        assert format_price(None, default="نامشخص") == "نامشخص ریال"

    def test_format_price_invalid(self):
        """تست فرمت‌بندی قیمت با مقدار نامعتبر"""
        assert format_price("abc") == "۰ ریال"

    # ============================================================
    # تست‌های format_currency
    # ============================================================

    def test_format_currency_default(self):
        """تست فرمت‌بندی ارز با تنظیمات پیش‌فرض"""
        assert format_currency(1234567) == "1,234,567 IRT"
        assert format_currency(1000) == "1,000 IRT"

    def test_format_currency_with_code(self):
        """تست فرمت‌بندی ارز با کد سفارشی"""
        assert format_currency(1234567, currency="USD") == "1,234,567 USD"
        assert format_currency(1000, currency="EUR") == "1,000 EUR"

    def test_format_currency_none(self):
        """تست فرمت‌بندی ارز با None"""
        assert format_currency(None) == "۰ IRT"

    # ============================================================
    # تست‌های format_boolean
    # ============================================================

    def test_format_boolean_true(self):
        """تست فرمت‌بندی True"""
        assert format_boolean(True) == "بله"
        assert format_boolean(1) == "بله"
        assert format_boolean("1") == "بله"
        assert format_boolean("true") == "بله"
        assert format_boolean("بله") == "بله"

    def test_format_boolean_false(self):
        """تست فرمت‌بندی False"""
        assert format_boolean(False) == "خیر"
        assert format_boolean(0) == "خیر"
        assert format_boolean("0") == "خیر"
        assert format_boolean("false") == "خیر"
        assert format_boolean("") == "خیر"

    def test_format_boolean_custom_text(self):
        """تست فرمت‌بندی بولی با متن سفارشی"""
        assert format_boolean(True, true_text="✅ فعال", false_text="❌ غیرفعال") == "✅ فعال"
        assert format_boolean(False, true_text="✅ فعال", false_text="❌ غیرفعال") == "❌ غیرفعال"

    def test_format_boolean_none(self):
        """تست فرمت‌بندی بولی با None"""
        assert format_boolean(None) == "خیر"

    # ============================================================
    # تست‌های format_yes_no
    # ============================================================

    def test_format_yes_no(self):
        """تست فرمت‌بندی بله/خیر"""
        assert format_yes_no(True) == "✅ بله"
        assert format_yes_no(False) == "❌ خیر"
        assert format_yes_no(1) == "✅ بله"
        assert format_yes_no(0) == "❌ خیر"

    # ============================================================
    # تست‌های truncate_number
    # ============================================================

    def test_truncate_number_small(self):
        """تست کوتاه‌سازی اعداد کوچک"""
        assert truncate_number(500) == "500"
        assert truncate_number(999) == "999"

    def test_truncate_number_thousands(self):
        """تست کوتاه‌سازی اعداد هزار"""
        assert truncate_number(1500) == "1.5K"
        assert truncate_number(999999) == "1000.0K"

    def test_truncate_number_millions(self):
        """تست کوتاه‌سازی اعداد میلیون"""
        assert truncate_number(1500000) == "1.5M"
        assert truncate_number(999999999) == "1000.0M"

    def test_truncate_number_billions(self):
        """تست کوتاه‌سازی اعداد میلیارد"""
        assert truncate_number(1500000000) == "1.5B"
        assert truncate_number(999999999999) == "1000.0B"

    def test_truncate_number_trillions(self):
        """تست کوتاه‌سازی اعداد تریلیون"""
        assert truncate_number(1500000000000) == "1.5T"

    def test_truncate_number_none(self):
        """تست کوتاه‌سازی با None"""
        assert truncate_number(None) == "۰"

    # ============================================================
    # تست‌های human_readable_size
    # ============================================================

    def test_human_readable_size_bytes(self):
        """تست تبدیل حجم به بایت"""
        assert human_readable_size(0) == "۰ B"
        assert human_readable_size(500) == "500.00 B"

    def test_human_readable_size_kb(self):
        """تست تبدیل حجم به کیلوبایت"""
        assert human_readable_size(1024) == "1.00 KB"
        assert human_readable_size(1536) == "1.50 KB"

    def test_human_readable_size_mb(self):
        """تست تبدیل حجم به مگابایت"""
        assert human_readable_size(1048576) == "1.00 MB"

    def test_human_readable_size_gb(self):
        """تست تبدیل حجم به گیگابایت"""
        assert human_readable_size(1073741824) == "1.00 GB"

    def test_human_readable_size_none(self):
        """تست تبدیل حجم با None"""
        assert human_readable_size(None) == "نامشخص"

    # ============================================================
    # تست‌های format_datetime
    # ============================================================

    def test_format_datetime_with_datetime(self):
        """تست فرمت‌بندی تاریخ با datetime"""
        dt = datetime(2024, 1, 15, 14, 30, 0)
        assert format_datetime(dt) == "2024-01-15 14:30"

    def test_format_datetime_with_iso_string(self):
        """تست فرمت‌بندی تاریخ با رشته ISO"""
        assert format_datetime("2024-01-15T14:30:00") == "2024-01-15 14:30"
        assert format_datetime("2024-01-15T14:30:00Z") == "2024-01-15 14:30"

    def test_format_datetime_with_simple_string(self):
        """تست فرمت‌بندی تاریخ با رشته ساده"""
        assert format_datetime("2024-01-15 14:30:00") == "2024-01-15 14:30"
        assert format_datetime("2024-01-15") == "2024-01-15"

    def test_format_datetime_none(self):
        """تست فرمت‌بندی تاریخ با None"""
        assert format_datetime(None) == "نامشخص"
        assert format_datetime("") == "نامشخص"

    # ============================================================
    # تست‌های format_date
    # ============================================================

    def test_format_date_with_datetime(self):
        """تست فرمت‌بندی تاریخ با datetime"""
        dt = datetime(2024, 1, 15, 14, 30, 0)
        assert format_date(dt) == "2024-01-15"

    def test_format_date_with_string(self):
        """تست فرمت‌بندی تاریخ با رشته"""
        assert format_date("2024-01-15") == "2024-01-15"
        assert format_date("2024-01-15T14:30:00") == "2024-01-15"
        assert format_date("2024-01-15 14:30:00") == "2024-01-15"

    def test_format_date_none(self):
        """تست فرمت‌بندی تاریخ با None"""
        assert format_date(None) == "نامشخص"

    # ============================================================
    # تست‌های format_time
    # ============================================================

    def test_format_time_with_datetime(self):
        """تست فرمت‌بندی زمان با datetime"""
        dt = datetime(2024, 1, 15, 14, 30, 0)
        assert format_time(dt) == "14:30"

    def test_format_time_with_string(self):
        """تست فرمت‌بندی زمان با رشته"""
        assert format_time("14:30:00") == "14:30"
        assert format_time("2024-01-15T14:30:00") == "14:30"
        assert format_time("2024-01-15 14:30:00") == "14:30"

    def test_format_time_none(self):
        """تست فرمت‌بندی زمان با None"""
        assert format_time(None) == "نامشخص"

    # ============================================================
    # تست‌های format_duration
    # ============================================================

    def test_format_duration_seconds(self):
        """تست فرمت‌بندی مدت زمان به ثانیه"""
        assert format_duration(30) == "30 ثانیه"
        assert format_duration(59) == "59 ثانیه"

    def test_format_duration_minutes(self):
        """تست فرمت‌بندی مدت زمان به دقیقه"""
        assert format_duration(60) == "1 دقیقه"
        assert format_duration(120) == "2 دقیقه"
        assert format_duration(90) == "1 دقیقه"

    def test_format_duration_hours(self):
        """تست فرمت‌بندی مدت زمان به ساعت"""
        assert format_duration(3600) == "1 ساعت"
        assert format_duration(7200) == "2 ساعت"
        assert format_duration(4500) == "1 ساعت و 15 دقیقه"

    def test_format_duration_days(self):
        """تست فرمت‌بندی مدت زمان به روز"""
        assert format_duration(86400) == "1 روز"
        assert format_duration(172800) == "2 روز"
        assert format_duration(90000) == "1 روز و 1 ساعت"

    def test_format_duration_complex(self):
        """تست فرمت‌بندی مدت زمان ترکیبی"""
        assert format_duration(93700) == "1 روز و 2 ساعت و 1 دقیقه"

    def test_format_duration_none(self):
        """تست فرمت‌بندی مدت زمان با None"""
        assert format_duration(None) == "نامشخص"

    def test_format_duration_negative(self):
        """تست فرمت‌بندی مدت زمان منفی"""
        assert format_duration(-100) == "نامشخص"

    # ============================================================
    # تست‌های human_readable_time
    # ============================================================

    def test_human_readable_time_now(self):
        """تست زمان نسبی برای لحظه حال"""
        result = human_readable_time(datetime.now())
        assert "لحظه" in result or "پیش" in result

    def test_human_readable_time_minutes(self):
        """تست زمان نسبی برای دقیقه‌ها"""
        dt = datetime.now() - timedelta(minutes=5)
        result = human_readable_time(dt)
        assert "دقیقه" in result

    def test_human_readable_time_hours(self):
        """تست زمان نسبی برای ساعت‌ها"""
        dt = datetime.now() - timedelta(hours=2)
        result = human_readable_time(dt)
        assert "ساعت" in result

    def test_human_readable_time_days(self):
        """تست زمان نسبی برای روزها"""
        dt = datetime.now() - timedelta(days=3)
        result = human_readable_time(dt)
        assert "روز" in result

    def test_human_readable_time_weeks(self):
        """تست زمان نسبی برای هفته‌ها"""
        dt = datetime.now() - timedelta(days=14)
        result = human_readable_time(dt)
        assert "هفته" in result

    def test_human_readable_time_months(self):
        """تست زمان نسبی برای ماه‌ها"""
        dt = datetime.now() - timedelta(days=60)
        result = human_readable_time(dt)
        assert "ماه" in result

    def test_human_readable_time_years(self):
        """تست زمان نسبی برای سال‌ها"""
        dt = datetime.now() - timedelta(days=400)
        result = human_readable_time(dt)
        assert "سال" in result

    def test_human_readable_time_with_timestamp(self):
        """تست زمان نسبی با timestamp عددی"""
        timestamp = int(datetime.now().timestamp()) - 3600
        result = human_readable_time(timestamp)
        assert "ساعت" in result or "پیش" in result

    def test_human_readable_time_none(self):
        """تست زمان نسبی با None"""
        result = human_readable_time(None)
        assert "نامشخص" in result or result == "نامشخص"

    # ============================================================
    # تست‌های format_phone
    # ============================================================

    def test_format_phone_mobile(self):
        """تست فرمت‌بندی شماره تلفن همراه"""
        assert format_phone("09123456789") == "0912 345 6789"
        assert format_phone("0912-345-6789") == "0912 345 6789"

    def test_format_phone_landline(self):
        """تست فرمت‌بندی شماره تلفن ثابت"""
        assert format_phone("0212345678") == "021 234 5678"
        assert format_phone("021-234-5678") == "021 234 5678"

    def test_format_phone_empty(self):
        """تست فرمت‌بندی شماره تلفن خالی"""
        assert format_phone(None) == "نامشخص"
        assert format_phone("") == "نامشخص"
        assert format_phone("", default="ندارد") == "ندارد"

    # ============================================================
    # تست‌های format_national_code
    # ============================================================

    def test_format_national_code(self):
        """تست فرمت‌بندی کد ملی"""
        assert format_national_code("0123456789") == "0123456789"
        assert format_national_code("1234567890") == "1234567890"

    def test_format_national_code_with_spaces(self):
        """تست فرمت‌بندی کد ملی با فاصله"""
        assert format_national_code("012 345 6789") == "0123456789"

    def test_format_national_code_empty(self):
        """تست فرمت‌بندی کد ملی خالی"""
        assert format_national_code(None) == "نامشخص"
        assert format_national_code("") == "نامشخص"

    def test_format_national_code_short(self):
        """تست فرمت‌بندی کد ملی کوتاه"""
        assert format_national_code("12345") == "12345"

    # ============================================================
    # تست‌های format_tracking_code
    # ============================================================

    def test_format_tracking_code_long(self):
        """تست فرمت‌بندی کد رهگیری بلند"""
        assert format_tracking_code("TRK12345678") == "TRK1-2345-678"
        assert format_tracking_code("1234567890") == "1234-5678-90"

    def test_format_tracking_code_short(self):
        """تست فرمت‌بندی کد رهگیری کوتاه"""
        assert format_tracking_code("1234") == "1234"
        assert format_tracking_code("ABC") == "ABC"

    def test_format_tracking_code_empty(self):
        """تست فرمت‌بندی کد رهگیری خالی"""
        assert format_tracking_code(None) == "ندارد"
        assert format_tracking_code("") == "ندارد"

    # ============================================================
    # تست‌های format_order_status
    # ============================================================

    def test_format_order_status(self):
        """تست فرمت‌بندی وضعیت سفارش"""
        assert "در انتظار" in format_order_status("pending")
        assert "پرداخت" in format_order_status("paid")
        assert "تکمیل" in format_order_status("completed")
        assert "لغو" in format_order_status("cancelled")
        assert "ناموفق" in format_order_status("failed")
        assert "بازگشت" in format_order_status("refunded")

    def test_format_order_status_unknown(self):
        """تست فرمت‌بندی وضعیت ناشناخته"""
        assert format_order_status("unknown") == "unknown"

    # ============================================================
    # تست‌های format_ordered_list
    # ============================================================

    def test_format_ordered_list(self):
        """تست فرمت‌بندی لیست شماره‌دار"""
        items = ["اول", "دوم", "سوم"]
        result = format_ordered_list(items)
        expected = "1. اول\n2. دوم\n3. سوم"
        assert result == expected

    def test_format_ordered_list_with_start(self):
        """تست فرمت‌بندی لیست شماره‌دار با شماره شروع"""
        items = ["اول", "دوم", "سوم"]
        result = format_ordered_list(items, start=5)
        expected = "5. اول\n6. دوم\n7. سوم"
        assert result == expected

    def test_format_ordered_list_empty(self):
        """تست فرمت‌بندی لیست خالی"""
        assert format_ordered_list([]) == ""

    # ============================================================
    # تست‌های format_bullet_list
    # ============================================================

    def test_format_bullet_list(self):
        """تست فرمت‌بندی لیست گلوله‌ای"""
        items = ["اول", "دوم", "سوم"]
        result = format_bullet_list(items)
        expected = "• اول\n• دوم\n• سوم"
        assert result == expected

    def test_format_bullet_list_with_custom_bullet(self):
        """تست فرمت‌بندی لیست گلوله‌ای با علامت سفارشی"""
        items = ["اول", "دوم", "سوم"]
        result = format_bullet_list(items, bullet="-")
        expected = "- اول\n- دوم\n- سوم"
        assert result == expected

    def test_format_bullet_list_empty(self):
        """تست فرمت‌بندی لیست خالی"""
        assert format_bullet_list([]) == ""

    # ============================================================
    # تست‌های format_key_value
    # ============================================================

    def test_format_key_value(self):
        """تست فرمت‌بندی کلید-مقدار"""
        assert format_key_value("نام", "علی") == "نام: علی"
        assert format_key_value("سن", 25) == "سن: 25"

    def test_format_key_value_custom_separator(self):
        """تست فرمت‌بندی کلید-مقدار با جداکننده سفارشی"""
        assert format_key_value("نام", "علی", separator=" = ") == "نام = علی"

    # ============================================================
    # تست‌های format_key_value_list
    # ============================================================

    def test_format_key_value_list(self):
        """تست فرمت‌بندی لیست کلید-مقدار"""
        data = {"نام": "علی", "سن": 25, "شهر": "تهران"}
        result = format_key_value_list(data)
        expected = "نام: علی\nسن: 25\nشهر: تهران"
        assert result == expected

    def test_format_key_value_list_with_none(self):
        """تست فرمت‌بندی لیست کلید-مقدار با مقادیر None"""
        data = {"نام": "علی", "سن": None, "شهر": "تهران"}
        result = format_key_value_list(data)
        expected = "نام: علی\nشهر: تهران"
        assert result == expected

    def test_format_key_value_list_empty(self):
        """تست فرمت‌بندی لیست خالی"""
        assert format_key_value_list({}) == ""

    # ============================================================
    # تست‌های safe_int
    # ============================================================

    def test_safe_int_valid(self):
        """تست تبدیل ایمن به عدد صحیح"""
        assert safe_int("123") == 123
        assert safe_int("1,234") == 1234
        assert safe_int(" 123 ") == 123
        assert safe_int(456) == 456
        assert safe_int(123.45) == 123

    def test_safe_int_invalid(self):
        """تست تبدیل ایمن به عدد صحیح با مقدار نامعتبر"""
        assert safe_int("abc") == 0
        assert safe_int(None) == 0
        assert safe_int([]) == 0

    def test_safe_int_with_default(self):
        """تست تبدیل ایمن به عدد صحیح با مقدار پیش‌فرض"""
        assert safe_int("abc", default=10) == 10
        assert safe_int(None, default=10) == 10

    # ============================================================
    # تست‌های safe_float
    # ============================================================

    def test_safe_float_valid(self):
        """تست تبدیل ایمن به عدد اعشاری"""
        assert safe_float("123.45") == 123.45
        assert safe_float("1,234.56") == 1234.56
        assert safe_float(" 123.45 ") == 123.45
        assert safe_float(456.78) == 456.78
        assert safe_float(123) == 123.0

    def test_safe_float_invalid(self):
        """تست تبدیل ایمن به عدد اعشاری با مقدار نامعتبر"""
        assert safe_float("abc") == 0.0
        assert safe_float(None) == 0.0
        assert safe_float([]) == 0.0

    def test_safe_float_with_default(self):
        """تست تبدیل ایمن به عدد اعشاری با مقدار پیش‌فرض"""
        assert safe_float("abc", default=10.5) == 10.5
        assert safe_float(None, default=10.5) == 10.5

    # ============================================================
    # تست‌های format_number با اعداد بزرگ
    # ============================================================

    def test_format_number_very_large(self):
        """تست فرمت‌بندی اعداد بسیار بزرگ"""
        assert format_number(1234567890123456) == "1,234,567,890,123,456"

    # ============================================================
    # تست‌های human_readable_size با واحدهای مختلف
    # ============================================================

    def test_human_readable_size_pb(self):
        """تست تبدیل حجم به پتابایت"""
        # 1 PB = 1125899906842624 bytes
        assert "PB" in human_readable_size(1125899906842624)

    # ============================================================
    # تست‌های format_duration با مقادیر مرزی
    # ============================================================

    def test_format_duration_boundary_values(self):
        """تست فرمت‌بندی مدت زمان با مقادیر مرزی"""
        assert format_duration(59) == "59 ثانیه"
        assert format_duration(60) == "1 دقیقه"
        assert format_duration(3599) == "59 دقیقه"
        assert format_duration(3600) == "1 ساعت"
        assert format_duration(86399) == "23 ساعت و 59 دقیقه"
        assert format_duration(86400) == "1 روز"

    # ============================================================
    # تست‌های format_phone با فرمت‌های مختلف
    # ============================================================

    def test_format_phone_with_international(self):
        """تست فرمت‌بندی شماره تلفن بین‌المللی"""
        assert format_phone("+989123456789") == "+989123456789"
        assert format_phone("989123456789") == "989123456789"

    def test_format_phone_with_dash(self):
        """تست فرمت‌بندی شماره تلفن با خط تیره"""
        assert format_phone("021-234-5678") == "021 234 5678"