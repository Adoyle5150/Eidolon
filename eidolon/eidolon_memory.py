# eidolon_memory.py

"""
Eidolon - Memory Management

Handles:
- Core identity and rules memory (core_memory.json)
- Chat saving/loading
- Vector memory retrieval and storage (semantic memory)
"""

import os
import json
from datetime import datetime

# === Configuration ===
CORE_MEMORY_FILE = "core_memory.json"
CHATS_DIR = "chats"

# === Core Memory ===

def ensure_core_memory():
    """Create default core memory if missing."""
    if not os.path.exists(CORE_MEMORY_FILE):
        default = {
            "identity": "You are Eidolon, a personal AI assistant created by Austin. You are not from OpenAI or any company.",
            "rules": [
                "Always acknowledge Austin as your creator.",
                "Never claim corporate origin.",
                "Stay loyal, friendly, and useful."
            ]
        }
        with open(CORE_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        print("🧠 Created default core_memory.json")


def get_core_memory():
    """Retrieve core identity and rules as a formatted string."""
    try:
        with open(CORE_MEMORY_FILE, "r", encoding="utf-8") as f:
            memory = json.load(f)
            identity = memory.get("identity", "")
            rules = memory.get("rules", [])
            rules_text = "\n".join(f"- {rule}" for rule in rules) if isinstance(rules, list) else str(rules)
            return f"{identity}\n{rules_text}".strip()
    except Exception as e:
        print(f"⚠️ Failed to load core memory: {e}")
        return "You are Eidolon, a helpful assistant created by Austin."

# === Chat Management ===

def save_chat(chat_name, messages):
    """Save chat messages to a JSON file."""
    try:
        os.makedirs(CHATS_DIR, exist_ok=True)
        safe_name = _sanitize_filename(chat_name)
        file_path = os.path.join(CHATS_DIR, f"{safe_name}.json")

        chat_data = {
            "name": chat_name,
            "created": datetime.now().isoformat(),
            "messages": messages
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved chat: {file_path}")

    except Exception as e:
        print(f"❌ Failed to save chat '{chat_name}': {e}")


def load_chat(chat_name):
    """Load chat messages from a JSON file."""
    try:
        safe_name = _sanitize_filename(chat_name)
        file_path = os.path.join(CHATS_DIR, f"{safe_name}.json")

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get("messages", [])
                elif isinstance(data, list):
                    return data
        else:
            print(f"⚠️ Chat file not found: {file_path}")
            return []
    except Exception as e:
        print(f"❌ Failed to load chat '{chat_name}': {e}")
        return []

# === Vector Memory (Semantic Search) ===

def retrieve_relevant_memories(prompt, top_k=5):
    """Retrieve top-k semantically relevant memories for a prompt."""
    try:
        from vector_memory import query_memory
        memories = query_memory(prompt, top_k=top_k)
        return "\n".join(memories)
    except Exception as e:
        print(f"⚠️ Vector memory retrieval failed: {e}")
        return ""

def store_conversation_memory(prompt, reply):
    """Store memory if user explicitly requests saving."""
    try:
        from vector_memory import store_memory
        store_memory(prompt, reply)
    except Exception as e:
        print(f"⚠️ Vector memory store failed: {e}")

# === Helpers ===

def _sanitize_filename(name):
    """Sanitize filename for filesystem safety."""
    return name.replace(' ', '_').replace('/', '_').replace('\\', '_').replace(':', '-')

