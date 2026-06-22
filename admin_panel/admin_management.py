# admin_panel/admin_management.py
# مدیریت کامل ادمین‌ها در پنل مدیریت - نسخه کامل با تمام قابلیت‌ها
# پشتیبانی از جستجو، آمار، صفحه‌بندی و مدیریت نقش‌ها
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states, OWNER_ID
from database import (
    get_all_admins,
    add_admin,
    remove_admin,
    update_admin_role,
    toggle_admin_status,
    get_admin_stats,
    search_admins,
    is_admin,
    get_db_connection,
    get_user,
)
from keyboards import admin_main_keyboard
from keyboards.kb_admin_common import (
    admin_admins_list_keyboard,
    admin_admin_detail_keyboard,
    admin_roles_keyboard,
    admin_add_admin_roles_keyboard,
    admin_remove_confirm_keyboard,
    admin_search_keyboard,
    admin_stats_keyboard,
)
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error,
    log_security_error
)


# ==================== ابزارهای کمکی ====================

def _is_owner(user_id):
    """بررسی آیا کاربر OWNER_ID است"""
    return user_id == OWNER_ID


def _get_role_label(role):
    """دریافت برچسب فارسی نقش"""
    labels = {
        'owner': '👑 مالک',
        'admin': '🛡️ ادمین',
        'manager': '📋 مدیر',
        'observer': '👁️ ناظر'
    }
    return labels.get(role, role)


def _get_status_label(is_active):
    """دریافت برچسب فارسی وضعیت"""
    return "🟢 فعال" if is_active == 1 else "🔴 غیرفعال"


def _admin_exists(user_id):
    """
    بررسی وجود ادمین در دیتابیس (صرف‌نظر از وضعیت فعال/غیرفعال)
    با یک کوئری مستقیم که فقط وجود رکورد را چک می‌کند
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        log_database_error(
            f"Error in _admin_exists for user {user_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id
        )
        return False


def _get_user_display_name(user_id):
    """دریافت نام قابل نمایش کاربر"""
    try:
        user = get_user(user_id)
        if user:
            return user.get('first_name') or user.get('username') or str(user_id)
        return str(user_id)
    except Exception as e:
        log_database_error(
            f"Error in _get_user_display_name for user {user_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id
        )
        return str(user_id)


# ==================== توابع اصلی مدیریت ادمین‌ها ====================

async def handle_admin_management(chat_id, user_id, page=0):
    """
    نمایش لیست ادمین‌ها با صفحه‌بندی
    """
    try:
        # بررسی دسترسی (فقط OWNER_ID)
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات (OWNER) دسترسی به مدیریت ادمین‌ها دارد.")
            return True

        # دریافت لیست ادمین‌ها
        all_admins = get_all_admins()
        total = len(all_admins)
        per_page = 5

        # صفحه‌بندی
        start = page * per_page
        end = min(start + per_page, total)
        admins = all_admins[start:end]

        # افزودن نام کاربر به اطلاعات ادمین‌ها
        for admin in admins:
            admin['display_name'] = _get_user_display_name(admin['user_id'])

        # ساخت کیبورد
        keyboard = admin_admins_list_keyboard(admins, page, per_page, total)

        # پیام
        msg = "👥 **مدیریت ادمین‌ها**\n\n"
        msg += f"📊 تعداد کل: {total} نفر\n"
        msg += "برای مشاهده جزئیات هر ادمین کلیک کنید:\n"

        await send_message(chat_id, msg, keyboard)
        logger.info(f"لیست ادمین‌ها برای کاربر {user_id} نمایش داده شد. صفحه {page+1}")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_admin_management: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست ادمین‌ها.")
        return True


async def handle_admin_detail(chat_id, user_id, data):
    """
    نمایش جزئیات یک ادمین خاص
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # استخراج user_id از دیتا
        parts = data.split("_")
        if len(parts) < 4:
            await send_message(chat_id, "❌ شناسه ادمین نامعتبر.")
            return True

        target_user_id = int(parts[3])

        # دریافت اطلاعات ادمین
        all_admins = get_all_admins()
        target_admin = None
        for admin in all_admins:
            if admin['user_id'] == target_user_id:
                target_admin = admin
                break

        if not target_admin:
            await send_message(chat_id, "❌ ادمین یافت نشد.")
            return True

        # ساخت پیام
        role = target_admin.get('role', 'admin')
        is_active = target_admin.get('is_active', 1)
        added_at = target_admin.get('added_at', 'نامشخص')
        display_name = _get_user_display_name(target_user_id)

        msg = f"👤 **جزئیات ادمین**\n\n"
        msg += f"🆔 شناسه: {target_user_id}\n"
        msg += f"📛 نام: {display_name}\n"
        msg += f"🎯 نقش: {_get_role_label(role)}\n"
        msg += f"📌 وضعیت: {_get_status_label(is_active)}\n"
        msg += f"📅 تاریخ افزودن: {added_at}\n"

        # کیبورد
        is_owner = _is_owner(target_user_id)
        keyboard = admin_admin_detail_keyboard(target_user_id, role, is_active, is_owner)

        await send_message(chat_id, msg, keyboard)
        logger.info(f"جزئیات ادمین {target_user_id} برای کاربر {user_id} نمایش داده شد.")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_admin_detail: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات ادمین.")
        return True


