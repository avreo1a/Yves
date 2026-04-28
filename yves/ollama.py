import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
_MODEL_TRACKER = os.path.join(os.path.dirname(__file__), ".current_model")


def sync_model(model: str):
    """Delete the previously used model if it differs from the current one."""
    if not os.path.exists(_MODEL_TRACKER):
        _write_model(model)
        return

    with open(_MODEL_TRACKER) as f:
        previous = f.read().strip()

    if previous and previous != model:
        try:
            requests.delete(f"{OLLAMA_URL}/api/delete", json={"name": previous})
            print(f"Deleted old model: {previous}")
        except Exception as e:
            print(f"Could not delete old model '{previous}': {e}")

    _write_model(model)


def _write_model(model: str):
    with open(_MODEL_TRACKER, "w") as f:
        f.write(model)


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