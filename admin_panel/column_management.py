# admin_panel/column_management.py
# مدیریت پیشرفته ستون‌های منو - شامل توابع اصلی برای مدیریت ستون‌ها در سه سطح
# سطوح: ۱- عمومی (پیش‌فرض), ۲- دسته‌بندی, ۳- دکمه

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states
from database import (
    get_db_connection,
    get_all_categories_admin,
    get_category_by_id,
    get_button_by_id,
    get_all_buttons,
    get_default_menu_columns,
    get_category_columns,
    get_button_columns,
    get_effective_columns,
    set_default_menu_columns,
    set_category_columns,
    set_button_columns,
    update_category,
    update_button,
    get_buttons_by_category,
    get_buttons_by_parent,
)
from keyboards import main_menu_keyboard, more_menu_keyboard, other_services_keyboard
from keyboards.kb_column_preview import (
    column_management_main_keyboard,
    column_category_list_keyboard,
    column_category_edit_keyboard,
    column_button_list_keyboard,
    column_button_edit_keyboard,
    column_preview_keyboard,
    column_reset_confirm_keyboard,
    column_set_quick_keyboard,
)
from utils.error_handler import (
    log_callback_error,
    log_database_error,
    log_general_error
)
import json


# ==================== توابع اصلی مدیریت ستون‌ها ====================

async def handle_column_management(chat_id, user_id):
    """
    نمایش منوی اصلی مدیریت ستون‌ها
    """
    try:
        default_columns = get_default_menu_columns()
        
        # دریافت وضعیت ستون‌های دسته‌بندی‌ها
        categories = get_all_categories_admin()
        category_status = []
        for cat in categories:
            cat_columns = get_category_columns(cat['id'])
            effective = get_effective_columns(category_id=cat['id'])
            category_status.append({
                'id': cat['id'],
                'name': cat['name'],
                'location': cat.get('location', 'main'),
                'custom': cat_columns,
                'effective': effective,
                'has_custom': cat_columns is not None
            })
        
        # دریافت دکمه‌هایی که تنظیمات اختصاصی دارند
        all_buttons = get_all_buttons()
        buttons_with_custom = []
        for btn in all_buttons:
            btn_columns = get_button_columns(btn['id'])
            if btn_columns is not None:
                buttons_with_custom.append({
                    'id': btn['id'],
                    'name': btn['name'],
                    'category_id': btn['category_id'],
                    'columns': btn_columns
                })
        
        msg = f"📊 **مدیریت پیشرفته ستون‌های منو**\n\n"
        msg += f"🔧 **تنظیمات پیش‌فرض عمومی:** {default_columns} ستون\n\n"
        
        msg += f"📂 **وضعیت دسته‌بندی‌ها:**\n"
        for cat in category_status:
            custom_text = f"✅ {cat['custom']} ستون" if cat['has_custom'] else "❌ پیش‌فرض"
            effective_icon = "🌟" if cat['has_custom'] else "📌"
            msg += f"  {effective_icon} {cat['name']}: {cat['effective']} ستون (اختصاصی: {custom_text})\n"
        
        if buttons_with_custom:
            msg += f"\n🔘 **دکمه‌های با تنظیمات اختصاصی:** {len(buttons_with_custom)} عدد\n"
            for btn in buttons_with_custom[:5]:  # نمایش فقط ۵ مورد اول
                cat = get_category_by_id(btn['category_id'])
                cat_name = cat['name'] if cat else 'نامشخص'
                msg += f"  • {btn['name']} ({cat_name}): {btn['columns']} ستون\n"
            if len(buttons_with_custom) > 5:
                msg += f"  ... و {len(buttons_with_custom) - 5} مورد دیگر\n"
        
        keyboard = column_management_main_keyboard(default_columns, category_status, buttons_with_custom)
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_management: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش مدیریت ستون‌ها.")
        return True


