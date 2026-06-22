-- ============================================================
-- database/migrations/add_indexes.sql
-- افزودن ایندکس‌های بهینه‌سازی برای جداول اصلی دیتابیس
-- ============================================================

-- ============================================================
-- ۱. ایندکس‌های جدول users
-- ============================================================

-- ایندکس برای جستجوی کاربر بر اساس شناسه (Primary Key خودش ایندکس است)
-- ایندکس برای آخرین فعالیت (مرتب‌سازی و فیلتر کاربران فعال)
CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);

-- ایندکس ترکیبی برای جستجوی کاربران با نام کاربری (در صورت جستجو)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);


-- ============================================================
-- ۲. ایندکس‌های جدول admins
-- ============================================================

-- ایندکس برای بررسی سریع ادمین بودن کاربر
CREATE INDEX IF NOT EXISTS idx_admins_user_id ON admins(user_id);

-- ایندکس ترکیبی برای فیلتر ادمین‌های فعال
CREATE INDEX IF NOT EXISTS idx_admins_is_active_role ON admins(is_active, role);


-- ============================================================
-- ۳. ایندکس‌های جدول categories
-- ============================================================

-- ایندکس برای دریافت دسته‌بندی بر اساس مکان (location)
CREATE INDEX IF NOT EXISTS idx_categories_location ON categories(location);

-- ایندکس برای فیلتر دسته‌بندی‌های فعال
CREATE INDEX IF NOT EXISTS idx_categories_is_active ON categories(is_active);


-- ============================================================
-- ۴. ایندکس‌های جدول buttons
-- ============================================================

-- ایندکس برای دریافت دکمه‌های یک دسته‌بندی
CREATE INDEX IF NOT EXISTS idx_buttons_category_id ON buttons(category_id);

-- ایندکس برای دریافت زیرمنوهای یک دکمه
CREATE INDEX IF NOT EXISTS idx_buttons_parent_button_id ON buttons(parent_button_id);

-- ایندکس برای جستجوی دکمه بر اساس callback_data (منحصر‌به‌فرد است)
CREATE INDEX IF NOT EXISTS idx_buttons_callback_data ON buttons(callback_data);

-- ایندکس ترکیبی برای دریافت دکمه‌های فعال یک دسته‌بندی با ترتیب
CREATE INDEX IF NOT EXISTS idx_buttons_category_active_sort ON buttons(category_id, is_active, sort_order);

-- ایندکس برای فیلتر دکمه‌های فعال
CREATE INDEX IF NOT EXISTS idx_buttons_is_active ON buttons(is_active);


-- ============================================================
-- ۵. ایندکس‌های جدول questions
-- ============================================================

-- ایندکس برای دریافت سوالات یک دکمه
CREATE INDEX IF NOT EXISTS idx_questions_button_id ON questions(button_id);

-- ایندکس ترکیبی برای دریافت سوالات فعال یک دکمه با ترتیب
CREATE INDEX IF NOT EXISTS idx_questions_button_active_sort ON questions(button_id, is_active, sort_order);

-- ایندکس برای فیلتر سوالات فعال
CREATE INDEX IF NOT EXISTS idx_questions_is_active ON questions(is_active);


-- ============================================================
-- ۶. ایندکس‌های جدول question_options
-- ============================================================

-- ایندکس برای دریافت گزینه‌های یک سوال
CREATE INDEX IF NOT EXISTS idx_question_options_question_id ON question_options(question_id);

-- ایندکس برای جستجوی گزینه بر اساس callback_data
CREATE INDEX IF NOT EXISTS idx_question_options_callback_data ON question_options(callback_data);

-- ایندکس برای فیلتر گزینه‌های فعال
CREATE INDEX IF NOT EXISTS idx_question_options_is_active ON question_options(is_active);


-- ============================================================
-- ۷. ایندکس‌های جدول question_conditions
-- ============================================================

-- ایندکس برای دریافت شرط‌های یک سوال
CREATE INDEX IF NOT EXISTS idx_question_conditions_question_id ON question_conditions(question_id);

-- ایندکس برای دریافت شرط‌هایی که به یک سوال مرجع اشاره دارند
CREATE INDEX IF NOT EXISTS idx_question_conditions_condition_question_id ON question_conditions(condition_question_id);


