import requests
from io import BytesIO
from telebot import types
from PIL import Image, ImageOps, ImageEnhance

# 🔑 مفتاح remove.bg
REMOVE_BG_KEY = "PawTQh5RB1AQiqeiW2sS5kpy"


def images_handler(bot, user_states):

    # ━━━━━━━━━━━━━━━━━━━
    # 📂 القائمة الرئيسية
    # ━━━━━━━━━━━━━━━━━━━
    @bot.callback_query_handler(func=lambda c: c.data == "show_menu")
    def images_menu(call):
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✨ إزالة الخلفية", callback_data="mode_remove_bg"),
            types.InlineKeyboardButton("🪄 توضيح الصورة", callback_data="mode_enhance"),
            types.InlineKeyboardButton("🎭 تحويل لملصق", callback_data="mode_sticker"),
            types.InlineKeyboardButton("🏁 أبيض وأسود", callback_data="mode_bw"),
            types.InlineKeyboardButton("استخراج رابط الصورة", callback_data="mode_link"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="main_start")
        )

        text = (
            "<b>🖼️ أدوات الصور الاحترافية</b>\n\n"
            "اختر الوظيفة التي تريدها ثم أرسل الصورة 📤\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )

    # ━━━━━━━━━━━━━━━━━━━
    # 🎯 اختيار الوضع
    # ━━━━━━━━━━━━━━━━━━━
    @bot.callback_query_handler(func=lambda call: call.data.startswith("mode_"))
    def set_mode(call):
        user_id = call.from_user.id
        mode = call.data.replace("mode_", "")
        user_states[user_id] = mode

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 إلغاء", callback_data="show_menu"))

        modes_text = {
            "remove_bg": "✨ وضع إزالة الخلفية مفعل",
            "enhance": "🪄 وضع توضيح الصورة مفعل",
            "sticker": "🎭 وضع التحويل لملصق مفعل",
            "bw": "🏁 وضع الأبيض والأسود مفعل",
            "link":"وضع استخراج الرابط"
        }

        bot.edit_message_text(
            f"<b>{modes_text.get(mode)} ✅</b>\n\nأرسل الصورة الآن",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )

    # ━━━━━━━━━━━━━━━━━━━
    # 🖼️ استقبال الصور
    # ━━━━━━━━━━━━━━━━━━━
    @bot.message_handler(content_types=['photo'])
    def handle_image(message):
        user_id = message.from_user.id
        mode = user_states.get(user_id)

        if not mode:
            return

        status = bot.reply_to(
            message,
            "<b>⏳ جاري المعالجة...</b>",
            parse_mode="HTML"
        )

        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            # ── إزالة الخلفية ──
            if mode == "remove_bg":
                image_bytes = BytesIO(downloaded_file)
                image_bytes.seek(0)

                response = requests.post(
                    "https://api.remove.bg/v1.0/removebg",
                    headers={"X-Api-Key": REMOVE_BG_KEY},
                    files={"image_file": ("image.png", image_bytes, "image/png")},
                    data={"size": "auto"}
                )

                if response.status_code == 200:
                    output = BytesIO(response.content)
                    output.name = "removed_bg.png"
                    output.seek(0)

                    bot.send_document(
                        message.chat.id,
                        output,
                        caption="<b>✅ تمت إزالة الخلفية بنجاح</b>",
                        parse_mode="HTML"
                    )
                else:
                    try:
                        error = response.json()["errors"][0]["title"]
                    except:
                        error = "فشل غير معروف"
                    bot.send_message(message.chat.id, f"❌ خطأ: {error}")

            # ── توضيح الصورة ──
            elif mode == "enhance":
                img = Image.open(BytesIO(downloaded_file)).convert("RGB")

                img = ImageEnhance.Sharpness(img).enhance(2.0)
                img = ImageEnhance.Contrast(img).enhance(1.4)
                img = ImageEnhance.Color(img).enhance(1.3)

                output = BytesIO()
                img.save(output, format="JPEG", quality=95)
                output.seek(0)

                bot.send_photo(
                    message.chat.id,
                    output,
                    caption="<b>🪄 تم توضيح الصورة وتحسين جودتها</b>",
                    parse_mode="HTML"
                )

            # ── أبيض وأسود ──
            elif mode == "bw":
                img = Image.open(BytesIO(downloaded_file))
                bw_img = ImageOps.grayscale(img)

                output = BytesIO()
                bw_img.save(output, format="JPEG")
                output.seek(0)

                bot.send_photo(
                    message.chat.id,
                    output,
                    caption="<b>🏁 الصورة بالأبيض والأسود</b>",
                    parse_mode="HTML"
                )
                
            elif mode == "link":
                # --- استخراج رابط ---
                # نستخدم خدمة رفع خارجية بسيطة أو رابط تليجرام
                img_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
                bot.reply_to(message, f"<b>🔗 رابط الصورة المباشر:</b>\n<code>{img_url}</code>", parse_mode="HTML")                
            # ── ملصق ──
            elif mode == "sticker":
                sticker = BytesIO(downloaded_file)
                sticker.seek(0)
                bot.send_sticker(message.chat.id, sticker)

            bot.delete_message(message.chat.id, status.message_id)
            user_states.pop(user_id, None)

        except Exception as e:
            print(e)
            bot.edit_message_text(
                "⚠️ حدث خطأ أثناء المعالجة، حاول مرة أخرى.",
                message.chat.id,
                status.message_id
            )