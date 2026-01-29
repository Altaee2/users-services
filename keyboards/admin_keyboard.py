from telebot import types

def admin_panel():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 إحصائيات", callback_data="stats"),
        types.InlineKeyboardButton("📁 تصدير CSV", callback_data="export_csv")
    )
    kb.add(
        types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast"),
        types.InlineKeyboardButton("🔐 إعدادات الاشتراك", callback_data="sub_settings")
    )
    kb.add(
        types.InlineKeyboardButton("🚫 حظر", callback_data="ban"),
        types.InlineKeyboardButton("✅ إلغاء حظر", callback_data="unban")
    )
    return kb