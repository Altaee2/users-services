import requests
from telebot import types
import os
from keyboards.main_keyboard import get_start_keyboard

user_links = {}

def get_file_size(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=10)
        size = int(r.headers.get("Content-Length", 0))
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
    except:
        return "غير معروف"

def download_tiktok(url):
    headers = {
        "referer": "https://lovetik.com/sa/video/",
        "origin": "https://lovetik.com",
        "user-agent": "Mozilla/5.0"
    }

    r = requests.post(
        "https://lovetik.com/api/ajax/search",
        headers=headers,
        data={"query": url},
        timeout=20
    ).json()

    video_url = r["links"][2]["a"]
    audio_url = r["links"][1]["a"]

    return video_url, audio_url

def tiktok_handler(bot):

    @bot.callback_query_handler(func=lambda c: c.data == "go_tiktok")
    def ask_link(call):
        bot.edit_message_text(
            "<b>🎵 تحميل من TikTok</b>\n\n"
            "✍️ أرسل رابط فيديو تيك توك:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, receive_link)

    def receive_link(message):
        user_links[message.from_user.id] = message.text.strip()

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("🎥 تحميل فيديو", callback_data="tt_video"),
            types.InlineKeyboardButton("🎧 تحميل صوت MP3", callback_data="tt_audio")
        )
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="main_start"))

        bot.send_message(message.chat.id, "اختر نوع التحميل:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data in ["tt_video", "tt_audio"])
    def download(call):
        uid = call.from_user.id
        url = user_links.get(uid)

        if not url:
            bot.answer_callback_query(call.id, "❌ أعد إرسال الرابط", show_alert=True)
            return

        try:
            video_url, audio_url = download_tiktok(url)

            if call.data == "tt_video":
                size = get_file_size(video_url)

                caption = (
                    f"✅ <b>تم تحميل الفيديو</b>\n"
                    f"📦 الحجم: <b>{size}</b>\n\n"
                    f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
                )

                bot.send_video(
                    call.message.chat.id,
                    video_url,
                    caption=caption,
                    parse_mode="HTML"
                )

            else:
                audio_path = f"tiktok_{uid}.mp3"

                with requests.get(audio_url, stream=True) as r:
                    with open(audio_path, "wb") as f:
                        for chunk in r.iter_content(1024 * 1024):
                            f.write(chunk)

                size = os.path.getsize(audio_path)
                size = f"{size / (1024*1024):.2f} MB"

                caption = (
                    f"🎧 <b>تم تحميل الصوت MP3</b>\n"
                    f"📦 الحجم: <b>{size}</b>\n\n"
                    "🤍 @altaee_z\n🌐 www.ali-Altaee.free.nf"
                )

                with open(audio_path, "rb") as audio:
                    bot.send_audio(
                        call.message.chat.id,
                        audio,
                        caption=caption,
                        parse_mode="HTML"
                    )

                os.remove(audio_path)

        except Exception as e:
            bot.send_message(
                call.message.chat.id,
                "❌ فشل التحميل، الرابط غير صالح أو الخدمة غير متاحة."
            )