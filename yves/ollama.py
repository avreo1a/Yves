import requests

def ollama_request(model, prompt):
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "qwen2.5:3b",
            "messages": messages, #messages is just a placeholder rn for the actual sent messahe
            "stream": False #streaming is just for live text updates from the model
        }
        
    )
    return response.json()["message"]["content"] 
