# ```markdown

# \# مستندات ساختار دیتابیس (Database Schema)

# 

# \## 📌 معرفی کلی

# 

# دیتابیس ربات با استفاده از \*\*SQLite\*\* به‌عنوان دیتابیس پیش‌فرض طراحی شده است، اما با قابلیت مهاجرت به \*\*PostgreSQL\*\* و \*\*MySQL\*\* نیز سازگار است.  

# دیتابیس شامل ۱۵ جدول اصلی است که اطلاعات کاربران، دکمه‌ها، سوالات، سفارشات، آمار و تنظیمات را ذخیره می‌کنند.

# 

# \---

# 

# \## 🗄️ دیاگرام ER (Entity-Relationship)

# 

# ```

# ┌─────────────┐     ┌─────────────┐     ┌─────────────┐

# │   admins    │     │   users     │     │   categories│

# ├─────────────┤     ├─────────────┤     ├─────────────┤

# │ user\_id (PK)│◄────│ user\_id (PK)│     │ id (PK)     │

# │ role        │     │ username    │     │ name        │

# │ is\_active   │     │ first\_name  │     │ icon        │

# │ added\_at    │     │ last\_name   │     │ location    │

# └─────────────┘     │ first\_seen  │     │ sort\_order  │

# &#x20;                   │ last\_active │     │ is\_active   │

# &#x20;                   │ is\_blocked  │     │ columns     │

# &#x20;                   │ block\_reason│     │ created\_at  │

# &#x20;                   │ blocked\_at  │     └─────────────┘

# &#x20;                   │ language    │            │

# &#x20;                   │ timezone    │            │

# &#x20;                   │ extra\_data  │            │

# &#x20;                   └─────────────┘            │

# &#x20;                          │                   │

# &#x20;                          │                   │

# &#x20;                   ┌──────▼──────┐     ┌──────▼──────┐

# &#x20;                   │user\_answers │     │   buttons   │

# &#x20;                   ├─────────────┤     ├─────────────┤

# &#x20;                   │ id (PK)     │     │ id (PK)     │

# &#x20;                   │ user\_id (FK)│     │ category\_id │

# &#x20;                   │ button\_id   │     │ parent\_id   │

# &#x20;                   │ question\_id │     │ name        │

# &#x20;                   │ answer      │     │ icon        │

# &#x20;                   │ submitted\_at│     │ callback\_data│

# &#x20;                   └─────────────┘     │ has\_submenu │

# &#x20;                          │            │ has\_payment │

# &#x20;                          │            │ price\_amount│

# &#x20;                   ┌──────▼──────┐     │ price\_label │

# &#x20;                   │question\_    │     │ sort\_order  │

# &#x20;                   │options      │     │ is\_active   │

# &#x20;                   ├─────────────┤     │ columns     │

# &#x20;                   │ id (PK)     │     │ created\_at  │

# &#x20;                   │ question\_id │     └─────────────┘

# &#x20;                   │ option\_text │            │

# &#x20;                   │ callback\_dat│            │

# &#x20;                   │ sort\_order  │            │

# &#x20;                   │ is\_active   │            │

# &#x20;                   └─────────────┘            │

# &#x20;                          │                   │

# &#x20;                   ┌──────▼──────┐            │

# &#x20;                   │ questions   │            │

# &#x20;                   ├─────────────┤            │

# &#x20;                   │ id (PK)     │            │

# &#x20;                   │ button\_id   │◄───────────┘

# &#x20;                   │ question\_tex│

# &#x20;                   │ question\_typ│

# &#x20;                   │ validation  │

# &#x20;                   │ error\_msg   │

# &#x20;                   │ needs\_btn   │

# &#x20;                   │ array\_name  │

# &#x20;                   │ sort\_order  │

# &#x20;                   │ is\_active   │

# &#x20;                   │ is\_required │

# &#x20;                   │ validation\_\*│ (بیش از ۳۰ فیلد)

# &#x20;                   │ created\_at  │

# &#x20;                   └─────────────┘

# &#x20;                          │

# &#x20;                   ┌──────▼──────┐

# &#x20;                   │question\_    │

# &#x20;                   │conditions   │

# &#x20;                   ├─────────────┤

# &#x20;                   │ id (PK)     │

# &#x20;                   │ question\_id │

# &#x20;                   │ condition\_  │

# &#x20;                   │ question\_id │

