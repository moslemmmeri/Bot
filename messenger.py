# messenger.py
# مدیریت ارسال همزمان پیام‌ها با استفاده از asyncio.gather

import asyncio
import traceback  # ✅ اضافه شد برای traceback کامل
from typing import List, Dict, Any, Optional, Union, Callable, Awaitable
from config import config
from logger_config import logger
from core import send_message, send_photo, send_document
from utils.error_handler import log_general_error  # ✅ اضافه شد


class Messenger:
    """
    مدیریت ارسال همزمان پیام‌ها با استفاده از asyncio.gather
    برای افزایش سرعت ارسال در مواقعی که چندین پیام به یک یا چند کاربر ارسال می‌شود
    """
    
    def __init__(self):
        self._semaphore = asyncio.Semaphore(10)  # محدودیت همزمانی برای جلوگیری از overload
        self._timeout = config.HTTP_TIMEOUT
    
    async def _send_with_semaphore(self, func: Callable, *args, **kwargs) -> Any:
        """ارسال با محدودیت همزمانی"""
        async with self._semaphore:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=self._timeout)
            except asyncio.TimeoutError:
                # ✅ ثبت خطای تایم‌اوت با traceback کامل
                log_general_error(
                    f"Timeout in messenger: {func.__name__}",
                    traceback=traceback.format_exc()
                )
                return None
            except Exception as e:
                # ✅ ثبت خطا با traceback کامل
                log_general_error(
                    f"Error in messenger: {str(e)}",
                    traceback=traceback.format_exc()
                )
                return None
    
    async def send_messages(self, messages: List[Dict[str, Any]]) -> List[Any]:
        """
        ارسال همزمان چندین پیام متنی
        
        پارامترها:
            messages: لیست دیکشنری‌های شامل chat_id, text, keyboard (اختیاری)
        
        بازگشت: لیست نتایج ارسال
        """
        tasks = []
        for msg in messages:
            chat_id = msg.get('chat_id')
            text = msg.get('text')
            keyboard = msg.get('keyboard')
            if chat_id and text:
                tasks.append(self._send_with_semaphore(send_message, chat_id, text, keyboard))
        
        if not tasks:
            return []
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_photos(self, photos: List[Dict[str, Any]]) -> List[Any]:
        """
        ارسال همزمان چندین عکس
        
        پارامترها:
            photos: لیست دیکشنری‌های شامل chat_id, file_id, caption (اختیاری)
        
        بازگشت: لیست نتایج ارسال
        """
        tasks = []
        for photo in photos:
            chat_id = photo.get('chat_id')
            file_id = photo.get('file_id')
            caption = photo.get('caption', '')
            if chat_id and file_id:
                tasks.append(self._send_with_semaphore(send_photo, chat_id, file_id, caption))
        
        if not tasks:
            return []
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_documents(self, documents: List[Dict[str, Any]]) -> List[Any]:
        """
        ارسال همزمان چندین فایل
        
        پارامترها:
            documents: لیست دیکشنری‌های شامل chat_id, file_id, caption (اختیاری)
        
        بازگشت: لیست نتایج ارسال
        """
        tasks = []
        for doc in documents:
            chat_id = doc.get('chat_id')
            file_id = doc.get('file_id')
            file_path = doc.get('file_path')
            caption = doc.get('caption', '')
            if chat_id and (file_id or file_path):
                tasks.append(self._send_with_semaphore(send_document, chat_id, file_id, file_path, caption))
        
        if not tasks:
            return []
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_mixed(self, items: List[Dict[str, Any]]) -> List[Any]:
        """
        ارسال همزمان انواع مختلف پیام (متن، عکس، فایل)
        
        پارامترها:
            items: لیست دیکشنری‌های شامل type, chat_id, و سایر پارامترها
        
        بازگشت: لیست نتایج ارسال
        """
        tasks = []
        for item in items:
            msg_type = item.get('type', 'message')
            chat_id = item.get('chat_id')
            
            if not chat_id:
                continue
            
            if msg_type == 'photo':
                file_id = item.get('file_id')
                caption = item.get('caption', '')
                if file_id:
                    tasks.append(self._send_with_semaphore(send_photo, chat_id, file_id, caption))
            
            elif msg_type == 'document':
                file_id = item.get('file_id')
                file_path = item.get('file_path')
                caption = item.get('caption', '')
                if file_id or file_path:
                    tasks.append(self._send_with_semaphore(send_document, chat_id, file_id, file_path, caption))
            
            else:  # message
                text = item.get('text')
                keyboard = item.get('keyboard')
                if text:
                    tasks.append(self._send_with_semaphore(send_message, chat_id, text, keyboard))
        
        if not tasks:
            return []
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to_users(self, user_ids: List[int], text: str, keyboard: Optional[Dict] = None) -> List[Any]:
        """
        ارسال یک پیام به چندین کاربر همزمان
        
        پارامترها:
            user_ids: لیست شناسه‌های کاربران
            text: متن پیام
            keyboard: کیبورد (اختیاری)
        
        بازگشت: لیست نتایج ارسال
        """
        messages = [{'chat_id': uid, 'text': text, 'keyboard': keyboard} for uid in user_ids]
        return await self.send_messages(messages)
    
    async def send_batch(self, chat_id: int, contents: List[Dict[str, Any]]) -> List[Any]:
        """
        ارسال چندین محتوای مختلف به یک کاربر همزمان
        
        پارامترها:
            chat_id: شناسه کاربر
            contents: لیست محتواها (هر کدام شامل type و پارامترهای مربوطه)
        
        بازگشت: لیست نتایج ارسال
        """
        for item in contents:
            item['chat_id'] = chat_id
        return await self.send_mixed(contents)
    
    def create_batch_from_order(self, order: Dict, chat_id: int) -> List[Dict[str, Any]]:
        """
        ایجاد لیست محتوا از یک سفارش برای ارسال همزمان
        
        پارامترها:
            order: دیکشنری سفارش
            chat_id: شناسه کاربر
        
        بازگشت: لیست محتواها
        """
        import json
        contents = []
        
        # پیام اصلی
        order_data = order.get('order_data', {})
        if isinstance(order_data, str):
            try:
                order_data = json.loads(order_data)
            except:
                order_data = {}
        
        answers = order_data.get('answers', {})
        files = order_data.get('files', {})
        
        # ساخت پیام اصلی
        msg = f"📋 **جزئیات سفارش #{order.get('id')}**\n"
        msg += f"👤 کاربر: {order.get('user_id', 'نامشخص')}\n"
        msg += f"📌 وضعیت: {order.get('status', 'pending')}\n"
        msg += f"💰 مبلغ: {order.get('payment_amount', 0):,} ریال\n"
        msg += f"⏰ زمان: {order.get('created_at', 'نامشخص')}\n\n"
        msg += "📝 **پاسخ‌ها:**\n"
        
        for q_text, ans in answers.items():
            if q_text not in files:
                msg += f"▪️ {q_text}: {ans}\n"
        
        contents.append({
            'type': 'message',
            'chat_id': chat_id,
            'text': msg
        })
        
        # فایل‌ها
        for question_text, file_info in files.items():
            file_id = file_info.get('file_id')
            file_type = file_info.get('type', 'document')
            caption = f"📎 {question_text}"
            
            if file_type == 'photo':
                contents.append({
                    'type': 'photo',
                    'chat_id': chat_id,
                    'file_id': file_id,
                    'caption': caption
                })
            else:
                contents.append({
                    'type': 'document',
                    'chat_id': chat_id,
                    'file_id': file_id,
                    'caption': caption
                })
        
        return contents
    
    async def send_order_details(self, order: Dict, chat_id: int) -> List[Any]:
        """
        ارسال کامل جزئیات یک سفارش به صورت همزمان
        
        پارامترها:
            order: دیکشنری سفارش
            chat_id: شناسه کاربر
        
        بازگشت: لیست نتایج ارسال
        """
        contents = self.create_batch_from_order(order, chat_id)
        return await self.send_batch(chat_id, contents)
    
    async def broadcast(self, user_ids: List[int], message: str, keyboard: Optional[Dict] = None) -> Dict[str, Any]:
        """
        پخش پیام به چندین کاربر و نمایش آمار
        
        پارامترها:
            user_ids: لیست شناسه‌های کاربران
            message: متن پیام
            keyboard: کیبورد (اختیاری)
        
        بازگشت: دیکشنری شامل آمار ارسال
        """
        total = len(user_ids)
        results = await self.send_to_users(user_ids, message, keyboard)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_count += 1
                errors.append({'user_id': user_ids[i], 'error': str(result)})
            elif result is not None:
                success_count += 1
            else:
                error_count += 1
                errors.append({'user_id': user_ids[i], 'error': 'No response'})
        
        return {
            'total': total,
            'success': success_count,
            'error': error_count,
            'errors': errors
        }