async def handle_add_admin_start(chat_id, user_id):
    """
    شروع فرآیند افزودن ادمین جدید
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        user_states[user_id] = {"state": "admin_add_admin"}
        await send_message(chat_id, "➕ **افزودن ادمین جدید**\n\nلطفاً شناسه کاربری (user_id) را وارد کنید:\n(مثال: 123456789)\n\nبرای انصراف، /cancel را ارسال کنید.")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_add_admin_start: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع افزودن ادمین.")
        return True


async def handle_add_admin_role(chat_id, user_id, data):
    """
    انتخاب نقش برای ادمین جدید
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # استخراج user_id از دیتا
        parts = data.split("_")
        if len(parts) < 5:
            await send_message(chat_id, "❌ شناسه نامعتبر.")
            return True

        target_user_id = int(parts[4])
        role = parts[5] if len(parts) > 5 else 'admin'

        # بررسی نقش مجاز
        if role not in ['admin', 'manager', 'observer']:
            role = 'admin'

        # بررسی اینکه آیا کاربر از قبل ادمین است (حتی غیرفعال)
        if _admin_exists(target_user_id):
            await send_message(chat_id, f"⚠️ کاربر {target_user_id} از قبل در لیست ادمین‌ها وجود دارد.")
            user_states[user_id] = {"state": "main"}
            await handle_admin_management(chat_id, user_id, 0)
            return True

        # بررسی وجود کاربر
        user = get_user(target_user_id)
        if not user:
            await send_message(chat_id, f"⚠️ کاربر {target_user_id} در دیتابیس یافت نشد. آیا این شناسه معتبر است؟")
            return True

        # افزودن ادمین
        success = add_admin(target_user_id, role)

        if success:
            await send_message(chat_id, f"✅ ادمین {target_user_id} با نقش «{_get_role_label(role)}» با موفقیت اضافه شد.")
        else:
            await send_message(chat_id, f"❌ خطا در افزودن ادمین {target_user_id}.")

        user_states[user_id] = {"state": "main"}
        # بازگشت به لیست ادمین‌ها
        await handle_admin_management(chat_id, user_id, 0)
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_add_admin_role: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در افزودن ادمین.")
        return True


async def handle_remove_admin(chat_id, user_id, data):
    """
    نمایش تایید حذف ادمین
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # استخراج user_id از دیتا
        parts = data.split("_")
        if len(parts) < 4:
            await send_message(chat_id, "❌ شناسه ادمین نامعتبر.")
            return True

        target_user_id = int(parts[3])

        # بررسی اینکه آیا OWNER_ID است
        if _is_owner(target_user_id):
            await send_message(chat_id, "⚠️ نمی‌توانید OWNER_ID را حذف کنید.")
            return True

        # بررسی وجود ادمین (حتی غیرفعال)
        if not _admin_exists(target_user_id):
            await send_message(chat_id, f"❌ کاربر {target_user_id} در لیست ادمین‌ها وجود ندارد.")
            return True

        display_name = _get_user_display_name(target_user_id)

        # نمایش تایید
        keyboard = admin_remove_confirm_keyboard(target_user_id, display_name)
        await send_message(chat_id, f"⚠️ **هشدار حذف ادمین**\n\nآیا از حذف ادمین `{display_name}` (شناسه: {target_user_id}) مطمئن هستید؟", keyboard)
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_remove_admin: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع حذف ادمین.")
        return True


async def handle_remove_admin_confirm(chat_id, user_id, data):
    """
    تایید نهایی حذف ادمین
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # استخراج user_id از دیتا
        parts = data.split("_")
        if len(parts) < 4:
            await send_message(chat_id, "❌ شناسه ادمین نامعتبر.")
            return True

        target_user_id = int(parts[3])

        # بررسی اینکه آیا OWNER_ID است
        if _is_owner(target_user_id):
            await send_message(chat_id, "⚠️ نمی‌توانید OWNER_ID را حذف کنید.")
            return True

        # بررسی وجود ادمین (حتی غیرفعال)
        if not _admin_exists(target_user_id):
            await send_message(chat_id, f"❌ کاربر {target_user_id} در لیست ادمین‌ها وجود ندارد.")
            return True

        # حذف ادمین
        success = remove_admin(target_user_id)

        if success:
            display_name = _get_user_display_name(target_user_id)
            await send_message(chat_id, f"✅ ادمین {display_name} (شناسه: {target_user_id}) با موفقیت حذف شد.")
        else:
            await send_message(chat_id, f"❌ خطا در حذف ادمین {target_user_id}.")

        # بازگشت به لیست ادمین‌ها
        await handle_admin_management(chat_id, user_id, 0)
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_remove_admin_confirm: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف ادمین.")
        return True


