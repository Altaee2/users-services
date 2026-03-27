import requests, os
import yt_dlp
from telebot import types

user_links = {}
# دالة التحميل باستخدام yt-dlp
def download_instagram(url):
    # إعدادات التحميل
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video_%(id)s.%(ext)s',  # اسم الملف المؤقت
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


def instagram_handler(bot):

    @bot.callback_query_handler(func=lambda c: c.data == "go_instagram")
    def ask_link(call):
        bot.edit_message_text(
            "<b>📸 تحميل من إنستجرام (Reels)</b>\n\n"
            "✍️ أرسل رابط الريلز:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, receive_link)

    def receive_link(message):
        if "instagram.com" not in message.text:
            bot.send_message(message.chat.id, "❌ يرجى إرسال رابط إنستجرام صحيح.")
            return

        user_links[message.from_user.id] = message.text.strip()

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("🎥 تحميل فيديو", callback_data="ig_video"),
            types.InlineKeyboardButton("🎧 تحميل صوت", callback_data="ig_audio")
        )
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="main_start"))

        bot.send_message(message.chat.id, "اختر نوع التحميل:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data in ["ig_video", "ig_audio"])
    def download(call):
        uid = call.from_user.id
        link = user_links.get(uid)

        if not link:
            bot.answer_callback_query(call.id, "❌ أعد إرسال الرابط", show_alert=True)
            return

        # رسالة انتظار
        wait_msg = bot.send_message(call.message.chat.id, "⏳ جاري التحميل... قد يستغرق الأمر لحظات")

        try:
            # تنفيذ التحميل
            file_path = download_instagram(link)
            if not os.path.exists(file_path):
                raise Exception("File not found")

            with open(file_path, 'rb') as f:
                if call.data == "ig_video":
                    bot.send_video(
                        call.message.chat.id, f,
                        caption="✅ <b>تم تحميل الفيديو بنجاح</b>\n\n🤍 @z0a_bot\n حجم التحميل: {size}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_audio(
                        call.message.chat.id, f,
                        caption="🎧 <b>تم استخراج الصوت بنجاح</b>\n\n🤍 @altaee_z",
                        parse_mode="HTML"
                    )

            # تنظيف: حذف الملف من السيرفر بعد الإرسال
            os.remove(file_path)
            bot.delete_message(call.message.chat.id, wait_msg.message_id)

        except Exception as e:
            print(f"Error: {e}")
            bot.delete_message(call.message.chat.id, wait_msg.message_id)
            bot.send_message(
                call.message.chat.id,
                "❌ فشل التحميل. تأكد أن الحساب عام أو حاول لاحقاً."
            )