# &#x20;                   │ operator    │

# &#x20;                   │ value       │

# &#x20;                   │ logic\_op    │

# &#x20;                   │ sort\_order  │

# &#x20;                   │ is\_active   │

# &#x20;                   └─────────────┘

# 

# 

# ┌─────────────┐     ┌─────────────┐     ┌─────────────┐

# │dynamic\_     │     │ button\_stats│     │ button\_     │

# │orders       │     │             │     │ versions    │

# ├─────────────┤     ├─────────────┤     ├─────────────┤

# │ id (PK)     │     │ id (PK)     │     │ id (PK)     │

# │ user\_id (FK)│     │ button\_id   │     │ button\_id   │

# │ button\_id   │     │ user\_id     │     │ version\_num │

# │ order\_data  │     │ action\_type │     │ snapshot    │

# │ payment\_amt │     │ amount      │     │ created\_by  │

# │ tracking\_cod│     │ created\_at  │     │ note        │

# │ status      │     └─────────────┘     │ created\_at  │

# │ admin\_note  │                         └─────────────┘

# │ status\_hist │

# │ created\_at  │

# └─────────────┘

# 

# 

# ┌─────────────┐     ┌─────────────┐     ┌─────────────┐

# │ order\_logs  │     │ error\_logs  │     │ settings    │

# ├─────────────┤     ├─────────────┤     ├─────────────┤

# │ id (PK)     │     │ id (PK)     │     │ key (PK)    │

# │ order\_id    │     │ error\_type  │     │ value       │

# │ user\_id     │     │ error\_msg   │     │ description │

# │ action      │     │ traceback   │     │ updated\_at  │

# │ old\_value   │     │ user\_id     │     └─────────────┘

# │ new\_value   │     │ chat\_id     │

# │ note        │     │ data        │

# │ created\_at  │     │ is\_resolved │

# └─────────────┘     │ resolved\_at │

# &#x20;                   │ resolved\_by │

# &#x20;                   │ created\_at  │

# &#x20;                   └─────────────┘

# ```

# 

# \---

# 

# \## 📋 شرح جداول

# 

# \### 1. جدول `users` (کاربران)

# 

# \*\*توضیح:\*\* ذخیره‌سازی اطلاعات کاربران ربات.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `user\_id` | INTEGER (PK) | شناسه کاربر از بله |

# | `username` | TEXT | نام کاربری |

# | `first\_name` | TEXT | نام |

# | `last\_name` | TEXT | نام خانوادگی |

# | `first\_seen` | TEXT (DATETIME) | اولین فعالیت |

# | `last\_active` | TEXT (DATETIME) | آخرین فعالیت |

# | `is\_blocked` | INTEGER (0/1) | وضعیت مسدودیت |

# | `block\_reason` | TEXT | دلیل مسدودیت |

# | `blocked\_at` | TEXT (DATETIME) | زمان مسدودیت |

# | `role` | INTEGER | نقش کاربر (0=کاربر عادی، 1=ادمین، 2=مدیر، 3=ناظر، 10=مالک) |

# | `status` | INTEGER | وضعیت (0=فعال، 1=مسدود، 2=حذف) |

# | `language` | TEXT | زبان (پیش‌فرض: fa) |

# | `timezone` | TEXT | منطقه زمانی (پیش‌فرض: Asia/Tehran) |

# | `extra\_data` | TEXT (JSON) | داده‌های اضافی |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_users\_last\_active` روی `last\_active`

# \- `idx\_users\_username` روی `username`

# 

# \---

# 

# \### 2. جدول `admins` (ادمین‌ها)

# 

# \*\*توضیح:\*\* لیست ادمین‌ها و نقش‌های آنها.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `user\_id` | INTEGER (PK) | شناسه کاربر (ارجاع به users) |

# | `role` | TEXT | نقش (owner, admin, manager, observer) |

# | `is\_active` | INTEGER (0/1) | وضعیت فعال/غیرفعال |

# | `added\_at` | TEXT (DATETIME) | زمان افزودن |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_admins\_user\_id` روی `user\_id`

# \- `idx\_admins\_is\_active\_role` روی `is\_active, role`

# 

# \---

# 

# \### 3. جدول `categories` (دسته‌بندی‌ها)

# 

