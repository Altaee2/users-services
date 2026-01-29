from telebot import types

def get_deco_keyboard():
    k = types.InlineKeyboardMarkup(row_width=2)
    k.add(
        types.InlineKeyboardButton("🇬🇧 زخرفة إنجليزي", callback_data="deco_eng"),
        types.InlineKeyboardButton("🇮🇶 زخرفة عربي", callback_data="deco_ar")
    )
    k.add(
        types.InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="main_start")
    )
    return k