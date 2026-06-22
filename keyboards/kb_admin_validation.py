# keyboards/kb_admin_validation.py
# کیبوردهای مدیریت اعتبارسنجی

def admin_validation_main_keyboard(q_id, settings):
    """کیبورد اصلی مدیریت اعتبارسنجی با نمایش وضعیت همه قابلیت‌ها"""
    keyboard = []
    
    # وضعیت کلی
    req_status = "✅" if settings.get('is_required', 0) == 1 else "❌"
    val_status = "✅" if settings.get('validation_enabled', 0) == 1 else "❌"
    keyboard.append([{"text": f"{req_status} اجباری", "callback_data": f"admin_q_toggle_required_{q_id}"}])
    keyboard.append([{"text": f"{val_status} اعتبارسنجی کلی", "callback_data": f"admin_q_toggle_validation_{q_id}"}])
    keyboard.append([{"text": f"🔧 نوع: {settings.get('validation_type', 'none')}", "callback_data": f"admin_q_val_type_change_{q_id}"}])
    
    # محدودیت‌های متن
    len_status = "✅" if settings.get('length_validation_enabled', 0) == 1 else "❌"
    word_status = "✅" if settings.get('word_validation_enabled', 0) == 1 else "❌"
    keyboard.append([{"text": f"{len_status} محدودیت طول", "callback_data": f"admin_q_toggle_length_{q_id}"}])
    keyboard.append([{"text": f"{word_status} محدودیت کلمه", "callback_data": f"admin_q_toggle_words_{q_id}"}])
    
    # اعتبارسنجی عددی
    num_status = "✅" if settings.get('numeric_validation_enabled', 0) == 1 else "❌"
    keyboard.append([{"text": f"{num_status} اعتبارسنجی عددی", "callback_data": f"admin_q_toggle_numeric_{q_id}"}])
    
    # اعتبارسنجی تاریخ
    date_status = "✅" if settings.get('date_validation_enabled', 0) == 1 else "❌"
    keyboard.append([{"text": f"{date_status} اعتبارسنجی تاریخ", "callback_data": f"admin_q_toggle_date_{q_id}"}])
    
    # اعتبارسنجی فایل
    file_status = "✅" if settings.get('file_validation_enabled', 0) == 1 else "❌"
    dim_status = "✅" if settings.get('dimensions_enabled', 0) == 1 else "❌"
    keyboard.append([{"text": f"{file_status} اعتبارسنجی فایل", "callback_data": f"admin_q_toggle_file_{q_id}"}])
    keyboard.append([{"text": f"{dim_status} اعتبارسنجی ابعاد", "callback_data": f"admin_q_toggle_dimensions_{q_id}"}])
    
    # الگو و محتوا
    pat_status = "✅" if settings.get('pattern_validation_enabled', 0) == 1 else "❌"
    con_status = "✅" if settings.get('contains_validation_enabled', 0) == 1 else "❌"
    keyboard.append([{"text": f"{pat_status} اعتبارسنجی الگو", "callback_data": f"admin_q_toggle_pattern_{q_id}"}])
    keyboard.append([{"text": f"{con_status} اعتبارسنجی محتوا", "callback_data": f"admin_q_toggle_contains_{q_id}"}])
    
    # پیشرفته
    cond_status = "✅" if settings.get('conditional_enabled', 0) == 1 else "❌"
    fix_status = "✅" if settings.get('auto_fix_enabled', 0) == 1 else "❌"
    keyboard.append([{"text": f"{cond_status} شرط نمایش", "callback_data": f"admin_q_toggle_conditional_{q_id}"}])
    keyboard.append([{"text": f"{fix_status} اصلاح خودکار", "callback_data": f"admin_q_toggle_autofix_{q_id}"}])
    
    # دکمه‌های تنظیم مقادیر
    keyboard.append([
        {"text": "📏 حداقل طول", "callback_data": f"admin_q_set_min_len_{q_id}"},
        {"text": "📏 حداکثر طول", "callback_data": f"admin_q_set_max_len_{q_id}"}
    ])
    keyboard.append([
        {"text": "📝 حداقل کلمه", "callback_data": f"admin_q_set_min_words_{q_id}"},
        {"text": "📝 حداکثر کلمه", "callback_data": f"admin_q_set_max_words_{q_id}"}
    ])
    keyboard.append([
        {"text": "🔢 حداقل مقدار", "callback_data": f"admin_q_set_min_val_{q_id}"},
        {"text": "🔢 حداکثر مقدار", "callback_data": f"admin_q_set_max_val_{q_id}"}
    ])
    keyboard.append([{"text": "🔢 گام عددی", "callback_data": f"admin_q_set_step_{q_id}"}])
    keyboard.append([
        {"text": "📅 حداقل تاریخ", "callback_data": f"admin_q_set_min_date_{q_id}"},
        {"text": "📅 حداکثر تاریخ", "callback_data": f"admin_q_set_max_date_{q_id}"}
    ])
    keyboard.append([{"text": "📎 فرمت‌های فایل", "callback_data": f"admin_q_set_formats_{q_id}"}])
    keyboard.append([
        {"text": "📎 حداکثر حجم", "callback_data": f"admin_q_set_max_size_{q_id}"},
        {"text": "📎 حداقل حجم", "callback_data": f"admin_q_set_min_size_{q_id}"}
    ])
    keyboard.append([{"text": "📎 تعداد مجاز فایل", "callback_data": f"admin_q_set_max_files_{q_id}"}])
    keyboard.append([{"text": "🖼️ ابعاد عکس", "callback_data": f"admin_q_set_dimensions_{q_id}"}])
    keyboard.append([{"text": "📐 نسبت تصویر", "callback_data": f"admin_q_set_ratio_{q_id}"}])
    keyboard.append([{"text": "⚙️ الگوی regex", "callback_data": f"admin_q_set_regex_{q_id}"}])
    keyboard.append([
        {"text": "🔤 شروع با", "callback_data": f"admin_q_set_starts_{q_id}"},
        {"text": "🔤 پایان با", "callback_data": f"admin_q_set_ends_{q_id}"}
    ])
    keyboard.append([
        {"text": "📋 شامل", "callback_data": f"admin_q_set_contains_{q_id}"},
        {"text": "🚫 شامل نباشد", "callback_data": f"admin_q_set_not_contains_{q_id}"}
    ])
    keyboard.append([{"text": "⛔ کلمات ممنوع", "callback_data": f"admin_q_set_forbidden_{q_id}"}])
    keyboard.append([{"text": "✅ کلمات الزامی", "callback_data": f"admin_q_set_required_words_{q_id}"}])
    keyboard.append([{"text": "🔗 شرط نمایش", "callback_data": f"admin_q_set_conditional_{q_id}"}])
    keyboard.append([{"text": "💬 پیام خطا", "callback_data": f"admin_q_set_error_{q_id}"}])
    keyboard.append([{"text": "💡 راهنما", "callback_data": f"admin_q_set_hint_{q_id}"}])
    
    # عملیات‌های کلی
    keyboard.append([
        {"text": "✅ فعال‌سازی همه", "callback_data": f"admin_q_enable_all_{q_id}"},
        {"text": "❌ غیرفعال‌سازی همه", "callback_data": f"admin_q_disable_all_{q_id}"}
    ])
    keyboard.append([
        {"text": "🔄 بازنشانی", "callback_data": f"admin_q_reset_{q_id}"},
        {"text": "📋 اعمال پروفایل", "callback_data": f"admin_q_apply_profile_{q_id}"}
    ])
    keyboard.append([{"text": "💾 ذخیره پروفایل", "callback_data": f"admin_q_save_profile_{q_id}"}])
    keyboard.append([{"text": "🔙 برگشت به سوال", "callback_data": f"admin_q_{q_id}"}])
    
    return {"inline_keyboard": keyboard}