-- ============================================================
-- ۸. ایندکس‌های جدول dynamic_orders (سفارشات)
-- ============================================================

-- ایندکس برای دریافت سفارشات یک کاربر
CREATE INDEX IF NOT EXISTS idx_dynamic_orders_user_id ON dynamic_orders(user_id);

-- ایندکس برای دریافت سفارشات یک سرویس (دکمه)
CREATE INDEX IF NOT EXISTS idx_dynamic_orders_button_id ON dynamic_orders(button_id);

-- ایندکس برای فیلتر سفارشات بر اساس وضعیت
CREATE INDEX IF NOT EXISTS idx_dynamic_orders_status ON dynamic_orders(status);

-- ایندکس ترکیبی برای فیلتر سریع سفارشات بر اساس وضعیت و تاریخ
CREATE INDEX IF NOT EXISTS idx_dynamic_orders_status_created ON dynamic_orders(status, created_at);

-- ایندکس برای مرتب‌سازی سفارشات بر اساس تاریخ
CREATE INDEX IF NOT EXISTS idx_dynamic_orders_created_at ON dynamic_orders(created_at);

-- ایندکس برای جستجوی کد رهگیری
CREATE INDEX IF NOT EXISTS idx_dynamic_orders_tracking_code ON dynamic_orders(tracking_code);


-- ============================================================
-- ۹. ایندکس‌های جدول user_answers (پاسخ‌های کاربران)
-- ============================================================

-- ایندکس ترکیبی برای دریافت پاسخ‌های یک کاربر در یک دکمه
CREATE INDEX IF NOT EXISTS idx_user_answers_user_button ON user_answers(user_id, button_id);

-- ایندکس برای دریافت پاسخ‌های یک سوال
CREATE INDEX IF NOT EXISTS idx_user_answers_question_id ON user_answers(question_id);

-- ایندکس برای دریافت پاسخ‌های یک کاربر
CREATE INDEX IF NOT EXISTS idx_user_answers_user_id ON user_answers(user_id);


-- ============================================================
-- ۱۰. ایندکس‌های جدول button_stats (آمار دکمه‌ها)
-- ============================================================

-- ایندکس ترکیبی برای دریافت آمار یک دکمه
CREATE INDEX IF NOT EXISTS idx_button_stats_button_id ON button_stats(button_id);

-- ایندکس ترکیبی برای دریافت آمار یک کاربر
CREATE INDEX IF NOT EXISTS idx_button_stats_user_id ON button_stats(user_id);

-- ایندکس ترکیبی برای فیلتر بر اساس نوع عمل و تاریخ
CREATE INDEX IF NOT EXISTS idx_button_stats_action_created ON button_stats(action_type, created_at);

-- ایندکس برای دریافت آمار دوره‌ای بر اساس تاریخ
CREATE INDEX IF NOT EXISTS idx_button_stats_created_at ON button_stats(created_at);

-- ایندکس ترکیبی برای محاسبه سریع درآمد یک دکمه
CREATE INDEX IF NOT EXISTS idx_button_stats_button_action ON button_stats(button_id, action_type);


-- ============================================================
-- ۱۱. ایندکس‌های جدول error_logs (خطاها)
-- ============================================================

-- ایندکس برای فیلتر خطاها بر اساس نوع
CREATE INDEX IF NOT EXISTS idx_error_logs_error_type ON error_logs(error_type);

-- ایندکس برای فیلتر خطاهای حل‌نشده
CREATE INDEX IF NOT EXISTS idx_error_logs_is_resolved ON error_logs(is_resolved);

-- ایندکس ترکیبی برای دریافت خطاهای حل‌نشده یک نوع
CREATE INDEX IF NOT EXISTS idx_error_logs_type_resolved ON error_logs(error_type, is_resolved);

-- ایندکس برای دریافت خطاهای یک کاربر
CREATE INDEX IF NOT EXISTS idx_error_logs_user_id ON error_logs(user_id);

-- ایندکس برای مرتب‌سازی خطاها بر اساس تاریخ
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs(created_at);


-- ============================================================
-- ۱۲. ایندکس‌های جدول button_versions (نسخه‌های دکمه‌ها)
-- ============================================================

