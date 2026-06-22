# admin_panel/btn_routes.py
# ثبت روت‌های مربوط به مدیریت دکمه‌ها و دسته‌بندی‌ها در پنل مدیریت
# شامل: ایجاد دکمه، مدیریت دسته‌بندی‌ها، ویرایش دکمه، تغییر ترتیب، انتقال و تنظیم ستون‌ها
# همچنین قیمت متغیر و مدیریت پیشرفته ستون‌ها

from .router import route, extract_params
from core import send_message, user_states
from .btn_create import (
    handle_create_button_start,
    handle_location_selection,
    handle_parent_selection,
    handle_has_submenu,
    handle_add_button_in_category,
    handle_category_location,
)
from .btn_manage import (
    handle_show_categories,
    handle_show_category_buttons,
    handle_show_submenu,
    handle_button_detail,
    handle_button_edit,
    handle_button_price,
    handle_button_payment_status,
    handle_button_active_status,
    handle_button_delete,
    handle_submenu_manage,
    handle_submenu_add,
    handle_category_edit,
    handle_category_delete_confirm,
    handle_category_delete,
    handle_button_up,
    handle_button_down,
    handle_button_move_start,
    handle_button_move_select,
    handle_button_set_columns,
    handle_button_set_columns_select,
    handle_category_set_columns,
    handle_category_set_columns_select,
    handle_button_price_type,
    handle_button_price_type_set,
    handle_button_set_min_price,
    handle_button_set_max_price,
    handle_category_price,
)


# ========== روت‌های مدیریت دکمه‌ها و دسته‌بندی‌ها ==========

@route("admin_buttons")
async def admin_buttons(update):
    """نمایش لیست دسته‌بندی‌ها (سطح اول)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_show_categories(chat_id)


@route("admin_cat_")
async def admin_cat(update):
    """نمایش دکمه‌های یک دسته‌بندی خاص"""
    chat_id, user_id, data = extract_params(update)
    return await handle_show_category_buttons(chat_id, user_id, data)


@route("admin_sub_")
async def admin_sub(update):
    """نمایش زیرمنوهای یک دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_show_submenu(chat_id, user_id, data)


@route("admin_btn_")
async def admin_btn(update):
    """نمایش جزئیات یک دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_detail(chat_id, user_id, data)


@route("admin_create_button")
async def admin_create_button(update):
    """شروع فرآیند ایجاد دکمه جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_create_button_start(chat_id, user_id)


@route("admin_loc_")
async def admin_location(update):
    """پردازش انتخاب دسته‌بندی یا افزودن دسته‌بندی جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_location_selection(chat_id, user_id, data)


@route("admin_parent_")
async def admin_parent(update):
    """پردازش انتخاب والد برای زیرمنو"""
    chat_id, user_id, data = extract_params(update)
    return await handle_parent_selection(chat_id, user_id, data)


@route("admin_has_submenu_")
async def admin_has_submenu(update):
    """پاسخ به داشتن زیرمنو"""
    chat_id, user_id, data = extract_params(update)
    return await handle_has_submenu(chat_id, user_id, data)


@route("admin_add_category")
async def admin_add_category(update):
    """شروع فرآیند افزودن دسته‌بندی جدید"""
    chat_id, user_id, data = extract_params(update)
    user_states[user_id] = {"state": "admin_add_category_name"}
    await send_message(chat_id, "➕ **افزودن دسته‌بندی جدید**\nلطفاً نام دسته‌بندی را وارد کنید:")
    return True


@route("admin_cat_loc_")
async def admin_cat_location(update):
    """پردازش انتخاب مکان برای دسته‌بندی جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_category_location(chat_id, user_id, data)


@route("admin_cat_edit_")
async def admin_cat_edit(update):
    """شروع ویرایش نام دسته‌بندی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_category_edit(chat_id, user_id, data)


@route("admin_cat_del_confirm_")
async def admin_cat_del_confirm(update):
    """نمایش تاییدیه حذف دسته‌بندی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_category_delete_confirm(chat_id, user_id, data)


@route("admin_cat_del_yes_")
async def admin_cat_del_yes(update):
    """اجرای حذف دسته‌بندی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_category_delete(chat_id, user_id, data)


@route("admin_add_btn_in_cat_")
async def admin_add_btn_in_cat(update):
    """شروع افزودن دکمه جدید در یک دسته‌بندی خاص"""
    chat_id, user_id, data = extract_params(update)
    return await handle_add_button_in_category(chat_id, user_id, data)


@route("admin_btn_edit_")
async def admin_btn_edit(update):
    """شروع ویرایش نام دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_edit(chat_id, user_id, data)


@route("admin_btn_price_")
async def admin_btn_price(update):
    """شروع تنظیم قیمت دکمه (ثابت یا متغیر)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_price(chat_id, user_id, data)


@route("admin_btn_payment_")
async def admin_btn_payment(update):
    """تغییر وضعیت پرداخت دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_payment_status(chat_id, user_id, data)


@route("admin_btn_status_")
async def admin_btn_status(update):
    """تغییر وضعیت فعال/غیرفعال دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_active_status(chat_id, user_id, data)


@route("admin_btn_del_")
async def admin_btn_del(update):
    """حذف دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_delete(chat_id, user_id, data)


