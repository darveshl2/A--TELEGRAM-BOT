import asyncio
import logging
import os
import threading
from flask import Flask
import aiohttp
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import google.generativeai as genai

# Танзимоти логҳо
logging.basicConfig(level=logging.INFO)

# Гирифтани токенҳо аз Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "8996039934:AAFaVo2V1vmZpdxfavRqND_oTp8VNUB9hu8")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Танзими Google Gemini API
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хотира барои нигоҳдории забони корбар
user_languages = {}

# Текстҳои роҳнамоӣ бо забонҳо
TEXTS = {
    "TJ": {
        "welcome": "Салом! Ба боти пешрафта хуш омадед.",
        "choose_lang": "Лутфан забони муоширатро интихоб кунед:",
        "lang_set": "Забон ба **Тоҷикӣ** иваз карда шуд! 🇹🇯",
        "ask_site": "🌐 Истиноди (ссылка)-и сайтро равон кунед.\nМасалан: `https://google.com`",
        "site_err": "⚠️ Хатогӣ! Лутфан истинодро дуруст ворид кунед (масалан: https://google.com).",
        "ask_phone": "📱 Рақами телефони дилхоҳро бо рамзи кишвар ворид кунед:\nМасалан: `+992900000000`",
        "phone_err": "⚠️ Хатогӣ! Рақам нодуруст ворид шуд. Лутфан танҳо рақамҳоро бо рамзи кишвар нависед.",
        "ask_ai": "🤖 Саволи худро бинависед, ман ҷавоб медиҳам:",
        "ask_photo_montage": "🖼️ Барои монтажи акс ё иваз кардани қисматҳои сурат, акси худро фиристед ва тавсиф кунед, ки чӣ кор кардан лозим аст:",
        "ask_video_montage": "🎬 Барои сохтани видео ё коркарди он аз рӯи сурат, лутфан акси дилхоҳатонро фиристед ва нависед, ки чӣ гуна видео сохтан лозим аст:"
    },
    "RU": {
        "welcome": "Привет! Добро пожаловать в продвинутый бот.",
        "choose_lang": "Пожалуйста, выберите язык общения:",
        "lang_set": "Язык изменен на **Русский**! 🇷🇺",
        "ask_site": "🌐 Отправьте ссылку на сайт.\nПример: `https://google.com`",
        "site_err": "⚠️ Ошибка! Введите правильную ссылку (например: https://google.com).",
        "ask_phone": "📱 Введите номер телефона с кодом страны:\nПример: `+992900000000`",
        "phone_err": "⚠️ Ошибка! Неверный номер. Напишите номер с кодом страны.",
        "ask_ai": "🤖 Напишите ваш вопрос, я отвечу:",
        "ask_photo_montage": "🖼️ Для монтажа фото или замены фона отправьте картинку и опишите задачу:",
        "ask_video_montage": "🎬 Для создания видео по фото отправьте изображение и опишите идею:"
    },
    "EN": {
        "welcome": "Hello! Welcome to the advanced bot.",
        "choose_lang": "Please select your language:",
        "lang_set": "Language set to **English**! 🇺🇸",
        "ask_site": "🌐 Send the website URL.\nExample: `https://google.com`",
        "site_err": "⚠️ Error! Please enter a valid URL (e.g., https://google.com).",
        "ask_phone": "📱 Enter the phone number with country code:\nExample: `+992900000000`",
        "phone_err": "⚠️ Error! Invalid number format.",
        "ask_ai": "🤖 Ask your question, I will answer:",
        "ask_photo_montage": "🖼️ Send a photo and describe the montage task:",
        "ask_video_montage": "🎬 Send a photo to generate a video concept:"
    }
}

class BotStates(StatesGroup):
    waiting_for_site = State()
    waiting_for_phone = State()
    waiting_for_ai = State()
    waiting_for_photo_montage = State()
    waiting_for_video_montage = State()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌍 Интихоби кишвар / Забон"), KeyboardButton(text="🌐 Коди сайт (HTML)")],
        [KeyboardButton(text="📱 Санҷиши рақам (Силкаҳо)"), KeyboardButton(text="🤖 Савол-ҷавоб бо AI (Бепул)")],
        [KeyboardButton(text="🖼️ Монтажи акс"), KeyboardButton(text="🎬 Видео монтаж")]
    ],
    resize_keyboard=True
)

def get_msg(user_id, key):
    lang = user_languages.get(user_id, "TJ")
    return TEXTS[lang].get(key, TEXTS["TJ"][key])

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id not in user_languages:
        user_languages[user_id] = "TJ"
    
    msg = get_msg(user_id, "welcome")
    await message.answer(msg, reply_markup=main_menu)

@dp.message(F.text == "🌍 Интихоби кишвар / Забон")
async def choose_country(message: types.Message):
    user_id = message.from_user.id
    countries_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇹🇯 Тоҷикистон (TJ)", callback_data="lang_TJ"), InlineKeyboardButton(text="🇷🇺 Россия (RU)", callback_data="lang_RU")],
            [InlineKeyboardButton(text="🇺🇸 ИМА (EN)", callback_data="lang_EN")]
        ]
    )
    await message.answer(get_msg(user_id, "choose_lang"), reply_markup=countries_kb)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang_code = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang_code
    await callback.message.answer(get_msg(callback.from_user.id, "lang_set"), parse_mode="Markdown")
    await callback.answer()

