# admin_panel/q_routes.py
# ثبت روت‌های مربوط به مدیریت سوالات، گزینه‌ها، شرط‌ها و اعتبارسنجی در پنل مدیریت

from .router import route, extract_params
from core import send_message
from .q_manage import (
    handle_question_manage,
    handle_question_add_start,
    handle_question_detail,
    handle_question_delete,
    handle_question_edit,
    handle_question_back,
)
from .q_options import (
    handle_option_list,
    handle_option_add,
    handle_option_detail,
    handle_option_edit,
    handle_option_delete,
)
from .q_conditions import (
    handle_condition_add_start,
    handle_condition_ref,
    handle_condition_operator,
    handle_condition_logic,
    handle_condition_delete,
    handle_condition_edit_start,
    handle_condition_edit_ref,
    handle_condition_edit_operator,
    handle_condition_edit_value,
    handle_condition_list,
    handle_condition_detail,
    handle_question_condition_skip,
    handle_question_condition_yes,
    handle_question_condition_no,
    handle_question_condition_ref,
    handle_question_condition_operator,
)
from .q_validation import (
    handle_question_validation,
    handle_toggle_required,
    handle_toggle_validation,
    handle_toggle_length,
    handle_toggle_words,
    handle_toggle_numeric,
    handle_toggle_date,
    handle_toggle_file,
    handle_toggle_dimensions,
    handle_toggle_pattern,
    handle_toggle_contains,
    handle_toggle_conditional,
    handle_toggle_autofix,
    handle_set_min_length,
    handle_set_max_length,
    handle_set_min_words,
    handle_set_max_words,
    handle_set_min_value,
    handle_set_max_value,
    handle_set_step,
    handle_set_min_date,
    handle_set_max_date,
    handle_set_allowed_formats,
    handle_set_max_file_size,
    handle_set_min_file_size,
    handle_set_max_files,
    handle_set_dimensions,
    handle_set_aspect_ratio,
    handle_set_regex_pattern,
    handle_set_starts_with,
    handle_set_ends_with,
    handle_set_contains,
    handle_set_not_contains,
    handle_set_forbidden_words,
    handle_set_required_words,
    handle_set_validation_error,
    handle_set_validation_hint,
    handle_set_conditional_on,
    handle_set_conditional_on_select,
    handle_enable_all,
    handle_disable_all,
    handle_reset_validation,
    handle_apply_profile,
    handle_apply_profile_select,
    handle_save_profile,
    handle_change_validation_type,
    handle_select_validation_type,
)


# ========== روت‌های مدیریت سوالات ==========

@route("admin_q_manage_")
async def admin_q_manage(update):
    """نمایش لیست سوالات یک دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_manage(chat_id, user_id, data)


@route("admin_q_add_")
async def admin_q_add(update):
    """شروع فرآیند افزودن سوال جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_add_start(chat_id, user_id, data)


@route("admin_q_del_")
async def admin_q_del(update):
    """حذف سوال"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_delete(chat_id, user_id, data)


@route("admin_q_edit_")
async def admin_q_edit(update):
    """شروع ویرایش متن سوال"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_edit(chat_id, user_id, data)


@route("admin_q_back_")
async def admin_q_back(update):
    """بازگشت به لیست سوالات دکمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_back(chat_id, user_id, data)


@route("admin_q_")
async def admin_q(update):
    """نمایش جزئیات یک سوال"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_detail(chat_id, user_id, data)


# ========== روت‌های مدیریت گزینه‌های دکمه‌ای ==========

@route("admin_qopt_list_")
async def admin_qopt_list(update):
    """نمایش لیست گزینه‌های یک سوال"""
    chat_id, user_id, data = extract_params(update)
    return await handle_option_list(chat_id, user_id, data)


@route("admin_qopt_add_")
async def admin_qopt_add(update):
    """شروع فرآیند افزودن گزینه جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_option_add(chat_id, user_id, data)


@route("admin_qopt_edit_")
async def admin_qopt_edit(update):
    """شروع ویرایش گزینه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_option_edit(chat_id, user_id, data)


