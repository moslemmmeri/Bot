# admin_panel/decorators.py
# دکوراتورهای مدیریت دسترسی و نقش‌ها - کنترل دسترسی به بخش‌های مختلف پنل مدیریت

from functools import wraps
import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from config import config
from core import send_message
from database import is_admin, get_user_role
from utils.error_handler import log_general_error  # ✅ اضافه شد


OWNER_ID = config.OWNER_ID


def get_user_role(user_id):
    """
    دریافت نقش کاربر از دیتابیس.
    اگر کاربر در دیتابیس نباشد، None برمی‌گرداند.
    """
    return get_user_role(user_id)


def require_owner(func):
    """
    دکوراتور: فقط OWNER_ID دسترسی دارد.
    اگر کاربر OWNER نباشد، پیام خطا نمایش داده می‌شود.
    """
    @wraps(func)
    async def wrapper(update, *args, **kwargs):
        try:
            # استخراج user_id از update
            cb = update.get("callback_query")
            if not cb:
                return await func(update, *args, **kwargs)
            
            user_id = cb.get("from", {}).get("id")
            chat_id = cb.get("message", {}).get("chat", {}).get("id")
            
            if not user_id or not chat_id:
                return await func(update, *args, **kwargs)
            
            if user_id != OWNER_ID:
                await send_message(chat_id, "⛔ فقط مالک ربات (OWNER) دسترسی به این بخش دارد.")
                logger.warning(f"دسترسی غیرمجاز به بخش OWNER توسط کاربر {user_id}")
                return True
            
            return await func(update, *args, **kwargs)
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error in require_owner decorator: {str(e)}",
                traceback=traceback.format_exc()
            )
            return await func(update, *args, **kwargs)
    
    return wrapper


def require_admin(func):
    """
    دکوراتور: فقط ادمین‌های فعال دسترسی دارند.
    شامل OWNER_ID نیز می‌شود (چون OWNER نیز ادمین محسوب می‌شود).
    """
    @wraps(func)
    async def wrapper(update, *args, **kwargs):
        try:
            cb = update.get("callback_query")
            if not cb:
                return await func(update, *args, **kwargs)
            
            user_id = cb.get("from", {}).get("id")
            chat_id = cb.get("message", {}).get("chat", {}).get("id")
            
            if not user_id or not chat_id:
                return await func(update, *args, **kwargs)
            
            # OWNER_ID همیشه مجاز است
            if user_id == OWNER_ID:
                return await func(update, *args, **kwargs)
            
            # بررسی ادمین بودن
            if not is_admin(user_id):
                await send_message(chat_id, "⛔ شما دسترسی به پنل مدیریت ندارید.")
                logger.warning(f"دسترسی غیرمجاز به پنل مدیریت توسط کاربر {user_id}")
                return True
            
            return await func(update, *args, **kwargs)
            
        except Exception as e:
            # ✅ استفاده از log_general_error با traceback کامل
            log_general_error(
                f"Error in require_admin decorator: {str(e)}",
                traceback=traceback.format_exc()
            )
            return await func(update, *args, **kwargs)
    
    return wrapper