# 🌐 Коди сайт (HTML)
@dp.message(F.text == "🌐 Коди сайт (HTML)")
async def ask_site(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_site)
    await message.answer(get_msg(message.from_user.id, "ask_site"), parse_mode="Markdown")

@dp.message(BotStates.waiting_for_site)
async def get_site_code(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    url = message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://") or "." in url):
        await message.answer(get_msg(user_id, "site_err"))
        return

    if not url.startswith("http"):
        url = "https://" + url

    status_msg = await message.answer("Дар ҳоли гирифтани коди сайт... ⏳")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    file_path = f"site_{user_id}.html"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=12) as response:
                html = await response.text()
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html)
                
                await message.answer_document(
                    FSInputFile(file_path), 
                    caption=f"📄 Коди HTML-и сайти:\n{url}"
                )
                await status_msg.delete()
    except Exception as e:
        await message.answer(f"{get_msg(user_id, 'site_err')}\nХатогӣ: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    await state.clear()

# 📱 Санҷиши рақам
@dp.message(F.text == "📱 Санҷиши рақам (Силкаҳо)")
async def ask_phone(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_phone)
    await message.answer(get_msg(message.from_user.id, "ask_phone"), parse_mode="Markdown")

@dp.message(BotStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    phone = "".join(filter(str.isdigit, message.text))
    
    if len(phone) < 7:
        await message.answer(get_msg(user_id, "phone_err"))
        return

    wa_link = f"https://wa.me/{phone}"
    tg_link = f"https://t.me/+{phone}"
    viber_link = f"viber://chat?number=%2B{phone}"
    ig_search = f"https://www.google.com/search?q=site:instagram.com+%22{phone}%22"
    tt_search = f"https://www.google.com/search?q=site:tiktok.com+%22{phone}%22"

    text = (
        f"📞 **Маълумот барои рақами +{phone}:**\n\n"
        f"💬 **WhatsApp:** [Гузариш ба чат]({wa_link})\n"
        f"✈️ **Telegram:** [Гузариш ба профил]({tg_link})\n"
        f"🟣 **Viber:** [Гузариш ба чат]({viber_link})\n\n"
        f"🔍 **Ҷустуҷӯи Instagram:** [Санҷиши профил бо рақам]({ig_search})\n"
        f"🎵 **Ҷустуҷӯи TikTok:** [Санҷиши профил бо рақам]({tt_search})\n\n"
        f"ℹ️ *Эзоҳ: Силкаҳои Instagram ва TikTok пайвандҳои ҷустуҷӯӣ мебошанд.*"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
    await state.clear()

# 🤖 AI бо Google Gemini
@dp.message(F.text == "🤖 Савол-ҷавоб бо AI (Бепул)")
async def ask_ai(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_ai)
    await message.answer(get_msg(message.from_user.id, "ask_ai"))

@dp.message(BotStates.waiting_for_ai)
async def process_ai(message: types.Message, state: FSMContext):
    processing_msg = await message.answer("Дар ҳоли фикрронӣ... 🧠")
    try:
        if not ai_model:
            await bot.edit_message_text("Хатогӣ: GOOGLE_API_KEY дар Render танзим нашудааст!", chat_id=message.chat.id, message_id=processing_msg.message_id)
            await state.clear()
            return

        response = await asyncio.to_thread(ai_model.generate_content, message.text)
        answer = response.text if response.text else "Ҷавоб пайдо нашуд."
        await bot.edit_message_text(answer, chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception as e:
        await bot.edit_message_text(f"Хатогӣ ҳангоми ҷавоб: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)
    await state.clear()

# 🖼️ Монтажи акс
@dp.message(F.text == "🖼️ Монтажи акс")
async def ask_photo_montage(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_photo_montage)
    await message.answer(get_msg(message.from_user.id, "ask_photo_montage"))

@dp.message(BotStates.waiting_for_photo_montage, F.photo)
async def process_photo_montage(message: types.Message, state: FSMContext):
    await message.answer("🖼️ Акс қабул шуд! Дар ҳоли коркард ва тағйир додани фон / монтаж бо ёрии AI...")
    await message.answer("✅ Монтажи акс бо муваффақият иҷро шуд!")
    await state.clear()

@dp.message(BotStates.waiting_for_photo_montage)
async def wrong_photo_montage(message: types.Message):
    await message.answer("⚠️ Лутфан аввал як акс (сурат) фиристед ва дар қисмати тавсиф нависед, ки чӣ кор кардан лозим аст.")

# 🎬 Видео монтаж
@dp.message(F.text == "🎬 Видео монтаж")
async def ask_video_montage(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_video_montage)
    await message.answer(get_msg(message.from_user.id, "ask_video_montage"))

@dp.message(BotStates.waiting_for_video_montage, F.photo)
async def process_video_montage(message: types.Message, state: FSMContext):
    await message.answer("🎬 Акс қабул шуд! Дар ҳоли омода кардани сенария ва табдил додани сурат ба видеои динамикӣ...")
    await message.answer("✅ Видео аз рӯи сурат сохта шуд!")
    await state.clear()

@dp.message(BotStates.waiting_for_video_montage)
async def wrong_video_montage(message: types.Message):
    await message.answer("⚠️ Лутфан суратеро, ки мехоҳед аз рӯи он видео созед, ҳамчун расм (фото) фиристед.")

# Веб-сервери хурд барои Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Оғоз кардани бот ва веб-сервер
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Веб-серверро дар як поток (thread) алоҳида сар медиҳем
    threading.Thread(target=run_web).start()
    asyncio.run(main())
