import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("8996039934:AAFaVo2VlVmZpdxfavRqND_oTp8VNUB9hu8")

# Admin Telegram ID
ADMIN_ID = int(os.getenv("ADMIN_ID", "78750558715"))

# Database
DATABASE = "data/bot.db"

# Bot settings
BOT_NAME = "AVALIN SECURITY BOT"
VERSION = "1.0.0"