async def handle_column_category_list(chat_id, user_id):
    """
    نمایش لیست دسته‌بندی‌ها برای مدیریت ستون‌ها
    """
    try:
        categories = get_all_categories_admin()
        
        category_data = []
        for cat in categories:
            cat_columns = get_category_columns(cat['id'])
            effective = get_effective_columns(category_id=cat['id'])
            category_data.append({
                'id': cat['id'],
                'name': cat['name'],
                'location': cat.get('location', 'main'),
                'custom': cat_columns,
                'effective': effective,
                'has_custom': cat_columns is not None
            })
        
        keyboard = column_category_list_keyboard(category_data)
        await send_message(chat_id, "📂 **مدیریت ستون‌های دسته‌بندی‌ها**\n\nبرای ویرایش هر دسته‌بندی کلیک کنید:", keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_category_list: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست دسته‌بندی‌ها.")
        return True


async def handle_column_category_edit(chat_id, user_id, data):
    """
    نمایش صفحه ویرایش ستون‌های یک دسته‌بندی
    """
    try:
        category_id = int(data.split("_")[-1])
        category = get_category_by_id(category_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        current_columns = get_category_columns(category_id)
        effective = get_effective_columns(category_id=category_id)
        default = get_default_menu_columns()
        
        # دریافت دکمه‌های این دسته‌بندی
        buttons = get_buttons_by_category(category_id)
        button_status = []
        for btn in buttons:
            btn_columns = get_button_columns(btn['id'])
            btn_effective = get_effective_columns(button_id=btn['id'], category_id=category_id)
            button_status.append({
                'id': btn['id'],
                'name': btn['name'],
                'custom': btn_columns,
                'effective': btn_effective,
                'has_custom': btn_columns is not None
            })
        
        # دریافت زیرمنوها
        submenus = []
        for btn in buttons:
            subs = get_buttons_by_parent(btn['id'])
            for sub in subs:
                sub_columns = get_button_columns(sub['id'])
                sub_effective = get_effective_columns(button_id=sub['id'], category_id=category_id)
                submenus.append({
                    'id': sub['id'],
                    'name': sub['name'],
                    'parent_name': btn['name'],
                    'custom': sub_columns,
                    'effective': sub_effective,
                    'has_custom': sub_columns is not None
                })
        
        keyboard = column_category_edit_keyboard(category_id, current_columns, effective, default, button_status, submenus)
        
        msg = f"📂 **تنظیم ستون‌های دسته‌بندی: {category['name']}**\n\n"
        msg += f"📍 مکان: {category.get('location', 'main')}\n"
        msg += f"🔧 تنظیمات اختصاصی: {current_columns if current_columns else 'ندارد'}\n"
        msg += f"📊 مقدار مؤثر: {effective} ستون\n"
        msg += f"📌 مقدار پیش‌فرض عمومی: {default} ستون\n\n"
        
        if button_status:
            msg += f"🔘 **وضعیت دکمه‌های این دسته‌بندی:**\n"
            for btn in button_status:
                custom_text = f"✅ {btn['custom']} ستون" if btn['has_custom'] else "❌ پیش‌فرض"
                msg += f"  • {btn['name']}: {btn['effective']} ستون ({custom_text})\n"
        
        if submenus:
            msg += f"\n📋 **زیرمنوهای این دسته‌بندی:**\n"
            for sub in submenus:
                custom_text = f"✅ {sub['custom']} ستون" if sub['has_custom'] else "❌ پیش‌فرض"
                msg += f"  • {sub['parent_name']} > {sub['name']}: {sub['effective']} ستون ({custom_text})\n"
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_category_edit: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ویرایش ستون‌های دسته‌بندی.")
        return True


async def handle_column_category_set(chat_id, user_id, data):
    """
    تنظیم ستون‌های یک دسته‌بندی (admin_col_cat_set_<category_id>_<columns>)
    """
    try:
        parts = data.split("_")
        category_id = int(parts[4])
        columns_str = parts[5]
        
        # بررسی مقدار 'null' برای حذف تنظیمات اختصاصی
        if columns_str == 'null':
            columns = None
        else:
            columns = int(columns_str)
            if columns < 1 or columns > 8:
                await send_message(chat_id, "❌ تعداد ستون‌ها باید بین ۱ تا ۸ باشد.")
                return True
        
        category = get_category_by_id(category_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        # ذخیره در دیتابیس
        set_category_columns(category_id, columns)
        
        if columns is None:
            await send_message(chat_id, f"✅ تنظیمات اختصاصی دسته‌بندی «{category['name']}» حذف شد. (از مقدار پیش‌فرض استفاده می‌شود)")
        else:
            await send_message(chat_id, f"✅ تعداد ستون‌های دسته‌بندی «{category['name']}» به {columns} تغییر یافت.")
        
        # بازگشت به صفحه ویرایش
        return await handle_column_category_edit(chat_id, user_id, f"admin_col_cat_edit_{category_id}")
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_category_set: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم ستون‌های دسته‌بندی.")
        return True


async def handle_column_button_list(chat_id, user_id):
    """
    نمایش لیست دکمه‌ها برای مدیریت ستون‌ها
    """
    try:
        buttons = get_all_buttons()
        
        button_data = []
        for btn in buttons:
            btn_columns = get_button_columns(btn['id'])
            effective = get_effective_columns(button_id=btn['id'], category_id=btn['category_id'])
            button_data.append({
                'id': btn['id'],
                'name': btn['name'],
                'category_id': btn['category_id'],
                'custom': btn_columns,
                'effective': effective,
                'has_custom': btn_columns is not None,
                'is_submenu': btn.get('parent_button_id') is not None
            })
        
        keyboard = column_button_list_keyboard(button_data)
        await send_message(chat_id, "🔘 **مدیریت ستون‌های دکمه‌ها**\n\nبرای ویرایش هر دکمه کلیک کنید:", keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_button_list: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست دکمه‌ها.")
        return True


async def handle_column_button_edit(chat_id, user_id, data):
    """
    نمایش صفحه ویرایش ستون‌های یک دکمه
    """
    try:
        button_id = int(data.split("_")[-1])
        button = get_button_by_id(button_id)
        if not button:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        current_columns = get_button_columns(button_id)
        effective = get_effective_columns(button_id=button_id, category_id=button['category_id'])
        default = get_default_menu_columns()
        category_columns = get_category_columns(button['category_id'])
        
        category = get_category_by_id(button['category_id'])
        category_name = category['name'] if category else 'نامشخص'
        
        keyboard = column_button_edit_keyboard(button_id, current_columns, effective, default, category_columns)
        
        msg = f"🔘 **تنظیم ستون‌های دکمه: {button['name']}**\n\n"
        msg += f"📂 دسته‌بندی: {category_name}\n"
        msg += f"🔧 تنظیمات اختصاصی: {current_columns if current_columns else 'ندارد'}\n"
        msg += f"📊 مقدار مؤثر: {effective} ستون\n"
        msg += f"📌 ستون‌های دسته‌بندی: {category_columns if category_columns else 'پیش‌فرض'}\n"
        msg += f"📌 مقدار پیش‌فرض عمومی: {default} ستون\n"
        
        if button.get('parent_button_id'):
            parent = get_button_by_id(button['parent_button_id'])
            if parent:
                msg += f"🔗 زیرمنوی: {parent['name']}\n"
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_button_edit: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ویرایش ستون‌های دکمه.")
        return True


async def handle_column_button_set(chat_id, user_id, data):
    """
    تنظیم ستون‌های یک دکمه (admin_col_btn_set_<button_id>_<columns>)
    """
    try:
        parts = data.split("_")
        button_id = int(parts[4])
        columns_str = parts[5]
        
        # بررسی مقدار 'null' برای حذف تنظیمات اختصاصی
        if columns_str == 'null':
            columns = None
        else:
            columns = int(columns_str)
            if columns < 1 or columns > 8:
                await send_message(chat_id, "❌ تعداد ستون‌ها باید بین ۱ تا ۸ باشد.")
                return True
        
        button = get_button_by_id(button_id)
        if not button:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        # ذخیره در دیتابیس
        set_button_columns(button_id, columns)
        
        if columns is None:
            await send_message(chat_id, f"✅ تنظیمات اختصاصی دکمه «{button['name']}» حذف شد. (از تنظیمات دسته‌بندی استفاده می‌شود)")
        else:
            await send_message(chat_id, f"✅ تعداد ستون‌های دکمه «{button['name']}» به {columns} تغییر یافت.")
        
        # بازگشت به صفحه ویرایش
        return await handle_column_button_edit(chat_id, user_id, f"admin_col_btn_edit_{button_id}")
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_button_set: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم ستون‌های دکمه.")
        return True


async def handle_column_preview(chat_id, user_id, data):
    """
    نمایش پیش‌نمایش یک دسته‌بندی با تعداد ستون‌های مختلف
    """
    try:
        parts = data.split("_")
        category_id = int(parts[3])
        columns = int(parts[4]) if len(parts) > 4 else None
        
        category = get_category_by_id(category_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        # دریافت دکمه‌های دسته‌بندی
        buttons = get_buttons_by_category(category_id)
        if not buttons:
            await send_message(chat_id, "❌ این دسته‌بندی هیچ دکمه‌ای ندارد.")
            return True
        
        # ساخت پیش‌نمایش
        preview_items = []
        for btn in buttons:
            icon = "📂" if btn.get('has_submenu', 0) == 1 else "🔘"
            preview_items.append(f"{icon} {btn['name']}")
        
        # تعیین تعداد ستون‌های نمایش
        display_columns = columns if columns else get_effective_columns(category_id=category_id)
        if display_columns < 1 or display_columns > 8:
            display_columns = 2
        
        # ساخت جدول پیش‌نمایش
        preview_msg = f"📊 **پیش‌نمایش دسته‌بندی: {category['name']}**\n\n"
        preview_msg += f"تعداد ستون‌ها: {display_columns}\n"
        preview_msg += f"تعداد دکمه‌ها: {len(preview_items)}\n\n"
        
        # نمایش دکمه‌ها در ردیف‌های مشخص
        preview_msg += "```\n"
        row = []
        for i, item in enumerate(preview_items, 1):
            row.append(item)
            if i % display_columns == 0:
                preview_msg += " | ".join(row) + "\n"
                row = []
        if row:
            preview_msg += " | ".join(row) + "\n"
        preview_msg += "```\n"
        
        preview_msg += "\n📌 **راهنما:**\n"
        preview_msg += "🔘 = دکمه ساده | 📂 = دکمه دارای زیرمنو\n\n"
        preview_msg += "برای مشاهده با ستون‌های مختلف، از دکمه‌های زیر استفاده کنید:"
        
        keyboard = column_preview_keyboard(category_id, display_columns)
        await send_message(chat_id, preview_msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_preview: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش پیش‌نمایش.")
        return True


async def handle_column_quick_set(chat_id, user_id, data):
    """
    تنظیم سریع ستون‌ها با یک کلیک (admin_col_quick_<columns>)
    """
    try:
        columns = int(data.split("_")[-1])
        if columns < 1 or columns > 8:
            await send_message(chat_id, "❌ تعداد ستون‌ها باید بین ۱ تا ۸ باشد.")
            return True
        
        # تنظیم پیش‌فرض عمومی
        set_default_menu_columns(columns)
        
        # همچنین تمام دسته‌بندی‌هایی که تنظیمات اختصاصی ندارند، از مقدار جدید استفاده می‌کنند
        # اما دسته‌بندی‌های با تنظیمات اختصاصی، تغییر نمی‌کنند
        
        await send_message(
            chat_id, 
            f"✅ تنظیمات سریع اعمال شد.\n\n"
            f"📊 تعداد ستون‌های پیش‌فرض به {columns} تغییر یافت.\n\n"
            f"📌 دسته‌بندی‌هایی که تنظیمات اختصاصی دارند، تغییری نمی‌کنند.\n"
            f"برای تغییر دسته‌بندی‌های خاص، از بخش «مدیریت دسته‌بندی‌ها» استفاده کنید."
        )
        
        # بازگشت به منوی اصلی مدیریت ستون‌ها
        return await handle_column_management(chat_id, user_id)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_quick_set: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم سریع.")
        return True


async def handle_column_reset(chat_id, user_id):
    """
    نمایش تاییدیه بازنشانی همه تنظیمات ستون‌ها
    """
    try:
        keyboard = column_reset_confirm_keyboard()
        await send_message(
            chat_id,
            "🔄 **بازنشانی همه تنظیمات ستون‌ها**\n\n"
            "⚠️ **هشدار!**\n"
            "این عملیات:\n"
            "• تنظیمات پیش‌فرض عمومی را به ۲ ستون بازنشانی می‌کند\n"
            "• تمام تنظیمات اختصاصی دسته‌بندی‌ها را حذف می‌کند\n"
            "• تمام تنظیمات اختصاصی دکمه‌ها را حذف می‌کند\n\n"
            "آیا مطمئن هستید؟",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_reset: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش تاییدیه بازنشانی.")
        return True


async def handle_column_reset_confirm(chat_id, user_id):
    """
    اجرای بازنشانی همه تنظیمات ستون‌ها
    """
    try:
        # ۱. بازنشانی پیش‌فرض عمومی به ۲
        set_default_menu_columns(2)
        
        # ۲. حذف تنظیمات اختصاصی همه دسته‌بندی‌ها
        categories = get_all_categories_admin()
        for cat in categories:
            set_category_columns(cat['id'], None)
        
        # ۳. حذف تنظیمات اختصاصی همه دکمه‌ها
        buttons = get_all_buttons()
        for btn in buttons:
            set_button_columns(btn['id'], None)
        
        await send_message(
            chat_id,
            "✅ همه تنظیمات ستون‌ها به حالت پیش‌فرض بازنشانی شدند.\n\n"
            "📊 تعداد ستون‌های پیش‌فرض: ۲\n"
            "📌 همه دسته‌بندی‌ها و دکمه‌ها از مقدار پیش‌فرض استفاده می‌کنند."
        )
        
        # بازگشت به منوی اصلی
        return await handle_column_management(chat_id, user_id)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_reset_confirm: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در بازنشانی تنظیمات.")
        return True


async def handle_column_set_default(chat_id, user_id, data):
    """
    تنظیم مستقیم پیش‌فرض عمومی (admin_col_set_default_<columns>)
    """
    try:
        columns = int(data.split("_")[-1])
        if columns < 1 or columns > 8:
            await send_message(chat_id, "❌ تعداد ستون‌ها باید بین ۱ تا ۸ باشد.")
            return True
        
        set_default_menu_columns(columns)
        
        await send_message(
            chat_id,
            f"✅ تعداد ستون‌های پیش‌فرض عمومی به {columns} تغییر یافت.\n\n"
            f"📌 این مقدار برای دسته‌بندی‌ها و دکمه‌هایی که تنظیمات اختصاصی ندارند، استفاده می‌شود."
        )
        
        # بازگشت به منوی اصلی
        return await handle_column_management(chat_id, user_id)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_column_set_default: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم پیش‌فرض عمومی.")
        return True


def get_column_status_summary():
    """
    دریافت خلاصه وضعیت ستون‌ها برای نمایش در داشبورد
    """
    try:
        default_columns = get_default_menu_columns()
        categories = get_all_categories_admin()
        
        total_categories = len(categories)
        categories_with_custom = 0
        categories_using_default = 0
        
        for cat in categories:
            if get_category_columns(cat['id']) is not None:
                categories_with_custom += 1
            else:
                categories_using_default += 1
        
        buttons = get_all_buttons()
        buttons_with_custom = 0
        for btn in buttons:
            if get_button_columns(btn['id']) is not None:
                buttons_with_custom += 1
        
        return {
            'default_columns': default_columns,
            'total_categories': total_categories,
            'categories_with_custom': categories_with_custom,
            'categories_using_default': categories_using_default,
            'buttons_with_custom': buttons_with_custom,
            'total_buttons': len(buttons)
        }
        
    except Exception as e:
        log_general_error(  # ✅ جایگزینی logger.error با log_general_error + traceback کامل
            f"Error in get_column_status_summary: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {
            'default_columns': 2,
            'total_categories': 0,
            'categories_with_custom': 0,
            'categories_using_default': 0,
            'buttons_with_custom': 0,
            'total_buttons': 0
        }


__all__ = [
    'handle_column_management',
    'handle_column_category_list',
    'handle_column_category_edit',
    'handle_column_category_set',
    'handle_column_button_list',
    'handle_column_button_edit',
    'handle_column_button_set',
    'handle_column_preview',
    'handle_column_quick_set',
    'handle_column_reset',
    'handle_column_reset_confirm',
    'handle_column_set_default',
    'get_column_status_summary',
]