# models/order.py
# مدل سفارش

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import IntEnum


class OrderStatus(IntEnum):
    """وضعیت‌های سفارش"""
    PENDING = 0       # در انتظار پرداخت
    PAID = 1          # پرداخت شده
    COMPLETED = 2     # تکمیل شده
    CANCELLED = 3     # لغو شده
    FAILED = 4        # ناموفق
    REFUNDED = 5      # بازگشت وجه


@dataclass
class Order:
    """مدل سفارش"""
    id: Optional[int] = None
    user_id: int = 0
    button_id: int = 0
    order_data: Dict[str, Any] = field(default_factory=dict)
    payment_amount: int = 0
    tracking_code: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    admin_note: Optional[str] = None
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def status_text(self) -> str:
        """متن وضعیت به فارسی"""
        status_map = {
            OrderStatus.PENDING: '⏳ در انتظار پرداخت',
            OrderStatus.PAID: '✅ پرداخت شده',
            OrderStatus.COMPLETED: '✅ تکمیل شده',
            OrderStatus.CANCELLED: '❌ لغو شده',
            OrderStatus.FAILED: '❌ ناموفق',
            OrderStatus.REFUNDED: '🔄 بازگشت وجه',
        }
        return status_map.get(self.status, 'نامشخص')
    
    @property
    def status_icon(self) -> str:
        """آیکون وضعیت"""
        icon_map = {
            OrderStatus.PENDING: '⏳',
            OrderStatus.PAID: '✅',
            OrderStatus.COMPLETED: '🎉',
            OrderStatus.CANCELLED: '❌',
            OrderStatus.FAILED: '❌',
            OrderStatus.REFUNDED: '🔄',
        }
        return icon_map.get(self.status, '❓')
    
    @property
    def is_pending(self) -> bool:
        return self.status == OrderStatus.PENDING
    
    @property
    def is_paid(self) -> bool:
        return self.status in [OrderStatus.PAID, OrderStatus.COMPLETED]
    
    @property
    def is_completed(self) -> bool:
        return self.status == OrderStatus.COMPLETED
    
    @property
    def is_cancelled(self) -> bool:
        return self.status == OrderStatus.CANCELLED
    
    @property
    def can_cancel(self) -> bool:
        """آیا سفارش قابل لغو است"""
        return self.status == OrderStatus.PENDING
    
    @property
    def can_update_status(self) -> bool:
        """آیا وضعیت قابل تغییر است"""
        return self.status not in [OrderStatus.CANCELLED, OrderStatus.COMPLETED]
    
    @property
    def amount_formatted(self) -> str:
        """مبلغ فرمت‌شده با کاما"""
        return f"{self.payment_amount:,}"
    
    @property
    def created_at_formatted(self) -> str:
        """تاریخ ایجاد فرمت‌شده"""
        if not self.created_at:
            return "نامشخص"
        return self.created_at.strftime("%Y-%m-%d %H:%M")
    
    @property
    def answers(self) -> Dict[str, Any]:
        """پاسخ‌های کاربر از order_data"""
        return self.order_data.get('answers', {})
    
    @property
    def files(self) -> Dict[str, Any]:
        """فایل‌های ارسالی از order_data"""
        return self.order_data.get('files', {})
    
    @property
    def fullname(self) -> str:
        """نام کامل کاربر از order_data"""
        fullname = self.order_data.get('fullname')
        if fullname:
            return fullname
        answers = self.answers
        if answers:
            return next(iter(answers.values()), 'کاربر ناشناس')
        return 'کاربر ناشناس'
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'Order':
        """ایجاد از دیکشنری دیتابیس"""
        import json
        
        status = data.get('status', 'pending')
        status_map = {
            'pending': OrderStatus.PENDING,
            'paid': OrderStatus.PAID,
            'completed': OrderStatus.COMPLETED,
            'cancelled': OrderStatus.CANCELLED,
            'failed': OrderStatus.FAILED,
            'refunded': OrderStatus.REFUNDED,
        }
        
        order_data = data.get('order_data', {})
        if isinstance(order_data, str):
            try:
                order_data = json.loads(order_data)
            except:
                order_data = {}
        
        status_history = data.get('status_history', [])
        if isinstance(status_history, str):
            try:
                status_history = json.loads(status_history)
            except:
                status_history = []
        
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', 0),
            button_id=data.get('button_id', 0),
            order_data=order_data,
            payment_amount=data.get('payment_amount', 0) or 0,
            tracking_code=data.get('tracking_code'),
            status=status_map.get(status, OrderStatus.PENDING),
            admin_note=data.get('admin_note'),
            status_history=status_history,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_db(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای ذخیره در دیتابیس"""
        import json
        
        status_map = {
            OrderStatus.PENDING: 'pending',
            OrderStatus.PAID: 'paid',
            OrderStatus.COMPLETED: 'completed',
            OrderStatus.CANCELLED: 'cancelled',
            OrderStatus.FAILED: 'failed',
            OrderStatus.REFUNDED: 'refunded',
        }
        
        return {
            'user_id': self.user_id,
            'button_id': self.button_id,
            'order_data': json.dumps(self.order_data, ensure_ascii=False),
            'payment_amount': self.payment_amount,
            'tracking_code': self.tracking_code,
            'status': status_map.get(self.status, 'pending'),
            'admin_note': self.admin_note,
            'status_history': json.dumps(self.status_history, ensure_ascii=False),
        }
    
    def update_status(self, new_status: OrderStatus, user_id: int, note: Optional[str] = None) -> None:
        """بروزرسانی وضعیت سفارش و ثبت در تاریخچه"""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()
        
        # افزودن به تاریخچه
        self.status_history.append({
            'from': old_status.name,
            'to': new_status.name,
            'by': user_id,
            'timestamp': datetime.now().isoformat(),
            'note': note
        })
    
    def add_note(self, note: str, user_id: int) -> None:
        """افزودن یادداشت به سفارش"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_note = f"[{timestamp}] {note}"
        if self.admin_note:
            self.admin_note += f"\n{new_note}"
        else:
            self.admin_note = new_note
        
        self.updated_at = datetime.now()
    
    def get_last_status_change(self) -> Optional[Dict[str, Any]]:
        """دریافت آخرین تغییر وضعیت"""
        if not self.status_history:
            return None
        return self.status_history[-1]


# ============================================================
# توابع کمکی
# ============================================================

def create_order(user_id: int, button_id: int, order_data: Dict[str, Any],
                 payment_amount: int = 0, tracking_code: Optional[str] = None) -> Order:
    """ایجاد سفارش جدید"""
    return Order(
        user_id=user_id,
        button_id=button_id,
        order_data=order_data,
        payment_amount=payment_amount,
        tracking_code=tracking_code,
        status=OrderStatus.PENDING,
        created_at=datetime.now()
    )


__all__ = [
    'Order',
    'OrderStatus',
    'create_order',
]