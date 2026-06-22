# services/payment_service.py
# سرویس مدیریت پرداخت‌ها - منطق کسب‌وکار مربوط به پرداخت‌ها

import json
import time
import hmac
import hashlib
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import Optional, List, Dict, Any
from datetime import datetime
from logger_config import logger
from config import config
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class PaymentService:
    """سرویس مدیریت پرداخت‌ها"""
    
    def __init__(self, connection):
        """
        پارامترها:
            connection: اتصال به دیتابیس
        """
        self._connection = connection
        self._provider_token = config.PAYMENT_PROVIDER_TOKEN
        self._default_currency = "IRT"
    
    # ============================================================
    # ایجاد فاکتور
    # ============================================================
    
    def create_invoice_data(self, title: str, description: str,
                           price_amount: int, price_label: str = "هزینه خدمات",
                           payload: Optional[str] = None,
                           currency: str = "IRT") -> Dict[str, Any]:
        """
        ایجاد داده‌های فاکتور پرداخت
        
        پارامترها:
            title: عنوان فاکتور
            description: توضیحات فاکتور
            price_amount: مبلغ (به ریال)
            price_label: برچسب مبلغ
            payload: داده‌های اضافی برای شناسایی پرداخت
            currency: واحد پولی (پیش‌فرض: IRT)
        
        بازگشت: دیکشنری داده‌های فاکتور
        """
        if payload is None:
            payload = f"pay_{int(time.time())}"
        
        # اطمینان از حداقل مبلغ
        if price_amount < 10000:
            price_amount = 10000
        
        return {
            "title": title,
            "description": description,
            "payload": payload,
            "provider_token": self._provider_token,
            "currency": currency,
            "prices": [{"label": price_label, "amount": price_amount}],
            "start_parameter": "pay"
        }
    
    def create_service_invoice(self, button_name: str, button_id: int,
                              price_amount: int, price_label: str = "هزینه خدمات",
                              user_id: int = None) -> Dict[str, Any]:
        """
        ایجاد فاکتور برای یک سرویس
        
        پارامترها:
            button_name: نام دکمه/سرویس
            button_id: شناسه دکمه
            price_amount: مبلغ
            price_label: برچسب مبلغ
            user_id: شناسه کاربر (اختیاری)
        
        بازگشت: دیکشنری داده‌های فاکتور
        """
        title = f"پرداخت هزینه {button_name}"
        description = f"پرداخت برای {button_name}"
        
        # ایجاد payload منحصربه‌فرد
        payload_parts = [f"dyn_{button_id}"]
        if user_id:
            payload_parts.append(str(user_id))
        payload_parts.append(str(int(time.time())))
        payload = "_".join(payload_parts)
        
        return self.create_invoice_data(
            title=title,
            description=description,
            price_amount=price_amount,
            price_label=price_label,
            payload=payload
        )
    
    # ============================================================
    # تأیید و پردازش پرداخت
    # ============================================================
    
    def verify_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تأیید اطلاعات پرداخت
        
        پارامترها:
            payment_data: داده‌های پرداخت دریافتی از بله
        
        بازگشت: دیکشنری شامل اطلاعات تأییدشده پرداخت
        """
        # استخراج اطلاعات از payment_data
        # در بله، اطلاعات پرداخت در successful_payment قرار دارد
        success_payment = payment_data.get('successful_payment', {})
        
        result = {
            'is_valid': False,
            'tracking_code': None,
            'total_amount': 0,
            'payload': None,
            'payment_id': None,
            'error': None
        }
        
        try:
            # بررسی وجود اطلاعات پرداخت
            if not success_payment:
                result['error'] = 'No payment data found'
                return result
            
            # استخراج اطلاعات
            tracking_code = success_payment.get('provider_payment_charge_id')
            total_amount = success_payment.get('total_amount', 0)
            payload = success_payment.get('payload')
            payment_id = success_payment.get('payment_id')
            
            if not tracking_code:
                result['error'] = 'No tracking code found'
                return result
            
            # اعتبارسنجی مبلغ
            if total_amount <= 0:
                result['error'] = 'Invalid payment amount'
                return result
            
            result['is_valid'] = True
            result['tracking_code'] = tracking_code
            result['total_amount'] = total_amount
            result['payload'] = payload
            result['payment_id'] = payment_id
            
            logger.info(f"✅ Payment verified: {tracking_code} - {total_amount} IRT")
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error verifying payment: {str(e)}",
                traceback=traceback.format_exc()
            )
            result['error'] = str(e)
        
        return result
    
    def parse_payment_payload(self, payload: str) -> Dict[str, Any]:
        """
        تجزیه payload برای استخراج اطلاعات
        
        پارامترها:
            payload: رشته payload از پرداخت
        
        بازگشت: دیکشنری اطلاعات استخراج‌شده
        """
        result = {
            'type': None,
            'button_id': None,
            'user_id': None,
            'timestamp': None,
            'is_valid': False
        }
        
        if not payload:
            return result
        
        try:
            parts = payload.split('_')
            
            if len(parts) >= 3 and parts[0] == 'dyn':
                # فرمت: dyn_{button_id}_{user_id}_{timestamp}
                result['type'] = 'dynamic'
                result['button_id'] = int(parts[1]) if len(parts) > 1 else None
                result['user_id'] = int(parts[2]) if len(parts) > 2 else None
                result['timestamp'] = parts[3] if len(parts) > 3 else None
                result['is_valid'] = True
            
            elif payload.startswith('pay_'):
                # فرمت: pay_{timestamp}
                result['type'] = 'simple'
                result['timestamp'] = payload.split('_')[1] if len(payload.split('_')) > 1 else None
                result['is_valid'] = True
            
            else:
                result['type'] = 'unknown'
                result['payload'] = payload
                result['is_valid'] = False
                
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error parsing payment payload: {str(e)}",
                traceback=traceback.format_exc()
            )
            result['error'] = str(e)
        
        return result
    
    # ============================================================
    # مدیریت تراکنش‌ها (برای آینده)
    # ============================================================
    
    def log_payment(self, user_id: int, order_id: int, tracking_code: str,
                   amount: int, status: str = 'success') -> bool:
        """
        ثبت لاگ پرداخت
        
        پارامترها:
            user_id: شناسه کاربر
            order_id: شناسه سفارش
            tracking_code: کد رهگیری پرداخت
            amount: مبلغ
            status: وضعیت پرداخت (success, failed)
        
        بازگشت: True در صورت موفقیت
        """
        try:
            # استفاده از جدول button_stats برای ثبت آمار پرداخت
            from database.db_stats import log_order_paid
            log_order_paid(order_id, user_id, amount)
            
            logger.info(f"Payment logged: user={user_id}, order={order_id}, amount={amount}, tracking={tracking_code}")
            return True
            
        except Exception as e:
            # ✅ استفاده از log_database_error با traceback کامل
            log_database_error(
                f"Error logging payment: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return False
    
    def get_payment_summary(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت خلاصه پرداخت‌های یک کاربر
        
        پارامترها:
            user_id: شناسه کاربر
        
        بازگشت: دیکشنری شامل اطلاعات پرداخت‌های کاربر
        """
        try:
            from database import get_user_total_payment, get_user_orders_count
            
            total_amount = get_user_total_payment(user_id)
            orders_count = get_user_orders_count(user_id)
            
            return {
                'user_id': user_id,
                'total_paid': total_amount,
                'orders_count': orders_count,
                'avg_amount': total_amount / orders_count if orders_count > 0 else 0
            }
            
        except Exception as e:
            # ✅ استفاده از log_database_error با traceback کامل
            log_database_error(
                f"Error getting payment summary for user {user_id}: {str(e)}",
                traceback=traceback.format_exc(),
                user_id=user_id
            )
            return {
                'user_id': user_id,
                'total_paid': 0,
                'orders_count': 0,
                'avg_amount': 0,
                'error': str(e)
            }
    
    def get_total_revenue(self) -> Dict[str, Any]:
        """
        دریافت مجموع درآمد کل
        
        بازگشت: دیکشنری شامل کل درآمد و آمار
        """
        try:
            from database import get_dashboard_stats
            stats = get_dashboard_stats()
            
            return {
                'total_revenue': stats.get('total_revenue', 0),
                'total_orders': stats.get('total_orders', 0),
                'avg_order_value': stats.get('avg_order_value', 0),
            }
            
        except Exception as e:
            # ✅ استفاده از log_database_error با traceback کامل
            log_database_error(
                f"Error getting total revenue: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total_revenue': 0,
                'total_orders': 0,
                'avg_order_value': 0,
                'error': str(e)
            }
    
    def get_revenue_by_service(self) -> List[Dict[str, Any]]:
        """
        دریافت درآمد به تفکیک سرویس‌ها
        
        بازگشت: لیست دیکشنری‌های سرویس و درآمد
        """
        try:
            from database import get_db_connection
            
            query = """
                SELECT 
                    b.id as button_id,
                    b.name as service_name,
                    COUNT(o.id) as orders_count,
                    COALESCE(SUM(o.payment_amount), 0) as revenue
                FROM buttons b
                LEFT JOIN dynamic_orders o ON b.id = o.button_id AND o.status IN ('paid', 'completed')
                WHERE b.is_active = 1
                GROUP BY b.id
                ORDER BY revenue DESC
            """
            
            with self._connection.get_cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()
                
        except Exception as e:
            # ✅ استفاده از log_database_error با traceback کامل
            log_database_error(
                f"Error getting revenue by service: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    # ============================================================
    # پیاده‌سازی وب‌هوک (برای آینده)
    # ============================================================
    
    def verify_webhook_signature(self, data: Dict[str, Any], signature: str) -> bool:
        """
        بررسی امضای وب‌هوک (برای تأیید امنیتی)
        
        پارامترها:
            data: داده‌های دریافتی
            signature: امضای ارسال‌شده
        
        بازگشت: True اگر امضا معتبر باشد
        """
        try:
            # این یک پیاده‌سازی ساده است
            # در واقعیت باید از کلید مخفی مخصوص استفاده کرد
            expected = hmac.new(
                self._provider_token.encode(),
                json.dumps(data, sort_keys=True).encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected, signature)
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error verifying webhook signature: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def handle_webhook_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پردازش وب‌هوک پرداخت
        
        پارامترها:
            data: داده‌های دریافتی از وب‌هوک
        
        بازگشت: دیکشنری نتیجه پردازش
        """
        try:
            # استخراج اطلاعات پرداخت
            payment_data = data.get('payment', {})
            user_id = data.get('user_id')
            order_id = data.get('order_id')
            
            if not payment_data or not user_id or not order_id:
                return {
                    'success': False,
                    'error': 'Missing required data'
                }
            
            tracking_code = payment_data.get('tracking_code')
            amount = payment_data.get('amount', 0)
            
            if not tracking_code:
                return {
                    'success': False,
                    'error': 'Missing tracking code'
                }
            
            # به‌روزرسانی سفارش
            from services.order_service import OrderService
            order_service = OrderService(self._connection)
            
            # تغییر وضعیت سفارش به paid
            success = order_service.update_status(
                order_id,
                'paid',
                user_id,
                note=f"پرداخت از طریق وب‌هوک: {tracking_code}"
            )
            
            if success:
                # بروزرسانی کد رهگیری
                order_service.update_tracking_code(order_id, tracking_code)
                
                # ثبت لاگ پرداخت
                self.log_payment(user_id, order_id, tracking_code, amount)
                
                return {
                    'success': True,
                    'order_id': order_id,
                    'tracking_code': tracking_code,
                    'amount': amount
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to update order status'
                }
                
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error handling webhook payment: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'success': False,
                'error': str(e)
            }


__all__ = [
    'PaymentService',
]