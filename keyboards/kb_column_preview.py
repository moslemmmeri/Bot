# keyboards/kb_column_preview.py
# کیبوردهای مدیریت پیشرفته ستون‌های منو
# شامل: منوی اصلی، لیست دسته‌بندی‌ها، ویرایش دسته‌بندی، ویرایش دکمه، پیش‌نمایش و تنظیم سریع

from database import get_category_by_id, get_button_by_id


def column_management_main_keyboard(default_columns, categories, buttons_with_custom):
    """
    کیبورد اصلی مدیریت پیشرفته ستون‌ها
    
    پارامترها:
        default_columns: تعداد ستون‌های پیش‌فرض عمومی
        categories: لیست دسته‌بندی‌ها با وضعیت
        buttons_with_custom: لیست دکمه‌های با تنظیمات اختصاصی
    """
    keyboard = []
    
    # بخش تنظیمات سریع
    keyboard.append([{"text": "⚡ تنظیم سریع (همه منوها)", "callback_data": "admin_col_quick_2"}])
    keyboard.append([
        {"text": "2 ستون", "callback_data": "admin_col_quick_2"},
        {"text": "3 ستون", "callback_data": "admin_col_quick_3"},
        {"text": "4 ستون", "callback_data": "admin_col_quick_4"},
        {"text": "6 ستون", "callback_data": "admin_col_quick_6"}
    ])
    
    # بخش مدیریت دسته‌بندی‌ها
    keyboard.append([{"text": "📂 مدیریت دسته‌بندی‌ها", "callback_data": "admin_col_cat_list"}])
    
    # نمایش وضعیت سریع دسته‌بندی‌ها
    for cat in categories[:5]:  # نمایش فقط ۵ مورد اول
        icon = "🌟" if cat['has_custom'] else "📌"
        keyboard.append([
            {"text": f"{icon} {cat['name']}: {cat['effective']} ستون", 
             "callback_data": f"admin_col_cat_edit_{cat['id']}"}
        ])
    if len(categories) > 5:
        keyboard.append([{"text": f"... و {len(categories) - 5} دسته‌بندی دیگر", "callback_data": "admin_col_cat_list"}])
    
    # بخش مدیریت دکمه‌ها
    keyboard.append([{"text": "🔘 مدیریت دکمه‌های خاص", "callback_data": "admin_col_btn_list"}])
    if buttons_with_custom:
        keyboard.append([{"text": f"🔘 {len(buttons_with_custom)} دکمه با تنظیمات اختصاصی", "callback_data": "admin_col_btn_list"}])
    
    # بخش تنظیمات پیش‌فرض
    keyboard.append([
        {"text": f"🔧 تنظیم پیش‌فرض عمومی (فعلی: {default_columns})", "callback_data": "admin_col_set_default_2"}
    ])
    keyboard.append([
        {"text": "1", "callback_data": "admin_col_set_default_1"},
        {"text": "2", "callback_data": "admin_col_set_default_2"},
        {"text": "3", "callback_data": "admin_col_set_default_3"},
        {"text": "4", "callback_data": "admin_col_set_default_4"},
        {"text": "5", "callback_data": "admin_col_set_default_5"},
        {"text": "6", "callback_data": "admin_col_set_default_6"},
        {"text": "7", "callback_data": "admin_col_set_default_7"},
        {"text": "8", "callback_data": "admin_col_set_default_8"}
    ])
    
    # بخش بازنشانی
    keyboard.append([{"text": "🔄 بازنشانی همه تنظیمات", "callback_data": "admin_col_reset"}])
    
    # برگشت
    keyboard.append([{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}])
    
    return {"inline_keyboard": keyboard}


def column_category_list_keyboard(categories):
    """
    کیبورد لیست دسته‌بندی‌ها برای مدیریت ستون‌ها
    
    پارامترها:
        categories: لیست دسته‌بندی‌ها با وضعیت
    """
    keyboard = []
    
    for cat in categories:
        icon = "🌟" if cat['has_custom'] else "📌"
        keyboard.append([
            {"text": f"{icon} {cat['name']} - {cat['effective']} ستون (اختصاصی: {cat['custom'] if cat['has_custom'] else 'پیش‌فرض'})",
             "callback_data": f"admin_col_cat_edit_{cat['id']}"}
        ])
    
    keyboard.append([
        {"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_columns"}
    ])
    
    return {"inline_keyboard": keyboard}


