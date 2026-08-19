import os
import requests
import telebot
from telebot import types
import google.generativeai as genai
from flask import Flask
from threading import Thread

# Сервери Flask барои фаъол нигоҳ доштани бот дар Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running with API Tokens!"

def run_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# Гирифтани тамоми токенҳо аз Environment Variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SHODAN_API_KEY = os.environ.get("SHODAN_API_KEY")
VIRUSTOTAL_API_KEY = os.environ.get("VIRUSTOTAL_API_KEY")
ABUSEIPDB_API_KEY = os.environ.get("ABUSEIPDB_API_KEY")

# Танзими Google Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Менюи асосӣ
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💬 AI Сӯҳбат", "🔍 Shodan IP")
    markup.row("🛡 VirusTotal URL", "📊 AbuseIPDB Check")
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    text = (
        "Салом! Боти бисёрфунксионалӣ бо пайвасти API-Токенҳо фаъол аст.\n\n"
        "Хидматҳои пайвастшуда:\n"
        "1. 💬 Google Gemini AI API (Сӯҳбат ва таҳлил ба 50+ забон)\n"
        "2. 🔍 Shodan API (Таҳлили портҳо ва серверҳо)\n"
        "3. 🛡 VirusTotal API (Санҷиши бехатарии истинодҳо)\n"
        "4. 📊 AbuseIPDB API (Санҷиши репутатсияи IP)"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())

# 1. Shodan API
@bot.message_handler(func=lambda m: m.text == "🔍 Shodan IP")
def ask_shodan(message):
    msg = bot.send_message(message.chat.id, "IP-суроғаро ворид кунед (масалан: 8.8.8.8):")
    bot.register_next_step_handler(msg, process_shodan)

def process_shodan(message):
    if not SHODAN_API_KEY:
        bot.send_message(message.chat.id, "❌ SHODAN_API_KEY дар Render танзим нашудааст.")
        return
    
    ip = message.text.strip()
    url = f"https://api.shodan.io/shodan/host/{ip}?key={SHODAN_API_KEY}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            ports = data.get('ports', [])
            org = data.get('org', 'Номаълум')
            country = data.get('country_name', 'Номаълум')
            bot.send_message(message.chat.id, f"🔍 **Shodan Report ({ip}):**\n\n▫️ Кишвар: {country}\n▫️ Ташкилот: {org}\n▫️ Портҳои кушода: {ports}", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❌ Маълумот ёфта нашуд ё хатогии API: {res.status_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Хатогӣ: {e}")

# 2. VirusTotal API
@bot.message_handler(func=lambda m: m.text == "🛡 VirusTotal URL")
def ask_virustotal(message):
    msg = bot.send_message(message.chat.id, "Истинод (URL)-ро барои санҷиш фиристед:")
    bot.register_next_step_handler(msg, process_virustotal)

def process_virustotal(message):
    if not VIRUSTOTAL_API_KEY:
        bot.send_message(message.chat.id, "❌ VIRUSTOTAL_API_KEY дар Render танзим нашудааст.")
        return

    target_url = message.text.strip()
    endpoint = "https://www.virustotal.com/api/v3/urls"
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    
    try:
        res = requests.post(endpoint, headers=headers, data={"url": target_url}, timeout=10)
        if res.status_code in [200, 201]:
            bot.send_message(message.chat.id, f"✅ URL ба VirusTotal фиристода шуд. Анализ оғоз ёфт.")
        else:
            bot.send_message(message.chat.id, f"❌ Хатогии VirusTotal API: {res.status_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Хатогӣ: {e}")

# 3. AbuseIPDB API
@bot.message_handler(func=lambda m: m.text == "📊 AbuseIPDB Check")
def ask_abuseipdb(message):
    msg = bot.send_message(message.chat.id, "IP-суроғаро барои санҷиш ворид кунед:")
    bot.register_next_step_handler(msg, process_abuseipdb)

def process_abuseipdb(message):
    if not ABUSEIPDB_API_KEY:
        bot.send_message(message.chat.id, "❌ ABUSEIPDB_API_KEY дар Render танзим нашудааст.")
        return

    ip = message.text.strip()
    endpoint = "https://api.abuseipdb.com/api/v2/check"
    headers = {"Key": ABUSEIPDB_API_KEY, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": "90"}

    try:
        res = requests.get(endpoint, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json().get("data", {})
            score = data.get("abuseConfidenceScore", 0)
            country = data.get("countryCode", "Номаълум")
            usage = data.get("usageType", "Номаълум")
            bot.send_message(message.chat.id, f"📊 **AbuseIPDB ({ip}):**\n\n▫️ Дараҷаи хатар: {score}%\n▫️ Кишвар: {country}\n▫️ Навъи истифода: {usage}", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❌ Хатогии API: {res.status_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Хатогӣ: {e}")

# 4. Google Gemini AI Handler
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    if not GEMINI_API_KEY:
        bot.send_message(message.chat.id, "❌ GEMINI_API_KEY танзим нашудааст.")
        return

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        response = ai_model.generate_content(message.text)
        answer = response.text

        if len(answer) > 4000:
            for x in range(0, len(answer), 4000):
                bot.send_message(message.chat.id, answer[x:x+4000])
        else:
            bot.send_message(message.chat.id, answer)
    except Exception as e:
        bot.send_message(message.chat.id, f"Хатогии AI: {e}")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.infinity_polling()
