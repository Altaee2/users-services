from telebot import types
from datetime import datetime, timedelta
import json, random
from keyboards.tasbih_keyboard import get_tasbih_keyboard
from keyboards.main_keyboard import get_start_keyboard
import os
import json


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AZKAR_PATH = os.path.join(BASE_DIR, "data", "azkar.json")
with open(AZKAR_PATH, "r", encoding="utf-8") as f:
    azkar_data = json.load(f)

user_data = {}

def tasbih_handler(bot, user_data):

    @bot.callback_query_handler(func=lambda c: c.data == "go_tasbih")
    def tasbih_home(call):
        uid = call.from_user.id
        user_data.setdefault(uid, {
            "zahra_step": 0, "zahra_count": 0,
            "salawat": 0, "custom_count": 0
        })

        now = datetime.utcnow() + timedelta(hours=3)
        hour = now.hour
        time_now = now.strftime("%I:%M %p").replace("AM", "صباحاً").replace("PM", "مساءً")

        if 5 <= hour < 12: status = "🌅 وقت أذكار الصباح"
        elif 12 <= hour < 17: status = "📿 وقت التسبيح والاستغفار"
        elif 17 <= hour < 21: status = "🌃 وقت أذكار المساء"
        else: status = "🌙 وقت الاستغفار والذكر"

        text = (
            "<b>✨ قسم الأذكار والتسبيح</b>\n\n"
            "﴿ أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ ﴾\n\n"
            f"📌 <b>الآن:</b> {status}\n"
            f"⏰ <b>توقيت بغداد:</b> <code>{time_now}</code>"
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_tasbih_keyboard(),
            parse_mode="HTML"
        )

    # تسبيح الزهراء (ع)
    @bot.callback_query_handler(func=lambda c: c.data in ["start_zahra", "inc_zahra"])
    def zahra(call):
        uid = call.from_user.id
        steps = [("الله أكبر", 34), ("سبحان الله", 33), ("الحمد لله", 34), ("لا إله إلا الله", 1)]

        if call.data == "start_zahra":
            user_data[uid]["zahra_step"] = 0
            user_data[uid]["zahra_count"] = 0

        if call.data == "inc_zahra":
            user_data[uid]["zahra_count"] += 1

        step, limit = steps[user_data[uid]["zahra_step"]]

        if user_data[uid]["zahra_count"] >= limit:
            if user_data[uid]["zahra_step"] == len(steps) - 1:
                user_data[uid]["zahra_step"] = 0
                user_data[uid]["zahra_count"] = 0
                bot.edit_message_text(
                    "🎊 <b>هنيئاً لك، أتممت تسبيح الزهراء (ع)</b>",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=get_tasbih_keyboard(),
                    parse_mode="HTML"
                )
                return
            user_data[uid]["zahra_step"] += 1
            user_data[uid]["zahra_count"] = 0

        progress = int((user_data[uid]["zahra_count"] / limit) * 10)
        bar = "🟢" * progress + "⚪" * (10 - progress)

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(f"{step} ({user_data[uid]['zahra_count']}/{limit})", callback_data="inc_zahra"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_tasbih"))

        bot.edit_message_text(
            f"<b>📿 تسبيح الزهراء (ع)</b>\n\n<blockquote>{step}</blockquote>\n<b>التقدم:</b> <code>{bar}</code>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )

    # الصلوات
    @bot.callback_query_handler(func=lambda c: c.data in ["start_salawat", "inc_salawat"])
    def salawat(call):
        uid = call.from_user.id
        if call.data == "inc_salawat":
            user_data[uid]["salawat"] += 1

        if user_data[uid]["salawat"] >= 100:
            user_data[uid]["salawat"] = 0
            bot.answer_callback_query(call.id, "✅ أتممت 100 صلاة", show_alert=True)
            return

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(f"{user_data[uid]['salawat']}/100", callback_data="inc_salawat"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_tasbih"))

        bot.edit_message_text(
            "📿 <b>اللهم صل على محمد وآل محمد</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )

    # ذكر عشوائي
    @bot.callback_query_handler(func=lambda c: c.data == "random_thikr")
    def random_thikr(call):
        bot.answer_callback_query(call.id, random.choice(azkar_data["random"]), show_alert=True)

    # أذكار صباح / مساء
    @bot.callback_query_handler(func=lambda c: c.data.startswith("azkar_"))
    def azkar(call):
        _, typ, idx = call.data.split("_")
        idx = int(idx)

        if idx >= len(azkar_data[typ]):
            bot.edit_message_text("✅ تمت الأذكار بحمد الله", call.message.chat.id, call.message.message_id,
                                  reply_markup=get_tasbih_keyboard(), parse_mode="HTML")
            return

        item = azkar_data[typ][idx]
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➡️ التالي", callback_data=f"azkar_{typ}_{idx+1}"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_tasbih"))

        bot.edit_message_text(
            f"<b>{'🌅 أذكار الصباح' if typ=='sabah' else '🌃 أذكار المساء'}</b>\n\n"
            f"<blockquote>{item['text']}</blockquote>\n"
            f"🔢 التكرار: <code>{item['count']}</code>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )