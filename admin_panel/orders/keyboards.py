# admin_panel/orders/keyboards.py
# کیبوردهای مربوط به مدیریت سفارشات
# این فایل به‌عنوان لایه‌ی واسط، کیبوردهای مورد نیاز را از ماژول اصلی کیبوردها import و export می‌کند

import traceback  # ✅ اضافه شد برای traceback کامل (در صورت استفاده در آینده)
from utils.error_handler import (  # ✅ اضافه شد برای استفاده در صورت اضافه شدن logic
    log_general_error,
    log_callback_error,
    log_database_error
)

from keyboards.kb_admin_common import (
    admin_orders_menu_keyboard,
    admin_orders_filter_keyboard,
    admin_orders_filter_service_keyboard,
    admin_orders_status_keyboard,
    admin_order_delete_confirm_keyboard,
    admin_order_detail_actions_keyboard,
    admin_order_note_keyboard,
    admin_order_stats_keyboard,
    admin_orders_search_keyboard,
    admin_orders_export_keyboard,
    admin_order_reminder_keyboard,
)

__all__ = [
    'admin_orders_menu_keyboard',
    'admin_orders_filter_keyboard',
    'admin_orders_filter_service_keyboard',
    'admin_orders_status_keyboard',
    'admin_order_delete_confirm_keyboard',
    'admin_order_detail_actions_keyboard',
    'admin_order_note_keyboard',
    'admin_order_stats_keyboard',
    'admin_orders_search_keyboard',
    'admin_orders_export_keyboard',
    'admin_order_reminder_keyboard',
]