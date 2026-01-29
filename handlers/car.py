import requests
from telebot import types

# دالة إرسال الصورة لموقع carnet.ai والتعرف عليها
def recognize_car(image_url):
    url = "https://carnet.ai/recognize-url"
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://carnet.ai',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Mobile Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    # إرسال رابط الصورة كبيانات للـ API
    try:
        r = requests.post(url, headers=headers, data=image_url, timeout=30)
        return r.json()
    except:
        return None

def car_handler(bot):

    # 1. عند الضغط على زر "فحص سيارة" في القائمة
    @bot.callback_query_handler(func=lambda c: c.data == "go_car_check")
    def ask_photo_car(call):
        bot.edit_message_text(
            "<b>🚗 خدمة التعرف على السيارات (AI)</b>\n\n"
            "✍️ يرجى إرسال صورة واضحة للسيارة:\n"
            "<i>(يفضل أن تكون الصورة من الأمام أو الجانب)</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        # ننتقل للخطوة التالية لاستلام الصورة
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, receive_car_photo)

    # 2. استلام الصورة ومعالجتها
    def receive_car_photo(message):
        if not message.photo:
            bot.send_message(message.chat.id, "❌ يرجى إرسال <b>صورة</b> للسيارة وليس نصاً!")
            return

        # إشعار المستخدم بالانتظار
        wait_msg = bot.send_message(message.chat.id, "⏳ جاري تحليل الصورة... انتظر قليلاً")
        bot.send_chat_action(message.chat.id, 'upload_photo')

        try:
            # الحصول على رابط الصورة من تليجرام
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

            # إرسال الرابط للـ API
            result = recognize_car(file_url)

            if not result or 'error' in result or 'car' not in result:
                bot.delete_message(message.chat.id, wait_msg.message_id)
                bot.send_message(message.chat.id, "❌ عذراً، لم أستطع التعرف على هذه السيارة. تأكد من وضوح الصورة.")
                return

            # استخراج البيانات
            car = result.get('car', {})
            carname = car.get('make', 'غير معروف')
            carmodel = car.get('model', 'غير معروف')
            years = car.get('years', 'غير معروف')
            angle = result.get('angle', {}).get('name', 'غير معروف')
            color = result.get('color', {}).get('name', 'غير معروف')

            reply = (
                "✅ <b>تم التعرف على السيارة بنجاح:</b>\n\n"
                f"• 🏢 الشركة: <b>{carname}</b>\n"
                f"• 🚘 الموديل: <b>{carmodel}</b>\n"
                f"• 📅 سنة الإصدار: <b>{years}</b>\n"
                f"• 🎨 اللون: <b>{color}</b>\n"
                f"• 📸 الزاوية: <b>{angle}</b>\n\n"
                f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
            )

            # إضافة أزرار خيارات
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔄 فحص سيارة أخرى", callback_data="go_car_check"))
            kb.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_start"))

            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.reply_to(message, reply, parse_mode="HTML", reply_markup=kb)

        except Exception as e:
            print(f"Car Error: {e}")
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, "❌ حدث خطأ أثناء الاتصال بسيرفر الفحص.")

