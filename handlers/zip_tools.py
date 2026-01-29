import os
import zipfile
import time
from io import BytesIO
from datetime import datetime
from telebot import types

# مخزن الجلسات
user_data = {}

def zip_handler(bot): # <-- نضع الكود داخل دالة لتمرير البوت

    # --- [ 1. معالجة الضغط على الزر الرئيسي ] ---
    @bot.callback_query_handler(func=lambda c: c.data == "go_compress")
    def zip_main_menu(call):
        uid = call.from_user.id
        text = (
            "📦 **خدمة إدارة الملفات (Zip)**\n\n"
            "• **انشاء ملف مضغوط**: تجميع عدة ملفات.\n"
            "• **فك ضغط**: استخراج ملفات من Zip.\n\n"
            "⚠️ **ملاحظة:** الحد الأقصى للملف هو 100MB."
        )
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("➕ انشاء ملف مضغوط", callback_data="set_zip_create"),
            types.InlineKeyboardButton("🔓 فك ضغط", callback_data="set_zip_extract"),
            types.InlineKeyboardButton("الرجوع ", callback_data="main_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                              reply_markup=markup, parse_mode="Markdown")

    # --- [ 2. تحديد نوع العملية ] ---
    @bot.callback_query_handler(func=lambda c: c.data.startswith("set_zip_"))
    def set_service_mode(call):
        uid = call.from_user.id
        mode = call.data.split("_")[-1]
        
        if mode == "create":
            user_data[uid] = {'mode': 'compress', 'files': []}
            msg = "📥 **وضع الإنشاء:** أرسل الملفات الآن.\nعند الانتهاء اضغط (حفظ)."
            markup = get_finish_markup()
        else:
            user_data[uid] = {'mode': 'extract'}
            msg = "📂 **وضع فك الضغط:** أرسل ملف الـ Zip الآن."
            markup = None
            
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, 
                              reply_markup=markup, parse_mode="Markdown")

    # --- [ 3. استقبال ومعالجة الملفات ] ---
    @bot.message_handler(content_types=['document'])
    def handle_zip_documents(message):
        uid = message.from_user.id
        if uid not in user_data: return 

        doc = message.document
        if doc.file_size > 100 * 1024 * 1024:
            return bot.reply_to(message, "❌ حجم الملف يتجاوز 100MB.")

        if user_data[uid]['mode'] == 'compress':
            file_info = bot.get_file(doc.file_id)
            downloaded = bot.download_file(file_info.file_path)
            user_data[uid]['files'].append({'name': doc.file_name, 'content': downloaded})
            
            info_msg = (f"✅ **تم استلام:** `{doc.file_name}`\n"
                        f"🔢 العدد الحالي: {len(user_data[uid]['files'])}")
            bot.reply_to(message, info_msg, parse_mode="Markdown", reply_markup=get_finish_markup())

        elif user_data[uid]['mode'] == 'extract':
            if not doc.file_name.lower().endswith('.zip'):
                return bot.reply_to(message, "⚠️ أرسل ملف .zip فقط.")
            
            try:
                file_info = bot.get_file(doc.file_id)
                downloaded = bot.download_file(file_info.file_path)
                with zipfile.ZipFile(BytesIO(downloaded), 'r') as zf:
                    for item in zf.infolist():
                        if item.is_dir(): continue
                        bot.send_document(message.chat.id, BytesIO(zf.read(item.filename)), 
                                         visible_file_name=os.path.basename(item.filename))
                        time.sleep(0.3)
                del user_data[uid]
            except:
                bot.reply_to(message, "❌ خطأ في الملف.")

    # --- [ 4. إنهاء الضغط ] ---
    @bot.callback_query_handler(func=lambda c: c.data == "finish_zip_action")
    def finalize_zip(call):
        uid = call.from_user.id
        if uid not in user_data or not user_data[uid].get('files'): return
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zf:
            for f in user_data[uid]['files']:
                zf.writestr(f['name'], f['content'])
        
        zip_buffer.seek(0)
        bot.send_document(call.message.chat.id, zip_buffer, visible_file_name="Archive.zip",
                          caption="📦 تم إنشاء ملفك بنجاح!")
        del user_data[uid]

def get_finish_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💾 حفظ وإنشاء (Zip)", callback_data="finish_zip_action"))
    return markup
