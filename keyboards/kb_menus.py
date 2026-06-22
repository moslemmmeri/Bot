# keyboards/kb_menus.py
# کیبوردهای منوها - نسخه داینامیک (خواندن از دیتابیس)
# با پشتیبانی از تنظیم تعداد ستون‌ها در سه سطح: دکمه، دسته‌بندی، و پیش‌فرض عمومی
# همچنین پشتیبانی از پیش‌نمایش با ستون‌های مختلف (برای مدیریت ستون‌ها)
# اضافه شدن دکمه‌های پروفایل و راهنما به منوی اصلی

from database import get_buttons_by_location, get_effective_columns, get_category_by_location


def chunk_list(lst, n=2):
    """
    تقسیم لیست به گروه‌های n تایی برای نمایش در ردیف‌های کنار هم
    n: تعداد ستون‌ها (تعداد دکمه در هر ردیف)
    """
    if n < 1:
        n = 1
    if n > 8:  # حداکثر ۸ دکمه در هر ردیف (محدودیت تلگرام)
        n = 8
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def get_dynamic_menu_keyboard(location: str, extra_buttons=None, override_columns=None):
    """
    ساخت کیبورد منو بر اساس location (main, more, other)
    location: نام بخش (مطابق با فیلد location در جدول categories)
    extra_buttons: لیستی از دکمه‌های اضافی که در انتها اضافه می‌شوند
    override_columns: (اختیاری) تعداد ستون‌های مورد نظر برای بازنویسی (برای پیش‌نمایش)
    
    تعداد ستون‌ها بر اساس اولویت زیر تعیین می‌شود:
    1. override_columns (اگر ارائه شده باشد - برای پیش‌نمایش)
    2. تنظیمات اختصاصی دکمه (در حال حاضر برای دکمه‌های منو پشتیبانی نمی‌شود)
    3. تنظیمات دسته‌بندی (فیلد columns در جدول categories)
    4. مقدار پیش‌فرض عمومی (default_menu_columns در جدول settings)
    """
    buttons = get_buttons_by_location(location)
    items = []
    for btn in buttons:
        text = btn.get('name', 'بدون نام')
        # اگر دکمه زیرمنو دارد، آیکون 📂 نمایش داده شود
        if btn.get('has_submenu', 0) == 1:
            text = f"📂 {text}"
        items.append({"text": text, "callback_data": btn['callback_data']})
    
    # تعیین تعداد ستون‌ها
    if override_columns is not None:
        # برای پیش‌نمایش، از مقدار override استفاده می‌شود
        columns = override_columns
    else:
        # دریافت دسته‌بندی مرتبط با این location
        category = get_category_by_location(location)
        columns = 2  # مقدار پیش‌فرض
        if category:
            # دریافت تعداد ستون‌های مؤثر با استفاده از تابع کمکی
            columns = get_effective_columns(
                button_id=None,  # برای منوها دکمه خاصی نداریم
                category_id=category['id']
            )
    
    # اطمینان از معتبر بودن تعداد ستون‌ها
    if columns < 1:
        columns = 1
    if columns > 8:
        columns = 8
    
    keyboard = []
    # تقسیم به ردیف‌های با تعداد ستون‌های مشخص‌شده
    for row in chunk_list(items, columns):
        keyboard.append(row)
    
    # اضافه کردن دکمه‌های اضافی در انتها
    if extra_buttons:
        keyboard.append(extra_buttons)
    
    return {"inline_keyboard": keyboard}


