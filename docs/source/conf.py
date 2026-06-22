# docs/source/conf.py
# پیکربندی Sphinx برای مستندسازی پروژه ربات (نسخه پایدار با مدیریت خطا)

import os
import sys
from datetime import datetime

# ============================================================
# مسیرهای پروژه
# ============================================================

sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../admin_panel'))
sys.path.insert(0, os.path.abspath('../../services'))
sys.path.insert(0, os.path.abspath('../../repositories'))
sys.path.insert(0, os.path.abspath('../../database'))
sys.path.insert(0, os.path.abspath('../../utils'))
sys.path.insert(0, os.path.abspath('../../handlers'))
sys.path.insert(0, os.path.abspath('../../dynamic'))
sys.path.insert(0, os.path.abspath('../../models'))
sys.path.insert(0, os.path.abspath('../../dto'))
sys.path.insert(0, os.path.abspath('../../keyboards'))

# تنظیم متغیرهای محیطی برای مستندسازی
os.environ.setdefault('DATABASE_TYPE', 'sqlite')
os.environ.setdefault('SQLITE_DB_PATH', ':memory:')
os.environ.setdefault('REDIS_ENABLED', 'false')
os.environ.setdefault('RATE_LIMIT_ENABLED', 'false')
os.environ.setdefault('BOT_TOKEN', 'DOCS_TOKEN')
os.environ.setdefault('OWNER_ID', '0')

# ============================================================
# اطلاعات پروژه
# ============================================================

project = 'ربات خدمات آنلاین (Bale Bot)'
copyright = f'{datetime.now().year}, تیم توسعه'
author = 'تیم توسعه'

try:
    from config import config
    version = release = getattr(config, 'VERSION', '1.0.0')
except:
    version = release = '1.0.0'

# ============================================================
# تنظیمات عمومی Sphinx (فقط افزونه‌های اصلی)
# ============================================================

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    # 'sphinx.ext.coverage',     # اختیاری
    # 'sphinx.ext.intersphinx',  # در صورت نیاز
]

# ============================================================
# تنظیمات Theme
# ============================================================

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
}

# ============================================================
# تنظیمات خروجی HTML
# ============================================================

html_title = f"{project} v{version}"
html_short_title = "ربات بله"
html_static_path = ['_static']
html_show_sourcelink = True
html_show_copyright = True
html_show_sphinx = True

# ============================================================
# تنظیمات autodoc و napoleon
# ============================================================

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
}

napoleon_google_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

# ============================================================
# تنظیمات زبان و تاریخ (با مدیریت خطا)
# ============================================================

language = 'fa'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'venv', 'env', '__pycache__']
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# ============================================================
# مدیریت import pytz (اختیاری)
# ============================================================

try:
    import pytz
except ImportError:
    pytz = None  # در صورت نبود pytz، خطا نمی‌دهد

# ============================================================
# تنظیمات لاگ
# ============================================================

import logging
logging.basicConfig(level=logging.INFO)