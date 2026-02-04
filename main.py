from pathlib import Path
import os
import sqlite3
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ------------------ ENV ------------------
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ------------------ DATABASE ------------------
DB_PATH = "storage.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_type TEXT,
            file_id TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_file(user_id, file_type, file_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO files (user_id, file_type, file_id) VALUES (?, ?, ?)",
        (user_id, file_type, file_id)
    )
    conn.commit()
    conn.close()

def get_files(user_id, file_type):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT file_id FROM files WHERE user_id=? AND file_type=?",
        (user_id, file_type)
    )
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

# ------------------ UI ------------------
def main_menu():
    keyboard = [
        ["📄 My Documents", "🖼️ My Photos"],
        ["🎥 My Videos"],
        ["ℹ️ Help"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ------------------ COMMANDS ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Send me documents, photos, or videos.\n"
        "I’ll save them safely for you.\n\n"
        "👇 Use the menu below:",
        reply_markup=main_menu()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Help*\n\n"
        "📄 My Documents – get your documents\n"
        "🖼️ My Photos – get your photos\n"
        "🎥 My Videos – get your videos\n\n"
        "📤 Just send files to save them.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ------------------ MEDIA SAVE (Telegram storage) ------------------
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = msg.from_user.id

    if msg.document:
        save_file(user_id, "document", msg.document.file_id)
        await msg.reply_text("📄 Document saved")

    elif msg.photo:
        save_file(user_id, "photo", msg.photo[-1].file_id)
        await msg.reply_text("🖼️ Photo saved")

    elif msg.video:
        save_file(user_id, "video", msg.video.file_id)
        await msg.reply_text("🎥 Video saved")

# ------------------ MEDIA SEND ------------------
async def send_documents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = get_files(update.message.from_user.id, "document")
    if not files:
        await update.message.reply_text("📂 No documents found.")
        return
    for f in files:
        await update.message.reply_document(f)

async def send_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = get_files(update.message.from_user.id, "photo")
    if not files:
        await update.message.reply_text("🖼️ No photos found.")
        return
    for f in files:
        await update.message.reply_photo(f)

async def send_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = get_files(update.message.from_user.id, "video")
    if not files:
        await update.message.reply_text("🎥 No videos found.")
        return
    for f in files:
        await update.message.reply_video(f)

# ------------------ MENU HANDLER ------------------
async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📄 My Documents":
        await send_documents(update, context)
    elif text == "🖼️ My Photos":
        await send_photos(update, context)
    elif text == "🎥 My Videos":
        await send_videos(update, context)
    elif text == "ℹ️ Help":
        await help_cmd(update, context)
    else:
        await update.message.reply_text("❓ Use the menu below.", reply_markup=main_menu())

# ------------------ APP ------------------
def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, handle_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_click))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
