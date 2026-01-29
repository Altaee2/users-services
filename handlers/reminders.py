import json
import os
import threading
import time
from datetime import datetime, timedelta
from telebot import types

# --- الإعدادات الأساسية ---
REMINDERS_FILE = 'data/reminders.json'
TEMP_DATA = {} # لتخزين البيانات مؤقتاً أثناء عملية الإضافة لمنع أخطاء الأزرار

def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_reminders(data):
    with open(REMINDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def reminders_handler(bot):

    # --- 1. محرك التنبيه الذكي (يفحص كل 30 ثانية) ---
    def check_reminders_loop():
        while True:
            try:
                # جلب الوقت الحالي بتنسيق مطابق للمخزن (توقيت بغداد 12 ساعة)
                now = datetime.now()
                now_str = now.strftime("%Y-%m-%d %-I:%M %p").replace("AM", "صباحاً").replace("PM", "مساءً")
                
                data = load_reminders()
                updated = False

                for uid, user_rems in data.items():
                    for rem in user_rems[:]:
                        # جلب الوقت من الحقل الجديد أو القديم لضمان عدم حدوث خطأ
                        rem_time = rem.get('datetime') or rem.get('time')
                        
                        if rem_time == now_str:
                            alert_text = (
                                f"🔔 <b>تذكير عاجل!</b>\n"
                                f"━━━━━━━━━━━━━━\n"
                                f"📌 <b>العنوان:</b> {rem['title']}\n"
                                f"📝 <b>الوصف:</b> {rem['desc']}\n"
                                f"⏰ <b>الموعد:</b> {rem_time}\n"
                                f"🔄 <b>الحالة:</b> {rem.get('repeat', 'مرة واحدة')}\n"
                                f"━""\n"
                f"<b>🤍 مطور البوت: @altaee_z</b>\n"
               f"📦 إصدار البوت: <a href='http://www.services-bot.free.nf'><b>V2.5.0</b></a>"                           
                            )
                            try:
                                bot.send_message(uid, alert_text, parse_mode="HTML")
                            except: pass

                            # نظام التكرار
                            if rem.get('repeat') == "يومي":
                                try:
                                    clean_time = rem_time.replace("صباحاً", "AM").replace("مساءً", "PM")
                                    dt_obj = datetime.strptime(clean_time, "%Y-%m-%d %I:%M %p")
                                    next_dt = dt_obj + timedelta(days=1)
                                    rem['datetime'] = next_dt.strftime("%Y-%m-%d %I:%M %p").replace("AM", "صباحاً").replace("PM", "مساءً")
                                except: user_rems.remove(rem)
                            else:
                                user_rems.remove(rem)
                            updated = True

                if updated: save_reminders(data)
                time.sleep(3)
            except Exception as e:
                print(f"Error in Loop: {e}")
                time.sleep(1)

    # تشغيل المحرك في الخلفية
    threading.Thread(target=check_reminders_loop, daemon=True).start()

    # --- 2. لوحة التحكم الرئيسية ---
    @bot.callback_query_handler(func=lambda c: c.data == "go_reminders")
    def reminders_menu(call):
        uid = str(call.from_user.id)
        data = load_reminders()
        user_rems = data.get(uid, [])
        
        # ميزة عرض أقرب تذكير مباشرة في اللوحة
        next_rem_info = "لا توجد تذكيرات نشطة"
        if user_rems:
            try:
                # ترتيب حسب الوقت (الأقرب أولاً)
                sorted_rems = sorted(user_rems, key=lambda x: x.get('datetime', x.get('time', '')))
                next_rem_info = f"📍 {sorted_rems[0]['title']} ({sorted_rems[0].get('datetime')})"
            except: pass

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton("➕ إضافة تذكير جديد", callback_data="add_rem"))
        kb.add(types.InlineKeyboardButton("📋 تذكيراتي", callback_data="list_rem"),
               types.InlineKeyboardButton("🗑️ مسح الكل", callback_data="clear_all_rems"))
        kb.add(types.InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_start"))
        
        text = (
            f"<b>🔔 نظام التذكير الذكي </b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"🎯 <b>أقرب موعد قادم:</b>\n<code>{next_rem_info}</code>\n\n"
            f"📊 <b>إجمالي المواعيد:</b> {len(user_rems)}\n"
            f"🕒 <b>توقيت البوت الآن:</b> {datetime.now().strftime('%-I:%M %p')}\n"
            f"━━━━━━━━━━━━━━"
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

    # --- 3. نظام الإضافة الذكي ---
    @bot.callback_query_handler(func=lambda c: c.data == "add_rem")
    def start_add(call):
        msg = bot.send_message(call.message.chat.id, "📌 <b>أدخل عنوان التذكير (مثلاً: موعد دكتور):</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, get_title)

    def get_title(message):
        title = message.text
        msg = bot.send_message(message.chat.id, "📝 <b>أدخل تفاصيل بسيطة للتذكير:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, get_desc, title)

    def get_desc(message, title):
        desc = message.text
        help_text = (
            "⏰ <b>تحديد الوقت والتاريخ:</b>\n\n"
            "يمكنك الإرسال هكذا:\n"
            "• للوقت فقط: <code>09:15</code>\n"
            "• تاريخ ووقت: <code>2026-02-10 11:30</code>"
        )
        msg = bot.send_message(message.chat.id, help_text, parse_mode="HTML")
        bot.register_next_step_handler(msg, get_time_val, title, desc)

    def get_time_val(message, title, desc):
        time_input = message.text.strip()
        uid = str(message.from_user.id)
        # تخزين مؤقت لمنع خطأ Callback length
        TEMP_DATA[uid] = {"title": title, "desc": desc, "time": time_input}
        
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("صباحاً ☀️", callback_data="setp_AM"),
               types.InlineKeyboardButton("مساءً 🌙", callback_data="setp_PM"))
        bot.send_message(message.chat.id, "⏱ <b>اختر الفترة الزمنية:</b>", reply_markup=kb, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("setp_"))
    def handle_period(call):
        uid = str(call.from_user.id)
        period = call.data.split("_")[1]
        
        if uid not in TEMP_DATA:
            bot.send_message(call.message.chat.id, "❌ حدث خطأ في الجلسة، حاول مرة أخرى.")
            return

        t_val = TEMP_DATA[uid]['time']
        period_ar = "صباحاً" if period == "AM" else "مساءً"
        
        # دمج التاريخ مع الوقت
        if len(t_val) <= 5: # لو دخل وقت بس
            final_dt = f"{datetime.now().strftime('%Y-%m-%d')} {t_val} {period_ar}"
        else: # لو دخل تاريخ ووقت
            final_dt = f"{t_val} {period_ar}"
        
        TEMP_DATA[uid]['final_dt'] = final_dt
        
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("مرة واحدة", callback_data="setr_None"),
               types.InlineKeyboardButton("تكرار يومي", callback_data="setr_يومي"))
        bot.edit_message_text(f"🔄 <b>هل تريد تكرار التذكير؟</b>", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("setr_"))
    def save_final_reminder(call):
        uid = str(call.from_user.id)
        rep = call.data.split("_")[1]
        
        if uid in TEMP_DATA:
            data = load_reminders()
            if uid not in data: data[uid] = []
            
            data[uid].append({
                "title": TEMP_DATA[uid]['title'],
                "desc": TEMP_DATA[uid]['desc'],
                "datetime": TEMP_DATA[uid]['final_dt'],
                "repeat": rep if rep != "None" else "مرة واحدة"
            })
            save_reminders(data)
            del TEMP_DATA[uid] # حذف البيانات المؤقتة
            
            bot.answer_callback_query(call.id, "✅ تم ضبط التذكير بنجاح!")
            reminders_menu(call)

    # --- 4. إدارة التذكيرات (تعديل وحذف) ---
    @bot.callback_query_handler(func=lambda c: c.data == "list_rem")
    def list_rems(call):
        uid = str(call.from_user.id)
        data = load_reminders()
        user_rems = data.get(uid, [])
        
        if not user_rems:
            bot.answer_callback_query(call.id, "📭 قائمة تذكيراتك فارغة", show_alert=True)
            return

        kb = types.InlineKeyboardMarkup()
        for i, r in enumerate(user_rems):
            # عرض العنوان والوقت في الزر
            display_time = r.get('datetime', r.get('time', '')).split(" ", 1)[-1]
            kb.add(types.InlineKeyboardButton(f"📍 {r['title']} | {display_time}", callback_data=f"mng_{i}"))
        
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_reminders"))
        bot.edit_message_text("<b>📋 تذكيراتك القادمة:</b>\nاضغط على أي تذكير لإدارته أو حذفه.", 
                              call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("mng_"))
    def manage_single_rem(call):
        idx = int(call.data.split("_")[1])
        uid = str(call.from_user.id)
        data = load_reminders()
        
        if uid in data and len(data[uid]) > idx:
            rem = data[uid][idx]
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🗑️ حذف هذا التذكير فوراً", callback_data=f"delr_{idx}"))
            kb.add(types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="list_rem"))
            
            text = (
                f"⚙️ <b>إدارة التذكير</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"📌 <b>العنوان:</b> {rem['title']}\n"
                f"📝 <b>الوصف:</b> {rem['desc']}\n"
                f"⏰ <b>الموعد:</b> {rem.get('datetime', rem.get('time'))}\n"
                f"🔄 <b>التكرار:</b> {rem['repeat']}\n"
                f"━━━━━━━━━━━━━━"
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("delr_"))
    def delete_reminder(call):
        idx = int(call.data.split("_")[1])
        uid = str(call.from_user.id)
        data = load_reminders()
        
        if uid in data and len(data[uid]) > idx:
            data[uid].pop(idx)
            save_reminders(data)
            bot.answer_callback_query(call.id, "✅ تم الحذف بنجاح")
            list_rems(call)

    @bot.callback_query_handler(func=lambda c: c.data == "clear_all_rems")
    def clear_all(call):
        uid = str(call.from_user.id)
        data = load_reminders()
        if uid in data:
            data[uid] = []
            save_reminders(data)
            bot.answer_callback_query(call.id, "🗑️ تم مسح كل التذكيرات")
            reminders_menu(call)
