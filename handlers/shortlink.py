import gdshortener
import re
from telebot import types

# دالة الاختصار
def shorten_link(url):
    try:
        s = gdshortener.ISGDShortener()
        short_url = s.shorten(url)
        return short_url[0] if isinstance(short_url, list) else short_url
    except:
        return None

def shortener_handler(bot):
    
    # 1. عند الضغط على زر "اختصار رابط" في القائمة الرئيسية
    @bot.callback_query_handler(func=lambda c: c.data == "go_shortener")
    def ask_link_short(call):
        bot.edit_message_text(
            "<b>🔗 خدمة اختصار الروابط</b>\n\n"
            "✍️ أرسل الرابط الطويل الذي تريد اختصاره:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        # ننتقل للخطوة التالية لاستلام الرابط
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, receive_link_to_shorten)

    # 2. استلام الرابط ومعالجته
    def receive_link_to_shorten(message):
        url = message.text.strip()
        
        # التحقق إذا كان المرسل رابطاً فعلاً
        if re.search(r"https?://[^\s]+", url):
            # إرسال رسالة انتظار
            wait_msg = bot.send_message(message.chat.id, "⏳ جاري إنشاء الرابط المختصر...")
            
            short = shorten_link(url)
            
            if short:
                # حذف رسالة الانتظار وإظهار النتيجة
                bot.delete_message(message.chat.id, wait_msg.message_id)
                
                text = (
                    f"✅ <b>تم اختصار الرابط بنجاح!</b>\n\n"
                    f"🔗 الرابط المختصر:\n<code>{short}</code>\n\n"
                    f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
                )
                
                # إضافة زر رجوع للقائمة الرئيسية
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="main_start"))
                
                bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)
                
                # ننتقل لخطوة التقييم إذا أردت
                bot.register_next_step_handler(message, rate_bot)
            else:
                bot.delete_message(message.chat.id, wait_msg.message_id)
                bot.send_message(message.chat.id, "❌ عذراً، فشل الاختصار حالياً. حاول لاحقاً.")
        else:
            bot.send_message(message.chat.id, "❌ هذا ليس رابطاً صالحاً. أرسل رابطاً يبدأ بـ http أو https.")

    # 3. دالة التقييم
    def rate_bot(message):
        if message.text in ['1', '2', '3', '4', '5']:
            bot.reply_to(message, "شكراً لتقييمك يا غالي! ❤️")
        else:
            # إذا أرسل شيئاً آخر غير الأرقام ننهي العملية بهدوء
            pass
