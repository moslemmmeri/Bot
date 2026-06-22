# admin_panel/orders/__init__.py
# پکیج مدیریت سفارشات - صادر کردن توابع اصلی از زیرماژول‌ها
# این فایل جایگزین admin_panel/orders.py شده است

"""
پکیج `orders` شامل مدیریت کامل سفارشات در پنل مدیریت است.

زیرماژول‌ها:
- grouping: گروه‌بندی سفارشات بر اساس تاریخ، سرویس و کاربر
- filtering: فیلترهای پیشرفته سفارشات (وضعیت، سرویس، ...)
- actions: تغییر وضعیت، حذف، یادداشت و جزئیات سفارش
- export: خروجی Excel و آمار سفارشات
- reminder: یادآوری سفارشات ناتمام
"""

# ============================================================
# ایمپورت از زیرماژول‌ها
# ============================================================

from .grouping import (
    handle_orders_list,
    handle_orders_group_by_date,
    handle_orders_date_page,
    handle_orders_date,
    handle_orders_service_page,
    handle_orders_service_back,
    handle_orders_service,
    handle_orders_user_page,
    handle_orders_user,
    handle_order_by_id,
)

from .filtering import (
    handle_orders_filter_start,
    handle_orders_filter_status,
    handle_orders_filter_service,
    handle_orders_filter_service_select,
    handle_orders_filter_apply,
    handle_orders_filter_clear,
    handle_orders_search,
    handle_orders_search_result,
)

from .actions import (
    handle_order_status_change,
    handle_order_status_change_confirm,
    handle_order_delete,
    handle_order_delete_confirm,
    handle_order_note,
    handle_order_note_add,
    handle_order_detail,
    show_order_detail,
)

from .export import (
    handle_orders_export,
    handle_orders_stats,
)

from .reminder import (
    handle_order_reminder,
    handle_order_remind_single,
    handle_order_remind_all,
)


# ============================================================
# صادر کردن همه توابع
# ============================================================

__all__ = [
    # grouping
    'handle_orders_list',
    'handle_orders_group_by_date',
    'handle_orders_date_page',
    'handle_orders_date',
    'handle_orders_service_page',
    'handle_orders_service_back',
    'handle_orders_service',
    'handle_orders_user_page',
    'handle_orders_user',
    'handle_order_by_id',
    
    # filtering
    'handle_orders_filter_start',
    'handle_orders_filter_status',
    'handle_orders_filter_service',
    'handle_orders_filter_service_select',
    'handle_orders_filter_apply',
    'handle_orders_filter_clear',
    'handle_orders_search',
    'handle_orders_search_result',
    
    # actions
    'handle_order_status_change',
    'handle_order_status_change_confirm',
    'handle_order_delete',
    'handle_order_delete_confirm',
    'handle_order_note',
    'handle_order_note_add',
    'handle_order_detail',
    'show_order_detail',
    
    # export
    'handle_orders_export',
    'handle_orders_stats',
    
    # reminder
    'handle_order_reminder',
    'handle_order_remind_single',
    'handle_order_remind_all',
]