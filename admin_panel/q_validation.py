# admin_panel/q_validation.py
# مدیریت اعتبارسنجی سوالات در پنل ادمین - نسخه async با logging
# اصلاح شده با مدیریت خطا و traceback کامل

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states
from database import (
    get_question_by_id,
    update_question,
    get_validation_settings,
    toggle_validation_feature,
    enable_all_validations,
    disable_all_validations,
    reset_validation_to_default,
    get_validation_profiles,
    apply_validation_profile,
    save_validation_profile,
    get_previous_questions
)
from keyboards import admin_validation_main_keyboard, admin_validation_type_keyboard
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error
)


async def handle_question_validation(chat_id, user_id, data):
    """نمایش صفحه مدیریت اعتبارسنجی سوال (admin_q_validation_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        q = get_question_by_id(q_id)
        if not q:
            await send_message(chat_id, "❌ سوال یافت نشد.")
            return True
        
        user_states[user_id]["current_question_id"] = q_id
        settings = get_validation_settings(q_id)
        
        if not settings:
            await send_message(chat_id, "❌ تنظیمات اعتبارسنجی یافت نشد.")
            return True
        
        keyboard = admin_validation_main_keyboard(q_id, settings)
        
        msg = f"🔧 **مدیریت اعتبارسنجی سوال #{q_id}**\n\n"
        msg += f"📝 **متن سوال:** {q['question_text']}\n\n"
        msg += f"⚙️ **وضعیت کلی:**\n"
        msg += f"  🔹 اجباری: {'✅ فعال' if settings.get('is_required', 0) == 1 else '❌ غیرفعال'}\n"
        msg += f"  🔹 اعتبارسنجی: {'✅ فعال' if settings.get('validation_enabled', 0) == 1 else '❌ غیرفعال'}\n"
        msg += f"  🔹 نوع: {settings.get('validation_type', 'none')}\n\n"
        msg += f"📏 **محدودیت‌های متن:**\n"
        msg += f"  🔹 محدودیت طول: {'✅ فعال' if settings.get('length_validation_enabled', 0) == 1 else '❌ غیرفعال'}\n"
        msg += f"  🔹 محدودیت کلمه: {'✅ فعال' if settings.get('word_validation_enabled', 0) == 1 else '❌ غیرفعال'}\n\n"
        msg += f"🔢 **اعتبارسنجی عددی:**\n"
        msg += f"  🔹 {'✅ فعال' if settings.get('numeric_validation_enabled', 0) == 1 else '❌ غیرفعال'}\n\n"
        msg += f"📅 **اعتبارسنجی تاریخ:**\n"
        msg += f"  🔹 {'✅ فعال' if settings.get('date_validation_enabled', 0) == 1 else '❌ غیرفعال'}\n\n"
        msg += f"📎 **اعتبارسنجی فایل:**\n"
        msg += f"  🔹 {'✅ فعال' if settings.get('file_validation_enabled', 0) == 1 else '❌ غیرفعال'}\n"
        msg += f"  🔹 ابعاد: {'✅ فعال' if settings.get('dimensions_enabled', 0) == 1 else '❌ غیرفعال'}\n\n"
        msg += f"📐 **الگو و محتوا:**\n"
        msg += f"  🔹 الگو: {'✅ فعال' if settings.get('pattern_validation_enabled', 0) == 1 else '❌ غیرفعال'}\n"
        msg += f"  🔹 محتوا: {'✅ فعال' if settings.get('contains_validation_enabled', 0) == 1 else '❌ غیرفعال'}\n\n"
        msg += f"🔗 **پیشرفته:**\n"
        msg += f"  🔹 شرط نمایش: {'✅ فعال' if settings.get('conditional_enabled', 0) == 1 else '❌ غیرفعال'}\n"
        msg += f"  🔹 اصلاح خودکار: {'✅ فعال' if settings.get('auto_fix_enabled', 0) == 1 else '❌ غیرفعال'}"
        
        await send_message(chat_id, msg, keyboard)
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_question_validation for question {q_id}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش صفحه اعتبارسنجی.")
        return True


async def _toggle_feature(chat_id, user_id, data, feature_name):
    """تابع کمکی برای تغییر وضعیت یک قابلیت اعتبارسنجی"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        settings = get_validation_settings(q_id)
        if not settings:
            await send_message(chat_id, "❌ سوال یافت نشد.")
            return True
        
        current = settings.get(feature_name, 0)
        new_status = 0 if current == 1 else 1
        toggle_validation_feature(q_id, feature_name, new_status)
        
        status_text = "فعال" if new_status == 1 else "غیرفعال"
        logger.info(f"قابلیت {feature_name} برای سوال {q_id} به {status_text} تغییر یافت (توسط کاربر {user_id})")
        await send_message(chat_id, f"✅ {feature_name} به «{status_text}» تغییر یافت.")
        
        # بازگشت به صفحه اعتبارسنجی
        await handle_question_validation(chat_id, user_id, f"admin_q_validation_{q_id}")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in _toggle_feature for {feature_name}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر وضعیت.")
        return True


