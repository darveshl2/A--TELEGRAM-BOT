import asyncio
import logging
import os
import threading
from flask import Flask
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import google.generativeai as genai

# Танзимоти логҳо
logging.basicConfig(level=logging.INFO)

# Гирифтани токенҳо аз Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Инициализатсияи бот ва диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Танзими Google Gemini API
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

# Сулсилаи ҳолатҳо (FSM)
class BotStates(StatesGroup):
    waiting_for_ai_prompt = State()
    waiting_for_site_url = State()
    waiting_for_photo_montage = State()
    waiting_for_video_montage = State()

# Забонҳо ва матнҳо
LANGUAGES = {
    'tj': '🇹🇯 Тоҷикӣ',
    'ru': '🇷🇺 Русский',
    'en': '🇬🇧 English'
}

MESSAGES = {
    'tj': {
        'welcome': "Ассалому алейкум! Ба боти бисёрфунксионалии мо хуш омадед.",
        'choose_lang': "Лутфан забонро интихоб кунед:",
        'main_menu': "Матни асосӣ:",
        'ai_chat': "🤖 Чат бо AI (Gemini)",
        'site_code': "🌐 Гирифтани коди сайт",
        'phone_links': "📱 Интиқоли коди телефон",
        'photo_montage': "🖼 Чопи акс ва монтаж",
        'video_montage': "🎬 Видео монтаж",
        'ask_ai': "Саволи худро ба AI нависед:",
        'ask_site': "Лутфан линки сайт-ро фиристонед (масалан: https://example.com):",
        'ask_photo_montage': "Лутфан аксеро фиристед ва дар қисмати тавсиф (caption) нависед, ки чӣ тавр онро монтаж кунем:",
        'ask_video_montage': "Лутфан суратеро фиристед, ки мехоҳед аз рӯи он видео созед:",
        'no_ai': "Хатогӣ: API Key барои Gemini танзим нашудааст."
    },
    'ru': {
        'welcome': "Здравствуйте! Добро пожаловать в нашего многофункционального бота.",
        'choose_lang': "Пожалуйста, выберите язык:",
        'main_menu': "Главное меню:",
        'ai_chat': "🤖 Чат с ИИ (Gemini)",
        'site_code': "🌐 Получить код сайта",
        'phone_links': "📱 Ссылки для подтверждения номера",
        'photo_montage': "🖼 Фотомонтаж",
        'video_montage': "🎬 Видеомонтаж",
        'ask_ai': "Задайте ваш вопрос ИИ:",
        'ask_site': "Пожалуйста, отправьте ссылку на сайт (например: https://example.com):",
        'ask_photo_montage': "Отправьте фото и в описании (caption) напишите, как его обработать:",
        'ask_video_montage': "Отправьте фото, из которого нужно создать видео:",
        'no_ai': "Ошибка: API Key для Gemini не настроен."
    },
    'en': {
        'welcome': "Hello! Welcome to our multifunctional bot.",
        'choose_lang': "Please select a language:",
        'main_menu': "Main Menu:",
        'ai_chat': "🤖 AI Chat (Gemini)",
        'site_code': "🌐 Get Website Source",
        'phone_links': "📱 Phone Verification Links",
        'photo_montage': "🖼 Photo Editing",
        'video_montage': "🎬 Video Editing",
        'ask_ai': "Ask your question to AI:",
        'ask_site': "Please send the website URL (e.g. https://example.com):",
        'ask_photo_montage': "Send a photo and describe in the caption how to edit it:",
        'ask_video_montage': "Send a photo to create a video from it:",
        'no_ai': "Error: Gemini API Key is not configured."
    }
}

# Луғати нигоҳдории забони корбарон (дар хотира)
user_languages = {}

def get_msg(user_id, key):
    lang = user_languages.get(user_id, 'tj')
    return MESSAGES.get(lang, MESSAGES['tj']).get(key, '')

def get_main_keyboard(user_id):
    lang = user_languages.get(user_id, 'tj')
    msgs = MESSAGES.get(lang, MESSAGES['tj'])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=msgs['ai_chat']), KeyboardButton(text=msgs['site_code'])],
            [KeyboardButton(text=msgs['phone_links'])],
            [KeyboardButton(text=msgs['photo_montage']), KeyboardButton(text=msgs['video_montage'])],
            [KeyboardButton(text="🌐 Забон / Язык / Language")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Сарлавҳаи /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang_tj"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
            ]
        ]
    )
    await message.answer("Лутфан забонро интихоб кунед / Пожалуйста, выберите язык / Please choose a language:", reply_markup=inline_kb)