def main_menu_keyboard(columns=None):
    """
    منوی اصلی - شامل دکمه‌های بخش 'main' و یک دکمه «بیشتر» در انتها
    همچنین دکمه‌های پروفایل و راهنما در انتهای منو اضافه می‌شوند
    
    پارامترها:
        columns: (اختیاری) تعداد ستون‌های مورد نظر برای بازنویسی (برای پیش‌نمایش)
    """
    # دکمه‌های اصلی منو
    extra = [
        {"text": "➕ بیشتر", "callback_data": "menu_more"}
    ]
    
    keyboard = get_dynamic_menu_keyboard('main', extra, columns)
    
    # اضافه کردن دکمه‌های پروفایل و راهنما در انتهای منو
    # این دکمه‌ها همیشه در منوی اصلی نمایش داده می‌شوند
    keyboard["inline_keyboard"].append([
        {"text": "👤 پروفایل", "callback_data": "profile_main"},
        {"text": "❓ راهنما", "callback_data": "help_main"}
    ])
    
    return keyboard


def more_menu_keyboard(columns=None):
    """
    منوی بیشتر - شامل دکمه‌های بخش 'more' و دکمه برگشت به منوی اصلی
    
    پارامترها:
        columns: (اختیاری) تعداد ستون‌های مورد نظر برای بازنویسی (برای پیش‌نمایش)
    """
    extra = [{"text": "🔙 برگشت به منو", "callback_data": "back_main"}]
    return get_dynamic_menu_keyboard('more', extra, columns)


