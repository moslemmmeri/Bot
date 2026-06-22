# ```markdown

# \# راهنمای نصب و راه‌اندازی ربات

# 

# \## 📌 پیش‌نیازها

# 

# قبل از شروع، مطمئن شوید که موارد زیر روی سیستم شما نصب شده است:

# 

# | پیش‌نیاز | نسخه حداقل | توضیح |

# |---------|-----------|-------|

# | \*\*Python\*\* | 3.9+ | زبان برنامه‌نویسی اصلی |

# | \*\*pip\*\* | 20.0+ | مدیریت پکیج‌های Python |

# | \*\*Git\*\* | 2.0+ | (اختیاری) برای clone کردن مخزن |

# | \*\*Redis\*\* | 6.0+ | (اختیاری) برای کش و Rate Limiting |

# | \*\*PostgreSQL / MySQL\*\* | - | (اختیاری) برای محیط تولید |

# 

# \---

# 

# \## 🚀 مراحل نصب

# 

# \### ۱. دریافت کد پروژه

# 

# \*\*روش ۱: Clone از Git\*\*

# ```bash

# git clone https://github.com/your-username/your-bot.git

# cd your-bot

# ```

# 

# \*\*روش ۲: دانلود مستقیم\*\*

# 1\. فایل Zip پروژه را دانلود کنید

# 2\. آن را در پوشه‌ی مورد نظر استخراج کنید

# 3\. وارد پوشه‌ی پروژه شوید:

# ```bash

# cd /path/to/your-bot

# ```

# 

# \---

# 

# \### ۲. ایجاد محیط مجازی (Virtual Environment)

# 

# توصیه می‌شود از یک محیط مجازی برای ایزوله کردن وابستگی‌ها استفاده کنید:

# 

# \*\*Windows:\*\*

# ```bash

# python -m venv venv

# venv\\Scripts\\activate

# ```

# 

# \*\*Linux/Mac:\*\*

# ```bash

# python3 -m venv venv

# source venv/bin/activate

# ```

# 

# \---

# 

# \### ۳. نصب وابستگی‌ها

# 

# \*\*نصب وابستگی‌های اصلی:\*\*

# ```bash

# pip install -r requirements.txt

# ```

# 

# \*\*اگر فایل requirements.txt وجود ندارد، به‌صورت دستی نصب کنید:\*\*

# ```bash

# pip install aiohttp python-dotenv APScheduler redis openpyxl matplotlib

# ```

# 

# \---

# 

# \### ۴. تنظیم متغیرهای محیطی

# 

# یک فایل `.env` در ریشه‌ی پروژه ایجاد کنید:

# 

# ```bash

# cp .env.example .env   # اگر فایل نمونه وجود دارد

# \# یا

# touch .env

# ```

# 

# فایل `.env` را با اطلاعات خود ویرایش کنید:

# 

# ```env

# \# تنظیمات اصلی

# BOT\_TOKEN=128512944:gh4ep\_rAkuEzSveBaLBSN3o1zLiIdDBWr5w

# OWNER\_ID=1332804468

# PAYMENT\_PROVIDER\_TOKEN=WALLET-TEST-1111111111111111

# 

# \# تنظیمات دیتابیس

# DATABASE\_TYPE=sqlite

# SQLITE\_DB\_PATH=bot\_config.db

# 

# \# تنظیمات Redis (اختیاری)

# REDIS\_ENABLED=false

# REDIS\_HOST=localhost

# REDIS\_PORT=6379

# REDIS\_DB=0

# 

# \# تنظیمات Rate Limiting

# RATE\_LIMIT\_ENABLED=true

# RATE\_LIMIT\_PER\_MINUTE=30

# ```

# 

# > \*\*⚠️ نکته امنیتی:\*\* هرگز فایل `.env` را در مخزن Git قرار ندهید. آن را به `.gitignore` اضافه کنید.

# 

# \---

# 