async def handle_toggle_required(chat_id, user_id, data):
    """تغییر وضعیت اجباری بودن سوال (admin_q_toggle_required_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "is_required")


async def handle_toggle_validation(chat_id, user_id, data):
    """تغییر وضعیت اعتبارسنجی کلی (admin_q_toggle_validation_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "validation_enabled")


async def handle_toggle_length(chat_id, user_id, data):
    """تغییر وضعیت محدودیت طول (admin_q_toggle_length_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "length_validation_enabled")


async def handle_toggle_words(chat_id, user_id, data):
    """تغییر وضعیت محدودیت کلمه (admin_q_toggle_words_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "word_validation_enabled")


async def handle_toggle_numeric(chat_id, user_id, data):
    """تغییر وضعیت اعتبارسنجی عددی (admin_q_toggle_numeric_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "numeric_validation_enabled")


async def handle_toggle_date(chat_id, user_id, data):
    """تغییر وضعیت اعتبارسنجی تاریخ (admin_q_toggle_date_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "date_validation_enabled")


async def handle_toggle_file(chat_id, user_id, data):
    """تغییر وضعیت اعتبارسنجی فایل (admin_q_toggle_file_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "file_validation_enabled")


async def handle_toggle_dimensions(chat_id, user_id, data):
    """تغییر وضعیت اعتبارسنجی ابعاد (admin_q_toggle_dimensions_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "dimensions_enabled")


async def handle_toggle_pattern(chat_id, user_id, data):
    """تغییر وضعیت اعتبارسنجی الگو (admin_q_toggle_pattern_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "pattern_validation_enabled")


async def handle_toggle_contains(chat_id, user_id, data):
    """تغییر وضعیت اعتبارسنجی محتوا (admin_q_toggle_contains_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "contains_validation_enabled")


async def handle_toggle_conditional(chat_id, user_id, data):
    """تغییر وضعیت شرط نمایش (admin_q_toggle_conditional_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "conditional_enabled")


async def handle_toggle_autofix(chat_id, user_id, data):
    """تغییر وضعیت اصلاح خودکار (admin_q_toggle_autofix_<question_id>)"""
    return await _toggle_feature(chat_id, user_id, data, "auto_fix_enabled")


async def _start_set_validation_value(chat_id, user_id, data, field_name, state_name, prompt):
    """تابع کمکی برای شروع تنظیم یک مقدار اعتبارسنجی"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        user_states[user_id] = {
            "state": state_name,
            "q_id": q_id,
            "field_name": field_name
        }
        await send_message(chat_id, f"📝 {prompt}")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in _start_set_validation_value for {field_name}: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در شروع تنظیم مقدار.")
        return True


async def handle_set_min_length(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "min_length", "admin_set_min_length", "حداقل طول را وارد کنید (عدد):")


async def handle_set_max_length(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "max_length", "admin_set_max_length", "حداکثر طول را وارد کنید (عدد):")


async def handle_set_min_words(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "min_words", "admin_set_min_words", "حداقل کلمه را وارد کنید (عدد):")


async def handle_set_max_words(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "max_words", "admin_set_max_words", "حداکثر کلمه را وارد کنید (عدد):")


