import requests
from telebot import types

# دالة التشكيل عبر موقع arabic-keyboard (محرك المعالجة)
def tashkeel_text(text):
    try:
        # استخدام quote لضمان إرسال النص العربي بشكل صحيح في الرابط
        url = f'https://www.arabic-keyboard.org/tashkeel/import.php?area={requests.utils.quote(text)}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.arabic-keyboard.org/tashkeel/'
        }
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            dat = res.json()
            return dat.get("text", "")
        return None
    except Exception as e:
        print(f"Tashkeel Logic Error: {e}")
        return None

def tashkeel_handler(bot):

    # 1. عند الضغط على زر "تشكيل النصوص" من القائمة الرئيسية
    @bot.callback_query_handler(func=lambda c: c.data == "go_tashkeel")
    def ask_tashkeel_text(call):
        # نقوم بتحديث نفس الرسالة لطلب النص
        bot.edit_message_text(
            "<b>✍️ خدمة تشكيل النصوص العربية</b>\n\n"
            "أرسل الآن النص الذي تريد وضع الحركات والتشكيل عليه:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        # ننتظر رد المستخدم بالنص
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: process_tashkeel(m, bot))

    # 2. استلام النص ومعالجته وإرسال النتيجة
    def process_tashkeel(message, bot):
        text_to_format = message.text.strip() if message.text else ""
        
        # التحقق من أن المستخدم أرسل نصاً وليس صورة أو ملف
        if not text_to_format or len(text_to_format) < 2:
            bot.send_message(message.chat.id, "❌ يرجى إرسال نص عربي واضح لغرض التشكيل.")
            return

        # إرسال رسالة انتظار مؤقتة
        wait_msg = bot.send_message(message.chat.id, "⏳ جاري تشكيل النص... انتظر قليلاً")
        bot.send_chat_action(message.chat.id, 'typing')

        formatted_text = tashkeel_text(text_to_format)

        if formatted_text:
            # مسح رسالة الانتظار ليبقى الشات مرتباً
            try: bot.delete_message(message.chat.id, wait_msg.message_id)
            except: pass

            reply = (
                "✅ <b>تم تشكيل النص بنجاح:</b>\n\n"
                f"<code>{formatted_text}</code>\n\n"
                f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
            )
            
            # أزرار التحكم
            kb = types.InlineKeyboardMarkup()
            kb.row(types.InlineKeyboardButton("🔄 تشكيل نص آخر", callback_data="go_tashkeel"))
            # هذا الزر سيمسح هذه الرسالة ويرسل الـ Start من جديد (start_handler.py)
            kb.row(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_start"))
            
            bot.send_message(message.chat.id, reply, parse_mode="HTML", reply_markup=kb)
        else:
            # في حال حدوث خطأ في السيرفر
            try: bot.delete_message(message.chat.id, wait_msg.message_id)
            except: pass
            
            bot.send_message(
                message.chat.id, 
                "❌ عذراً، فشل الاتصال بسيرفر التشكيل. حاول لاحقاً.",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_start")
                )
            )
