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
            types.InlineKeyboardButton("🖼️ تحويل إلى ICO", callback_data='mode_conv_ico'),
            types.InlineKeyboardButton("🔄 تحويل إلى PNG", callback_data='mode_conv_png'),
            types.InlineKeyboardButton("🖼️ تحويل إلى JPG", callback_data='mode_conv_jpg'),
            types.InlineKeyboardButton("✏️ إعادة تسمية", callback_data='mode_rename'),
            types.InlineKeyboardButton("✂️ قص الصورة", callback_data='mode_crop'),
            types.InlineKeyboardButton("📏 تغيير الحجم يدوياً", callback_data='mode_resize'),
            types.InlineKeyboardButton("🎨 استخراج الألوان", callback_data='mode_colors'),
            types.InlineKeyboardButton("📄 تحويل لـ PDF", callback_data='mode_pdf'),
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
            "link":"وضع استخراج الرابط",
            "conv_ico": "🖼️ وضع التحويل إلى ICO مفعل",
            "conv_png": "🔄 وضع التحويل إلى PNG مفعل",
            "conv_jpg": "🖼️ وضع التحويل إلى JPG مفعل",
            "rename": "✏️ وضع إعادة التسمية مفعل\n\nأرسل الصورة أولاً، ثم سأطلب منك الاسم الجديد.",
            "crop": "✂️ وضع القص مفعل\n\nأرسل الصورة أولاً، ثم سأعطيك خيارات أبعاد القص الجاهزة.",
            "resize": "📏 وضع تغيير الحجم مفعل\n\nأرسل الصورة أولاً، ثم سأطلب منك الأبعاد الجديدة.",
            "colors": "🎨 وضع استخراج الألوان مفعل\n\nأرسل الصورة وسأقوم بتحليل الألوان الموجودة فيها.",
            "pdf": "📄 وضع التحويل لـ PDF مفعل\nأرسل الصورة وسأحولها لملف مستند جاهز.",

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

            elif mode == "resize":
                user_states[user_id] = {'action': 'waiting_width', 'file_id': message.photo[-1].file_id}
                bot.edit_message_text(
                    "<b>📐 الخطوة 1:</b>\nأرسل الآن <b>العرض</b> المطلوب (Width) بالبكسل:",
                    message.chat.id,
                    status.message_id,
                    parse_mode="HTML"
                )
                return
            elif mode == 'colors':
                # التصليح هنا: استخدمنا downloaded_file بدلاً من input_io غير المعرف
                img = Image.open(BytesIO(downloaded_file)).convert("RGB")
                
                # تصغير الصورة جداً لتسريع المعالجة
                img.thumbnail((100, 100))
                
                # استخراج قائمة الألوان
                palette = img.getcolors(100 * 100)
                
                # ترتيب الألوان وأخذ أول 8
                dominant_colors = sorted(palette, key=lambda x: x[0], reverse=True)[:8]
                
                response_msg = "<b>🎨 لوحة الألوان المستخرجة:</b>\n━━━━━━━━━━━━\n"
                
                for count, rgb in dominant_colors:
                    hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb).upper()
                    response_msg += f"Color: <code>{hex_color}</code>\n"
                    response_msg += f"RGB: <code>{rgb}</code>\n"
                    response_msg += "━━━━━━━━━━━━\n"
                
                bot.send_message(
                    message.chat.id,
                    response_msg,
                    parse_mode="HTML"
                )
            elif mode == 'pdf':
                img = Image.open(BytesIO(downloaded_file)).convert("RGB")
                output = BytesIO()
                output.name = "@Z0A_BOT.pdf"
                img.save(output, format='PDF')
                output.seek(0)
                bot.send_document(message.chat.id, output, caption="<b>✅ تم تحويل الصورة إلى PDF بنجاح</b>", parse_mode="HTML")

            
            elif mode == "crop":
                # نحفظ الـ file_id في الذاكرة مؤقتاً
                user_states[user_id] = {'action': 'waiting_crop_size', 'file_id': message.photo[-1].file_id}
                
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("1:1 (مربع)", callback_data='crop_1:1'),
                    types.InlineKeyboardButton("4:5 (انستقرام)", callback_data='crop_4:5'),
                    types.InlineKeyboardButton("16:9 (يوتيوب)", callback_data='crop_16:9'),
                    types.InlineKeyboardButton("❌ إلغاء", callback_data='show_menu')
                )
                
                bot.edit_message_text(
                    "<b>✂️ اختر أبعاد القص المطلوبة:</b>",
                    message.chat.id,
                    status.message_id,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
                return # ننتظر اختيار المستخدم من الأزرار
            elif mode == "rename":
                # نحفظ بيانات الصورة في الذاكرة مؤقتاً ونطلب الاسم
                user_states[user_id] = {'action': 'waiting_name', 'file_id': message.photo[-1].file_id}
                bot.edit_message_text("✅ استلمت الصورة، الآن أرسل **الاسم الجديد** (بدون صيغة):", message.chat.id, status.message_id, parse_mode="Markdown")
                return # نوقف الدالة هنا وننتظر الرسالة القادمة
            elif mode == 'conv_ico':
                img = Image.open(BytesIO(downloaded_file))
                output = BytesIO()
                # تحويل الصورة وحفظها بصيغة ICO
                img.save(output, format='ICO', sizes=[(256, 256)])
                output.name = "@Z0A_BOT.ico"
                output.seek(0)

                bot.send_document(
                    message.chat.id,
                    output,
                    caption="<b>✅ تم تحويل الصورة إلى أيقونة ICO</b>",
                    parse_mode="HTML"
                )
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
                
            elif mode == 'conv_png':
                img = Image.open(BytesIO(downloaded_file)).convert("RGBA")
                output = BytesIO()
                output.name = "@Z0A_BOT.png"
                img.save(output, format='PNG')
                output.seek(0)

                bot.send_document(
                    message.chat.id,
                    output,
                    caption="<b>✅ تم تحويل الصورة إلى PNG بنجاح</b>",
                    parse_mode="HTML"
                )
            elif mode == "link":
                # --- استخراج رابط ---
                # نستخدم خدمة رفع خارجية بسيطة أو رابط تليجرام
                img_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
                bot.reply_to(message, f"<b>🔗 رابط الصورة المباشر:</b>\n<code>{img_url}</code>", parse_mode="HTML")                
            elif mode == 'conv_jpg':
                img = Image.open(BytesIO(downloaded_file)).convert("RGB") # تحويل لـ RGB ضروري للـ JPG
                output = BytesIO()
                output.name = "@Z0A_BOT.jpg"
                img.save(output, format='JPEG', quality=95) # جودة عالية
                output.seek(0)

                bot.send_photo(
                    message.chat.id,
                    output,
                    caption="<b>✅ تم تحويل الصورة إلى JPG بنجاح</b>",
                    parse_mode="HTML"
                )
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
    @bot.message_handler(func=lambda message: isinstance(user_states.get(message.from_user.id), dict) and user_states.get(message.from_user.id).get('action') == 'waiting_name')
    def process_rename(message):
        user_id = message.from_user.id
        data = user_states.get(user_id)
        new_name = message.text.strip()
        
        status = bot.reply_to(message, "⏳ جاري تغيير الاسم وإرسال الملف...")
        
        try:
            file_info = bot.get_file(data['file_id'])
            downloaded_file = bot.download_file(file_info.file_path)
            
            output = BytesIO(downloaded_file)
            output.name = f"{new_name}.jpg" # نعطيه الاسم الجديد مع صيغة jpg كافتراضي
            output.seek(0)
            
            bot.send_document(
                message.chat.id, 
                output, 
                caption=f"✅ تم إعادة التسمية إلى: <b>{new_name}</b>",
                parse_mode="HTML"
            )
            bot.delete_message(message.chat.id, status.message_id)
        except Exception as e:
            bot.edit_message_text("⚠️ فشل تغيير الاسم، حاول مجدداً.", message.chat.id, status.message_id)
        
        # تنظيف الحالة
        user_states.pop(user_id, None)
    @bot.callback_query_handler(func=lambda c: c.data.startswith('crop_'))
    def process_crop_selection(call):
        user_id = call.from_user.id
        data = user_states.get(user_id)
        
        if not data or not isinstance(data, dict):
            bot.answer_callback_query(call.id, "⚠️ انتهت الجلسة، أرسل الصورة من جديد.")
            return

        ratio_str = call.data.replace('crop_', '') # مثلاً "1:1"
        bot.edit_message_text("⏳ جاري قص الصورة...", call.message.chat.id, call.message.message_id)

        try:
            file_info = bot.get_file(data['file_id'])
            downloaded_file = bot.download_file(file_info.file_path)
            img = Image.open(BytesIO(downloaded_file)).convert("RGB")
            width, height = img.size

            # حساب أبعاد القص (الوسط)
            ratio_w, ratio_h = map(int, ratio_str.split(':'))
            target_ratio = ratio_w / ratio_h
            current_ratio = width / height

            if current_ratio > target_ratio:
                new_width = int(target_ratio * height)
                offset = (width - new_width) // 2
                img = img.crop((offset, 0, width - offset, height))
            else:
                new_height = int(width / target_ratio)
                offset = (height - new_height) // 2
                img = img.crop((0, offset, width, height - offset))

            output = BytesIO()
            img.save(output, format="JPEG", quality=95)
            output.seek(0)

            bot.send_photo(call.message.chat.id, output, caption=f"✅ تم القص بنسبة {ratio_str}")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            
        except Exception as e:
            bot.send_message(call.message.chat.id, "⚠️ حدث خطأ أثناء القص.")
        
        user_states.pop(user_id, None)
        
    @bot.message_handler(func=lambda message: isinstance(user_states.get(message.from_user.id), dict) and user_states.get(message.from_user.id).get('action') in ['waiting_width', 'waiting_height'])
    def process_resizing(message):
        user_id = message.from_user.id
        data = user_states.get(user_id)
        text = message.text.strip()

        if not text.isdigit():
            bot.reply_to(message, "⚠️ يرجى إرسال رقم صحيح فقط.")
            return

        # إذا كنا ننتظر العرض
        if data['action'] == 'waiting_width':
            data['width'] = int(text)
            data['action'] = 'waiting_height'
            user_states[user_id] = data
            bot.reply_to(message, f"✅ العرض: {text}px\n\nالآن أرسل <b>الارتفاع</b> المطلوب (Height):", parse_mode="HTML")
        
        # إذا كنا ننتظر الطول (المرحلة النهائية)
        elif data['action'] == 'waiting_height':
            height = int(text)
            width = data['width']
            file_id = data['file_id']
            
            status = bot.reply_to(message, "⏳ جاري تغيير الحجم والإرسال...")
            
            try:
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                img = Image.open(BytesIO(downloaded_file)).convert("RGB")
                
                # تغيير الحجم باستخدام أعلى جودة (LANCZOS)
                img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
                
                output = BytesIO()
                output.name = f"resized_{width}x{height}.jpg"
                img_resized.save(output, format='JPEG', quality=100)
                output.seek(0)
                
                bot.send_document(
                    message.chat.id,
                    output,
                    caption=f"✅ تم تغيير الحجم بنجاح إلى: <b>{width}x{height}</b>",
                    parse_mode="HTML"
                )
                bot.delete_message(message.chat.id, status.message_id)
            except Exception as e:
                bot.send_message(message.chat.id, "⚠️ فشلت عملية تغيير الحجم.")
            
            # مسح الحالة
            user_states.pop(user_id, None)
        
            
