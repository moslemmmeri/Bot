# admin_panel/filters.py
# مدیریت فیلترهای پیشرفته برای آمار و گزارش‌ها
# شامل: فیلترهای بازه زمانی، نوع سرویس، وضعیت، محدوده مبلغ، کاربر و ...

import json
import traceback  # ✅ اضافه شد برای traceback کامل
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from logger_config import logger
from database import get_dynamic_orders, get_button_by_id, get_user
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


# ============================================================
# دیتاکلاس فیلترها
# ============================================================

@dataclass
class DateFilter:
    """فیلتر بازه زمانی"""
    start_date: Optional[str] = None  # فرمت YYYY-MM-DD
    end_date: Optional[str] = None    # فرمت YYYY-MM-DD
    period: Optional[str] = None      # today, yesterday, last_7_days, last_30_days, last_90_days, custom

    def apply(self, orders: List[Dict]) -> List[Dict]:
        """اعمال فیلتر تاریخ روی سفارشات"""
        if not orders:
            return orders
        
        # اگر بازه مشخص نشده، همه را برگردان
        if not self.start_date and not self.end_date and not self.period:
            return orders
        
        # تعیین تاریخ‌ها بر اساس period
        if self.period:
            start, end = self._get_date_range_from_period(self.period)
            if start:
                self.start_date = start
            if end:
                self.end_date = end
        
        filtered = []
        for order in orders:
            created_at = order.get('created_at')
            if not created_at:
                continue
            
            # استخراج تاریخ از created_at
            if isinstance(created_at, str):
                date_str = created_at[:10] if len(created_at) >= 10 else created_at
            else:
                date_str = created_at.strftime("%Y-%m-%d") if hasattr(created_at, 'strftime') else str(created_at)[:10]
            
            # بررسی بازه
            if self.start_date and date_str < self.start_date:
                continue
            if self.end_date and date_str > self.end_date:
                continue
            
            filtered.append(order)
        
        return filtered

    def _get_date_range_from_period(self, period: str) -> Tuple[Optional[str], Optional[str]]:
        """دریافت بازه تاریخ بر اساس دوره"""
        today = datetime.now().date()
        
        if period == 'today':
            return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        
        elif period == 'yesterday':
            yesterday = today - timedelta(days=1)
            return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
        
        elif period == 'last_7_days':
            start = today - timedelta(days=7)
            return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        
        elif period == 'last_30_days':
            start = today - timedelta(days=30)
            return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        
        elif period == 'last_90_days':
            start = today - timedelta(days=90)
            return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        
        elif period == 'this_month':
            start = today.replace(day=1)
            return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        
        elif period == 'last_month':
            first_day = today.replace(day=1) - timedelta(days=1)
            last_day = first_day
            first_day = first_day.replace(day=1)
            return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")
        
        return None, None

    def get_label(self) -> str:
        """دریافت برچسب قابل نمایش برای فیلتر تاریخ"""
        period_labels = {
            'today': 'امروز',
            'yesterday': 'دیروز',
            'last_7_days': '۷ روز اخیر',
            'last_30_days': '۳۰ روز اخیر',
            'last_90_days': '۹۰ روز اخیر',
            'this_month': 'این ماه',
            'last_month': 'ماه گذشته',
            'custom': 'سفارشی',
        }
        
        if self.period and self.period in period_labels:
            return period_labels[self.period]
        
        if self.start_date and self.end_date:
            return f"{self.start_date} تا {self.end_date}"
        elif self.start_date:
            return f"از {self.start_date} به بعد"
        elif self.end_date:
            return f"تا {self.end_date}"
        
        return 'همه'


@dataclass
class StatusFilter:
    """فیلتر وضعیت سفارش"""
    statuses: List[str] = field(default_factory=list)  # pending, paid, completed

    def apply(self, orders: List[Dict]) -> List[Dict]:
        """اعمال فیلتر وضعیت روی سفارشات"""
        if not self.statuses:
            return orders
        
        return [o for o in orders if o.get('status') in self.statuses]

    def get_label(self) -> str:
        """دریافت برچسب قابل نمایش برای فیلتر وضعیت"""
        if not self.statuses:
            return 'همه'
        
        status_labels = {
            'pending': 'در انتظار پرداخت',
            'paid': 'پرداخت شده',
            'completed': 'تکمیل شده',
            'cancelled': 'لغو شده',
        }
        
        labels = [status_labels.get(s, s) for s in self.statuses]
        return '، '.join(labels)


