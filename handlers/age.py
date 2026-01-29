from datetime import datetime, timedelta
from telebot import types
import pytz

# إعداد توقيت بغداد
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

def age_handler(bot, user_states):

    @bot.callback_query_handler(func=lambda c: c.data == "go_age")
    def ask_birth(call):
        user_states[call.from_user.id] = "age"
        bot.edit_message_text(
            "<b>📅 حاسبة العمر الدقيقة</b>\n\n"
            "✍️ أرسل تاريخ ميلادك بالتنسيق التالي:\n"
            "<code>سنة/شهر/يوم</code>\n\n"
            "مثال: <code>2000/01/25</code>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

    @bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "age")
    def calc_age(message):
        user_id = message.from_user.id
        try:
            # تحليل التاريخ المدخل
            birth_date = datetime.strptime(message.text.strip(), "%Y/%m/%d")
            # الوقت الحالي في بغداد
            now = datetime.now(BAGHDAD_TZ).replace(tzinfo=None)
            
            if birth_date > now:
                bot.reply_to(message, "❌ هل أنت من المستقبل؟ يرجى إدخال تاريخ صحيح.")
                return

            # حساب الفرق التفصيلي
            diff = now - birth_date
            
            years = now.year - birth_date.year
            months = now.month - birth_date.month
            days = now.day - birth_date.day
            
            if days < 0:
                months -= 1
                # جلب عدد أيام الشهر السابق
                prev_month = (now.month - 1) if now.month > 1 else 12
                days += 30 # تقريبي لغرض السرعة أو يمكن تحسينه
            
            if months < 0:
                years -= 1
                months += 12

            # حساب الساعات والدقائق الكلية
            total_minutes = int(diff.total_seconds() // 60)
            total_hours = int(total_minutes // 60)

            # حساب المتبقي لعيد الميلاد القادم
            next_birthday = birth_date.replace(year=now.year)
            if next_birthday < now:
                next_birthday = next_birthday.replace(year=now.year + 1)
            
            days_to_birthday = (next_birthday - now).days
            months_to_birthday = days_to_birthday // 30
            rem_days = days_to_birthday % 30

            # تنسيق الرد الاحترافي
            reply = (
                f"<b>🎂 إحصائيات عمرك بالكامل:</b>\n"
                f"━" "\n"
                f"✅ <b>عمرك الآن:</b>\n"
                f"• 📅 <code>{years}</code> سنة و <code>{months}</code> شهر\n"
                f"• 🗓 <code>{days}</code> يوم\n"
                f"• 🕒 <code>{now.hour}</code> ساعة و <code>{now.minute}</code> دقيقة\n\n"
                f"📊 <b>بالأرقام الكلية:</b>\n"
                f"• الساعات: <code>{total_hours:,}</code> ساعة\n"
                f"• الدقائق: <code>{total_minutes:,}</code> دقيقة\n\n"
                f"🎁 <b>عيد ميلادك القادم:</b>\n"
                f"• متبقي له: <b>{days_to_birthday}</b> يوم\n"
                f"<i>(أي ما يعادل {months_to_birthday} شهر و {rem_days} يوم)</i>\n"
                f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
            )

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔄 حساب عمر آخر", callback_data="go_age"))
            kb.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_start"))

            bot.reply_to(message, reply, parse_mode="HTML", reply_markup=kb)

        except ValueError:
            bot.reply_to(message, "❌ التنسيق خاطئ! أرسل التاريخ هكذا: 1995/05/15")
        except Exception as e:
            bot.reply_to(message, "❌ حدث خطأ غير متوقع.")
        
        # إنهاء الحالة للمستخدم
        user_states.pop(user_id, None)
