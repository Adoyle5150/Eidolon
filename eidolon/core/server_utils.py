import os
import subprocess
import requests
import time

# If you centralize config, import these from there
try:
    from eidolon.config import LLAMA_SERVER, MODEL_PATH, SERVER_URL
except ImportError:
    LLAMA_SERVER = "E:/Eidolon/llama.cpp/build/bin/llama-server.exe"
    MODEL_PATH = "E:/Eidolon/models/DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf"
    SERVER_URL = "http://localhost:11434"

def start_llama_web_server():
    """
    Starts the llama-server executable and waits until it is ready.
    """
    print("[EIDOLON] 🧠 Launching llama-server...")

    if not os.path.exists(LLAMA_SERVER):
        print(f"❌ llama-server not found: {LLAMA_SERVER}")
        exit()
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model file not found: {MODEL_PATH}")
        exit()

    subprocess.Popen([
        LLAMA_SERVER,
        "--model", MODEL_PATH,
        "--port", "11434",
        "--threads", "12",
        "--n-gpu-layers", "80",
        "--ctx-size", "2048",
        "--n-predict", "2048"
    ])

    for _ in range(30):
        try:
            res = requests.get(f"{SERVER_URL}/api/tags")
            if res.status_code == 200:
                print("[EIDOLON] ✅ Web backend ready.")
                return
        except Exception:
            pass
        time.sleep(1)

    print("❌ Server didn't respond after 30 seconds.")
    exit()

def threaded_llama_start():
    """
    Launches the llama-server in a thread.
    """
    print("[EIDOLON] 🧠 Launching llama-server in thread...")
    start_llama_web_server()
