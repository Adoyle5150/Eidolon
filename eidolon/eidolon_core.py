import os
import json
import time
import re
import ast
import threading
import subprocess
import requests
from datetime import datetime
from eidolon_server import threaded_llama_start, ask_server
from eidolon_utils import ensure_core_memory, save_individual_chat



# ==========================
# ✅ AssistantCore Class
# ==========================
import threading

class AssistantCore:
    def __init__(self, push_message_func=None):
        """
        Initialize the AssistantCore with optional push_message callback.
        Sets up chat state and ensures core memory is available.
        """
        self.push_message = push_message_func
        self.chat_history = []
        self.current_chat_name = ""
        self.animated_typing_enabled = True  # Default, can load from config
        ensure_core_memory()
        print("[AssistantCore] ✅ Initialized.")

    def start_services(self):
        """
        Starts necessary background services such as the LLaMA server.
        """
        threading.Thread(target=threaded_llama_start, daemon=True).start()
        print("[AssistantCore] 🧠 Background services started.")

    def handle_user_message(self, text):
        """
        Handles a user message:
        - Adds it to the chat history.
        - Pushes to UI if callback is present.
        - Calls LLM to generate a reply and sends it to UI.
        """
        def process():
            # Add user message
            self.chat_history.append({"role": "user", "content": text})
            if self.push_message:
                self.push_message("user", text)

            # Optionally signal typing animation
            if self.push_message and self.animated_typing_enabled:
                self.push_message("status", "typing")

            # Get assistant reply
            try:
                reply = ask_server(self.chat_history)
            except Exception as e:
                reply = f"❌ Error: {e}"

            # Add assistant message
            self.chat_history.append({"role": "assistant", "content": reply})
            if self.push_message:
                self.push_message("assistant", reply)

            # Signal ready state after typing
            if self.push_message:
                self.push_message("status", "ready")

        threading.Thread(target=process, daemon=True).start()

    def shutdown(self):
        """
        Shutdown handler for cleaning up resources.
        """
        print("[AssistantCore] 🛑 Shutting down background services (placeholder).")
        # Optionally implement vector DB shutdown, websocket close, etc.

    def save_current_session(self):
        """
        Save the current chat session safely on exit or demand.
        """
        try:
            save_individual_chat(self.current_chat_name or "Untitled", self.chat_history)
            print(f"[AssistantCore] 💾 Session saved for '{self.current_chat_name or 'Untitled'}'.")
        except Exception as e:
            print(f"[AssistantCore] ⚠️ Failed to save session: {e}")

    def set_global_chat_state(self, name, history):
        """
        Update the current chat name and history globally.
        """
        self.current_chat_name = name
        self.chat_history = history
        print(f"[AssistantCore] ✅ State updated: chat_name='{name}', messages={len(history)}")

    def get_current_chat_name(self):
        """
        Retrieve the current active chat name.
        """
        return self.current_chat_name

    def get_chat_history(self):
        """
        Retrieve the current chat history.
        """
        return self.chat_history

    def set_push_message_callback(self, callback):
        """
        Dynamically set the push message callback (for GUI).
        """
        self.push_message = callback
        print("[AssistantCore] ✅ Push message callback set.")

    def load_config(self, config_path="config.json"):
        """
        Load configuration settings, e.g., for animated_typing_enabled.
        """
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.animated_typing_enabled = config.get("animated_typing_enabled", True)
                print(f"[AssistantCore] ✅ Config loaded: animated_typing_enabled={self.animated_typing_enabled}")
            except Exception as e:
                print(f"[AssistantCore] ⚠️ Failed to load config: {e}")
        else:
            print("[AssistantCore] ℹ️ Config file not found, using defaults.")

    def reset_chat(self):
        """
        Reset the chat history while retaining the current chat name.
        """
        self.chat_history = []
        print(f"[AssistantCore] 🔄 Chat '{self.current_chat_name}' reset.")

    def inject_system_message(self, message):
        """
        Programmatically inject a system message into the chat.
        """
        self.chat_history.append({"role": "system", "content": message})
        print(f"[AssistantCore] 🪐 Injected system message: {message[:50]}")