import os
import telebot
from telebot import types
from groq import Groq
from flask import Flask
from threading import Thread

# Сервери Flask барои бастани порт дар Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# Гирифтани токенҳо аз Environment Variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# Танзими системавии универсалӣ (AI System Prompt)
SYSTEM_PROMPT = """
Шумо системаи пешрафтатарини интеллектуалӣ (AI) ва коршиноси ҳаматарафа ҳастед. 
Вазифаҳои шумо:
1. Киберамният ва Хакерӣ: Таҳлили заъфҳои системаҳо, Penetration Testing, таҳлили форензикӣ, бехатарии шабакаҳо ва навиштани скриптҳо (Python, Bash, C++).
2. Барномасозӣ: Навиштани кодҳои мураккаб, веб-девелопмент, эҷоди ботҳо ва автоматизатсия.
3. Кор бо рақамҳои телефон: Таҳлили сохтор, рамзҳои кишварҳо, OSINT ва роҳҳои бехатарии рақамҳо.
4. Монтаж ва Видео: Машварат ва навиштани скриптҳо барои монтажи видео (CapCut, Premiere Pro), коркарди тасвир ва эффектҳо.
5. Таҳлили Link (Истинодҳо): Таҳлили бехатарии URL, муайян кардани фишинг ва фиристодани истинодҳои зарурӣ.
6. Забон: Ҳамеша бо забоне, ки корбар муроҷиат мекунад, посухи амиқ ва касбӣ диҳед.
"""

# Рӯйхати 50 давлати ҷаҳон
COUNTRIES = [
    "🇹🇯 Тоҷикистон", "🇷🇺 Русия", "🇹🇷 Туркия", "🇺🇸 ИМА", "🇬🇧 Британия",
    "🇨🇳 Чин", "🇩🇪 Олмон", "🇫🇷 Фаронса", "🇸🇦 Арабистони Саудӣ", "🇦🇪 Аморати Муттаҳида",
    "🇺🇿 Ӯзбекистон", "🇰🇿 Қазоқистон", "🇰🇬 Қирғизистон", "🇹🇲 Туркманистон", "🇮🇷 Эрон",
    "🇨🇦 Канада", "🇯🇵 Ҷопон", "🇰🇷 Кореяи Ҷанубӣ", "🇮🇳 Ҳиндустон", "🇵🇰 Покистон",
    "🇮🇹 Италия", "🇪🇸 Испания", "🇵🇹 Португалия", "🇳🇱 Нидерландия", "🇨🇭 Швейтсария",
    "🇸🇪 Шведсия", "🇳🇴 Норвегия", "🇫🇮 Финляндия", "🇵🇱 Польша", "🇺АК Украина",
    "🇦🇿 Озарбойҷон", "🇬🇪 Гурҷистон", "🇦🇲 Арманистон", "🇪🇬 Миср", "🇶🇦 Қатар",
    "🇧🇷 Бразилия", "🇲🇽 Мексика", "🇦🇺 Австралия", "🇦🇷 Аргентина", "🇲🇦 Марокаш",
    "🇮🇩 Индонезия", "🇲🇾 Малайзия", "🇹🇭 Таиланд", "🇻🇳 Вйетнам", "🇸🇬 Сингапур",
    "🇧🇪 Беларус", "🇲🇩 Молдова", "🇮🇱 Исроил", "🇿🇦 Африқои Ҷанубӣ", "🇳🇬 Нигерия"
]

def get_country_keyboard(page=0):
    markup = types.InlineKeyboardMarkup(row_width=2)
    start_idx = page * 10
    end_idx = start_idx + 10
    current_countries = COUNTRIES[start_idx:end_idx]
    
    buttons = [types.InlineKeyboardButton(text=c, callback_data=f"country_{c}") for c in current_countries]
    markup.add(*buttons)
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️ Оқиб", callback_data=f"page_{page-1}"))
    if end_idx < len(COUNTRIES):
        nav_buttons.append(types.InlineKeyboardButton(text="Пеш ➡️", callback_data=f"page_{page+1}"))
    
    if nav_buttons:
        markup.add(*nav_buttons)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = "Салом! Ман боти супер-интеллектуалӣ ҳастам.\n\nИмкониятҳо:\n- Киберамният ва Хакерӣ\n- Барномасозӣ ва Кодкунӣ\n- Кор бо рақамҳои телефон ва Link-ҳо\n- Монтаж ва кор бо видео\n\nБарои интихоби давлат тугмаи зерро пахш кунед:"
    bot.send_message(message.chat.id, text, reply_markup=get_country_keyboard(0))

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    if call.data.startswith("page_"):
        page = int(call.data.split("_")[1])
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_country_keyboard(page))
    elif call.data.startswith("country_"):
        country_name = call.data.replace("country_", "")
        bot.send_message(call.message.chat.id, f"Шумо кишвари **{country_name}**-ро интихоб кардед. Оид ба коду амният ё рақамҳои ин кишвар чӣ савол доред?")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Рӯйхати моделҳои фаъол ва пурқуввати Groq
        models = [
            "llama-3.1-8b-instant",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        
        answer = None
        last_error = ""

        for m in models:
            try:
                response = client.chat.completions.create(
                    model=m,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message.text}
                    ],
                    temperature=0.7
                )
                if response and response.choices:
                    answer = response.choices[0].message.content
                    break
            except Exception as err:
                last_error = str(err)
                continue

        if not answer:
            answer = f"Хатогӣ: Моделҳо ҷавоб надоданд. Сабаб: {last_error}"

        if len(answer) > 4000:
            for x in range(0, len(answer), 4000):
                bot.send_message(message.chat.id, answer[x:x+4000])
        else:
            bot.send_message(message.chat.id, answer)

    except Exception as e:
        bot.send_message(message.chat.id, f"Хатогии системавӣ: {e}")