async def handle_change_role(chat_id, user_id, data):
    """
    شروع فرآیند تغییر نقش ادمین
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # استخراج user_id از دیتا
        parts = data.split("_")
        if len(parts) < 4:
            await send_message(chat_id, "❌ شناسه ادمین نامعتبر.")
            return True

        target_user_id = int(parts[3])

        # بررسی اینکه آیا OWNER_ID است
        if _is_owner(target_user_id):
            await send_message(chat_id, "⚠️ نمی‌توانید نقش OWNER_ID را تغییر دهید.")
            return True

        # بررسی وجود ادمین (حتی غیرفعال)
        if not _admin_exists(target_user_id):
            await send_message(chat_id, f"❌ کاربر {target_user_id} در لیست ادمین‌ها وجود ندارد.")
            return True

        # دریافت نقش فعلی
        all_admins = get_all_admins()
        target_admin = None
        for admin in all_admins:
            if admin['user_id'] == target_user_id:
                target_admin = admin
                break

        if not target_admin:
            await send_message(chat_id, "❌ ادمین یافت نشد.")
            return True

        current_role = target_admin.get('role', 'admin')
        keyboard = admin_roles_keyboard(target_user_id, current_role)
        await send_message(chat_id, f"🔄 **تغییر نقش ادمین**\n\nنقش فعلی: {_get_role_label(current_role)}\nنقش جدید را انتخاب کنید:", keyboard)
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_change_role: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع تغییر نقش.")
        return True


async def handle_change_role_select(chat_id, user_id, data):
    """
    انتخاب و اعمال نقش جدید
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # استخراج اطلاعات از دیتا
        parts = data.split("_")
        if len(parts) < 6:
            await send_message(chat_id, "❌ اطلاعات نامعتبر.")
            return True

        target_user_id = int(parts[4])
        new_role = parts[5]

        # بررسی اینکه آیا OWNER_ID است
        if _is_owner(target_user_id):
            await send_message(chat_id, "⚠️ نمی‌توانید نقش OWNER_ID را تغییر دهید.")
            return True

        # بررسی نقش مجاز
        if new_role not in ['admin', 'manager', 'observer']:
            await send_message(chat_id, "❌ نقش نامعتبر.")
            return True

        # بررسی وجود ادمین (حتی غیرفعال)
        if not _admin_exists(target_user_id):
            await send_message(chat_id, f"❌ کاربر {target_user_id} در لیست ادمین‌ها وجود ندارد.")
            return True

        # تغییر نقش
        success = update_admin_role(target_user_id, new_role)

        if success:
            await send_message(chat_id, f"✅ نقش ادمین {_get_user_display_name(target_user_id)} به «{_get_role_label(new_role)}» تغییر یافت.")
        else:
            await send_message(chat_id, f"❌ خطا در تغییر نقش ادمین {target_user_id}.")

        # بازگشت به جزئیات ادمین
        await handle_admin_detail(chat_id, user_id, f"admin_admin_detail_{target_user_id}")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_change_role_select: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر نقش.")
        return True


async def handle_toggle_admin_status(chat_id, user_id, data):
    """
    فعال/غیرفعال‌سازی ادمین
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # استخراج user_id از دیتا
        parts = data.split("_")
        if len(parts) < 4:
            await send_message(chat_id, "❌ شناسه ادمین نامعتبر.")
            return True

        target_user_id = int(parts[3])

        # بررسی اینکه آیا OWNER_ID است
        if _is_owner(target_user_id):
            await send_message(chat_id, "⚠️ نمی‌توانید وضعیت OWNER_ID را تغییر دهید.")
            return True

        # بررسی وجود ادمین (حتی غیرفعال)
        if not _admin_exists(target_user_id):
            await send_message(chat_id, f"❌ کاربر {target_user_id} در لیست ادمین‌ها وجود ندارد.")
            return True

        # تغییر وضعیت
        success, new_status = toggle_admin_status(target_user_id)

        if success:
            status_text = "فعال" if new_status == 1 else "غیرفعال"
            await send_message(chat_id, f"✅ وضعیت ادمین {_get_user_display_name(target_user_id)} به «{status_text}» تغییر یافت.")
        else:
            await send_message(chat_id, f"❌ خطا در تغییر وضعیت ادمین {target_user_id}.")

        # بازگشت به جزئیات ادمین
        await handle_admin_detail(chat_id, user_id, f"admin_admin_detail_{target_user_id}")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_toggle_admin_status: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر وضعیت ادمین.")
        return True


async def handle_search_admin(chat_id, user_id):
    """
    شروع فرآیند جستجوی ادمین
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        user_states[user_id] = {"state": "admin_search_admin"}
        await send_message(chat_id, "🔍 **جستجوی ادمین‌ها**\n\nلطفاً کلمه کلیدی مورد نظر را وارد کنید:\n(شناسه کاربری یا نقش)\n\nبرای انصراف، /cancel را ارسال کنید.")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_search_admin: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع جستجو.")
        return True