@route("admin_qopt_del_")
async def admin_qopt_del(update):
    """حذف گزینه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_option_delete(chat_id, user_id, data)


@route("admin_qopt_")
async def admin_qopt(update):
    """نمایش جزئیات یک گزینه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_option_detail(chat_id, user_id, data)


# ========== روت‌های مدیریت شرط‌ها ==========

@route("admin_condition_add")
async def admin_condition_add(update):
    """شروع فرآیند افزودن شرط جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_add_start(chat_id, user_id)


@route("admin_cond_ref_")
async def admin_cond_ref(update):
    """پردازش انتخاب سوال مرجع برای شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_ref(chat_id, user_id, data)


@route("admin_cond_op_")
async def admin_cond_op(update):
    """پردازش انتخاب عملگر شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_operator(chat_id, user_id, data)


@route("admin_cond_logic_")
async def admin_cond_logic(update):
    """پردازش انتخاب منطق ترکیب شرط‌ها"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_logic(chat_id, user_id, data)


@route("admin_cond_del_")
async def admin_cond_del(update):
    """حذف شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_delete(chat_id, user_id, data)


@route("admin_cond_edit_")
async def admin_cond_edit(update):
    """شروع ویرایش شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_edit_start(chat_id, user_id, data)


@route("admin_cond_edit_ref_")
async def admin_cond_edit_ref(update):
    """پردازش انتخاب سوال مرجع جدید برای ویرایش شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_edit_ref(chat_id, user_id, data)


@route("admin_cond_edit_op_")
async def admin_cond_edit_op(update):
    """پردازش انتخاب عملگر جدید برای ویرایش شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_edit_operator(chat_id, user_id, data)


@route("admin_cond_edit_value_")
async def admin_cond_edit_value(update):
    """شروع ویرایش مقدار شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_edit_value(chat_id, user_id, data)


@route("admin_cond_list_")
async def admin_cond_list(update):
    """نمایش لیست شرط‌های یک سوال"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_list(chat_id, user_id, data)


@route("admin_cond_detail_")
async def admin_cond_detail(update):
    """نمایش جزئیات یک شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_condition_detail(chat_id, user_id, data)


# ========== روت‌های شرط برای سوال جدید ==========

@route("admin_question_condition_skip")
async def admin_question_condition_skip(update):
    """ذخیره سوال بدون شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_condition_skip(chat_id, user_id)


@route("admin_condition_yes")
async def admin_condition_yes(update):
    """شروع افزودن شرط برای سوال جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_condition_yes(chat_id, user_id)


@route("admin_condition_no")
async def admin_condition_no(update):
    """ذخیره سوال بدون شرط"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_condition_no(chat_id, user_id)


@route("admin_q_condition_ref_")
async def admin_q_condition_ref(update):
    """پردازش انتخاب سوال مرجع برای شرط سوال جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_condition_ref(chat_id, user_id, data)


@route("admin_q_condition_op_")
async def admin_q_condition_op(update):
    """پردازش انتخاب عملگر شرط برای سوال جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_condition_operator(chat_id, user_id, data)


# ========== روت‌های مدیریت اعتبارسنجی ==========

@route("admin_q_validation_")
async def admin_q_validation(update):
    """نمایش صفحه مدیریت اعتبارسنجی سوال"""
    chat_id, user_id, data = extract_params(update)
    return await handle_question_validation(chat_id, user_id, data)


@route("admin_q_toggle_required_")
async def admin_q_toggle_required(update):
    """تغییر وضعیت اجباری بودن سوال"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_required(chat_id, user_id, data)


@route("admin_q_toggle_validation_")
async def admin_q_toggle_validation(update):
    """تغییر وضعیت اعتبارسنجی کلی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_validation(chat_id, user_id, data)


@route("admin_q_toggle_length_")
async def admin_q_toggle_length(update):
    """تغییر وضعیت محدودیت طول"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_length(chat_id, user_id, data)


@route("admin_q_toggle_words_")
async def admin_q_toggle_words(update):
    """تغییر وضعیت محدودیت کلمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_words(chat_id, user_id, data)


