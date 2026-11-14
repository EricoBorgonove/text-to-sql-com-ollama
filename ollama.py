"""Cliente Ollama: nenhum serviço externo necessario."""
import os
import requests


def conversar(mensagens, formato=None):
    payload = {
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        "messages": mensagens,
        "stream": False,
        "options": {"temperature": 0, "num_ctx": 4096},
        "keep_alive": "2m",
    }
    if formato:
        payload["format"] = formato
    r = requests.post(
        os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat"),
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()
