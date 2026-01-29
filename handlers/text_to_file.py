import os
from io import BytesIO
from datetime import datetime
from telebot import types

# قواميس لتخزين البيانات مؤقتاً
waiting_for_text = {} # تخزين الامتداد المختارة
text_buffers = {}     # تخزين النصوص المستلمة

# الهيدر والفوتر للملف (اختياري)
RIGHTS_HEADER = """# 🤍 تلجرام :- @altaee_z 
# http://www.services-bot.free.nf
# ---------------------------------------
"""

RIGHTS_FOOTER = """
# ---------------------------------------
# تم التحويل بواسطة بوت علي الطائي
# 🤍 تلجرام :- @altaee_z 
"""
def text_handler(bot):

    # 1. قائمة اختيار الامتداد (التصميم الذي طلبته)
    @bot.callback_query_handler(func=lambda call: call.data == "go_text")
    def choose_extension(call):
        k = types.InlineKeyboardMarkup(row_width=3)
        k.add(
            types.InlineKeyboardButton("🐍 py", callback_data="ext_py"),
            types.InlineKeyboardButton("🐘 php", callback_data="ext_php"),
            types.InlineKeyboardButton("📄 txt", callback_data="ext_txt"),
            types.InlineKeyboardButton("🌐 html", callback_data="ext_html"),
            types.InlineKeyboardButton("🟨 js", callback_data="ext_js"),
            types.InlineKeyboardButton("🎨 css", callback_data="ext_css"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="main_start")
        )
        bot.edit_message_text(
            "📁 اختر امتداد الملف:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=k
        )

    # 2. بدء الجلسة بعد اختيار الامتداد
    @bot.callback_query_handler(func=lambda call: call.data.startswith("ext_"))
    def start_collecting(call):
        ext = call.data.replace("ext_", "")
        uid = call.from_user.id

        waiting_for_text[uid] = ext
        text_buffers[uid] = []

        k = types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_text"))

        bot.edit_message_text(
            f"✍️ أرسل النصوص الآن\n\n"
            f"📌 الامتداد المختار: `.{ext}`\n"
            f"📥 كل رسالة ترسلها ستُضاف للملف نفسه.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=k,
            parse_mode="Markdown"
        )

    # 3. استقبال النصوص وإظهار إشعار مع زر الانتهاء
    @bot.message_handler(func=lambda m: m.from_user.id in waiting_for_text)
    def collect_messages(message):
        uid = message.from_user.id
        ext = waiting_for_text[uid]
        
        text_buffers[uid].append(message.text)
        count = len(text_buffers[uid])

        # كيبورد الإشعار (يظهر مع كل رسالة)
        k = types.InlineKeyboardMarkup()
        k.add(
            types.InlineKeyboardButton("✅ انتهاء وحفظ الملف", callback_data="finish_text"),
            types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_text")
        )

        bot.reply_to(
            message,
            f"📥 **تم استلام النص رقم ({count})**\n"
            f"📌 الملف الحالي: `.{ext}`\n\n"
            "أرسل المزيد أو اضغط (انتهاء) لتسمية الملف وحفظه.",
            reply_markup=k,
            parse_mode="Markdown"
        )

    # 4. مرحلة طلب الاسم بعد الضغط على انتهاء
    @bot.callback_query_handler(func=lambda call: call.data == "finish_text")
    def ask_name(call):
        uid = call.from_user.id
        if uid not in text_buffers or not text_buffers[uid]:
            return bot.answer_callback_query(call.id, "⚠️ لا توجد نصوص!", show_alert=True)

        k = types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("⏭️ تخطي (اسم تلقائي)", callback_data="skip_name"))
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        msg = bot.send_message(
            call.message.chat.id,
            "📝 **أرسل الآن الاسم الذي تريده للملف:**\n"
            "مثلاً: `my_script`",
            reply_markup=k,
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_custom_name, bot)

    # 5. معالجة الاسم المكتوب
    def process_custom_name(message, bot):
        if message.text:
            create_and_send_final(bot, message, message.text)

    # 6. معالجة التخطي
    @bot.callback_query_handler(func=lambda call: call.data == "skip_name")
    def skip_name_btn(call):
        bot.clear_step_handler_by_chat_id(call.message.chat.id)
        create_and_send_final(bot, call.message, None, is_skipped=True)

    # 7. دالة الإنشاء النهائية والإرسال
    def create_and_send_final(bot, message, name, is_skipped=False):
        uid = message.chat.id
        ext = waiting_for_text.get(uid)
        if not ext: return

        try:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")

            # اختيار الاسم
            final_filename = f"File_{date_str}.{ext}" if is_skipped else f"{name}.{ext}"

            # دمج النصوص
            content = RIGHTS_HEADER + "\n\n".join(text_buffers[uid]) + RIGHTS_FOOTER
            lines_count = sum(len(text.split('\n')) for text in text_buffers[uid])

            # تكوين الملف في الذاكرة
            bio = BytesIO()
            bio.write(content.encode('utf-8'))
            bio.seek(0)
            bio.name = final_filename

            caption = (
                f"<b>✅ تم تحويل النص إلى ملف</b>\n\n"
                f"📁 <b>اسم الملف:</b> <code>{final_filename}</code>\n"
                f"📝 <b>عدد الأسطر:</b> <code>{lines_count}</code>\n"
                f"📅 <b>التاريخ:</b> <code>{date_str}</code>\n"
                f"⏰ <b>الوقت:</b> <code>{time_str}</code>\n\n"
                f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
            )

            bot.send_document(
                message.chat.id,
                bio,
                caption=caption,
                parse_mode="HTML"
            )

        except Exception as e:
            bot.send_message(message.chat.id, "❌ حدث خطأ غير متوقع.")
        
        finally:
            # تنظيف الذاكرة للمستخدم
            waiting_for_text.pop(uid, None)
            text_buffers.pop(uid, None)

    # 8. إلغاء العملية
    @bot.callback_query_handler(func=lambda call: call.data == "cancel_text")
    def cancel_text(call):
        uid = call.from_user.id
        waiting_for_text.pop(uid, None)
        text_buffers.pop(uid, None)
        bot.edit_message_text("❌ تم إلغاء العملية وتم مسح البيانات.", call.message.chat.id, call.message.message_id)

