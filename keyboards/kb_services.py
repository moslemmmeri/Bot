# keyboards/kb_services.py
# کیبوردهای سرویس‌ها

def abolaghieh_recovery_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔄 بازیابی رمز عبور", "callback_data": "abolaghieh_recover"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "back_main"}]
        ]
    }


def tax_recovery_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔄 بازیابی رمز عبور", "callback_data": "tax_recovery"}]
        ]
    }


def description_skip_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "⏩ بدون توضیح", "callback_data": "skip_description"}]
        ]
    }


def suborder_type_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "پرینت جزئی", "callback_data": "suborder_detail"}],
            [{"text": "پرینت عمده", "callback_data": "suborder_bulk"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "back_main"}]
        ]
    }


def print_type_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "⚫ سیاه و سفید", "callback_data": "print_bw"}, {"text": "🌈 رنگی", "callback_data": "print_color"}],
            [{"text": "✨ گلاسه", "callback_data": "print_glossy"}, {"text": "🧲 پشت بچسب دار", "callback_data": "print_sticky"}],
            [{"text": "🔙 برگشت", "callback_data": "back_suborder"}]
        ]
    }


def sided_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📄 تک رو", "callback_data": "sided_single"}, {"text": "📑 پشت رو", "callback_data": "sided_double"}],
            [{"text": "🔙 برگشت", "callback_data": "back_print_type"}]
        ]
    }


def vehicle_type_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "سواری شخصی", "callback_data": "vtype_personal"}, {"text": "موتور سیکلت", "callback_data": "vtype_motorcycle"}],
            [{"text": "سواری عمومی", "callback_data": "vtype_public"}, {"text": "سواری دولتی", "callback_data": "vtype_government"}],
            [{"text": "وانت شخصی", "callback_data": "vtype_pickup_personal"}, {"text": "وانت دولتی", "callback_data": "vtype_pickup_government"}],
            [{"text": "وانت عمومی", "callback_data": "vtype_pickup_public"}, {"text": "تاکسی", "callback_data": "vtype_taxi"}],
            [{"text": "خودرو سنگین یا نیمه سنگین", "callback_data": "vtype_heavy"}, {"text": "ماشین‌های کشاورزی", "callback_data": "vtype_agricultural"}],
            [{"text": "گذر موقت", "callback_data": "vtype_temporary"}, {"text": "مناطق آزاد", "callback_data": "vtype_freezone"}],
            [{"text": "مناطق آزاد قدیم", "callback_data": "vtype_old_freezone"}, {"text": "تاریخی", "callback_data": "vtype_historical"}],
            [{"text": "موتور سیکلت قدیمی", "callback_data": "vtype_old_motorcycle"}]
        ]
    }


def vehicle_type_for_inspection_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "سواری بنزینی", "callback_data": "insp_gasoline"}, {"text": "سواری دوگانه", "callback_data": "insp_dual"}],
            [{"text": "سواری دیزلی", "callback_data": "insp_diesel"}, {"text": "سنگین", "callback_data": "insp_heavy"}],
            [{"text": "موتور سیکلت", "callback_data": "insp_motorcycle"}]
        ]
    }


def power_of_attorney_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "دارای وکالت نامه", "callback_data": "poa_yes"}, {"text": "فاقد وکالت نامه", "callback_data": "poa_no"}]
        ]
    }


def recovery_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "بازیابی رمز عبور", "callback_data": "recovery_password"}]
        ]
    }


def declaration_type_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "اظهار نامه توافقی (تبصره 100)", "callback_data": "decl_agreed"}],
            [{"text": "اظهار نامه عادی (خود اظهاری)", "callback_data": "decl_normal"}]
        ]
    }


def tax_payment_type_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "پرداخت قبض مالیاتی", "callback_data": "pay_bill"}],
            [{"text": "پرداخت عوارض خروج از کشور", "callback_data": "pay_exit"}]
        ]
    }


def travel_type_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "سفر سیاحتی", "callback_data": "travel_tourist"}],
            [{"text": "سفر حج", "callback_data": "travel_hajj"}],
            [{"text": "عتبات عالیات، هوایی", "callback_data": "travel_atabat_air"}],
            [{"text": "عتبات عالیات، زمینی یا دریایی", "callback_data": "travel_atabat_ground"}]
        ]
    }


def tax_period_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "فصل بهار", "callback_data": "period_spring"}],
            [{"text": "فصل تابستان", "callback_data": "period_summer"}],
            [{"text": "فصل پاییز", "callback_data": "period_autumn"}],
            [{"text": "فصل زمستان", "callback_data": "period_winter"}]
        ]
    }


def property_status_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "ملک شخصی", "callback_data": "prop_own"}],
            [{"text": "ملک اجاره‌ای", "callback_data": "prop_rent"}]
        ]
    }