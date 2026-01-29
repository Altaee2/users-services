import os
from telebot import types
from PIL import Image
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter

TEMP = "temp_pdf"
os.makedirs(TEMP, exist_ok=True)

USER_IMAGES = {}
USER_PDF = {}
USER_PDF_SETTINGS = {}
USER_WAIT = {}

RIGHTS = (
    "\n━━━━━━━━━━━━━━\n"
    "© Developed by Ali Altaee\n"
    "🤍 تلجرام :- @altaee_z\n"
    "🌐 موقعي : www.ali-Altaee.free.nf\n"
    "━━━━━━━━━━━━━━"
)

def pdf_converter_handler(bot):

    # ================== الدخول ==================
    @bot.callback_query_handler(func=lambda c: c.data == "go_pdf")
    def pdf_menu(call):
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📸 إنشاء ملف من صور", callback_data="pdf_from_images"),
            types.InlineKeyboardButton("✂️ إدارة ملف PDF", callback_data="pdf_edit")
        )
        bot.edit_message_text(
            "<b>📄 أدوات PDF</b>\nاختر العملية 👇",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )

    # ================== صور → PDF ==================
    @bot.callback_query_handler(func=lambda c: c.data == "pdf_from_images")
    def start_images(call):
        uid = call.from_user.id
        USER_IMAGES[uid] = []
        USER_PDF_SETTINGS[uid] = {"password": None}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📸 أرسل الصور الآن")

    @bot.message_handler(content_types=["photo"])
    def collect_images(message):
        uid = message.from_user.id
        if uid not in USER_IMAGES:
            return

        file_id = message.photo[-1].file_id
        info = bot.get_file(file_id)
        data = bot.download_file(info.file_path)

        img_path = os.path.join(TEMP, f"{uid}_{len(USER_IMAGES[uid])}.jpg")
        with open(img_path, "wb") as f:
            f.write(data)

        USER_IMAGES[uid].append(img_path)

        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("✅ تم – حوّل الآن", callback_data="make_pdf"),
            types.InlineKeyboardButton("🔐 قفل بكلمة مرور", callback_data="set_pdf_pass")
        )

        bot.send_message(
            message.chat.id,
            f"📸 تم حفظ الصورة ({len(USER_IMAGES[uid])})",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda c: c.data == "set_pdf_pass")
    def ask_pass(call):
        uid = call.from_user.id
        USER_WAIT[uid] = "PASS"
        bot.send_message(call.message.chat.id, "🔐 أرسل كلمة المرور أو اكتب تخطي")

    @bot.message_handler(func=lambda m: USER_WAIT.get(m.from_user.id) == "PASS")
    def save_pass(message):
        uid = message.from_user.id
        if message.text.lower() != "تخطي":
            USER_PDF_SETTINGS[uid]["password"] = message.text
        USER_WAIT.pop(uid)
        bot.send_message(message.chat.id, "🔐 تم حفظ الإعداد")

    @bot.callback_query_handler(func=lambda c: c.data == "make_pdf")
    def make_pdf(call):
        uid = call.from_user.id
        imgs = [Image.open(p).convert("RGB") for p in USER_IMAGES[uid]]

        name = f"images_{datetime.now().strftime('%H%M%S')}.pdf"
        path = os.path.join(TEMP, name)

        imgs[0].save(path, save_all=True, append_images=imgs[1:])

        if USER_PDF_SETTINGS[uid]["password"]:
            reader = PdfReader(path)
            writer = PdfWriter()
            for p in reader.pages:
                writer.add_page(p)
            writer.encrypt(USER_PDF_SETTINGS[uid]["password"])
            with open(path, "wb") as f:
                writer.write(f)

        bot.send_document(
            call.message.chat.id,
            open(path, "rb"),
            caption="✅ تم إنشاء الملف"+RIGHTS
        )

        USER_PDF[uid] = path
        USER_IMAGES.pop(uid)
        USER_PDF_SETTINGS.pop(uid)

    # ================== إدارة PDF ==================
    @bot.callback_query_handler(func=lambda c: c.data == "pdf_edit")
    def ask_pdf(call):
        bot.send_message(call.message.chat.id, "📄 أرسل ملف PDF")

    @bot.message_handler(content_types=["document"])
    def receive_pdf(message):
        uid = message.from_user.id
        if not message.document.file_name.lower().endswith(".pdf"):
            return

        info = bot.get_file(message.document.file_id)
        data = bot.download_file(info.file_path)

        path = os.path.join(TEMP, f"{uid}.pdf")
        with open(path, "wb") as f:
            f.write(data)

        USER_PDF[uid] = path

        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("✂️ أخذ صفحات", callback_data="keep_pages"),
            types.InlineKeyboardButton("🗑️ حذف صفحات", callback_data="remove_pages")
        )
        bot.send_message(message.chat.id, "اختر العملية", reply_markup=kb)

    def process_pages(uid, pages, keep=True):
        reader = PdfReader(USER_PDF[uid])
        writer = PdfWriter()

        total = len(reader.pages)
        pages = [p-1 for p in pages if 1 <= p <= total]

        for i in range(total):
            if (i in pages and keep) or (i not in pages and not keep):
                writer.add_page(reader.pages[i])

        out = os.path.join(TEMP, f"result_{uid}.pdf")
        with open(out, "wb") as f:
            writer.write(f)

        return out

    @bot.callback_query_handler(func=lambda c: c.data in ["keep_pages", "remove_pages"])
    def ask_pages(call):
        USER_WAIT[call.from_user.id] = c = call.data
        bot.send_message(call.message.chat.id, "✏️ اكتب الصفحات مثل: 1,3,5")

    @bot.message_handler(func=lambda m: USER_WAIT.get(m.from_user.id) in ["keep_pages", "remove_pages"])
    def handle_pages(message):
        uid = message.from_user.id
        pages = list(map(int, message.text.replace(" ", "").split(",")))
        keep = USER_WAIT[uid] == "keep_pages"
        USER_WAIT.pop(uid)

        out = process_pages(uid, pages, keep)
        bot.send_document(
            message.chat.id,
            open(out, "rb"),
            caption="✅ تم تعديل الملف"+RIGHTS
        )