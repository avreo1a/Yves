from flask import Flask, request, jsonify
from db import init_db, get_history, save_message
from ollama import ollama_request

app = Flask(__name__)

MODEL = "qwen2.5:3b"

with open("systemPrompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

def ask_ollama(chat_id, user_msg):
    history = get_history(chat_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_msg}
    ]
    return ollama_request(MODEL, messages)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    chat_id = data.get("chat_id")
    user_msg = data.get("message")

    reply = ask_ollama(chat_id, user_msg)
    save_message(chat_id, "user", user_msg)
    save_message(chat_id, "assistant", reply)

    return jsonify({"reply": reply})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", debug=True)