async def handle_set_min_value(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "min_value", "admin_set_min_value", "حداقل مقدار عددی را وارد کنید:")


async def handle_set_max_value(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "max_value", "admin_set_max_value", "حداکثر مقدار عددی را وارد کنید:")


async def handle_set_step(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "step", "admin_set_step", "گام عددی را وارد کنید:")


async def handle_set_min_date(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "min_date", "admin_set_min_date", "حداقل تاریخ را وارد کنید (مثال: ۱۴۰۳/۰۱/۰۱):")


async def handle_set_max_date(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "max_date", "admin_set_max_date", "حداکثر تاریخ را وارد کنید (مثال: ۱۴۰۳/۱۲/۲۹):")


async def handle_set_allowed_formats(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "allowed_formats", "admin_set_allowed_formats", "فرمت‌های مجاز را با کاما جدا کنید (مثال: jpg,png,pdf):")


async def handle_set_max_file_size(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "max_file_size", "admin_set_max_file_size", "حداکثر حجم فایل را به کیلوبایت وارد کنید (مثال: ۵۱۲۰):")


async def handle_set_min_file_size(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "min_file_size", "admin_set_min_file_size", "حداقل حجم فایل را به کیلوبایت وارد کنید:")


async def handle_set_max_files(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "max_files", "admin_set_max_files", "تعداد مجاز فایل را وارد کنید:")


async def handle_set_dimensions(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "dimensions", "admin_set_dimensions", "ابعاد موردنیاز را به فرمت عرض×ارتفاع وارد کنید (مثال: ۳۰۰×۳۰۰):")


async def handle_set_aspect_ratio(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "aspect_ratio", "admin_set_aspect_ratio", "نسبت تصویر را وارد کنید (مثال: 1:1 یا 16:9):")


async def handle_set_regex_pattern(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "regex_pattern", "admin_set_regex_pattern", "الگوی regex را وارد کنید:")


async def handle_set_starts_with(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "starts_with", "admin_set_starts_with", "مقدار شروع با را وارد کنید:")


async def handle_set_ends_with(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "ends_with", "admin_set_ends_with", "مقدار پایان با را وارد کنید:")


async def handle_set_contains(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "contains", "admin_set_contains", "مقدار شامل را وارد کنید:")


async def handle_set_not_contains(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "not_contains", "admin_set_not_contains", "مقدار شامل نباشد را وارد کنید:")


async def handle_set_forbidden_words(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "forbidden_words", "admin_set_forbidden_words", "کلمات ممنوع را با کاما جدا کنید:")


async def handle_set_required_words(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "required_words", "admin_set_required_words", "کلمات الزامی را با کاما جدا کنید:")


async def handle_set_validation_error(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "validation_error", "admin_set_validation_error", "پیام خطای سفارشی را وارد کنید:")


async def handle_set_validation_hint(chat_id, user_id, data):
    return await _start_set_validation_value(chat_id, user_id, data, "validation_hint", "admin_set_validation_hint", "راهنمای نمایشی را وارد کنید:")