# \*\*توضیح:\*\* دسته‌بندی‌های منوهای اصلی (منوی اصلی، منوی بیشتر، دیگر خدمات).

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه دسته‌بندی |

# | `name` | TEXT | نام دسته‌بندی |

# | `icon` | TEXT | آیکون (پیش‌فرض: 📁) |

# | `location` | TEXT | مکان (main, more, other) |

# | `sort\_order` | INTEGER | ترتیب نمایش |

# | `is\_active` | INTEGER (0/1) | وضعیت فعال/غیرفعال |

# | `columns` | INTEGER | تعداد ستون‌های پیش‌فرض (۱ تا ۸) |

# | `created\_at` | TEXT (DATETIME) | زمان ایجاد |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_categories\_location` روی `location`

# \- `idx\_categories\_is\_active` روی `is\_active`

# 

# \---

# 

# \### 4. جدول `buttons` (دکمه‌ها)

# 

# \*\*توضیح:\*\* دکمه‌های منو و سرویس‌ها.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه دکمه |

# | `category\_id` | INTEGER (FK) | شناسه دسته‌بندی |

# | `parent\_button\_id` | INTEGER (FK) | شناسه دکمه والد (برای زیرمنوها) |

# | `name` | TEXT | نام دکمه |

# | `icon` | TEXT | آیکون |

# | `callback\_data` | TEXT (UNIQUE) | داده کالبک |

# | `has\_submenu` | INTEGER (0/1) | آیا زیرمنو دارد |

# | `has\_payment` | INTEGER (0/1) | آیا نیاز به پرداخت دارد |

# | `price\_amount` | INTEGER | مبلغ (ریال) |

# | `price\_label` | TEXT | برچسب مبلغ |

# | `price\_type` | TEXT | نوع قیمت (fixed, variable) |

# | `min\_price` | INTEGER | حداقل مبلغ (قیمت متغیر) |

# | `max\_price` | INTEGER | حداکثر مبلغ (قیمت متغیر) |

# | `sort\_order` | INTEGER | ترتیب نمایش |

# | `is\_active` | INTEGER (0/1) | وضعیت فعال/غیرفعال |

# | `columns` | INTEGER | تعداد ستون‌های اختصاصی (اختیاری) |

# | `created\_at` | TEXT (DATETIME) | زمان ایجاد |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_buttons\_category\_id` روی `category\_id`

# \- `idx\_buttons\_parent\_button\_id` روی `parent\_button\_id`

# \- `idx\_buttons\_callback\_data` روی `callback\_data`

# \- `idx\_buttons\_category\_active\_sort` روی `category\_id, is\_active, sort\_order`

# \- `idx\_buttons\_is\_active` روی `is\_active`

# 

# \---

# 

# \### 5. جدول `questions` (سوالات)

# 

# \*\*توضیح:\*\* سوالات هر دکمه/سرویس با قابلیت اعتبارسنجی پیشرفته.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه سوال |

# | `button\_id` | INTEGER (FK) | شناسه دکمه |

# | `question\_text` | TEXT | متن سوال |

# | `question\_type` | TEXT | نوع سوال (text, number, file, button, date, ...) |

# | `validation\_rule` | TEXT | قانون اعتبارسنجی (قدیمی) |

# | `error\_message` | TEXT | پیام خطا |

# | `needs\_button` | INTEGER (0/1) | آیا دکمه‌ای است |

# | `array\_name` | TEXT | نام آرایه (برای گروه‌بندی) |

# | `sort\_order` | INTEGER | ترتیب نمایش |

# | `is\_active` | INTEGER (0/1) | وضعیت فعال/غیرفعال |

# | `is\_required` | INTEGER (0/1) | اجباری بودن |

# | `validation\_enabled` | INTEGER (0/1) | فعال بودن اعتبارسنجی |

# | `validation\_type` | TEXT | نوع اعتبارسنجی (text, number, phone, ...) |

# | `length\_validation\_enabled` | INTEGER (0/1) | محدودیت طول |

# | `min\_length` | INTEGER | حداقل طول |

# | `max\_length` | INTEGER | حداکثر طول |

# | `word\_validation\_enabled` | INTEGER (0/1) | محدودیت کلمه |

# | `min\_words` | INTEGER | حداقل کلمه |

# | `max\_words` | INTEGER | حداکثر کلمه |

# | `numeric\_validation\_enabled` | INTEGER (0/1) | اعتبارسنجی عددی |

