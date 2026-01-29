import requests
import re
import json
import os
from datetime import datetime, timedelta
from telebot import types
from keyboards.main_keyboard import get_start_keyboard

# --- الإعدادات الثابتة ---
ADMIN_ID = 6454550864
USERS_FILE = 'users.json'
CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f: json.dump({"channel": "@تغيير_القناة_هنا"}, f)
    with open(CONFIG_FILE, 'r') as f: return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f: json.dump(config, f)

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f: json.dump({}, f)
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def get_sistani_hijri():
    url = "https://www.sistani.org"
    try:
        response = requests.get(url, timeout=5)
        res = re.search(r'style="margin-left:9px;">([^<]+)</span>', response.text)
        return res.group(1).strip() if res else "تعذر جلب التاريخ"
    except: return "غير متوفر حالياً"

def start_handler(bot):

    # --- التحقق من الاشتراك الإجباري ---
    def check_sub(user_id):
        config = load_config()
        channel = config['channel']
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['member', 'administrator', 'creator']:
                return True
            return False
        except: return True 

    # --- تسجيل مستخدم جديد وإشعار المطور ---
    def register_user(user):
        users = load_users()
        uid = str(user.id)
        if uid not in users:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            users[uid] = {
                "name": user.first_name,
                "username": f"@{user.username}" if user.username else "لا يوجد",
                "joined_at": now_str,
                "is_banned": False
            }
            save_users(users)
            # إشعار دخول مستخدم جديد
            msg = (f"🔔 <b>مستخدم جديد دخل للبوت!</b>\n\n"
                   f"👤 الاسم: {user.first_name}\n"
                   f"🆔 الأيدي: <code>{user.id}</code>\n"
                   f"🔗 اليوزر: @{user.username if user.username else 'لا يوجد'}\n"
                   f"📅 التاريخ: {now_str}")
            try: bot.send_message(ADMIN_ID, msg, parse_mode="HTML")
            except: pass

    # --- إشعار الحظر أو مغادرة القناة ---
    @bot.my_chat_member_handler()
    def status_handler(update):
        new = update.new_chat_member
        user = update.from_user
        if new.status == 'kicked': # إذا حظر البوت
            msg = f"🚫 <b>المستخدم قام بحظر البوت!</b>\n👤 الاسم: {user.first_name}\n🆔 الأيدي: <code>{user.id}</code>"
            try: bot.send_message(ADMIN_ID, msg, parse_mode="HTML")
            except: pass

    # --- دالة البداية ---
    def send_welcome_logic(chat_id, user, message_id=None):
        uid = str(user.id)
        users = load_users()
        user_name = user.first_name
        user_id = user.id
        username = f"@{user.username}" if user.username else "لا يوجد"
        if uid in users and users[uid].get('is_banned'):
            bot.send_message(chat_id, "❌ عذراً، لقد تم حظرك من استخدام البوت.")
            return

        if not check_sub(user.id):
            config = load_config()
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("اضغط هنا للاشتراك", url=f"https://t.me/{config['channel'].replace('@','')}"))
            kb.add(types.InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="main_start"))
            bot.send_message(chat_id, f"⚠️ يجب عليك الاشتراك في قناة البوت أولاً:\n{config['channel']}", reply_markup=kb)
            return

        register_user(user)
        
        main_kb = get_start_keyboard()
        if user.id == ADMIN_ID:
            # إضافة زر الأدمن إذا لم يكن موجوداً
            is_admin_btn_exists = any(b.callback_data == "admin_panel" for row in main_kb.keyboard for b in row)
            if not is_admin_btn_exists:
                main_kb.add(types.InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel"))

        now = datetime.utcnow() + timedelta(hours=3)
        time_24 = now.strftime("%H:%M:%S")
        time_12 = now.strftime("%I:%M:%S %p").replace("AM", "صباحاً").replace("PM", "مساءً")
        day_name_en = now.strftime("%A")

        days_ar = {
            "Monday": "الأثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
            "Thursday": "الخميس", "Friday": "الجمعة",
            "Saturday": "السبت", "Sunday": "الأحد"
        }

        months_miladi = [
            "", "كانون الثاني", "شباط", "آذار", "نيسان", "أيار",
            "حزيران", "تموز", "آب", "أيلول",
            "تشرين الأول", "تشرين الثاني", "كانون الأول"
        ]

        date_miladi_str = f"{now.day} {months_miladi[now.month]} {now.year}"

        date_hijri_str = get_sistani_hijri()

        welcome_html = (
            f"<b>✨ أهلاً بك يا {user_name} في بوت الخدمات الشامل</b>\n\n"
            f"<b>👤 معلوماتك:</b>\n"
            f"• اليوزر: {username}\n"
            f"• الأيدي: <code>{user_id}</code>\n\n"
            f"<b>📅 تاريخ اليوم:</b>\n"
            f"• اليوم: <b>{days_ar.get(day_name_en)}</b>\n"
            f"• ميلادي: <b>{date_miladi_str}</b>\n"
            f"• هجري: <b>{date_hijri_str}</b>\n\n"
            f"<b>⏰ الوقت الحالي (بتوقيت بغداد):</b>\n"
            f"• نظام 12H: <code>{time_12}</code>\n"
            f"• نظام 24H: <code>{time_24}</code>\n\n"
            f"<b>🛠 ماذا يقدم البوت؟</b>\n"
            f"يقدم البوت خدمات دينية، تقنية، وخدمات صور متقدمة.\n\n"
            f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"
        )

        if message_id:
            try: bot.delete_message(chat_id, message_id)
            except: pass
        
        bot.send_message(chat_id, welcome_html, reply_markup=main_kb, parse_mode="HTML", disable_web_page_preview=True)

    @bot.message_handler(commands=['start'])
    def start(message):
        send_welcome_logic(message.chat.id, message.from_user)

    @bot.callback_query_handler(func=lambda c: c.data == "main_start")
    def back_to_main(call):
        send_welcome_logic(call.message.chat.id, call.from_user, message_id=call.message.message_id)

    # --- لوحة التحكم ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_panel" and c.from_user.id == ADMIN_ID)
    def admin_panel(call):
        users = load_users()
        banned = sum(1 for u in users.values() if u.get('is_banned', False))
        
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="admin_broadcast"),
               types.InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats"))
        kb.add(types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"),
               types.InlineKeyboardButton("✅ فك حظر", callback_data="admin_unban"))
        kb.add(types.InlineKeyboardButton("📝 تصدير TXT", callback_data="admin_export"),
               types.InlineKeyboardButton("📡 القناة", callback_data="admin_channel"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="main_start"))

        text = (f"<b>🛠 لوحة التحكم</b>\n\n"
                f"👤 المستخدمين: {len(users)}\n"
                f"🚫 المحظورين: {banned}")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

    # --- الإذاعة ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast" and c.from_user.id == ADMIN_ID)
    def start_broadcast(call):
        msg = bot.send_message(call.message.chat.id, "📢 أرسل الإذاعة (نص أو ميديا):")
        bot.register_next_step_handler(msg, perform_broadcast)

    def perform_broadcast(message):
        users = load_users()
        s, f = 0, 0
        for uid in users:
            try:
                bot.copy_message(uid, message.chat.id, message.message_id)
                s += 1
            except: f += 1
        bot.send_message(message.chat.id, f"✅ انتهى:\nنجاح: {s}\nفشل: {f}")

    # --- التصدير (مع حل مشكلة الـ KeyError) ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_export" and c.from_user.id == ADMIN_ID)
    def export_users(call):
        users = load_users()
        file_path = "users.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"قائمة المستخدمين - العدد: {len(users)}\n\n")
            for uid, info in users.items():
                name = info.get('name', 'غير معروف')
                user = info.get('username', 'لا يوجد')
                date = info.get('joined_at', 'تاريخ قديم')
                f.write(f"ID: {uid} | Name: {name} | User: {user} | Joined: {date}\n")
        
        with open(file_path, "rb") as f:
            bot.send_document(call.message.chat.id, f, caption="✅ ملف المستخدمين")
        os.remove(file_path)

    # --- تغيير القناة ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_channel" and c.from_user.id == ADMIN_ID)
    def change_channel_step(call):
        msg = bot.send_message(call.message.chat.id, "📡 أرسل معرف القناة الجديد (مع @):")
        bot.register_next_step_handler(msg, save_new_channel)

    def save_new_channel(message):
        if message.text.startswith("@"):
            config = load_config()
            config['channel'] = message.text.strip()
            save_config(config)
            bot.send_message(message.chat.id, f"✅ تم التغيير إلى: {message.text}")
        else: bot.send_message(message.chat.id, "❌ خطأ في المعرف!")
    # --- لوحة التحكم ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_panel" and c.from_user.id == ADMIN_ID)
    def admin_panel(call):
        users = load_users()
        banned_count = sum(1 for u in users.values() if u.get('is_banned', False))
        
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("📢 إذاعة", callback_data="admin_broadcast"),
               types.InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats"))
        kb.add(types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"),
               types.InlineKeyboardButton("✅ فك حظر", callback_data="admin_unban"))
        kb.add(types.InlineKeyboardButton("📝 تصدير TXT", callback_data="admin_export"),
               types.InlineKeyboardButton("📡 القناة", callback_data="admin_channel"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="main_start"))

        text = (f"<b>🛠 لوحة التحكم الخاصة بالمطور</b>\n\n"
                f"👤 المستخدمين: {len(users)}\n"
                f"🚫 المحظورين: {banned_count}")
        try: bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
        except: pass

    # --- 📊 قسم الإحصائيات المفصلة ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_stats" and c.from_user.id == ADMIN_ID)
    def show_stats(call):
        users = load_users()
        total = len(users)
        banned_list = [f"<code>{uid}</code> ({u.get('username', 'بدون يوزر')})" for uid, u in users.items() if u.get('is_banned', False)]
        banned_count = len(banned_list)
        active_count = total - banned_count
        
        banned_text = "\n".join(banned_list) if banned_list else "لا يوجد محظورين"

        text = (
            f"<b>📊 إحصائيات البوت</b>\n\n"
            f"👥 المستخدمين: {total}\n"
            f"🚫 المحظورين: {banned_count}\n"
            f"🔔 المشتركين النشطين: {active_count}\n\n"
            f"<b>🚫 قائمة المحظورين:</b>\n{banned_text}"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

    # --- 🚫 قسم الحظر ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_ban" and c.from_user.id == ADMIN_ID)
    def ban_prompt(call):
        msg = bot.send_message(call.message.chat.id, "🚫 <b>أرسل أيدي (ID) الشخص المراد حظره:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_ban)

    def process_ban(message):
        uid = message.text.strip()
        users = load_users()
        if uid in users:
            users[uid]['is_banned'] = True
            save_users(users)
            bot.send_message(message.chat.id, f"✅ تم حظر المستخدم <code>{uid}</code> بنجاح.", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ هذا الأيدي غير موجود في قاعدة البيانات.")

    # --- ✅ قسم فك الحظر ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_unban" and c.from_user.id == ADMIN_ID)
    def unban_prompt(call):
        msg = bot.send_message(call.message.chat.id, "✅ <b>أرسل أيدي (ID) الشخص لفك الحظر عنه:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_unban)

    def process_unban(message):
        uid = message.text.strip()
        users = load_users()
        if uid in users:
            users[uid]['is_banned'] = False
            save_users(users)
            bot.send_message(message.chat.id, f"✅ تم فك الحظر عن المستخدم <code>{uid}</code>.", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ الأيدي غير موجود.")

    # --- 📢 الإذاعة المتطورة ---
    @bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast" and c.from_user.id == ADMIN_ID)
    def start_broadcast(call):
        msg = bot.send_message(call.message.chat.id, "📢 أرسل رسالة الإذاعة (نص، صورة، فيديو، ملف):")
        bot.register_next_step_handler(msg, perform_broadcast)

    def perform_broadcast(message):
        users = load_users()
        success, fail = 0, 0
        for uid in users:
            try:
                bot.copy_message(uid, message.chat.id, message.message_id)
                success += 1
            except: fail += 1
        bot.send_message(message.chat.id, f"<b>✅ اكتملت الإذاعة</b>\n\n• نجاح: {success}\n• فشل: {fail}", parse_mode="HTML")