def column_category_edit_keyboard(category_id, current_columns, effective, default, buttons, submenus=None):
    """
    کیبورد ویرایش ستون‌های یک دسته‌بندی
    
    پارامترها:
        category_id: شناسه دسته‌بندی
        current_columns: ستون‌های فعلی (یا None)
        effective: ستون‌های مؤثر
        default: ستون‌های پیش‌فرض عمومی
        buttons: لیست دکمه‌های دسته‌بندی
        submenus: لیست زیرمنوها (اختیاری)
    """
    keyboard = []
    
    # عنوان
    keyboard.append([{"text": f"📊 تنظیم ستون‌های این دسته‌بندی"}])
    
    # گزینه‌های انتخاب ستون
    columns_options = [
        (1, "۱ ستون"),
        (2, "۲ ستون"),
        (3, "۳ ستون"),
        (4, "۴ ستون"),
        (5, "۵ ستون"),
        (6, "۶ ستون"),
        (7, "۷ ستون"),
        (8, "۸ ستون")
    ]
    
    for col, label in columns_options:
        selected = "✅ " if col == current_columns else ""
        callback = f"admin_col_cat_set_{category_id}_{col}"
        keyboard.append([
            {"text": f"{selected}{label}", "callback_data": callback}
        ])
    
    # گزینه حذف تنظیمات اختصاصی
    if current_columns is not None:
        keyboard.append([
            {"text": "❌ حذف تنظیمات اختصاصی (استفاده از پیش‌فرض)", 
             "callback_data": f"admin_col_cat_set_{category_id}_null"}
        ])
    
    keyboard.append([{"text": "─────────────"}])
    
    # پیش‌نمایش
    keyboard.append([
        {"text": "👁️ پیش‌نمایش با ۲ ستون", "callback_data": f"admin_col_preview_{category_id}_2"},
        {"text": "👁️ پیش‌نمایش با ۴ ستون", "callback_data": f"admin_col_preview_{category_id}_4"},
        {"text": "👁️ پیش‌نمایش با ۶ ستون", "callback_data": f"admin_col_preview_{category_id}_6"}
    ])
    
    keyboard.append([{"text": "─────────────"}])
    
    # اطلاعات دکمه‌های این دسته‌بندی
    if buttons:
        keyboard.append([{"text": f"🔘 {len(buttons)} دکمه در این دسته‌بندی"}])
        # نمایش دکمه‌هایی که تنظیمات اختصاصی دارند
        for btn in buttons:
            if btn['has_custom']:
                keyboard.append([
                    {"text": f"  ✏️ {btn['name']}: {btn['effective']} ستون (اختصاصی: {btn['custom']})",
                     "callback_data": f"admin_col_btn_edit_{btn['id']}"}
                ])
    
    # اطلاعات زیرمنوها
    if submenus:
        keyboard.append([{"text": f"📋 {len(submenus)} زیرمنو در این دسته‌بندی"}])
        for sub in submenus[:3]:  # نمایش فقط ۳ مورد اول
            if sub['has_custom']:
                keyboard.append([
                    {"text": f"  ✏️ {sub['parent_name']} > {sub['name']}: {sub['effective']} ستون",
                     "callback_data": f"admin_col_btn_edit_{sub['id']}"}
                ])
        if len(submenus) > 3:
            keyboard.append([{"text": f"  ... و {len(submenus) - 3} زیرمنو دیگر", "callback_data": "admin_col_btn_list"}])
    
    keyboard.append([{"text": "─────────────"}])
    
    # برگشت
    keyboard.append([
        {"text": "🔙 برگشت به لیست دسته‌بندی‌ها", "callback_data": "admin_col_cat_list"},
        {"text": "🏠 برگشت به منوی اصلی", "callback_data": "admin_columns"}
    ])
    
    return {"inline_keyboard": keyboard}