@route("admin_q_toggle_numeric_")
async def admin_q_toggle_numeric(update):
    """تغییر وضعیت اعتبارسنجی عددی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_numeric(chat_id, user_id, data)


@route("admin_q_toggle_date_")
async def admin_q_toggle_date(update):
    """تغییر وضعیت اعتبارسنجی تاریخ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_date(chat_id, user_id, data)


@route("admin_q_toggle_file_")
async def admin_q_toggle_file(update):
    """تغییر وضعیت اعتبارسنجی فایل"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_file(chat_id, user_id, data)


@route("admin_q_toggle_dimensions_")
async def admin_q_toggle_dimensions(update):
    """تغییر وضعیت اعتبارسنجی ابعاد"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_dimensions(chat_id, user_id, data)


@route("admin_q_toggle_pattern_")
async def admin_q_toggle_pattern(update):
    """تغییر وضعیت اعتبارسنجی الگو"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_pattern(chat_id, user_id, data)


@route("admin_q_toggle_contains_")
async def admin_q_toggle_contains(update):
    """تغییر وضعیت اعتبارسنجی محتوا"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_contains(chat_id, user_id, data)


@route("admin_q_toggle_conditional_")
async def admin_q_toggle_conditional(update):
    """تغییر وضعیت شرط نمایش"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_conditional(chat_id, user_id, data)


@route("admin_q_toggle_autofix_")
async def admin_q_toggle_autofix(update):
    """تغییر وضعیت اصلاح خودکار"""
    chat_id, user_id, data = extract_params(update)
    return await handle_toggle_autofix(chat_id, user_id, data)


# ========== روت‌های تنظیم مقادیر اعتبارسنجی ==========

@route("admin_q_set_min_len_")
async def admin_q_set_min_len(update):
    """شروع تنظیم حداقل طول"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_min_length(chat_id, user_id, data)


@route("admin_q_set_max_len_")
async def admin_q_set_max_len(update):
    """شروع تنظیم حداکثر طول"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_max_length(chat_id, user_id, data)


@route("admin_q_set_min_words_")
async def admin_q_set_min_words(update):
    """شروع تنظیم حداقل کلمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_min_words(chat_id, user_id, data)


@route("admin_q_set_max_words_")
async def admin_q_set_max_words(update):
    """شروع تنظیم حداکثر کلمه"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_max_words(chat_id, user_id, data)


@route("admin_q_set_min_val_")
async def admin_q_set_min_val(update):
    """شروع تنظیم حداقل مقدار عددی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_min_value(chat_id, user_id, data)


@route("admin_q_set_max_val_")
async def admin_q_set_max_val(update):
    """شروع تنظیم حداکثر مقدار عددی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_max_value(chat_id, user_id, data)


@route("admin_q_set_step_")
async def admin_q_set_step(update):
    """شروع تنظیم گام عددی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_step(chat_id, user_id, data)


@route("admin_q_set_min_date_")
async def admin_q_set_min_date(update):
    """شروع تنظیم حداقل تاریخ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_min_date(chat_id, user_id, data)


@route("admin_q_set_max_date_")
async def admin_q_set_max_date(update):
    """شروع تنظیم حداکثر تاریخ"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_max_date(chat_id, user_id, data)


@route("admin_q_set_formats_")
async def admin_q_set_formats(update):
    """شروع تنظیم فرمت‌های مجاز فایل"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_allowed_formats(chat_id, user_id, data)


@route("admin_q_set_max_size_")
async def admin_q_set_max_size(update):
    """شروع تنظیم حداکثر حجم فایل"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_max_file_size(chat_id, user_id, data)


@route("admin_q_set_min_size_")
async def admin_q_set_min_size(update):
    """شروع تنظیم حداقل حجم فایل"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_min_file_size(chat_id, user_id, data)


@route("admin_q_set_max_files_")
async def admin_q_set_max_files(update):
    """شروع تنظیم تعداد مجاز فایل"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_max_files(chat_id, user_id, data)


@route("admin_q_set_dimensions_")
async def admin_q_set_dimensions(update):
    """شروع تنظیم ابعاد عکس"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_dimensions(chat_id, user_id, data)


@route("admin_q_set_ratio_")
async def admin_q_set_ratio(update):
    """شروع تنظیم نسبت تصویر"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_aspect_ratio(chat_id, user_id, data)


