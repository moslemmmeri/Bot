# keyboards/__init__.py
# پکیج کیبوردها - صادر کردن کیبوردها از ماژول‌های مختلف
# شامل کیبوردهای منوها، سرویس‌ها، مدیریت، اعتبارسنجی، ستون‌ها و مانیتورینگ

from .kb_menus import (
    main_menu_keyboard,
    more_menu_keyboard,
    tax_main_keyboard,
    car_services_keyboard,
    tax_services_keyboard,
    insurance_services_keyboard,
    judicial_services_keyboard,
    banking_services_keyboard,
    online_reg_services_keyboard,
    loan_services_keyboard,
    license_services_keyboard,
    medical_services_keyboard,
    design_services_keyboard,
    ticket_services_keyboard,
    postal_services_keyboard,
    bill_services_keyboard,
    currency_services_keyboard,
    other_services_keyboard,
    household_services_keyboard,
    chunk_list,
    get_dynamic_menu_keyboard,
    preview_menu_keyboard,
    preview_main_menu,
    preview_more_menu,
    preview_other_menu,
)

from .kb_services import (
    abolaghieh_recovery_keyboard,
    tax_recovery_keyboard,
    description_skip_keyboard,
    suborder_type_keyboard,
    print_type_keyboard,
    sided_keyboard,
    vehicle_type_keyboard,
    vehicle_type_for_inspection_keyboard,
    power_of_attorney_keyboard,
    recovery_keyboard,
    declaration_type_keyboard,
    tax_payment_type_keyboard,
    travel_type_keyboard,
    tax_period_keyboard,
    property_status_keyboard,
)

from .kb_admin_validation import (
    admin_validation_main_keyboard,
    admin_validation_toggle_keyboard,
    admin_validation_type_keyboard,
    admin_validation_presets_keyboard,
    admin_validation_confirm_keyboard,
)

from .kb_admin_common import (
    admin_main_keyboard,
    admin_questions_keyboard,
    admin_question_options_keyboard,
    admin_submenu_keyboard,
    condition_operator_keyboard,
    logic_operator_keyboard,
    yes_no_keyboard,
    admin_categories_keyboard,
    admin_category_buttons_keyboard,
    admin_submenu_list_keyboard,
    admin_category_delete_confirm_keyboard,
    admin_category_columns_keyboard,
    admin_button_columns_keyboard,
    admin_admins_list_keyboard,
    admin_admin_detail_keyboard,
    admin_roles_keyboard,
    admin_add_admin_roles_keyboard,
    admin_remove_confirm_keyboard,
    admin_search_keyboard,
    admin_stats_keyboard,
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
    admin_errors_main_keyboard,
    admin_errors_list_keyboard,
    admin_errors_detail_keyboard,
    admin_errors_stats_keyboard,
    admin_errors_cleanup_confirm_keyboard,
    admin_errors_clear_all_confirm_keyboard,
)

# ========== کیبوردهای مدیریت پیشرفته ستون‌ها ==========
from .kb_column_preview import (
    column_management_main_keyboard,
    column_category_list_keyboard,
    column_category_edit_keyboard,
    column_button_list_keyboard,
    column_button_edit_keyboard,
    column_preview_keyboard,
    column_reset_confirm_keyboard,
    column_set_quick_keyboard,
    column_status_keyboard,
)

# ========== کیبوردهای جدید مانیتورینگ ==========
from .kb_monitoring import (
    monitoring_main_keyboard,
    monitoring_health_keyboard,
    monitoring_health_detail_keyboard,
    monitoring_alerts_keyboard,
    monitoring_alert_detail_keyboard,
    monitoring_metrics_keyboard,
    monitoring_metrics_type_keyboard,
    monitoring_reports_keyboard,
    monitoring_reports_list_keyboard,
    monitoring_report_detail_keyboard,
    monitoring_confirm_keyboard,
    monitoring_empty_keyboard,
    monitoring_back_keyboard,
)


