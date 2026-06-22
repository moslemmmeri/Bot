# admin_panel/btn_manage.py
# مدیریت دکمه‌ها، زیرمنوها و دسته‌بندی‌ها در پنل ادمین - نسخه کامل با قابلیت‌های جدید
# شامل: تغییر ترتیب (Sort Order)، انتقال دکمه به دسته‌بندی دیگر، نمایش ساختار درختی
# مدیریت ستون‌ها (تعداد ستون‌های منو) و پشتیبانی از قیمت متغیر
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states, get_admin_title
from database import (
    get_db_connection,
    get_all_categories_admin,
    get_category_by_id,
    get_buttons_by_category_for_admin,
    get_buttons_by_parent,
    get_button_by_id,
    get_all_buttons,
    update_button,
    delete_button,
    update_category,
    delete_category,
    add_category,
    get_buttons_by_category,
    get_effective_columns,
    get_button_price_info,
    update_button_price,
)
from keyboards import (
    admin_main_keyboard,
    admin_categories_keyboard,
    admin_category_buttons_keyboard,
    admin_submenu_list_keyboard,
    admin_submenu_keyboard,
    admin_category_delete_confirm_keyboard,
    admin_category_columns_keyboard,
    admin_button_columns_keyboard,
)
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error
)


# ==================== توابع کمکی ====================

