# admin_panel/advanced_search.py
# جستجوی پیشرفته در سفارشات با فیلترهای متعدد
# شامل: جستجو بر اساس تاریخ، مبلغ، وضعیت، سرویس، کاربر، کلمات کلیدی و ...

import json
import traceback  # ✅ اضافه شد برای traceback کامل
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from logger_config import logger
from core import send_message, user_states, OWNER_ID
from database import (
    get_dynamic_orders,
    get_dynamic_order_by_id,
    get_button_by_id,
    get_user,
    search_users,
    get_db_connection,
    get_dashboard_stats,
    get_advanced_stats_aggregated,
)
from keyboards import admin_main_keyboard
from .helpers import format_number, format_datetime, format_percent, get_service_name, get_fullname_from_order
from utils.error_handler import (
    log_callback_error,
    log_general_error,
    log_database_error,
    log_security_error
)


# ============================================================
# کلاس جستجوی پیشرفته
# ============================================================

class AdvancedSearch:
    """جستجوی پیشرفته در سفارشات"""
    
    def __init__(self, orders: List[Dict] = None):
        try:
            if orders is None:
                self._orders = get_dynamic_orders()
            else:
                self._orders = orders
            
            self._results = self._orders.copy()
            self._filters_applied = []
        except Exception as e:
            log_database_error(
                f"Error initializing AdvancedSearch: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
            self._orders = []
            self._results = []
            self._filters_applied = []
    
    def reset(self) -> 'AdvancedSearch':
        """بازنشانی نتایج"""
        try:
            self._results = self._orders.copy()
            self._filters_applied = []
        except Exception as e:
            log_general_error(
                f"Error in AdvancedSearch.reset: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        return self
    
    def search_by_keyword(self, keyword: str) -> 'AdvancedSearch':
        """جستجو بر اساس کلمه کلیدی در سفارشات"""
        try:
            if not keyword or keyword.strip() == "":
                return self
            
            keyword_lower = keyword.lower().strip()
            filtered = []
            
            for order in self._results:
                # جستجو در شناسه سفارش
                if str(order.get('id', '')).lower() == keyword_lower:
                    filtered.append(order)
                    continue
                
                # جستجو در شناسه کاربر
                if str(order.get('user_id', '')).lower() == keyword_lower:
                    filtered.append(order)
                    continue
                
                # جستجو در کد رهگیری
                tracking = order.get('tracking_code', '')
                if tracking and keyword_lower in str(tracking).lower():
                    filtered.append(order)
                    continue
                
                # جستجو در نام کاربر (از order_data)
                fullname = get_fullname_from_order(order)
                if fullname and keyword_lower in fullname.lower():
                    filtered.append(order)
                    continue
                
                # جستجو در پاسخ‌ها
                order_data = order.get('order_data', {})
                if isinstance(order_data, str):
                    try:
                        order_data = json.loads(order_data)
                    except:
                        order_data = {}
                
                answers = order_data.get('answers', {})
                for q_text, ans in answers.items():
                    if ans and keyword_lower in str(ans).lower():
                        filtered.append(order)
                        break
            
            self._results = filtered
            self._filters_applied.append(f"کلمه کلیدی: {keyword}")
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_keyword with keyword '{keyword}': {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def search_by_date_range(self, start_date: str = None, end_date: str = None) -> 'AdvancedSearch':
        """فیلتر بر اساس بازه زمانی"""
        try:
            if not start_date and not end_date:
                return self
            
            filtered = []
            for order in self._results:
                created_at = order.get('created_at', '')
                if not created_at:
                    continue
                
                # استخراج تاریخ
                if isinstance(created_at, str):
                    date_str = created_at[:10] if len(created_at) >= 10 else created_at
                else:
                    date_str = created_at.strftime("%Y-%m-%d") if hasattr(created_at, 'strftime') else str(created_at)[:10]
                
                if start_date and date_str < start_date:
                    continue
                if end_date and date_str > end_date:
                    continue
                
                filtered.append(order)
            
            self._results = filtered
            filter_text = f"تاریخ: {start_date or '...'} تا {end_date or '...'}"
            self._filters_applied.append(filter_text)
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_date_range: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def search_by_status(self, statuses: List[str]) -> 'AdvancedSearch':
        """فیلتر بر اساس وضعیت"""
        try:
            if not statuses:
                return self
            
            valid_statuses = ['pending', 'paid', 'completed', 'cancelled', 'failed', 'refunded']
            statuses = [s for s in statuses if s in valid_statuses]
            
            if not statuses:
                return self
            
            self._results = [o for o in self._results if o.get('status') in statuses]
            from .common import get_order_status_persian
            status_labels = [get_order_status_persian(s) for s in statuses]
            self._filters_applied.append(f"وضعیت: {', '.join(status_labels)}")
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_status: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def search_by_service(self, button_ids: List[int]) -> 'AdvancedSearch':
        """فیلتر بر اساس سرویس"""
        try:
            if not button_ids:
                return self
            
            self._results = [o for o in self._results if o.get('button_id') in button_ids]
            service_names = []
            for bid in button_ids:
                name = get_service_name(bid)
                service_names.append(name)
            self._filters_applied.append(f"سرویس: {', '.join(service_names[:3])}{'...' if len(service_names) > 3 else ''}")
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_service: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def search_by_amount_range(self, min_amount: int = None, max_amount: int = None) -> 'AdvancedSearch':
        """فیلتر بر اساس محدوده مبلغ"""
        try:
            if min_amount is None and max_amount is None:
                return self
            
            filtered = []
            for order in self._results:
                amount = order.get('payment_amount', 0) or 0
                if min_amount is not None and amount < min_amount:
                    continue
                if max_amount is not None and amount > max_amount:
                    continue
                filtered.append(order)
            
            self._results = filtered
            if min_amount and max_amount:
                self._filters_applied.append(f"مبلغ: {format_number(min_amount)} تا {format_number(max_amount)} ریال")
            elif min_amount:
                self._filters_applied.append(f"مبلغ: بیشتر از {format_number(min_amount)} ریال")
            elif max_amount:
                self._filters_applied.append(f"مبلغ: کمتر از {format_number(max_amount)} ریال")
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_amount_range: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def search_by_user(self, user_id: int = None, username: str = None) -> 'AdvancedSearch':
        """فیلتر بر اساس کاربر"""
        try:
            if not user_id and not username:
                return self
            
            # اگر نام کاربری داده شده، ابتدا کاربر را پیدا کن
            if username:
                users = search_users(username, limit=1)
                if users:
                    user_id = users[0]['user_id']
                else:
                    self._results = []
                    self._filters_applied.append(f"کاربر: @{username} (یافت نشد)")
                    return self
            
            if user_id:
                self._results = [o for o in self._results if o.get('user_id') == user_id]
                user = get_user(user_id)
                user_display = user.get('first_name') or user.get('username') or str(user_id) if user else str(user_id)
                self._filters_applied.append(f"کاربر: {user_display}")
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_user: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def search_by_tracking_code(self, tracking_code: str) -> 'AdvancedSearch':
        """جستجو بر اساس کد رهگیری"""
        try:
            if not tracking_code or tracking_code.strip() == "":
                return self
            
            code_lower = tracking_code.lower().strip()
            self._results = [o for o in self._results if code_lower in str(o.get('tracking_code', '')).lower()]
            self._filters_applied.append(f"کد رهگیری: {tracking_code}")
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_tracking_code: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def search_by_order_id(self, order_id: int) -> 'AdvancedSearch':
        """جستجو بر اساس شناسه سفارش"""
        try:
            if not order_id:
                return self
            
            self._results = [o for o in self._results if o.get('id') == order_id]
            self._filters_applied.append(f"شناسه سفارش: {order_id}")
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_order_id: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def search_by_has_file(self, has_file: bool = True) -> 'AdvancedSearch':
        """فیلتر سفارشاتی که فایل دارند"""
        try:
            filtered = []
            for order in self._results:
                order_data = order.get('order_data', {})
                if isinstance(order_data, str):
                    try:
                        order_data = json.loads(order_data)
                    except:
                        order_data = {}
                
                files = order_data.get('files', {})
                has_files = bool(files)
                
                if has_file == has_files:
                    filtered.append(order)
            
            self._results = filtered
            self._filters_applied.append(f"دارای فایل: {'بله' if has_file else 'خیر'}")
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_has_file: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def search_by_date_created(self, date: str) -> 'AdvancedSearch':
        """فیلتر سفارشات ثبت‌شده در یک تاریخ خاص"""
        try:
            if not date:
                return self
            
            filtered = []
            for order in self._results:
                created_at = order.get('created_at', '')
                if not created_at:
                    continue
                
                if isinstance(created_at, str):
                    date_str = created_at[:10] if len(created_at) >= 10 else created_at
                else:
                    date_str = created_at.strftime("%Y-%m-%d") if hasattr(created_at, 'strftime') else str(created_at)[:10]
                
                if date_str == date:
                    filtered.append(order)
            
            self._results = filtered
            self._filters_applied.append(f"تاریخ ثبت: {date}")
            
        except Exception as e:
            log_general_error(
                f"Error in search_by_date_created: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self
    
    def get_results(self) -> List[Dict]:
        """دریافت نتایج جستجو"""
        return self._results
    
    def get_count(self) -> int:
        """تعداد نتایج"""
        return len(self._results)
    
    def get_filters_summary(self) -> str:
        """دریافت خلاصه فیلترهای اعمال‌شده"""
        if not self._filters_applied:
            return "بدون فیلتر"
        return " | ".join(self._filters_applied)
    
    def sort_by(self, key: str, reverse: bool = True) -> 'AdvancedSearch':
        """مرتب‌سازی نتایج"""
        try:
            sort_key_map = {
                'id': 'id',
                'amount': 'payment_amount',
                'created_at': 'created_at',
                'user_id': 'user_id',
                'status': 'status',
            }
            
            sort_key = sort_key_map.get(key, 'id')
            
            def get_sort_value(order):
                value = order.get(sort_key, 0)
                if sort_key == 'created_at':
                    if isinstance(value, str):
                        return value
                    return str(value) if value else ''
                if sort_key == 'payment_amount':
                    return value or 0
                return value
            
            self._results.sort(key=get_sort_value, reverse=reverse)
            
        except Exception as e:
            log_general_error(
                f"Error in sort_by: {str(e)}",
                traceback=traceback.format_exc()  # ✅ traceback کامل
            )
        
        return self


# ============================================================
# کیبوردها
# ============================================================

def advanced_search_main_keyboard() -> dict:
    """کیبورد اصلی جستجوی پیشرفته"""
    return {
        "inline_keyboard": [
            [{"text": "🔍 جستجوی سریع (کلمه کلیدی)", "callback_data": "admin_adv_search_quick"}],
            [{"text": "📅 جستجو بر اساس تاریخ", "callback_data": "admin_adv_search_date"}],
            [{"text": "💰 جستجو بر اساس مبلغ", "callback_data": "admin_adv_search_amount"}],
            [{"text": "📌 جستجو بر اساس وضعیت", "callback_data": "admin_adv_search_status"}],
            [{"text": "🔘 جستجو بر اساس سرویس", "callback_data": "admin_adv_search_service"}],
            [{"text": "👤 جستجو بر اساس کاربر", "callback_data": "admin_adv_search_user"}],
            [{"text": "🎫 جستجو بر اساس کد رهگیری", "callback_data": "admin_adv_search_tracking"}],
            [{"text": "📎 جستجوی سفارشات دارای فایل", "callback_data": "admin_adv_search_has_file"}],
            [{"text": "📋 جستجوی ترکیبی (پیشرفته)", "callback_data": "admin_adv_search_combo"}],
            [{"text": "🔄 بازنشانی جستجو", "callback_data": "admin_adv_search_reset"}],
            [{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}],
            [{"text": "🔙 بازگشت", "callback_data": "admin_back"}]
        ]
    }


def search_results_keyboard(results: List[Dict], page: int = 0, per_page: int = 5) -> dict:
    """کیبورد نمایش نتایج جستجو"""
    try:
        total = len(results)
        start = page * per_page
        end = min(start + per_page, total)
        page_results = results[start:end]
        
        keyboard = []
        
        for order in page_results:
            order_id = order.get('id')
            fullname = get_fullname_from_order(order)
            status = order.get('status', 'pending')
            from .common import get_order_status_persian
            status_icon = "✅" if status in ['paid', 'completed'] else "⏳" if status == 'pending' else "❌"
            amount = order.get('payment_amount', 0) or 0
            service = get_service_name(order.get('button_id'))
            
            keyboard.append([
                {"text": f"{status_icon} #{order_id} - {fullname[:12]} - {service[:12]} - {format_number(amount)} ریال",
                 "callback_data": f"admin_adv_search_order_{order_id}"}
            ])
        
        if not results:
            keyboard.append([{"text": "❌ هیچ نتیجه‌ای یافت نشد", "callback_data": "admin_none"}])
        
        # دکمه‌های صفحه‌بندی
        nav_row = []
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_adv_search_page_{page-1}"})
        if page < total_pages - 1:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_adv_search_page_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)
        
        # آمار
        keyboard.append([{"text": f"📊 {total} نتیجه یافت شد", "callback_data": "admin_none"}])
        
        keyboard.append([
            {"text": "📥 خروجی Excel", "callback_data": "admin_adv_search_export"},
            {"text": "🔙 بازگشت به جستجو", "callback_data": "admin_adv_search"}
        ])
        
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in search_results_keyboard: {str(e)}",
            traceback=traceback.format_exc()  # ✅ traceback کامل
        )
        return {"inline_keyboard": [[{"text": "❌ خطا در نمایش نتایج", "callback_data": "admin_adv_search"}]]}


def search_status_keyboard(selected: List[str] = None) -> dict:
    """کیبورد انتخاب وضعیت برای جستجو"""
    try:
        if selected is None:
            selected = []
        
        statuses = [
            ('pending', '⏳ در انتظار پرداخت'),
            ('paid', '✅ پرداخت شده'),
            ('completed', '✅ تکمیل شده'),
            ('cancelled', '❌ لغو شده'),
            ('failed', '❌ ناموفق'),
            ('refunded', '🔄 بازگشت وجه'),
        ]
        
        keyboard = []
        for status, label in statuses:
            check = "☑️" if status in selected else "⬜"
            keyboard.append([{"text": f"{check} {label}", "callback_data": f"admin_adv_search_status_toggle_{status}"}])
        
        keyboard.append([
            {"text": "✅ اعمال", "callback_data": "admin_adv_search_status_apply"},
            {"text": "❌ پاک کردن", "callback_data": "admin_adv_search_status_clear"}
        ])
        keyboard.append([{"text": "🔙 بازگشت", "callback_data": "admin_adv_search"}])
        
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in search_status_keyboard: {str(e)}",
            traceback=traceback.format_exc()  # ✅ traceback کامل
        )
        return {"inline_keyboard": [[{"text": "❌ خطا", "callback_data": "admin_adv_search"}]]}


def search_service_keyboard(selected: List[int] = None, page: int = 0) -> dict:
    """کیبورد انتخاب سرویس برای جستجو"""
    try:
        if selected is None:
            selected = []
        
        from database import get_all_buttons
        buttons = get_all_buttons()
        per_page = 8
        total = len(buttons)
        start = page * per_page
        end = min(start + per_page, total)
        page_buttons = buttons[start:end]
        
        keyboard = []
        for btn in page_buttons:
            check = "☑️" if btn['id'] in selected else "⬜"
            icon = "📂" if btn.get('has_submenu', 0) == 1 else "🔘"
            keyboard.append([{"text": f"{check} {icon} {btn['name']}", "callback_data": f"admin_adv_search_service_toggle_{btn['id']}"}])
        
        # صفحه‌بندی
        nav_row = []
        if page > 0:
            nav_row.append({"text": "⬅️ قبلی", "callback_data": f"admin_adv_search_service_page_{page-1}"})
        if end < total:
            nav_row.append({"text": "➡️ بعدی", "callback_data": f"admin_adv_search_service_page_{page+1}"})
        if nav_row:
            keyboard.append(nav_row)
        
        keyboard.append([
            {"text": "✅ اعمال", "callback_data": "admin_adv_search_service_apply"},
            {"text": "❌ پاک کردن", "callback_data": "admin_adv_search_service_clear"}
        ])
        keyboard.append([{"text": "🔙 بازگشت", "callback_data": "admin_adv_search"}])
        
        return {"inline_keyboard": keyboard}
        
    except Exception as e:
        log_general_error(
            f"Error in search_service_keyboard: {str(e)}",
            traceback=traceback.format_exc()  # ✅ traceback کامل
        )
        return {"inline_keyboard": [[{"text": "❌ خطا", "callback_data": "admin_adv_search"}]]}


# ============================================================
# توابع اصلی جستجوی پیشرفته
# ============================================================

async def handle_advanced_search(chat_id: int, user_id: int) -> bool:
    """نمایش منوی اصلی جستجوی پیشرفته"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        # ایجاد یا بازیابی جستجو
        if user_id not in user_states:
            user_states[user_id] = {}
        
        if "adv_search" not in user_states[user_id]:
            user_states[user_id]["adv_search"] = AdvancedSearch()
        
        search_obj = user_states[user_id]["adv_search"]
        count = search_obj.get_count()
        filters = search_obj.get_filters_summary()
        
        msg = (
            f"🔍 **جستجوی پیشرفته در سفارشات**\n\n"
            f"📊 نتایج فعلی: {count} سفارش\n"
            f"📌 فیلترهای اعمال‌شده: {filters}\n\n"
            f"یکی از گزینه‌های زیر را انتخاب کنید:"
        )
        
        await send_message(chat_id, msg, advanced_search_main_keyboard())
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_advanced_search: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جستجوی پیشرفته.")
        return True


async def handle_search_quick(chat_id: int, user_id: int) -> bool:
    """جستجوی سریع با کلمه کلیدی"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_states[user_id]["adv_search_state"] = "quick_keyword"
        await send_message(
            chat_id,
            "🔍 **جستجوی سریع**\n\n"
            "لطفاً کلمه کلیدی مورد نظر را وارد کنید:\n"
            "(شناسه سفارش، شناسه کاربر، کد رهگیری، نام کاربر، یا هر کلمه در پاسخ‌ها)\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_quick: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجوی سریع.")
        return True


async def handle_search_date(chat_id: int, user_id: int) -> bool:
    """جستجو بر اساس تاریخ"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_states[user_id]["adv_search_state"] = "date_range"
        await send_message(
            chat_id,
            "📅 **جستجو بر اساس تاریخ**\n\n"
            "لطفاً تاریخ شروع و پایان را به فرمت **YYYY-MM-DD** وارد کنید:\n"
            "(مثال: 2024-01-01 تا 2024-01-31)\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_date: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجوی تاریخ.")
        return True


async def handle_search_amount(chat_id: int, user_id: int) -> bool:
    """جستجو بر اساس مبلغ"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_states[user_id]["adv_search_state"] = "amount_range"
        await send_message(
            chat_id,
            "💰 **جستجو بر اساس مبلغ**\n\n"
            "لطفاً محدوده مبلغ را به ریال وارد کنید:\n"
            "(مثال: 100000 تا 1000000)\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_amount: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجوی مبلغ.")
        return True


async def handle_search_status(chat_id: int, user_id: int) -> bool:
    """جستجو بر اساس وضعیت"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = user_states.get(user_id, {}).get("adv_search_statuses", [])
        await send_message(
            chat_id,
            "📌 **جستجو بر اساس وضعیت**\n\n"
            "وضعیت‌های مورد نظر را انتخاب کنید:\n"
            "(روی هر گزینه کلیک کنید تا انتخاب/لغو شود)\n"
            "سپس روی «اعمال» کلیک کنید.",
            search_status_keyboard(selected)
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_status: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجوی وضعیت.")
        return True


async def handle_search_status_toggle(chat_id: int, user_id: int, status: str) -> bool:
    """تغییر انتخاب یک وضعیت"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if user_id not in user_states:
            user_states[user_id] = {}
        
        if "adv_search_statuses" not in user_states[user_id]:
            user_states[user_id]["adv_search_statuses"] = []
        
        selected = user_states[user_id]["adv_search_statuses"]
        
        if status in selected:
            selected.remove(status)
        else:
            selected.append(status)
        
        user_states[user_id]["adv_search_statuses"] = selected
        
        await send_message(
            chat_id,
            f"📌 وضعیت‌های انتخاب‌شده: {len(selected)} مورد",
            search_status_keyboard(selected)
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_status_toggle: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر انتخاب وضعیت.")
        return True


async def handle_search_status_apply(chat_id: int, user_id: int) -> bool:
    """اعمال فیلتر وضعیت"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = user_states.get(user_id, {}).get("adv_search_statuses", [])
        
        if not selected:
            await send_message(chat_id, "⚠️ هیچ وضعیتی انتخاب نشده است.")
            return True
        
        if user_id not in user_states:
            user_states[user_id] = {}
        
        if "adv_search" not in user_states[user_id]:
            user_states[user_id]["adv_search"] = AdvancedSearch()
        
        search_obj = user_states[user_id]["adv_search"]
        search_obj.search_by_status(selected)
        user_states[user_id]["adv_search_statuses"] = []
        
        await send_message(
            chat_id,
            f"✅ فیلتر وضعیت اعمال شد.\n\n"
            f"📊 تعداد نتایج: {search_obj.get_count()}",
            {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_status_apply: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در اعمال فیلتر وضعیت.")
        return True


async def handle_search_status_clear(chat_id: int, user_id: int) -> bool:
    """پاک کردن فیلتر وضعیت"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if user_id in user_states:
            user_states[user_id].pop("adv_search_statuses", None)
        
        await send_message(
            chat_id,
            "✅ فیلتر وضعیت پاک شد.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به جستجو", "callback_data": "admin_adv_search"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_status_clear: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در پاک کردن فیلتر وضعیت.")
        return True


async def handle_search_service(chat_id: int, user_id: int, page: int = 0) -> bool:
    """جستجو بر اساس سرویس"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = user_states.get(user_id, {}).get("adv_search_services", [])
        await send_message(
            chat_id,
            f"🔘 **جستجو بر اساس سرویس - صفحه {page + 1}**\n\n"
            "سرویس‌های مورد نظر را انتخاب کنید:\n"
            "(روی هر گزینه کلیک کنید تا انتخاب/لغو شود)",
            search_service_keyboard(selected, page)
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_service: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجوی سرویس.")
        return True


async def handle_search_service_toggle(chat_id: int, user_id: int, service_id: int) -> bool:
    """تغییر انتخاب یک سرویس"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if user_id not in user_states:
            user_states[user_id] = {}
        
        if "adv_search_services" not in user_states[user_id]:
            user_states[user_id]["adv_search_services"] = []
        
        selected = user_states[user_id]["adv_search_services"]
        
        if service_id in selected:
            selected.remove(service_id)
        else:
            selected.append(service_id)
        
        user_states[user_id]["adv_search_services"] = selected
        
        await send_message(
            chat_id,
            f"🔘 سرویس‌های انتخاب‌شده: {len(selected)} مورد",
            search_service_keyboard(selected)
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_service_toggle: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در تغییر انتخاب سرویس.")
        return True


async def handle_search_service_page(chat_id: int, user_id: int, page: int) -> bool:
    """صفحه‌بندی سرویس‌ها"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = user_states.get(user_id, {}).get("adv_search_services", [])
        await send_message(
            chat_id,
            f"🔘 **سرویس‌ها - صفحه {page + 1}**",
            search_service_keyboard(selected, page)
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_service_page: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی سرویس‌ها.")
        return True


async def handle_search_service_apply(chat_id: int, user_id: int) -> bool:
    """اعمال فیلتر سرویس"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        selected = user_states.get(user_id, {}).get("adv_search_services", [])
        
        if not selected:
            await send_message(chat_id, "⚠️ هیچ سرویسی انتخاب نشده است.")
            return True
        
        if user_id not in user_states:
            user_states[user_id] = {}
        
        if "adv_search" not in user_states[user_id]:
            user_states[user_id]["adv_search"] = AdvancedSearch()
        
        search_obj = user_states[user_id]["adv_search"]
        search_obj.search_by_service(selected)
        user_states[user_id]["adv_search_services"] = []
        
        await send_message(
            chat_id,
            f"✅ فیلتر سرویس اعمال شد.\n\n"
            f"📊 تعداد نتایج: {search_obj.get_count()}",
            {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_service_apply: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در اعمال فیلتر سرویس.")
        return True


async def handle_search_service_clear(chat_id: int, user_id: int) -> bool:
    """پاک کردن فیلتر سرویس"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if user_id in user_states:
            user_states[user_id].pop("adv_search_services", None)
        
        await send_message(
            chat_id,
            "✅ فیلتر سرویس پاک شد.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به جستجو", "callback_data": "admin_adv_search"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_service_clear: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در پاک کردن فیلتر سرویس.")
        return True


async def handle_search_user(chat_id: int, user_id: int) -> bool:
    """جستجو بر اساس کاربر"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_states[user_id]["adv_search_state"] = "user_search"
        await send_message(
            chat_id,
            "👤 **جستجو بر اساس کاربر**\n\n"
            "لطفاً شناسه کاربری (user_id) یا نام کاربری را وارد کنید:\n"
            "(مثال: 123456789 یا @username)\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_user: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجوی کاربر.")
        return True


async def handle_search_tracking(chat_id: int, user_id: int) -> bool:
    """جستجو بر اساس کد رهگیری"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        user_states[user_id]["adv_search_state"] = "tracking_code"
        await send_message(
            chat_id,
            "🎫 **جستجو بر اساس کد رهگیری**\n\n"
            "لطفاً کد رهگیری را وارد کنید:\n\n"
            "برای انصراف، /cancel را ارسال کنید."
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_tracking: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجوی کد رهگیری.")
        return True


async def handle_search_has_file(chat_id: int, user_id: int) -> bool:
    """جستجوی سفارشات دارای فایل"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if user_id not in user_states:
            user_states[user_id] = {}
        
        if "adv_search" not in user_states[user_id]:
            user_states[user_id]["adv_search"] = AdvancedSearch()
        
        search_obj = user_states[user_id]["adv_search"]
        search_obj.search_by_has_file(True)
        
        await send_message(
            chat_id,
            f"✅ جستجوی سفارشات دارای فایل اعمال شد.\n\n"
            f"📊 تعداد نتایج: {search_obj.get_count()}",
            {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_has_file: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در جستجوی فایل.")
        return True


async def handle_search_reset(chat_id: int, user_id: int) -> bool:
    """بازنشانی جستجو"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if user_id in user_states:
            user_states[user_id]["adv_search"] = AdvancedSearch()
            user_states[user_id].pop("adv_search_state", None)
            user_states[user_id].pop("adv_search_statuses", None)
            user_states[user_id].pop("adv_search_services", None)
        
        await send_message(
            chat_id,
            "🔄 جستجو بازنشانی شد.\n\n"
            "همه نتایج به حالت اولیه بازگشتند.",
            {"inline_keyboard": [[{"text": "🔙 بازگشت به جستجو", "callback_data": "admin_adv_search"}]]}
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_reset: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در بازنشانی جستجو.")
        return True


# ============================================================
# نمایش نتایج
# ============================================================

async def handle_search_results(chat_id: int, user_id: int, page: int = 0) -> bool:
    """نمایش نتایج جستجو"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if user_id not in user_states:
            user_states[user_id] = {}
        
        if "adv_search" not in user_states[user_id]:
            user_states[user_id]["adv_search"] = AdvancedSearch()
        
        search_obj = user_states[user_id]["adv_search"]
        results = search_obj.get_results()
        filters = search_obj.get_filters_summary()
        
        if not results:
            await send_message(
                chat_id,
                f"🔍 **نتایج جستجو**\n\n"
                f"❌ هیچ نتیجه‌ای یافت نشد.\n"
                f"📌 فیلترها: {filters}\n\n"
                f"برای تغییر جستجو، به منوی اصلی بازگردید.",
                {"inline_keyboard": [[{"text": "🔙 بازگشت به جستجو", "callback_data": "admin_adv_search"}]]}
            )
            return True
        
        keyboard = search_results_keyboard(results, page)
        
        await send_message(
            chat_id,
            f"🔍 **نتایج جستجو**\n\n"
            f"📊 {len(results)} نتیجه یافت شد\n"
            f"📌 فیلترها: {filters}\n\n"
            f"برای مشاهده جزئیات هر سفارش کلیک کنید:",
            keyboard
        )
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_results: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش نتایج.")
        return True


async def handle_search_page(chat_id: int, user_id: int, page: int) -> bool:
    """صفحه‌بندی نتایج جستجو"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        return await handle_search_results(chat_id, user_id, page)
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_page: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در صفحه‌بندی.")
        return True


async def handle_search_order_detail(chat_id: int, user_id: int, order_id: int) -> bool:
    """نمایش جزئیات یک سفارش از نتایج جستجو"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        order = get_dynamic_order_by_id(order_id)
        if not order:
            await send_message(chat_id, "❌ سفارش یافت نشد.")
            return True
        
        from .orders import show_order_detail
        await show_order_detail(chat_id, user_id, order, "admin_adv_search_results")
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_order_detail for order {order_id}: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در نمایش جزئیات سفارش.")
        return True


async def handle_search_export(chat_id: int, user_id: int) -> bool:
    """خروجی Excel از نتایج جستجو"""
    try:
        if user_id != OWNER_ID:
            await send_message(chat_id, "⛔ فقط مالک ربات دسترسی به این بخش دارد.")
            return True
        
        if user_id not in user_states:
            user_states[user_id] = {}
        
        if "adv_search" not in user_states[user_id]:
            user_states[user_id]["adv_search"] = AdvancedSearch()
        
        search_obj = user_states[user_id]["adv_search"]
        results = search_obj.get_results()
        
        if not results:
            await send_message(chat_id, "❌ هیچ نتیجه‌ای برای خروجی وجود ندارد.")
            return True
        
        await send_message(chat_id, f"⏳ در حال تولید فایل Excel برای {len(results)} سفارش...")
        
        from .excel_export import create_orders_excel
        filepath = create_orders_excel(
            results, 
            f"نتایج جستجوی پیشرفته - {len(results)} سفارش",
            include_stats=True,
            include_chart=True
        )
        
        if filepath:
            from core import send_document
            import os
            await send_document(
                chat_id,
                file_path=filepath,
                caption=f"📊 **خروجی جستجوی پیشرفته**\n\n📦 {len(results)} سفارش\n📌 فیلترها: {search_obj.get_filters_summary()}"
            )
            try:
                os.remove(filepath)
            except:
                pass
        else:
            await send_message(chat_id, "❌ خطا در تولید فایل Excel.")
        
        return True
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_search_export: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, f"❌ خطا در خروجی Excel: {str(e)}")
        return True


# ============================================================
# پردازش پیام‌های جستجو
# ============================================================

async def handle_adv_search_message(chat_id: int, user_id: int, text: str) -> bool:
    """پردازش پیام‌های مربوط به جستجوی پیشرفته"""
    try:
        state_info = user_states.get(user_id, {})
        search_state = state_info.get("adv_search_state")
        
        if not search_state:
            return False
        
        if user_id not in user_states:
            user_states[user_id] = {}
        
        if "adv_search" not in user_states[user_id]:
            user_states[user_id]["adv_search"] = AdvancedSearch()
        
        search_obj = user_states[user_id]["adv_search"]
        
        # ========== جستجوی سریع (کلمه کلیدی) ==========
        if search_state == "quick_keyword":
            if not text or text.strip() == "":
                await send_message(chat_id, "❌ لطفاً یک کلمه کلیدی معتبر وارد کنید.")
                return True
            
            search_obj.search_by_keyword(text.strip())
            user_states[user_id].pop("adv_search_state", None)
            
            await send_message(
                chat_id,
                f"✅ جستجوی کلمه کلیدی «{text}» اعمال شد.\n\n"
                f"📊 تعداد نتایج: {search_obj.get_count()}",
                {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
            )
            return True
        
        # ========== جستجو بر اساس تاریخ ==========
        if search_state == "date_range":
            try:
                parts = text.split("تا")
                if len(parts) == 2:
                    start = parts[0].strip()
                    end = parts[1].strip()
                else:
                    # اگر فقط یک تاریخ وارد شده
                    start = text.strip()
                    end = None
                
                # اعتبارسنجی تاریخ
                from datetime import datetime
                if start:
                    datetime.strptime(start, "%Y-%m-%d")
                if end:
                    datetime.strptime(end, "%Y-%m-%d")
                
                search_obj.search_by_date_range(start, end)
                user_states[user_id].pop("adv_search_state", None)
                
                await send_message(
                    chat_id,
                    f"✅ فیلتر تاریخ اعمال شد.\n\n"
                    f"📅 از {start or 'نامشخص'} تا {end or 'نامشخص'}\n"
                    f"📊 تعداد نتایج: {search_obj.get_count()}",
                    {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
                )
                return True
                
            except ValueError:
                await send_message(chat_id, "❌ فرمت تاریخ نامعتبر. لطفاً به فرمت YYYY-MM-DD وارد کنید.")
                return True
        
        # ========== جستجو بر اساس مبلغ ==========
        if search_state == "amount_range":
            try:
                parts = text.replace("تا", " ").replace(" ", "").split()
                if len(parts) == 2:
                    min_amount = int(parts[0])
                    max_amount = int(parts[1])
                elif len(parts) == 1:
                    min_amount = int(parts[0])
                    max_amount = None
                else:
                    await send_message(chat_id, "❌ فرمت نامعتبر. مثال: 100000 تا 1000000")
                    return True
                
                if min_amount and min_amount < 0:
                    await send_message(chat_id, "❌ مبلغ نمی‌تواند منفی باشد.")
                    return True
                if max_amount and max_amount < 0:
                    await send_message(chat_id, "❌ مبلغ نمی‌تواند منفی باشد.")
                    return True
                if min_amount and max_amount and min_amount > max_amount:
                    await send_message(chat_id, "❌ حداقل نباید از حداکثر بیشتر باشد.")
                    return True
                
                search_obj.search_by_amount_range(min_amount, max_amount)
                user_states[user_id].pop("adv_search_state", None)
                
                await send_message(
                    chat_id,
                    f"✅ فیلتر مبلغ اعمال شد.\n\n"
                    f"💰 محدوده: {min_amount or 'نامحدود'} تا {max_amount or 'نامحدود'} ریال\n"
                    f"📊 تعداد نتایج: {search_obj.get_count()}",
                    {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
                )
                return True
                
            except ValueError:
                await send_message(chat_id, "❌ لطفاً اعداد معتبر وارد کنید.")
                return True
        
        # ========== جستجو بر اساس کاربر ==========
        if search_state == "user_search":
            if not text or text.strip() == "":
                await send_message(chat_id, "❌ لطفاً شناسه یا نام کاربری معتبر وارد کنید.")
                return True
            
            user_id_search = None
            username = None
            
            if text.strip().isdigit():
                user_id_search = int(text.strip())
            else:
                username = text.strip().lstrip('@')
            
            search_obj.search_by_user(user_id_search, username)
            user_states[user_id].pop("adv_search_state", None)
            
            await send_message(
                chat_id,
                f"✅ فیلتر کاربر اعمال شد.\n\n"
                f"👤 کاربر: {text}\n"
                f"📊 تعداد نتایج: {search_obj.get_count()}",
                {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
            )
            return True
        
        # ========== جستجو بر اساس کد رهگیری ==========
        if search_state == "tracking_code":
            if not text or text.strip() == "":
                await send_message(chat_id, "❌ لطفاً کد رهگیری را وارد کنید.")
                return True
            
            search_obj.search_by_tracking_code(text.strip())
            user_states[user_id].pop("adv_search_state", None)
            
            await send_message(
                chat_id,
                f"✅ فیلتر کد رهگیری اعمال شد.\n\n"
                f"🎫 کد رهگیری: {text}\n"
                f"📊 تعداد نتایج: {search_obj.get_count()}",
                {"inline_keyboard": [[{"text": "📊 نمایش نتایج", "callback_data": "admin_adv_search_results"}]]}
            )
            return True
        
        return False
        
    except Exception as e:
        log_callback_error(
            f"Error in handle_adv_search_message: {str(e)}",
            traceback=traceback.format_exc(),  # ✅ traceback کامل
            user_id=user_id,
            chat_id=chat_id
        )
        await send_message(chat_id, "❌ خطا در پردازش پیام جستجو.")
        return True


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'AdvancedSearch',
    'handle_advanced_search',
    'handle_search_quick',
    'handle_search_date',
    'handle_search_amount',
    'handle_search_status',
    'handle_search_status_toggle',
    'handle_search_status_apply',
    'handle_search_status_clear',
    'handle_search_service',
    'handle_search_service_toggle',
    'handle_search_service_page',
    'handle_search_service_apply',
    'handle_search_service_clear',
    'handle_search_user',
    'handle_search_tracking',
    'handle_search_has_file',
    'handle_search_reset',
    'handle_search_results',
    'handle_search_page',
    'handle_search_order_detail',
    'handle_search_export',
    'handle_adv_search_message',
    'search_results_keyboard',
    'search_status_keyboard',
    'search_service_keyboard',
]