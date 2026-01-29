import os
import json
import time
import pytz
import io
from datetime import datetime, timedelta
from threading import Lock, Thread
from telebot import types

# --- الإعدادات العامة ---
DATA_FILE = "todo_data.json"
LOCK = Lock()
BAGHDAD_TZ = pytz.timezone('Asia/Baghdad')

# --- دوال إدارة البيانات (JSON) ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with LOCK:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}

def save_data(data):
    with LOCK:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_tasks(user_id):
    return load_data().get(str(user_id), [])

def set_user_tasks(user_id, tasks):
    data = load_data()
    data[str(user_id)] = tasks
    save_data(data)

# --- محرك التذكير (Background Thread) ---
def reminder_scheduler(bot):
    while True:
        try:
            now = datetime.now(BAGHDAD_TZ).timestamp()
            data = load_data()
            updated = False
            for uid, tasks in data.items():
                for t in tasks:
                    # التحقق إذا كان هناك تذكير ولم يتم إرساله بعد
                    if t.get("remind_at") and not t.get("reminded") and now >= t["remind_at"]:
                        bot.send_message(uid, f"🔔 <b>تذكير بمهمة!</b>\n\n📝 المهمة: <b>{t['text']}</b>\n\n🤍 لا تنسى إنجازها يا بطل!\n@altaee_z", parse_mode="HTML")
                        t["reminded"] = True
                        updated = True
            if updated:
                save_data(data)
        except Exception as e:
            print(f"Reminder Error: {e}")
        time.sleep(30) # فحص كل 30 ثانية

