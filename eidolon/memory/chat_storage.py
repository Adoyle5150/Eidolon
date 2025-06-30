import os
import json
from datetime import datetime

def _safe_filename(chat_name):
    """
    Sanitize chat_name for filesystem-safe filenames.
    """
    return chat_name.strip().replace(' ', '_').replace('/', '_').replace('\\', '_')

def _generate_chat_name(messages):
    """
    Generate a meaningful chat name from the first user message or timestamp.
    """
    if not messages:
        return f"Chat {datetime.now().strftime('%m/%d %H:%M')}"
    
    # Find first user message
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "").strip()
            if content:
                # Take first 30 chars, clean up
                name = content[:30].replace('\n', ' ').replace('\r', ' ')
                # Remove extra spaces
                name = ' '.join(name.split())
                if name:
                    return name
    
    # Fallback to timestamp
    return f"Chat {datetime.now().strftime('%m/%d %H:%M')}"

def _save_chat(chat_name, messages, folder, limit, label):
    """
    Core function to save chat data with controlled message limit and consistent structure.
    """
    try:
        os.makedirs(folder, exist_ok=True)
        
        # Generate meaningful name if chat_name is generic
        if chat_name in ["Untitled", "Untitled Chat"] or not chat_name.strip():
            chat_name = _generate_chat_name(messages)
        
        safe_name = _safe_filename(chat_name)
        file_path = os.path.join(folder, f"{safe_name}.json")
        
        # Check if file exists and get creation time
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    created_time = existing_data.get("created", datetime.now().isoformat())
            except:
                created_time = datetime.now().isoformat()
        else:
            created_time = datetime.now().isoformat()

        chat_data = {
            "name": chat_name,
            "created": created_time,
            "modified": datetime.now().isoformat(),
            "messages": messages[-limit:] if messages else []
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)

        print(f"[chat_storage] 💾 {label} chat '{chat_name}' saved with {len(chat_data['messages'])} messages.")
        return chat_name  # Return the actual name used

    except Exception as e:
        print(f"[chat_storage] ❌ Error saving {label.lower()} chat '{chat_name}': {e}")
        return chat_name

def save_current_chat(chat_name, messages, folder="chats"):
    """
    Save the current chat with the last 50 messages for main autosave and exit saving.
    Returns the actual chat name used (may be different if auto-generated).
    """
    return _save_chat(chat_name, messages, folder, limit=50, label="Full")

def save_individual_chat(chat_name, messages, folder="chats"):
    """
    Save the current chat with the last 20 messages for sidebar incremental updates.
    Returns the actual chat name used (may be different if auto-generated).
    """
    return _save_chat(chat_name, messages, folder, limit=20, label="Incremental")

def load_chat(chat_name, folder="chats"):
    """
    Load chat data from disk, returning the messages list.
    Returns [] if file does not exist or fails.
    """
    try:
        safe_name = _safe_filename(chat_name)
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