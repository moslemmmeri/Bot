# admin_panel/msg_validation.py
# پردازش پیام‌های متنی مدیریت اعتبارسنجی - نسخه async با logging

import traceback  # ✅ اضافه شد برای traceback کامل
from logger_config import logger
from core import send_message, user_states
from database import (
    update_question,
    get_validation_settings,
    save_validation_profile
)
from .cb_routes import handle_admin_callback
from utils.error_handler import log_general_error, log_callback_error  # ✅ اضافه شد


async def handle_admin_message_validation(update):
    """
    پردازش پیام‌های متنی مربوط به مدیریت اعتبارسنجی
    بازگشت True اگر پیام پردازش شد، در غیر این صورت False
    """
    try:
        msg = update.get("message")
        if not msg:
            return False

        chat_id = msg.get("chat", {}).get("id")
        user_id = msg.get("from", {}).get("id")
        text = msg.get("text", "").strip()

        if not user_id or not chat_id:
            return False

        state_info = user_states.get(user_id, {"state": "main"})
        current_state = state_info.get("state")

        # ========== مدیریت اعتبارسنجی - تنظیم مقادیر ==========
        if current_state in [
            "admin_set_min_length",
            "admin_set_max_length",
            "admin_set_min_words",
            "admin_set_max_words",
            "admin_set_min_value",
            "admin_set_max_value",
            "admin_set_step",
            "admin_set_min_date",
            "admin_set_max_date",
            "admin_set_allowed_formats",
            "admin_set_max_file_size",
            "admin_set_min_file_size",
            "admin_set_max_files",
            "admin_set_dimensions",
            "admin_set_aspect_ratio",
            "admin_set_regex_pattern",
            "admin_set_starts_with",
            "admin_set_ends_with",
            "admin_set_contains",
            "admin_set_not_contains",
            "admin_set_forbidden_words",
            "admin_set_required_words",
            "admin_set_validation_error",
            "admin_set_validation_hint",
            "admin_set_conditional_value"
        ]:
            q_id = state_info.get("q_id")
            field_name = state_info.get("field_name")

            if not q_id or not field_name:
                await send_message(chat_id, "❌ خطا: اطلاعات ناقص.")
                user_states[user_id] = {"state": "main"}
                return True

            try:
                # شرط نمایش - مقدار
                if current_state == "admin_set_conditional_value":
                    cond_on = state_info.get("conditional_on")
                    if not cond_on:
                        await send_message(chat_id, "❌ خطا: سوال مرجع انتخاب نشده.")
                        user_states[user_id] = {"state": "main"}
                        return True

                    update_question(q_id, conditional_on=cond_on, conditional_value=text)
                    logger.info(f"شرط نمایش برای سوال {q_id} با مقدار «{text}» تنظیم شد (توسط کاربر {user_id})")
                    await send_message(chat_id, f"✅ شرط نمایش با مقدار «{text}» تنظیم شد.")
                    user_states[user_id] = {"state": "main"}
                    await handle_admin_callback({
                        "callback_query": {
                            "data": f"admin_q_validation_{q_id}",
                            "from": {"id": user_id},
                            "message": {"chat": {"id": chat_id}}
                        }
                    })
                    return True

                # ابعاد عکس
                if current_state == "admin_set_dimensions":
                    if "×" not in text and "x" not in text:
                        await send_message(chat_id, "❌ فرمت ابعاد را به درستی وارد کنید (مثال: ۳۰۰×۳۰۰).")
                        return True

                    parts = text.replace("x", "×").split("×")
                    if len(parts) != 2:
                        await send_message(chat_id, "❌ فرمت ابعاد را به درستی وارد کنید (مثال: ۳۰۰×۳۰۰).")
                        return True

                    try:
                        width = int(parts[0].strip())
                        height = int(parts[1].strip())
                        update_question(q_id, required_width=width, required_height=height)
                        logger.info(f"ابعاد سوال {q_id} به {width}×{height} تنظیم شد (توسط کاربر {user_id})")
                        await send_message(chat_id, f"✅ ابعاد {width}×{height} تنظیم شد.")
                    except ValueError:
                        await send_message(chat_id, "❌ لطفاً اعداد معتبر وارد کنید.")
                        user_states[user_id] = {"state": "main"}
                        return True

                # مقادیر عددی
                elif current_state in [
                    "admin_set_min_length",
                    "admin_set_max_length",
                    "admin_set_min_words",
                    "admin_set_max_words",
                    "admin_set_min_value",
                    "admin_set_max_value",
                    "admin_set_step",
                    "admin_set_max_file_size",
                    "admin_set_min_file_size",
                    "admin_set_max_files"
                ]:
                    try:
                        value = int(text.replace(",", "").replace(" ", ""))
                        if value < 0:
                            await send_message(chat_id, "❌ مقدار نمی‌تواند منفی باشد.")
                            return True
                        update_question(q_id, **{field_name: value})
                        logger.info(f"{field_name} برای سوال {q_id} به {value} تنظیم شد (توسط کاربر {user_id})")
                        await send_message(chat_id, f"✅ {field_name} به {value} تنظیم شد.")
                    except ValueError:
                        await send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید.")
                        user_states[user_id] = {"state": "main"}
                        return True

                # تاریخ
                elif current_state in ["admin_set_min_date", "admin_set_max_date"]:
                    # اعتبارسنجی ساده تاریخ
                    if len(text) < 8 or "/" not in text:
                        await send_message(chat_id, "❌ فرمت تاریخ را به درستی وارد کنید (مثال: ۱۴۰۳/۰۱/۰۱).")
                        return True
                    update_question(q_id, **{field_name: text})
                    logger.info(f"{field_name} برای سوال {q_id} به {text} تنظیم شد (توسط کاربر {user_id})")
                    await send_message(chat_id, f"✅ {field_name} به {text} تنظیم شد.")

                # نسبت تصویر
                elif current_state == "admin_set_aspect_ratio":
                    if ":" not in text:
                        await send_message(chat_id, "❌ فرمت نسبت تصویر را به درستی وارد کنید (مثال: 1:1 یا 16:9).")
                        return True
                    update_question(q_id, aspect_ratio=text)
                    logger.info(f"نسبت تصویر سوال {q_id} به {text} تنظیم شد (توسط کاربر {user_id})")
                    await send_message(chat_id, f"✅ نسبت تصویر به {text} تنظیم شد.")

                # سایر فیلدها
                else:
                    update_question(q_id, **{field_name: text})
                    logger.info(f"{field_name} برای سوال {q_id} به {text} تنظیم شد (توسط کاربر {user_id})")
                    await send_message(chat_id, f"✅ {field_name} تنظیم شد.")

                user_states[user_id] = {"state": "main"}
                await handle_admin_callback({
                    "callback_query": {
                        "data": f"admin_q_validation_{q_id}",
                        "from": {"id": user_id},
                        "message": {"chat": {"id": chat_id}}
                    }
                })
                return True

            except Exception as e:
                # ✅ استفاده از log_general_error با traceback کامل
                log_general_error(
                    f"Error in validation message handling for state {current_state}: {str(e)}",
                    traceback=traceback.format_exc(),
                    user_id=user_id,
                    chat_id=chat_id
                )
                await send_message(chat_id, f"❌ خطا در تنظیم {field_name}: {str(e)}")
                user_states[user_id] = {"state": "main"}
                return True

        # ========== ذخیره پروفایل ==========
        if current_state == "admin_set_profile_name":
            if not text:
                await send_message(chat_id, "❌ نام نمی‌تواند خالی باشد.")
                return True

            q_id = state_info.get("q_id")
            if not q_id:
                await send_message(chat_id, "❌ خطا: شناسه سوال یافت نشد.")
                user_states[user_id] = {"state": "main"}
                return True

            try:
                settings = get_validation_settings(q_id)
                if not settings:
                    await send_message(chat_id, "❌ تنظیمات یافت نشد.")
                    user_states[user_id] = {"state": "main"}
                    return True

                # حذف فیلدهای غیرضروری از تنظیمات
                settings.pop('id', None)

                # ذخیره پروفایل
                save_validation_profile(text, settings)
                logger.info(f"پروفایل «{text}» با موفقیت ذخیره شد (توسط کاربر {user_id})")
                await send_message(chat_id, f"✅ پروفایل «{text}» با موفقیت ذخیره شد.")

                user_states[user_id] = {"state": "main"}
                await handle_admin_callback({
                    "callback_query": {
                        "data": f"admin_q_validation_{q_id}",
                        "from": {"id": user_id},
                        "message": {"chat": {"id": chat_id}}
                    }
                })
                return True

            except Exception as e:
                # ✅ استفاده از log_general_error با traceback کامل
                log_general_error(
                    f"Error in saving validation profile: {str(e)}",
                    traceback=traceback.format_exc(),
                    user_id=user_id,
                    chat_id=chat_id
                )
                await send_message(chat_id, f"❌ خطا در ذخیره پروفایل: {str(e)}")
                user_states[user_id] = {"state": "main"}
                return True

        return False

    except Exception as e:
        # ✅ استفاده از log_callback_error با traceback کامل
        log_callback_error(
            f"Error in handle_admin_message_validation: {str(e)}",
            traceback=traceback.format_exc(),
            user_id=user_id if 'user_id' in locals() else None,
            chat_id=chat_id if 'chat_id' in locals() else None
        )
        try:
            await send_message(chat_id, f"❌ خطای سیستمی: {str(e)}")
        except Exception:
            pass
        return True