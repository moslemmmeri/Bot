# dto/order_dto.py
# Data Transfer Object برای سفارشات

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class OrderDTO:
    """
    Data Transfer Object برای سفارشات
    برای انتقال داده بین لایه‌های مختلف بدون وابستگی به مدل‌های دیتابیس
    """
    id: Optional[int] = None
    user_id: int = 0
    button_id: int = 0
    fullname: str = ""
    service_name: str = ""
    payment_amount: int = 0
    tracking_code: Optional[str] = None
    status: str = "pending"
    status_text: str = "⏳ در انتظار پرداخت"
    status_icon: str = "⏳"
    admin_note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    answers: Dict[str, Any] = field(default_factory=dict)
    files: Dict[str, Any] = field(default_factory=dict)
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_db(cls, data: Dict[str, Any]) -> 'OrderDTO':
        """ایجاد از دیکشنری دیتابیس"""
        from models.order import Order
        
        order = Order.from_db(data)
        
        return cls(
            id=order.id,
            user_id=order.user_id,
            button_id=order.button_id,
            fullname=order.fullname,
            service_name="",  # بعداً با ButtonService پر می‌شود
            payment_amount=order.payment_amount,
            tracking_code=order.tracking_code,
            status=order.status.name.lower(),
            status_text=order.status_text,
            status_icon=order.status_icon,
            admin_note=order.admin_note,
            created_at=order.created_at_formatted,
            updated_at=order.updated_at.strftime("%Y-%m-%d %H:%M") if order.updated_at else None,
            answers=order.answers,
            files=order.files,
            status_history=order.status_history,
        )
    
    @classmethod
    def from_db_with_service(cls, data: Dict[str, Any], service_name: str) -> 'OrderDTO':
        """ایجاد از دیکشنری دیتابیس با نام سرویس"""
        dto = cls.from_db(data)
        dto.service_name = service_name
        return dto
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای JSON"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'button_id': self.button_id,
            'fullname': self.fullname,
            'service_name': self.service_name,
            'payment_amount': self.payment_amount,
            'tracking_code': self.tracking_code,
            'status': self.status,
            'status_text': self.status_text,
            'status_icon': self.status_icon,
            'admin_note': self.admin_note,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'answers': self.answers,
            'files': self.files,
            'status_history': self.status_history,
        }
    
    @property
    def is_pending(self) -> bool:
        return self.status == "pending"
    
    @property
    def is_paid(self) -> bool:
        return self.status in ["paid", "completed"]
    
    @property
    def is_completed(self) -> bool:
        return self.status == "completed"
    
    @property
    def is_cancelled(self) -> bool:
        return self.status == "cancelled"
    
    @property
    def can_cancel(self) -> bool:
        return self.status == "pending"
    
    @property
    def amount_formatted(self) -> str:
        return f"{self.payment_amount:,}"
    
    @property
    def has_files(self) -> bool:
        return bool(self.files)
    
    @property
    def answer_count(self) -> int:
        return len(self.answers)
    
    @property
    def file_count(self) -> int:
        return len(self.files)


@dataclass
class OrderListDTO:
    """
    DTO برای لیست سفارشات با آمار
    """
    items: List[OrderDTO] = field(default_factory=list)
    total: int = 0
    page: int = 0
    per_page: int = 10
    total_pages: int = 0
    
    @classmethod
    def from_db_list(cls, orders: List[Dict[str, Any]], 
                     service_names: Dict[int, str] = None,
                     page: int = 0, per_page: int = 10, total: int = 0) -> 'OrderListDTO':
        """ایجاد از لیست دیکشنری‌های دیتابیس"""
        items = []
        for order in orders:
            dto = OrderDTO.from_db(order)
            if service_names and order.get('button_id') in service_names:
                dto.service_name = service_names[order.get('button_id')]
            items.append(dto)
        
        return cls(
            items=items,
            total=total or len(items),
            page=page,
            per_page=per_page,
            total_pages=((total or len(items)) + per_page - 1) // per_page if (total or len(items)) > 0 else 0
        )


@dataclass
class OrderStatsDTO:
    """
    DTO برای آمار سفارشات
    """
    total_orders: int = 0
    total_amount: int = 0
    avg_amount: int = 0
    pending_count: int = 0
    paid_count: int = 0
    completed_count: int = 0
    cancelled_count: int = 0
    total_users: int = 0
    
    @classmethod
    def from_db_stats(cls, stats: Dict[str, Any]) -> 'OrderStatsDTO':
        """ایجاد از دیکشنری آمار دیتابیس"""
        statuses = stats.get('statuses', {})
        return cls(
            total_orders=stats.get('total', 0),
            total_amount=stats.get('total_amount', 0),
            avg_amount=int(stats.get('avg_amount', 0)),
            pending_count=statuses.get('pending', 0),
            paid_count=statuses.get('paid', 0),
            completed_count=statuses.get('completed', 0),
            cancelled_count=statuses.get('cancelled', 0),
            total_users=stats.get('total_users', 0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_orders': self.total_orders,
            'total_amount': self.total_amount,
            'avg_amount': self.avg_amount,
            'pending_count': self.pending_count,
            'paid_count': self.paid_count,
            'completed_count': self.completed_count,
            'cancelled_count': self.cancelled_count,
            'total_users': self.total_users
        }


@dataclass
class OrderCreateDTO:
    """
    DTO برای ایجاد سفارش جدید
    """
    user_id: int
    button_id: int
    order_data: Dict[str, Any]
    payment_amount: int = 0
    tracking_code: Optional[str] = None
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        import json
        return {
            'user_id': self.user_id,
            'button_id': self.button_id,
            'order_data': json.dumps(self.order_data, ensure_ascii=False),
            'payment_amount': self.payment_amount,
            'tracking_code': self.tracking_code,
            'status': self.status
        }


@dataclass
class OrderUpdateDTO:
    """
    DTO برای به‌روزرسانی سفارش
    """
    order_id: int
    user_id: int
    new_status: Optional[str] = None
    note: Optional[str] = None
    tracking_code: Optional[str] = None
    admin_note: Optional[str] = None


@dataclass
class OrderFilterDTO:
    """
    DTO برای فیلترهای جستجوی سفارشات
    """
    status: Optional[str] = None
    user_id: Optional[int] = None
    button_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None
    tracking_code: Optional[str] = None
    keyword: Optional[str] = None
    has_file: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.status:
            result['status'] = self.status
        if self.user_id:
            result['user_id'] = self.user_id
        if self.button_id:
            result['button_id'] = self.button_id
        if self.start_date:
            result['start_date'] = self.start_date
        if self.end_date:
            result['end_date'] = self.end_date
        if self.min_amount is not None:
            result['min_amount'] = self.min_amount
        if self.max_amount is not None:
            result['max_amount'] = self.max_amount
        if self.tracking_code:
            result['tracking_code'] = self.tracking_code
        if self.keyword:
            result['keyword'] = self.keyword
        if self.has_file is not None:
            result['has_file'] = self.has_file
        return result


__all__ = [
    'OrderDTO',
    'OrderListDTO',
    'OrderStatsDTO',
    'OrderCreateDTO',
    'OrderUpdateDTO',
    'OrderFilterDTO',
]