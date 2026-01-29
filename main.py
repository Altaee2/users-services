import telebot
from config import TOKEN
from handlers.start import start_handler
from handlers.tasbih import tasbih_handler
from handlers.deco import deco_handler
from handlers.age import age_handler
from handlers.takleef import takleef_handler
from handlers.text_to_file import text_handler
from handlers.pinterest import pinterest_handler
from handlers.images import images_handler
from handlers.zip_tools import zip_handler
from handlers.quran import quran_handler
from handlers.tiktok import tiktok_handler
from handlers.instagram import instagram_handler
from handlers.shortlink import shortener_handler
from handlers.gpt import gpt_handler
from handlers.car import car_handler
from handlers.todo import todo_handler
from handlers.tashkeel import tashkeel_handler
from handlers.reminders import reminders_handler
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

user_data = {}
user_states = {}

start_handler(bot)
tasbih_handler(bot, user_data)
deco_handler(bot)
age_handler(bot, user_states)
takleef_handler(bot)
text_handler(bot)
pinterest_handler(bot)
images_handler(bot, user_states)
zip_handler(bot)
quran_handler(bot)
tiktok_handler(bot)
instagram_handler(bot)
shortener_handler(bot)
gpt_handler(bot)
car_handler(bot)
todo_handler(bot)
tashkeel_handler(bot)
reminders_handler(bot)
print("✅ البوت يعمل بنظام الملفات...")
bot.polling(none_stop=True)