# \### ۵. ایجاد و مقداردهی دیتابیس

# 

# دیتابیس به‌صورت خودکار هنگام اولین اجرای ربات ایجاد می‌شود. اما اگر می‌خواهید دستی ایجاد کنید:

# 

# ```bash

# python -c "from database import init\_db; init\_db()"

# ```

# 

# برای اعمال مهاجرت‌های دیتابیس:

# ```bash

# python -c "from database.db\_migrations import migrate\_to\_latest; migrate\_to\_latest()"

# ```

# 

# \---

# 

# \### ۶. اجرای ربات

# 

# \*\*اجرای عادی:\*\*

# ```bash

# python bot.py

# ```

# 

# \*\*اجرا با لاگ‌گیری در فایل:\*\*

# ```bash

# python bot.py >> bot.log 2>\&1

# ```

# 

# \*\*اجرا در پس‌زمینه (Linux/Mac):\*\*

# ```bash

# nohup python bot.py > bot.log 2>\&1 \&

# ```

# 

# \---

# 

# \### ۷. راه‌اندازی تسک‌های زمان‌بندی‌شده (اختیاری)

# 

# اگر از تسک‌های زمان‌بندی‌شده (پشتیبان‌گیری خودکار، یادآوری، پاکسازی) استفاده می‌کنید، باید Scheduler را فعال کنید.

# 

# در فایل `bot.py`، مطمئن شوید که سطر زیر وجود دارد:

# 

# ```python

# from scheduler import init\_scheduler

# init\_scheduler()

# ```

# 

# \---

# 

# \## 🐳 نصب با Docker

# 

# \### ۱. ساخت Dockerfile

# 

# یک فایل `Dockerfile` در ریشه‌ی پروژه ایجاد کنید:

# 

# ```dockerfile

# FROM python:3.10-slim

# 

# WORKDIR /app

# 

# COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt

# 

# COPY . .

# 

# CMD \["python", "bot.py"]

# ```

# 

# \### ۲. ساخت و اجرا

# 

# ```bash

# \# ساختイメージ

# docker build -t my-bot .

# 

# \# اجرا

# docker run -d --name my-bot --env-file .env my-bot

# ```

# 

# \### ۳. استفاده از Docker Compose (با Redis و PostgreSQL)

# 

# فایل `docker-compose.yml`:

# 

# ```yaml

# version: '3.8'

# 

# services:

# &#x20; bot:

# &#x20;   build: .

# &#x20;   env\_file:

# &#x20;     - .env

# &#x20;   depends\_on:

# &#x20;     - redis

# &#x20;     - postgres

# &#x20;   restart: always

# 

# &#x20; redis:

# &#x20;   image: redis:7-alpine

# &#x20;   ports:

# &#x20;     - "6379:6379"

# &#x20;   restart: always

# 

# &#x20; postgres:

# &#x20;   image: postgres:15-alpine

# &#x20;   environment:

# &#x20;     POSTGRES\_DB: bot\_db

# &#x20;     POSTGRES\_USER: bot\_user

# &#x20;     POSTGRES\_PASSWORD: your\_password

# &#x20;   ports:

# &#x20;     - "5432:5432"

# &#x20;   volumes:

# &#x20;     - postgres\_data:/var/lib/postgresql/data

# &#x20;   restart: always

# 

# volumes:

# &#x20; postgres\_data:

# ```

# 

# اجرا:

# ```bash

# docker-compose up -d

# ```

# 

# \---

# 

# \## 🛠️ عیب‌یابی (Troubleshooting)

# 

# \### خطا: `ModuleNotFoundError`

# 

# \*\*راه‌حل:\*\* وابستگی‌های از دست رفته را نصب کنید:

# 

# ```bash

# pip install -r requirements.txt

# ```

# 

# \### خطا: `sqlite3.OperationalError: unable to open database file`

# 