def _get_category_name(category_id):
    """دریافت نام دسته‌بندی با شناسه"""
    try:
        cat = get_category_by_id(category_id)
        return cat['name'] if cat else f"دسته‌بندی {category_id}"
    except Exception as e:
        log_database_error(
            f"Error in _get_category_name for {category_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return f"دسته‌بندی {category_id}"


def _get_button_name(button_id):
    """دریافت نام دکمه با شناسه"""
    try:
        btn = get_button_by_id(button_id)
        return btn['name'] if btn else f"دکمه {button_id}"
    except Exception as e:
        log_database_error(
            f"Error in _get_button_name for {button_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return f"دکمه {button_id}"


def _swap_sort_order(item_id, direction, table_name, id_field='id'):
    """
    جابجایی sort_order بین دو آیتم در یک جدول.
    direction: 'up' یا 'down'
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT sort_order FROM {table_name} WHERE {id_field} = ?", (item_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            current_order = row['sort_order']
            
            if direction == 'up':
                cursor.execute(f"""
                    SELECT {id_field}, sort_order FROM {table_name} 
                    WHERE sort_order < ? 
                    ORDER BY sort_order DESC 
                    LIMIT 1
                """, (current_order,))
            else:
                cursor.execute(f"""
                    SELECT {id_field}, sort_order FROM {table_name} 
                    WHERE sort_order > ? 
                    ORDER BY sort_order ASC 
                    LIMIT 1
                """, (current_order,))
            
            neighbor = cursor.fetchone()
            if not neighbor:
                return False
            
            cursor.execute(f"""
                UPDATE {table_name} SET sort_order = ? WHERE {id_field} = ?
            """, (neighbor['sort_order'], item_id))
            
            cursor.execute(f"""
                UPDATE {table_name} SET sort_order = ? WHERE {id_field} = ?
            """, (current_order, neighbor[id_field]))
            
            conn.commit()
            logger.info(f"✅ sort_order در جدول {table_name} برای آیتم {item_id} و {neighbor[id_field]} جابجا شد.")
            return True
    except Exception as e:
        log_database_error(
            f"Error in _swap_sort_order for item {item_id} in {table_name}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


def _move_button_to_category(button_id, new_category_id):
    """
    انتقال یک دکمه به دسته‌بندی جدید.
    تمام زیرمنوهای دکمه نیز به همان دسته‌بندی منتقل می‌شوند.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM buttons WHERE id = ?", (button_id,))
            button = cursor.fetchone()
            if not button:
                return False
            
            cursor.execute("SELECT * FROM categories WHERE id = ?", (new_category_id,))
            category = cursor.fetchone()
            if not category:
                return False
            
            cursor.execute("UPDATE buttons SET category_id = ? WHERE id = ?", (new_category_id, button_id))
            cursor.execute("UPDATE buttons SET category_id = ? WHERE parent_button_id = ?", (new_category_id, button_id))
            
            conn.commit()
            logger.info(f"✅ دکمه {button_id} و زیرمنوهای آن به دسته‌بندی {new_category_id} منتقل شدند.")
            return True
    except Exception as e:
        log_database_error(
            f"Error in _move_button_to_category for button {button_id}: {str(e)}",
            traceback=traceback.format_exc()
        )
        return False


# ==================== توابع اصلی ====================

async def handle_show_categories(chat_id):
    """نمایش لیست دسته‌بندی‌ها (سطح اول) با دکمه‌های ویرایش و حذف"""
    try:
        categories = get_all_categories_admin()
        if not categories:
            await send_message(chat_id, "❌ هیچ دسته‌بندی یافت نشد.", admin_main_keyboard())
            return True
        
        keyboard = admin_categories_keyboard(categories)
        await send_message(chat_id, "🔘 **لیست دسته‌بندی‌ها**\nبرای مشاهده دکمه‌ها، ویرایش نام یا حذف دسته‌بندی کلیک کنید:", keyboard)
        return True
    except Exception as e:
        log_general_error(
            f"Error in handle_show_categories: {str(e)}",
            traceback=traceback.format_exc()
        )
        await send_message(chat_id, "❌ خطا در نمایش دسته‌بندی‌ها.")
        return True


async def handle_show_category_buttons(chat_id, user_id, data):
    """نمایش دکمه‌های یک دسته‌بندی خاص (admin_cat_<id>)"""
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
        
        buttons = get_buttons_by_category_for_admin(category_id)
        
        keyboard = admin_category_buttons_keyboard(buttons, category['name'], category_id)
        
        effective_columns = get_effective_columns(category_id=category_id)
        keyboard["inline_keyboard"].append([
            {"text": f"📊 مدیریت ستون‌های این دسته‌بندی (مؤثر: {effective_columns})", 
             "callback_data": f"admin_col_cat_edit_{category_id}"}
        ])
        
        # دکمه تنظیم قیمت متغیر
        keyboard["inline_keyboard"].append([
            {"text": f"💰 مدیریت قیمت‌های متغیر", 
             "callback_data": f"admin_cat_price_{category_id}"}
        ])
        
        await send_message(chat_id, f"🔘 **{category['name']}**\nبرای مشاهده جزئیات هر دکمه کلیک کنید:", keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_show_category_buttons: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش دکمه‌های دسته‌بندی.")
        return True


async def handle_show_submenu(chat_id, user_id, data):
    """نمایش زیرمنوهای یک دکمه (admin_sub_<id>)"""
    try:
        button_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True
    
    try:
        button = get_button_by_id(button_id)
        if not button:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        if button.get('has_submenu', 0) != 1:
            return await handle_button_detail(chat_id, user_id, data)
        
        submenus = get_buttons_by_parent(button_id)
        category_id = button['category_id']
        keyboard = admin_submenu_list_keyboard(submenus, button['name'], button_id, category_id)
        await send_message(chat_id, f"🔽 **زیرمنوهای {button['name']}**\nبرای مشاهده جزئیات هر زیرمنو کلیک کنید:", keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_show_submenu: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش زیرمنوها.")
        return True


async def handle_show_buttons(chat_id):
    """نمایش لیست تمام دکمه‌ها (با ساختار درختی)"""
    try:
        await send_message(chat_id, "🔘 **لیست تمام دکمه‌ها**\nبرای مشاهده جزئیات هر دکمه کلیک کنید:", admin_tree_buttons_keyboard())
        return True
    except Exception as e:
        log_general_error(
            f"Error in handle_show_buttons: {str(e)}",
            traceback=traceback.format_exc()
        )
        await send_message(chat_id, "❌ خطا در نمایش دکمه‌ها.")
        return True


def admin_tree_buttons_keyboard():
    """نمایش تمام دکمه‌ها به همراه زیرمنوها (ساختار درختی) - مخصوص پنل مدیریت"""
    try:
        buttons = get_all_buttons()
        keyboard = []
        
        for btn in buttons:
            submenus = get_buttons_by_parent(btn['id'])
            if submenus:
                keyboard.append([
                    {"text": f"📂 {btn['name']}", 
                     "callback_data": f"admin_btn_{btn['id']}"}
                ])
                for sub in submenus:
                    keyboard.append([
                        {"text": f"  └─ {sub['name']}", 
                         "callback_data": f"admin_btn_{sub['id']}"}
                    ])
            else:
                keyboard.append([
                    {"text": f"📄 {btn['name']}", 
                     "callback_data": f"admin_btn_{btn['id']}"}
                ])
        
        if not buttons:
            keyboard.append([{"text": "❌ هیچ دکمه‌ای یافت نشد", "callback_data": "admin_none"}])
        keyboard.append([{"text": "🔙 برگشت", "callback_data": "admin_back"}])
        return {"inline_keyboard": keyboard}
    except Exception as e:
        log_general_error(
            f"Error in admin_tree_buttons_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری دکمه‌ها", "callback_data": "admin_back"}]]}


async def handle_button_detail(chat_id, user_id, data):
    """نمایش جزئیات یک دکمه خاص (admin_btn_<id>)"""
    try:
        btn_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه دکمه نامعتبر.")
        return True
    
    try:
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        cat = get_category_by_id(btn['category_id'])
        
        effective_columns = get_effective_columns(button_id=btn_id, category_id=btn['category_id'])
        btn_columns = btn.get('columns')
        cat_columns = cat.get('columns') if cat else None
        columns_display = f"{btn_columns if btn_columns is not None else 'پیش‌فرض'}"
        if cat_columns is not None:
            columns_display += f" (دسته‌بندی: {cat_columns})"
        columns_display += f" → مؤثر: {effective_columns}"
        
        # اطلاعات قیمت
        price_info = get_button_price_info(btn_id)
        price_type = price_info.get('price_type', 'fixed')
        price_display = "ثابت" if price_type == 'fixed' else "متغیر"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "✏️ ویرایش نام", "callback_data": f"admin_btn_edit_{btn_id}"}],
                [{"text": "❓ مدیریت سوالات", "callback_data": f"admin_q_manage_{btn_id}"}]
            ]
        }
        
        if btn.get('has_submenu') == 1:
            keyboard["inline_keyboard"].append(
                [{"text": "🔽 مدیریت زیرمنوها", "callback_data": f"admin_sub_manage_{btn_id}"}]
            )
        
        keyboard["inline_keyboard"].append(
            [{"text": "💰 تنظیم مبلغ", "callback_data": f"admin_btn_price_{btn_id}"}]
        )
        
        keyboard["inline_keyboard"].append(
            [{"text": f"💰 نوع قیمت: {price_display}", "callback_data": f"admin_btn_price_type_{btn_id}"}]
        )
        
        payment_status = "فعال" if btn.get('has_payment', 0) == 1 else "غیرفعال"
        keyboard["inline_keyboard"].append(
            [{"text": f"💳 پرداخت: {payment_status}", "callback_data": f"admin_btn_payment_{btn_id}"}]
        )
        
        active_status = "فعال" if btn.get('is_active', 1) == 1 else "غیرفعال"
        keyboard["inline_keyboard"].append(
            [{"text": f"🔘 وضعیت: {active_status}", "callback_data": f"admin_btn_status_{btn_id}"}]
        )
        
        keyboard["inline_keyboard"].append([
            {"text": "⬆️ بالا", "callback_data": f"admin_btn_up_{btn_id}"},
            {"text": "⬇️ پایین", "callback_data": f"admin_btn_down_{btn_id}"},
            {"text": "📂 انتقال به دسته‌بندی", "callback_data": f"admin_btn_move_{btn_id}"}
        ])
        
        keyboard["inline_keyboard"].append([
            {"text": f"📊 تنظیم ستون‌ها: {columns_display}", "callback_data": f"admin_btn_set_columns_{btn_id}"}
        ])
        
        keyboard["inline_keyboard"].append([
            {"text": f"📊 مدیریت پیشرفته ستون‌های این دکمه", 
             "callback_data": f"admin_col_btn_edit_{btn_id}"}
        ])
        
        keyboard["inline_keyboard"].append(
            [{"text": "🗑️ حذف دکمه", "callback_data": f"admin_btn_del_{btn_id}"}]
        )
        
        if btn.get('parent_button_id'):
            keyboard["inline_keyboard"].append(
                [{"text": "🔙 برگشت به زیرمنوها", "callback_data": f"admin_sub_{btn['parent_button_id']}"}]
            )
        else:
            keyboard["inline_keyboard"].append(
                [{"text": "🔙 برگشت به دسته‌بندی", "callback_data": f"admin_cat_{btn['category_id']}"}]
            )
        
        msg = f"🔘 **{btn['name']}**\nشناسه: {btn['id']}\n"
        msg += f"دسته‌بندی: {cat['name'] if cat else 'ندارد'}\n"
        if btn.get('parent_button_id'):
            parent = get_button_by_id(btn['parent_button_id'])
            msg += f"زیرمنوی: {parent['name'] if parent else 'ندارد'}\n"
        msg += f"زیرمنو: {'دارد' if btn['has_submenu'] else 'ندارد'}\n"
        msg += f"پرداخت: {'فعال' if btn['has_payment'] else 'غیرفعال'}\n"
        msg += f"وضعیت: {'فعال' if btn['is_active'] else 'غیرفعال'}\n"
        if btn['has_payment']:
            msg += f"مبلغ: {btn['price_amount']} ریال\n"
            msg += f"نوع قیمت: {price_display}\n"
            if price_type == 'variable':
                min_price = price_info.get('min_price')
                max_price = price_info.get('max_price')
                if min_price:
                    msg += f"حداقل مبلغ: {min_price} ریال\n"
                if max_price:
                    msg += f"حداکثر مبلغ: {max_price} ریال\n"
        msg += f"تعداد ستون‌ها: {columns_display}"
        
        await send_message(chat_id, msg, keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_detail: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات دکمه.")
        return True


# ==================== تغییر ترتیب دکمه‌ها ====================

async def handle_button_up(chat_id, user_id, data):
    """انتقال دکمه یک ردیف بالا (admin_btn_up_<button_id>)"""
    try:
        btn_id = int(data.split("_")[-1])
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        current_order = btn.get('sort_order', 0)
        category_id = btn['category_id']
        parent_id = btn.get('parent_button_id')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if parent_id:
                cursor.execute("""
                    SELECT id, sort_order FROM buttons 
                    WHERE parent_button_id = ? AND sort_order < ? 
                    ORDER BY sort_order DESC LIMIT 1
                """, (parent_id, current_order))
            else:
                cursor.execute("""
                    SELECT id, sort_order FROM buttons 
                    WHERE category_id = ? AND (parent_button_id IS NULL OR parent_button_id = 0) 
                    AND sort_order < ? 
                    ORDER BY sort_order DESC LIMIT 1
                """, (category_id, current_order))
            
            prev = cursor.fetchone()
            if not prev:
                await send_message(chat_id, "❌ این دکمه در ابتدای لیست قرار دارد.")
                return True
            
            cursor.execute("UPDATE buttons SET sort_order = ? WHERE id = ?", (prev['sort_order'], btn_id))
            cursor.execute("UPDATE buttons SET sort_order = ? WHERE id = ?", (current_order, prev['id']))
            conn.commit()
        
        logger.info(f"✅ دکمه {btn_id} ({btn['name']}) یک ردیف بالا رفت.")
        
        if parent_id:
            return await handle_show_submenu(chat_id, user_id, f"admin_sub_{parent_id}")
        else:
            return await handle_show_category_buttons(chat_id, user_id, f"admin_cat_{category_id}")
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_up: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جابجایی دکمه.")
        return True


async def handle_button_down(chat_id, user_id, data):
    """انتقال دکمه یک ردیف پایین (admin_btn_down_<button_id>)"""
    try:
        btn_id = int(data.split("_")[-1])
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        current_order = btn.get('sort_order', 0)
        category_id = btn['category_id']
        parent_id = btn.get('parent_button_id')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if parent_id:
                cursor.execute("""
                    SELECT id, sort_order FROM buttons 
                    WHERE parent_button_id = ? AND sort_order > ? 
                    ORDER BY sort_order ASC LIMIT 1
                """, (parent_id, current_order))
            else:
                cursor.execute("""
                    SELECT id, sort_order FROM buttons 
                    WHERE category_id = ? AND (parent_button_id IS NULL OR parent_button_id = 0) 
                    AND sort_order > ? 
                    ORDER BY sort_order ASC LIMIT 1
                """, (category_id, current_order))
            
            next_item = cursor.fetchone()
            if not next_item:
                await send_message(chat_id, "❌ این دکمه در انتهای لیست قرار دارد.")
                return True
            
            cursor.execute("UPDATE buttons SET sort_order = ? WHERE id = ?", (next_item['sort_order'], btn_id))
            cursor.execute("UPDATE buttons SET sort_order = ? WHERE id = ?", (current_order, next_item['id']))
            conn.commit()
        
        logger.info(f"✅ دکمه {btn_id} ({btn['name']}) یک ردیف پایین رفت.")
        
        if parent_id:
            return await handle_show_submenu(chat_id, user_id, f"admin_sub_{parent_id}")
        else:
            return await handle_show_category_buttons(chat_id, user_id, f"admin_cat_{category_id}")
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_down: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جابجایی دکمه.")
        return True


# ==================== انتقال دکمه به دسته‌بندی دیگر ====================

async def handle_button_move_start(chat_id, user_id, data):
    """شروع فرآیند انتقال دکمه به دسته‌بندی دیگر (admin_btn_move_<button_id>)"""
    try:
        btn_id = int(data.split("_")[-1])
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        categories = get_all_categories_admin()
        if not categories:
            await send_message(chat_id, "❌ هیچ دسته‌بندی برای انتقال وجود ندارد.")
            return True
        
        user_states[user_id] = {
            "state": "admin_btn_move_select",
            "moving_button_id": btn_id
        }
        
        keyboard = []
        current_cat_id = btn['category_id']
        for cat in categories:
            selected = "✅ " if cat['id'] == current_cat_id else ""
            keyboard.append([
                {"text": f"{selected}{cat['name']}", "callback_data": f"admin_btn_move_select_{cat['id']}"}
            ])
        
        keyboard.append([{"text": "🔙 انصراف", "callback_data": f"admin_btn_{btn_id}"}])
        
        await send_message(
            chat_id,
            f"📂 **انتقال دکمه «{btn['name']}» به دسته‌بندی دیگر**\n\n"
            f"دسته‌بندی فعلی: {_get_category_name(current_cat_id)}\n"
            f"لطفاً دسته‌بندی مقصد را انتخاب کنید:",
            {"inline_keyboard": keyboard}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_move_start: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع انتقال دکمه.")
        return True


async def handle_button_move_select(chat_id, user_id, data):
    """انتخاب دسته‌بندی مقصد و اجرای انتقال (admin_btn_move_select_<category_id>)"""
    try:
        target_cat_id = int(data.split("_")[-1])
        state_info = user_states.get(user_id, {})
        btn_id = state_info.get("moving_button_id")
        
        if not btn_id:
            await send_message(chat_id, "❌ خطا: شناسه دکمه یافت نشد.")
            user_states[user_id] = {"state": "main"}
            return True
        
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            user_states[user_id] = {"state": "main"}
            return True
        
        current_cat_id = btn['category_id']
        
        if target_cat_id == current_cat_id:
            await send_message(chat_id, "⚠️ دکمه در همین دسته‌بندی قرار دارد.")
            user_states[user_id] = {"state": "main"}
            return await handle_button_detail(chat_id, user_id, f"admin_btn_{btn_id}")
        
        success = _move_button_to_category(btn_id, target_cat_id)
        
        if success:
            target_cat = get_category_by_id(target_cat_id)
            await send_message(
                chat_id,
                f"✅ دکمه «{btn['name']}» با موفقیت به دسته‌بندی «{target_cat['name']}» منتقل شد.\n"
                f"همه زیرمنوهای آن نیز منتقل شدند."
            )
        else:
            await send_message(chat_id, "❌ خطا در انتقال دکمه.")
        
        user_states[user_id] = {"state": "main"}
        
        return await handle_show_category_buttons(chat_id, user_id, f"admin_cat_{target_cat_id}")
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_move_select: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتقال دکمه.")
        user_states[user_id] = {"state": "main"}
        return True


# ==================== مدیریت ستون‌های دکمه ====================

async def handle_button_set_columns(chat_id, user_id, data):
    """نمایش کیبورد انتخاب تعداد ستون‌ها برای یک دکمه (admin_btn_set_columns_<button_id>)"""
    try:
        btn_id = int(data.split("_")[-1])
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        current_columns = btn.get('columns')
        keyboard = admin_button_columns_keyboard(btn_id, current_columns)
        
        await send_message(
            chat_id,
            f"📊 **تنظیم تعداد ستون‌ها برای دکمه «{btn['name']}»**\n\n"
            f"تعداد ستون‌های فعلی: {current_columns if current_columns is not None else 'پیش‌فرض (استفاده از تنظیمات دسته‌بندی)'}\n"
            f"تعداد ستون‌های مؤثر: {get_effective_columns(button_id=btn_id, category_id=btn['category_id'])}\n\n"
            f"لطفاً تعداد ستون‌های مورد نظر را انتخاب کنید (۱ تا ۸):",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_set_columns: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش تنظیمات ستون‌ها.")
        return True


async def handle_button_set_columns_select(chat_id, user_id, data):
    """ذخیره تعداد ستون‌های انتخاب‌شده برای دکمه (admin_btn_set_columns_select_<button_id>_<columns>)"""
    try:
        parts = data.split("_")
        btn_id = int(parts[4])
        columns = int(parts[5])
        
        if columns < 1 or columns > 8:
            await send_message(chat_id, "❌ تعداد ستون‌ها باید بین ۱ تا ۸ باشد.")
            return True
        
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        if columns == 0:
            update_button(btn_id, columns=None)
            await send_message(chat_id, f"✅ تنظیمات اختصاصی ستون‌های دکمه «{btn['name']}» حذف شد. (از تنظیمات دسته‌بندی استفاده می‌شود)")
        else:
            update_button(btn_id, columns=columns)
            await send_message(chat_id, f"✅ تعداد ستون‌های دکمه «{btn['name']}» به {columns} تغییر یافت.")
        
        return await handle_button_detail(chat_id, user_id, f"admin_btn_{btn_id}")
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_set_columns_select: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ذخیره تنظیمات ستون‌ها.")
        return True


# ==================== مدیریت قیمت متغیر ====================

async def handle_button_price_type(chat_id, user_id, data):
    """تغییر نوع قیمت دکمه (admin_btn_price_type_<button_id>)"""
    try:
        btn_id = int(data.split("_")[-1])
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        current_type = btn.get('price_type', 'fixed')
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "✅ ثابت" if current_type == 'fixed' else "ثابت", 
                  "callback_data": f"admin_btn_price_type_set_{btn_id}_fixed"}],
                [{"text": "✅ متغیر" if current_type == 'variable' else "متغیر", 
                  "callback_data": f"admin_btn_price_type_set_{btn_id}_variable"}],
                [{"text": "🔙 انصراف", "callback_data": f"admin_btn_{btn_id}"}]
            ]
        }
        
        await send_message(
            chat_id,
            f"💰 **نوع قیمت دکمه «{btn['name']}»**\n\n"
            f"نوع فعلی: {'ثابت' if current_type == 'fixed' else 'متغیر'}\n\n"
            f"• ثابت: مبلغ ثابت برای همه کاربران\n"
            f"• متغیر: کاربر مبلغ را وارد می‌کند (با حداقل و حداکثر مشخص)\n\n"
            f"نوع مورد نظر را انتخاب کنید:",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_price_type: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر نوع قیمت.")
        return True


async def handle_button_price_type_set(chat_id, user_id, data):
    """اعمال نوع قیمت جدید (admin_btn_price_type_set_<button_id>_<type>)"""
    try:
        parts = data.split("_")
        btn_id = int(parts[5])
        price_type = parts[6]
        
        if price_type not in ['fixed', 'variable']:
            await send_message(chat_id, "❌ نوع قیمت نامعتبر.")
            return True
        
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        update_button_price(btn_id, price_type=price_type)
        
        if price_type == 'variable':
            # اگر نوع متغیر شد، از کاربر حداقل و حداکثر مبلغ را می‌خواهیم
            user_states[user_id] = {
                "state": "admin_btn_set_min_price",
                "btn_id": btn_id
            }
            await send_message(
                chat_id,
                f"✅ نوع قیمت دکمه «{btn['name']}» به «متغیر» تغییر یافت.\n\n"
                f"لطفاً **حداقل مبلغ** را به ریال وارد کنید:\n"
                f"(کاربر نمی‌تواند کمتر از این مبلغ وارد کند)\n\n"
                f"برای انصراف، /cancel را ارسال کنید."
            )
        else:
            await send_message(
                chat_id,
                f"✅ نوع قیمت دکمه «{btn['name']}» به «ثابت» تغییر یافت.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": f"admin_btn_{btn_id}"}]]}
            )
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_price_type_set: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم نوع قیمت.")
        return True


