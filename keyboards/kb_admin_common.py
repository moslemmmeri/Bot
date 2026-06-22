# keyboards/kb_admin_common.py
# کیبوردهای عمومی مدیریت (شامل کیبوردهای جدید برای نمایش لایه‌لایه و مدیریت ادمین‌ها)
# نسخه کامل با تمام کیبوردها و رفع مشکل کالبک گروه‌بندی سفارشات
# به همراه کیبوردهای مدیریت ستون‌ها (تعداد ستون‌های منو)
# اضافه شده: کیبوردهای مدیریت خطاها و مانیتورینگ و مستندات

from database import (
    get_questions_by_button,
    get_options_by_question,
    get_buttons_by_parent
)
from utils import format_number


# ==================== منوی اصلی مدیریت ====================

def admin_main_keyboard():
    """منوی اصلی پنل مدیریت با دکمه مدیریت ادمین‌ها و بخش‌های جدید"""
    return {
        "inline_keyboard": [
            [{"text": "➕ ایجاد دکمه جدید", "callback_data": "admin_create_button"}],
            [{"text": "🔘 مدیریت دکمه‌ها", "callback_data": "admin_buttons"}],
            [{"text": "📋 مشاهده سفارشات", "callback_data": "admin_orders"}],
            [{"text": "👥 مدیریت ادمین‌ها", "callback_data": "admin_manage_admins"}],
            [{"text": "👤 مدیریت کاربران", "callback_data": "admin_users"}],
            [{"text": "📊 آمار و تحلیل", "callback_data": "admin_analytics"}],
            [{"text": "🎨 برندینگ", "callback_data": "admin_branding"}],
            [{"text": "📦 نسخه‌سازی", "callback_data": "admin_version"}],
            [{"text": "💾 پشتیبان‌گیری", "callback_data": "admin_backup"}],
            [{"text": "🚨 مدیریت خطاها", "callback_data": "admin_errors"}],
            [{"text": "📊 مانیتورینگ", "callback_data": "admin_monitoring"}],
            [{"text": "📊 مدیریت ستون‌های منو", "callback_data": "admin_columns"}],
            [{"text": "⚙️ تنظیمات", "callback_data": "admin_settings"}],
            [{"text": "📚 مستندات", "callback_data": "admin_docs"}],  # <-- دکمه جدید
            [{"text": "🔙 برگشت به ربات", "callback_data": "back_main"}]
        ]
    }


# ==================== کیبوردهای مدیریت ادمین‌ها ====================

def admin_admins_list_keyboard(admins, page=0, per_page=5, total=0):
    """کیبورد نمایش لیست ادمین‌ها با صفحه‌بندی"""
    keyboard = []
    if not admins:
        keyboard.append([{"text": "❌ هیچ ادمینی یافت نشد", "callback_data": "admin_none"}])
    else:
        for admin in admins:
            user_id = admin['user_id']
            role = admin.get('role', 'admin')
            is_active = admin.get('is_active', 1)
            status_icon = "🟢" if is_active == 1 else "🔴"
            role_icons = {'owner': '👑', 'admin': '🛡️', 'manager': '📋', 'observer': '👁️'}
            role_icon = role_icons.get(role, '👤')
            display_name = admin.get('display_name', str(user_id))
            keyboard.append([
                {"text": f"{status_icon} {role_icon} {display_name} - {role}",
                 "callback_data": f"admin_admin_detail_{user_id}"}
            ])
    nav_row = []
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    if page > 0:
        nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_admins_page_{page-1}"})
    if page < total_pages - 1:
        nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_admins_page_{page+1}"})
    if nav_row:
        keyboard.append(nav_row)
    keyboard.append([
        {"text": "➕ افزودن ادمین جدید", "callback_data": "admin_add_admin_start"},
        {"text": "🔍 جستجو", "callback_data": "admin_search_admin"}
    ])
    keyboard.append([{"text": "📊 آمار ادمین‌ها", "callback_data": "admin_admins_stats"}])
    keyboard.append([{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}])
    return {"inline_keyboard": keyboard}


def admin_admin_detail_keyboard(user_id, role, is_active, is_owner=False):
    """کیبورد جزئیات یک ادمین با گزینه‌های مدیریت"""
    keyboard = []
    status_text = "🟢 فعال" if is_active == 1 else "🔴 غیرفعال"
    keyboard.append([
        {"text": f"📌 وضعیت: {status_text}", "callback_data": f"admin_toggle_status_{user_id}"}
    ])
    if not is_owner:
        keyboard.append([
            {"text": "🔄 تغییر نقش", "callback_data": f"admin_change_role_{user_id}"}
        ])
    if not is_owner:
        keyboard.append([
            {"text": "🗑️ حذف ادمین", "callback_data": f"admin_remove_admin_{user_id}"}
        ])
    keyboard.append([
        {"text": "🔙 برگشت به لیست", "callback_data": "admin_manage_admins"}
    ])
    return {"inline_keyboard": keyboard}


