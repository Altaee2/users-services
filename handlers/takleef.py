from telebot import types
from datetime import datetime
from hijri_converter import Gregorian, Hijri

# قائمة أسماء الأشهر الهجرية
HIJRI_MONTHS = [
    "محرم", "صفر", "ربيع الأول", "ربيع الثاني", 
    "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان", 
    "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
]

user_context = {}

def get_now_dates():
    now = datetime.now()
    h = Gregorian(now.year, now.month, now.day).to_hijri()
    return now, h

def calculate_diff(start_date, end_date):
    years = end_date.year - start_date.year
    months = end_date.month - start_date.month
    days = end_date.day - start_date.day
    
    if days < 0:
        months -= 1
        days += 30 
    if months < 0:
        years -= 1
        months += 12
    return years, months, days

def takleef_handler(bot):
    @bot.callback_query_handler(func=lambda c: c.data == "go_takleef")
    def takleef(call):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("👦🏻 ذكر", callback_data="gender_male"),
            types.InlineKeyboardButton("🧕🏻 أنثى", callback_data="gender_female"),
            types.InlineKeyboardButton("الرجوع", callback_data="main_start")
        )
        now_m, now_h = get_now_dates()
        month_name = HIJRI_MONTHS[now_h.month - 1]
        
        bot.send_message(
            call.message.chat.id,
            f"⚖️ **حساب التكليف الشرعي**\n"
            f"📅 ميلادي: {now_m.strftime('%Y/%m/%d')}\n"
            f"🌙 هجري: {now_h.day} {month_name} {now_h.year}\n\n"
            f"اختر الجنس لبدء الحساب:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda c: c.data in ["gender_male", "gender_female"])
    def choose_gender(call):
        uid = call.from_user.id
        gender = "male" if call.data == "gender_male" else "female"
        user_context[uid] = {"gender": gender, "step": "year", "birth": {}, "msg_id": call.message.message_id}
        
        bot.edit_message_text(
            "📍 أرسل الآن **سنة ميلادك الميلادية** (مثلاً: 2005):",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )

    @bot.message_handler(func=lambda message: message.from_user.id in user_context)
    def handle_birth_message(message):
        uid = message.from_user.id
        text = message.text.strip()
        chat_id = message.chat.id
        ctx = user_context[uid]

        try:
            if "/" in text and len(text.split("/")) == 3:
                y, m, d = map(int, text.split("/"))
                ctx["birth"] = {"year": y, "month": m, "day": d}
            else:
                if ctx["step"] == "year":
                    ctx["birth"]["year"] = int(text); ctx["step"] = "month"
                    bot.edit_message_text("✅ أرسل الآن **شهر الميلاد** (1-12):", chat_id, ctx["msg_id"]); return
                elif ctx["step"] == "month":
                    ctx["birth"]["month"] = int(text); ctx["step"] = "day"
                    bot.edit_message_text("✅ أرسل الآن **يوم الميلاد** (1-31):", chat_id, ctx["msg_id"]); return
                elif ctx["step"] == "day":
                    ctx["birth"]["day"] = int(text)

            b = ctx["birth"]
            birth_g = datetime(b['year'], b['month'], b['day'])
            birth_h = Gregorian(b['year'], b['month'], b['day']).to_hijri()
            now_m, now_h = get_now_dates()
            
            age_m_y, age_m_m, age_m_d = calculate_diff(birth_g, now_m)
            age_h_y, age_h_m, age_h_d = calculate_diff(birth_h, now_h)
            
            gender = ctx["gender"]
            takleef_limit_h = 15 if gender == "male" else 9
            takleef_date_h = Hijri(birth_h.year + takleef_limit_h, birth_h.month, birth_h.day)
            takleef_date_g = takleef_date_h.to_gregorian()
            
            is_mukallaf = age_h_y >= takleef_limit_h
            
            if is_mukallaf:
                p_y, p_m, p_d = calculate_diff(takleef_date_g, now_m)
                status_msg = f"✅ **أنت مكلف شرعاً منذ:**\n{p_y} سنة و {p_m} شهر و {p_d} يوم"
            else:
                r_y, r_m, r_d = calculate_diff(now_m, takleef_date_g)
                status_msg = f"⏳ **متبقي على تكليفك:**\n{r_y} سنة و {r_m} شهر و {r_d} يوم"

            # رسالة مخصصة حسب الجنس
            advice = (
                "🔹 **عزيزي الشاب:** بلوغك السن الشرعي يعني أنك أصبحت رجلاً مسؤولاً أمام الله عن أفعالك، فاحرص على الصلاة في وقتها."
                if gender == "male" else
                "🔹 **ابنتي العزيزة:** التكليف هو تشريف إلهي لكِ، فقد أصبحتِ الآن أهلاً لمخاطبة الله لكِ بالواجبات، فزيني روحكِ بالعفة والطاعة."
            )

            res = (
                f"📋 **تقرير التكليف الشرعي**\n"
                f"━━━━━━━━━━━━\n"
                f"👤 الجنس: {'ذكر' if gender=='male' else 'أنثى'}\n\n"
                f"🎂 **عمرك الحالي:**\n"
                f"• ميلادي: {age_m_y} سنة، {age_m_m} شهر، {age_m_d} يوم\n"
                f"• هجري: {age_h_y} سنة، {age_h_m} شهر ({HIJRI_MONTHS[birth_h.month-1]})، {age_h_d} يوم\n\n"
                f"⚖️ **سن التكليف:** {takleef_limit_h} سنة هجرية\n"
                f"📅 **تاريخ بلوغك التكليف:**\n"
                f"• هجري: {takleef_date_h.day} {HIJRI_MONTHS[takleef_date_h.month-1]} {takleef_date_h.year}\n"
                f"• ميلادي: {takleef_date_g.strftime('%Y/%m/%d')}\n\n"
                f"{status_msg}\n\n"
                f"{advice}\n"
                f"━━━━━━━━━━━━\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
            )
            
            bot.send_message(chat_id, res, parse_mode="Markdown", disable_web_page_preview=True)
            del user_context[uid]

        except Exception:
            bot.send_message(chat_id, "❌ خطأ في إدخال البيانات، يرجى المحاولة مجدداً.")
            if uid in user_context: del user_context[uid]
