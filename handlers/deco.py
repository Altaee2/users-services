from telebot import types
from datetime import datetime, timedelta
from keyboards.deco_keyboard import get_deco_keyboard
from utils.deco_data import eng_chars, ar_styles
import random

def deco_handler(bot):

    # دخول قسم الزخرفة
    @bot.callback_query_handler(func=lambda c: c.data == "go_deco")
    def open_deco(call):
        now = datetime.utcnow() + timedelta(hours=3)
        time_now = now.strftime("%I:%M %p").replace("AM", "صباحاً").replace("PM", "مساءً")

        text = (
            "<b>💎 قسم زخرفة النصوص الاحترافي</b>\n\n"
            "اختر نوع اللغة:\n"
            "• زخرفة إنجليزية\n"
            "• زخرفة عربية\n\n"
            f"⏰ الوقت: <code>{time_now}</code>\n"
            f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_deco_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    # زخرفة إنجليزي
    @bot.callback_query_handler(func=lambda c: c.data == "deco_eng")
    def ask_eng(call):
        msg = bot.send_message(
            call.message.chat.id,
            "<b>✍️ أرسل النص الإنجليزي:</b>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_eng)

    def process_eng(message):
        text = message.text
        results = []

        for i in range(5):
            styled = ""
            for ch in text:
                if ch in eng_chars:
                    styled += random.choice(eng_chars[ch])
                else:
                    styled += ch
            results.append(styled)

        bot.reply_to(message, "\n".join(results))

    # زخرفة عربي
    @bot.callback_query_handler(func=lambda c: c.data == "deco_ar")
    def ask_ar(call):
        msg = bot.send_message(
            call.message.chat.id,
            "<b>✍️ أرسل النص العربي:</b>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_ar)

    def process_ar(message):
        word = message.text
        results = [style.format(word) for style in ar_styles]
        bot.reply_to(message, "\n".join(results))