def other_services_keyboard(columns=None):
    """
    منوی دیگر خدمات - شامل دکمه‌های بخش 'other' و دکمه برگشت به منوی بیشتر
    
    پارامترها:
        columns: (اختیاری) تعداد ستون‌های مورد نظر برای بازنویسی (برای پیش‌نمایش)
    """
    extra = [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
    return get_dynamic_menu_keyboard('other', extra, columns)


# ==================== توابع جدید برای پیش‌نمایش ====================

def preview_menu_keyboard(location: str, columns: int, extra_buttons=None):
    """
    ساخت کیبورد پیش‌نمایش یک منو با تعداد ستون‌های مشخص
    این تابع برای نمایش پیش‌نمایش در پنل مدیریت ستون‌ها استفاده می‌شود
    
    پارامترها:
        location: نام بخش (main, more, other)
        columns: تعداد ستون‌های مورد نظر برای پیش‌نمایش
        extra_buttons: (اختیاری) دکمه‌های اضافی
    
    بازگشت: کیبورد با تعداد ستون‌های مشخص
    """
    return get_dynamic_menu_keyboard(location, extra_buttons, override_columns=columns)


def preview_main_menu(columns=2):
    """پیش‌نمایش منوی اصلی با تعداد ستون‌های مشخص"""
    extra = [{"text": "➕ بیشتر", "callback_data": "menu_more"}]
    keyboard = get_dynamic_menu_keyboard('main', extra, columns)
    # اضافه کردن دکمه‌های پروفایل و راهنما در پیش‌نمایش
    keyboard["inline_keyboard"].append([
        {"text": "👤 پروفایل", "callback_data": "profile_main"},
        {"text": "❓ راهنما", "callback_data": "help_main"}
    ])
    return keyboard


def preview_more_menu(columns=2):
    """پیش‌نمایش منوی بیشتر با تعداد ستون‌های مشخص"""
    extra = [{"text": "🔙 برگشت به منو", "callback_data": "back_main"}]
    return get_dynamic_menu_keyboard('more', extra, columns)


def preview_other_menu(columns=2):
    """پیش‌نمایش منوی دیگر خدمات با تعداد ستون‌های مشخص"""
    extra = [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
    return get_dynamic_menu_keyboard('other', extra, columns)


# ==================== توابع ثابت قبلی (برای سازگاری با کدهای قدیمی) ====================
# این توابع در صورت نیاز باقی می‌مانند. در نسخه داینامیک، منوهای اصلی از دیتابیس خوانده می‌شوند.
# اما برای جلوگیری از خطا در بخش‌های دیگر که مستقیماً از این توابع استفاده می‌کنند، نگه‌داشته می‌شوند.

def tax_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📝 ثبت نام مالیاتی", "callback_data": "tax_registration"}],
            [{"text": "📄 اظهار نامه مالیاتی", "callback_data": "tax_declaration"}],
            [{"text": "💳 پرداخت مالیاتی", "callback_data": "tax_payment"}],
            [{"text": "🧾 ارزش افزوده", "callback_data": "tax_vat"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def car_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🚗 ثبت نام خودرو", "callback_data": "car_registration"}],
            [{"text": "🚨 خلافی خودرو", "callback_data": "car_violation"}, {"text": "💰 عوارض خودرو", "callback_data": "car_toll"}],
            [{"text": "🛣️ عوارض آزادراهی", "callback_data": "car_freeway_toll"}, {"text": "🔄 تعویض پلاک", "callback_data": "car_plate_change"}],
            [{"text": "🔧 معاینه فنی", "callback_data": "car_inspection"}, {"text": "🚫 نمره منفی گواهی نامه", "callback_data": "car_negative_score"}],
            [{"text": "📜 تاریخچه پلاک", "callback_data": "car_plate_history"}, {"text": "🚦 طرح ترافیک", "callback_data": "car_traffic_plan"}],
            [{"text": "💰 مالیات نقل و انتقال", "callback_data": "car_tax_transfer"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def tax_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📝 ثبت نام مالیاتی", "callback_data": "tax_registration"}, {"text": "📄 اظهار نامه مالیاتی", "callback_data": "tax_declaration"}],
            [{"text": "💳 پرداخت مالیاتی", "callback_data": "tax_payment"}, {"text": "🔄 مالیات نقل و انتقال", "callback_data": "tax_transfer"}],
            [{"text": "🧾 ارزش افزوده", "callback_data": "tax_vat"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def insurance_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔍 استعلام بیمه نامه", "callback_data": "ins_inquiry"}, {"text": "📄 صدور انواع بیمه نامه", "callback_data": "ins_issue"}],
            [{"text": "🔄 تمدید انواع بیمه نامه", "callback_data": "ins_renew"}, {"text": "💰 پرداخت حق بیمه", "callback_data": "ins_payment"}],
            [{"text": "🏃 بیمه ورزشی", "callback_data": "ins_sports"}, {"text": "📉 کسر از حقوق", "callback_data": "ins_salary_deduct"}],
            [{"text": "⚖️ حکم حقوقی", "callback_data": "ins_legal_judgment"}, {"text": "🧾 فیش حقوقی", "callback_data": "ins_pay_slip"}],
            [{"text": "🆘 درخواست غرامت", "callback_data": "ins_compensation"}, {"text": "📜 سابقه بیمه", "callback_data": "ins_history"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def judicial_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📢 ابلاغیه", "callback_data": "jud_notification"}, {"text": "🔐 ثبت ثنا", "callback_data": "jud_sana_register"}],
            [{"text": "📅 نوبت دهی قضایی", "callback_data": "jud_appointment"}, {"text": "🚫 سوء پیشینه", "callback_data": "jud_criminal_record"}],
            [{"text": "📜 گواهی ثبت ثنا", "callback_data": "jud_sana_certificate"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def banking_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📝 ثبت چک", "callback_data": "bank_check_register"}, {"text": "🔍 استعلام چک", "callback_data": "bank_check_inquiry"}],
            [{"text": "🧮 محاسبه شبا", "callback_data": "bank_heba_calc"}, {"text": "✅ اعتبارسنجی بانکی", "callback_data": "bank_credit_score"}],
            [{"text": "💼 مشاوره تسهیلات بانکی", "callback_data": "bank_loan_consult"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def online_reg_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📝 سنجش بدو ورود", "callback_data": "online_entrance_exam"}, {"text": "🎓 نمونه دولتی و سمپاد", "callback_data": "online_sample_sampad"}],
            [{"text": "🆔 کارت ملی", "callback_data": "online_national_card"}, {"text": "🏦 سجام", "callback_data": "online_sejam"}],
            [{"text": "💰 سهام عدالت", "callback_data": "online_equity_shares"}, {"text": "🎲 ثبت نام لاتاری", "callback_data": "online_lottery"}],
            [{"text": "🏢 ثبت شرکت", "callback_data": "online_company_reg"}, {"text": "📚 کنکور", "callback_data": "online_concour"}],
            [{"text": "📖 ثبت نام کتاب درسی", "callback_data": "online_textbook"}, {"text": "🏛️ تاییدیه اماکن", "callback_data": "online_place_approval"}],
            [{"text": "💰 ثبت نام یارانه", "callback_data": "online_subsidy"}, {"text": "✏️ انتخاب رشته", "callback_data": "online_field_selection"}],
            [{"text": "💳 درگاه پرداخت", "callback_data": "online_payment_gateway"}, {"text": "💳 کارتخوان", "callback_data": "online_pos"}],
            [{"text": "👔 استخدام", "callback_data": "online_employment"}, {"text": "📚 انتخاب واحد درسی", "callback_data": "online_course_selection"}],
            [{"text": "✅ نماد اعتماد", "callback_data": "online_trust_symbol"}, {"text": "📋 ساماندهی", "callback_data": "online_organization"}],
            [{"text": "🏠 املاک و اسکان", "callback_data": "online_housing"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def loan_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "💍 وام ازدواج", "callback_data": "loan_marriage"}, {"text": "👶 وام فرزندآوری", "callback_data": "loan_childbirth"}],
            [{"text": "🏠 وام ودیعه مسکن", "callback_data": "loan_housing_deposit"}, {"text": "🤝 وام بدون ضامن", "callback_data": "loan_no_guarantor"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def license_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🚛 پروانه اشتغال رانندگان", "callback_data": "license_driver_employment"}, {"text": "🚛 پروانه فعالیت رانندگان", "callback_data": "license_driver_activity"}],
            [{"text": "🏪 پروانه کسب", "callback_data": "license_business"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def medical_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "👨‍⚕️ نوبت دهی دکتر", "callback_data": "medical_doctor_appointment"}, {"text": "💊 دریافت دارو", "callback_data": "medical_get_medicine"}],
            [{"text": "💉 نوبت دهی واکسن", "callback_data": "medical_vaccine_appointment"}, {"text": "🩺 تمدید بیمه سلامت", "callback_data": "medical_health_insurance_renew"}],
            [{"text": "📄 دریافت نسخه الکترونیک", "callback_data": "medical_electronic_prescription"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def design_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 پاورپوینت", "callback_data": "design_powerpoint"}, {"text": "🎨 لوگو", "callback_data": "design_logo"}],
            [{"text": "🪪 کارت ویزیت", "callback_data": "design_card"}, {"text": "📢 بنر تبلیغاتی", "callback_data": "design_banner"}],
            [{"text": "🌐 طراحی سایت", "callback_data": "design_website"}, {"text": "📱 طراحی اپلیکیشن", "callback_data": "design_app"}],
            [{"text": "🎬 موشن گرافیک", "callback_data": "design_motion"}, {"text": "🖼️ طراحی کاور", "callback_data": "design_cover"}],
            [{"text": "📊 اکسل", "callback_data": "design_excel"}, {"text": "🧾 فاکتور", "callback_data": "design_invoice"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def ticket_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🏟️ بلیط استادیوم", "callback_data": "ticket_stadium"}],
            [{"text": "🚌 خرید بلیط (اتوبوس - قطار - هواپیما)", "callback_data": "ticket_transport"}],
            [{"text": "🏨 رزرو اقامتگاه", "callback_data": "ticket_reservation"}, {"text": "🎬 بلیط سینما", "callback_data": "ticket_cinema"}],
            [{"text": "🎡 بلیط مجتمع تفریحی", "callback_data": "ticket_entertainment"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def postal_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "✅ تاییدیه پستی", "callback_data": "postal_confirmation"}, {"text": "🏠 احراز نشانی پستی", "callback_data": "postal_address_verification"}],
            [{"text": "📮 درخواست کدپستی جدید", "callback_data": "postal_new_code"}],
            [{"text": "📦 رهگیری مرسوله پستی", "callback_data": "postal_tracking"}],
            [{"text": "🏢 احراز نشانی سخا", "callback_data": "postal_sakha"}],
            [{"text": "🔍 استعلام مدارک گمشده", "callback_data": "postal_lost_docs"}, {"text": "🏠 تغییر نشانی در ثبت احوال", "callback_data": "postal_change_address"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def bill_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📱 قبض تلفن همراه", "callback_data": "bill_mobile"}, {"text": "💸 پرداخت قبوض", "callback_data": "bill_utilities"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def currency_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🏦 افتتاح حساب صرافی (ایرانی - خارجی)", "callback_data": "currency_exchange_account"}],
            [{"text": "💳 افتتاح حساب ارزی (پی پال - مسترکارت - ویزاکارت)", "callback_data": "currency_forex_account"}],
            [{"text": "💰 نقد کردن درآمد ارزی", "callback_data": "currency_cash"}],
            [{"text": "🔐 سفارش کیف پول سخت افزاری", "callback_data": "currency_hardware_wallet"}],
            [{"text": "📘 آموزش ساخت کیف پول ارز دیجیتال", "callback_data": "currency_crypto_wallet"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def other_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📝 سفارش تحقیق", "callback_data": "other_research"}, {"text": "⌨️ تایپ", "callback_data": "other_typing"}],
            [{"text": "🚫 استعلام ممنوع الخروجی", "callback_data": "other_travel_ban"}, {"text": "📨 پیامک تبلیغاتی", "callback_data": "other_sms"}],
            [{"text": "🖼️ تدوین عکس", "callback_data": "other_photo_edit"}, {"text": "🎓 تاییدیه تحصیلی", "callback_data": "other_education_verify"}],
            [{"text": "🔑 ساخت اکانت", "callback_data": "other_create_account"}, {"text": "🎫 کارت ورود به جلسه", "callback_data": "other_exam_card"}],
            [{"text": "📄 دریافت کارنامه", "callback_data": "other_transcript"}, {"text": "🌍 خدمات اتباع", "callback_data": "other_foreigners"}],
            [{"text": "🔙 برگشت به بیشتر", "callback_data": "back_more"}]
        ]
    }


def household_services_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🛒 کالا برگ", "callback_data": "household_voucher"}],
            [{"text": "📊 استعلام دهک بندی یارانه ها", "callback_data": "household_decile"}],
            [{"text": "⚠️ اعتراض به قطع یارانه", "callback_data": "household_protest"}],
            [{"text": "🔧 حل مشکل یارانه", "callback_data": "household_solve"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "back_main"}]
        ]
    }


__all__ = [
    'main_menu_keyboard',
    'more_menu_keyboard',
    'other_services_keyboard',
    'tax_main_keyboard',
    'car_services_keyboard',
    'tax_services_keyboard',
    'insurance_services_keyboard',
    'judicial_services_keyboard',
    'banking_services_keyboard',
    'online_reg_services_keyboard',
    'loan_services_keyboard',
    'license_services_keyboard',
    'medical_services_keyboard',
    'design_services_keyboard',
    'ticket_services_keyboard',
    'postal_services_keyboard',
    'bill_services_keyboard',
    'currency_services_keyboard',
    'other_services_keyboard',
    'household_services_keyboard',
    'chunk_list',
    'get_dynamic_menu_keyboard',
    # توابع جدید برای پیش‌نمایش
    'preview_menu_keyboard',
    'preview_main_menu',
    'preview_more_menu',
    'preview_other_menu',
]