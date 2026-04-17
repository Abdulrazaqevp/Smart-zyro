from pathlib import Path
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

ADMIN_ID = 5293211699  # 👈 your Telegram user 
upload_state = {}
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
BOT_TOKEN = os.getenv("BOT_TOKEN")

MENU_SEMESTER_1 = "📚 Semester 1"
MENU_SEMESTER_2 = "📚 Semester 2"
MENU_HELP = "ℹ️ Help"
MENU_BACK = "⬅ Back"


def main_menu():
    keyboard = [
        [MENU_SEMESTER_1, MENU_SEMESTER_2],
        [MENU_HELP],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def semester_1_menu():
    keyboard = [
        ["📖 Maths", "📖 Physics"],
        ["📖 MDF"],
        [MENU_BACK],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def semester_2_menu():
    keyboard = [
        ["📖 Data Structures", "📖 Electronics"],
        [MENU_BACK],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome!\n\nSelect semester to get lecture notes.",
        reply_markup=main_menu(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Choose a semester, then choose a subject to get its notes.\n\n"
        "If a subject says notes are not uploaded yet, add a real Telegram file_id for it in NOTES.",
        reply_markup=main_menu(),
    )


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("Send a document file to get its file ID.")
        return

    file_id = update.message.document.file_id
    await update.message.reply_text(f"FILE ID:\n{file_id}")

def save_note(subject, file_id):
    supabase.table("files").insert({
        "subject": subject,
        "file_id": file_id
    }).execute()


def get_notes(subject):
    res = supabase.table("files")\
        .select("file_id")\
        .eq("subject", subject)\
        .execute()

    return [row["file_id"] for row in res.data]

def delete_notes(subject):
    supabase.table("files")\
        .delete()\
        .eq("subject", subject)\
        .execute()

async def send_subject_notes(update, text):
    files = get_notes(text)

    if not files:
        await update.message.reply_text("📂 Notes not uploaded yet.")
        return

    await update.message.reply_text(f"📚 Sending notes for {text}...")

    for file_id in files:
        await update.message.reply_document(file_id)



async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == MENU_SEMESTER_1:
        await update.message.reply_text(
            "Semester 1 Subjects:",
            reply_markup=semester_1_menu(),
        )
        return

    if text == MENU_SEMESTER_2:
        await update.message.reply_text(
            "Semester 2 Subjects:",
            reply_markup=semester_2_menu(),
        )
        return

    if text == MENU_BACK:
        await update.message.reply_text(
            "Back to main menu.",
            reply_markup=main_menu(),
        )
        return

    if text == MENU_HELP:
        await help_cmd(update, context)
        return

    if text in NOTES:
        await send_subject_notes(update, text)
        return

    await update.message.reply_text(
        "Please choose from the menu.",
        reply_markup=main_menu(),
    )

#--------DELETE---------------

async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /delete Maths")
        return

    subject = f"📖 {' '.join(context.args)}"

    if subject not in NOTES:
        await update.message.reply_text("❌ Subject not found.")
        return

    delete_notes(subject)

    await update.message.reply_text(f"🗑️ All files deleted for {subject}")



#-------------Upload-----------

async def upload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /upload MDF")
        return

    subject = " ".join(context.args)
    upload_state[user_id] = subject

    await update.message.reply_text(f"📤 Send file for {subject}")


#----------ADMIN---------------
async def handle_admin_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in upload_state:
        return

    subject = f"📖 {upload_state[user_id]}"

    if update.message.document:
        file_id = update.message.document.file_id

        if subject not in NOTES:
            NOTES[subject] = []

        save_note(subject, file_id)

        await update.message.reply_text("✅ File added successfully!")

        del upload_state[user_id]

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing from the .env file.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("getid", get_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_click))
    app.add_handler(CommandHandler("upload", upload_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_admin_upload))
    app.add_handler(CommandHandler("delete", delete_cmd))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
