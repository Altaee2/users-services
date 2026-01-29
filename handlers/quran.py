from telebot import types
import json, os

QURAN_IMG = "https://quran.ksu.edu.sa/png_big/"
DATA_PATH = "data/quran_index.json"
USERS_PATH = "data/quran_users.json"

# تحميل الفهرس
with open(DATA_PATH, "r", encoding="utf-8") as f:
    QURAN_INDEX = json.load(f)

# تحميل المستخدمين
if not os.path.exists("data"): os.makedirs("data")
if not os.path.exists(USERS_PATH):
    with open(USERS_PATH, "w") as f: json.dump({}, f)

def load_users():
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_sura_by_page(page):
    last = QURAN_INDEX[0]
    for item in QURAN_INDEX:
        if page >= item["page"]:
            last = item
    return last["sura"]

def youtube_link(sura):
    return f"https://www.youtube.com/results?search_query=سورة+{sura}"

def quran_handler(bot):

    # قائمة القرآن الرئيسية
    def quran_menu():
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📑 فهرس السور", callback_data="quran_index"),
            types.InlineKeyboardButton("🔁 آخر صفحة", callback_data="quran_last")
        )
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="main_start"))
        return kb

    # دخول القرآن
    @bot.callback_query_handler(func=lambda c: c.data == "go_quran")
    def quran_home(call):
        bot.edit_message_text(
            "📖 <b>القرآن الكريم</b>\n\n"
            "✍️ أرسل <b>رقم الصفحة</b> أو <b>اسم السورة</b> للبحث:\n"
            "مثال: <code>150</code> أو <code>الكهف</code>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=quran_menu()
        )

    # استقبال رقم صفحة أو اسم سورة
    @bot.message_handler(func=lambda m: True)
    def handle_quran_input(message):
        text = message.text.strip()
        
        # إذا كان المدخل رقماً (صفحة)
        if text.isdigit():
            page = int(text)
            if 1 <= page <= 604:
                send_page(message.chat.id, page, message.from_user.id)
            else:
                bot.reply_to(message, "❌ الصفحة من 1 إلى 604 فقط")
        
        # إذا كان المدخل نصاً (بحث عن سورة)
        else:
            found_page = None
            for item in QURAN_INDEX:
                if text in item["sura"] or text.replace("ال", "") in item["sura"]:
                    found_page = item["page"]
                    break
            
            if found_page:
                send_page(message.chat.id, found_page, message.from_user.id)
            else:
                # إذا لم يكن رقماً ولا اسماً معروفاً، لا نفعل شيئاً أو نرسل تنبيه بسيط
                pass

    # إرسال صفحة
    def send_page(chat_id, page, uid, msg_id=None):
        users = load_users()
        users[str(uid)] = page
        save_users(users)

        sura = get_sura_by_page(page)

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton(f"📄 صفحة: {page} | {sura}", callback_data="noop"))
        
        # أزرار التنقل
        nav_btns = []
        if page > 1:
            nav_btns.append(types.InlineKeyboardButton("⬅️ السابقة", callback_data=f"quran_{page-1}"))
        if page < 604:
            nav_btns.append(types.InlineKeyboardButton("➡️ التالية", callback_data=f"quran_{page+1}"))
        kb.add(*nav_btns)

        kb.add(
            types.InlineKeyboardButton("🔊 استماع", url=youtube_link(sura)),
            types.InlineKeyboardButton("📑 الفهرس", callback_data="quran_index")
        )
        kb.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_start"))

        img_url = f"{QURAN_IMG}{page}.png"
        
        try:
            if msg_id:
                bot.edit_message_media(
                    types.InputMediaPhoto(img_url),
                    chat_id, msg_id, reply_markup=kb
                )
            else:
                bot.send_photo(chat_id, img_url, reply_markup=kb)
        except Exception as e:
            bot.send_message(chat_id, f"حدث خطأ في عرض الصفحة: {page}")

    # تنقل الصفحات (تم إصلاح الفلتر هنا)
    @bot.callback_query_handler(func=lambda c: c.data.startswith("quran_") and c.data.split("_")[1].isdigit())
    def nav(call):
        page = int(call.data.split("_")[1])
        send_page(call.message.chat.id, page, call.from_user.id, call.message.message_id)

    # آخر صفحة محفوظة
    @bot.callback_query_handler(func=lambda c: c.data == "quran_last")
    def last_page(call):
        users = load_users()
        uid = str(call.from_user.id)
        if uid in users:
            send_page(call.message.chat.id, users[uid], call.from_user.id)
        else:
            bot.answer_callback_query(call.id, "❌ لم تقرأ أي صفحة بعد", show_alert=True)

    # فهرس السور
    @bot.callback_query_handler(func=lambda c: c.data == "quran_index")
    def index(call):
        # إذا كانت الرسالة الحالية تحتوي على صورة، نحذفها ونرسل الفهرس كرسالة نصية جديدة
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        kb = types.InlineKeyboardMarkup(row_width=3)
        btns = []
        used = set()
        for item in QURAN_INDEX:
            if item["sura"] not in used:
                btns.append(types.InlineKeyboardButton(item["sura"], callback_data=f"jump_{item['page']}"))
                used.add(item["sura"])
        
        kb.add(*btns[:99]) 
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_quran"))

        bot.send_message(call.message.chat.id, "📑 <b>فهرس السور</b>\nاضغط على اسم السورة للانتقال:", 
                         parse_mode="HTML", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("jump_"))
    def jump(call):
        page = int(call.data.split("_")[1])
        # نرسلها كرسالة جديدة لأن الفهرس نص والصفحة صورة
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_page(call.message.chat.id, page, call.from_user.id)