@dataclass
class ServiceFilter:
    """فیلتر سرویس (دکمه)"""
    button_ids: List[int] = field(default_factory=list)

    def apply(self, orders: List[Dict]) -> List[Dict]:
        """اعمال فیلتر سرویس روی سفارشات"""
        if not self.button_ids:
            return orders
        
        return [o for o in orders if o.get('button_id') in self.button_ids]

    def get_label(self) -> str:
        """دریافت برچسب قابل نمایش برای فیلتر سرویس"""
        if not self.button_ids:
            return 'همه سرویس‌ها'
        
        names = []
        for btn_id in self.button_ids[:3]:
            btn = get_button_by_id(btn_id)
            if btn:
                names.append(btn['name'])
            else:
                names.append(f"سرویس {btn_id}")
        
        if len(self.button_ids) > 3:
            names.append(f"... و {len(self.button_ids) - 3} سرویس دیگر")
        
        return '، '.join(names)


@dataclass
class AmountFilter:
    """فیلتر محدوده مبلغ"""
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None

    def apply(self, orders: List[Dict]) -> List[Dict]:
        """اعمال فیلتر مبلغ روی سفارشات"""
        if self.min_amount is None and self.max_amount is None:
            return orders
        
        filtered = []
        for order in orders:
            amount = order.get('payment_amount', 0) or 0
            if self.min_amount is not None and amount < self.min_amount:
                continue
            if self.max_amount is not None and amount > self.max_amount:
                continue
            filtered.append(order)
        
        return filtered

    def get_label(self) -> str:
        """دریافت برچسب قابل نمایش برای فیلتر مبلغ"""
        if self.min_amount is None and self.max_amount is None:
            return 'همه مبالغ'
        
        if self.min_amount is not None and self.max_amount is not None:
            return f"{self.min_amount:,} تا {self.max_amount:,} ریال"
        elif self.min_amount is not None:
            return f"بیش از {self.min_amount:,} ریال"
        elif self.max_amount is not None:
            return f"کمتر از {self.max_amount:,} ریال"
        
        return 'همه مبالغ'


@dataclass
class UserFilter:
    """فیلتر کاربر"""
    user_id: Optional[int] = None
    username: Optional[str] = None

    def apply(self, orders: List[Dict]) -> List[Dict]:
        """اعمال فیلتر کاربر روی سفارشات"""
        if self.user_id is None and not self.username:
            return orders
        
        if self.user_id:
            return [o for o in orders if o.get('user_id') == self.user_id]
        
        if self.username:
            from database import search_users
            users = search_users(self.username, limit=1)
            if users:
                target_user_id = users[0]['user_id']
                return [o for o in orders if o.get('user_id') == target_user_id]
            return []
        
        return orders

    def get_label(self) -> str:
        """دریافت برچسب قابل نمایش برای فیلتر کاربر"""
        if self.user_id:
            user = get_user(self.user_id)
            if user:
                name = user.get('first_name') or user.get('username') or str(self.user_id)
                return f"کاربر {name}"
            return f"کاربر {self.user_id}"
        
        if self.username:
            return f"کاربر @{self.username}"
        
        return 'همه کاربران'