# ============================================================
# آبجکت سراسری
# ============================================================

_messenger = None


def get_messenger() -> Messenger:
    """دریافت آبجکت سراسری Messenger (Singleton)"""
    global _messenger
    if _messenger is None:
        _messenger = Messenger()
    return _messenger


# ============================================================
# توابع راحت‌تر برای استفاده
# ============================================================

async def send_messages_batch(messages: List[Dict[str, Any]]) -> List[Any]:
    """ارسال همزمان چندین پیام متنی"""
    return await get_messenger().send_messages(messages)


async def send_photos_batch(photos: List[Dict[str, Any]]) -> List[Any]:
    """ارسال همزمان چندین عکس"""
    return await get_messenger().send_photos(photos)


async def send_documents_batch(documents: List[Dict[str, Any]]) -> List[Any]:
    """ارسال همزمان چندین فایل"""
    return await get_messenger().send_documents(documents)


async def send_mixed_batch(items: List[Dict[str, Any]]) -> List[Any]:
    """ارسال همزمان انواع مختلف پیام"""
    return await get_messenger().send_mixed(items)


async def broadcast_message(user_ids: List[int], message: str, keyboard: Optional[Dict] = None) -> Dict[str, Any]:
    """پخش پیام به چندین کاربر"""
    return await get_messenger().broadcast(user_ids, message, keyboard)


