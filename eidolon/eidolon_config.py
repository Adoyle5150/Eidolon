# eidolon_config.py

"""
Eidolon - Configuration Management Module

Central location for paths, model settings, and runtime flags.
Allows future loading from config.json or GUI-based settings editor.
"""

import os

class EidolonConfig:
    def __init__(self):
        # === Paths ===
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_tag = "DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf"
        self.models_dir = os.path.join(self.project_root, "models")
        self.model_path = os.path.join(self.models_dir, self.model_tag)
        self.llama_server_exe = os.path.join(self.project_root, "llama.cpp", "build", "bin", "llama-server.exe")
        self.core_memory_file = os.path.join(self.project_root, "core_memory.json")
        self.chat_history_file = os.path.join(self.project_root, "chat_history.json")
        self.chats_folder = os.path.join(self.project_root, "chats")

        # === Server ===
        self.server_url = "http://localhost:11434"
        self.server_port = 11434
        self.server_threads = 12
        self.server_gpu_layers = 80
        self.server_ctx_size = 2048
        self.server_n_predict = 2048

        # === LLM Parameters ===
        self.temperature = 0.7
        self.top_p = 0.95

        # === Flags ===
        self.web_search_enabled = True
        self.vision_enabled = True
        self.animated_typing_enabled = True

        # === System Prompts ===
        self.web_search_system_prompt = (
            "You are a helpful assistant. Rephrase the user's request into a clear, concise web search query "
            "that can be used to find real-time information on the web."
        )

    def print_summary(self):
        print("[EIDOLON_CONFIG] Configuration Summary:")
        print(f"  Model Path: {self.model_path}")
        print(f"  LLaMA Server: {self.llama_server_exe}")
        print(f"  Server URL: {self.server_url}")
        print(f"  Temperature: {self.temperature}")
        print(f"  Web Search Enabled: {self.web_search_enabled}")
        print(f"  Vision Enabled: {self.vision_enabled}")
        print(f"  Animated Typing: {self.animated_typing_enabled}")

# Singleton instance for convenience
config = EidolonConfig()
