import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from db import (init_db, register_user, get_history, save_message,
                get_message_count, get_oldest_messages, delete_messages_by_ids,
                get_summary, save_summary)
from ollama import ollama_request, sync_model

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MODEL = "aisingapore/Llama-SEA-LION-v3.5-8B-R"

# Summarization settings
MAX_MESSAGES_BEFORE_SUMMARY = 30  # Trigger summarization when we hit this count
MESSAGES_TO_SUMMARIZE = 20        # How many old messages to summarize at once
RECENT_MESSAGES_TO_KEEP = 10      # Keep this many recent messages verbatim

# Load system prompt once at startup; restart required to pick up changes
with open("systemPrompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — register the user and send a greeting."""
    chat_id = str(update.effective_chat.id)
    register_user(chat_id)
    await update.message.reply_text("Kumusta")


async def summarize_messages(chat_id: str):
    """
    Summarize older messages to save context window space.
    Takes both user and assistant messages into account.
    """
    message_count = get_message_count(chat_id)

    if message_count < MAX_MESSAGES_BEFORE_SUMMARY:
        return  # Not enough messages to summarize yet

    # Get oldest messages to summarize
    oldest_messages = get_oldest_messages(chat_id, MESSAGES_TO_SUMMARIZE)
    if not oldest_messages:
        return

    # Format conversation for summarization
    conversation_text = []
    message_ids = []
    for msg_id, role, content in oldest_messages:
        message_ids.append(msg_id)
        speaker = "User" if role == "user" else "Yves"
        conversation_text.append(f"{speaker}: {content}")

    conversation_str = "\n".join(conversation_text)

    # Get existing summary to build upon
    existing_summary = get_summary(chat_id)

    # Create summarization prompt
    if existing_summary:
        summary_prompt = f"""You are summarizing a Tagalog learning conversation between a user and their Filipino friend Yves.

Previous summary of older conversation:
{existing_summary}

New messages to incorporate into the summary:
{conversation_str}

Create an updated summary that captures:
1. The user's current Tagalog skill level based on their responses
2. Key topics they've discussed
3. Words/phrases the user has learned or struggled with
4. Any personal details shared (to maintain natural friendship)
5. The overall progress and tone of the conversation

Keep the summary concise but informative. Write in plain text, not as a list."""
    else:
        summary_prompt = f"""You are summarizing a Tagalog learning conversation between a user and their Filipino friend Yves.

Conversation to summarize:
{conversation_str}

Create a summary that captures:
1. The user's current Tagalog skill level based on their responses
2. Key topics they've discussed
3. Words/phrases the user has learned or struggled with
4. Any personal details shared (to maintain natural friendship)
5. The overall progress and tone of the conversation

Keep the summary concise but informative. Write in plain text, not as a list."""

    # Request summary from Ollama
    summary_messages = [
        {"role": "system", "content": "You are a helpful assistant that summarizes conversations accurately and concisely."},
        {"role": "user", "content": summary_prompt}
    ]

    new_summary = ollama_request(MODEL, summary_messages)

    # Save the new summary
    current_count = get_message_count(chat_id) - len(message_ids)
    save_summary(chat_id, new_summary, current_count)

    # Delete the summarized messages
    delete_messages_by_ids(chat_id, message_ids)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages: build context, query Ollama, save and reply."""
    chat_id = str(update.effective_chat.id)
    user_msg = update.message.text

    # If user didn't do /start make sure we still create an id for them
    register_user(chat_id)

    # Build context: system prompt + summary (if exists) + recent history
    summary = get_summary(chat_id)
    history = get_history(chat_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add summary as context if we have one
    if summary:
        messages.append({
            "role": "system",
            "content": f"[Previous conversation summary: {summary}]"
        })

    # Add recent message history
    messages.extend(history)

    # Add current user message
    messages.append({"role": "user", "content": user_msg})

    # Persist user message before calling the model
    save_message(chat_id, "user", user_msg)
    reply = ollama_request(MODEL, messages)
    save_message(chat_id, "assistant", reply)

    await update.message.reply_text(reply)

    # Check if we need to summarize old messages (runs in background after reply)
    await summarize_messages(chat_id)

if __name__ == "__main__":
    init_db()
    sync_model(MODEL)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
