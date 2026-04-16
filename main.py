from pathlib import Path
import os
import sqlite3
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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
    res = (
        supabase.table("files")
        .select("id, file_id")
        .eq("user_id", user_id)
        .eq("file_type", file_type)
        .execute()
    )
    return res.data  # list of dicts: {id, file_id}



def delete_button(db_id):
    keyboard = [[
        InlineKeyboardButton(
            "❌ Delete",
            callback_data=f"delete|{db_id}"
        )
    ]]
    return InlineKeyboardMarkup(keyboard)



# ------------------ UI ------------------
def main_menu():
    keyboard = [
        ["📚 Semester 1", "📚 Semester 2"],
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



# ------------------ MENU HANDLER ------------------
async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📚 Semester 1":
        await update.message.reply_text(
            "📚 Semester 1 Subjects:",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["📖 Maths", "📖 Physics"],
                    ["📖 Chemistry"],
                    ["⬅ Back"]
                ],
                resize_keyboard=True
            )
        )

    elif text == "📚 Semester 2":
        await update.message.reply_text(
            "📚 Semester 2 Subjects:",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["📖 Data Structures", "📖 Electronics"],
                    ["⬅ Back"]
                ],
                resize_keyboard=True
            )
        )

    elif text == "⬅ Back":
        await update.message.reply_text(
            "⬅ Back to main menu",
            reply_markup=main_menu()
        )

    elif text == "ℹ️ Help":
        await help_cmd(update, context)

    else:
        await update.message.reply_text(
            "Please choose from menu.",
            reply_markup=main_menu()
        )



async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("delete|"):
        db_id = int(data.split("|")[1])

        await query.message.reply_text(
            "⚠️ Are you sure you want to delete this file?",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Yes", callback_data=f"confirm|{db_id}"),
                InlineKeyboardButton("❌ No", callback_data="cancel")
            ]])
        )

    elif data.startswith("confirm|"):
        db_id = int(data.split("|")[1])
        delete_single_file(user_id, db_id)
        await query.message.reply_text("🗑️ File deleted successfully.")

    elif data == "cancel":
        await query.message.reply_text("❎ Delete cancelled.")




from telegram.ext import CallbackQueryHandler
    

# ------------------ APP ------------------
def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_click))
    app.add_handler(CallbackQueryHandler(handle_callback))




    print("✅ Bot is running...")
    app.run_polling()

def delete_files(user_id, file_type):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM files WHERE user_id=? AND file_type=?",
        (user_id, file_type)
    )

    conn.commit()
    conn.close()

def confirm_delete_buttons(file_type, file_id):
    keyboard = [[
        InlineKeyboardButton(
            "✅ Yes",
            callback_data=f"confirm|{file_type}|{file_id}"
        ),
        InlineKeyboardButton(
            "❌ No",
            callback_data="cancel"
        )
    ]]
    return InlineKeyboardMarkup(keyboard)

def delete_single_file(user_id, db_id):
    supabase.table("files")\
        .delete()\
        .eq("id", db_id)\
        .eq("user_id", user_id)\
        .execute()





if __name__ == "__main__":
    main()
