import random
import requests
import re
from telebot import types

# قاموس لتتبع حالة المستخدمين
user_states = {}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def pinterest_handler(bot):

    # 1. عند الضغط على زر "قسم بينترست"
    @bot.callback_query_handler(func=lambda c: c.data == "go_pin")
    def pin_welcome(call):
        uid = call.from_user.id
        # تفعيل حالة الانتظار لهذا المستخدم
        user_states[uid] = "waiting_for_pin"
        
        text = (
            "<b>🎯 مرحباً بك في قسم تحميل Pinterest</b>\n\n"
            "هذا القسم مخصص لتحميل الفيديوهات من بينترست بأعلى جودة.\n\n"
            "ℹ️ <b>كيفية الاستخدام:</b>\n"
            "1. اذهب إلى تطبيق Pinterest.\n"
            "2. اختر الفيديو الذي تريده وانقر على 'نسخ الرابط'.\n"
            "3. قم بلصق الرابط هنا في المحادثة مباشرة.\n\n"
            "<b>انتظر إرسال الرابط منك الآن... 📥</b>"
        )
        
        k = types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("🔙 إلغاء والعودة", callback_data="main_start"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=k)

    # 2. إلغاء الحالة عند العودة
    @bot.callback_query_handler(func=lambda c: c.data == "cancel_pin")
    def cancel_pin(call):
        uid = call.from_user.id
        user_states.pop(uid, None) # حذف الحالة
        # هنا تضع كود العودة لقائمتك الرئيسية
        bot.edit_message_text("<b>تم إلغاء العملية والعودة للقائمة الرئيسية.</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")

    # 3. معالجة الروابط (بشرط أن يكون المستخدم ضغط الزر أولاً)
    @bot.message_handler(func=lambda message: message.text and 
                         ("pinterest.com" in message.text or "pin.it" in message.text) and 
                         user_states.get(message.from_user.id) == "waiting_for_pin")
    def handle_pinterest_url(message):
        uid = message.from_user.id
        url = message.text
        
        status_msg = bot.reply_to(message, "<b>جاري المعالجة... ⏳</b>", parse_mode="HTML")
        
        try:
            bot.edit_message_text("<b>جاري استخراج الفيديو... 📥</b>", message.chat.id, status_msg.message_id, parse_mode="HTML")
            
            data = {'url': url}
            response = requests.post('https://pinterestvideodownloader.com/download.php', headers=headers, data=data).text
            video_url = re.findall(r'<video src="(.*?)"', response)
            
            if video_url:
                v_url = video_url[0]
                file_info = requests.head(v_url)
                size_bytes = int(file_info.headers.get('content-length', 0))
                size_mb = round(size_bytes / (1024 * 1024), 2)
                bot.edit_message_text("<b>اكتمل التحميل! ✅</b>", message.chat.id, status_msg.message_id, parse_mode="HTML")
                
                caption = (
                    f"<b>🎬 تم تحميل الفيديو بنجاح</b>\n\n"
                    f"📦 <b>الحجم:</b> <code>{size_mb} MB</code>\n"
                    f"📌 <b>المصدر:</b> <code>Pinterest</code>\n"
                    f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
                )
                
                bot.send_video(message.chat.id, v_url, caption=caption, parse_mode="HTML")
                bot.delete_message(message.chat.id, status_msg.message_id)
                
                # اختياري: إلغاء الحالة بعد التحميل بنجاح
                # user_states.pop(uid, None) 
            else:
                bot.reply_to(message, "❌ لم يتم العثور على فيديو.")
                
        except Exception as e:
            bot.edit_message_text("⚠️ حدث خطأ.", message.chat.id, status_msg.message_id)