# | `min\_value` | INTEGER | حداقل مقدار |

# | `max\_value` | INTEGER | حداکثر مقدار |

# | `step` | INTEGER | گام عددی |

# | `date\_validation\_enabled` | INTEGER (0/1) | اعتبارسنجی تاریخ |

# | `min\_date` | TEXT | حداقل تاریخ |

# | `max\_date` | TEXT | حداکثر تاریخ |

# | `future\_only` | INTEGER (0/1) | فقط تاریخ آینده |

# | `past\_only` | INTEGER (0/1) | فقط تاریخ گذشته |

# | `weekdays\_only` | INTEGER (0/1) | فقط روزهای کاری |

# | `file\_validation\_enabled` | INTEGER (0/1) | اعتبارسنجی فایل |

# | `allowed\_formats` | TEXT | فرمت‌های مجاز (مثال: jpg,png,pdf) |

# | `max\_file\_size` | INTEGER | حداکثر حجم (KB) |

# | `min\_file\_size` | INTEGER | حداقل حجم (KB) |

# | `max\_files` | INTEGER | تعداد مجاز فایل |

# | `dimensions\_enabled` | INTEGER (0/1) | اعتبارسنجی ابعاد |

# | `required\_width` | INTEGER | عرض موردنیاز |

# | `required\_height` | INTEGER | ارتفاع موردنیاز |

# | `aspect\_ratio` | TEXT | نسبت تصویر (مثال: 1:1) |

# | `pattern\_validation\_enabled` | INTEGER (0/1) | اعتبارسنجی الگو |

# | `regex\_pattern` | TEXT | الگوی regex |

# | `starts\_with` | TEXT | شروع با |

# | `ends\_with` | TEXT | پایان با |

# | `contains\_validation\_enabled` | INTEGER (0/1) | اعتبارسنجی محتوا |

# | `contains` | TEXT | شامل |

# | `not\_contains` | TEXT | شامل نباشد |

# | `forbidden\_words` | TEXT | کلمات ممنوع (جدا شده با کاما) |

# | `required\_words` | TEXT | کلمات الزامی (جدا شده با کاما) |

# | `conditional\_enabled` | INTEGER (0/1) | شرط نمایش |

# | `conditional\_on` | INTEGER | سوال مرجع شرط |

# | `conditional\_value` | TEXT | مقدار شرط |

# | `auto\_fix\_enabled` | INTEGER (0/1) | اصلاح خودکار |

# | `validation\_error` | TEXT | پیام خطای سفارشی |

# | `validation\_hint` | TEXT | راهنمای نمایشی |

# | `created\_at` | TEXT (DATETIME) | زمان ایجاد |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_questions\_button\_id` روی `button\_id`

# \- `idx\_questions\_button\_active\_sort` روی `button\_id, is\_active, sort\_order`

# \- `idx\_questions\_is\_active` روی `is\_active`

# 

# \---

# 

# \### 6. جدول `question\_options` (گزینه‌های سوال)

# 

# \*\*توضیح:\*\* گزینه‌های سوالات دکمه‌ای.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه گزینه |

# | `question\_id` | INTEGER (FK) | شناسه سوال |

# | `option\_text` | TEXT | متن گزینه |

# | `callback\_data` | TEXT (UNIQUE) | داده کالبک |

# | `sort\_order` | INTEGER | ترتیب نمایش |

# | `is\_active` | INTEGER (0/1) | وضعیت فعال/غیرفعال |

# | `created\_at` | TEXT (DATETIME) | زمان ایجاد |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_question\_options\_question\_id` روی `question\_id`

# \- `idx\_question\_options\_callback\_data` روی `callback\_data`

# \- `idx\_question\_options\_is\_active` روی `is\_active`

# 

# \---

# 

# \### 7. جدول `question\_conditions` (شرط‌های سوال)

# 

# \*\*توضیح:\*\* شرط‌های نمایش سوالات بر اساس پاسخ سوالات قبلی.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه شرط |

# | `question\_id` | INTEGER (FK) | شناسه سوال |

# | `condition\_question\_id` | INTEGER (FK) | شناسه سوال مرجع |

# | `condition\_operator` | TEXT | عملگر (==, !=, contains, >, <, ...) |

# | `condition\_value` | TEXT | مقدار شرط |

# | `logic\_operator` | TEXT | منطق ترکیب (AND, OR) |

