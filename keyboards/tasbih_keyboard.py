from telebot import types

def get_tasbih_keyboard():
    k = types.InlineKeyboardMarkup(row_width=2)
    k.add(
        types.InlineKeyboardButton("✨ تسبيح الزهراء", callback_data="start_zahra"),
        types.InlineKeyboardButton("📿 100 صلاة", callback_data="start_salawat"),
        types.InlineKeyboardButton("🌅 أذكار الصباح", callback_data="azkar_sabah_0"),
        types.InlineKeyboardButton("🌃 أذكار المساء", callback_data="azkar_massa_0"),
        types.InlineKeyboardButton("♾️ تسبيح مخصص", callback_data="custom_thikr"),
        types.InlineKeyboardButton("🎲 ذكر عشوائي", callback_data="random_thikr"),
        types.InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_start")
    )
    return k