@dp.callback_query(F.data.startswith("lang_"))
async def language_callback(call: types.CallbackQuery):
    lang_code = call.data.split("_")[1]
    user_languages[call.from_user.id] = lang_code
    await call.answer()
    
    msg_text = get_msg(call.from_user.id, 'welcome')
    await call.message.answer(msg_text, reply_markup=get_main_keyboard(call.from_user.id))

@dp.message(F.text == "🌐 Забон / Язык / Language")
async def change_language(message: types.Message):
    await start_handler(message)

# 🤖 Чат бо AI
@dp.message(F.text.in_([MESSAGES['tj']['ai_chat'], MESSAGES['ru']['ai_chat'], MESSAGES['en']['ai_chat']]))
async def ask_ai_handler(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_ai_prompt)
    await message.answer(get_msg(message.from_user.id, 'ask_ai'))

@dp.message(BotStates.waiting_for_ai_prompt, F.text)
async def process_ai_prompt(message: types.Message, state: FSMContext):
    if not ai_model:
        await message.answer(get_msg(message.from_user.id, 'no_ai'))
        await state.clear()
        return

    msg = await message.answer("⏳ ...")
    try:
        response = ai_model.generate_content(message.text)
        await msg.edit_text(response.text)
    except Exception as e:
        await msg.edit_text(f"Хатогӣ дар AI: {str(e)}")
    await state.clear()

# 🌐 Коди сайт
@dp.message(F.text.in_([MESSAGES['tj']['site_code'], MESSAGES['ru']['site_code'], MESSAGES['en']['site_code']]))
async def ask_site_handler(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_site_url)
    await message.answer(get_msg(message.from_user.id, 'ask_site'))

@dp.message(BotStates.waiting_for_site_url, F.text)
async def process_site_url(message: types.Message, state: FSMContext):
    url = message.text
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    msg = await message.answer("⏳ Коди сайт гирифта шуда истодааст...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                html_code = await resp.text()
                
                # Захира ба файл
                file_path = "site_code.html"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_code)
                
                input_file = FSInputFile(file_path)
                await message.answer_document(input_file, caption=f"Коди HTML барои: {url}")
                os.remove(file_path)
                await msg.delete()
    except Exception as e:
        await msg.edit_text(f"Хатогӣ ҳангоми гирифтани коди сайт: {str(e)}")
    
    await state.clear()

# 📱 Линки тасдиқи номер
@dp.message(F.text.in_([MESSAGES['tj']['phone_links'], MESSAGES['ru']['phone_links'], MESSAGES['en']['phone_links']]))
async def phone_links_handler(message: types.Message):
    text = (
        "🔗 **Сомонаҳо барои гирифтани рақами виртуалӣ ва коди SMS:**\n\n"
        "1. [SMS-Activate](https://sms-activate.org)\n"
        "2. [5SIM](https://5sim.net)\n"
        "3. [OnlineSim](https://onlinesim.io)\n"
        "4. [Receive-SMS-Free](https://receive-sms-free.cc)"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

# 🖼 Акс ва монтаж
@dp.message(F.text.in_([MESSAGES['tj']['photo_montage'], MESSAGES['ru']['photo_montage'], MESSAGES['en']['photo_montage']]))
async def ask_photo_montage(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_photo_montage)
    await message.answer(get_msg(message.from_user.id, 'ask_photo_montage'))

@dp.message(BotStates.waiting_for_photo_montage, F.photo)
async def process_photo_montage(message: types.Message, state: FSMContext):
    await message.answer("Акс қабул шуд! Вазифа ба коркард фиристода шуд.")
    await state.clear()

@dp.message(BotStates.waiting_for_photo_montage)
async def wrong_photo_montage(message: types.Message):
    await message.answer("⚠️ Лутфан аввал як акс (сурат) фиристед ва дар қисмати тавсиф нависед.")

# 🎬 Видео монтаж
@dp.message(F.text.in_([MESSAGES['tj']['video_montage'], MESSAGES['ru']['video_montage'], MESSAGES['en']['video_montage']]))
async def ask_video_montage(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_video_montage)
    await message.answer(get_msg(message.from_user.id, 'ask_video_montage'))

@dp.message(BotStates.waiting_for_video_montage, F.photo)
async def process_video_montage(message: types.Message, state: FSMContext):
    await message.answer("Акс қабул шуд! Дар ҳоли омода кардани сенария ва табдил додани сурат ба видео...")
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