def admin_roles_keyboard(user_id, current_role):
    """کیبورد انتخاب نقش جدید برای ادمین"""
    roles = [('admin', '🛡️ ادمین'), ('manager', '📋 مدیر'), ('observer', '👁️ ناظر')]
    keyboard = []
    for role, label in roles:
        selected = "✅ " if role == current_role else ""
        keyboard.append([
            {"text": f"{selected}{label}", "callback_data": f"admin_change_role_select_{user_id}_{role}"}
        ])
    keyboard.append([
        {"text": "🔙 انصراف", "callback_data": f"admin_admin_detail_{user_id}"}
    ])
    return {"inline_keyboard": keyboard}


def admin_add_admin_roles_keyboard(user_id):
    """کیبورد انتخاب نقش برای افزودن ادمین جدید"""
    roles = [('admin', '🛡️ ادمین'), ('manager', '📋 مدیر'), ('observer', '👁️ ناظر')]
    keyboard = []
    for role, label in roles:
        keyboard.append([
            {"text": f"{label}", "callback_data": f"admin_add_admin_role_{user_id}_{role}"}
        ])
    keyboard.append([
        {"text": "🔙 انصراف", "callback_data": "admin_manage_admins"}
    ])
    return {"inline_keyboard": keyboard}


def admin_remove_confirm_keyboard(user_id, username=""):
    """کیبورد تایید حذف ادمین"""
    display_name = username if username else user_id
    return {
        "inline_keyboard": [
            [{"text": f"⚠️ آیا از حذف ادمین «{display_name}» مطمئن هستید؟"}],
            [{"text": "✅ بله، حذف شود", "callback_data": f"admin_remove_confirm_{user_id}"}],
            [{"text": "❌ خیر، انصراف", "callback_data": f"admin_admin_detail_{user_id}"}]
        ]
    }


def admin_search_keyboard():
    """کیبورد جستجوی ادمین‌ها"""
    return {
        "inline_keyboard": [
            [{"text": "🔍 جستجو بر اساس شناسه یا نقش", "callback_data": "admin_search_admin"}],
            [{"text": "🔙 برگشت به لیست", "callback_data": "admin_manage_admins"}]
        ]
    }


def admin_stats_keyboard(stats):
    """کیبورد نمایش آمار ادمین‌ها"""
    keyboard = []
    keyboard.append([{"text": "📊 **آمار ادمین‌ها**"}])
    keyboard.append([{"text": f"👥 کل: {stats.get('total', 0)}"}])
    keyboard.append([{"text": f"🟢 فعال: {stats.get('active', 0)}"}])
    keyboard.append([{"text": f"🔴 غیرفعال: {stats.get('inactive', 0)}"}])
    roles = stats.get('roles', {})
    if roles:
        role_labels = {'owner': '👑 مالک', 'admin': '🛡️ ادمین', 'manager': '📋 مدیر', 'observer': '👁️ ناظر'}
        keyboard.append([{"text": "📌 تفکیک نقش‌ها:"}])
        for role, count in roles.items():
            label = role_labels.get(role, role)
            keyboard.append([{"text": f"  {label}: {count}"}])
    keyboard.append([
        {"text": "🔙 برگشت به لیست", "callback_data": "admin_manage_admins"}
    ])
    return {"inline_keyboard": keyboard}


# ==================== کیبوردهای سوالات و گزینه‌ها ====================