-- ایندکس ترکیبی برای دریافت نسخه‌های یک دکمه
CREATE INDEX IF NOT EXISTS idx_button_versions_button_id ON button_versions(button_id);

-- ایندکس ترکیبی منحصر‌به‌فرد برای دریافت یک نسخه خاص
-- (این ایندکس با UNIQUE(button_id, version_number) پوشش داده می‌شود)


-- ============================================================
-- ۱۳. ایندکس‌های جدول order_logs (تاریخچه سفارشات)
-- ============================================================

-- ایندکس برای دریافت تاریخچه یک سفارش
CREATE INDEX IF NOT EXISTS idx_order_logs_order_id ON order_logs(order_id);

-- ایندکس برای دریافت تاریخچه یک کاربر
CREATE INDEX IF NOT EXISTS idx_order_logs_user_id ON order_logs(user_id);

-- ایندکس برای مرتب‌سازی تاریخچه بر اساس زمان
CREATE INDEX IF NOT EXISTS idx_order_logs_created_at ON order_logs(created_at);


-- ============================================================
-- ۱۴. ایندکس‌های جدول validation_profiles (پروفایل‌های اعتبارسنجی)
-- ============================================================

-- ایندکس برای جستجوی پروفایل بر اساس نام (منحصر‌به‌فرد است)
CREATE INDEX IF NOT EXISTS idx_validation_profiles_name ON validation_profiles(name);


-- ============================================================
-- ۱۵. ایندکس‌های جدول submenus (زیرمنوها - در صورت وجود)
-- ============================================================

-- ایندکس برای دریافت زیرمنوهای یک دکمه
CREATE INDEX IF NOT EXISTS idx_submenus_button_id ON submenus(button_id);

-- ایندکس برای جستجوی زیرمنو بر اساس callback_data
CREATE INDEX IF NOT EXISTS idx_submenus_callback_data ON submenus(callback_data);


-- ============================================================
-- ۱۶. ایندکس‌های جدول settings (تنظیمات)
-- ============================================================

-- ایندکس برای دریافت تنظیمات بر اساس کلید (Primary Key است)


-- ============================================================
-- ۱۷. ایندکس‌های جدول button_stats برای گزارش‌دهی دوره‌ای
-- ============================================================

-- ایندکس ترکیبی برای گزارش‌های روزانه/هفتگی
CREATE INDEX IF NOT EXISTS idx_button_stats_created_action ON button_stats(created_at, action_type);

-- ایندکس ترکیبی برای گزارش درآمد دوره‌ای
CREATE INDEX IF NOT EXISTS idx_button_stats_action_amount ON button_stats(action_type, amount);


-- ============================================================
-- ۱۸. ایندکس‌های ترکیبی پیشرفته برای کوئری‌های سنگین
-- ============================================================

-- ایندکس ترکیبی برای دریافت سفارشات یک کاربر با وضعیت خاص
CREATE INDEX IF NOT EXISTS idx_dynamic_orders_user_status ON dynamic_orders(user_id, status);

-- ایندکس ترکیبی برای دریافت سفارشات یک سرویس با وضعیت خاص
CREATE INDEX IF NOT EXISTS idx_dynamic_orders_button_status ON dynamic_orders(button_id, status);

-- ایندکس ترکیبی برای دریافت پاسخ‌های یک کاربر در یک سوال خاص
CREATE INDEX IF NOT EXISTS idx_user_answers_user_question ON user_answers(user_id, question_id);


-- ============================================================
-- خلاصه ایندکس‌های اضافه‌شده
-- ============================================================
-- 
-- تعداد کل ایندکس‌ها: ~۴۰ ایندکس
-- 
-- جداول بهینه‌سازی‌شده:
--   - users: 2 ایندکس
--   - admins: 2 ایندکس
--   - categories: 2 ایندکس
--   - buttons: 5 ایندکس
--   - questions: 3 ایندکس
--   - question_options: 3 ایندکس
--   - question_conditions: 2 ایندکس
--   - dynamic_orders: 7 ایندکس
--   - user_answers: 3 ایندکس
--   - button_stats: 5 ایندکس
--   - error_logs: 5 ایندکس
--   - button_versions: 1 ایندکس
--   - order_logs: 3 ایندکس
--   - validation_profiles: 1 ایندکس
--   - submenus: 2 ایندکس
--
-- ============================================================