def admin_validation_toggle_keyboard(q_id, feature_name, status):
    """کیبورد اختصاصی برای تغییر وضعیت یک قابلیت"""
    status_text = "فعال" if status == 1 else "غیرفعال"
    keyboard = {
        "inline_keyboard": [
            [{"text": f"✅ فعال کردن", "callback_data": f"admin_q_toggle_{feature_name}_{q_id}_1"}],
            [{"text": f"❌ غیرفعال کردن", "callback_data": f"admin_q_toggle_{feature_name}_{q_id}_0"}],
            [{"text": "🔙 برگشت", "callback_data": f"admin_q_validation_{q_id}"}]
        ]
    }
    return keyboard


def admin_validation_type_keyboard(q_id):
    """کیبورد انتخاب نوع اعتبارسنجی"""
    types = [
        ("none", "بدون اعتبارسنجی"),
        ("text", "📝 متن آزاد"),
        ("number", "🔢 عدد"),
        ("decimal", "💳 عدد اعشاری"),
        ("national_code", "🆔 کد ملی"),
        ("phone", "📞 تلفن همراه"),
        ("phone_landline", "☎️ تلفن ثابت"),
        ("postal_code", "📮 کدپستی"),
        ("plate", "🚗 پلاک خودرو"),
        ("iban", "🏦 شماره شبا"),
        ("card_number", "💳 شماره کارت"),
        ("email", "📧 ایمیل"),
        ("url", "🌐 آدرس وب"),
        ("date", "📅 تاریخ شمسی"),
        ("date_gregorian", "📅 تاریخ میلادی"),
        ("time", "⏰ زمان"),
        ("datetime", "📅 تاریخ و زمان"),
        ("persian_text", "🕌 متن فارسی"),
        ("english_text", "🔤 متن انگلیسی"),
        ("alphanumeric", "🔢 حروف و اعداد"),
        ("json", "📋 داده JSON"),
        ("file", "📎 فایل"),
        ("image", "🖼️ تصویر"),
        ("document", "📄 سند")
    ]
    keyboard = []
    for t in types:
        keyboard.append([{"text": t[1], "callback_data": f"admin_q_val_type_select_{q_id}_{t[0]}"}])
    keyboard.append([{"text": "🔙 برگشت", "callback_data": f"admin_q_validation_{q_id}"}])
    return {"inline_keyboard": keyboard}


