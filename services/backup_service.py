# services/backup_service.py
# سرویس مدیریت پشتیبان‌گیری (Backup) و بازیابی (Restore) دیتابیس
# منطق کسب‌وکار مربوط به ایجاد، مدیریت و بازیابی پشتیبان‌ها

import os
import shutil
import sqlite3
import tempfile
import traceback  # ✅ اضافه شد برای traceback کامل
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from logger_config import logger
from config import config
from utils.error_handler import log_general_error, log_database_error  # ✅ اضافه شد


class BackupService:
    """سرویس مدیریت پشتیبان‌گیری و بازیابی دیتابیس"""
    
    def __init__(self, connection, db_path: Optional[str] = None,
                 backup_dir: Optional[str] = None):
        """
        پارامترها:
            connection: اتصال به دیتابیس
            db_path: مسیر فایل دیتابیس (در صورت عدم ارائه، از config استفاده می‌شود)
            backup_dir: پوشه پشتیبان (در صورت عدم ارائه، از config استفاده می‌شود)
        """
        self._connection = connection
        self._db_path = db_path or config.SQLITE_DB_PATH
        self._backup_dir = backup_dir or config.BACKUP_DIR
        self._max_backup_files = config.MAX_BACKUP_FILES
        self._ensure_backup_dir()
    
    # ============================================================
    # توابع کمکی
    # ============================================================
    
    def _ensure_backup_dir(self) -> str:
        """ایجاد پوشه پشتیبان در صورت عدم وجود"""
        if not os.path.exists(self._backup_dir):
            os.makedirs(self._backup_dir, exist_ok=True)
            logger.info(f"📁 پوشه پشتیبان ایجاد شد: {self._backup_dir}")
        return self._backup_dir
    
    def _get_backup_filename(self, prefix: str = "backup") -> str:
        """تولید نام فایل پشتیبان با زمان‌بندی"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.db"
    
    def _get_backup_path(self, filename: str) -> str:
        """دریافت مسیر کامل فایل پشتیبان"""
        return os.path.join(self._backup_dir, filename)
    
    def _get_backup_files(self) -> List[Dict[str, Any]]:
        """دریافت لیست فایل‌های پشتیبان با اطلاعات کامل"""
        files = []
        if not os.path.exists(self._backup_dir):
            return files
        
        for f in os.listdir(self._backup_dir):
            if f.endswith('.db'):
                file_path = os.path.join(self._backup_dir, f)
                try:
                    stat = os.stat(file_path)
                    files.append({
                        'name': f,
                        'path': file_path,
                        'size_kb': stat.st_size // 1024,
                        'size_bytes': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'is_auto': f.startswith('auto_backup') or f.startswith('pre_restore')
                    })
                except Exception as e:
                    log_general_error(
                        f"Error reading backup file {f}: {str(e)}",
                        traceback=traceback.format_exc()
                    )
        
        # مرتب‌سازی بر اساس تاریخ (جدیدترین اول)
        files.sort(key=lambda x: x['modified'], reverse=True)
        return files
    
    def _cleanup_old_backups(self, keep_count: Optional[int] = None) -> int:
        """
        حذف فایل‌های پشتیبان قدیمی (فقط تعداد مشخصی نگهداری می‌شوند)
        
        پارامترها:
            keep_count: تعداد فایل‌های نگهداری‌شده (در صورت عدم ارائه، از config استفاده می‌شود)
        
        بازگشت: تعداد فایل‌های حذف‌شده
        """
        if keep_count is None:
            keep_count = self._max_backup_files
        
        files = self._get_backup_files()
        if len(files) <= keep_count:
            return 0
        
        to_delete = files[keep_count:]  # فایل‌های قدیمی‌تر
        deleted = 0
        for file_info in to_delete:
            try:
                os.remove(file_info['path'])
                deleted += 1
                logger.info(f"🗑️ فایل پشتیبان قدیمی حذف شد: {file_info['name']}")
            except Exception as e:
                log_database_error(
                    f"Error deleting old backup file {file_info['name']}: {str(e)}",
                    traceback=traceback.format_exc()
                )
        
        return deleted
    
    def _validate_database_file(self, file_path: str) -> Tuple[bool, str]:
        """
        اعتبارسنجی فایل دیتابیس (بررسی اینکه آیا یک دیتابیس SQLite معتبر است)
        
        پارامترها:
            file_path: مسیر فایل
        
        بازگشت: (is_valid, message)
        """
        try:
            if not os.path.exists(file_path):
                return False, "فایل وجود ندارد."
            
            if os.path.getsize(file_path) == 0:
                return False, "فایل خالی است."
            
            # تلاش برای اتصال به دیتابیس
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # بررسی وجود جدول‌های اصلی
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buttons'")
            if not cursor.fetchone():
                conn.close()
                return False, "فایل دیتابیس معتبر نیست (جدول buttons یافت نشد)."
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
            if not cursor.fetchone():
                conn.close()
                return False, "فایل دیتابیس معتبر نیست (جدول categories یافت نشد)."
            
            conn.close()
            return True, "فایل معتبر است."
            
        except sqlite3.DatabaseError as e:
            log_database_error(
                f"Database error validating file {file_path}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False, f"خطای دیتابیس: {str(e)}"
        except Exception as e:
            log_general_error(
                f"Error validating database file {file_path}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False, f"خطا در اعتبارسنجی: {str(e)}"
    
    def _create_backup_file(self, backup_path: str) -> bool:
        """
        ایجاد یک فایل پشتیبان از دیتابیس فعلی
        از sqlite3.backup برای اطمینان از یکپارچگی استفاده می‌شود
        """
        try:
            # اطمینان از وجود پوشه
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # اتصال به دیتابیس اصلی
            src_conn = sqlite3.connect(self._db_path)
            src_conn.row_factory = sqlite3.Row
            
            # ایجاد دیتابیس مقصد
            dst_conn = sqlite3.connect(backup_path)
            
            # کپی کردن دیتابیس با استفاده از backup API
            src_conn.backup(dst_conn)
            
            # بستن اتصالات
            dst_conn.close()
            src_conn.close()
            
            logger.info(f"✅ فایل پشتیبان ایجاد شد: {backup_path}")
            return True
            
        except Exception as e:
            log_database_error(
                f"Error creating backup file {backup_path}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # عملیات اصلی پشتیبان‌گیری
    # ============================================================
    
    def create_backup(self, prefix: str = "backup", auto_cleanup: bool = True) -> Optional[Dict[str, Any]]:
        """
        ایجاد یک فایل پشتیبان جدید
        
        پارامترها:
            prefix: پیشوند نام فایل
            auto_cleanup: آیا پاکسازی خودکار انجام شود
        
        بازگشت: دیکشنری اطلاعات فایل پشتیبان یا None در صورت خطا
        """
        try:
            filename = self._get_backup_filename(prefix)
            backup_path = self._get_backup_path(filename)
            
            success = self._create_backup_file(backup_path)
            if not success:
                return None
            
            if auto_cleanup:
                self._cleanup_old_backups()
            
            stat = os.stat(backup_path)
            return {
                'name': filename,
                'path': backup_path,
                'size_kb': stat.st_size // 1024,
                'size_bytes': stat.st_size,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_auto': prefix in ['auto_backup', 'pre_restore']
            }
            
        except Exception as e:
            log_database_error(
                f"Error creating backup with prefix {prefix}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return None
    
    def get_backup_list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        دریافت لیست فایل‌های پشتیبان
        
        پارامترها:
            limit: تعداد نتایج (اختیاری)
        
        بازگشت: لیست فایل‌های پشتیبان
        """
        files = self._get_backup_files()
        if limit:
            return files[:limit]
        return files
    
    def get_backup_by_name(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        دریافت اطلاعات یک فایل پشتیبان بر اساس نام
        
        پارامترها:
            filename: نام فایل
        
        بازگشت: دیکشنری اطلاعات فایل یا None
        """
        files = self._get_backup_files()
        for file_info in files:
            if file_info['name'] == filename:
                return file_info
        return None
    
    def download_backup(self, filename: str) -> Optional[str]:
        """
        دریافت مسیر فایل پشتیبان برای دانلود
        
        پارامترها:
            filename: نام فایل
        
        بازگشت: مسیر فایل یا None
        """
        file_info = self.get_backup_by_name(filename)
        if not file_info:
            logger.warning(f"Backup file {filename} not found")
            return None
        
        if not os.path.exists(file_info['path']):
            logger.warning(f"Backup file {filename} does not exist on disk")
            return None
        
        return file_info['path']
    
    def delete_backup(self, filename: str) -> bool:
        """
        حذف یک فایل پشتیبان
        
        پارامترها:
            filename: نام فایل
        
        بازگشت: True در صورت موفقیت
        """
        file_info = self.get_backup_by_name(filename)
        if not file_info:
            logger.warning(f"Backup file {filename} not found")
            return False
        
        try:
            os.remove(file_info['path'])
            logger.info(f"🗑️ فایل پشتیبان حذف شد: {filename}")
            return True
        except Exception as e:
            log_database_error(
                f"Error deleting backup file {filename}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def cleanup_old_backups(self, keep_count: Optional[int] = None) -> int:
        """
        پاکسازی فایل‌های پشتیبان قدیمی
        
        پارامترها:
            keep_count: تعداد فایل‌های نگهداری‌شده
        
        بازگشت: تعداد فایل‌های حذف‌شده
        """
        return self._cleanup_old_backups(keep_count)
    
    def restore_backup(self, filename: str, create_auto_backup: bool = True) -> bool:
        """
        بازیابی دیتابیس از یک فایل پشتیبان
        
        پارامترها:
            filename: نام فایل پشتیبان
            create_auto_backup: آیا قبل از بازیابی، پشتیبان خودکار ایجاد شود
        
        بازگشت: True در صورت موفقیت
        """
        try:
            # ۱. بررسی وجود فایل
            file_info = self.get_backup_by_name(filename)
            if not file_info:
                logger.warning(f"Backup file {filename} not found")
                return False
            
            # ۲. اعتبارسنجی فایل
            is_valid, msg = self._validate_database_file(file_info['path'])
            if not is_valid:
                logger.warning(f"Invalid backup file: {msg}")
                return False
            
            # ۳. ایجاد پشتیبان خودکار از دیتابیس فعلی
            if create_auto_backup:
                auto_backup = self.create_backup("pre_restore", auto_cleanup=False)
                if auto_backup:
                    logger.info(f"✅ پشتیبان خودکار قبل از بازیابی ایجاد شد: {auto_backup['name']}")
            
            # ۴. انجام بازیابی (کپی فایل)
            shutil.copy2(file_info['path'], self._db_path)
            logger.info(f"✅ دیتابیس از فایل {filename} بازیابی شد.")
            
            # ۵. پاکسازی پشتیبان‌های قدیمی
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            log_database_error(
                f"Error restoring backup {filename}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    def restore_from_file(self, file_path: str, create_auto_backup: bool = True) -> bool:
        """
        بازیابی دیتابیس از یک فایل آپلودشده
        
        پارامترها:
            file_path: مسیر فایل آپلودشده
            create_auto_backup: آیا قبل از بازیابی، پشتیبان خودکار ایجاد شود
        
        بازگشت: True در صورت موفقیت
        """
        try:
            # ۱. اعتبارسنجی فایل
            is_valid, msg = self._validate_database_file(file_path)
            if not is_valid:
                logger.warning(f"Invalid file: {msg}")
                return False
            
            # ۲. کپی فایل به پوشه پشتیبان
            filename = self._get_backup_filename("restored")
            backup_path = self._get_backup_path(filename)
            shutil.copy2(file_path, backup_path)
            logger.info(f"📁 فایل آپلودشده در پوشه پشتیبان ذخیره شد: {filename}")
            
            # ۳. بازیابی
            return self.restore_backup(filename, create_auto_backup)
            
        except Exception as e:
            log_general_error(
                f"Error restoring from file {file_path}: {str(e)}",
                traceback=traceback.format_exc()
            )
            return False
    
    # ============================================================
    # وضعیت و گزارش
    # ============================================================
    
    def get_backup_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت پشتیبان‌گیری‌ها
        
        بازگشت: دیکشنری شامل اطلاعات وضعیت
        """
        try:
            files = self._get_backup_files()
            
            total_size = sum(f['size_bytes'] for f in files)
            auto_backups = [f for f in files if f['is_auto']]
            manual_backups = [f for f in files if not f['is_auto']]
            
            return {
                'total_files': len(files),
                'max_files': self._max_backup_files,
                'total_size_kb': total_size // 1024,
                'total_size_mb': total_size // (1024 * 1024),
                'auto_backups': len(auto_backups),
                'manual_backups': len(manual_backups),
                'last_backup': files[0] if files else None,
                'backup_dir': self._backup_dir,
                'db_path': self._db_path,
                'is_healthy': len(files) > 0
            }
        except Exception as e:
            log_general_error(
                f"Error getting backup status: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total_files': 0,
                'max_files': self._max_backup_files,
                'total_size_kb': 0,
                'total_size_mb': 0,
                'auto_backups': 0,
                'manual_backups': 0,
                'last_backup': None,
                'backup_dir': self._backup_dir,
                'db_path': self._db_path,
                'is_healthy': False
            }
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار پشتیبان‌ها
        
        بازگشت: دیکشنری شامل آمار
        """
        try:
            files = self._get_backup_files()
            
            if not files:
                return {
                    'total': 0,
                    'total_size_kb': 0,
                    'avg_size_kb': 0,
                    'oldest': None,
                    'newest': None,
                    'auto_count': 0,
                    'manual_count': 0
                }
            
            total_size = sum(f['size_bytes'] for f in files)
            avg_size = total_size // len(files) if files else 0
            
            return {
                'total': len(files),
                'total_size_kb': total_size // 1024,
                'avg_size_kb': avg_size // 1024,
                'oldest': files[-1]['modified_str'] if files else None,
                'newest': files[0]['modified_str'] if files else None,
                'auto_count': len([f for f in files if f['is_auto']]),
                'manual_count': len([f for f in files if not f['is_auto']])
            }
        except Exception as e:
            log_general_error(
                f"Error getting backup statistics: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total': 0,
                'total_size_kb': 0,
                'avg_size_kb': 0,
                'oldest': None,
                'newest': None,
                'auto_count': 0,
                'manual_count': 0
            }
    
    def get_backup_size_limit_status(self) -> Dict[str, Any]:
        """
        دریافت وضعیت محدودیت حجم پشتیبان‌ها
        
        بازگشت: دیکشنری شامل وضعیت
        """
        try:
            files = self._get_backup_files()
            total_size = sum(f['size_bytes'] for f in files)
            
            # محدودیت ۱ گیگابایت (برای هشدار)
            warning_limit = 1024 * 1024 * 1024  # 1 GB
            critical_limit = 2 * 1024 * 1024 * 1024  # 2 GB
            
            return {
                'total_size_mb': total_size // (1024 * 1024),
                'warning_limit_mb': warning_limit // (1024 * 1024),
                'critical_limit_mb': critical_limit // (1024 * 1024),
                'is_warning': total_size > warning_limit,
                'is_critical': total_size > critical_limit,
                'percentage': min(100, (total_size / warning_limit) * 100) if warning_limit > 0 else 0
            }
        except Exception as e:
            log_general_error(
                f"Error getting backup size limit status: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'total_size_mb': 0,
                'warning_limit_mb': 0,
                'critical_limit_mb': 0,
                'is_warning': False,
                'is_critical': False,
                'percentage': 0
            }
    
    # ============================================================
    # متدهای کمکی برای پنل مدیریت
    # ============================================================
    
    def get_backup_files_paginated(self, page: int = 0, per_page: int = 5) -> Dict[str, Any]:
        """
        دریافت لیست فایل‌های پشتیبان با صفحه‌بندی
        
        پارامترها:
            page: شماره صفحه (از ۰ شروع می‌شود)
            per_page: تعداد آیتم در هر صفحه
        
        بازگشت: دیکشنری شامل items, total, page, per_page, total_pages
        """
        try:
            files = self._get_backup_files()
            total = len(files)
            start = page * per_page
            end = min(start + per_page, total)
            
            return {
                'items': files[start:end],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page if total > 0 else 0
            }
        except Exception as e:
            log_general_error(
                f"Error getting paginated backup files: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            }
    
    def get_backup_file_count(self) -> int:
        """تعداد فایل‌های پشتیبان"""
        try:
            return len(self._get_backup_files())
        except Exception as e:
            log_general_error(
                f"Error getting backup file count: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_total_backup_size(self) -> int:
        """مجموع حجم پشتیبان‌ها (بایت)"""
        try:
            files = self._get_backup_files()
            return sum(f['size_bytes'] for f in files)
        except Exception as e:
            log_general_error(
                f"Error getting total backup size: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0
    
    def get_backup_files_by_date(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        دریافت پشتیبان‌های ایجادشده در تعداد روزهای اخیر
        
        پارامترها:
            days: تعداد روزهای اخیر
        
        بازگشت: لیست فایل‌های پشتیبان
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            files = self._get_backup_files()
            return [f for f in files if f['modified'] >= cutoff]
        except Exception as e:
            log_general_error(
                f"Error getting backup files by date: {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def get_backup_files_by_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        """
        دریافت پشتیبان‌ها بر اساس الگوی نام
        
        پارامترها:
            pattern: الگوی نام (مانند 'auto_backup' یا 'backup')
        
        بازگشت: لیست فایل‌های پشتیبان
        """
        try:
            files = self._get_backup_files()
            return [f for f in files if f['name'].startswith(pattern)]
        except Exception as e:
            log_general_error(
                f"Error getting backup files by pattern '{pattern}': {str(e)}",
                traceback=traceback.format_exc()
            )
            return []
    
    def is_backup_directory_writable(self) -> bool:
        """بررسی قابلیت نوشتن در پوشه پشتیبان"""
        try:
            self._ensure_backup_dir()
            test_file = os.path.join(self._backup_dir, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except Exception:
            return False
    
    def get_backup_directory_info(self) -> Dict[str, Any]:
        """
        دریافت اطلاعات پوشه پشتیبان
        
        بازگشت: دیکشنری شامل اطلاعات پوشه
        """
        try:
            exists = os.path.exists(self._backup_dir)
            is_writable = self.is_backup_directory_writable() if exists else False
            
            return {
                'path': self._backup_dir,
                'exists': exists,
                'is_writable': is_writable,
                'max_files': self._max_backup_files
            }
        except Exception as e:
            log_general_error(
                f"Error getting backup directory info: {str(e)}",
                traceback=traceback.format_exc()
            )
            return {
                'path': self._backup_dir,
                'exists': False,
                'is_writable': False,
                'max_files': self._max_backup_files
            }
    
    # ============================================================
    # متدهای مدیریت خودکار
    # ============================================================
    
    def auto_backup(self) -> Optional[Dict[str, Any]]:
        """
        ایجاد پشتیبان خودکار (با پیشوند auto_backup)
        
        بازگشت: دیکشنری اطلاعات فایل پشتیبان
        """
        return self.create_backup("auto_backup", auto_cleanup=True)
    
    def pre_restore_backup(self) -> Optional[Dict[str, Any]]:
        """
        ایجاد پشتیبان قبل از بازیابی (با پیشوند pre_restore)
        
        بازگشت: دیکشنری اطلاعات فایل پشتیبان
        """
        return self.create_backup("pre_restore", auto_cleanup=False)
    
    def cleanup_old_auto_backups(self, keep_count: int = 5) -> int:
        """
        پاکسازی پشتیبان‌های خودکار قدیمی
        
        پارامترها:
            keep_count: تعداد پشتیبان‌های خودکار نگهداری‌شده
        
        بازگشت: تعداد فایل‌های حذف‌شده
        """
        try:
            files = self._get_backup_files()
            auto_backups = [f for f in files if f['is_auto']]
            
            if len(auto_backups) <= keep_count:
                return 0
            
            to_delete = auto_backups[keep_count:]
            deleted = 0
            for file_info in to_delete:
                try:
                    os.remove(file_info['path'])
                    deleted += 1
                except Exception as e:
                    log_database_error(
                        f"Error deleting auto backup {file_info['name']}: {str(e)}",
                        traceback=traceback.format_exc()
                    )
            
            if deleted > 0:
                logger.info(f"🗑️ {deleted} پشتیبان خودکار قدیمی حذف شدند.")
            return deleted
        except Exception as e:
            log_general_error(
                f"Error cleaning up old auto backups: {str(e)}",
                traceback=traceback.format_exc()
            )
            return 0


__all__ = [
    'BackupService',
]