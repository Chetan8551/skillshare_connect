import requests
import json
from typing import Optional

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "llama3.2:1b"

def call_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 400,
    timeout: int = 120
) -> Optional[str]:
    """Call Ollama API and return response text."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "options": {"num_predict": max_tokens},
                "stream": True
            },
            timeout=timeout,
            stream=True
        )
        response.raise_for_status()

        full_text = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_obj = json.loads(line.decode("utf-8"))
                    if "response" in json_obj:
                        full_text += json_obj["response"]
                except:
                    continue
        return full_text.strip()
    except Exception as e:
        print(f"Ollama API call failed: {e}")
        return None
