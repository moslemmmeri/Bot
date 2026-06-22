# bot.py
# حلقه اصلی ربات - نسخه ناهمگام با استفاده از handlers و services
# استفاده از معماری لایه‌ای: handlers (کنترلر) ← services (منطق) ← repositories (دسترسی به داده)

import asyncio
import traceback
from config import config
from logger_config import logger
from core import get_updates, delete_webhook, log_error
from database import init_db
from database.connection.manager import get_db_connection
from services import create_services
from handlers import MainHandler

# ============================================================
# مقداردهی اولیه
# ============================================================

init_db()
logger.info("✅ دیتابیس مقداردهی اولیه شد.")

# زمان‌های تاخیر از تنظیمات
LOOP_SLEEP_INTERVAL = getattr(config, 'LOOP_SLEEP_INTERVAL', 0.5)
ERROR_SLEEP_INTERVAL = getattr(config, 'ERROR_SLEEP_INTERVAL', 2)


# ============================================================
# تابع اصلی
# ============================================================

async def main():
    """
    حلقه اصلی دریافت آپدیت‌ها و پردازش آنها با استفاده از MainHandler
    """
    logger.info("🚀 ربات راه‌اندازی شد... (نسخه با handlers)")

    # حذف وب‌هوک برای اطمینان از دریافت آپدیت‌ها به‌صورت Long Polling
    await delete_webhook()
    logger.info("✅ وب‌هوک حذف شد.")

    last_update_id = 0

    while True:
        try:
            # دریافت آپدیت‌ها
            updates = await get_updates(offset=last_update_id + 1)

            for update in updates:
                update_id = update.get("update_id")
                if update_id and update_id > last_update_id:
                    last_update_id = update_id

                # پردازش هر آپدیت با یک اتصال دیتابیس جدید
                # استفاده از context manager برای بسته‌شدن خودکار اتصال
                with get_db_connection() as conn:
                    # ایجاد سرویس‌ها با اتصال فعلی
                    services = create_services(conn)

                    # ایجاد هندلر اصلی و پردازش آپدیت
                    handler = MainHandler(conn, services)
                    await handler.handle(update)

            # مکث کوتاه بین درخواست‌ها
            await asyncio.sleep(LOOP_SLEEP_INTERVAL)

        except Exception as e:
            # ثبت خطا با traceback کامل
            error_msg = f"خطا در حلقه اصلی: {str(e)}"
            logger.error(error_msg, exc_info=True)
            log_error('critical', error_msg, traceback=traceback.format_exc())

            # مکث قبل از تلاش مجدد
            await asyncio.sleep(ERROR_SLEEP_INTERVAL)


# ============================================================
# اجرای اصلی
# ============================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ ربات با Ctrl+C متوقف شد.")
    except Exception as e:
        logger.error(f"❌ خطای بحرانی در اجرای ربات: {e}", exc_info=True)