# eidolon/core/ai_handler.py

import requests
import re
import threading

from eidolon.memory.core_memory import get_core_memory
from eidolon.utils.helpers import is_valid_python
from eidolon.memory import vector_memory_faiss as vector_memory

# Local constants used only by ask_server
SERVER_URL = "http://localhost:11434"

WEB_SEARCH_SYSTEM_PROMPT = (
    "You are a helpful assistant. Rephrase the user's request into a clear, concise web search query "
    "that can be used to find real-time information on the web."
)

WEB_SEARCH_AVAILABLE = True  # Set False if you don't want web search attempts

def ask_server(messages, use_web_search=True):
    """
    Send messages to the local LLM server and return the cleaned response.
    Optionally injects system identity, web search prompt, and relevant memories.
    """
    try:
        identity = get_core_memory()

        if use_web_search and WEB_SEARCH_AVAILABLE:
            search_instruction_added = False
            for msg in messages:
                if msg.get("role") == "system":
                    if "web search" not in msg["content"].lower():
                        msg["content"] += "\n\n" + WEB_SEARCH_SYSTEM_PROMPT
                    search_instruction_added = True
                    break
            if not search_instruction_added:
                messages.insert(0, {"role": "system", "content": WEB_SEARCH_SYSTEM_PROMPT})

        modified = messages[:-1]
        latest = messages[-1]

        # Store "remember" statements in FAISS without blocking
        if latest["content"].lower().startswith("remember"):
            threading.Thread(
                target=vector_memory.store_memory,
                args=(latest["content"],),
                daemon=True
            ).start()

        # Retrieve relevant memories and prepend to prompt
        memory_block = vector_memory.retrieve_relevant_memories(latest["content"], top_k=5)
        if memory_block:
            latest["content"] = f"{memory_block}\n{latest['content']}".strip()
            print("✅ Injected FAISS vector memories into prompt.")
        else:
            print("ℹ️ No relevant memories retrieved.")

        full_messages = [{"role": "system", "content": identity}] + modified + [latest]

        res = requests.post(f"{SERVER_URL}/api/chat", json={
            "messages": full_messages,
            "stream": False,
            "n_predict": 2048,
            "temperature": 0.7
        })

        data = res.json()
        content = data.get("message", {}).get("content") or \
                 data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Clean unwanted tokens
        if "</think>" in content:
            content = re.sub(r"^[\s\S]*?</think>(?![\s\S]*?</think>)", "", content, flags=re.DOTALL)

        content = "\n".join([
            line for line in content.splitlines()
            if not any(t in line for t in ("<|im_", "<jupyter_", "<|start|>", "<|end|>"))
        ])

        # Check for Python code validity
        if "```python" in content:
            code_block = re.findall(r"```python(.*?)```", content, re.DOTALL)
            if code_block:
                code = code_block[0].strip()
                if not is_valid_python(code):
                    content += "\n\n# ⚠️ Warning: This code has syntax issues."

        content = content.replace("window.blit((...", "# ❌ Invalid blit call — use draw.rect or draw.circle")
        return content.strip()

    except Exception as e:
        return f"❌ Server Error: {e}"