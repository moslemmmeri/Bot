# admin_panel/search/__init__.py
# پکیج جستجوی پیشرفته سفارشات
# این فایل به‌عنوان نقطه‌ی ورودی پکیج عمل می‌کند و توابع اصلی را صادر می‌کند.

"""
پکیج `search` شامل جستجوی پیشرفته در سفارشات با فیلترهای متعدد است.

زیرماژول‌ها:
- core: کلاس AdvancedSearch و منطق اصلی جستجو
- handlers: هندلرهای کالبک جستجو
- keyboards: کیبوردهای مربوط به جستجو
- message_handlers: پردازش پیام‌های جستجو

استفاده:
    from admin_panel.search import (
        AdvancedSearch,
        handle_advanced_search,
        handle_search_results,
        ...
    )
"""

# ============================================================
# ایمپورت از زیرماژول‌ها
# ============================================================

from .core import (
    AdvancedSearch,
)

from .handlers import (
    handle_advanced_search,
    handle_search_quick,
    handle_search_date,
    handle_search_amount,
    handle_search_status,
    handle_search_status_toggle,
    handle_search_status_apply,
    handle_search_status_clear,
    handle_search_service,
    handle_search_service_toggle,
    handle_search_service_page,
    handle_search_service_apply,
    handle_search_service_clear,
    handle_search_user,
    handle_search_tracking,
    handle_search_has_file,
    handle_search_reset,
    handle_search_results,
    handle_search_page,
    handle_search_order_detail,
    handle_search_export,
)

from .message_handlers import (
    handle_adv_search_message,
)

from .keyboards import (
    advanced_search_main_keyboard,
    search_results_keyboard,
    search_status_keyboard,
    search_service_keyboard,
)


# ============================================================
# صادر کردن همه توابع
# ============================================================

__all__ = [
    # core
    'AdvancedSearch',
    
    # handlers
    'handle_advanced_search',
    'handle_search_quick',
    'handle_search_date',
    'handle_search_amount',
    'handle_search_status',
    'handle_search_status_toggle',
    'handle_search_status_apply',
    'handle_search_status_clear',
    'handle_search_service',
    'handle_search_service_toggle',
    'handle_search_service_page',
    'handle_search_service_apply',
    'handle_search_service_clear',
    'handle_search_user',
    'handle_search_tracking',
    'handle_search_has_file',
    'handle_search_reset',
    'handle_search_results',
    'handle_search_page',
    'handle_search_order_detail',
    'handle_search_export',
    
    # message_handlers
    'handle_adv_search_message',
    
    # keyboards
    'advanced_search_main_keyboard',
    'search_results_keyboard',
    'search_status_keyboard',
    'search_service_keyboard',
]