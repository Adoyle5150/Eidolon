# eidolon_llm.py

import requests

# Adjust if your llama-server is on a different port
LLAMA_SERVER_URL = "http://127.0.0.1:11434/completion"

def ask_server(prompt: str, system_prompt: str = "") -> str:
    """
    Sends a prompt to your local llama-server and returns the generated text.
    Compatible with DeepSeek / llama.cpp server endpoints.
    """

    payload = {
        "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
        "max_tokens": 1024,
        "temperature": 0.7,
        "stop": ["<|endoftext|>", "###", "```"]
    }

    try:
        response = requests.post(LLAMA_SERVER_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        # Depending on your server, you might need to adjust:
        # If using llama-server:
        return data["content"]

        # If using llama.cpp server directly:
        # return data["choices"][0]["text"]

    except Exception as e:
        print(f"❌ ask_server error: {e}")
        return ""
