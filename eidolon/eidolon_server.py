"""
Eidolon Server Utilities
Handles starting and managing the LLaMA server process cleanly.
"""

import os
import subprocess
import time
import requests

# Configuration constants (adjust as needed)
MODEL_TAG = "DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf"
MODEL_PATH = f"E:/Eidolon/models/{MODEL_TAG}"
LLAMA_SERVER_PATH = "E:/Eidolon/llama.cpp/build/bin/llama-server.exe"
SERVER_URL = "http://localhost:11434"


def start_llama_server():
    """Start the LLaMA server process and wait for readiness."""
    print("[EIDOLON] 🧠 Launching LLaMA server...")

    if not os.path.exists(LLAMA_SERVER_PATH):
        print(f"❌ LLaMA server binary not found at: {LLAMA_SERVER_PATH}")
        return False

    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model file not found at: {MODEL_PATH}")
        return False

    # Launch the server as a subprocess
    subprocess.Popen([
        LLAMA_SERVER_PATH,
        "--model", MODEL_PATH,
        "--port", "11434",
        "--threads", "12",
        "--n-gpu-layers", "80",
        "--ctx-size", "2048",
        "--n-predict", "2048"
    ])

    # Wait for the server to become ready
    for i in range(30):
        try:
            response = requests.get(f"{SERVER_URL}/api/tags")
            if response.status_code == 200:
                print("[EIDOLON] ✅ LLaMA server is ready.")
                return True
        except requests.RequestException:
            pass
        time.sleep(1)

    print("❌ LLaMA server did not respond within 30 seconds.")
    return False


def threaded_llama_start():
    """Launch the LLaMA server in a daemon thread."""
    import threading
    thread = threading.Thread(target=start_llama_server, daemon=True)
    thread.start()
