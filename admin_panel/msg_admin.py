# admin_panel/msg_admin.py
# پردازش پیام‌های متنی مدیریت - نسخه کامل با پشتیبانی از تمام بخش‌ها
# شامل: برندینگ، نسخه‌سازی، مدیریت کاربران، پشتیبان‌گیری، تنظیمات و ...

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states, log_error, log_callback_error, log_general_error, log_database_error
from database import (
    get_button_by_id,
    update_button,
    get_question_by_id,
    update_question,
    add_question,
    add_question_option,
    add_condition,
    update_condition,
    get_db_connection,
    set_setting,
    get_category_by_id,
    add_button,
    delete_duplicate_submenus,
    get_all_submenus,
    update_category,
    add_category,
    add_admin,
    search_admins,
    is_admin,
    save_button_version,
    get_setting,
    set_default_menu_columns,
)
from keyboards import admin_main_keyboard, admin_questions_keyboard
from datetime import datetime

# ایمپورت توابع مدیریت اعتبارسنجی (برای پردازش پیام‌های مربوطه)
from .msg_validation import handle_admin_message_validation

# ایمپورت توابع بخش‌های جدید
from .branding import handle_branding_save
from .versioning import handle_version_save_note
from .backup import handle_backup_restore_file
from .user_management import handle_user_search_result
from .btn_manage import handle_button_move_select, handle_button_set_min_price, handle_button_set_max_price
# اصلاح: توابع تنظیمات از settings (نه settings_routes)
from .settings import handle_set_price_message, handle_set_default_columns_message
from .filter_routes import handle_filter_message
from .advanced_search import handle_adv_search_message
from .templates import handle_template_message