def admin_validation_presets_keyboard(q_id):
    """کیبورد انتخاب پروفایل‌های پیش‌فرض"""
    keyboard = {
        "inline_keyboard": [
            [{"text": "📋 پروفایل خالی", "callback_data": f"admin_q_apply_profile_{q_id}_empty"}],
            [{"text": "👤 پروفایل نام کامل", "callback_data": f"admin_q_apply_profile_{q_id}_fullname"}],
            [{"text": "🆔 پروفایل کد ملی", "callback_data": f"admin_q_apply_profile_{q_id}_national"}],
            [{"text": "📞 پروفایل تلفن", "callback_data": f"admin_q_apply_profile_{q_id}_phone"}],
            [{"text": "📎 پروفایل مدارک", "callback_data": f"admin_q_apply_profile_{q_id}_documents"}],
            [{"text": "💰 پروفایل مالی", "callback_data": f"admin_q_apply_profile_{q_id}_financial"}],
            [{"text": "📅 پروفایل تاریخ", "callback_data": f"admin_q_apply_profile_{q_id}_date"}],
            [{"text": "🔙 برگشت", "callback_data": f"admin_q_validation_{q_id}"}]
        ]
    }
    return keyboard


def admin_validation_confirm_keyboard(q_id, action):
    """کیبورد تأیید برای عملیات‌های مهم"""
    keyboard = {
        "inline_keyboard": [
            [{"text": "✅ تأیید", "callback_data": f"admin_q_confirm_{action}_{q_id}"}],
            [{"text": "❌ انصراف", "callback_data": f"admin_q_validation_{q_id}"}]
        ]
    }
    return keyboard