async def send_order_batch(order: Dict, chat_id: int) -> List[Any]:
    """ارسال کامل جزئیات یک سفارش به صورت همزمان"""
    return await get_messenger().send_order_details(order, chat_id)


# ============================================================
# کلاس کمکی برای ساخت بچ پیام
# ============================================================

class MessageBuilder:
    """کمک‌سازنده برای ساخت بچ پیام"""
    
    def __init__(self):
        self._items = []
    
    def add_message(self, chat_id: int, text: str, keyboard: Optional[Dict] = None) -> 'MessageBuilder':
        """افزودن پیام متنی"""
        self._items.append({
            'type': 'message',
            'chat_id': chat_id,
            'text': text,
            'keyboard': keyboard
        })
        return self
    
    def add_photo(self, chat_id: int, file_id: str, caption: str = '') -> 'MessageBuilder':
        """افزودن عکس"""
        self._items.append({
            'type': 'photo',
            'chat_id': chat_id,
            'file_id': file_id,
            'caption': caption
        })
        return self
    
    def add_document(self, chat_id: int, file_id: str, caption: str = '') -> 'MessageBuilder':
        """افزودن فایل"""
        self._items.append({
            'type': 'document',
            'chat_id': chat_id,
            'file_id': file_id,
            'caption': caption
        })
        return self
    
    def add_to_user(self, user_id: int, text: str, keyboard: Optional[Dict] = None) -> 'MessageBuilder':
        """افزودن پیام به یک کاربر (همان chat_id)"""
        return self.add_message(user_id, text, keyboard)
    
    def add_to_users(self, user_ids: List[int], text: str, keyboard: Optional[Dict] = None) -> 'MessageBuilder':
        """افزودن یک پیام به چندین کاربر"""
        for uid in user_ids:
            self.add_message(uid, text, keyboard)
        return self
    
    def add_batch(self, items: List[Dict[str, Any]]) -> 'MessageBuilder':
        """افزودن لیست محتوا"""
        self._items.extend(items)
        return self
    
    def build(self) -> List[Dict[str, Any]]:
        """دریافت لیست محتوا"""
        return self._items
    
    async def send(self) -> List[Any]:
        """ارسال همه محتواها به صورت همزمان"""
        return await send_mixed_batch(self._items)
    
    def clear(self) -> 'MessageBuilder':
        """پاک کردن لیست"""
        self._items = []
        return self


__all__ = [
    'Messenger',
    'get_messenger',
    'send_messages_batch',
    'send_photos_batch',
    'send_documents_batch',
    'send_mixed_batch',
    'broadcast_message',
    'send_order_batch',
    'MessageBuilder',
]