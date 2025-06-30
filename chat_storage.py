import os
import json
from datetime import datetime

def save_current_chat(chat_name, messages, folder="chats"):
    """
    Save the current chat to a JSON file inside the specified folder.
    Keeps the last 50 messages for lightweight storage.
    """
    try:
        os.makedirs(folder, exist_ok=True)
        safe_name = chat_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        file_path = os.path.join(folder, f"{safe_name}.json")

        chat_data = {
            "name": chat_name,
            "created": datetime.now().isoformat(),
            "messages": messages[-50:]  # Keep last 50 messages for context
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)

        print(f"[chat_storage] 💾 Chat '{chat_name}' saved successfully with {len(messages[-50:])} messages.")

    except Exception as e:
        print(f"[chat_storage] ❌ Error saving chat '{chat_name}': {e}")


def load_chat(chat_name, folder="chats"):
    """
    Load a chat by name from the specified folder, returning its message list.
    """
    try:
        safe_name = chat_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        file_path = os.path.join(folder, f"{safe_name}.json")

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                messages = data.get("messages", [])
                print(f"[chat_storage] ✅ Chat '{chat_name}' loaded with {len(messages)} messages.")
                return messages

        else:
            print(f"[chat_storage] ⚠️ Chat file not found: {file_path}")
            return []

    except Exception as e:
        print(f"[chat_storage] ❌ Error loading chat '{chat_name}': {e}")
        return []