def column_button_list_keyboard(buttons):
    """
    کیبورد لیست دکمه‌ها برای مدیریت ستون‌ها
    
    پارامترها:
        buttons: لیست دکمه‌ها با وضعیت
    """
    keyboard = []
    
    # فیلتر دکمه‌های با تنظیمات اختصاصی
    custom_buttons = [b for b in buttons if b['has_custom']]
    other_buttons = [b for b in buttons if not b['has_custom']]
    
    if custom_buttons:
        keyboard.append([{"text": "🌟 دکمه‌های با تنظیمات اختصاصی:"}])
        for btn in custom_buttons:
            cat = get_category_by_id(btn['category_id'])
            cat_name = cat['name'] if cat else 'نامشخص'
            icon = "📂" if btn.get('is_submenu') else "🔘"
            keyboard.append([
                {"text": f"{icon} {btn['name']} ({cat_name}) - {btn['effective']} ستون",
                 "callback_data": f"admin_col_btn_edit_{btn['id']}"}
            ])
    
    if other_buttons and len(other_buttons) <= 10:
        keyboard.append([{"text": "📌 دکمه‌های بدون تنظیمات اختصاصی:"}])
        for btn in other_buttons[:5]:  # نمایش فقط ۵ مورد اول
            cat = get_category_by_id(btn['category_id'])
            cat_name = cat['name'] if cat else 'نامشخص'
            icon = "📂" if btn.get('is_submenu') else "🔘"
            keyboard.append([
                {"text": f"{icon} {btn['name']} ({cat_name}) - {btn['effective']} ستون (پیش‌فرض)",
                 "callback_data": f"admin_col_btn_edit_{btn['id']}"}
            ])
        if len(other_buttons) > 5:
            keyboard.append([{"text": f"... و {len(other_buttons) - 5} دکمه دیگر", "callback_data": "admin_col_btn_list"}])
    
    if not custom_buttons and not other_buttons:
        keyboard.append([{"text": "❌ هیچ دکمه‌ای یافت نشد", "callback_data": "admin_none"}])
    
    keyboard.append([
        {"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_columns"}
    ])
    
    return {"inline_keyboard": keyboard}


def column_button_edit_keyboard(button_id, current_columns, effective, default, category_columns):
    """
    کیبورد ویرایش ستون‌های یک دکمه
    
    پارامترها:
        button_id: شناسه دکمه
        current_columns: ستون‌های فعلی (یا None)
        effective: ستون‌های مؤثر
        default: ستون‌های پیش‌فرض عمومی
        category_columns: ستون‌های دسته‌بندی
    """
    keyboard = []
    
    button = get_button_by_id(button_id)
    button_name = button['name'] if button else 'نامشخص'
    
    keyboard.append([{"text": f"🔘 تنظیم ستون‌های: {button_name}"}])
    
    # گزینه استفاده از پیش‌فرض دسته‌بندی
    selected = "✅ " if current_columns is None else ""
    category_text = f"پیش‌فرض (دسته‌بندی: {category_columns if category_columns else default} ستون)"
    keyboard.append([
        {"text": f"{selected}{category_text}", 
         "callback_data": f"admin_col_btn_set_{button_id}_null"}
    ])
    
    # گزینه‌های انتخاب ستون
    columns_options = [
        (1, "۱ ستون"),
        (2, "۲ ستون"),
        (3, "۳ ستون"),
        (4, "۴ ستون"),
        (5, "۵ ستون"),
        (6, "۶ ستون"),
        (7, "۷ ستون"),
        (8, "۸ ستون")
    ]
    
    for col, label in columns_options:
        selected = "✅ " if col == current_columns else ""
        callback = f"admin_col_btn_set_{button_id}_{col}"
        keyboard.append([
            {"text": f"{selected}{label}", "callback_data": callback}
        ])
    
    keyboard.append([{"text": "─────────────"}])
    
    # اطلاعات
    keyboard.append([{"text": f"📊 مقدار مؤثر: {effective} ستون"}])
    keyboard.append([{"text": f"📌 پیش‌فرض عمومی: {default} ستون"}])
    if category_columns:
        keyboard.append([{"text": f"📂 ستون‌های دسته‌بندی: {category_columns} ستون"}])
    else:
        keyboard.append([{"text": f"📂 دسته‌بندی: از پیش‌فرض عمومی استفاده می‌کند"}])
    
    keyboard.append([{"text": "─────────────"}])
    
    # برگشت
    keyboard.append([
        {"text": "🔙 برگشت به لیست دکمه‌ها", "callback_data": "admin_col_btn_list"},
        {"text": "🏠 برگشت به منوی اصلی", "callback_data": "admin_columns"}
    ])
    
    return {"inline_keyboard": keyboard}


