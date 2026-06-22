# admin_panel/btn_create.py
# ایجاد دکمه جدید در پنل ادمین - نسخه اصلاح‌شده (async + logging)
# شامل انتخاب دسته‌بندی از لیست، افزودن دسته‌بندی جدید و پشتیبانی از بازگشت به دسته‌بندی
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states
from database import (
    get_all_buttons,
    get_button_by_id,
    get_category_by_id,
    get_all_categories_admin,
    add_category,
    add_button,
    update_button,
    delete_duplicate_submenus
)
from keyboards import admin_main_keyboard
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error
)


async def handle_create_button_start(chat_id, user_id):
    """شروع فرآیند ایجاد دکمه جدید با نمایش لیست دسته‌بندی‌ها"""
    try:
        categories = get_all_categories_admin()
        keyboard = []
        
        if categories:
            for cat in categories:
                keyboard.append([
                    {"text": f"📂 {cat['name']}", "callback_data": f"admin_loc_cat_{cat['id']}"}
                ])
        else:
            keyboard.append([{"text": "❌ هیچ دسته‌بندی یافت نشد", "callback_data": "admin_none"}])
        
        keyboard.append([
            {"text": "➕ افزودن دسته‌بندی جدید", "callback_data": "admin_loc_add_cat"}
        ])
        keyboard.append([
            {"text": "🔙 برگشت", "callback_data": "admin_back"}
        ])
        
        user_states[user_id] = {"state": "admin_create_button_location"}
        await send_message(chat_id, "➕ **ایجاد دکمه جدید**\n\nلطفاً دسته‌بندی مورد نظر را انتخاب کنید:", {"inline_keyboard": keyboard})
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_create_button_start: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش دسته‌بندی‌ها.")
        return True


async def handle_location_selection(chat_id, user_id, data):
    """پردازش انتخاب دسته‌بندی یا افزودن دسته‌بندی جدید"""
    try:
        # انتخاب دسته‌بندی موجود
        if data.startswith("admin_loc_cat_"):
            try:
                cat_id = int(data.split("_")[-1])
            except ValueError:
                await send_message(chat_id, "❌ شناسه دسته‌بندی نامعتبر.")
                return True
            
            category = get_category_by_id(cat_id)
            if not category:
                await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
                return True
            
            user_states[user_id] = {
                "state": "admin_create_button_name",
                "cat_id": cat_id,
                "from_category": False
            }
            await send_message(chat_id, f"✅ دسته‌بندی «{category['name']}» انتخاب شد.\nلطفاً **نام دکمه** را وارد کنید:")
            return True
        
        # افزودن دسته‌بندی جدید
        elif data == "admin_loc_add_cat":
            user_states[user_id] = {"state": "admin_add_category_name"}
            await send_message(chat_id, "➕ **افزودن دسته‌بندی جدید**\nلطفاً نام دسته‌بندی جدید را وارد کنید:")
            return True
        
        return False
    except Exception as e:
        log_callback_error(
            f"Error in handle_location_selection: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب دسته‌بندی.")
        return True


async def handle_category_location(chat_id, user_id, data):
    """
    پردازش انتخاب مکان برای دسته‌بندی جدید (admin_cat_loc_*)
    بعد از دریافت نام دسته‌بندی، این تابع فراخوانی می‌شود
    """
    try:
        loc_map = {
            "admin_cat_loc_main": "main",
            "admin_cat_loc_more": "more",
            "admin_cat_loc_other": "other"
        }
        location = loc_map.get(data)
        if not location:
            await send_message(chat_id, "❌ مکان نامعتبر.")
            return True
        
        cat_name = user_states[user_id].get("temp_category_name")
        if not cat_name:
            await send_message(chat_id, "❌ خطا: نام دسته‌بندی یافت نشد.")
            user_states[user_id] = {"state": "main"}
            return True
        
        # ایجاد دسته‌بندی با location انتخاب‌شده
        cat_id = add_category(cat_name, location=location)
        user_states[user_id].pop("temp_category_name", None)
        user_states[user_id]["state"] = "main"
        
        await send_message(chat_id, f"✅ دسته‌بندی «{cat_name}» در منوی «{location}» ایجاد شد.")
        
        # بازگشت به لیست دسته‌بندی‌ها
        from .btn_manage import handle_show_categories
        await handle_show_categories(chat_id)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_category_location: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ایجاد دسته‌بندی.")
        return True