# --- الهاندلر الرئيسي لخدمة المهام ---
def todo_handler(bot):
    
    # تشغيل خيط التذكير مرة واحدة فقط عند تشغيل البوت
    if not hasattr(bot, 'reminder_started'):
        Thread(target=reminder_scheduler, args=(bot,), daemon=True).start()
        bot.reminder_started = True

    # 1. القائمة الرئيسية للمهام
    @bot.callback_query_handler(func=lambda c: c.data == "go_todo")
    def open_todo_menu(call):
        user_id = call.from_user.id
        tasks = get_user_tasks(user_id)
        
        # حساب إحصائيات الإنجاز
        total = len(tasks)
        done_count = sum(1 for t in tasks if t.get("done"))
        percent = (done_count / total * 100) if total > 0 else 0

        text = f"<b>📝 قائمة المهام - @altaee_z</b>\n"
        text += f"📊 نسبة الإنجاز: <code>[{percent:.0f}%]</code>\n"
        text += "━" * 15 + "\n"
        
        if not tasks:
            text += "📭 قائمة مهامك فارغة حالياً."
        else:
            for i, t in enumerate(tasks, start=1):
                status = "✅" if t.get("done") else "◻️"
                text += f"{i}. {status} <b>{t['text']}</b>\n"
                text += f"   └ 🕒 {t['time']} | 📅 {t['date']}\n"
        
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("➕ إضافة مهمة", callback_data="add_task_input"))
        if tasks:
            kb.row(types.InlineKeyboardButton("⚙️ إدارة المهام", callback_data="manage_tasks"))
            kb.row(types.InlineKeyboardButton("📄 سحب ملف TXT", callback_data="export_txt"))
            kb.row(types.InlineKeyboardButton("🗑️ مسح الكل", callback_data="clear_all_tasks"))
        kb.row(types.InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="main_start"))

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

    # 2. استقبال نص المهمة
    @bot.callback_query_handler(func=lambda c: c.data == "add_task_input")
    def ask_task(call):
        bot.edit_message_text("✍️ <b>أرسل الآن نص المهمة التي تريد حفظها:</b>", 
                              call.message.chat.id, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: receive_task(m, bot))

    def receive_task(message, bot):
        user_id = message.from_user.id
        task_text = message.text.strip() if message.text else ""
        if not task_text:
            bot.send_message(message.chat.id, "❌ لم ترسل نصاً! أعد المحاولة من القائمة.")
            return

        now = datetime.now(BAGHDAD_TZ)
        new_task = {
            "text": task_text,
            "done": False,
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%Y-%m-%d"),
            "remind_at": None,
            "reminded": False
        }
        
        tasks = get_user_tasks(user_id)
        tasks.append(new_task)
        set_user_tasks(user_id, tasks)
        task_idx = len(tasks) - 1

        reply = (
            "✅ <b>تم حفظ المهمة بنجاح:</b>\n\n"
            f"• 📝 المهمة: <b>{task_text}</b>\n"
            f"• 🕒 الوقت: <b>{new_task['time']}</b>\n\n"
            "🔔 هل تريد ضبط تذكير لهذه المهمة؟"
        )
        
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("⏰ ضبط تذكير", callback_data=f"set_remind_{task_idx}"))
        kb.row(types.InlineKeyboardButton("📋 القائمة", callback_data="go_todo"))
        
        bot.send_message(message.chat.id, reply, parse_mode="HTML", reply_markup=kb)

    # 3. قائمة ضبط التذكير
    @bot.callback_query_handler(func=lambda c: c.data.startswith("set_remind_"))
    def remind_options(call):
        task_idx = call.data.split("_")[-1]
        kb = types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("بعد ساعة", callback_data=f"rem_{task_idx}_1"),
               types.InlineKeyboardButton("بعد 3 ساعات", callback_data=f"rem_{task_idx}_3"))
        kb.row(types.InlineKeyboardButton("غداً (24 ساعة)", callback_data=f"rem_{task_idx}_24"))
        kb.add(types.InlineKeyboardButton("🔙 إلغاء", callback_data="go_todo"))
        
        bot.edit_message_text("⏰ <b>اختر وقت التذكير:</b>", 
                              call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("rem_"))
    def save_reminder(call):
        _, idx, hours = call.data.split("_")
        tasks = get_user_tasks(call.from_user.id)
        remind_time = datetime.now(BAGHDAD_TZ) + timedelta(hours=int(hours))
        
        tasks[int(idx)]["remind_at"] = remind_time.timestamp()
        set_user_tasks(call.from_user.id, tasks)
        
        bot.answer_callback_query(call.id, f"🔔 سيتم تذكيرك الساعة {remind_time.strftime('%I:%M %p')}", show_alert=True)
        open_todo_menu(call)

    # 4. واجهة الإدارة (إنجاز وحذف)
    @bot.callback_query_handler(func=lambda c: c.data == "manage_tasks")
    def manage_view(call):
        tasks = get_user_tasks(call.from_user.id)
        kb = types.InlineKeyboardMarkup()
        for idx, t in enumerate(tasks):
            status = "✅" if t['done'] else "✔️"
            kb.row(
                types.InlineKeyboardButton(f"{t['text'][:12]}..", callback_data=f"none_{idx}"),
                types.InlineKeyboardButton(status, callback_data=f"tgl_{idx}"),
                types.InlineKeyboardButton("🗑️", callback_data=f"del_{idx}")
            )
        kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="go_todo"))
        bot.edit_message_text("<b>⚙️ إدارة المهام:</b>\nإنجاز (✅) أو حذف (🗑️)", 
                              call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith(("tgl_", "del_")))
    def process_actions(call):
        action, idx = call.data.split("_")
        idx = int(idx)
        tasks = get_user_tasks(call.from_user.id)
        
        if action == "tgl":
            tasks[idx]['done'] = not tasks[idx]['done']
        elif action == "del":
            tasks.pop(idx)
            
        set_user_tasks(call.from_user.id, tasks)
        manage_view(call)

    # 5. سحب المهام ملف TXT
    @bot.callback_query_handler(func=lambda c: c.data == "export_txt")
    def export_tasks(call):
        tasks = get_user_tasks(call.from_user.id)
        content = f"📋 قائمة مهامك - {call.from_user.first_name}\n"
        content += "═" * 30 + "\n\n"
        for i, t in enumerate(tasks, 1):
            stat = "[تم الإنجاز]" if t['done'] else "[قيد الانتظار]"
            content += f"{i}. {stat} {t['text']}\n   📅 {t['date']} | 🕒 {t['time']}\n\n"
        
        content += "═" * 30 + "\n🤍 حقوق التطوير: @altaee_z\n🌐 موقعي: www.ali-Altaee.free.nf"
        
        with io.BytesIO(content.encode()) as file:
            file.name = f"Tasks_{call.from_user.id}.txt"
            bot.send_document(call.message.chat.id, file, caption="✅ تفضل يا غالي، هذا ملف مهامك مرتب.")

    # 6. مسح الكل
    @bot.callback_query_handler(func=lambda c: c.data == "clear_all_tasks")
    def clear_all(call):
        set_user_tasks(call.from_user.id, [])
        bot.answer_callback_query(call.id, "🗑️ تم إفراغ القائمة بالكامل", show_alert=True)
        open_todo_menu(call)
