import os
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("🤖 AI Чат", callback_data="ai"),
            InlineKeyboardButton("🌍 Забон", callback_data="language")
        ],
        [
            InlineKeyboardButton("🐍 Python", callback_data="python"),
            InlineKeyboardButton("🖼 Сурат", callback_data="image")
        ],
        [
            InlineKeyboardButton("📚 PDF", callback_data="pdf"),
            InlineKeyboardButton("🛡 Амният", callback_data="security")
        ]
    ]

    await update.message.reply_text(
        "👋 Салом!\n\n"
        "Ман ёвари бисёрфунксионалӣ ҳастам.\n"
        "Системаи ман дар ҳоли рушд аст.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Тугмаҳо
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    answers = {
        "ai": "🧠 AI Chat фаъол мешавад.",
        "language": "🌍 Интихоби забонҳо илова мешавад.",
        "python": "🐍 Python Assistant омода мешавад.",
        "image": "🖼 Системаи сурат пайваст мешавад.",
        "pdf": "📚 Системаи PDF сохта мешавад.",
        "security": "🛡 White-hat Security омӯзишӣ фаъол мешавад."
    }

    await query.edit_message_text(
        answers.get(data, "Функсия ёфт нашуд.")
    )


# Паёмҳои корбар
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user

    text = update.message.text

    await update.message.reply_text(
        f"👤 Корбар: {user.first_name}\n"
        f"⏰ Вақт: {datetime.now()}\n\n"
        f"Шумо навиштед:\n{text}\n\n"
        "🤖 AI дар версияи оянда пайваст мешавад."
    )


def main():

    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN ёфт нашуд. Дар Render Environment илова кунед."
        )

    app = Application.builder().token(TOKEN).build()


    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    app.add_handler(
        MessageHandler(filters.TEXT, chat)
    )


    print("BOT STARTED 24/7")

async def run_bot():
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    import asyncio
    await asyncio.Event().wait()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_bot())
