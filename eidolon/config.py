# eidolon/config.py

# Model and server paths
MODEL_TAG = "DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf"
MODEL_PATH = f"E:/Eidolon/models/{MODEL_TAG}"
LLAMA_SERVER = "E:/Eidolon/llama.cpp/build/bin/llama-server.exe"
SERVER_URL = "http://localhost:11434"

# Memory file
CORE_MEMORY_FILE = "core_memory.json"

# Web search system prompt
WEB_SEARCH_SYSTEM_PROMPT = (
    "You are a helpful assistant. Rephrase the user's request into a clear, concise web search query "
    "that can be used to find real-time information on the web."
)

# Animation settings (adjust if you want to control globally)
ANIMATED_TYPING_ENABLED = True

# Any additional future settings:
VISION_CAPTURE_INTERVAL = 10  # seconds
