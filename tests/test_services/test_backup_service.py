# tests/test_services/test_backup_service.py
# تست‌های واحد برای BackupService

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, mock_open

import pytest

from services.backup_service import BackupService


class TestBackupService:
    """تست‌های BackupService"""

    @pytest.fixture
    def backup_service(self, db_connection, temp_db_path):
        """ایجاد BackupService با اتصال دیتابیس تست"""
        # ایجاد یک دیتابیس موقت با جداول اصلی
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE buttons (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.close()

        with patch('config.config.SQLITE_DB_PATH', temp_db_path):
            with patch('config.config.BACKUP_DIR', tempfile.mkdtemp()):
                service = BackupService(db_connection, db_path=temp_db_path)
                yield service

    @pytest.fixture
    def temp_backup_dir(self):
        """ایجاد پوشه موقت برای پشتیبان‌ها"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    # ============================================================
    # تست‌های _ensure_backup_dir
    # ============================================================

    def test_ensure_backup_dir_creates_directory(self, backup_service):
        """تست ایجاد پوشه پشتیبان در صورت عدم وجود"""
        with patch('os.path.exists', return_value=False):
            with patch('os.makedirs') as mock_makedirs:
                result = backup_service._ensure_backup_dir()
                mock_makedirs.assert_called_once_with(backup_service._backup_dir, exist_ok=True)
                assert result == backup_service._backup_dir

    def test_ensure_backup_dir_exists(self, backup_service):
        """تست وقتی پوشه پشتیبان وجود دارد"""
        with patch('os.path.exists', return_value=True):
            with patch('os.makedirs') as mock_makedirs:
                result = backup_service._ensure_backup_dir()
                mock_makedirs.assert_not_called()
                assert result == backup_service._backup_dir

    # ============================================================
    # تست‌های _get_backup_filename
    # ============================================================

    def test_get_backup_filename_default(self, backup_service):
        """تست تولید نام فایل پشتیبان با پیشوند پیش‌فرض"""
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
            filename = backup_service._get_backup_filename()
            assert filename == 'backup_20240101_120000.db'

    def test_get_backup_filename_with_prefix(self, backup_service):
        """تست تولید نام فایل پشتیبان با پیشوند سفارشی"""
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
            filename = backup_service._get_backup_filename('auto_backup')
            assert filename == 'auto_backup_20240101_120000.db'

    # ============================================================
    # تست‌های _get_backup_files
    # ============================================================

    def test_get_backup_files_empty(self, backup_service):
        """تست دریافت لیست فایل‌های پشتیبان در صورت خالی بودن پوشه"""
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=[]):
                files = backup_service._get_backup_files()
                assert files == []

    def test_get_backup_files_with_files(self, backup_service, temp_backup_dir):
        """تست دریافت لیست فایل‌های پشتیبان"""
        # ایجاد فایل‌های تست
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            for i in range(3):
                with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                    f.write('test')

            files = backup_service._get_backup_files()
            assert len(files) == 3
            for f in files:
                assert f['name'].startswith('backup_')
                assert f['name'].endswith('.db')
                assert 'size_kb' in f
                assert 'modified' in f
                assert 'path' in f

    def test_get_backup_files_only_db_files(self, backup_service, temp_backup_dir):
        """تست دریافت فقط فایل‌های با پسوند .db"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد فایل‌های مختلف
            with open(os.path.join(temp_backup_dir, 'backup_1.db'), 'w') as f:
                f.write('test')
            with open(os.path.join(temp_backup_dir, 'file.txt'), 'w') as f:
                f.write('test')
            with open(os.path.join(temp_backup_dir, 'backup_2.db'), 'w') as f:
                f.write('test')

            files = backup_service._get_backup_files()
            assert len(files) == 2
            for f in files:
                assert f['name'].endswith('.db')

    # ============================================================
    # تست‌های _cleanup_old_backups
    # ============================================================

    def test_cleanup_old_backups_no_files(self, backup_service):
        """تست پاکسازی وقتی فایلی وجود ندارد"""
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=[]):
                deleted = backup_service._cleanup_old_backups()
                assert deleted == 0

    def test_cleanup_old_backups_under_limit(self, backup_service, temp_backup_dir):
        """تست پاکسازی وقتی تعداد فایل‌ها کمتر از حد مجاز است"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد ۳ فایل (حداکثر ۱۰)
            for i in range(3):
                with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                    f.write('test')

            deleted = backup_service._cleanup_old_backups()
            assert deleted == 0
            # همه فایل‌ها باید باقی بمانند
            files = os.listdir(temp_backup_dir)
            assert len(files) == 3

    def test_cleanup_old_backups_over_limit(self, backup_service, temp_backup_dir):
        """تست پاکسازی وقتی تعداد فایل‌ها بیشتر از حد مجاز است"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            with patch.object(backup_service, '_max_backup_files', 3):
                # ایجاد ۵ فایل
                for i in range(5):
                    with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                        f.write('test')
                    # تنظیم زمان اصلاح برای مرتب‌سازی
                    os.utime(os.path.join(temp_backup_dir, f'backup_{i}.db'), (i, i))

                deleted = backup_service._cleanup_old_backups()
                assert deleted == 2
                # فقط ۳ فایل باید باقی بمانند
                files = os.listdir(temp_backup_dir)
                assert len(files) == 3

    # ============================================================
    # تست‌های _validate_database_file
    # ============================================================

    def test_validate_database_file_success(self, backup_service, temp_db_path):
        """تست اعتبارسنجی فایل دیتابیس معتبر"""
        # ایجاد یک فایل دیتابیس معتبر
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE buttons (id INTEGER PRIMARY KEY)")
        cursor.execute("CREATE TABLE categories (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        is_valid, msg = backup_service._validate_database_file(temp_db_path)
        assert is_valid is True
        assert msg == "فایل معتبر است."

    def test_validate_database_file_not_exists(self, backup_service):
        """تست اعتبارسنجی فایل ناموجود"""
        with patch('os.path.exists', return_value=False):
            is_valid, msg = backup_service._validate_database_file('/nonexistent/path.db')
            assert is_valid is False
            assert "فایل وجود ندارد" in msg

    def test_validate_database_file_empty(self, backup_service, temp_db_path):
        """تست اعتبارسنجی فایل خالی"""
        with open(temp_db_path, 'w') as f:
            pass

        is_valid, msg = backup_service._validate_database_file(temp_db_path)
        assert is_valid is False
        assert "خالی است" in msg

    def test_validate_database_file_invalid(self, backup_service):
        """تست اعتبارسنجی فایل نامعتبر (بدون جداول)"""
        with tempfile.NamedTemporaryFile(suffix='.db') as tmp:
            conn = sqlite3.connect(tmp.name)
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.commit()
            conn.close()

            is_valid, msg = backup_service._validate_database_file(tmp.name)
            assert is_valid is False
            assert "جدول buttons یافت نشد" in msg

    # ============================================================
    # تست‌های _create_backup_file
    # ============================================================

    def test_create_backup_file_success(self, backup_service, temp_db_path):
        """تست ایجاد فایل پشتیبان با موفقیت"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            backup_path = tmp.name

        # ایجاد یک دیتابیس نمونه
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test (name) VALUES ('test1'), ('test2')")
        conn.commit()
        conn.close()

        with patch.object(backup_service, '_db_path', temp_db_path):
            result = backup_service._create_backup_file(backup_path)

            assert result is True
            assert os.path.exists(backup_path)

            # بررسی محتویات فایل پشتیبان
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM test")
            count = cursor.fetchone()[0]
            assert count == 2
            conn.close()

            os.unlink(backup_path)

    def test_create_backup_file_fails(self, backup_service):
        """تست ایجاد فایل پشتیبان با خطا"""
        with patch('sqlite3.connect', side_effect=sqlite3.OperationalError('Disk full')):
            result = backup_service._create_backup_file('/path/to/backup.db')
            assert result is False

    # ============================================================
    # تست‌های create_backup
    # ============================================================

    def test_create_backup_success(self, backup_service, temp_db_path):
        """تست ایجاد پشتیبان جدید با موفقیت"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(backup_service, '_backup_dir', tmpdir):
                with patch.object(backup_service, '_db_path', temp_db_path):
                    # ایجاد یک دیتابیس نمونه
                    conn = sqlite3.connect(temp_db_path)
                    cursor = conn.cursor()
                    cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
                    cursor.execute("INSERT INTO test (name) VALUES ('test')")
                    conn.commit()
                    conn.close()

                    result = backup_service.create_backup()

                    assert result is not None
                    assert 'name' in result
                    assert 'path' in result
                    assert 'size_kb' in result
                    assert 'created_at' in result
                    assert result['name'].startswith('backup_')
                    assert os.path.exists(result['path'])

    def test_create_backup_with_cleanup(self, backup_service, temp_backup_dir):
        """تست ایجاد پشتیبان با پاکسازی خودکار"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            with patch.object(backup_service, '_create_backup_file', return_value=True):
                with patch.object(backup_service, '_cleanup_old_backups') as mock_cleanup:
                    result = backup_service.create_backup(auto_cleanup=True)

                    assert result is not None
                    mock_cleanup.assert_called_once()

    def test_create_backup_without_cleanup(self, backup_service, temp_backup_dir):
        """تست ایجاد پشتیبان بدون پاکسازی خودکار"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            with patch.object(backup_service, '_create_backup_file', return_value=True):
                with patch.object(backup_service, '_cleanup_old_backups') as mock_cleanup:
                    result = backup_service.create_backup(auto_cleanup=False)

                    assert result is not None
                    mock_cleanup.assert_not_called()

    def test_create_backup_fails(self, backup_service):
        """تست ایجاد پشتیبان با خطا"""
        with patch.object(backup_service, '_create_backup_file', return_value=False):
            result = backup_service.create_backup()
            assert result is None

    # ============================================================
    # تست‌های get_backup_list
    # ============================================================

    def test_get_backup_list(self, backup_service, temp_backup_dir):
        """تست دریافت لیست پشتیبان‌ها"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد چند فایل
            for i in range(3):
                with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                    f.write('test')

            files = backup_service.get_backup_list()
            assert len(files) == 3

    def test_get_backup_list_with_limit(self, backup_service, temp_backup_dir):
        """تست دریافت لیست پشتیبان‌ها با محدودیت تعداد"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد چند فایل
            for i in range(5):
                with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                    f.write('test')

            files = backup_service.get_backup_list(limit=2)
            assert len(files) == 2

    # ============================================================
    # تست‌های get_backup_by_name
    # ============================================================

    def test_get_backup_by_name_found(self, backup_service, temp_backup_dir):
        """تست دریافت پشتیبان با نام موجود"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد یک فایل
            with open(os.path.join(temp_backup_dir, 'test_backup.db'), 'w') as f:
                f.write('test')

            file_info = backup_service.get_backup_by_name('test_backup.db')
            assert file_info is not None
            assert file_info['name'] == 'test_backup.db'
            assert file_info['path'] == os.path.join(temp_backup_dir, 'test_backup.db')

    def test_get_backup_by_name_not_found(self, backup_service):
        """تست دریافت پشتیبان با نام ناموجود"""
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['backup_1.db']):
                file_info = backup_service.get_backup_by_name('nonexistent.db')
                assert file_info is None

    # ============================================================
    # تست‌های download_backup
    # ============================================================

    def test_download_backup_success(self, backup_service, temp_backup_dir):
        """تست دریافت مسیر فایل پشتیبان برای دانلود"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد یک فایل
            with open(os.path.join(temp_backup_dir, 'test_backup.db'), 'w') as f:
                f.write('test')

            path = backup_service.download_backup('test_backup.db')
            assert path == os.path.join(temp_backup_dir, 'test_backup.db')

    def test_download_backup_not_found(self, backup_service):
        """تست دانلود پشتیبان ناموجود"""
        with patch.object(backup_service, 'get_backup_by_name', return_value=None):
            path = backup_service.download_backup('nonexistent.db')
            assert path is None

    def test_download_backup_file_not_exist(self, backup_service):
        """تست دانلود پشتیبان با فایل ناموجود روی دیسک"""
        with patch.object(backup_service, 'get_backup_by_name', return_value={'name': 'test.db', 'path': '/path/to/test.db'}):
            with patch('os.path.exists', return_value=False):
                path = backup_service.download_backup('test.db')
                assert path is None

    # ============================================================
    # تست‌های delete_backup
    # ============================================================

    def test_delete_backup_success(self, backup_service, temp_backup_dir):
        """تست حذف پشتیبان با موفقیت"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد یک فایل
            filepath = os.path.join(temp_backup_dir, 'test_backup.db')
            with open(filepath, 'w') as f:
                f.write('test')

            result = backup_service.delete_backup('test_backup.db')
            assert result is True
            assert not os.path.exists(filepath)

    def test_delete_backup_not_found(self, backup_service):
        """تست حذف پشتیبان ناموجود"""
        with patch.object(backup_service, 'get_backup_by_name', return_value=None):
            result = backup_service.delete_backup('nonexistent.db')
            assert result is False

    def test_delete_backup_os_error(self, backup_service):
        """تست حذف پشتیبان با خطای سیستمی"""
        with patch.object(backup_service, 'get_backup_by_name', return_value={'name': 'test.db', 'path': '/path/to/test.db'}):
            with patch('os.remove', side_effect=OSError('Permission denied')):
                result = backup_service.delete_backup('test.db')
                assert result is False

    # ============================================================
    # تست‌های cleanup_old_backups
    # ============================================================

    def test_cleanup_old_backups_public(self, backup_service):
        """تست پاکسازی پشتیبان‌های قدیمی (متد عمومی)"""
        with patch.object(backup_service, '_cleanup_old_backups', return_value=3) as mock_cleanup:
            result = backup_service.cleanup_old_backups(keep_count=5)
            assert result == 3
            mock_cleanup.assert_called_once_with(5)

    # ============================================================
    # تست‌های restore_backup
    # ============================================================

    def test_restore_backup_success(self, backup_service, temp_backup_dir, temp_db_path):
        """تست بازیابی پشتیبان با موفقیت"""
        # ایجاد یک فایل پشتیبان معتبر
        backup_path = os.path.join(temp_backup_dir, 'backup.db')
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE buttons (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO buttons (name) VALUES ('test_button')")
        conn.commit()
        conn.close()

        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            with patch.object(backup_service, '_db_path', temp_db_path):
                with patch.object(backup_service, 'get_backup_by_name', return_value={
                    'name': 'backup.db',
                    'path': backup_path,
                }):
                    with patch.object(backup_service, '_validate_database_file', return_value=(True, 'valid')):
                        with patch('shutil.copy2') as mock_copy:
                            with patch.object(backup_service, '_cleanup_old_backups'):
                                result = backup_service.restore_backup('backup.db', create_auto_backup=False)

                                assert result is True
                                mock_copy.assert_called_once_with(backup_path, temp_db_path)

    def test_restore_backup_not_found(self, backup_service):
        """تست بازیابی پشتیبان ناموجود"""
        with patch.object(backup_service, 'get_backup_by_name', return_value=None):
            result = backup_service.restore_backup('nonexistent.db')
            assert result is False

    def test_restore_backup_invalid_file(self, backup_service):
        """تست بازیابی فایل نامعتبر"""
        with patch.object(backup_service, 'get_backup_by_name', return_value={'name': 'backup.db', 'path': '/path/to/backup.db'}):
            with patch.object(backup_service, '_validate_database_file', return_value=(False, 'Invalid')):
                result = backup_service.restore_backup('backup.db')
                assert result is False

    def test_restore_backup_with_auto_backup(self, backup_service, temp_backup_dir):
        """تست بازیابی با ایجاد پشتیبان خودکار"""
        with patch.object(backup_service, 'get_backup_by_name', return_value={'name': 'backup.db', 'path': '/path/to/backup.db'}):
            with patch.object(backup_service, '_validate_database_file', return_value=(True, 'valid')):
                with patch.object(backup_service, 'create_backup') as mock_create_backup:
                    with patch('shutil.copy2'):
                        with patch.object(backup_service, '_cleanup_old_backups'):
                            result = backup_service.restore_backup('backup.db', create_auto_backup=True)

                            assert result is True
                            mock_create_backup.assert_called_once_with('pre_restore', auto_cleanup=False)

    # ============================================================
    # تست‌های restore_from_file
    # ============================================================

    def test_restore_from_file_success(self, backup_service, temp_backup_dir, temp_db_path):
        """تست بازیابی از فایل آپلودشده با موفقیت"""
        # ایجاد یک فایل دیتابیس معتبر
        file_path = os.path.join(temp_backup_dir, 'uploaded.db')
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE buttons (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.close()

        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            with patch.object(backup_service, '_db_path', temp_db_path):
                with patch.object(backup_service, '_validate_database_file', return_value=(True, 'valid')):
                    with patch.object(backup_service, 'restore_backup', return_value=True) as mock_restore:
                        result = backup_service.restore_from_file(file_path, create_auto_backup=False)

                        assert result is True
                        mock_restore.assert_called_once()

    def test_restore_from_file_invalid(self, backup_service):
        """تست بازیابی از فایل نامعتبر"""
        with patch.object(backup_service, '_validate_database_file', return_value=(False, 'Invalid')):
            result = backup_service.restore_from_file('/path/to/file.db')
            assert result is False

    # ============================================================
    # تست‌های get_backup_status
    # ============================================================

    def test_get_backup_status(self, backup_service, temp_backup_dir):
        """تست دریافت وضعیت پشتیبان‌ها"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد چند فایل با نام‌های مختلف
            with open(os.path.join(temp_backup_dir, 'auto_backup_1.db'), 'w') as f:
                f.write('test')
            with open(os.path.join(temp_backup_dir, 'auto_backup_2.db'), 'w') as f:
                f.write('test')
            with open(os.path.join(temp_backup_dir, 'backup_manual.db'), 'w') as f:
                f.write('test')

            status = backup_service.get_backup_status()
            assert status['total_files'] == 3
            assert status['auto_backups'] == 2
            assert status['manual_backups'] == 1
            assert status['max_files'] == backup_service._max_backup_files
            assert status['is_healthy'] is True

    def test_get_backup_status_empty(self, backup_service):
        """تست دریافت وضعیت پشتیبان‌ها در صورت خالی بودن"""
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=[]):
                status = backup_service.get_backup_status()
                assert status['total_files'] == 0
                assert status['is_healthy'] is False

    # ============================================================
    # تست‌های get_backup_statistics
    # ============================================================

    def test_get_backup_statistics(self, backup_service, temp_backup_dir):
        """تست دریافت آمار پشتیبان‌ها"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد چند فایل
            for i in range(3):
                with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                    f.write('a' * 1024)  # 1KB

            stats = backup_service.get_backup_statistics()
            assert stats['total'] == 3
            assert stats['total_size_kb'] >= 3
            assert stats['avg_size_kb'] >= 1
            assert stats['auto_count'] == 0
            assert stats['manual_count'] == 3
            assert stats['newest'] is not None
            assert stats['oldest'] is not None

    def test_get_backup_statistics_empty(self, backup_service):
        """تست دریافت آمار پشتیبان‌ها در صورت خالی بودن"""
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=[]):
                stats = backup_service.get_backup_statistics()
                assert stats['total'] == 0
                assert stats['total_size_kb'] == 0
                assert stats['avg_size_kb'] == 0
                assert stats['oldest'] is None
                assert stats['newest'] is None

    # ============================================================
    # تست‌های get_backup_size_limit_status
    # ============================================================

    def test_get_backup_size_limit_status_normal(self, backup_service, temp_backup_dir):
        """تست دریافت وضعیت محدودیت حجم در حالت عادی"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد یک فایل کوچک
            with open(os.path.join(temp_backup_dir, 'backup.db'), 'w') as f:
                f.write('a' * 1024)  # 1KB

            status = backup_service.get_backup_size_limit_status()
            assert status['is_warning'] is False
            assert status['is_critical'] is False
            assert status['total_size_mb'] < 1

    def test_get_backup_size_limit_status_warning(self, backup_service, temp_backup_dir):
        """تست دریافت وضعیت محدودیت حجم در حالت هشدار"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            with patch('os.path.getsize', return_value=1024 * 1024 * 1024):  # 1GB
                status = backup_service.get_backup_size_limit_status()
                assert status['is_warning'] is True
                assert status['is_critical'] is False

    # ============================================================
    # تست‌های get_backup_files_paginated
    # ============================================================

    def test_get_backup_files_paginated(self, backup_service, temp_backup_dir):
        """تست دریافت لیست پشتیبان‌ها با صفحه‌بندی"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد ۱۰ فایل
            for i in range(10):
                with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                    f.write('test')

            result = backup_service.get_backup_files_paginated(page=1, per_page=3)
            assert result['total'] == 10
            assert len(result['items']) == 3
            assert result['page'] == 1
            assert result['per_page'] == 3
            assert result['total_pages'] == 4

    def test_get_backup_files_paginated_empty(self, backup_service):
        """تست دریافت لیست پشتیبان‌ها با صفحه‌بندی در صورت خالی بودن"""
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=[]):
                result = backup_service.get_backup_files_paginated()
                assert result['total'] == 0
                assert len(result['items']) == 0
                assert result['total_pages'] == 0

    # ============================================================
    # تست‌های get_backup_file_count و get_total_backup_size
    # ============================================================

    def test_get_backup_file_count(self, backup_service, temp_backup_dir):
        """تست تعداد فایل‌های پشتیبان"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            for i in range(5):
                with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                    f.write('test')

            count = backup_service.get_backup_file_count()
            assert count == 5

    def test_get_total_backup_size(self, backup_service, temp_backup_dir):
        """تست مجموع حجم پشتیبان‌ها"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            for i in range(3):
                with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                    f.write('a' * 1024)  # 1KB

            total_size = backup_service.get_total_backup_size()
            assert total_size >= 3072

    # ============================================================
    # تست‌های get_backup_files_by_date
    # ============================================================

    def test_get_backup_files_by_date(self, backup_service, temp_backup_dir):
        """تست دریافت پشتیبان‌های بر اساس تاریخ"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد فایل‌ها با زمان‌های مختلف
            for i in range(3):
                with open(os.path.join(temp_backup_dir, f'backup_{i}.db'), 'w') as f:
                    f.write('test')
                # تنظیم زمان اصلاح
                days_ago = i * 10
                os.utime(os.path.join(temp_backup_dir, f'backup_{i}.db'), 
                         (datetime.now().timestamp() - days_ago * 86400,
                          datetime.now().timestamp() - days_ago * 86400))

            files = backup_service.get_backup_files_by_date(days=15)
            # باید ۲ فایل (0 و 1) برگردد
            assert len(files) == 2

    # ============================================================
    # تست‌های get_backup_files_by_pattern
    # ============================================================

    def test_get_backup_files_by_pattern(self, backup_service, temp_backup_dir):
        """تست دریافت پشتیبان‌ها بر اساس الگوی نام"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد فایل‌ها با پیشوندهای مختلف
            with open(os.path.join(temp_backup_dir, 'auto_backup_1.db'), 'w') as f:
                f.write('test')
            with open(os.path.join(temp_backup_dir, 'auto_backup_2.db'), 'w') as f:
                f.write('test')
            with open(os.path.join(temp_backup_dir, 'manual_backup.db'), 'w') as f:
                f.write('test')

            files = backup_service.get_backup_files_by_pattern('auto_backup')
            assert len(files) == 2

            files = backup_service.get_backup_files_by_pattern('manual')
            assert len(files) == 1

    # ============================================================
    # تست‌های is_backup_directory_writable
    # ============================================================

    def test_is_backup_directory_writable_true(self, backup_service, temp_backup_dir):
        """تست بررسی قابلیت نوشتن در پوشه پشتیبان (True)"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            with patch.object(backup_service, '_ensure_backup_dir'):
                with patch('builtins.open', mock_open()):
                    with patch('os.remove'):
                        result = backup_service.is_backup_directory_writable()
                        assert result is True

    def test_is_backup_directory_writable_false(self, backup_service):
        """تست بررسی قابلیت نوشتن در پوشه پشتیبان (False)"""
        with patch.object(backup_service, '_ensure_backup_dir', side_effect=OSError('Permission denied')):
            result = backup_service.is_backup_directory_writable()
            assert result is False

    # ============================================================
    # تست‌های get_backup_directory_info
    # ============================================================

    def test_get_backup_directory_info_exists(self, backup_service, temp_backup_dir):
        """تست دریافت اطلاعات پوشه پشتیبان (وجود دارد)"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            with patch('os.path.exists', return_value=True):
                with patch.object(backup_service, 'is_backup_directory_writable', return_value=True):
                    info = backup_service.get_backup_directory_info()
                    assert info['exists'] is True
                    assert info['is_writable'] is True
                    assert info['path'] == temp_backup_dir
                    assert info['max_files'] == backup_service._max_backup_files

    def test_get_backup_directory_info_not_exists(self, backup_service):
        """تست دریافت اطلاعات پوشه پشتیبان (وجود ندارد)"""
        with patch('os.path.exists', return_value=False):
            info = backup_service.get_backup_directory_info()
            assert info['exists'] is False
            assert info['is_writable'] is False

    # ============================================================
    # تست‌های auto_backup و pre_restore_backup
    # ============================================================

    def test_auto_backup(self, backup_service):
        """تست ایجاد پشتیبان خودکار"""
        with patch.object(backup_service, 'create_backup', return_value={'name': 'auto_backup.db'}) as mock_create:
            result = backup_service.auto_backup()
            mock_create.assert_called_once_with('auto_backup', auto_cleanup=True)
            assert result == {'name': 'auto_backup.db'}

    def test_pre_restore_backup(self, backup_service):
        """تست ایجاد پشتیبان قبل از بازیابی"""
        with patch.object(backup_service, 'create_backup', return_value={'name': 'pre_restore.db'}) as mock_create:
            result = backup_service.pre_restore_backup()
            mock_create.assert_called_once_with('pre_restore', auto_cleanup=False)
            assert result == {'name': 'pre_restore.db'}

    # ============================================================
    # تست‌های cleanup_old_auto_backups
    # ============================================================

    def test_cleanup_old_auto_backups(self, backup_service, temp_backup_dir):
        """تست پاکسازی پشتیبان‌های خودکار قدیمی"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            # ایجاد فایل‌های خودکار
            for i in range(7):
                with open(os.path.join(temp_backup_dir, f'auto_backup_{i}.db'), 'w') as f:
                    f.write('test')
                # تنظیم زمان اصلاح
                os.utime(os.path.join(temp_backup_dir, f'auto_backup_{i}.db'), (i, i))

            deleted = backup_service.cleanup_old_auto_backups(keep_count=3)
            assert deleted == 4

            # فقط ۳ فایل باید باقی بمانند
            files = os.listdir(temp_backup_dir)
            assert len(files) == 3

    def test_cleanup_old_auto_backups_under_limit(self, backup_service, temp_backup_dir):
        """تست پاکسازی پشتیبان‌های خودکار وقتی کمتر از حد مجاز است"""
        with patch.object(backup_service, '_backup_dir', temp_backup_dir):
            for i in range(2):
                with open(os.path.join(temp_backup_dir, f'auto_backup_{i}.db'), 'w') as f:
                    f.write('test')

            deleted = backup_service.cleanup_old_auto_backups(keep_count=5)
            assert deleted == 0
            assert len(os.listdir(temp_backup_dir)) == 2

    # ============================================================
    # تست‌های error handling
    # ============================================================

    def test_restore_backup_copy_error(self, backup_service, temp_backup_dir):
        """تست بازیابی با خطا در کپی فایل"""
        with patch.object(backup_service, 'get_backup_by_name', return_value={'name': 'backup.db', 'path': '/path/to/backup.db'}):
            with patch.object(backup_service, '_validate_database_file', return_value=(True, 'valid')):
                with patch('shutil.copy2', side_effect=OSError('Permission denied')):
                    result = backup_service.restore_backup('backup.db')
                    assert result is False

    def test_restore_from_file_copy_error(self, backup_service, temp_backup_dir):
        """تست بازیابی از فایل با خطا در کپی"""
        with patch.object(backup_service, '_validate_database_file', return_value=(True, 'valid')):
            with patch('shutil.copy2', side_effect=OSError('Permission denied')):
                result = backup_service.restore_from_file('/path/to/file.db')
                assert result is False

    def test_get_backup_files_os_error(self, backup_service):
        """تست دریافت لیست پشتیبان‌ها با خطای سیستمی"""
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', side_effect=OSError('Permission denied')):
                # نباید استثنا پرتاب کند
                files = backup_service._get_backup_files()
                assert files == []

    def test_cleanup_old_backups_os_error(self, backup_service):
        """تست پاکسازی پشتیبان‌ها با خطای سیستمی"""
        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['backup1.db']):
                with patch('os.remove', side_effect=OSError('Permission denied')):
                    # نباید استثنا پرتاب کند
                    deleted = backup_service._cleanup_old_backups()
                    assert deleted == 0