@dataclass
class AdvancedFilters:
    """مجموعه کامل فیلترهای پیشرفته"""
    date: DateFilter = field(default_factory=DateFilter)
    status: StatusFilter = field(default_factory=StatusFilter)
    service: ServiceFilter = field(default_factory=ServiceFilter)
    amount: AmountFilter = field(default_factory=AmountFilter)
    user: UserFilter = field(default_factory=UserFilter)
    
    # فیلدهای اضافی برای ذخیره وضعیت
    name: str = ""
    saved: bool = False
    
    def apply_all(self, orders: List[Dict]) -> List[Dict]:
        """اعمال همه فیلترها روی سفارشات"""
        result = orders
        
        # اعمال به ترتیب
        result = self.date.apply(result)
        result = self.status.apply(result)
        result = self.service.apply(result)
        result = self.amount.apply(result)
        result = self.user.apply(result)
        
        return result
    
    def get_summary(self) -> str:
        """دریافت خلاصه فیلترها به صورت متن"""
        parts = []
        
        date_label = self.date.get_label()
        if date_label != 'همه':
            parts.append(f"📅 {date_label}")
        
        status_label = self.status.get_label()
        if status_label != 'همه':
            parts.append(f"📌 {status_label}")
        
        service_label = self.service.get_label()
        if service_label != 'همه سرویس‌ها':
            parts.append(f"🔘 {service_label}")
        
        amount_label = self.amount.get_label()
        if amount_label != 'همه مبالغ':
            parts.append(f"💰 {amount_label}")
        
        user_label = self.user.get_label()
        if user_label != 'همه کاربران':
            parts.append(f"👤 {user_label}")
        
        if not parts:
            return "بدون فیلتر"
        
        return " | ".join(parts)
    
    def is_empty(self) -> bool:
        """بررسی خالی بودن فیلترها"""
        return (
            self.date.period is None and self.date.start_date is None and self.date.end_date is None and
            not self.status.statuses and
            not self.service.button_ids and
            self.amount.min_amount is None and self.amount.max_amount is None and
            self.user.user_id is None and self.user.username is None
        )
    
    def to_dict(self) -> Dict:
        """تبدیل به دیکشنری برای ذخیره"""
        return {
            'name': self.name,
            'saved': self.saved,
            'date': {
                'start_date': self.date.start_date,
                'end_date': self.date.end_date,
                'period': self.date.period,
            },
            'status': {
                'statuses': self.status.statuses,
            },
            'service': {
                'button_ids': self.service.button_ids,
            },
            'amount': {
                'min_amount': self.amount.min_amount,
                'max_amount': self.amount.max_amount,
            },
            'user': {
                'user_id': self.user.user_id,
                'username': self.user.username,
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AdvancedFilters':
        """ساخت از روی دیکشنری"""
        filters = cls()
        
        if 'name' in data:
            filters.name = data['name']
        if 'saved' in data:
            filters.saved = data['saved']
        
        if 'date' in data:
            d = data['date']
            filters.date.start_date = d.get('start_date')
            filters.date.end_date = d.get('end_date')
            filters.date.period = d.get('period')
        
        if 'status' in data:
            filters.status.statuses = data['status'].get('statuses', [])
        
        if 'service' in data:
            filters.service.button_ids = data['service'].get('button_ids', [])
        
        if 'amount' in data:
            filters.amount.min_amount = data['amount'].get('min_amount')
            filters.amount.max_amount = data['amount'].get('max_amount')
        
        if 'user' in data:
            filters.user.user_id = data['user'].get('user_id')
            filters.user.username = data['user'].get('username')
        
        return filters


# ============================================================
# مدیریت فیلترها
# ============================================================

class FilterManager:
    """مدیریت فیلترهای ذخیره‌شده کاربران"""
    
    def __init__(self):
        self._filters = {}  # {user_id: {filter_name: AdvancedFilters}}
    
    def save_filter(self, user_id: int, filter_obj: AdvancedFilters, name: str = None) -> bool:
        """ذخیره فیلتر برای کاربر"""
        try:
            if user_id not in self._filters:
                self._filters[user_id] = {}
            
            if name:
                filter_obj.name = name
            else:
                filter_obj.name = f"فیلتر {len(self._filters[user_id]) + 1}"
            
            filter_obj.saved = True
            self._filters[user_id][filter_obj.name] = filter_obj
            
            logger.debug(f"Filter saved for user {user_id}: {filter_obj.name}")
            return True
            
        except Exception as e:
            log_general_error(  # ✅ استفاده از log_general_error با traceback کامل
                f"Error saving filter for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def get_filters(self, user_id: int) -> Dict[str, AdvancedFilters]:
        """دریافت تمام فیلترهای ذخیره‌شده کاربر"""
        return self._filters.get(user_id, {})
    
    def get_filter(self, user_id: int, name: str) -> Optional[AdvancedFilters]:
        """دریافت یک فیلتر خاص از کاربر"""
        user_filters = self._filters.get(user_id, {})
        return user_filters.get(name)
    
    def delete_filter(self, user_id: int, name: str) -> bool:
        """حذف یک فیلتر از کاربر"""
        try:
            if user_id in self._filters and name in self._filters[user_id]:
                del self._filters[user_id][name]
                logger.debug(f"Filter deleted for user {user_id}: {name}")
                return True
            return False
        except Exception as e:
            log_general_error(  # ✅ استفاده از log_general_error با traceback کامل
                f"Error deleting filter for user {user_id}, name {name}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def clear_filters(self, user_id: int) -> bool:
        """پاک کردن تمام فیلترهای کاربر"""
        try:
            if user_id in self._filters:
                self._filters[user_id] = {}
                logger.debug(f"All filters cleared for user {user_id}")
                return True
            return False
        except Exception as e:
            log_general_error(  # ✅ استفاده از log_general_error با traceback کامل
                f"Error clearing filters for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def apply_filter(self, user_id: int, filter_name: str, orders: List[Dict]) -> List[Dict]:
        """اعمال یک فیلتر ذخیره‌شده روی سفارشات"""
        try:
            filter_obj = self.get_filter(user_id, filter_name)
            if filter_obj:
                return filter_obj.apply_all(orders)
            return orders
        except Exception as e:
            log_general_error(  # ✅ اضافه شد برای خطاهای احتمالی
                f"Error applying filter {filter_name} for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return orders


# ============================================================
# آبجکت سراسری
# ============================================================

_filter_manager = None


def get_filter_manager() -> FilterManager:
    """دریافت آبجکت سراسری FilterManager"""
    global _filter_manager
    if _filter_manager is None:
        _filter_manager = FilterManager()
    return _filter_manager


# ============================================================
# توابع کمکی
# ============================================================

def create_filter_from_params(params: Dict) -> AdvancedFilters:
    """ساخت فیلتر از پارامترهای دریافتی"""
    try:
        filters = AdvancedFilters()
        
        # فیلتر تاریخ
        if 'period' in params:
            filters.date.period = params['period']
        if 'start_date' in params:
            filters.date.start_date = params['start_date']
        if 'end_date' in params:
            filters.date.end_date = params['end_date']
        
        # فیلتر وضعیت
        if 'statuses' in params:
            if isinstance(params['statuses'], list):
                filters.status.statuses = params['statuses']
            elif isinstance(params['statuses'], str):
                filters.status.statuses = [s.strip() for s in params['statuses'].split(',') if s.strip()]
        
        # فیلتر سرویس
        if 'button_ids' in params:
            if isinstance(params['button_ids'], list):
                filters.service.button_ids = params['button_ids']
            elif isinstance(params['button_ids'], str):
                filters.service.button_ids = [int(b.strip()) for b in params['button_ids'].split(',') if b.strip().isdigit()]
        
        # فیلتر مبلغ
        if 'min_amount' in params:
            filters.amount.min_amount = int(params['min_amount'])
        if 'max_amount' in params:
            filters.amount.max_amount = int(params['max_amount'])
        
        # فیلتر کاربر
        if 'user_id' in params:
            filters.user.user_id = int(params['user_id'])
        if 'username' in params:
            filters.user.username = params['username']
        
        return filters
    except Exception as e:
        log_general_error(  # ✅ اضافه شد برای خطاهای احتمالی در ساخت فیلتر
            f"Error creating filter from params: {str(e)}",
            traceback=traceback.format_exc()
        )
        return AdvancedFilters()


def get_filter_presets() -> Dict[str, AdvancedFilters]:
    """
    دریافت فیلترهای از پیش تعیین‌شده
    برای استفاده سریع در پنل مدیریت
    """
    try:
        presets = {}
        
        # امروز
        today_filter = AdvancedFilters()
        today_filter.date.period = 'today'
        today_filter.name = 'امروز'
        presets['today'] = today_filter
        
        # دیروز
        yesterday_filter = AdvancedFilters()
        yesterday_filter.date.period = 'yesterday'
        yesterday_filter.name = 'دیروز'
        presets['yesterday'] = yesterday_filter
        
        # ۷ روز اخیر
        last_7_filter = AdvancedFilters()
        last_7_filter.date.period = 'last_7_days'
        last_7_filter.name = '۷ روز اخیر'
        presets['last_7_days'] = last_7_filter
        
        # ۳۰ روز اخیر
        last_30_filter = AdvancedFilters()
        last_30_filter.date.period = 'last_30_days'
        last_30_filter.name = '۳۰ روز اخیر'
        presets['last_30_days'] = last_30_filter
        
        # سفارشات پرداخت‌شده
        paid_filter = AdvancedFilters()
        paid_filter.status.statuses = ['paid', 'completed']
        paid_filter.name = 'پرداخت‌شده'
        presets['paid'] = paid_filter
        
        # سفارشات در انتظار
        pending_filter = AdvancedFilters()
        pending_filter.status.statuses = ['pending']
        pending_filter.name = 'در انتظار پرداخت'
        presets['pending'] = pending_filter
        
        # مبلغ بالا (بیش از ۵۰۰,۰۰۰ ریال)
        high_amount_filter = AdvancedFilters()
        high_amount_filter.amount.min_amount = 500000
        high_amount_filter.name = 'مبلغ بالا (>۵۰۰,۰۰۰)'
        presets['high_amount'] = high_amount_filter
        
        return presets
    except Exception as e:
        log_general_error(  # ✅ اضافه شد برای خطاهای احتمالی
            f"Error getting filter presets: {str(e)}",
            traceback=traceback.format_exc()
        )
        return {}


# ============================================================
# توابع راحت برای استفاده در مسیرها
# ============================================================

async def apply_filters_to_orders(
    orders: List[Dict],
    date_period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    statuses: Optional[List[str]] = None,
    button_ids: Optional[List[int]] = None,
    min_amount: Optional[int] = None,
    max_amount: Optional[int] = None,
    user_id: Optional[int] = None
) -> List[Dict]:
    """
    اعمال فیلترها روی سفارشات با پارامترهای ساده
    """
    try:
        filters = AdvancedFilters()
        
        if date_period:
            filters.date.period = date_period
        if start_date:
            filters.date.start_date = start_date
        if end_date:
            filters.date.end_date = end_date
        if statuses:
            filters.status.statuses = statuses
        if button_ids:
            filters.service.button_ids = button_ids
        if min_amount is not None:
            filters.amount.min_amount = min_amount
        if max_amount is not None:
            filters.amount.max_amount = max_amount
        if user_id:
            filters.user.user_id = user_id
        
        return filters.apply_all(orders)
    except Exception as e:
        log_general_error(  # ✅ اضافه شد برای خطاهای احتمالی
            f"Error applying filters to orders: {str(e)}",
            traceback=traceback.format_exc()
        )
        return orders


def get_filter_summary(filters: AdvancedFilters) -> str:
    """دریافت خلاصه فیلترها به صورت متن"""
    try:
        return filters.get_summary()
    except Exception as e:
        log_general_error(
            f"Error getting filter summary: {str(e)}",
            traceback=traceback.format_exc()
        )
        return "خطا در دریافت خلاصه فیلتر"


def is_filter_empty(filters: AdvancedFilters) -> bool:
    """بررسی خالی بودن فیلترها"""
    try:
        return filters.is_empty()
    except Exception as e:
        log_general_error(
            f"Error checking if filter is empty: {str(e)}",
            traceback=traceback.format_exc()
        )
        return True


__all__ = [
    # دیتاکلاس‌ها
    'DateFilter',
    'StatusFilter',
    'ServiceFilter',
    'AmountFilter',
    'UserFilter',
    'AdvancedFilters',
    # مدیریت
    'FilterManager',
    'get_filter_manager',
    # توابع کمکی
    'create_filter_from_params',
    'get_filter_presets',
    'apply_filters_to_orders',
    'get_filter_summary',
    'is_filter_empty',
]