# \*\*راه‌حل:\*\* مطمئن شوید که پوشه‌ی دیتابیس وجود دارد و دسترسی نوشتن دارد:

# 

# ```bash

# chmod 755 .

# ```

# 

# \### خطا: `Connection refused` برای Redis

# 

# \*\*راه‌حل:\*\* Redis را نصب و راه‌اندازی کنید یا `REDIS\_ENABLED=false` را در `.env` تنظیم کنید.

# 

# \### خطا: `BOT\_TOKEN is not set`

# 

# \*\*راه‌حل:\*\* مطمئن شوید که `BOT\_TOKEN` در فایل `.env` به‌درستی تنظیم شده است.

# 

# \### ربات پاسخ نمی‌دهد

# 

# \*\*راه‌حل:\*\*

# 1\. لاگ‌ها را بررسی کنید:

# &#x20;  ```bash

# &#x20;  tail -f bot.log

# &#x20;  ```

# 2\. اطمینان از اتصال به اینترنت

# 3\. بررسی کنید که توکن ربات معتبر است

# 

# \---

# 

# \## 📝 تنظیمات پیشرفته

# 

# \### ۱. استفاده از PostgreSQL

# 

# `.env` را به‌روزرسانی کنید:

# 

# ```env

# DATABASE\_TYPE=postgresql

# POSTGRES\_HOST=localhost

# POSTGRES\_PORT=5432

# POSTGRES\_DB=bot\_db

# POSTGRES\_USER=bot\_user

# POSTGRES\_PASSWORD=your\_password

# ```

# 

# \### ۲. فعال‌سازی کش Redis

# 

# ```env

# REDIS\_ENABLED=true

# REDIS\_HOST=localhost

# REDIS\_PORT=6379

# REDIS\_DB=0

# REDIS\_PASSWORD=

# REDIS\_CACHE\_TTL=300

# ```

# 

# \### ۳. تغییر زمان پشتیبان‌گیری خودکار

# 

# ```env

# BACKUP\_SCHEDULE=0 3 \* \* \*   # هر روز ساعت ۳ بامداد

# ```

# 

# \### ۴. تنظیم Rate Limit

# 

# ```env

# RATE\_LIMIT\_ENABLED=true

# RATE\_LIMIT\_PER\_MINUTE=30

# ```

# 

# \---

# 

# \## 📂 ساختار پوشه‌ها پس از نصب

# 

# ```

# your-bot/

# ├── bot.py

# ├── config.py

# ├── core.py

# ├── .env

# ├── requirements.txt

# ├── bot\_config.db          (دیتابیس)

# ├── bot.log                (لاگ)

# ├── backups/               (پشتیبان‌ها)

# ├── admin\_panel/

# ├── database/

# ├── dynamic/

# ├── handlers/

# ├── keyboards/

# ├── models/

# ├── repositories/

# ├── services/

# ├── dto/

# └── ...

# ```

# 

# \---

# 

# \## ✅ بررسی نصب موفق

# 

# برای اطمینان از نصب صحیح، مراحل زیر را دنبال کنید:

# 

# 1\. ربات را اجرا کنید:

# &#x20;  ```bash

# &#x20;  python bot.py

# &#x20;  ```

# 2\. یک پیام `/start` به ربات در بله ارسال کنید

# 3\. اگر پیام خوش‌آمدگویی دریافت کردید، نصب موفق بوده است

# 

# \---

# 

# \## 📌 پشتیبانی

# 

# \- \*\*مستندات کامل:\*\* فایل `docs/architecture.md` را مطالعه کنید

# \- \*\*گزارش خطا:\*\* لطفاً خطاها را در بخش Issues گزارش دهید

# \- \*\*ارتباط با توسعه‌دهنده:\*\* از طریق `OWNER\_ID` تعریف‌شده در فایل `.env`

# 

# \---

# 

# \*\*📅 آخرین بروزرسانی:\*\* ۱۴۰۳/۰۱/۱۵

# ```