async def handle_admin_message(update):
    """
    پردازش پیام‌های متنی ارسال‌شده به ربات در حالت مدیریت
    بازگشت True اگر پیام پردازش شد، در غیر این صورت False
    """
    try:
        msg = update.get("message")
        if not msg:
            return False

        chat_id = msg.get("chat", {}).get("id")
        user_id = msg.get("from", {}).get("id")
        text = msg.get("text", "").strip()

        if not user_id or not chat_id:
            return False

        state_info = user_states.get(user_id, {"state": "main"})
        current_state = state_info.get("state")

        # ========== تنظیم مبلغ پیش‌فرض ==========
        if current_state == "admin_set_price":
            return await handle_set_price_message(chat_id, user_id, text)

        # ========== تنظیم تعداد ستون‌های پیش‌فرض ==========
        if current_state == "admin_set_default_columns":
            return await handle_set_default_columns_message(chat_id, user_id, text)

        # ========== تنظیم حداقل مبلغ قیمت متغیر ==========
        if current_state == "admin_btn_set_min_price":
            return await handle_button_set_min_price(chat_id, user_id, text)

        # ========== تنظیم حداکثر مبلغ قیمت متغیر ==========
        if current_state == "admin_btn_set_max_price":
            return await handle_button_set_max_price(chat_id, user_id, text)

        # ========== بررسی وضعیت‌های مدیریت اعتبارسنجی ==========
        # این وضعیت‌ها با admin_set_ شروع می‌شوند اما بعد از وضعیت‌های خاص بالا قرار دارند
        if current_state and current_state.startswith("admin_set_"):
            return await handle_admin_message_validation(update)

        # ========== افزودن دسته‌بندی جدید - مرحله نام ==========
        if current_state == "admin_add_category_name":
            if not text:
                await send_message(chat_id, "❌ نام نمی‌تواند خالی باشد.")
                return True

            user_states[user_id]["temp_category_name"] = text
            user_states[user_id]["state"] = "admin_add_category_location"

            keyboard = {
                "inline_keyboard": [
                    [{"text": "📌 منوی اصلی", "callback_data": "admin_cat_loc_main"}],
                    [{"text": "📌 منوی بیشتر", "callback_data": "admin_cat_loc_more"}],
                    [{"text": "📌 دیگر خدمات", "callback_data": "admin_cat_loc_other"}]
                ]
            }
            await send_message(chat_id, f"➕ دسته‌بندی «{text}» در کدام منو قرار گیرد؟", keyboard)
            return True

        # ========== ایجاد دکمه جدید - مرحله نام ==========
        if current_state == "admin_create_button_name":
            if not text:
                await send_message(chat_id, "❌ نام نمی‌تواند خالی باشد.")
                return True

            cat_id = state_info.get("cat_id")
            parent_button_id = state_info.get("parent_button_id")
            from_category = state_info.get("from_category", False)

            if not cat_id:
                await send_message(chat_id, "❌ خطا: شناسه دسته‌بندی یافت نشد.")
                user_states[user_id] = {"state": "main"}
                return True

            btn_id = add_button(cat_id, text, parent_button_id=parent_button_id)

            if parent_button_id:
                update_button(parent_button_id, has_submenu=1)

            if parent_button_id:
                user_states[user_id] = {"state": "main"}
                await send_message(chat_id, f"✅ زیرمنو «{text}» با موفقیت ایجاد شد.")
                from .cb_routes import handle_admin_callback
                await handle_admin_callback({
                    "callback_query": {
                        "data": f"admin_sub_{parent_button_id}",
                        "from": {"id": user_id},
                        "message": {"chat": {"id": chat_id}}
                    }
                })
                return True

            if from_category:
                user_states[user_id]["btn_id"] = btn_id
                user_states[user_id]["cat_id_for_back"] = cat_id
                user_states[user_id]["state"] = "admin_create_submenu_ask"
                await send_message(
                    chat_id,
                    f"✅ نام دکمه «{text}» ثبت شد.\n\nآیا این دکمه **زیرمنو** دارد؟",
                    {
                        "inline_keyboard": [
                            [{"text": "بله", "callback_data": "admin_has_submenu_yes"}],
                            [{"text": "خیر", "callback_data": "admin_has_submenu_no"}]
                        ]
                    }
                )
                return True

            user_states[user_id]["btn_id"] = btn_id
            user_states[user_id]["state"] = "admin_create_submenu_ask"
            await send_message(
                chat_id,
                f"✅ نام دکمه «{text}» ثبت شد.\n\nآیا این دکمه **زیرمنو** دارد؟",
                {
                    "inline_keyboard": [
                        [{"text": "بله", "callback_data": "admin_has_submenu_yes"}],
                        [{"text": "خیر", "callback_data": "admin_has_submenu_no"}]
                    ]
                }
            )
            return True

        # ========== ایجاد زیرمنوها ==========
        if current_state == "admin_create_submenu_name":
            if text.lower() == "پایان":
                btn_id = state_info.get("btn_id")
                if btn_id:
                    delete_duplicate_submenus(btn_id)
                user_states[user_id] = {"state": "main"}
                await send_message(chat_id, "✅ ایجاد زیرمنوها به پایان رسید و زیرمنوهای تکراری پاکسازی شدند.")
                from .cb_routes import handle_admin_callback
                await handle_admin_callback({
                    "callback_query": {
                        "data": f"admin_sub_{btn_id}",
                        "from": {"id": user_id},
                        "message": {"chat": {"id": chat_id}}
                    }
                })
                return True

            btn_id = state_info.get("btn_id")
            cat_id = state_info.get("cat_id")

            if btn_id and cat_id:
                main_button = get_button_by_id(btn_id)
                if main_button and text.strip() == main_button['name']:
                    await send_message(
                        chat_id,
                        f"❌ نام زیرمنو نمی‌تواند با نام دکمه اصلی («{main_button['name']}») یکسان باشد.\nلطفاً نام دیگری وارد کنید:"
                    )
                    return True

                existing_submenus = get_all_submenus(btn_id)
                for sub in existing_submenus:
                    if sub['name'] == text.strip():
                        await send_message(
                            chat_id,
                            f"❌ زیرمنویی با نام «{text}» قبلاً وجود دارد.\nلطفاً نام دیگری وارد کنید:"
                        )
                        return True

                add_button(cat_id, text, parent_button_id=btn_id)
                await send_message(chat_id, f"✅ زیرمنو «{text}» اضافه شد.\nزیرمنوی بعدی را وارد کنید (یا 'پایان' برای اتمام):")
            return True

        # ========== ویرایش نام دکمه ==========
        if current_state == "admin_edit_button_name":
            btn_id = state_info.get("btn_id")
            if not btn_id or not text:
                await send_message(chat_id, "❌ خطا در ویرایش.")
                return True
            update_button(btn_id, name=text)
            await send_message(chat_id, f"✅ نام دکمه به «{text}» تغییر یافت.", admin_main_keyboard())
            user_states[user_id] = {"state": "main"}
            return True

        # ========== ویرایش نام دسته‌بندی ==========
        if current_state == "admin_edit_category_name":
            if not text:
                await send_message(chat_id, "❌ نام نمی‌تواند خالی باشد.")
                return True

            cat_id = state_info.get("cat_id")
            if not cat_id:
                await send_message(chat_id, "❌ خطا: شناسه دسته‌بندی یافت نشد.")
                user_states[user_id] = {"state": "main"}
                return True

            update_category(cat_id, name=text)
            await send_message(chat_id, f"✅ نام دسته‌بندی به «{text}» تغییر یافت.")

            from .btn_manage import handle_show_categories
            await handle_show_categories(chat_id)
            user_states[user_id] = {"state": "main"}
            return True

        # ========== تنظیم قیمت دکمه ==========
        if current_state == "admin_set_button_price":
            try:
                price = int(text.replace(",", "").replace(" ", ""))
                if price < 10000:
                    await send_message(chat_id, "❌ مبلغ نمی‌تواند کمتر از ۱۰,۰۰۰ ریال باشد.")
                    return True
                if price <= 0:
                    await send_message(chat_id, "❌ مبلغ باید بزرگتر از صفر باشد.")
                    return True
                btn_id = state_info.get("btn_id")
                if btn_id:
                    update_button(btn_id, price_amount=price)
                    await send_message(chat_id, f"✅ مبلغ دکمه به {price:,} ریال تنظیم شد.", admin_main_keyboard())
                else:
                    await send_message(chat_id, "❌ خطا: شناسه دکمه یافت نشد.")
                user_states[user_id] = {"state": "main"}
            except ValueError:
                await send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.")
            return True

        # ========== افزودن سوال جدید - مرحله متن ==========
        if current_state == "admin_add_question_text":
            if not text:
                await send_message(chat_id, "❌ متن نمی‌تواند خالی باشد.")
                return True
            btn_id = state_info.get("btn_id")
            if btn_id:
                user_states[user_id]["temp_question_text"] = text
                user_states[user_id]["btn_id"] = btn_id
                user_states[user_id]["state"] = "admin_question_condition_ask"
                await send_message(
                    chat_id,
                    f"❓ سوال: «{text}»\n\nآیا می‌خواهید برای این سوال **شرط نمایش** تعریف کنید؟\n(شرط بر اساس پاسخ یک سوال قبلی تعیین می‌شود)",
                    {
                        "inline_keyboard": [
                            [{"text": "بله", "callback_data": "admin_condition_yes"}],
                            [{"text": "خیر", "callback_data": "admin_condition_no"}]
                        ]
                    }
                )
            else:
                await send_message(chat_id, "❌ خطا: شناسه دکمه یافت نشد.")
            return True

        # ========== مقدار شرط برای سوال جدید ==========
        if current_state == "admin_question_condition_value":
            if not text:
                await send_message(chat_id, "❌ مقدار نمی‌تواند خالی باشد.")
                return True
            btn_id = state_info.get("btn_id")
            question_text = state_info.get("temp_question_text")
            ref_id = state_info.get("condition_ref_id")
            operator = state_info.get("condition_operator")
            if btn_id and question_text and ref_id and operator:
                array_name = f"answer_{btn_id}_{int(datetime.now().timestamp())}"
                q_id = add_question(btn_id, question_text, needs_button=0, array_name=array_name)
                add_condition(q_id, ref_id, operator, text)
                user_states[user_id].pop("temp_question_text", None)
                user_states[user_id].pop("condition_ref_id", None)
                user_states[user_id].pop("condition_operator", None)
                user_states[user_id]["state"] = "main"
                await send_message(
                    chat_id,
                    f"✅ سوال «{question_text}» با شرط «{operator} {text}» با موفقیت افزوده شد.",
                    admin_questions_keyboard(btn_id)
                )
            else:
                await send_message(chat_id, "❌ خطا در افزودن سوال.")
            return True

        # ========== مقدار شرط برای شرط جدید ==========
        if current_state == "admin_add_condition_value":
            if not text:
                await send_message(chat_id, "❌ مقدار نمی‌تواند خالی باشد.")
                return True
            q_id = state_info.get("condition_question_id")
            ref_id = state_info.get("condition_ref_id")
            operator = state_info.get("condition_operator")
            if not q_id:
                await send_message(chat_id, "❌ خطا: شناسه سوال یافت نشد. لطفاً از ابتدا اقدام کنید.")
                user_states[user_id] = {"state": "main"}
                return True
            if ref_id and operator:
                user_states[user_id]["condition_temp_value"] = text
                user_states[user_id]["state"] = "admin_add_condition_logic"
                from keyboards import logic_operator_keyboard
                await send_message(
                    chat_id,
                    "🔹 **انتخاب منطق ترکیب شرط‌ها**\nاین شرط با شرط بعدی چگونه ترکیب شود؟",
                    logic_operator_keyboard()
                )
            else:
                missing = []
                if not ref_id:
                    missing.append("سوال مرجع")
                if not operator:
                    missing.append("عملگر")
                await send_message(
                    chat_id,
                    f"❌ خطا: اطلاعات زیر یافت نشد: {', '.join(missing)}\nلطفاً دوباره از ابتدا اقدام کنید."
                )
                user_states[user_id] = {"state": "main"}
            return True

        # ========== ویرایش مقدار شرط ==========
        if current_state == "admin_edit_condition_value":
            if not text:
                await send_message(chat_id, "❌ مقدار نمی‌تواند خالی باشد.")
                return True
            cond_id = state_info.get("edit_condition_id")
            if cond_id:
                update_condition(cond_id, condition_value=text)
                user_states[user_id].pop("edit_condition_id", None)
                user_states[user_id]["state"] = "main"
                btn_id = user_states.get(user_id, {}).get("current_btn")
                await send_message(
                    chat_id,
                    "✅ مقدار شرط با موفقیت به‌روزرسانی شد.",
                    admin_questions_keyboard(btn_id)
                )
            else:
                await send_message(chat_id, "❌ خطا در ویرایش شرط.")
            return True

        # ========== ویرایش متن سوال ==========
        if current_state == "admin_edit_question_text":
            q_id = state_info.get("q_id")
            if not q_id or not text:
                await send_message(chat_id, "❌ خطا.")
                return True
            update_question(q_id, question_text=text)
            q = get_question_by_id(q_id)
            if q:
                await send_message(
                    chat_id,
                    f"✅ سوال به «{text}» تغییر یافت.",
                    admin_questions_keyboard(q['button_id'])
                )
            else:
                await send_message(chat_id, "✅ سوال به‌روز شد.", admin_main_keyboard())
            user_states[user_id] = {"state": "main"}
            return True

        # ========== افزودن گزینه دکمه‌ای ==========
        if current_state == "admin_add_question_option":
            if not text:
                await send_message(chat_id, "❌ متن گزینه نمی‌تواند خالی باشد.")
                return True
            q_id = state_info.get("q_id")
            if q_id:
                add_question_option(q_id, text)
                update_question(q_id, needs_button=1)
                await send_message(
                    chat_id,
                    f"✅ گزینه «{text}» اضافه شد.\n\nگزینه بعدی را وارد کنید (یا 'پایان' برای اتمام):"
                )
                user_states[user_id]["state"] = "admin_add_question_option_continue"
                user_states[user_id]["q_id"] = q_id
            return True

        if current_state == "admin_add_question_option_continue":
            if text.lower() == "پایان":
                user_states[user_id]["state"] = "main"
                await send_message(chat_id, "✅ افزودن گزینه‌ها به پایان رسید.", admin_main_keyboard())
                return True
            q_id = state_info.get("q_id")
            if q_id:
                add_question_option(q_id, text)
                await send_message(
                    chat_id,
                    f"✅ گزینه «{text}» اضافه شد.\nگزینه بعدی را وارد کنید (یا 'پایان' برای اتمام):"
                )
            return True

        # ========== ویرایش گزینه دکمه‌ای ==========
        if current_state == "admin_edit_question_option":
            opt_id = state_info.get("opt_id")
            if not opt_id or not text:
                await send_message(chat_id, "❌ خطا.")
                return True
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE question_options SET option_text = ? WHERE id = ?", (text, opt_id))
                conn.commit()
            await send_message(chat_id, f"✅ گزینه به «{text}» تغییر یافت.", admin_main_keyboard())
            user_states[user_id] = {"state": "main"}
            return True

        # ========== اضافه کردن ادمین جدید ==========
        if current_state == "admin_add_admin":
            try:
                new_admin_id = int(text.strip())
            except ValueError:
                await send_message(chat_id, "❌ شناسه کاربر باید عدد باشد. دوباره وارد کنید:")
                return True

            if is_admin(new_admin_id):
                await send_message(chat_id, f"⚠️ کاربر {new_admin_id} از قبل در لیست ادمین‌ها وجود دارد.")
                user_states[user_id] = {"state": "main"}
                from .admin_management import handle_admin_management
                await handle_admin_management(chat_id, user_id, 0)
                return True

            user_states[user_id]["pending_admin_id"] = new_admin_id
            user_states[user_id]["state"] = "admin_add_admin_role"

            from keyboards.kb_admin_common import admin_add_admin_roles_keyboard
            keyboard = admin_add_admin_roles_keyboard(new_admin_id)
            await send_message(
                chat_id,
                f"✅ شناسه کاربر {new_admin_id} دریافت شد.\n\nلطفاً نقش مورد نظر را انتخاب کنید:",
                keyboard
            )
            return True

        # ========== جستجوی ادمین‌ها ==========
        if current_state == "admin_search_admin":
            if not text or text.strip() == "":
                await send_message(chat_id, "❌ لطفاً یک کلمه کلیدی معتبر وارد کنید.")
                return True

            results = search_admins(text.strip())

            if not results:
                await send_message(chat_id, f"❌ هیچ ادمینی با عبارت «{text}» یافت نشد.")
                user_states[user_id] = {"state": "main"}
                from .admin_management import handle_admin_management
                await handle_admin_management(chat_id, user_id, 0)
                return True

            role_labels = {
                'owner': '👑 مالک',
                'admin': '🛡️ ادمین',
                'manager': '📋 مدیر',
                'observer': '👁️ ناظر'
            }

            msg = f"🔍 **نتایج جستجو برای «{text}»**\n\n"
            msg += f"تعداد: {len(results)} نفر\n\n"

            for admin in results:
                user_id_found = admin['user_id']
                role = admin.get('role', 'admin')
                is_active = admin.get('is_active', 1)
                status_icon = "🟢" if is_active == 1 else "🔴"
                role_label = role_labels.get(role, role)
                msg += f"{status_icon} {user_id_found} - {role_label}\n"

            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 برگشت به لیست ادمین‌ها", "callback_data": "admin_manage_admins"}]
                ]
            }

            await send_message(chat_id, msg, keyboard)
            user_states[user_id] = {"state": "main"}
            return True

        # ========== جستجوی سفارشات ==========
        if current_state == "admin_orders_search":
            if not text or text.strip() == "":
                await send_message(chat_id, "❌ لطفاً یک کلمه کلیدی معتبر وارد کنید.")
                return True

            from .orders import handle_orders_search_result
            await handle_orders_search_result(chat_id, user_id, text.strip())
            user_states[user_id] = {"state": "main"}
            return True

        # ========== افزودن یادداشت به سفارش ==========
        if current_state == "admin_order_note":
            if not text or text.strip() == "":
                await send_message(chat_id, "❌ متن یادداشت نمی‌تواند خالی باشد.")
                return True

            from .orders import handle_order_note_add
            await handle_order_note_add(chat_id, user_id, text.strip())
            user_states[user_id] = {"state": "main"}
            return True

        # ========== بخش جدید: برندینگ - ویرایش متن ==========
        if current_state == "admin_branding_edit":
            return await handle_branding_save(chat_id, user_id, text)

        # ========== بخش جدید: نسخه‌سازی - ذخیره یادداشت نسخه ==========
        if current_state == "admin_version_save_note":
            return await handle_version_save_note(chat_id, user_id, text)

        # ========== بخش جدید: پشتیبان‌گیری - دریافت فایل برای بازیابی ==========
        if current_state == "admin_restore_backup":
            # پردازش فایل آپلودشده
            if "document" in msg:
                file_info = {
                    "file_id": msg["document"]["file_id"],
                    "file_name": msg["document"].get("file_name", "backup.db")
                }
                return await handle_backup_restore_file(chat_id, user_id, file_info)
            elif "photo" in msg:
                await send_message(chat_id, "❌ لطفاً یک فایل دیتابیس (.db) ارسال کنید، نه عکس.")
                return True
            else:
                await send_message(chat_id, "❌ لطفاً یک فایل دیتابیس (.db) ارسال کنید.")
                return True

        # ========== بخش جدید: جستجوی کاربران ==========
        if current_state == "admin_search_users":
            return await handle_user_search_result(chat_id, user_id, text)

        # ========== بخش جدید: جستجوی پیشرفته ==========
        if current_state in ["admin_adv_search_state", "adv_search_state"]:
            from .advanced_search import handle_adv_search_message
            return await handle_adv_search_message(chat_id, user_id, text)

        # ========== بخش جدید: فیلترهای پیشرفته ==========
        if state_info.get("filter_state"):
            return await handle_filter_message(chat_id, user_id, text)

        # ========== بخش جدید: ساخت الگو ==========
        if current_state and current_state.startswith("admin_template_"):
            from .templates import handle_template_message
            return await handle_template_message(chat_id, user_id, text)

        # ========== بخش جدید: آمار - تاریخ سفارشی ==========
        if current_state == "awaiting_start_date" or current_state == "awaiting_end_date":
            from .analytics import handle_analytics_date_message
            return await handle_analytics_date_message(chat_id, user_id, text)

        # ========== پیام پیش‌فرض ==========
        # اگر هیچ وضعیت مدیریتی مطابقت نداشت، False برگردانید تا سایر بخش‌ها (داینامیک) پیام را پردازش کنند
        logger.debug(f"هیچ وضعیت مدیریتی برای کاربر {user_id} با وضعیت {current_state} یافت نشد.")
        return False

    except Exception as e:
        # ثبت خطا در دیتابیس با traceback کامل
        log_callback_error(
            f"Error in handle_admin_message: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id if 'user_id' in locals() else None,
            chat_id=chat_id if 'chat_id' in locals() else None
        )
        # ارسال پیام خطا به کاربر
        try:
            await send_message(chat_id, f"❌ خطای سیستمی: {str(e)}")
        except Exception:
            pass
        # در صورت خطا، True برگردانید تا از پردازش بیشتر جلوگیری شود
        return True