def require_role(allowed_roles):
    """
    دکوراتور: کاربر باید یکی از نقش‌های مجاز را داشته باشد.
    allowed_roles: لیستی از نقش‌های مجاز (مانند ['admin', 'manager', 'owner'])
    
    OWNER_ID همیشه مجاز است (صرف‌نظر از نقش).
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update, *args, **kwargs):
            try:
                cb = update.get("callback_query")
                if not cb:
                    return await func(update, *args, **kwargs)
                
                user_id = cb.get("from", {}).get("id")
                chat_id = cb.get("message", {}).get("chat", {}).get("id")
                
                if not user_id or not chat_id:
                    return await func(update, *args, **kwargs)
                
                # OWNER_ID همیشه مجاز است
                if user_id == OWNER_ID:
                    return await func(update, *args, **kwargs)
                
                # دریافت نقش کاربر
                role = get_user_role(user_id)
                if not role:
                    await send_message(chat_id, "⛔ شما دسترسی به این بخش ندارید.")
                    logger.warning(f"کاربر {user_id} با نقش نامشخص تلاش به دسترسی کرد.")
                    return True
                
                if role not in allowed_roles:
                    await send_message(chat_id, f"⛔ دسترسی غیرمجاز. نقش شما: {role}")
                    logger.warning(f"کاربر {user_id} با نقش {role} تلاش به دسترسی به بخشی با نقش‌های مجاز {allowed_roles} کرد.")
                    return True
                
                return await func(update, *args, **kwargs)
                
            except Exception as e:
                # ✅ استفاده از log_general_error با traceback کامل
                log_general_error(
                    f"Error in require_role decorator: {str(e)}",
                    traceback=traceback.format_exc()
                )
                return await func(update, *args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(permission):
    """
    دکوراتور: کاربر باید مجوز (Permission) خاصی داشته باشد.
    این دکوراتور برای کنترل دسترسی‌های دقیق‌تر (مثلاً مدیریت سفارشات، مدیریت ادمین‌ها و ...) استفاده می‌شود.
    
    permission: نام مجوز مانند 'manage_orders', 'manage_admins', 'manage_buttons', 'view_analytics'
    
    **توجه:** برای استفاده از این دکوراتور، باید جدول permissions و نقشه‌ی نقش‌ها به مجوزها در دیتابیس تعریف شود.
    فعلاً به‌عنوان یک قابلیت برای آینده پیاده‌سازی می‌شود.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update, *args, **kwargs):
            try:
                cb = update.get("callback_query")
                if not cb:
                    return await func(update, *args, **kwargs)
                
                user_id = cb.get("from", {}).get("id")
                chat_id = cb.get("message", {}).get("chat", {}).get("id")
                
                if not user_id or not chat_id:
                    return await func(update, *args, **kwargs)
                
                # OWNER_ID همیشه مجاز است
                if user_id == OWNER_ID:
                    return await func(update, *args, **kwargs)
                
                # بررسی مجوز کاربر
                # این بخش نیاز به توسعه دارد - فعلاً فقط نقش را بررسی می‌کنیم
                role = get_user_role(user_id)
                
                # نقشه‌ی نقش‌ها به مجوزها (موقتی)
                role_permissions = {
                    'owner': ['*'],  # همه مجوزها
                    'admin': ['manage_orders', 'manage_buttons', 'view_analytics', 'manage_users'],
                    'manager': ['manage_orders', 'view_analytics'],
                    'observer': ['view_analytics']
                }
                
                if not role:
                    await send_message(chat_id, "⛔ شما دسترسی به این بخش ندارید.")
                    return True
                
                user_perms = role_permissions.get(role, [])
                if '*' in user_perms or permission in user_perms:
                    return await func(update, *args, **kwargs)
                
                await send_message(chat_id, f"⛔ دسترسی غیرمجاز. شما مجوز {permission} را ندارید.")
                logger.warning(f"کاربر {user_id} با نقش {role} تلاش به دسترسی به مجوز {permission} کرد.")
                return True
                
            except Exception as e:
                # ✅ استفاده از log_general_error با traceback کامل
                log_general_error(
                    f"Error in require_permission decorator: {str(e)}",
                    traceback=traceback.format_exc()
                )
                return await func(update, *args, **kwargs)
        
        return wrapper
    return decorator


def log_activity(action):
    """
    دکوراتور: ثبت فعالیت کاربر در لاگ (برای audit log).
    action: نام عملیات (مانند 'view_order', 'delete_button', 'add_admin')
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update, *args, **kwargs):
            try:
                cb = update.get("callback_query")
                if not cb:
                    return await func(update, *args, **kwargs)
                
                user_id = cb.get("from", {}).get("id")
                chat_id = cb.get("message", {}).get("chat", {}).get("id")
                data = cb.get("data")
                
                # اجرای تابع اصلی
                result = await func(update, *args, **kwargs)
                
                # ثبت لاگ
                logger.info(f"📝 فعالیت: {action} - کاربر {user_id} - دیتا: {data}")
                
                # در آینده می‌توان به دیتابیس نیز لاگ ثبت کرد
                # from database import add_admin_log
                # add_admin_log(user_id, action, data)
                
                return result
                
            except Exception as e:
                # ✅ استفاده از log_general_error با traceback کامل
                log_general_error(
                    f"Error in log_activity decorator: {str(e)}",
                    traceback=traceback.format_exc()
                )
                return await func(update, *args, **kwargs)
        
        return wrapper
    return decorator


# ==================== کلاس برای استفاده آسان‌تر ====================

class AdminAccess:
    """
    کلاس کمکی برای استفاده از دکوراتورها در مسیریابی.
    این کلاس به‌عنوان wrapper برای توابع مسیریابی استفاده می‌شود.
    
    مثال:
    @route("admin_orders")
    @AdminAccess.require_role(['admin', 'manager'])
    async def admin_orders(update):
        ...
    """
    
    @staticmethod
    def require_owner(func):
        return require_owner(func)
    
    @staticmethod
    def require_admin(func):
        return require_admin(func)
    
    @staticmethod
    def require_role(allowed_roles):
        return require_role(allowed_roles)
    
    @staticmethod
    def require_permission(permission):
        return require_permission(permission)
    
    @staticmethod
    def log_activity(action):
        return log_activity(action)


__all__ = [
    'require_owner',
    'require_admin',
    'require_role',
    'require_permission',
    'log_activity',
    'AdminAccess',
]