def column_preview_keyboard(category_id, current_columns):
    """
    کیبورد پیش‌نمایش دسته‌بندی با ستون‌های مختلف
    
    پارامترها:
        category_id: شناسه دسته‌بندی
        current_columns: ستون‌های فعلی برای نمایش
    """
    keyboard = []
    
    # گزینه‌های تغییر ستون‌ها برای پیش‌نمایش
    columns_options = [1, 2, 3, 4, 5, 6]
    row = []
    for col in columns_options:
        selected = "✅" if col == current_columns else ""
        row.append({"text": f"{selected}{col}", "callback_data": f"admin_col_preview_{category_id}_{col}"})
        if len(row) == 6:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([{"text": "─────────────"}])
    
    # برگشت
    keyboard.append([
        {"text": "🔙 برگشت به ویرایش دسته‌بندی", "callback_data": f"admin_col_cat_edit_{category_id}"},
        {"text": "🏠 برگشت به منوی اصلی", "callback_data": "admin_columns"}
    ])
    
    return {"inline_keyboard": keyboard}


def column_reset_confirm_keyboard():
    """
    کیبورد تایید بازنشانی همه تنظیمات ستون‌ها
    """
    return {
        "inline_keyboard": [
            [{"text": "⚠️ آیا از بازنشانی همه تنظیمات ستون‌ها مطمئن هستید؟"}],
            [{"text": "⚠️ این عمل غیرقابل بازگشت است!"}],
            [{"text": "✅ بله، بازنشانی شود", "callback_data": "admin_col_reset_confirm"}],
            [{"text": "❌ خیر، انصراف", "callback_data": "admin_columns"}]
        ]
    }


def column_set_quick_keyboard(columns_options=None):
    """
    کیبورد تنظیم سریع ستون‌ها
    
    پارامترها:
        columns_options: لیست گزینه‌های ستون‌ها (پیش‌فرض [1,2,3,4,5,6,7,8])
    """
    if columns_options is None:
        columns_options = [1, 2, 3, 4, 5, 6, 7, 8]
    
    keyboard = []
    row = []
    for col in columns_options:
        row.append({"text": f"{col} ستون", "callback_data": f"admin_col_quick_{col}"})
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([
        {"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_columns"}
    ])
    
    return {"inline_keyboard": keyboard}


def column_status_keyboard(status_data):
    """
    کیبورد نمایش وضعیت ستون‌ها
    
    پارامترها:
        status_data: دیکشنری وضعیت
    """
    keyboard = []
    
    keyboard.append([{"text": f"📊 پیش‌فرض عمومی: {status_data.get('default_columns', 2)} ستون"}])
    keyboard.append([{"text": f"📂 دسته‌بندی‌ها: {status_data.get('total_categories', 0)} عدد"}])
    keyboard.append([{"text": f"  🌟 با تنظیم اختصاصی: {status_data.get('categories_with_custom', 0)} عدد"}])
    keyboard.append([{"text": f"  📌 با پیش‌فرض: {status_data.get('categories_using_default', 0)} عدد"}])
    keyboard.append([{"text": f"🔘 دکمه‌ها: {status_data.get('total_buttons', 0)} عدد"}])
    keyboard.append([{"text": f"  🌟 با تنظیم اختصاصی: {status_data.get('buttons_with_custom', 0)} عدد"}])
    
    keyboard.append([
        {"text": "🔙 برگشت به منوی اصلی", "callback_data": "admin_columns"}
    ])
    
    return {"inline_keyboard": keyboard}


__all__ = [
    'column_management_main_keyboard',
    'column_category_list_keyboard',
    'column_category_edit_keyboard',
    'column_button_list_keyboard',
    'column_button_edit_keyboard',
    'column_preview_keyboard',
    'column_reset_confirm_keyboard',
    'column_set_quick_keyboard',
    'column_status_keyboard',
]