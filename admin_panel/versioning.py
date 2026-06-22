# admin_panel/versioning.py
# مدیریت نسخه‌سازی (Versioning) و بازگردانی (Rollback) دکمه‌ها
# امکان ذخیره‌ی اسنپ‌شات از دکمه‌ها و بازگشت به نسخه‌های قبلی
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, OWNER_ID
from database import (
    get_button_by_id,
    get_all_buttons,
    save_button_version,
    get_button_versions,
    get_button_version,
    get_latest_version,
    get_total_versions,
    restore_button_version,
    delete_button_version,
    delete_old_versions
)
from keyboards import admin_main_keyboard
from services.permission_service import get_permission_service
from services.state_service import get_state_service
from utils import format_datetime
from utils.error_handler import (
    log_callback_error,
    log_database_error,
    log_general_error,
    log_security_error
)


# ==================== توابع کمکی ====================

def _is_owner(user_id):
    """بررسی آیا کاربر OWNER_ID است"""
    return user_id == OWNER_ID


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


# ==================== کیبوردها ====================

def versioning_main_keyboard():
    """کیبورد اصلی بخش نسخه‌سازی"""
    return {
        "inline_keyboard": [
            [{"text": "📋 لیست نسخه‌های یک دکمه", "callback_data": "admin_version_list"}],
            [{"text": "💾 ذخیره نسخه جدید", "callback_data": "admin_version_save"}],
            [{"text": "🗑️ پاکسازی نسخه‌های قدیمی", "callback_data": "admin_version_cleanup"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


def version_button_select_keyboard():
    """کیبورد انتخاب دکمه برای مدیریت نسخه‌ها"""
    try:
        buttons = get_all_buttons()
        keyboard = []
        
        if not buttons:
            keyboard.append([{"text": "❌ هیچ دکمه‌ای یافت نشد", "callback_data": "admin_none"}])
        else:
            for btn in buttons:
                icon = "📂" if btn.get('has_submenu', 0) == 1 else "🔘"
                # نمایش تعداد نسخه‌ها در کنار نام
                version_count = get_total_versions(btn['id'])
                version_badge = f" ({version_count})" if version_count > 0 else ""
                keyboard.append([
                    {"text": f"{icon} {btn['name']}{version_badge}", 
                     "callback_data": f"admin_version_btn_{btn['id']}"}
                ])
        
        keyboard.append([{"text": "🔙 برگشت به نسخه‌سازی", "callback_data": "admin_version"}])
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in version_button_select_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری دکمه‌ها", "callback_data": "admin_version"}]]}


def version_list_keyboard(versions, button_id, page=0, per_page=5, total=0):
    """
    کیبورد نمایش لیست نسخه‌های یک دکمه با صفحه‌بندی
    """
    try:
        keyboard = []
        
        if not versions:
            keyboard.append([{"text": "❌ هیچ نسخه‌ای برای این دکمه یافت نشد", "callback_data": "admin_none"}])
            keyboard.append([
                {"text": "💾 ذخیره نسخه جدید", "callback_data": f"admin_version_save_btn_{button_id}"}
            ])
        else:
            for version in versions:
                version_number = version.get('version_number', '?')
                created_by = version.get('created_by', 'نامشخص')
                created_at = format_datetime(version.get('created_at'))
                note = version.get('note', '')
                
                # نمایش مختصر یادداشت
                note_display = f" - {note[:20]}" if note else ""
                
                keyboard.append([
                    {"text": f"📌 نسخه {version_number} (توسط {created_by}){note_display}",
                     "callback_data": f"admin_version_detail_{button_id}_{version_number}"}
                ])
        
        # دکمه‌های صفحه‌بندی
        nav_row = []
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_version_list_page_{button_id}_{page-1}"})
        if page < total_pages - 1:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_version_list_page_{button_id}_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)
        
        # دکمه‌های عملیاتی
        if versions:
            keyboard.append([
                {"text": "💾 ذخیره نسخه جدید", "callback_data": f"admin_version_save_btn_{button_id}"}
            ])
        
        keyboard.append([
            {"text": "🔙 برگشت به لیست دکمه‌ها", "callback_data": "admin_version_list"}
        ])
        keyboard.append([
            {"text": "🔙 برگشت به منوی نسخه‌سازی", "callback_data": "admin_version"}
        ])
        
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in version_list_keyboard: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری نسخه‌ها", "callback_data": "admin_version"}]]}


def version_detail_keyboard(button_id, version_number):
    """کیبورد جزئیات یک نسخه با گزینه‌های بازیابی و حذف"""
    return {
        "inline_keyboard": [
            [{"text": "🔄 بازگردانی به این نسخه", "callback_data": f"admin_version_restore_{button_id}_{version_number}"}],
            [{"text": "🗑️ حذف این نسخه", "callback_data": f"admin_version_delete_{button_id}_{version_number}"}],
            [{"text": "🔙 برگشت به لیست نسخه‌ها", "callback_data": f"admin_version_list_btn_{button_id}"}],
            [{"text": "🔙 برگشت به منوی نسخه‌سازی", "callback_data": "admin_version"}]
        ]
    }


def version_restore_confirm_keyboard(button_id, version_number):
    """کیبورد تایید بازگردانی به نسخه‌ی مشخص"""
    return {
        "inline_keyboard": [
            [{"text": f"⚠️ آیا از بازگردانی دکمه به نسخه {version_number} مطمئن هستید؟"}],
            [{"text": "⚠️ این عملیات تمام تغییرات فعلی را بازنویسی می‌کند!"}],
            [{"text": "✅ بله، بازگردانی شود", "callback_data": f"admin_version_restore_confirm_{button_id}_{version_number}"}],
            [{"text": "❌ خیر، انصراف", "callback_data": f"admin_version_detail_{button_id}_{version_number}"}]
        ]
    }


def version_save_note_keyboard(button_id):
    """کیبورد درخواست یادداشت برای نسخه‌ی جدید"""
    return {
        "inline_keyboard": [
            [{"text": "📝 لطفاً توضیحی برای این نسخه وارد کنید (اختیاری):"}],
            [{"text": "⏭️ بدون توضیح", "callback_data": f"admin_version_save_skip_{button_id}"}],
            [{"text": "🔙 انصراف", "callback_data": f"admin_version_list_btn_{button_id}"}]
        ]
    }


# ==================== هندلر اصلی ====================

async def handle_versioning(chat_id, user_id):
    """
    نمایش منوی اصلی بخش نسخه‌سازی
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        # آمار سریع
        total_buttons = len(get_all_buttons())
        
        await send_message(
            chat_id,
            "📦 **مدیریت نسخه‌سازی (Versioning)**\n\n"
            "از این بخش می‌توانید:\n"
            "• از دکمه‌ها نسخه‌برداری (Snapshot) کنید\n"
            "• لیست نسخه‌های هر دکمه را مشاهده کنید\n"
            "• در صورت نیاز، به نسخه‌های قبلی بازگردید (Rollback)\n"
            "• نسخه‌های قدیمی را پاکسازی کنید\n\n"
            f"📊 تعداد کل دکمه‌ها: {total_buttons}\n\n"
            "⚠️ **توجه:** بازگردانی به نسخه‌ی قبلی، تمام تغییرات فعلی دکمه را بازنویسی می‌کند!",
            versioning_main_keyboard()
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_versioning: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش صفحه نسخه‌سازی.")
        return True


# ==================== لیست دکمه‌ها برای نسخه‌سازی ====================

async def handle_version_list(chat_id, user_id):
    """
    نمایش لیست دکمه‌ها برای انتخاب و مشاهده‌ی نسخه‌ها
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        keyboard = version_button_select_keyboard()
        await send_message(
            chat_id,
            "🔘 **انتخاب دکمه برای مدیریت نسخه‌ها**\n\n"
            "عدد داخل پرانتز تعداد نسخه‌های ثبت‌شده را نشان می‌دهد.\n"
            "لطفاً دکمه‌ی مورد نظر را انتخاب کنید:",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_list: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست دکمه‌ها.")
        return True


# ==================== لیست نسخه‌های یک دکمه ====================

async def handle_version_list_btn(chat_id, user_id, data):
    """
    نمایش لیست نسخه‌های یک دکمه خاص (admin_version_list_btn_<button_id>)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        button_id = int(data.split("_")[-1])
        await _show_version_list(chat_id, user_id, button_id, 0)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_list_btn: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست نسخه‌ها.")
        return True


async def handle_version_list_page(chat_id, user_id, data):
    """
    صفحه‌بندی لیست نسخه‌ها (admin_version_list_page_<button_id>_<page>)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        parts = data.split("_")
        button_id = int(parts[4])
        page = int(parts[5]) if len(parts) > 5 else 0
        
        await _show_version_list(chat_id, user_id, button_id, page)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_list_page: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی.")
        return True


async def _show_version_list(chat_id, user_id, button_id, page):
    """
    تابع کمکی برای نمایش لیست نسخه‌ها با صفحه‌بندی
    """
    try:
        button_name = _get_button_name(button_id)
        per_page = 5
        
        versions = get_button_versions(button_id, limit=per_page, offset=page * per_page)
        total = get_total_versions(button_id)
        
        keyboard = version_list_keyboard(versions, button_id, page, per_page, total)
        
        msg = f"📋 **نسخه‌های دکمه: {button_name}**\n\n"
        msg += f"تعداد کل نسخه‌ها: {total}\n"
        msg += f"صفحه‌ی {page + 1} از {((total + per_page - 1) // per_page) if total > 0 else 1}\n\n"
        
        if not versions:
            msg += "هنوز هیچ نسخه‌ای برای این دکمه ذخیره نشده است.\n"
            msg += "از گزینه‌ی «ذخیره نسخه جدید» استفاده کنید."
        else:
            msg += "برای مشاهده‌ی جزئیات هر نسخه کلیک کنید:"
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in _show_version_list for button {button_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش لیست نسخه‌ها.")
        return True


# ==================== ذخیره نسخه جدید ====================

async def handle_version_save(chat_id, user_id):
    """
    شروع فرآیند ذخیره نسخه جدید - نمایش لیست دکمه‌ها
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        keyboard = version_button_select_keyboard()
        await send_message(
            chat_id,
            "💾 **ذخیره نسخه جدید**\n\n"
            "لطفاً دکمه‌ای که می‌خواهید از آن نسخه بگیرید را انتخاب کنید:",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_save: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع ذخیره نسخه.")
        return True


async def handle_version_save_btn(chat_id, user_id, data):
    """
    انتخاب دکمه برای ذخیره نسخه (admin_version_save_btn_<button_id>)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        button_id = int(data.split("_")[-1])
        button_name = _get_button_name(button_id)
        
        # ذخیره در state_service
        state_service = get_state_service()
        await state_service.update_state(user_id, {
            "state": "admin_version_save_note",
            "version_button_id": button_id
        })
        
        keyboard = version_save_note_keyboard(button_id)
        await send_message(
            chat_id,
            f"💾 **ذخیره نسخه‌ی جدید برای دکمه: {button_name}**\n\n"
            f"لطفاً توضیحی برای این نسخه وارد کنید (اختیاری):\n"
            f"(مثلاً: «اصلاح اعتبارسنجی» یا «افزودن سوال جدید»)\n\n"
            f"برای ادامه بدون توضیح، روی دکمه‌ی «بدون توضیح» کلیک کنید.",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_save_btn: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب دکمه.")
        return True


async def handle_version_save_skip(chat_id, user_id, data):
    """
    ذخیره نسخه بدون یادداشت (admin_version_save_skip_<button_id>)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        button_id = int(data.split("_")[-1])
        return await _save_version(chat_id, user_id, button_id, None)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_save_skip: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ذخیره نسخه.")
        return True


async def handle_version_save_note(chat_id, user_id, text):
    """
    ذخیره نسخه با یادداشت (از msg_admin صدا زده می‌شود)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        state_service = get_state_service()
        state_info = await state_service.get_state(user_id, {})
        button_id = state_info.get("version_button_id")
        
        if not button_id:
            await send_message(chat_id, "❌ خطا: شناسه دکمه یافت نشد.")
            await state_service.set_state(user_id, {"state": "main"})
            return True
        
        return await _save_version(chat_id, user_id, button_id, text.strip() if text else None)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_save_note: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ذخیره نسخه.")
        await state_service.set_state(user_id, {"state": "main"})
        return True


async def _save_version(chat_id, user_id, button_id, note):
    """
    تابع کمکی برای ذخیره نسخه
    """
    try:
        button_name = _get_button_name(button_id)
        
        # ذخیره نسخه
        success, version_number = save_button_version(button_id, user_id, note)
        
        if success:
            await send_message(
                chat_id,
                f"✅ نسخه‌ی جدید برای دکمه «{button_name}» با موفقیت ذخیره شد.\n\n"
                f"📌 شماره نسخه: {version_number}\n"
                f"📝 یادداشت: {note if note else 'بدون توضیح'}\n"
                f"👤 ذخیره‌کننده: {user_id}",
                {
                    "inline_keyboard": [
                        [{"text": "📋 مشاهده نسخه‌ها", "callback_data": f"admin_version_list_btn_{button_id}"}],
                        [{"text": "🔙 برگشت به منوی نسخه‌سازی", "callback_data": "admin_version"}]
                    ]
                }
            )
            logger.info(f"✅ نسخه {version_number} برای دکمه {button_id} توسط کاربر {user_id} ذخیره شد.")
        else:
            await send_message(
                chat_id,
                f"❌ خطا در ذخیره نسخه برای دکمه «{button_name}».\n"
                f"لطفاً دوباره تلاش کنید.",
                versioning_main_keyboard()
            )
        
        state_service = get_state_service()
        await state_service.set_state(user_id, {"state": "main"})
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in _save_version for button {button_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ذخیره نسخه.")
        await get_state_service().set_state(user_id, {"state": "main"})
        return True


# ==================== جزئیات نسخه ====================

async def handle_version_detail(chat_id, user_id, data):
    """
    نمایش جزئیات یک نسخه (admin_version_detail_<button_id>_<version_number>)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        parts = data.split("_")
        button_id = int(parts[3])
        version_number = int(parts[4])
        
        version = get_button_version(button_id, version_number)
        if not version:
            await send_message(chat_id, "❌ نسخه یافت نشد.")
            return True
        
        button_name = _get_button_name(button_id)
        snapshot = version.get('snapshot_data', {})
        
        # اطلاعات نسخه
        created_by = version.get('created_by', 'نامشخص')
        created_at = format_datetime(version.get('created_at'))
        note = version.get('note', 'بدون توضیح')
        
        # آمار نسخه
        questions_count = len(snapshot.get('questions', []))
        
        # اطلاعات دکمه در نسخه
        btn_data = snapshot.get('button', {})
        btn_name = btn_data.get('name', 'نامشخص')
        has_payment = "✅" if btn_data.get('has_payment', 0) == 1 else "❌"
        price = btn_data.get('price_amount', 0)
        has_submenu = "✅" if btn_data.get('has_submenu', 0) == 1 else "❌"
        is_active = "✅" if btn_data.get('is_active', 0) == 1 else "❌"
        
        msg = f"📌 **جزئیات نسخه {version_number}**\n\n"
        msg += f"🔘 **دکمه:** {button_name}\n"
        msg += f"📛 **نام در نسخه:** {btn_name}\n"
        msg += f"👤 **ایجادکننده:** {created_by}\n"
        msg += f"📅 **تاریخ ایجاد:** {created_at}\n"
        msg += f"📝 **یادداشت:** {note}\n\n"
        
        msg += f"⚙️ **تنظیمات دکمه در این نسخه:**\n"
        msg += f"  • وضعیت: {is_active}\n"
        msg += f"  • زیرمنو: {has_submenu}\n"
        msg += f"  • پرداخت: {has_payment}\n"
        if has_payment == "✅":
            msg += f"  • مبلغ: {price:,} ریال\n"
        msg += f"  • تعداد سوالات: {questions_count}\n"
        
        # نمایش چند سوال اول
        if questions_count > 0:
            msg += f"\n📝 **سوالات (نمایش {min(3, questions_count)} مورد اول):**\n"
            for i, q in enumerate(snapshot.get('questions', [])[:3]):
                q_text = q.get('data', {}).get('question_text', 'بدون متن')
                msg += f"  {i+1}. {q_text[:40]}\n"
            if questions_count > 3:
                msg += f"  ... و {questions_count - 3} سوال دیگر\n"
        
        keyboard = version_detail_keyboard(button_id, version_number)
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_detail: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات نسخه.")
        return True


# ==================== بازگردانی (Rollback) ====================

async def handle_version_restore(chat_id, user_id, data):
    """
    نمایش تاییدیه بازگردانی به نسخه (admin_version_restore_<button_id>_<version_number>)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        parts = data.split("_")
        button_id = int(parts[3])
        version_number = int(parts[4])
        
        button_name = _get_button_name(button_id)
        
        keyboard = version_restore_confirm_keyboard(button_id, version_number)
        await send_message(
            chat_id,
            f"🔄 **بازگردانی دکمه به نسخه‌ی قبلی**\n\n"
            f"🔘 **دکمه:** {button_name}\n"
            f"📌 **نسخه‌ی مقصد:** {version_number}\n\n"
            f"⚠️ **هشدار!**\n"
            f"بازگردانی، تمام تغییرات فعلی دکمه را بازنویسی می‌کند.\n"
            f"قبل از بازگردانی، یک نسخه‌ی خودکار از وضعیت فعلی ذخیره می‌شود.\n\n"
            f"آیا مطمئن هستید؟",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_restore: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع بازگردانی.")
        return True


async def handle_version_restore_confirm(chat_id, user_id, data):
    """
    اجرای بازگردانی به نسخه (admin_version_restore_confirm_<button_id>_<version_number>)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        parts = data.split("_")
        button_id = int(parts[4])
        version_number = int(parts[5])
        
        button_name = _get_button_name(button_id)
        
        # اجرای بازگردانی
        success = restore_button_version(button_id, version_number, user_id)
        
        if success:
            await send_message(
                chat_id,
                f"✅ دکمه «{button_name}» با موفقیت به نسخه {version_number} بازگردانی شد.\n\n"
                f"📌 یک نسخه‌ی خودکار از وضعیت قبلی ذخیره شد.\n"
                f"👤 انجام‌دهنده: {user_id}",
                {
                    "inline_keyboard": [
                        [{"text": "📋 مشاهده نسخه‌ها", "callback_data": f"admin_version_list_btn_{button_id}"}],
                        [{"text": "🔙 برگشت به منوی نسخه‌سازی", "callback_data": "admin_version"}]
                    ]
                }
            )
            logger.info(f"🔄 دکمه {button_id} توسط کاربر {user_id} به نسخه {version_number} بازگردانی شد.")
        else:
            await send_message(
                chat_id,
                f"❌ خطا در بازگردانی دکمه «{button_name}» به نسخه {version_number}.",
                versioning_main_keyboard()
            )
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_restore_confirm: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در بازگردانی دکمه.")
        return True


# ==================== حذف نسخه ====================

async def handle_version_delete(chat_id, user_id, data):
    """
    حذف یک نسخه (admin_version_delete_<button_id>_<version_number>)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        parts = data.split("_")
        button_id = int(parts[3])
        version_number = int(parts[4])
        
        # دریافت نسخه برای نمایش اطلاعات
        version = get_button_version(button_id, version_number)
        if not version:
            await send_message(chat_id, "❌ نسخه یافت نشد.")
            return True
        
        version_id = version.get('id')
        
        # حذف نسخه
        success = delete_button_version(version_id)
        
        if success:
            await send_message(
                chat_id,
                f"✅ نسخه {version_number} با موفقیت حذف شد.",
                {
                    "inline_keyboard": [
                        [{"text": "📋 مشاهده نسخه‌ها", "callback_data": f"admin_version_list_btn_{button_id}"}],
                        [{"text": "🔙 برگشت به منوی نسخه‌سازی", "callback_data": "admin_version"}]
                    ]
                }
            )
        else:
            await send_message(chat_id, "❌ خطا در حذف نسخه.")
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_delete: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در حذف نسخه.")
        return True


# ==================== پاکسازی نسخه‌های قدیمی ====================

async def handle_version_cleanup(chat_id, user_id):
    """
    نمایش لیست دکمه‌ها برای پاکسازی نسخه‌های قدیمی
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        keyboard = version_button_select_keyboard()
        await send_message(
            chat_id,
            "🗑️ **پاکسازی نسخه‌های قدیمی**\n\n"
            "این عملیات نسخه‌های قدیمی‌تر از ۱۰ نسخه‌ی آخر را برای هر دکمه حذف می‌کند.\n"
            "لطفاً دکمه‌ی مورد نظر را انتخاب کنید:\n\n"
            "📌 **توجه:** فقط {نسخه‌های ۱۰ تای آخر} نگهداری می‌شوند.",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_cleanup: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش پاکسازی نسخه‌ها.")
        return True


async def handle_version_cleanup_btn(chat_id, user_id, data):
    """
    اجرای پاکسازی نسخه‌های قدیمی یک دکمه (admin_version_cleanup_btn_<button_id>)
    """
    try:
        permission_service = get_permission_service()
        if not permission_service.is_owner(user_id):
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        button_id = int(data.split("_")[-1])
        button_name = _get_button_name(button_id)
        
        # حذف نسخه‌های قدیمی (فقط ۱۰ نسخه‌ی آخر نگهداری می‌شوند)
        deleted_count = delete_old_versions(button_id, keep_count=10)
        
        if deleted_count > 0:
            await send_message(
                chat_id,
                f"✅ {deleted_count} نسخه‌ی قدیمی برای دکمه «{button_name}» حذف شدند.\n"
                f"📌 {10} نسخه‌ی آخر نگهداری شدند.",
                {
                    "inline_keyboard": [
                        [{"text": "📋 مشاهده نسخه‌ها", "callback_data": f"admin_version_list_btn_{button_id}"}],
                        [{"text": "🔙 برگشت به منوی نسخه‌سازی", "callback_data": "admin_version"}]
                    ]
                }
            )
        else:
            await send_message(
                chat_id,
                f"📊 دکمه «{button_name}» کمتر از ۱۰ نسخه دارد.\n"
                f"نیازی به پاکسازی نیست.",
                {
                    "inline_keyboard": [
                        [{"text": "📋 مشاهده نسخه‌ها", "callback_data": f"admin_version_list_btn_{button_id}"}],
                        [{"text": "🔙 برگشت به منوی نسخه‌سازی", "callback_data": "admin_version"}]
                    ]
                }
            )
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_version_cleanup_btn for {button_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در پاکسازی نسخه‌ها.")
        return True


__all__ = [
    'handle_versioning',
    'handle_version_list',
    'handle_version_list_btn',
    'handle_version_list_page',
    'handle_version_save',
    'handle_version_save_btn',
    'handle_version_save_skip',
    'handle_version_save_note',
    'handle_version_detail',
    'handle_version_restore',
    'handle_version_restore_confirm',
    'handle_version_delete',
    'handle_version_cleanup',
    'handle_version_cleanup_btn',
]