@route("admin_sub_manage_")
async def admin_sub_manage(update):
    """نمایش زیرمنوهای یک دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_submenu_manage(chat_id, user_id, data)


@route("admin_sub_add_")
async def admin_sub_add(update):
    """شروع افزودن زیرمنو جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_submenu_add(chat_id, user_id, data)


# ========== روت‌های جدید مدیریت دکمه‌ها (تغییر ترتیب و انتقال) ==========

@route("admin_btn_up_")
async def admin_btn_up(update):
    """انتقال دکمه یک ردیف بالا"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_up(chat_id, user_id, data)


@route("admin_btn_down_")
async def admin_btn_down(update):
    """انتقال دکمه یک ردیف پایین"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_down(chat_id, user_id, data)


@route("admin_btn_move_")
async def admin_btn_move(update):
    """شروع انتقال دکمه به دسته‌بندی دیگر"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_move_start(chat_id, user_id, data)


@route("admin_btn_move_select_")
async def admin_btn_move_select(update):
    """انتخاب دسته‌بندی مقصد و اجرای انتقال"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_move_select(chat_id, user_id, data)


# ========== روت‌های مدیریت ستون‌ها (ساده) ==========

@route("admin_btn_set_columns_")
async def admin_btn_set_columns(update):
    """نمایش کیبورد انتخاب تعداد ستون‌ها برای یک دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_set_columns(chat_id, user_id, data)


@route("admin_btn_set_columns_select_")
async def admin_btn_set_columns_select(update):
    """ذخیره تعداد ستون‌های انتخاب‌شده برای دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_set_columns_select(chat_id, user_id, data)


@route("admin_cat_set_columns_")
async def admin_cat_set_columns(update):
    """نمایش کیبورد انتخاب تعداد ستون‌ها برای یک دسته‌بندی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_category_set_columns(chat_id, user_id, data)


@route("admin_cat_set_columns_select_")
async def admin_cat_set_columns_select(update):
    """ذخیره تعداد ستون‌های انتخاب‌شده برای دسته‌بندی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_category_set_columns_select(chat_id, user_id, data)


# ========== روت‌های مدیریت قیمت متغیر ==========

@route("admin_btn_price_type_")
async def admin_btn_price_type(update):
    """تغییر نوع قیمت دکمه (admin_btn_price_type_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_price_type(chat_id, user_id, data)


@route("admin_btn_price_type_set_")
async def admin_btn_price_type_set(update):
    """اعمال نوع قیمت جدید (admin_btn_price_type_set_<button_id>_<type>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_button_price_type_set(chat_id, user_id, data)


@route("admin_btn_set_min_price_")
async def admin_btn_set_min_price(update):
    """تنظیم حداقل مبلغ قیمت متغیر (admin_btn_set_min_price_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        btn_id = int(data.split("_")[-1])
        user_states[user_id] = {"state": "admin_btn_set_min_price", "btn_id": btn_id}
        await send_message(
            chat_id,
            f"💰 **تنظیم حداقل مبلغ برای قیمت متغیر**\n\n"
            f"لطفاً حداقل مبلغ را به ریال وارد کنید (فقط عدد):\n\n"
            f"برای انصراف، /cancel را ارسال کنید."
        )
        return True
    except ValueError:
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True


@route("admin_btn_set_max_price_")
async def admin_btn_set_max_price(update):
    """تنظیم حداکثر مبلغ قیمت متغیر (admin_btn_set_max_price_<button_id>)"""
    chat_id, user_id, data = extract_params(update)
    try:
        btn_id = int(data.split("_")[-1])
        user_states[user_id] = {"state": "admin_btn_set_max_price", "btn_id": btn_id}
        await send_message(
            chat_id,
            f"💰 **تنظیم حداکثر مبلغ برای قیمت متغیر**\n\n"
            f"لطفاً حداکثر مبلغ را به ریال وارد کنید (فقط عدد):\n\n"
            f"برای انصراف، /cancel را ارسال کنید."
        )
        return True
    except ValueError:
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True


@route("admin_cat_price_")
async def admin_cat_price(update):
    """مدیریت قیمت‌های متغیر دکمه‌های یک دسته‌بندی (admin_cat_price_<category_id>)"""
    chat_id, user_id, data = extract_params(update)
    return await handle_category_price(chat_id, user_id, data)


# ========== صادر کردن ==========

__all__ = [
    # روت‌های اصلی
    'admin_buttons',
    'admin_cat',
    'admin_sub',
    'admin_btn',
    'admin_create_button',
    'admin_location',
    'admin_parent',
    'admin_has_submenu',
    'admin_add_category',
    'admin_cat_location',
    'admin_cat_edit',
    'admin_cat_del_confirm',
    'admin_cat_del_yes',
    'admin_add_btn_in_cat',
    'admin_btn_edit',
    'admin_btn_price',
    'admin_btn_payment',
    'admin_btn_status',
    'admin_btn_del',
    'admin_sub_manage',
    'admin_sub_add',
    
    # تغییر ترتیب و انتقال
    'admin_btn_up',
    'admin_btn_down',
    'admin_btn_move',
    'admin_btn_move_select',
    
    # مدیریت ستون‌ها
    'admin_btn_set_columns',
    'admin_btn_set_columns_select',
    'admin_cat_set_columns',
    'admin_cat_set_columns_select',
    
    # قیمت متغیر
    'admin_btn_price_type',
    'admin_btn_price_type_set',
    'admin_btn_set_min_price',
    'admin_btn_set_max_price',
    'admin_cat_price',
]