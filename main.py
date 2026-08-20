import logging
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from database import init_db, add_user
from config import BOT_TOKEN, ADMIN_ID


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# ===== MENU =====

main_menu = [
    ["👤 Профил", "🛡 Амният"],
    ["📚 Академия", "🧰 Асбобҳо"],
    ["📊 Статистика", "⚙️ Танзимот"]
]


# ===== START =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    await add_user(
        user.id,
        user.username or "NoUsername"
    )

    keyboard = ReplyKeyboardMarkup(
        main_menu,
        resize_keyboard=True
    )

    await update.message.reply_text(
        f"🤖 AVALIN SECURITY BOT\n\n"
        f"Салом, {user.first_name}!\n\n"
        "Ба системаи White Hat Security хуш омадед.",
        reply_markup=keyboard
    )


# ===== BUTTONS =====

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "👤 Профил":

        user = update.effective_user

        await update.message.reply_text(
            f"👤 Профил\n\n"
            f"ID: {user.id}\n"
            f"Username: @{user.username}"
        )


    elif text == "📚 Академия":

        await update.message.reply_text(
            "📚 Cyber Academy\n\n"
            "1. Linux\n"
            "2. Python Security\n"
            "3. Network\n"
            "4. TCP/IP\n"
            "5. Web Security\n"
            "6. OWASP Top 10\n"
            "7. CTF Training"
        )


    elif text == "🛡 Амният":

        await update.message.reply_text(
            "🛡 Security System\n\n"
            "✅ Anti Spam\n"
            "✅ User Permission\n"
            "✅ Logs"
        )


    elif text == "🧰 Асбобҳо":

        await update.message.reply_text(
            "🧰 Tools\n\n"
            "Security tools section"
        )


    elif text == "📊 Статистика":

        await update.message.reply_text(
            "📊 Statistics\n\n"
            "System statistics"
        )


    elif text == "⚙️ Танзимот":

        await update.message.reply_text(
            "⚙️ Settings"
        )


# ===== MAIN =====

async def main():

    await init_db()

    app = Application.builder().token(BOT_TOKEN).build()


    app.add_handler(
        CommandHandler("start", start)
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            buttons
        )
    )


    print("AVALIN BOT STARTED")


    await app.run_polling()



if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    # ===== START COMMAND =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await add_user(
        user.id,
        user.username
    )

    keyboard = [
        ["👤 Профил", "🛡 Амният"],
        ["📚 Академия", "🧰 Асбобҳо"],
        ["📊 Статистика", "⚙️ Танзимот"]
    ]

    reply = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        f"""
🤖 AVALIN SECURITY BOT

Салом {user.first_name} 👋

Ин бот барои омӯзиши:
🛡 White Hat Security
🐧 Linux
🐍 Python
🌐 Network
🔐 Cyber Security

истифода мешавад.
        """,
        reply_markup=reply
    )


# ===== BUTTON HANDLER =====

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "📚 Академия":
        await update.message.reply_text(
            """
📚 Cyber Academy

1️⃣ Linux Basics
2️⃣ Python Security
3️⃣ TCP/IP
4️⃣ Network Fundamentals
5️⃣ OWASP Top 10
6️⃣ Web Security
7️⃣ Ethical Hacking
8️⃣ CTF Training
            """
        )

    elif text == "🛡 Амният":
        await update.message.reply_text(
            """
🛡 Security System

✅ Anti Spam
✅ User Control
✅ Logs
✅ Permission System
✅ Backup Database
            """
        )

    elif text == "👤 Профил":
        user = update.effective_user

        await update.message.reply_text(
            f"""
👤 Profile

ID: {user.id}
Username: @{user.username}
            """
        )

    elif text == "📊 Статистика":
        await update.message.reply_text(
            "📊 Statistics system фаъол мешавад..."
        )

    elif text == "⚙️ Танзимот":
        await update.message.reply_text(
            "⚙️ Settings"
        )

    elif text == "🧰 Асбобҳо":
        await update.message.reply_text(
            """
🧰 Tools

🔎 Security checklist
🌐 Network info
📖 Learning tools
            """
        )
# ===== BOT START =====

def main():
    asyncio.run(init_db())

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            buttons
        )
    )

    print("🔒 AVALIN SECURITY BOT STARTED")

    app.run_polling()

if __name__ == "__main__":
    import asyncio
    main()
