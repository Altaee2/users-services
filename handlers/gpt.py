import requests
from telebot import types
from keyboards.main_keyboard import get_start_keyboard
# دالة جلب الإجابة من الذكاء الاصطناعي
def ask_gpt(question):
    try:
        # استخدام الـ API الذي قدمته
        url = f"https://chatgpt.apinepdev.workers.dev/?question={requests.utils.quote(question)}"
        r = requests.get(url, timeout=30).json()
        
        ans = r.get("answer", "لم أجد إجابة.")
        
        # تنظيف الإجابة من إعلانات المصدر
        ads = [
            "🔗 Join our community: [t.me/nepdevsz](https://t.me/nepdevsz)",
            "Join our community: t.me/nepdevsz",
            "t.me/nepdevsz"
        ]
        for ad in ads:
            ans = ans.replace(ad, "")
            
        # إضافة حقوقك الخاصة
        footer = "\n\n🤍 تلجرام :- @altaee_z\n🌐 موقعي : www.ali-Altaee.free.nf"
        return ans.strip() + footer
    except Exception as e:
        print(f"GPT Error: {e}")
        return None

def gpt_handler(bot):

    # 1. عند الضغط على زر "اسأل الذكاء الاصطناعي"
    @bot.callback_query_handler(func=lambda c: c.data == "go_gpt")
    def ask_question_start(call):
        bot.edit_message_text(
            "<b>🤖 مرحبا بك في قسم الذكاء الاصطناعي (GPT)</b>\n\n"
            "✍️ أرسل سؤالك أو أي شيء تريد مني كتابته:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, receive_gpt_question)

    # 2. استلام السؤال ومعالجته
    def receive_gpt_question(message):
        question = message.text.strip()
        
        if len(question) < 2:
            bot.send_message(message.chat.id, "❌ يرجى كتابة سؤال واضح.")
            return

        # إرسال حالة "جاري الكتابة" لإعطاء انطباع واقعي
        bot.send_chat_action(message.chat.id, 'typing')
        wait_msg = bot.send_message(message.chat.id, "🤔 جاري التفكير... انتظر لحظة")

        answer = ask_gpt(question)

        if answer:
            # إضافة زر "اسأل سؤالاً آخر" وزر "رجوع"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔄 سؤال آخر", callback_data="go_gpt"))
            kb.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="start_handler"))
            
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, answer, reply_markup=kb)
        else:
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, "❌ عذراً، الذكاء الاصطناعي مشغول حالياً. حاول لاحقاً.")

