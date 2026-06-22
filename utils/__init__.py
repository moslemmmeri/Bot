# utils/__init__.py
# پکیج توابع کمکی (Utility Functions)
# شامل توابع عمومی برای فرمت‌بندی، پردازش سفارشات، کاربران و متون

"""
پکیج `utils` شامل توابع کمکی و ابزاری برای استفاده در سراسر پروژه است.

این پکیج توابع پرکاربرد را در دسته‌بندی‌های زیر ارائه می‌دهد:

- **formatters**: فرمت‌بندی اعداد، درصد، تاریخ، قیمت و ...
- **order_helpers**: توابع کمکی برای پردازش سفارشات (نام سرویس، نام کاربر، وضعیت، ...)
- **user_helpers**: توابع کمکی برای کاربران (نام نمایشی، نقش، وضعیت، ...)
- **text_helpers**: توابع کمکی برای پردازش متن (کوتاه‌سازی، JSON، پاک‌سازی، ...)

استفاده:
    from utils import format_number, get_service_name, get_user_display_name, truncate_text
"""

# ============================================================
# ایمپورت از زیرماژول‌ها
# ============================================================

from .formatters import (
    format_number,
    format_percent,
    format_datetime,
    format_date,
    format_time,
    format_price,
    format_currency,
    format_duration,
    format_phone,
    format_national_code,
    format_tracking_code,
    format_order_status,
    format_boolean,
    format_yes_no,
    truncate_number,
    human_readable_size,
    human_readable_time,
    get_today_str,
    get_yesterday_str,
    get_date_range,
    get_error_type_icon,
)

from .order_helpers import (
    get_service_name,
    get_fullname_from_order,
    extract_date_from_order,
    get_order_status_persian,
    get_order_status_icon,
    get_order_status_color,
    get_order_status_emoji,
    is_order_paid,
    is_order_pending,
    is_order_completed,
    is_order_cancelled,
    get_order_amount,
    get_order_tracking_code,
    get_order_admin_note,
    get_order_status_history,
    extract_answers_from_order,
    extract_files_from_order,
    get_order_summary,
)

from .user_helpers import (
    get_user_display_name,
    get_user_full_name,
    get_user_short_name,
    get_role_label,
    get_role_icon,
    get_status_label,
    get_status_icon,
    get_user_mention,
    get_user_profile_link,
    is_user_active,
    is_user_blocked,
    get_user_status_text,
    get_user_last_active_text,
    get_user_joined_date,
    get_user_orders_summary,
    get_user_activity_summary,
)

from .text_helpers import (
    truncate_text,
    safe_json_loads,
    clean_text,
    normalize_text,
    remove_extra_spaces,
    escape_markdown,
    unescape_markdown,
    split_text_by_length,
    chunk_text,
    extract_hashtags,
    extract_mentions,
    is_valid_email,
    is_valid_phone,
    is_valid_national_code,
    is_valid_url,
    is_valid_uuid,
    generate_random_code,
    generate_tracking_code,
    make_slug,
    sanitize_filename,
)


# ============================================================
# صادر کردن همه توابع
# ============================================================

__all__ = [
    # formatters
    'format_number',
    'format_percent',
    'format_datetime',
    'format_date',
    'format_time',
    'format_price',
    'format_currency',
    'format_duration',
    'format_phone',
    'format_national_code',
    'format_tracking_code',
    'format_order_status',
    'format_boolean',
    'format_yes_no',
    'truncate_number',
    'human_readable_size',
    'human_readable_time',
    'get_today_str',
    'get_yesterday_str',
    'get_date_range',
    'get_error_type_icon',
    
    # order_helpers
    'get_service_name',
    'get_fullname_from_order',
    'extract_date_from_order',
    'get_order_status_persian',
    'get_order_status_icon',
    'get_order_status_color',
    'get_order_status_emoji',
    'is_order_paid',
    'is_order_pending',
    'is_order_completed',
    'is_order_cancelled',
    'get_order_amount',
    'get_order_tracking_code',
    'get_order_admin_note',
    'get_order_status_history',
    'extract_answers_from_order',
    'extract_files_from_order',
    'get_order_summary',
    
    # user_helpers
    'get_user_display_name',
    'get_user_full_name',
    'get_user_short_name',
    'get_role_label',
    'get_role_icon',
    'get_status_label',
    'get_status_icon',
    'get_user_mention',
    'get_user_profile_link',
    'is_user_active',
    'is_user_blocked',
    'get_user_status_text',
    'get_user_last_active_text',
    'get_user_joined_date',
    'get_user_orders_summary',
    'get_user_activity_summary',
    
    # text_helpers
    'truncate_text',
    'safe_json_loads',
    'clean_text',
    'normalize_text',
    'remove_extra_spaces',
    'escape_markdown',
    'unescape_markdown',
    'split_text_by_length',
    'chunk_text',
    'extract_hashtags',
    'extract_mentions',
    'is_valid_email',
    'is_valid_phone',
    'is_valid_national_code',
    'is_valid_url',
    'is_valid_uuid',
    'generate_random_code',
    'generate_tracking_code',
    'make_slug',
    'sanitize_filename',
]