# | `sort\_order` | INTEGER | ترتیب نمایش |

# | `is\_active` | INTEGER (0/1) | وضعیت فعال/غیرفعال |

# | `created\_at` | TEXT (DATETIME) | زمان ایجاد |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_question\_conditions\_question\_id` روی `question\_id`

# \- `idx\_question\_conditions\_condition\_question\_id` روی `condition\_question\_id`

# 

# \---

# 

# \### 8. جدول `dynamic\_orders` (سفارشات)

# 

# \*\*توضیح:\*\* ذخیره‌ی سفارشات ثبت‌شده توسط کاربران.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه سفارش |

# | `user\_id` | INTEGER (FK) | شناسه کاربر |

# | `button\_id` | INTEGER (FK) | شناسه دکمه/سرویس |

# | `order\_data` | TEXT (JSON) | داده‌های کامل سفارش (پاسخ‌ها، فایل‌ها) |

# | `payment\_amount` | INTEGER | مبلغ پرداختی (ریال) |

# | `tracking\_code` | TEXT | کد رهگیری |

# | `status` | TEXT | وضعیت (pending, paid, completed, cancelled) |

# | `admin\_note` | TEXT | یادداشت ادمین |

# | `status\_history` | TEXT (JSON) | تاریخچه تغییرات وضعیت |

# | `last\_reminder\_sent` | TEXT (DATETIME) | زمان آخرین یادآوری |

# | `created\_at` | TEXT (DATETIME) | زمان ثبت |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_dynamic\_orders\_user\_id` روی `user\_id`

# \- `idx\_dynamic\_orders\_button\_id` روی `button\_id`

# \- `idx\_dynamic\_orders\_status` روی `status`

# \- `idx\_dynamic\_orders\_status\_created` روی `status, created\_at`

# \- `idx\_dynamic\_orders\_created\_at` روی `created\_at`

# \- `idx\_dynamic\_orders\_tracking\_code` روی `tracking\_code`

# \- `idx\_dynamic\_orders\_user\_status` روی `user\_id, status`

# \- `idx\_dynamic\_orders\_button\_status` روی `button\_id, status`

# 

# \---

# 

# \### 9. جدول `user\_answers` (پاسخ‌های کاربران)

# 

# \*\*توضیح:\*\* ذخیره‌ی پاسخ‌های کاربران به سوالات.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه پاسخ |

# | `user\_id` | INTEGER (FK) | شناسه کاربر |

# | `button\_id` | INTEGER (FK) | شناسه دکمه |

# | `question\_id` | INTEGER (FK) | شناسه سوال |

# | `answer` | TEXT | پاسخ |

# | `submitted\_at` | TEXT (DATETIME) | زمان ارسال |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_user\_answers\_user\_button` روی `user\_id, button\_id`

# \- `idx\_user\_answers\_question\_id` روی `question\_id`

# \- `idx\_user\_answers\_user\_id` روی `user\_id`

# \- `idx\_user\_answers\_user\_question` روی `user\_id, question\_id`

# 

# \---

# 

# \### 10. جدول `button\_stats` (آمار دکمه‌ها)

# 

# \*\*توضیح:\*\* ذخیره‌ی آمار کلیک‌ها، شروع فرم و سفارشات هر دکمه.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه رکورد |

# | `button\_id` | INTEGER (FK) | شناسه دکمه |

# | `user\_id` | INTEGER (FK) | شناسه کاربر |

# | `action\_type` | TEXT | نوع اقدام (click, form\_start, order\_paid) |

# | `amount` | INTEGER | مبلغ (فقط برای order\_paid) |

# | `created\_at` | TEXT (DATETIME) | زمان ثبت |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_button\_stats\_button\_id` روی `button\_id`

# \- `idx\_button\_stats\_user\_id` روی `user\_id`

# \- `idx\_button\_stats\_action\_created` روی `action\_type, created\_at`

# \- `idx\_button\_stats\_created\_at` روی `created\_at`

# \- `idx\_button\_stats\_button\_action` روی `button\_id, action\_type`

# \- `idx\_button\_stats\_created\_action` روی `created\_at, action\_type`

# \- `idx\_button\_stats\_action\_amount` روی `action\_type, amount`

# 

# \---

# 

# \### 11. جدول `error\_logs` (لاگ خطاها)

# 

