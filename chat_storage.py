# chat_storage.py
import os, json
from datetime import datetime

def save_current_chat(chat_name, chat_history):
    os.makedirs("chats", exist_ok=True)
    safe_name = chat_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    chat_file = f"chats/{safe_name}.json"

    try:
        if not chat_history:
            print(f"⚠️ Skipping save for empty chat: {chat_name}")
            return

        # ✅ Save the raw message list — this is what your app expects
        with open(chat_file, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved chat: {chat_name} | File: {chat_file} | Messages saved: {len(chat_history)}")

    except Exception as e:
        print(f"❌ Failed to save chat '{chat_name}': {e}")