async def handle_button_set_min_price(chat_id, user_id, text):
    """تنظیم حداقل مبلغ برای قیمت متغیر"""
    try:
        state_info = user_states.get(user_id, {})
        btn_id = state_info.get("btn_id")
        
        if not btn_id:
            await send_message(chat_id, "❌ خطا: شناسه دکمه یافت نشد.")
            user_states[user_id] = {"state": "main"}
            return True
        
        try:
            min_price = int(text.replace(",", "").replace(" ", ""))
            if min_price < 0:
                await send_message(chat_id, "❌ مبلغ نمی‌تواند منفی باشد.")
                return True
        except ValueError:
            await send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.")
            return True
        
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            user_states[user_id] = {"state": "main"}
            return True
        
        update_button_price(btn_id, min_price=min_price)
        
        user_states[user_id]["state"] = "admin_btn_set_max_price"
        
        await send_message(
            chat_id,
            f"✅ حداقل مبلغ {min_price:,} ریال تنظیم شد.\n\n"
            f"لطفاً **حداکثر مبلغ** را به ریال وارد کنید:\n"
            f"(کاربر نمی‌تواند بیشتر از این مبلغ وارد کند)\n\n"
            f"برای انصراف، /cancel را ارسال کنید."
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_set_min_price: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم حداقل مبلغ.")
        return True


async def handle_button_set_max_price(chat_id, user_id, text):
    """تنظیم حداکثر مبلغ برای قیمت متغیر"""
    try:
        state_info = user_states.get(user_id, {})
        btn_id = state_info.get("btn_id")
        
        if not btn_id:
            await send_message(chat_id, "❌ خطا: شناسه دکمه یافت نشد.")
            user_states[user_id] = {"state": "main"}
            return True
        
        try:
            max_price = int(text.replace(",", "").replace(" ", ""))
            if max_price < 0:
                await send_message(chat_id, "❌ مبلغ نمی‌تواند منفی باشد.")
                return True
        except ValueError:
            await send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.")
            return True
        
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            user_states[user_id] = {"state": "main"}
            return True
        
        # بررسی اینکه حداکثر از حداقل کمتر نباشد
        price_info = get_button_price_info(btn_id)
        min_price = price_info.get('min_price')
        
        if min_price and max_price < min_price:
            await send_message(
                chat_id,
                f"❌ حداکثر مبلغ ({max_price:,}) نمی‌تواند از حداقل مبلغ ({min_price:,}) کمتر باشد."
            )
            return True
        
        update_button_price(btn_id, max_price=max_price)
        
        btn = get_button_by_id(btn_id)
        
        user_states[user_id] = {"state": "main"}
        
        await send_message(
            chat_id,
            f"✅ حداکثر مبلغ {max_price:,} ریال تنظیم شد.\n\n"
            f"💰 قیمت متغیر دکمه «{btn['name']}» تنظیم شد:\n"
            f"  • حداقل: {min_price:,} ریال\n"
            f"  • حداکثر: {max_price:,} ریال\n\n"
            f"کاربران می‌توانند مبلغی بین این دو مقدار وارد کنند.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به دکمه", "callback_data": f"admin_btn_{btn_id}"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_set_max_price: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم حداکثر مبلغ.")
        return True


# ==================== سایر توابع (ویرایش، قیمت، وضعیت، حذف) ====================

async def handle_button_edit(chat_id, user_id, data):
    """شروع ویرایش نام دکمه (admin_btn_edit_*)"""
    try:
        btn_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        user_states[user_id] = {"state": "admin_edit_button_name", "btn_id": btn_id}
        await send_message(chat_id, "✏️ **ویرایش نام دکمه**\nلطفاً نام جدید را وارد کنید:")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_edit: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع ویرایش.")
        return True


async def handle_button_price(chat_id, user_id, data):
    """شروع تنظیم قیمت دکمه (admin_btn_price_*)"""
    try:
        btn_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        price_type = btn.get('price_type', 'fixed')
        
        if price_type == 'variable':
            await send_message(
                chat_id,
                "💰 **تنظیم قیمت متغیر**\n\n"
                "این دکمه قیمت متغیر دارد. برای تنظیم حداقل و حداکثر، از گزینه‌های زیر استفاده کنید:",
                {
                    "inline_keyboard": [
                        [{"text": "💰 تنظیم حداقل مبلغ", "callback_data": f"admin_btn_set_min_price_{btn_id}"}],
                        [{"text": "💰 تنظیم حداکثر مبلغ", "callback_data": f"admin_btn_set_max_price_{btn_id}"}],
                        [{"text": "🔙 بازگشت", "callback_data": f"admin_btn_{btn_id}"}]
                    ]
                }
            )
            return True
        
        user_states[user_id] = {"state": "admin_set_button_price", "btn_id": btn_id}
        await send_message(chat_id, "💰 **تنظیم مبلغ ثابت**\nلطفاً مبلغ جدید را به ریال وارد کنید (فقط عدد):")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_price: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع تنظیم قیمت.")
        return True


async def handle_button_payment_status(chat_id, user_id, data):
    """تغییر وضعیت پرداخت دکمه (admin_btn_payment_*)"""
    try:
        btn_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        btn = get_button_by_id(btn_id)
        if btn:
            new_status = 0 if btn.get('has_payment', 0) == 1 else 1
            update_button(btn_id, has_payment=new_status)
            status_text = "فعال" if new_status == 1 else "غیرفعال"
            await send_message(chat_id, f"✅ وضعیت پرداخت دکمه «{btn['name']}» به «{status_text}» تغییر یافت.", admin_main_keyboard())
        else:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_payment_status: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر وضعیت پرداخت.")
        return True


async def handle_button_active_status(chat_id, user_id, data):
    """تغییر وضعیت فعال/غیرفعال دکمه (admin_btn_status_*)"""
    try:
        btn_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        btn = get_button_by_id(btn_id)
        if btn:
            new_status = 0 if btn.get('is_active', 1) == 1 else 1
            update_button(btn_id, is_active=new_status)
            status_text = "فعال" if new_status == 1 else "غیرفعال"
            await send_message(chat_id, f"✅ وضعیت دکمه «{btn['name']}» به «{status_text}» تغییر یافت.", admin_main_keyboard())
        else:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_active_status: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر وضعیت.")
        return True


async def handle_button_delete(chat_id, user_id, data):
    """حذف دکمه و بازگشت به صفحه مناسب (admin_btn_del_*)"""
    try:
        btn_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        btn = get_button_by_id(btn_id)
        if not btn:
            await send_message(chat_id, "❌ دکمه یافت نشد.")
            return True
        
        cat_id = btn['category_id']
        parent_id = btn.get('parent_button_id')
        btn_name = btn['name']
        
        success = delete_button(btn_id)
        if success:
            await send_message(chat_id, f"✅ دکمه «{btn_name}» با موفقیت حذف شد.")
            
            from .cb_routes import handle_admin_callback
            if parent_id:
                await handle_admin_callback({
                    "callback_query": {
                        "data": f"admin_sub_{parent_id}",
                        "from": {"id": user_id},
                        "message": {"chat": {"id": chat_id}}
                    }
                })
            else:
                await handle_admin_callback({
                    "callback_query": {
                        "data": f"admin_cat_{cat_id}",
                        "from": {"id": user_id},
                        "message": {"chat": {"id": chat_id}}
                    }
                })
        else:
            await send_message(chat_id, "❌ خطا در حذف دکمه.")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_button_delete: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف دکمه.")
        return True


async def handle_submenu_manage(chat_id, user_id, data):
    """نمایش زیرمنوهای یک دکمه (admin_sub_manage_*)"""
    try:
        btn_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        await send_message(chat_id, f"🔽 **زیرمنوهای این دکمه**", admin_submenu_keyboard(btn_id))
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_submenu_manage: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش زیرمنوها.")
        return True


async def handle_submenu_add(chat_id, user_id, data):
    """شروع افزودن زیرمنو جدید (admin_sub_add_*)"""
    try:
        parent_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        parent_btn = get_button_by_id(parent_id)
        if not parent_btn:
            await send_message(chat_id, "❌ دکمه والد یافت نشد.")
            return True
        
        cat_id = parent_btn['category_id']
        user_states[user_id] = {
            "state": "admin_create_button_name",
            "cat_id": cat_id,
            "parent_button_id": parent_id
        }
        await send_message(chat_id, f"➕ **افزودن زیرمنو برای {parent_btn['name']}**\nلطفاً نام زیرمنو را وارد کنید:")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_submenu_add: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع افزودن زیرمنو.")
        return True


# ==================== مدیریت دسته‌بندی‌ها ====================

async def handle_category_edit(chat_id, user_id, data):
    """شروع ویرایش نام دسته‌بندی (admin_cat_edit_<id>)"""
    try:
        cat_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه دسته‌بندی نامعتبر.")
        return True
    
    try:
        category = get_category_by_id(cat_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        user_states[user_id] = {"state": "admin_edit_category_name", "cat_id": cat_id}
        await send_message(chat_id, f"✏️ **ویرایش نام دسته‌بندی «{category['name']}»**\nلطفاً نام جدید را وارد کنید:")
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_category_edit: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع ویرایش دسته‌بندی.")
        return True


async def handle_category_set_columns(chat_id, user_id, data):
    """نمایش کیبورد انتخاب تعداد ستون‌ها برای یک دسته‌بندی (admin_cat_set_columns_<category_id>)"""
    try:
        cat_id = int(data.split("_")[-1])
        category = get_category_by_id(cat_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        current_columns = category.get('columns', 2)
        keyboard = admin_category_columns_keyboard(cat_id, current_columns)
        
        await send_message(
            chat_id,
            f"📊 **تنظیم تعداد ستون‌های منو برای دسته‌بندی «{category['name']}»**\n\n"
            f"تعداد ستون‌های فعلی: {current_columns}\n"
            f"این تنظیم بر نمایش دکمه‌های این دسته‌بندی در منو تأثیر می‌گذارد.\n\n"
            f"لطفاً تعداد ستون‌های مورد نظر را انتخاب کنید (۱ تا ۸):",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_category_set_columns: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش تنظیمات ستون‌های دسته‌بندی.")
        return True


async def handle_category_set_columns_select(chat_id, user_id, data):
    """ذخیره تعداد ستون‌های انتخاب‌شده برای دسته‌بندی (admin_cat_set_columns_select_<category_id>_<columns>)"""
    try:
        parts = data.split("_")
        cat_id = int(parts[4])
        columns = int(parts[5])
        
        if columns < 1 or columns > 8:
            await send_message(chat_id, "❌ تعداد ستون‌ها باید بین ۱ تا ۸ باشد.")
            return True
        
        category = get_category_by_id(cat_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        update_category(cat_id, columns=columns)
        await send_message(chat_id, f"✅ تعداد ستون‌های دسته‌بندی «{category['name']}» به {columns} تغییر یافت.")
        
        return await handle_show_category_buttons(chat_id, user_id, f"admin_cat_{cat_id}")
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_category_set_columns_select: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ذخیره تنظیمات ستون‌های دسته‌بندی.")
        return True


async def handle_category_delete_confirm(chat_id, user_id, data):
    """نمایش تاییدیه حذف دسته‌بندی (admin_cat_del_confirm_<id>)"""
    try:
        cat_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه دسته‌بندی نامعتبر.")
        return True
    
    try:
        category = get_category_by_id(cat_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        keyboard = admin_category_delete_confirm_keyboard(cat_id, category['name'])
        await send_message(chat_id, f"⚠️ **هشدار حذف دسته‌بندی**\nآیا از حذف دسته‌بندی «{category['name']}» و تمام دکمه‌های آن مطمئن هستید؟", keyboard)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_category_delete_confirm: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش تاییدیه حذف.")
        return True


async def handle_category_delete(chat_id, user_id, data):
    """اجرای حذف دسته‌بندی (admin_cat_del_yes_<id>)"""
    try:
        cat_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه دسته‌بندی نامعتبر.")
        return True
    
    try:
        category = get_category_by_id(cat_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        delete_category(cat_id)
        await send_message(chat_id, f"✅ دسته‌بندی «{category['name']}» و تمام دکمه‌های آن با موفقیت حذف شد.")
        
        await handle_show_categories(chat_id)
        return True
    except Exception as e:
        log_callback_error(
            f"Error in handle_category_delete: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف دسته‌بندی.")
        return True


# ==================== مدیریت قیمت متغیر دسته‌بندی ====================

async def handle_category_price(chat_id, user_id, data):
    """مدیریت قیمت‌های متغیر دکمه‌های یک دسته‌بندی (admin_cat_price_<category_id>)"""
    try:
        cat_id = int(data.split("_")[-1])
        category = get_category_by_id(cat_id)
        if not category:
            await send_message(chat_id, "❌ دسته‌بندی یافت نشد.")
            return True
        
        buttons = get_buttons_by_category(cat_id)
        variable_buttons = [b for b in buttons if b.get('price_type', 'fixed') == 'variable']
        
        if not variable_buttons:
            await send_message(
                chat_id,
                f"💰 **مدیریت قیمت متغیر - دسته‌بندی «{category['name']}»**\n\n"
                f"هیچ دکمه‌ای با قیمت متغیر در این دسته‌بندی وجود ندارد.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": f"admin_cat_{cat_id}"}]]}
            )
            return True
        
        msg = f"💰 **مدیریت قیمت متغیر - دسته‌بندی «{category['name']}»**\n\n"
        msg += f"دکمه‌های با قیمت متغیر:\n"
        
        keyboard = []
        for btn in variable_buttons:
            price_info = get_button_price_info(btn['id'])
            min_price = price_info.get('min_price')
            max_price = price_info.get('max_price')
            price_display = f"حداقل: {min_price:,} | حداکثر: {max_price:,}" if min_price and max_price else "تنظیم نشده"
            keyboard.append([
                {"text": f"🔘 {btn['name']} - {price_display}",
                 "callback_data": f"admin_btn_{btn['id']}"}
            ])
        
        keyboard.append([{"text": "🔙 برگشت", "callback_data": f"admin_cat_{cat_id}"}])
        
        await send_message(chat_id, msg, {"inline_keyboard": keyboard})
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_category_price: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در مدیریت قیمت متغیر دسته‌بندی.")
        return True


__all__ = [
    'handle_show_categories',
    'handle_show_category_buttons',
    'handle_show_submenu',
    'handle_button_detail',
    'handle_button_edit',
    'handle_button_price',
    'handle_button_payment_status',
    'handle_button_active_status',
    'handle_button_delete',
    'handle_submenu_manage',
    'handle_submenu_add',
    'handle_category_edit',
    'handle_category_delete_confirm',
    'handle_category_delete',
    'handle_show_buttons',
    'handle_button_up',
    'handle_button_down',
    'handle_button_move_start',
    'handle_button_move_select',
    'handle_button_set_columns',
    'handle_button_set_columns_select',
    'handle_category_set_columns',
    'handle_category_set_columns_select',
    'handle_button_price_type',
    'handle_button_price_type_set',
    'handle_button_set_min_price',
    'handle_button_set_max_price',
    'handle_category_price',
]