async def handle_parent_selection(chat_id, user_id, data):
    """پردازش انتخاب والد برای زیرمنو (admin_parent_*) - استفاده از همان دسته‌بندی والد"""
    try:
        parent_id = int(data.split("_")[2])
        parent_btn = get_button_by_id(parent_id)
        if parent_btn:
            cat_id = parent_btn['category_id']
            user_states[user_id] = {
                "state": "admin_create_button_name",
                "cat_id": cat_id,
                "parent_button_id": parent_id,
                "from_category": False
            }
            await send_message(chat_id, f"✅ دکمه والد «{parent_btn['name']}» انتخاب شد.\nلطفاً **نام زیرمنو** را وارد کنید:")
        else:
            await send_message(chat_id, "❌ دکمه والد یافت نشد.")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_parent_selection: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب والد.")
        return True


async def handle_has_submenu(chat_id, user_id, data):
    """پردازش پاسخ به داشتن زیرمنو (admin_has_submenu_*)"""
    try:
        if data == "admin_has_submenu_yes":
            btn_id = user_states.get(user_id, {}).get("btn_id")
            if not btn_id:
                await send_message(chat_id, "❌ خطا: شناسه دکمه یافت نشد. لطفاً دوباره از ابتدا ایجاد کنید.")
                user_states[user_id] = {"state": "main"}
                return True
            
            update_button(btn_id, has_submenu=1)
            user_states[user_id]["state"] = "admin_create_submenu_name"
            user_states[user_id]["submenu_list"] = []
            await send_message(chat_id, "✅ دکمه دارای زیرمنو است.\nلطفاً **نام زیرمنو** را وارد کنید (برای پایان، کلمه 'پایان' را بفرستید):")
            return True
        
        if data == "admin_has_submenu_no":
            btn_id = user_states.get(user_id, {}).get("btn_id")
            if not btn_id:
                await send_message(chat_id, "❌ خطا: شناسه دکمه یافت نشد. لطفاً دوباره از ابتدا ایجاد کنید.")
                user_states[user_id] = {"state": "main"}
                return True
            
            update_button(btn_id, has_submenu=0)
            delete_duplicate_submenus(btn_id)
            
            cat_id_for_back = user_states[user_id].get("cat_id_for_back")
            user_states[user_id].pop("cat_id_for_back", None)
            user_states[user_id]["state"] = "main"
            
            if cat_id_for_back:
                from .cb_routes import handle_admin_callback
                await handle_admin_callback({
                    "callback_query": {
                        "data": f"admin_cat_{cat_id_for_back}",
                        "from": {"id": user_id},
                        "message": {"chat": {"id": chat_id}}
                    }
                })
            else:
                btn = get_button_by_id(btn_id)
                cat_id = btn['category_id'] if btn else None
                if cat_id:
                    from .cb_routes import handle_admin_callback
                    await handle_admin_callback({
                        "callback_query": {
                            "data": f"admin_cat_{cat_id}",
                            "from": {"id": user_id},
                            "message": {"chat": {"id": chat_id}}
                        }
                    })
                else:
                    await send_message(chat_id, f"✅ دکمه با موفقیت ایجاد شد.", admin_main_keyboard())
            return True
        
        return False
    except Exception as e:
        log_callback_error(
            f"Error in handle_has_submenu: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در ایجاد دکمه: {str(e)}")
        return True


async def handle_add_button_in_category(chat_id, user_id, data):
    """
    شروع فرآیند افزودن دکمه جدید در یک دسته‌بندی خاص (از صفحه مدیریت دکمه‌ها)
    کالبک: admin_add_btn_in_cat_<category_id>
    """
    try:
        category_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه دسته‌بندی نامعتبر.")
        return True
    
    try:
        category = get_category_by_id(category_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        user_states[user_id] = {
            "state": "admin_create_button_name",
            "cat_id": category_id,
            "parent_button_id": None,
            "from_category": True
        }
        
        await send_message(chat_id, f"➕ **افزودن دکمه جدید در دسته‌بندی {category['name']}**\nلطفاً **نام دکمه** را وارد کنید:")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_add_button_in_category: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع افزودن دکمه.")
        return True