def admin_questions_keyboard(button_id):
    questions = get_questions_by_button(button_id)
    keyboard = []
    for q in questions:
        icon = "🔘" if q['needs_button'] == 1 else "❓"
        required = "⭐" if q.get('is_required', 0) == 1 else ""
        val = "🔧" if q.get('validation_enabled', 0) == 1 else ""
        keyboard.append([
            {"text": f"{icon}{required}{val} {q['question_text'][:30]}",
             "callback_data": f"admin_q_{q['id']}"}
        ])
    keyboard.append([
        {"text": "➕ افزودن سوال جدید", "callback_data": f"admin_q_add_{button_id}"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت به دکمه‌ها", "callback_data": "admin_buttons"}
    ])
    return {"inline_keyboard": keyboard}


def admin_question_options_keyboard(question_id):
    options = get_options_by_question(question_id)
    keyboard = []
    for opt in options:
        keyboard.append([
            {"text": f"🔘 {opt['option_text']}",
             "callback_data": f"admin_qopt_{opt['id']}"}
        ])
    keyboard.append([
        {"text": "➕ افزودن گزینه جدید", "callback_data": f"admin_qopt_add_{question_id}"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت به سوالات", "callback_data": f"admin_q_back_{question_id}"}
    ])
    return {"inline_keyboard": keyboard}


def admin_submenu_keyboard(button_id):
    submenus = get_buttons_by_parent(button_id)
    keyboard = []
    for sub in submenus:
        keyboard.append([
            {"text": f"  └─ {sub['name']}",
             "callback_data": f"admin_btn_{sub['id']}"}
        ])
    keyboard.append([
        {"text": "➕ افزودن زیرمنو جدید", "callback_data": f"admin_sub_add_{button_id}"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت", "callback_data": f"admin_btn_{button_id}"}
    ])
    return {"inline_keyboard": keyboard}


# ==================== کیبوردهای دسته‌بندی‌ها ====================

def admin_categories_keyboard(categories):
    keyboard = []
    for cat in categories:
        keyboard.append([
            {"text": f"📂 {cat['name']}", "callback_data": f"admin_cat_{cat['id']}"},
            {"text": "✏️", "callback_data": f"admin_cat_edit_{cat['id']}"},
            {"text": "🗑️", "callback_data": f"admin_cat_del_confirm_{cat['id']}"}
        ])
    if not categories:
        keyboard.append([{"text": "❌ هیچ دسته‌بندی یافت نشد", "callback_data": "admin_none"}])
    keyboard.append([
        {"text": "➕ افزودن دسته‌بندی جدید", "callback_data": "admin_add_category"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت", "callback_data": "admin_back"}
    ])
    return {"inline_keyboard": keyboard}


def admin_category_delete_confirm_keyboard(cat_id, cat_name):
    return {
        "inline_keyboard": [
            [{"text": f"⚠️ آیا دسته‌بندی «{cat_name}» و تمام دکمه‌های آن حذف شود؟"}],
            [{"text": "✅ بله، حذف شود", "callback_data": f"admin_cat_del_yes_{cat_id}"}],
            [{"text": "❌ خیر، انصراف", "callback_data": f"admin_cat_{cat_id}"}]
        ]
    }


def admin_category_buttons_keyboard(buttons, category_name, category_id):
    keyboard = []
    for btn in buttons:
        if btn.get('has_submenu', 0) == 1:
            btn_text = f"📂 {btn['name']}"
        else:
            btn_text = f"📄 {btn['name']}"
        keyboard.append([
            {"text": btn_text, "callback_data": f"admin_btn_{btn['id']}"},
            {"text": "🗑️ حذف", "callback_data": f"admin_btn_del_{btn['id']}"}
        ])
    if not buttons:
        keyboard.append([{"text": "❌ هیچ دکمه‌ای در این دسته‌بندی یافت نشد", "callback_data": "admin_none"}])
    keyboard.append([
        {"text": "➕ افزودن دکمه جدید", "callback_data": f"admin_add_btn_in_cat_{category_id}"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت به لیست دسته‌بندی‌ها", "callback_data": "admin_buttons"}
    ])
    return {"inline_keyboard": keyboard}


def admin_submenu_list_keyboard(submenus, parent_name, parent_id, category_id):
    keyboard = []
    for sub in submenus:
        keyboard.append([
            {"text": f"  └─ {sub['name']}", "callback_data": f"admin_btn_{sub['id']}"},
            {"text": "🗑️ حذف", "callback_data": f"admin_btn_del_{sub['id']}"}
        ])
    if not submenus:
        keyboard.append([{"text": "❌ این دکمه زیرمنویی ندارد", "callback_data": "admin_none"}])
    keyboard.append([
        {"text": "➕ افزودن زیرمنو جدید", "callback_data": f"admin_sub_add_{parent_id}"}
    ])
    keyboard.append([
        {"text": f"🔙 برگشت به {parent_name}", "callback_data": f"admin_cat_{category_id}"}
    ])
    return {"inline_keyboard": keyboard}


# ==================== کیبوردهای مدیریت ستون‌ها ====================

def admin_category_columns_keyboard(category_id, current_columns):
    columns_options = [(1, "۱ ستون"), (2, "۲ ستون"), (3, "۳ ستون"), (4, "۴ ستون"),
                       (5, "۵ ستون"), (6, "۶ ستون"), (7, "۷ ستون"), (8, "۸ ستون")]
    keyboard = []
    for col, label in columns_options:
        selected = "✅ " if col == current_columns else ""
        keyboard.append([
            {"text": f"{selected}{label}", "callback_data": f"admin_cat_set_columns_select_{category_id}_{col}"}
        ])
    keyboard.append([
        {"text": "🔙 انصراف", "callback_data": f"admin_cat_{category_id}"}
    ])
    return {"inline_keyboard": keyboard}


def admin_button_columns_keyboard(button_id, current_columns):
    keyboard = []
    selected = "✅ " if current_columns is None else ""
    keyboard.append([
        {"text": f"{selected}پیش‌فرض (استفاده از تنظیمات دسته‌بندی)",
         "callback_data": f"admin_btn_set_columns_select_{button_id}_0"}
    ])
    columns_options = [(1, "۱ ستون"), (2, "۲ ستون"), (3, "۳ ستون"), (4, "۴ ستون"),
                       (5, "۵ ستون"), (6, "۶ ستون"), (7, "۷ ستون"), (8, "۸ ستون")]
    for col, label in columns_options:
        selected = "✅ " if col == current_columns else ""
        keyboard.append([
            {"text": f"{selected}{label}", "callback_data": f"admin_btn_set_columns_select_{button_id}_{col}"}
        ])
    keyboard.append([
        {"text": "🔙 انصراف", "callback_data": f"admin_btn_{button_id}"}
    ])
    return {"inline_keyboard": keyboard}


# ==================== کیبوردهای شرط‌گذاری ====================

def condition_operator_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "برابر است با (==)", "callback_data": "admin_cond_op_=="}],
            [{"text": "مخالف است با (!=)", "callback_data": "admin_cond_op_!="}],
            [{"text": "شامل باشد (contains)", "callback_data": "admin_cond_op_contains"}],
            [{"text": "شروع با (startswith)", "callback_data": "admin_cond_op_startswith"}],
            [{"text": "بزرگتر از (>)", "callback_data": "admin_cond_op_>"}],
            [{"text": "کوچکتر از (<)", "callback_data": "admin_cond_op_<"}],
            [{"text": "بزرگتر یا مساوی (>=)", "callback_data": "admin_cond_op_>="}],
            [{"text": "کوچکتر یا مساوی (<=)", "callback_data": "admin_cond_op_<="}],
            [{"text": "بین دو عدد (between)", "callback_data": "admin_cond_op_between"}]
        ]
    }


def logic_operator_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "✅ AND (همه شرط‌ها)", "callback_data": "admin_cond_logic_AND"}],
            [{"text": "🔄 OR (حداقل یکی)", "callback_data": "admin_cond_logic_OR"}]
        ]
    }


