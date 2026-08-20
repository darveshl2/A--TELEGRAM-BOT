import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (аз Environment Variables мегирад)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin Telegram ID
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# Database path (роҳи бехатар)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "bot.db")

# Bot settings
BOT_NAME = "AVALIN SECURITY BOT"
VERSION = "1.0.0"