async def handle_set_conditional_on(chat_id, user_id, data):
    """شروع تنظیم سوال مرجع برای شرط نمایش (admin_q_set_conditional_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        q = get_question_by_id(q_id)
        if not q:
            await send_message(chat_id, "❌ سوال یافت نشد.")
            return True
        
        previous_questions = get_previous_questions(q['button_id'], q_id)
        if not previous_questions:
            await send_message(chat_id, "❌ هیچ سوال قبلی برای شرط وجود ندارد.")
            return True
        
        keyboard = []
        for pq in previous_questions:
            keyboard.append([{"text": f"{pq['question_text'][:30]}", "callback_data": f"admin_q_cond_on_{q_id}_{pq['id']}"}])
        keyboard.append([{"text": "🔙 انصراف", "callback_data": f"admin_q_validation_{q_id}"}])
        
        user_states[user_id]["state"] = "admin_set_conditional_on"
        user_states[user_id]["q_id"] = q_id
        await send_message(chat_id, "🔹 **انتخاب سوال مرجع برای شرط نمایش**\nلطفاً سوال مرجع را انتخاب کنید:", {"inline_keyboard": keyboard})
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_set_conditional_on: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تنظیم شرط نمایش.")
        return True


async def handle_set_conditional_on_select(chat_id, user_id, data):
    """پردازش انتخاب سوال مرجع برای شرط نمایش (admin_q_cond_on_<q_id>_<ref_q_id>)"""
    try:
        parts = data.split("_")
        q_id = int(parts[3])
        ref_q_id = int(parts[4])
    except (ValueError, IndexError):
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        user_states[user_id]["q_id"] = q_id
        user_states[user_id]["conditional_on"] = ref_q_id
        user_states[user_id]["state"] = "admin_set_conditional_value"
        await send_message(chat_id, "🔹 **مقدار شرط نمایش**\nلطفاً مقدار مورد نظر را وارد کنید (مقداری که پاسخ سوال مرجع باید داشته باشد):")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_set_conditional_on_select: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب سوال مرجع.")
        return True


async def handle_enable_all(chat_id, user_id, data):
    """فعال کردن همه قابلیت‌های اعتبارسنجی (admin_q_enable_all_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        enable_all_validations(q_id)
        logger.info(f"همه قابلیت‌های اعتبارسنجی برای سوال {q_id} فعال شدند (توسط کاربر {user_id})")
        await send_message(chat_id, "✅ همه قابلیت‌های اعتبارسنجی فعال شدند.")
        await handle_question_validation(chat_id, user_id, f"admin_q_validation_{q_id}")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_enable_all: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در فعال‌سازی همه قابلیت‌ها.")
        return True


async def handle_disable_all(chat_id, user_id, data):
    """غیرفعال کردن همه قابلیت‌های اعتبارسنجی (admin_q_disable_all_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        disable_all_validations(q_id)
        logger.info(f"همه قابلیت‌های اعتبارسنجی برای سوال {q_id} غیرفعال شدند (توسط کاربر {user_id})")
        await send_message(chat_id, "✅ همه قابلیت‌های اعتبارسنجی غیرفعال شدند.")
        await handle_question_validation(chat_id, user_id, f"admin_q_validation_{q_id}")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_disable_all: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در غیرفعال‌سازی همه قابلیت‌ها.")
        return True


async def handle_reset_validation(chat_id, user_id, data):
    """بازنشانی تنظیمات اعتبارسنجی به حالت پیش‌فرض (admin_q_reset_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        reset_validation_to_default(q_id)
        logger.info(f"تنظیمات اعتبارسنجی سوال {q_id} به حالت پیش‌فرض بازنشانی شد (توسط کاربر {user_id})")
        await send_message(chat_id, "✅ همه تنظیمات اعتبارسنجی به حالت پیش‌فرض بازنشانی شد.")
        await handle_question_validation(chat_id, user_id, f"admin_q_validation_{q_id}")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_reset_validation: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در بازنشانی تنظیمات.")
        return True


async def handle_apply_profile(chat_id, user_id, data):
    """نمایش لیست پروفایل‌ها برای اعمال (admin_q_apply_profile_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        profiles = get_validation_profiles()
        if not profiles:
            await send_message(chat_id, "❌ هیچ پروفایلی یافت نشد. ابتدا یک پروفایل ایجاد کنید.")
            return True
        
        keyboard = []
        for p in profiles:
            keyboard.append([{"text": f"📋 {p['name']}", "callback_data": f"admin_q_apply_profile_select_{q_id}_{p['name']}"}])
        keyboard.append([{"text": "🔙 انصراف", "callback_data": f"admin_q_validation_{q_id}"}])
        
        user_states[user_id]["state"] = "main"
        await send_message(chat_id, "📋 **انتخاب پروفایل اعتبارسنجی**\nلطفاً پروفایل مورد نظر را انتخاب کنید:", {"inline_keyboard": keyboard})
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_apply_profile: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش پروفایل‌ها.")
        return True


async def handle_apply_profile_select(chat_id, user_id, data):
    """اعمال پروفایل انتخاب‌شده (admin_q_apply_profile_select_<q_id>_<profile_name>)"""
    try:
        parts = data.split("_")
        q_id = int(parts[3])
        profile_name = "_".join(parts[4:])
    except (ValueError, IndexError):
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        apply_validation_profile(q_id, profile_name)
        logger.info(f"پروفایل {profile_name} برای سوال {q_id} اعمال شد (توسط کاربر {user_id})")
        await send_message(chat_id, f"✅ پروفایل «{profile_name}» با موفقیت اعمال شد.")
        await handle_question_validation(chat_id, user_id, f"admin_q_validation_{q_id}")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_apply_profile_select: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در اعمال پروفایل.")
        return True


async def handle_save_profile(chat_id, user_id, data):
    """شروع فرآیند ذخیره پروفایل جدید (admin_q_save_profile_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        user_states[user_id] = {"state": "admin_set_profile_name", "q_id": q_id}
        await send_message(chat_id, "📝 **نام پروفایل جدید را وارد کنید:**")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_save_profile: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در ذخیره پروفایل.")
        return True


async def handle_change_validation_type(chat_id, user_id, data):
    """نمایش لیست انواع اعتبارسنجی برای انتخاب (admin_q_val_type_change_<question_id>)"""
    try:
        q_id = int(data.split("_")[-1])
    except ValueError:
        await send_message(chat_id, "❌ شناسه سوال نامعتبر.")
        return True
    
    try:
        await send_message(chat_id, "🔧 **انتخاب نوع اعتبارسنجی**\nلطفاً نوع مورد نظر را انتخاب کنید:", admin_validation_type_keyboard(q_id))
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_change_validation_type: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش انواع اعتبارسنجی.")
        return True


async def handle_select_validation_type(chat_id, user_id, data):
    """پردازش انتخاب نوع اعتبارسنجی (admin_q_val_type_select_<q_id>_<type>)"""
    try:
        parts = data.split("_")
        q_id = int(parts[3])
        val_type = parts[4]
    except (ValueError, IndexError):
        await send_message(chat_id, "❌ شناسه نامعتبر.")
        return True
    
    try:
        update_question(q_id, validation_type=val_type)
        logger.info(f"نوع اعتبارسنجی سوال {q_id} به {val_type} تغییر یافت (توسط کاربر {user_id})")
        await send_message(chat_id, f"✅ نوع اعتبارسنجی به «{val_type}» تغییر یافت.")
        await handle_question_validation(chat_id, user_id, f"admin_q_validation_{q_id}")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_select_validation_type: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در انتخاب نوع اعتبارسنجی.")
        return True


__all__ = [
    'handle_question_validation',
    'handle_toggle_required',
    'handle_toggle_validation',
    'handle_toggle_length',
    'handle_toggle_words',
    'handle_toggle_numeric',
    'handle_toggle_date',
    'handle_toggle_file',
    'handle_toggle_dimensions',
    'handle_toggle_pattern',
    'handle_toggle_contains',
    'handle_toggle_conditional',
    'handle_toggle_autofix',
    'handle_set_min_length',
    'handle_set_max_length',
    'handle_set_min_words',
    'handle_set_max_words',
    'handle_set_min_value',
    'handle_set_max_value',
    'handle_set_step',
    'handle_set_min_date',
    'handle_set_max_date',
    'handle_set_allowed_formats',
    'handle_set_max_file_size',
    'handle_set_min_file_size',
    'handle_set_max_files',
    'handle_set_dimensions',
    'handle_set_aspect_ratio',
    'handle_set_regex_pattern',
    'handle_set_starts_with',
    'handle_set_ends_with',
    'handle_set_contains',
    'handle_set_not_contains',
    'handle_set_forbidden_words',
    'handle_set_required_words',
    'handle_set_validation_error',
    'handle_set_validation_hint',
    'handle_set_conditional_on',
    'handle_set_conditional_on_select',
    'handle_enable_all',
    'handle_disable_all',
    'handle_reset_validation',
    'handle_apply_profile',
    'handle_apply_profile_select',
    'handle_save_profile',
    'handle_change_validation_type',
    'handle_select_validation_type',
]