def yes_no_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "✅ بله", "callback_data": "admin_condition_yes"}],
            [{"text": "❌ خیر", "callback_data": "admin_condition_no"}]
        ]
    }


# ==================== کیبوردهای مدیریت پیشرفته سفارشات ====================

def admin_orders_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📅 گروه‌بندی بر اساس تاریخ", "callback_data": "admin_orders_group_by_date"}],
            [{"text": "🎯 فیلتر سفارشات", "callback_data": "admin_orders_filter"}],
            [{"text": "🔍 جستجوی سفارشات", "callback_data": "admin_orders_search"}],
            [{"text": "📊 آمار سفارشات", "callback_data": "admin_orders_stats"}],
            [{"text": "📥 خروجی CSV", "callback_data": "admin_orders_export"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


def admin_orders_filter_keyboard(current_status=None, current_service=None):
    keyboard = []
    statuses = [('pending', '⏳ در انتظار پرداخت'), ('paid', '✅ پرداخت شده'), ('completed', '✅ تکمیل شده')]
    keyboard.append([{"text": "📌 **فیلتر بر اساس وضعیت:**"}])
    for status, label in statuses:
        selected = "✅ " if status == current_status else ""
        keyboard.append([
            {"text": f"{selected}{label}", "callback_data": f"admin_orders_filter_status_{status}"}
        ])
    keyboard.append([
        {"text": "🔄 نمایش همه", "callback_data": "admin_orders_filter_status_all"}
    ])
    keyboard.append([{"text": "🔘 **فیلتر بر اساس سرویس:**"}])
    if current_service:
        from database import get_button_by_id
        btn = get_button_by_id(current_service)
        service_name = btn['name'] if btn else f"سرویس {current_service}"
        keyboard.append([{"text": f"✅ سرویس انتخاب‌شده: {service_name}", "callback_data": "admin_orders_filter_service"}])
    else:
        keyboard.append([
            {"text": "📋 انتخاب سرویس", "callback_data": "admin_orders_filter_service"}
        ])
    keyboard.append([
        {"text": "✅ اعمال فیلتر", "callback_data": "admin_orders_filter_apply"},
        {"text": "❌ حذف فیلتر", "callback_data": "admin_orders_filter_clear"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت", "callback_data": "admin_orders"}
    ])
    return {"inline_keyboard": keyboard}


def admin_orders_filter_service_keyboard(services):
    keyboard = []
    for service in services:
        keyboard.append([
            {"text": f"📌 {service['name']}", "callback_data": f"admin_orders_filter_service_{service['id']}"}
        ])
    keyboard.append([
        {"text": "🔙 برگشت به فیلتر", "callback_data": "admin_orders_filter"}
    ])
    return {"inline_keyboard": keyboard}


def admin_orders_status_keyboard(order_id, current_status):
    statuses = [
        ('pending', '⏳ در انتظار پرداخت'),
        ('paid', '✅ پرداخت شده'),
        ('completed', '✅ تکمیل شده'),
        ('cancelled', '❌ لغو شده'),
        ('failed', '❌ ناموفق'),
        ('refunded', '🔄 بازگشت وجه')
    ]
    keyboard = []
    for status, label in statuses:
        selected = "✅ " if status == current_status else ""
        keyboard.append([
            {"text": f"{selected}{label}", "callback_data": f"admin_order_status_change_{order_id}_{status}"}
        ])
    keyboard.append([
        {"text": "🔙 انصراف", "callback_data": f"admin_order_{order_id}"}
    ])
    return {"inline_keyboard": keyboard}


def admin_order_delete_confirm_keyboard(order_id):
    return {
        "inline_keyboard": [
            [{"text": f"⚠️ آیا از حذف سفارش #{order_id} مطمئن هستید؟"}],
            [{"text": "✅ بله، حذف شود", "callback_data": f"admin_order_delete_yes_{order_id}"}],
            [{"text": "❌ خیر، انصراف", "callback_data": f"admin_order_{order_id}"}]
        ]
    }


def admin_order_detail_actions_keyboard(order_id, status):
    return {
        "inline_keyboard": [
            [{"text": "🔄 تغییر وضعیت", "callback_data": f"admin_order_status_{order_id}"}],
            [{"text": "📝 افزودن یادداشت", "callback_data": f"admin_order_note_{order_id}"}],
            [{"text": "🗑️ حذف سفارش", "callback_data": f"admin_order_delete_{order_id}"}],
            [{"text": "🔙 برگشت", "callback_data": "admin_orders"}]
        ]
    }


def admin_order_note_keyboard(order_id):
    return {
        "inline_keyboard": [
            [{"text": "📝 لطفاً متن یادداشت را وارد کنید:"}],
            [{"text": "🔙 انصراف", "callback_data": f"admin_order_{order_id}"}]
        ]
    }


def admin_order_stats_keyboard(stats):
    """کیبورد نمایش آمار سفارشات - اصلاح شده با مدیریت None"""
    keyboard = []
    
    # ایمن‌سازی مقادیر عددی
    total = stats.get('total', 0)
    if total is None:
        total = 0
    
    total_amount = stats.get('total_amount', 0)
    if total_amount is None:
        total_amount = 0
    
    avg_amount = stats.get('avg_amount', 0)
    if avg_amount is None:
        avg_amount = 0
    
    total_users = stats.get('total_users', 0)
    if total_users is None:
        total_users = 0
    
    keyboard.append([{"text": "📊 **آمار سفارشات**"}])
    keyboard.append([{"text": f"📦 تعداد کل: {format_number(total)}"}])
    keyboard.append([{"text": f"💰 مجموع مبلغ: {format_number(total_amount)} ریال"}])
    keyboard.append([{"text": f"📊 میانگین مبلغ: {format_number(int(avg_amount))} ریال"}])
    keyboard.append([{"text": f"👥 تعداد کاربران: {format_number(total_users)}"}])
    
    statuses = stats.get('statuses', {})
    if statuses:
        status_labels = {
            'pending': '⏳ در انتظار پرداخت',
            'paid': '✅ پرداخت شده',
            'completed': '✅ تکمیل شده',
            'cancelled': '❌ لغو شده',
            'failed': '❌ ناموفق',
            'refunded': '🔄 بازگشت وجه'
        }
        keyboard.append([{"text": "📌 تفکیک وضعیت:"}])
        for status, count in statuses.items():
            label = status_labels.get(status, status)
            keyboard.append([{"text": f"  {label}: {count}"}])
    
    top_service_id = stats.get('top_service_id')
    if top_service_id:
        from database import get_button_by_id
        service = get_button_by_id(top_service_id)
        service_name = service['name'] if service else f"سرویس {top_service_id}"
        top_service_count = stats.get('top_service_count', 0) or 0
        keyboard.append([
            {"text": f"🏆 بیشترین سرویس: {service_name} ({format_number(top_service_count)} سفارش)"}
        ])
    
    keyboard.append([
        {"text": "🔙 برگشت", "callback_data": "admin_orders"}
    ])
    
    return {"inline_keyboard": keyboard}


def admin_orders_search_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔍 لطفاً کلمه کلیدی (کد رهگیری/نام کاربر/شناسه) را وارد کنید:"}],
            [{"text": "🔙 برگشت", "callback_data": "admin_orders"}]
        ]
    }


def admin_orders_export_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📥 دریافت خروجی CSV از همه سفارشات", "callback_data": "admin_orders_export"}],
            [{"text": "📥 دریافت خروجی CSV از سفارشات فیلتر شده", "callback_data": "admin_orders_export_filtered"}],
            [{"text": "🔙 برگشت", "callback_data": "admin_orders"}]
        ]
    }