# \*\*توضیح:\*\* ذخیره‌ی خطاهای رخ‌داده در سیستم.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه خطا |

# | `error\_type` | TEXT | نوع خطا (database, api, callback, payment, security, critical) |

# | `error\_message` | TEXT | پیام خطا |

# | `traceback` | TEXT | جزئیات کامل خطا |

# | `user\_id` | INTEGER | شناسه کاربر (اختیاری) |

# | `chat\_id` | INTEGER | شناسه چت (اختیاری) |

# | `data` | TEXT (JSON) | اطلاعات اضافی |

# | `is\_resolved` | INTEGER (0/1) | آیا حل شده است |

# | `resolved\_at` | TEXT (DATETIME) | زمان حل |

# | `resolved\_by` | INTEGER | شناسه کاربر حل‌کننده |

# | `created\_at` | TEXT (DATETIME) | زمان ثبت |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_error\_logs\_error\_type` روی `error\_type`

# \- `idx\_error\_logs\_is\_resolved` روی `is\_resolved`

# \- `idx\_error\_logs\_type\_resolved` روی `error\_type, is\_resolved`

# \- `idx\_error\_logs\_user\_id` روی `user\_id`

# \- `idx\_error\_logs\_created\_at` روی `created\_at`

# 

# \---

# 

# \### 12. جدول `button\_versions` (نسخه‌های دکمه)

# 

# \*\*توضیح:\*\* ذخیره‌ی اسنپ‌شات از دکمه‌ها برای بازگردانی (Rollback).

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه نسخه |

# | `button\_id` | INTEGER (FK) | شناسه دکمه |

# | `version\_number` | INTEGER | شماره نسخه |

# | `snapshot\_data` | TEXT (JSON) | داده‌های کامل دکمه |

# | `created\_by` | INTEGER | شناسه کاربر ایجادکننده |

# | `note` | TEXT | یادداشت نسخه |

# | `created\_at` | TEXT (DATETIME) | زمان ایجاد |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_button\_versions\_button\_id` روی `button\_id`

# \- `UNIQUE(button\_id, version\_number)` برای یکتایی

# 

# \---

# 

# \### 13. جدول `settings` (تنظیمات)

# 

# \*\*توضیح:\*\* ذخیره‌ی تنظیمات عمومی ربات.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `key` | TEXT (PK) | کلید تنظیمات |

# | `value` | TEXT | مقدار |

# | `description` | TEXT | توضیحات |

# | `updated\_at` | TEXT (DATETIME) | زمان بروزرسانی |

# 

# \*\*کلیدهای پیش‌فرض:\*\*

# \- `default\_price` - مبلغ پیش‌فرض

# \- `default\_price\_label` - برچسب مبلغ پیش‌فرض

# \- `default\_menu\_columns` - تعداد ستون‌های پیش‌فرض منو

# \- `brand\_\*` - متون برندینگ

# 

# \---

# 

# \### 14. جدول `validation\_profiles` (پروفایل‌های اعتبارسنجی)

# 

# \*\*توضیح:\*\* ذخیره‌ی پروفایل‌های اعتبارسنجی برای استفاده مجدد.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه پروفایل |

# | `name` | TEXT (UNIQUE) | نام پروفایل |

# | `settings` | TEXT (JSON) | تنظیمات اعتبارسنجی |

# | `created\_at` | TEXT (DATETIME) | زمان ایجاد |

# 

# \---

# 

# \### 15. جدول `order\_logs` (تاریخچه سفارشات)

# 

# \*\*توضیح:\*\* ذخیره‌ی تاریخچه تغییرات وضعیت و یادداشت‌های سفارشات.

# 

# | نام فیلد | نوع | توضیح |

# |----------|------|-------|

# | `id` | INTEGER (PK) | شناسه لاگ |

# | `order\_id` | INTEGER (FK) | شناسه سفارش |

# | `user\_id` | INTEGER | شناسه کاربر انجام‌دهنده |

# | `action` | TEXT | نوع اقدام (status\_change, note\_added, order\_deleted) |

# | `old\_value` | TEXT | مقدار قبلی |

# | `new\_value` | TEXT | مقدار جدید |

# | `note` | TEXT | یادداشت |

# | `created\_at` | TEXT (DATETIME) | زمان ثبت |

# 

# \*\*ایندکس‌ها:\*\*

