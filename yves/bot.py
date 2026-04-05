import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from db import init_db, register_user, get_history, save_message
from ollama import ollama_request

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MODEL = "qwen2.5:14b"

with open("systemPrompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    register_user(chat_id)
    await update.message.reply_text("Hey! Kumusta? 👋")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_msg = update.message.text

    register_user(chat_id)  # safe — INSERT OR IGNORE

    history = get_history(chat_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_msg}
    ]

    save_message(chat_id, "user", user_msg)
    reply = ollama_request(MODEL, messages)
    save_message(chat_id, "assistant", reply)

    await update.message.reply_text(reply)

if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
