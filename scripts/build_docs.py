#!/usr/bin/env python3
# scripts/build_docs.py
# اسکریپت ساخت خودکار مستندات با Sphinx

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# ============================================================
# تنظیمات
# ============================================================

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / 'docs'
SOURCE_DIR = DOCS_DIR / 'source'
BUILD_DIR = DOCS_DIR / 'build'
REQUIREMENTS_FILE = DOCS_DIR / 'requirements.txt'

def print_header(message: str):
    """چاپ هدر"""
    print("=" * 60)
    print(f"📚 {message}")
    print("=" * 60)

def print_step(message: str):
    """چاپ مرحله"""
    print(f"  🔹 {message}")

def run_command(cmd: list, cwd: Path = None) -> bool:
    """اجرای دستور و بازگشت نتیجه"""
    try:
        result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ خطا در اجرای دستور: {' '.join(cmd)}")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False

# ============================================================
# توابع اصلی
# ============================================================

def install_requirements():
    """نصب وابستگی‌های مستندسازی"""
    print_step("نصب وابستگی‌های مستندسازی...")
    return run_command(['pip', 'install', '-r', str(REQUIREMENTS_FILE)])

def clean_build():
    """پاکسازی خروجی‌های قبلی"""
    print_step("پاکسازی خروجی‌های قبلی...")
    if BUILD_DIR.exists():
        import shutil
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    return True

def generate_api_docs():
    """تولید مستندات API با autoapi"""
    print_step("تولید مستندات API...")
    # autoapi به‌صورت خودکار توسط Sphinx انجام می‌شود
    return True

def build_html():
    """ساخت خروجی HTML"""
    print_step("ساخت خروجی HTML...")
    return run_command(
        ['sphinx-build', '-b', 'html', str(SOURCE_DIR), str(BUILD_DIR / 'html')],
        cwd=DOCS_DIR
    )

def build_pdf():
    """ساخت خروجی PDF"""
    print_step("ساخت خروجی PDF...")
    return run_command(
        ['sphinx-build', '-b', 'latex', str(SOURCE_DIR), str(BUILD_DIR / 'latex')],
        cwd=DOCS_DIR
    )

def build_all():
    """ساخت همه خروجی‌ها"""
    print_step("ساخت همه خروجی‌ها...")
    return build_html() and build_pdf()

def open_docs():
    """باز کردن مستندات در مرورگر"""
    print_step("باز کردن مستندات در مرورگر...")
    html_path = BUILD_DIR / 'html' / 'index.html'
    if html_path.exists():
        import webbrowser
        webbrowser.open(str(html_path))
        return True
    print("❌ فایل index.html یافت نشد")
    return False

def get_stats():
    """دریافت آمار مستندات"""
    print_step("دریافت آمار مستندات...")
    html_dir = BUILD_DIR / 'html'
    if not html_dir.exists():
        print("❌ خروجی HTML یافت نشد")
        return

    # شمارش فایل‌ها
    html_files = list(html_dir.rglob('*.html'))
    print(f"📄 تعداد صفحات HTML: {len(html_files)}")

    # حجم کل
    total_size = sum(f.stat().st_size for f in html_files)
    print(f"📊 حجم کل: {total_size / 1024 / 1024:.2f} MB")

# ============================================================
# ورودی اصلی
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='ساخت مستندات پروژه')
    parser.add_argument('--install', action='store_true', help='نصب وابستگی‌ها')
    parser.add_argument('--clean', action='store_true', help='پاکسازی خروجی‌ها')
    parser.add_argument('--html', action='store_true', help='ساخت فقط HTML')
    parser.add_argument('--pdf', action='store_true', help='ساخت فقط PDF')
    parser.add_argument('--all', action='store_true', help='ساخت همه خروجی‌ها')
    parser.add_argument('--open', action='store_true', help='باز کردن مستندات در مرورگر')
    parser.add_argument('--stats', action='store_true', help='نمایش آمار مستندات')
    parser.add_argument('--watch', action='store_true', help='حالت نظارت (Live Reload)')

    args = parser.parse_args()

    print_header("ساخت مستندات پروژه")

    # اگر هیچ آرگومانی داده نشده، همه کارها را انجام بده
    if not any(vars(args).values()):
        args.install = True
        args.clean = True
        args.all = True

    # نصب وابستگی‌ها
    if args.install:
        if not install_requirements():
            sys.exit(1)

    # پاکسازی
    if args.clean:
        if not clean_build():
            sys.exit(1)

    # ساخت HTML
    if args.html:
        if not build_html():
            sys.exit(1)

    # ساخت PDF
    if args.pdf:
        if not build_pdf():
            sys.exit(1)

    # ساخت همه
    if args.all:
        if not build_all():
            sys.exit(1)

    # باز کردن در مرورگر
    if args.open:
        open_docs()

    # نمایش آمار
    if args.stats:
        get_stats()

    # حالت نظارت (با sphinx-autobuild)
    if args.watch:
        print_step("حالت نظارت (Live Reload)...")
        run_command([
            'sphinx-autobuild',
            '-b', 'html',
            str(SOURCE_DIR),
            str(BUILD_DIR / 'html')
        ], cwd=DOCS_DIR)

    print_header("✅ ساخت مستندات تکمیل شد")

if __name__ == "__main__":
    main()