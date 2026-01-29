from telebot import types

def get_start_keyboard():
    k = types.InlineKeyboardMarkup(row_width=2)
    k.add(
        types.InlineKeyboardButton("📿 الأذكار", callback_data="go_tasbih"),
        types.InlineKeyboardButton("القرآن الكريم", callback_data="go_quran"),
        types.InlineKeyboardButton("💎 الزخرفة", callback_data="go_deco"),
        types.InlineKeyboardButton("📅 احسب عمرك", callback_data="go_age"),
        types.InlineKeyboardButton("📦 الضغط", callback_data="go_compress"),
        types.InlineKeyboardButton("📄 تحويل النصوص", callback_data="go_text"),
        types.InlineKeyboardButton("⚖️ التكليف الشرعي", callback_data="go_takleef"),
        types.InlineKeyboardButton("📌 Pinterest", callback_data="go_pin"),
        types.InlineKeyboardButton("🖼️ الصور", callback_data="show_menu"),
        types.InlineKeyboardButton("🎥 Tik Tok", callback_data="go_tiktok"),
        types.InlineKeyboardButton("📸 Instagram", callback_data="go_instagram"),
        types.InlineKeyboardButton("اختصار الرابط 📎", callback_data="go_shortener"),
        types.InlineKeyboardButton("Chat GPT 🤖", callback_data="go_gpt"),
        types.InlineKeyboardButton("🚗 التعرف على السيارة", callback_data="go_car_check"),
        types.InlineKeyboardButton("📑 تدوين مهام", callback_data="go_todo"),
        types.InlineKeyboardButton("✍🏻 تشكيل الكلمات", callback_data="go_tashkeel"),
        types.InlineKeyboardButton("📣 تذكيرات ", callback_data="go_reminders")
        
    )
    return k