# \- `idx\_order\_logs\_order\_id` روی `order\_id`

# \- `idx\_order\_logs\_user\_id` روی `user\_id`

# \- `idx\_order\_logs\_created\_at` روی `created\_at`

# 

# \---

# 

# \## 🔗 روابط بین جداول (Foreign Keys)

# 

# | جدول | کلید خارجی | جدول مرجع | توضیح |

# |-------|-----------|-----------|-------|

# | `buttons` | `category\_id` | `categories.id` | هر دکمه در یک دسته‌بندی قرار دارد |

# | `buttons` | `parent\_button\_id` | `buttons.id` | رابطه‌ی درختی (زیرمنوها) |

# | `questions` | `button\_id` | `buttons.id` | هر سوال متعلق به یک دکمه است |

# | `question\_options` | `question\_id` | `questions.id` | گزینه‌های هر سوال |

# | `question\_conditions` | `question\_id` | `questions.id` | شرط‌های هر سوال |

# | `question\_conditions` | `condition\_question\_id` | `questions.id` | سوال مرجع شرط |

# | `dynamic\_orders` | `user\_id` | `users.user\_id` | سفارشات هر کاربر |

# | `dynamic\_orders` | `button\_id` | `buttons.id` | سرویس هر سفارش |

# | `user\_answers` | `user\_id` | `users.user\_id` | پاسخ‌های هر کاربر |

# | `user\_answers` | `button\_id` | `buttons.id` | پاسخ‌های هر دکمه |

# | `user\_answers` | `question\_id` | `questions.id` | پاسخ‌های هر سوال |

# | `button\_stats` | `button\_id` | `buttons.id` | آمار هر دکمه |

# | `button\_stats` | `user\_id` | `users.user\_id` | آمار هر کاربر |

# | `button\_versions` | `button\_id` | `buttons.id` | نسخه‌های هر دکمه |

# | `order\_logs` | `order\_id` | `dynamic\_orders.id` | تاریخچه هر سفارش |

# 

# \---

# 

# \## 📊 مهاجرت دیتابیس (Migrations)

# 

# دیتابیس از سیستم \*\*Versioning\*\* پشتیبانی می‌کند. نسخه‌ی فعلی: \*\*۴\*\*

# 

# | نسخه | توضیحات |

# |------|---------|

# | ۱ | ایجاد جداول اولیه |

# | ۲ | افزودن `admin\_note` و `status\_history` به `dynamic\_orders` |

# | ۳ | افزودن `sort\_order` به جداول اصلی |

# | ۴ | افزودن `columns` به `categories` و `buttons` + تنظیمات پیش‌فرض |

# 

# \*\*نحوه‌ی اعمال مهاجرت:\*\*

# ```python

# from database.db\_migrations import migrate\_to\_latest

# migrate\_to\_latest()

# ```

# 

# \---

# 

# \## 📌 نکات اجرایی

# 

# 1\. \*\*پشتیبان‌گیری\*\*: پشتیبان‌گیری خودکار از دیتابیس هر روز ساعت ۳ بامداد انجام می‌شود.

# 2\. \*\*بهینه‌سازی\*\*: جدول‌ها با ایندکس‌های مناسب برای عملکرد بهتر بهینه‌سازی شده‌اند.

# 3\. \*\*VACUUM\*\*: در صورت بزرگ شدن دیتابیس (بیش از ۱۰۰ مگابایت)، عملیات VACUUM خودکار انجام می‌شود.

# 4\. \*\*مهاجرت\*\*: برای تغییر ساختار دیتابیس از سیستم Migrations استفاده کنید.

# 5\. \*\*پروفایل‌ها\*\*: پروفایل‌های اعتبارسنجی قابل ذخیره و استفاده مجدد هستند.

# 

# \---

# 

# \## 🔧 نحوه‌ی افزودن جدول جدید

# 

# 1\. فایل `database/db\_connection.py` را باز کنید

# 2\. در تابع `init\_db()`، جدول جدید را با `CREATE TABLE` اضافه کنید

# 3\. در صورت نیاز، ایندکس‌ها را نیز اضافه کنید

# 4\. برای اعمال تغییرات، دیتابیس را با `migrate\_to\_latest()` مهاجرت دهید

# 

# \---

# 

# \*\*📌 آخرین بروزرسانی:\*\* ۱۴۰۳/۰۱/۱۵

# ```

