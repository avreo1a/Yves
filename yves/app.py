import requests
from flask import Flask, request, jsonify
from db import init_db, get_history, save_message

app = Flask(__name__)

with open("systemPrompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

def ask_ollama(chat_id, user_msg):
    history = get_history(chat_id)
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "qwen2.5:3b",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                *history,
                {"role": "user", "content": user_msg}
            ],
            "stream": False
        }
    )
    return response.json()["message"]["content"]

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    chat_id = data.get("chat_id")
    user_msg = data.get("message")

    save_message(chat_id, "user", user_msg)
    reply = ask_ollama(chat_id, user_msg)
    save_message(chat_id, "assistant", reply)

    return jsonify({"reply": reply})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)