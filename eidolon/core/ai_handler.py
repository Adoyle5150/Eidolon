# eidolon/core/ai_handler.py

import requests
import re
import threading
import json

from eidolon.memory.core_memory import get_core_memory
from eidolon.utils.helpers import is_valid_python, is_valid_message
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
    
    Note: This function now expects a limited message history (typically last 8 messages)
    to prevent token overload. The calling code should use _get_limited_history() 
    to prepare the messages parameter.
    """
    try:
        identity = get_core_memory()

        # --- WEB SEARCH SYSTEM PROMPT DEDUPLICATION ---
        if use_web_search and WEB_SEARCH_AVAILABLE:
            search_instruction_added = False
            for msg in messages:
                if msg.get("role") == "system":
                    if WEB_SEARCH_SYSTEM_PROMPT not in msg["content"]:
                        msg["content"] += "\n\n" + WEB_SEARCH_SYSTEM_PROMPT
                    search_instruction_added = True
                    break
            if not search_instruction_added:
                messages.insert(0, {"role": "system", "content": WEB_SEARCH_SYSTEM_PROMPT})

        valid_messages = [m for m in messages if is_valid_message(m)]
        if not valid_messages:
            raise ValueError("No valid messages to send to server.")

        modified = valid_messages[:-1]
        latest = valid_messages[-1]

        if not isinstance(latest["content"], str):
            latest["content"] = str(latest["content"])

        if latest["content"].lower().startswith("remember"):
            threading.Thread(
                target=vector_memory.store_memory,
                args=(latest["content"],),
                daemon=True
            ).start()

        if latest["content"].lower().startswith(("recall", "what do you remember")):
            memory_block = vector_memory.retrieve_relevant_memories(
                latest["content"],
                top_k=8,
                similarity_threshold=0.7,
                max_results=3
            )
            if memory_block and isinstance(memory_block, str) and memory_block.strip():
                formatted_memory = f"=== RELEVANT MEMORIES ===\n{memory_block}\n=== END MEMORIES ===\n\n"
                latest["content"] = f"{formatted_memory}{latest['content']}".strip()
                print("\u2705 Injected deduplicated FAISS vector memories into prompt.")
            else:
                print("\u2139\ufe0f No relevant memories retrieved or injection skipped.")

        memory_block = None
        if not use_web_search:
            if len(latest["content"].split()) <= 3:
                print("\u2139\ufe0f Skipping memory injection for short/trivial input.")
            else:
                memory_block = vector_memory.retrieve_relevant_memories(
                    latest["content"],
                    top_k=8,
                    similarity_threshold=0.7,
                    max_results=3
                )
        if memory_block and isinstance(memory_block, str) and memory_block.strip():
            formatted_memory = f"=== RELEVANT MEMORIES ===\n{memory_block}\n=== END MEMORIES ===\n\n"
            latest["content"] = f"{formatted_memory}{latest['content']}".strip()
            print("\u2705 Injected deduplicated FAISS vector memories into prompt.")
        else:
            if not use_web_search:
                print("\u2139\ufe0f No relevant memories retrieved or injection skipped.")

        full_messages = [{"role": "system", "content": identity}] + modified + [latest]

        payload = {
            "messages": full_messages,
            "stream": False,
            "n_predict": 2048,
            "temperature": 0.7
        }

        print(f"\U0001F4AC Sending payload to server: {json.dumps(payload, indent=2)}")

        try:
            res = requests.post(f"{SERVER_URL}/api/chat", json=payload)
            res.raise_for_status()
        except Exception as e:
            print(f"❌ Request failed: {e}")
            print(f"Response content: {res.text}")
            return f"❌ API error: {res.text}"

        data = res.json()
        content = data.get("message", {}).get("content") or \
                  data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if "</think>" in content:
            content = re.sub(r"^[\s\S]*?</think>(?![\s\S]*?</think>)", "", content, flags=re.DOTALL)

        content = "\n".join([
            line for line in content.splitlines()
            if not any(t in line for t in ("<|im_", "<jupyter_", "<|start|>", "<|end|>"))
        ])

        if "```python" in content:
            code_block = re.findall(r"```python(.*?)```", content, re.DOTALL)
            if code_block:
                code = code_block[0].strip()
                if not is_valid_python(code):
                    content += "\n\n# ⚠️ Warning: This code has syntax issues."

        content = content.replace("window.blit((...", "# ❌ Invalid blit call — use draw.rect or draw.circle")
        return content.strip()

    except Exception as e:
        print(f"❌ Server Error: {e}")
        return f"❌ Server Error: {e}"

def _get_limited_history(all_messages, max_messages=5):
    """
    Returns the last `max_messages` valid messages from the conversation history,
    excluding system identity injection to avoid token bloat.
    """
    valid = [m for m in all_messages if is_valid_message(m)]
    return valid[-max_messages:] if len(valid) > max_messages else valid