def admin_order_reminder_keyboard(orders):
    keyboard = []
    if not orders:
        keyboard.append([{"text": "✅ هیچ سفارشی نیاز به یادآوری ندارد", "callback_data": "admin_none"}])
    else:
        for order in orders[:10]:
            order_id = order.get('id')
            user_id = order.get('user_id')
            amount = order.get('payment_amount', 0) or 0
            keyboard.append([
                {"text": f"🆔 #{order_id} - کاربر {user_id} - {format_number(amount)} ریال",
                 "callback_data": f"admin_order_remind_{order_id}"}
            ])
        if len(orders) > 10:
            keyboard.append([
                {"text": f"... و {len(orders) - 10} سفارش دیگر", "callback_data": "admin_none"}
            ])
    keyboard.append([
        {"text": "📨 ارسال یادآوری به همه", "callback_data": "admin_order_remind_all"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت", "callback_data": "admin_orders"}
    ])
    return {"inline_keyboard": keyboard}


# ==================== کیبوردهای مدیریت خطاها ====================

def admin_errors_main_keyboard(stats):
    """کیبورد اصلی مدیریت خطاها (اصلاح‌شده)"""
    unresolved = stats.get('unresolved', 0) or 0
    return {
        "inline_keyboard": [
            [{"text": f"📋 لیست خطاها ({stats.get('total', 0) or 0})", "callback_data": "admin_errors_list"}],
            [{"text": f"⚠️ خطاهای حل‌نشده ({unresolved})", "callback_data": "admin_errors_list_unresolved"}],
            [{"text": "📊 آمار خطاها", "callback_data": "admin_errors_stats"}],
            [{"text": "🗑️ پاکسازی خطاهای قدیمی (بیش از ۳۰ روز)", "callback_data": "admin_errors_cleanup"}],
            [{"text": "🗑️ حذف همه خطاها (⚠️ غیرقابل بازگشت)", "callback_data": "admin_errors_clear_all"}],
            [{"text": "🔙 برگشت به منو", "callback_data": "admin_back"}]
        ]
    }


def admin_errors_list_keyboard(errors, page=0, per_page=10, total=0, show_unresolved=False):
    """کیبورد نمایش لیست خطاها با صفحه‌بندی (اصلاح‌شده)"""
    try:
        keyboard = []
        if not errors:
            keyboard.append([{"text": "❌ هیچ خطایی یافت نشد", "callback_data": "admin_none"}])
        else:
            for err in errors:
                error_id = err.get('id', '?')
                error_type = err.get('error_type', 'general')
                error_message = err.get('error_message', 'بدون پیام')[:30]
                is_resolved = err.get('is_resolved', 0)
                status_icon = "✅" if is_resolved == 1 else "🔴"
                from utils import get_error_type_icon
                type_icon = get_error_type_icon(error_type)
                keyboard.append([
                    {"text": f"{status_icon} {type_icon} #{error_id} - {error_message}",
                     "callback_data": f"admin_error_detail_{error_id}"}
                ])
        nav_row = []
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_errors_list_page_{page-1}_{'unresolved' if show_unresolved else 'all'}"})
        if page < total_pages - 1:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_errors_list_page_{page+1}_{'unresolved' if show_unresolved else 'all'}"})
        if nav_row:
            keyboard.append(nav_row)
        keyboard.append([
            {"text": "📊 آمار خطاها", "callback_data": "admin_errors_stats"},
            {"text": "🗑️ پاکسازی قدیمی‌ها", "callback_data": "admin_errors_cleanup"}
        ])
        if show_unresolved:
            keyboard.append([
                {"text": "📋 نمایش همه خطاها", "callback_data": "admin_errors_list"}
            ])
        else:
            keyboard.append([
                {"text": "⚠️ فقط خطاهای حل‌نشده", "callback_data": "admin_errors_list_unresolved"}
            ])
        keyboard.append([
            {"text": "🔙 برگشت به مدیریت خطاها", "callback_data": "admin_errors"}
        ])
        return {"inline_keyboard": keyboard}
    except Exception as e:
        from utils.error_handler import log_general_error
        log_general_error(f"Error in admin_errors_list_keyboard: {str(e)}", traceback=str(e))
        return {"inline_keyboard": [[{"text": "❌ خطا در بارگذاری خطاها", "callback_data": "admin_errors"}]]}


def admin_errors_detail_keyboard(error_id, is_resolved):
    """کیبورد جزئیات یک خطا با گزینه‌های مدیریت"""
    keyboard = []
    if is_resolved == 0:
        keyboard.append([
            {"text": "✅ علامت‌گذاری به عنوان حل‌شده", "callback_data": f"admin_error_resolve_{error_id}"}
        ])
    else:
        keyboard.append([
            {"text": "🔄 بازگشایی (حل‌نشده)", "callback_data": f"admin_error_unresolve_{error_id}"}
        ])
    keyboard.append([
        {"text": "🗑️ حذف این خطا", "callback_data": f"admin_error_delete_{error_id}"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت به لیست", "callback_data": "admin_errors_list"}
    ])
    return {"inline_keyboard": keyboard}


def admin_errors_stats_keyboard():
    """کیبورد نمایش آمار خطاها"""
    return {
        "inline_keyboard": [
            [{"text": "📋 مشاهده لیست خطاها", "callback_data": "admin_errors_list"}],
            [{"text": "⚠️ فقط خطاهای حل‌نشده", "callback_data": "admin_errors_list_unresolved"}],
            [{"text": "🗑️ پاکسازی خطاهای قدیمی", "callback_data": "admin_errors_cleanup"}],
            [{"text": "🔙 برگشت", "callback_data": "admin_errors"}]
        ]
    }


def admin_errors_cleanup_confirm_keyboard():
    """کیبورد تایید پاکسازی خطاهای قدیمی"""
    return {
        "inline_keyboard": [
            [{"text": "⚠️ آیا از پاکسازی خطاهای قدیمی‌تر از ۳۰ روز مطمئن هستید؟"}],
            [{"text": "✅ بله، پاکسازی شود", "callback_data": "admin_errors_cleanup_confirm"}],
            [{"text": "❌ خیر، انصراف", "callback_data": "admin_errors"}]
        ]
    }


def admin_errors_clear_all_confirm_keyboard(total):
    """کیبورد تایید حذف همه خطاها"""
    return {
        "inline_keyboard": [
            [{"text": f"⚠️ آیا از حذف همه {total} خطا مطمئن هستید؟"}],
            [{"text": "⚠️ این عملیات غیرقابل بازگشت است!"}],
            [{"text": "✅ بله، همه حذف شوند", "callback_data": "admin_errors_clear_all_confirm"}],
            [{"text": "❌ خیر، انصراف", "callback_data": "admin_errors"}]
        ]
    }


# ==================== کیبوردهای مانیتورینگ ====================

def monitoring_main_keyboard():
    """منوی اصلی مانیتورینگ"""
    return {
        "inline_keyboard": [
            [{"text": "📈 داشبورد لحظه‌ای", "callback_data": "monitoring_dashboard"}],
            [{"text": "🩺 بررسی سلامت", "callback_data": "monitoring_health"}],
            [{"text": "🔔 هشدارها", "callback_data": "monitoring_alerts"}],
            [{"text": "📊 متریک‌ها", "callback_data": "monitoring_metrics"}],
            [{"text": "📄 گزارش‌ها", "callback_data": "monitoring_reports"}],
            [{"text": "📚 مستندات", "callback_data": "admin_docs"}],  # <-- دکمه مستندات در منوی مانیتورینگ
            [{"text": "🔙 برگشت به منوی مدیریت", "callback_data": "admin_back"}]
        ]
    }


def monitoring_dashboard_keyboard():
    """کیبورد داشبورد مانیتورینگ"""
    return {
        "inline_keyboard": [
            [{"text": "🔄 به‌روزرسانی", "callback_data": "monitoring_dashboard_refresh"}],
            [{"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring"}]
        ]
    }


def monitoring_health_keyboard():
    """کیبورد بررسی سلامت"""
    return {
        "inline_keyboard": [
            [{"text": "🔄 اجرای مجدد بررسی سلامت", "callback_data": "monitoring_health_check"}],
            [{"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring"}]
        ]
    }


def monitoring_alerts_keyboard(show_resolved=False):
    """کیبورد مدیریت هشدارها"""
    return {
        "inline_keyboard": [
            [{"text": "🔔 هشدارهای فعال", "callback_data": "monitoring_alerts_active"}],
            [{"text": "✅ هشدارهای حل‌شده", "callback_data": "monitoring_alerts_resolved"}],
            [{"text": "📋 همه هشدارها", "callback_data": "monitoring_alerts_all"}],
            [{"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring"}]
        ]
    }


def monitoring_alerts_list_keyboard(alerts, page=0, per_page=10, total=0):
    """کیبورد نمایش لیست هشدارها با صفحه‌بندی"""
    keyboard = []
    if not alerts:
        keyboard.append([{"text": "✅ هیچ هشداری یافت نشد", "callback_data": "monitoring_none"}])
    else:
        for alert in alerts:
            alert_id = alert.get('id', '?')
            level = alert.get('alert_level', 'info')
            title = alert.get('title', 'بدون عنوان')[:25]
            is_resolved = alert.get('is_resolved', 0)
            status_icon = "✅" if is_resolved == 1 else "🔴"
            level_icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}.get(level, "📌")
            keyboard.append([
                {"text": f"{status_icon} {level_icon} #{alert_id} - {title}",
                 "callback_data": f"monitoring_alert_detail_{alert_id}"}
            ])
    nav_row = []
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    if page > 0:
        nav_row.append({"text": "⬅️ قبلی", "callback_data": f"monitoring_alerts_page_{page-1}"})
    if page < total_pages - 1:
        nav_row.append({"text": "➡️ بعدی", "callback_data": f"monitoring_alerts_page_{page+1}"})
    if nav_row:
        keyboard.append(nav_row)
    keyboard.append([
        {"text": "🔙 برگشت به هشدارها", "callback_data": "monitoring_alerts"}
    ])
    return {"inline_keyboard": keyboard}


def monitoring_alert_detail_keyboard(alert_id, is_resolved):
    """کیبورد جزئیات یک هشدار"""
    keyboard = []
    if not is_resolved:
        keyboard.append([
            {"text": "✅ حل کردن هشدار", "callback_data": f"monitoring_alert_resolve_{alert_id}"}
        ])
    else:
        keyboard.append([
            {"text": "🔄 بازگشایی هشدار", "callback_data": f"monitoring_alert_unresolve_{alert_id}"}
        ])
    keyboard.append([
        {"text": "🗑️ حذف هشدار", "callback_data": f"monitoring_alert_delete_{alert_id}"}
    ])
    keyboard.append([
        {"text": "🔙 برگشت به لیست", "callback_data": "monitoring_alerts_all"}
    ])
    return {"inline_keyboard": keyboard}


def monitoring_metrics_keyboard():
    """کیبورد متریک‌ها"""
    return {
        "inline_keyboard": [
            [{"text": "📊 خلاصه متریک‌ها", "callback_data": "monitoring_metrics_summary"}],
            [{"text": "📈 نمایش متریک خاص", "callback_data": "monitoring_metrics_select"}],
            [{"text": "🗑️ پاکسازی متریک‌های قدیمی", "callback_data": "monitoring_metrics_cleanup"}],
            [{"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring"}]
        ]
    }


def monitoring_metrics_select_keyboard(metric_types):
    """کیبورد انتخاب نوع متریک (با استفاده از لیست metric_types)"""
    keyboard = []
    for metric in metric_types:
        keyboard.append([
            {"text": f"📌 {metric}", "callback_data": f"monitoring_metrics_show_{metric}"}
        ])
    keyboard.append([
        {"text": "🔙 برگشت", "callback_data": "monitoring_metrics"}
    ])
    return {"inline_keyboard": keyboard}


def monitoring_reports_keyboard():
    """کیبورد گزارش‌ها"""
    return {
        "inline_keyboard": [
            [{"text": "📅 گزارش روزانه", "callback_data": "monitoring_report_daily"}],
            [{"text": "📅 گزارش هفتگی", "callback_data": "monitoring_report_weekly"}],
            [{"text": "📅 گزارش ماهانه", "callback_data": "monitoring_report_monthly"}],
            [{"text": "📋 لیست گزارش‌های ذخیره‌شده", "callback_data": "monitoring_reports_list"}],
            [{"text": "🗑️ پاکسازی گزارش‌های قدیمی", "callback_data": "monitoring_reports_cleanup"}],
            [{"text": "🔙 برگشت به منوی مانیتورینگ", "callback_data": "admin_monitoring"}]
        ]
    }


def monitoring_reports_list_keyboard(reports, page=0, per_page=10, total=0):
    """کیبورد نمایش لیست گزارش‌های ذخیره‌شده با صفحه‌بندی"""
    keyboard = []
    if not reports:
        keyboard.append([{"text": "❌ هیچ گزارشی یافت نشد", "callback_data": "monitoring_none"}])
    else:
        for report in reports:
            report_id = report.get('id', '?')
            title = report.get('title', 'بدون عنوان')[:30]
            status = report.get('status', 'pending')
            status_icon = {"pending": "⏳", "completed": "✅", "failed": "❌"}.get(status, "📌")
            keyboard.append([
                {"text": f"{status_icon} #{report_id} - {title}",
                 "callback_data": f"monitoring_report_detail_{report_id}"}
            ])
    nav_row = []
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    if page > 0:
        nav_row.append({"text": "⬅️ قبلی", "callback_data": f"monitoring_reports_page_{page-1}"})
    if page < total_pages - 1:
        nav_row.append({"text": "➡️ بعدی", "callback_data": f"monitoring_reports_page_{page+1}"})
    if nav_row:
        keyboard.append(nav_row)
    keyboard.append([
        {"text": "🔙 برگشت به گزارش‌ها", "callback_data": "monitoring_reports"}
    ])
    return {"inline_keyboard": keyboard}


def monitoring_report_detail_keyboard(report_id):
    """کیبورد جزئیات یک گزارش"""
    return {
        "inline_keyboard": [
            [{"text": "🗑️ حذف این گزارش", "callback_data": f"monitoring_report_delete_{report_id}"}],
            [{"text": "🔙 برگشت به لیست", "callback_data": "monitoring_reports_list"}]
        ]
    }


# ==================== صادر کردن ====================

__all__ = [
    'admin_main_keyboard',
    'admin_questions_keyboard',
    'admin_question_options_keyboard',
    'admin_submenu_keyboard',
    'condition_operator_keyboard',
    'logic_operator_keyboard',
    'yes_no_keyboard',
    'admin_categories_keyboard',
    'admin_category_buttons_keyboard',
    'admin_submenu_list_keyboard',
    'admin_category_delete_confirm_keyboard',
    'admin_category_columns_keyboard',
    'admin_button_columns_keyboard',
    'admin_admins_list_keyboard',
    'admin_admin_detail_keyboard',
    'admin_roles_keyboard',
    'admin_add_admin_roles_keyboard',
    'admin_remove_confirm_keyboard',
    'admin_search_keyboard',
    'admin_stats_keyboard',
    'admin_orders_menu_keyboard',
    'admin_orders_filter_keyboard',
    'admin_orders_filter_service_keyboard',
    'admin_orders_status_keyboard',
    'admin_order_delete_confirm_keyboard',
    'admin_order_detail_actions_keyboard',
    'admin_order_note_keyboard',
    'admin_order_stats_keyboard',
    'admin_orders_search_keyboard',
    'admin_orders_export_keyboard',
    'admin_order_reminder_keyboard',
    # کیبوردهای مدیریت خطاها
    'admin_errors_main_keyboard',
    'admin_errors_list_keyboard',
    'admin_errors_detail_keyboard',
    'admin_errors_stats_keyboard',
    'admin_errors_cleanup_confirm_keyboard',
    'admin_errors_clear_all_confirm_keyboard',
    # کیبوردهای مانیتورینگ
    'monitoring_main_keyboard',
    'monitoring_dashboard_keyboard',
    'monitoring_health_keyboard',
    'monitoring_alerts_keyboard',
    'monitoring_alerts_list_keyboard',
    'monitoring_alert_detail_keyboard',
    'monitoring_metrics_keyboard',
    'monitoring_metrics_select_keyboard',
    'monitoring_reports_keyboard',
    'monitoring_reports_list_keyboard',
    'monitoring_report_detail_keyboard',
]