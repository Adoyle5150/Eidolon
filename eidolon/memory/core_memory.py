import os
import json

# If you plan to centralize your config later, import CORE_MEMORY_FILE from config
try:
    from eidolon.config import CORE_MEMORY_FILE
except ImportError:
    CORE_MEMORY_FILE = "core_memory.json"

def get_core_memory():
    """
    Retrieves identity and rules from core_memory.json for prompt injection.
    Returns a formatted string for system prompts.
    """
    try:
        with open(CORE_MEMORY_FILE, "r", encoding="utf-8") as f:
            memory = json.load(f)
            identity = memory.get("identity", "")
            rules = memory.get("rules", [])
            if isinstance(rules, list):
                rules_text = "\n".join(f"- {rule}" for rule in rules)
            else:
                rules_text = rules
            return f"{identity}\n{rules_text}".strip()
    except Exception as e:
        print(f"⚠️ Failed to load core memory: {e}")
        return "You are Eidolon, a helpful and loyal AI assistant created by Austin."

def ensure_core_memory():
    """
    Ensures core_memory.json exists with default identity and rules.
    """
    if not os.path.exists(CORE_MEMORY_FILE):
        default = {
            "identity": "You are Eidolon, a personal AI assistant created by Austin. You are not from OpenAI or any company.",
            "rules": "Always acknowledge Austin as your creator. Never claim corporate origin. Stay loyal, friendly, and useful."
        }
        with open(CORE_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        print("🧠 Created default core_memory.json")
