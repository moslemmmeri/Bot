# tasks/backup_task.py
# تسک پشتیبان‌گیری خودکار از دیتابیس
# اصلاح شده با مدیریت خطا و لاگ‌گیری کامل در دیتابیس

import os
import asyncio
from datetime import datetime
from logger_config import logger
from config import config
from admin_panel.backup import (
    _ensure_backup_dir,
    _create_backup_file,
    _get_backup_filename,
    _cleanup_old_backups
)
from utils.error_handler import (
    log_critical_error,
    log_general_error,
    log_api_error,
    log_database_error
)


async def run_backup_task():
    """
    اجرای تسک پشتیبان‌گیری خودکار
    این تابع توسط Scheduler در زمان‌های مشخص فراخوانی می‌شود
    """
    try:
        logger.info("🔄 Starting automatic backup task...")
        
        # ایجاد پوشه پشتیبان
        backup_dir = _ensure_backup_dir()
        
        # تولید نام فایل
        filename = _get_backup_filename("auto_backup")
        backup_path = os.path.join(backup_dir, filename)
        
        # ایجاد فایل پشتیبان
        start_time = datetime.now()
        success = _create_backup_file(backup_path)
        
        if success:
            # پاکسازی فایل‌های قدیمی
            _cleanup_old_backups()
            
            # محاسبه حجم و زمان
            file_size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"✅ Auto backup completed successfully\n"
                f"   📁 File: {filename}\n"
                f"   📊 Size: {file_size // 1024} KB\n"
                f"   ⏱️  Time: {elapsed:.2f} seconds"
            )
            
            # ارسال گزارش به OWNER (در صورت نیاز)
            await _notify_owner(backup_path, filename, file_size, elapsed)
            
            return True
        else:
            log_general_error("❌ Auto backup failed - _create_backup_file returned False")
            await _notify_owner(None, filename, 0, 0, error=True)
            return False
            
    except Exception as e:
        log_critical_error(
            f"Error in backup_task: {str(e)}",
            traceback=str(e)
        )
        return False


async def _notify_owner(backup_path, filename, file_size, elapsed, error=False):
    """
    ارسال گزارش پشتیبان‌گیری به OWNER
    
    پارامترها:
        backup_path: مسیر فایل پشتیبان
        filename: نام فایل
        file_size: حجم فایل (بایت)
        elapsed: زمان اجرا (ثانیه)
        error: آیا خطا رخ داده است
    """
    try:
        from core import send_message, OWNER_ID
        
        if error:
            msg = (
                f"🚨 **خطا در پشتیبان‌گیری خودکار**\n\n"
                f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📁 فایل: {filename}\n"
                f"❌ وضعیت: ناموفق\n\n"
                f"لطفاً لاگ‌ها را بررسی کنید."
            )
        else:
            msg = (
                f"✅ **پشتیبان‌گیری خودکار انجام شد**\n\n"
                f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📁 فایل: {filename}\n"
                f"📊 حجم: {file_size // 1024} KB\n"
                f"⏱️  زمان اجرا: {elapsed:.2f} ثانیه\n"
                f"📂 مسیر: {backup_path}\n\n"
                f"تعداد فایل‌های پشتیبان موجود: {_count_backup_files()}"
            )
        
        await send_message(OWNER_ID, msg)
        
    except Exception as e:
        log_api_error(
            f"Error sending backup notification to owner: {str(e)}",
            traceback=str(e),
            user_id=OWNER_ID if 'OWNER_ID' in dir() else None
        )


def _count_backup_files() -> int:
    """تعداد فایل‌های پشتیبان موجود"""
    try:
        backup_dir = _ensure_backup_dir()
        files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        return len(files)
    except Exception as e:
        log_database_error(
            f"Error counting backup files: {str(e)}",
            traceback=str(e)
        )
        return 0


def get_backup_status() -> dict:
    """
    دریافت وضعیت پشتیبان‌گیری‌ها
    
    بازگشت: دیکشنری شامل اطلاعات پشتیبان‌ها
    """
    try:
        backup_dir = _ensure_backup_dir()
        files = []
        
        for f in os.listdir(backup_dir):
            if f.endswith('.db'):
                file_path = os.path.join(backup_dir, f)
                stat = os.stat(file_path)
                files.append({
                    'name': f,
                    'size_kb': stat.st_size // 1024,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'is_auto': f.startswith('auto_backup')
                })
        
        # مرتب‌سازی بر اساس تاریخ (جدیدترین اول)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            'total_files': len(files),
            'max_files': config.MAX_BACKUP_FILES,
            'files': files,
            'backup_dir': backup_dir,
            'last_backup': files[0]['modified'] if files else None,
            'last_backup_name': files[0]['name'] if files else None,
        }
        
    except Exception as e:
        log_general_error(
            f"Error getting backup status: {str(e)}",
            traceback=str(e)
        )
        return {
            'total_files': 0,
            'max_files': config.MAX_BACKUP_FILES,
            'files': [],
            'backup_dir': '',
            'last_backup': None,
            'last_backup_name': None,
            'error': str(e)
        }


__all__ = [
    'run_backup_task',
    'get_backup_status',
    '_notify_owner',
]