@route("admin_q_set_regex_")
async def admin_q_set_regex(update):
    """شروع تنظیم الگوی regex"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_regex_pattern(chat_id, user_id, data)


@route("admin_q_set_starts_")
async def admin_q_set_starts(update):
    """شروع تنظیم مقدار شروع با"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_starts_with(chat_id, user_id, data)


@route("admin_q_set_ends_")
async def admin_q_set_ends(update):
    """شروع تنظیم مقدار پایان با"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_ends_with(chat_id, user_id, data)


@route("admin_q_set_contains_")
async def admin_q_set_contains(update):
    """شروع تنظیم مقدار شامل"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_contains(chat_id, user_id, data)


@route("admin_q_set_not_contains_")
async def admin_q_set_not_contains(update):
    """شروع تنظیم مقدار شامل نباشد"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_not_contains(chat_id, user_id, data)


@route("admin_q_set_forbidden_")
async def admin_q_set_forbidden(update):
    """شروع تنظیم کلمات ممنوع"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_forbidden_words(chat_id, user_id, data)


@route("admin_q_set_required_words_")
async def admin_q_set_required_words(update):
    """شروع تنظیم کلمات الزامی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_required_words(chat_id, user_id, data)


@route("admin_q_set_error_")
async def admin_q_set_error(update):
    """شروع تنظیم پیام خطای سفارشی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_validation_error(chat_id, user_id, data)


@route("admin_q_set_hint_")
async def admin_q_set_hint(update):
    """شروع تنظیم راهنمای نمایشی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_validation_hint(chat_id, user_id, data)


@route("admin_q_cond_on_")
async def admin_q_cond_on(update):
    """پردازش انتخاب سوال مرجع برای شرط نمایش"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_conditional_on_select(chat_id, user_id, data)


@route("admin_q_set_conditional_")
async def admin_q_set_conditional(update):
    """شروع تنظیم سوال مرجع برای شرط نمایش"""
    chat_id, user_id, data = extract_params(update)
    return await handle_set_conditional_on(chat_id, user_id, data)


# ========== روت‌های عملیات‌های کلی اعتبارسنجی ==========

@route("admin_q_enable_all_")
async def admin_q_enable_all(update):
    """فعال کردن همه قابلیت‌های اعتبارسنجی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_enable_all(chat_id, user_id, data)


@route("admin_q_disable_all_")
async def admin_q_disable_all(update):
    """غیرفعال کردن همه قابلیت‌های اعتبارسنجی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_disable_all(chat_id, user_id, data)


@route("admin_q_reset_")
async def admin_q_reset(update):
    """بازنشانی تنظیمات اعتبارسنجی به حالت پیش‌فرض"""
    chat_id, user_id, data = extract_params(update)
    return await handle_reset_validation(chat_id, user_id, data)


@route("admin_q_apply_profile_select_")
async def admin_q_apply_profile_select(update):
    """اعمال پروفایل انتخاب‌شده"""
    chat_id, user_id, data = extract_params(update)
    return await handle_apply_profile_select(chat_id, user_id, data)


@route("admin_q_apply_profile_")
async def admin_q_apply_profile(update):
    """نمایش لیست پروفایل‌ها برای اعمال"""
    chat_id, user_id, data = extract_params(update)
    return await handle_apply_profile(chat_id, user_id, data)


@route("admin_q_save_profile_")
async def admin_q_save_profile(update):
    """شروع فرآیند ذخیره پروفایل جدید"""
    chat_id, user_id, data = extract_params(update)
    return await handle_save_profile(chat_id, user_id, data)


@route("admin_q_val_type_change_")
async def admin_q_val_type_change(update):
    """نمایش لیست انواع اعتبارسنجی برای انتخاب"""
    chat_id, user_id, data = extract_params(update)
    return await handle_change_validation_type(chat_id, user_id, data)


@route("admin_q_val_type_select_")
async def admin_q_val_type_select(update):
    """پردازش انتخاب نوع اعتبارسنجی"""
    chat_id, user_id, data = extract_params(update)
    return await handle_select_validation_type(chat_id, user_id, data)