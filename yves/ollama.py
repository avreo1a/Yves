import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


def ollama_request(model, messages):
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False
        }
    )
    return response.json()["message"]["content"]