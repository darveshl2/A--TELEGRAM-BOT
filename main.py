import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


TOKEN = os.getenv("BOT_TOKEN")


if not TOKEN:
    raise ValueError("BOT_TOKEN ёфт нашуд. Дар Render Environment илова кунед.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📌 Меню", callback_data="menu"),
            InlineKeyboardButton("ℹ️ Маълумот", callback_data="info")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Салом 👋\nБот фаъол аст.",
        reply_markup=reply_markup
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu":
        await query.edit_message_text(
            "📋 Меню:\n\n"
            "1. Хизматрасонӣ\n"
            "2. Маълумот\n"
            "3. Тамос"
        )

    elif query.data == "info":
        await query.edit_message_text(
            "🤖 Ин Telegram бот аст."
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    await update.message.reply_text(
        f"Шумо навиштед:\n{text}"
    )


async def error_handler(update, context):
    logging.error(
        f"Error: {context.error}"
    )


def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(buttons)
    )

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    app.add_error_handler(error_handler)

    print("BOT STARTED 24/7")

    app.run_polling()


if __name__ == "__main__":
    main()