async def handle_search_admin_result(chat_id, user_id, keyword):
    """
    نمایش نتایج جستجو
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        if not keyword or keyword.strip() == "":
            await send_message(chat_id, "❌ لطفاً یک کلمه کلیدی معتبر وارد کنید.")
            return True

        # جستجو
        results = search_admins(keyword.strip())

        if not results:
            await send_message(chat_id, f"❌ هیچ ادمینی با عبارت «{keyword}» یافت نشد.")
            user_states[user_id] = {"state": "main"}
            return True

        # ساخت پیام نتایج
        msg = f"🔍 **نتایج جستجو برای «{keyword}»**\n\n"
        msg += f"تعداد: {len(results)} نفر\n\n"

        for admin in results:
            user_id_found = admin['user_id']
            role = admin.get('role', 'admin')
            is_active = admin.get('is_active', 1)
            status_icon = "🟢" if is_active == 1 else "🔴"
            display_name = _get_user_display_name(user_id_found)
            msg += f"{status_icon} {display_name} (شناسه: {user_id_found}) - {_get_role_label(role)}\n"

        # دکمه بازگشت
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 برگشت به لیست ادمین‌ها", "callback_data": "admin_manage_admins"}]
            ]
        }

        await send_message(chat_id, msg, keyboard)
        user_states[user_id] = {"state": "main"}
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_search_admin_result: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجو.")
        user_states[user_id] = {"state": "main"}
        return True


async def handle_admin_stats(chat_id, user_id):
    """
    نمایش آمار ادمین‌ها
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # دریافت آمار
        stats = get_admin_stats()

        # ساخت کیبورد آمار
        keyboard = admin_stats_keyboard(stats)

        # پیام
        msg = "📊 **آمار ادمین‌ها**\n\n"
        msg += f"👥 کل: {stats.get('total', 0)}\n"
        msg += f"🟢 فعال: {stats.get('active', 0)}\n"
        msg += f"🔴 غیرفعال: {stats.get('inactive', 0)}\n\n"
        msg += "📌 تفکیک نقش‌ها:\n"

        roles = stats.get('roles', {})
        role_labels = {
            'owner': '👑 مالک',
            'admin': '🛡️ ادمین',
            'manager': '📋 مدیر',
            'observer': '👁️ ناظر'
        }
        for role, count in roles.items():
            label = role_labels.get(role, role)
            msg += f"  {label}: {count}\n"

        await send_message(chat_id, msg, keyboard)
        logger.info(f"آمار ادمین‌ها برای کاربر {user_id} نمایش داده شد.")
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_admin_stats: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش آمار.")
        return True


async def handle_admins_page(chat_id, user_id, data):
    """
    صفحه‌بندی لیست ادمین‌ها
    """
    try:
        # بررسی دسترسی
        if not _is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True

        # استخراج شماره صفحه
        parts = data.split("_")
        if len(parts) < 4:
            page = 0
        else:
            try:
                page = int(parts[3])
            except ValueError:
                page = 0

        # نمایش لیست با صفحه جدید
        await handle_admin_management(chat_id, user_id, page)
        return True

    except Exception as e:
        log_callback_error(
            f"Error in handle_admins_page: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی.")
        return True


# ==================== توابع کمکی برای پنل مدیریت ====================

async def handle_admin_management_from_callback(chat_id, user_id):
    """نمایش لیست ادمین‌ها (برای فراخوانی از کالبک)"""
    return await handle_admin_management(chat_id, user_id, 0)


def get_admin_management_keyboard():
    """دریافت کیبورد مدیریت ادمین‌ها (برای استفاده در بخش‌های دیگر)"""
    return admin_admins_list_keyboard([], 0, 5, 0)


__all__ = [
    'handle_admin_management',
    'handle_admin_detail',
    'handle_add_admin_start',
    'handle_add_admin_role',
    'handle_remove_admin',
    'handle_remove_admin_confirm',
    'handle_change_role',
    'handle_change_role_select',
    'handle_toggle_admin_status',
    'handle_search_admin',
    'handle_search_admin_result',
    'handle_admin_stats',
    'handle_admins_page',
    'handle_admin_management_from_callback',
    'get_admin_management_keyboard',
]