# ========== تابع کمکی برای افزودن دکمه پنل مدیریت ==========
def admin_panel_button(keyboard):
    """
    افزودن دکمه پنل مدیریت به کیبورد (فقط برای ادمین‌ها)
    """
    if "inline_keyboard" in keyboard:
        keyboard["inline_keyboard"].append(
            [{"text": "🔐 پنل مدیریت", "callback_data": "admin_panel"}]
        )
    return keyboard


__all__ = [
    # kb_menus
    'main_menu_keyboard',
    'more_menu_keyboard',
    'tax_main_keyboard',
    'car_services_keyboard',
    'tax_services_keyboard',
    'insurance_services_keyboard',
    'judicial_services_keyboard',
    'banking_services_keyboard',
    'online_reg_services_keyboard',
    'loan_services_keyboard',
    'license_services_keyboard',
    'medical_services_keyboard',
    'design_services_keyboard',
    'ticket_services_keyboard',
    'postal_services_keyboard',
    'bill_services_keyboard',
    'currency_services_keyboard',
    'other_services_keyboard',
    'household_services_keyboard',
    'chunk_list',
    'get_dynamic_menu_keyboard',
    'preview_menu_keyboard',
    'preview_main_menu',
    'preview_more_menu',
    'preview_other_menu',
    
    # kb_services
    'abolaghieh_recovery_keyboard',
    'tax_recovery_keyboard',
    'description_skip_keyboard',
    'suborder_type_keyboard',
    'print_type_keyboard',
    'sided_keyboard',
    'vehicle_type_keyboard',
    'vehicle_type_for_inspection_keyboard',
    'power_of_attorney_keyboard',
    'recovery_keyboard',
    'declaration_type_keyboard',
    'tax_payment_type_keyboard',
    'travel_type_keyboard',
    'tax_period_keyboard',
    'property_status_keyboard',
    
    # kb_admin_validation
    'admin_validation_main_keyboard',
    'admin_validation_toggle_keyboard',
    'admin_validation_type_keyboard',
    'admin_validation_presets_keyboard',
    'admin_validation_confirm_keyboard',
    
    # kb_admin_common
    'admin_main_keyboard',
    'admin_questions_keyboard',
    'admin_question_options_keyboard',
    'admin_submenu_keyboard',
    'condition_operator_keyboard',
    'logic_operator_keyboard',
    'yes_no_keyboard',
    'admin_categories_keyboard',
    'admin_category_buttons_keyboard',
    'admin_submenu_list_keyboard',
    'admin_category_delete_confirm_keyboard',
    'admin_category_columns_keyboard',
    'admin_button_columns_keyboard',
    'admin_admins_list_keyboard',
    'admin_admin_detail_keyboard',
    'admin_roles_keyboard',
    'admin_add_admin_roles_keyboard',
    'admin_remove_confirm_keyboard',
    'admin_search_keyboard',
    'admin_stats_keyboard',
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
    'admin_errors_main_keyboard',
    'admin_errors_list_keyboard',
    'admin_errors_detail_keyboard',
    'admin_errors_stats_keyboard',
    'admin_errors_cleanup_confirm_keyboard',
    'admin_errors_clear_all_confirm_keyboard',
    
    # kb_column_preview
    'column_management_main_keyboard',
    'column_category_list_keyboard',
    'column_category_edit_keyboard',
    'column_button_list_keyboard',
    'column_button_edit_keyboard',
    'column_preview_keyboard',
    'column_reset_confirm_keyboard',
    'column_set_quick_keyboard',
    'column_status_keyboard',

    # kb_monitoring (جدید)
    'monitoring_main_keyboard',
    'monitoring_health_keyboard',
    'monitoring_health_detail_keyboard',
    'monitoring_alerts_keyboard',
    'monitoring_alert_detail_keyboard',
    'monitoring_metrics_keyboard',
    'monitoring_metrics_type_keyboard',
    'monitoring_reports_keyboard',
    'monitoring_reports_list_keyboard',
    'monitoring_report_detail_keyboard',
    'monitoring_confirm_keyboard',
    'monitoring_empty_keyboard',
    'monitoring_back_keyboard',

    # تابع کمکی
    'admin_panel_button',
]