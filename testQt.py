import sys
sys.path.append("E:/Eidolon")
import os
import json
import time
import re
import ast
import threading
import subprocess
import requests
from datetime import datetime

# ✅ Force Fusion style to allow QML background/contentItem customization
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"

# ✅ Add Vision folder to sys.path so eidolon_vision is found
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Vision"))

from eidolon_vision import EidolonVision
from vector_memory import store_conversation_memory


# Fix for Pylance import errors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Qt Imports
from PyQt6.QtGui import QGuiApplication, QSurfaceFormat
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QUrl, QObject, QMetaObject, 
    Q_ARG, QVariant, pyqtProperty, pyqtSlot
)
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType

# Project Imports
from chat_storage import save_current_chat
from eidolon_qml_gui import EidolonQMLBridge
from globals_state import animated_typing_enabled

# Web search import
try:
    from web.searcher import web_search, get_searcher
    WEB_SEARCH_AVAILABLE = True
    print("✅ Web search module loaded successfully from searcher.py")
except ImportError as e:
    WEB_SEARCH_AVAILABLE = False
    print(f"⚠️ Web search not available: {e}")

# Vision system imports
try:
    from startup import start_all_background_services
    vision_available = True
    print("✅ Eidolon Vision module loaded")
except Exception as e:
    vision_available = False
    print(f"⚠️ Eidolon Vision not available: {e}")

# Web search system prompt
WEB_SEARCH_SYSTEM_PROMPT = (
    "You are a helpful assistant. Rephrase the user's request into a clear, concise web search query "
    "that can be used to find real-time information on the web."
)

# Set OpenGL and translucency for frameless resizing
fmt = QSurfaceFormat()
fmt.setAlphaBufferSize(8)
QSurfaceFormat.setDefaultFormat(fmt)

# Set DPI scaling policy
QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

# Global state
chat_history = []
current_chat_name = None
push_message_func = None
qml_bridge = None
gui = None
sidebar_backend = None
root = None

# Config
MODEL_TAG = "DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf"
MODEL_PATH = f"E:/Eidolon/models/{MODEL_TAG}"
LLAMA_SERVER = "E:/Eidolon/llama.cpp/build/bin/llama-server.exe"
SERVER_URL = "http://localhost:11434"
CORE_MEMORY_FILE = "core_memory.json"

# Sidebar Backend Class
class SidebarBackend(QObject):
    sidebarVisibilityChanged = pyqtSignal(bool)
    chatHistoryChanged = pyqtSignal()
    newChatRequested = pyqtSignal()
    currentChatChanged = pyqtSignal(str)
    chatLoadRequested = pyqtSignal(str)
    chatMessageAdded = pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self._sidebar_visible = True
        self._chat_history = []
        self._filtered_chat_history = []
        self._current_chat_name = ""
        self._search_filter = ""
        self.main_backend = None
        self.load_chat_history()

    @pyqtProperty(str)
    def currentChatName(self):
        return self._current_chat_name

    @pyqtProperty(bool, notify=sidebarVisibilityChanged)
    def sidebarVisible(self):
        return self._sidebar_visible

    @sidebarVisible.setter
    def sidebarVisible(self, value):
        if self._sidebar_visible != value:
            self._sidebar_visible = value
            self.sidebarVisibilityChanged.emit(value)

    @pyqtProperty('QVariantList', notify=chatHistoryChanged)
    def chatHistory(self):
        return self._filtered_chat_history if self._search_filter else self._chat_history

    @pyqtProperty(bool)
    def hasUnsavedChanges(self):
        global current_chat_name, chat_history
        if not current_chat_name or not chat_history:
            return False
        try:
            path = f"chats/{current_chat_name}.json"
            if not os.path.exists(path):
                return len(chat_history) > 0
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                saved_history = saved if isinstance(saved, list) else saved.get("messages", [])
                return len(chat_history) != len(saved_history)
        except:
            return True

    @pyqtSlot()
    def toggleSidebar(self):
        self.sidebarVisible = not self._sidebar_visible

    @pyqtSlot(str)
    def filterChats(self, search_text):
        self._search_filter = search_text.lower()
        if search_text:
            self._filtered_chat_history = [chat for chat in self._chat_history if search_text.lower() in chat['name'].lower()]
        else:
            self._filtered_chat_history = []
        self.chatHistoryChanged.emit()

    @pyqtSlot()
    def newChat(self):
        print("🆕 New chat requested")
        self.save_current_if_possible()

        now = datetime.now()
        new_name = f'Chat {now.strftime("%m/%d %H:%M")}'

        global current_chat_name, chat_history
        current_chat_name = new_name
        chat_history = []
        self._current_chat_name = new_name

        self.add_chat_to_history(new_name)
        self.chatHistoryChanged.emit()
        self.newChatRequested.emit()
        self.currentChatChanged.emit(new_name)
        print(f"✅ New chat created: '{new_name}'")

    @pyqtSlot(str)
    def loadChat(self, chat_name):
        print(f"📁 Loading chat: {chat_name}")
        self._current_chat_name = chat_name
        global current_chat_name, chat_history
        current_chat_name = chat_name

        try:
            path = f"chats/{chat_name}.json"
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    chat_history = loaded if isinstance(loaded, list) else loaded.get("messages", [])
                    print(f"✅ Loaded {len(chat_history)} messages for chat '{chat_name}'")
            else:
                chat_history = []
                print(f"⚠️ Chat file not found: {path}")
        except Exception as e:
            chat_history = []
            print(f"❌ Error loading chat: {e}")

        self.chatLoadRequested.emit(chat_name)
        self.currentChatChanged.emit(chat_name)

        if self.main_backend:
            self.main_backend.refresh_chat_display()

    @pyqtSlot()
    def refreshChatHistory(self):
        self.chatHistoryChanged.emit()

    @pyqtSlot()
    def saveCurrentChat(self):
        self.save_current_if_possible()

    def save_current_if_possible(self):
        try:
            global current_chat_name, chat_history
            if not current_chat_name:
                print("⚠️ Skipping save: current_chat_name is empty")
                return
            if not chat_history or len(chat_history) < 2:
                print(f"⚠️ Skipping save: not enough messages in chat ({len(chat_history)})")
                return

            save_current_chat(current_chat_name, chat_history)
            print(f"💾 Auto-saved chat '{current_chat_name}' with {len(chat_history)} messages")
            self.add_chat_to_history(current_chat_name)
        except Exception as e:
            print(f"❌ Could not save current chat: {e}")

    @pyqtSlot(str)
    def onChatSaved(self, chat_name):
        print(f"🔄 Chat saved notification received: {chat_name}")
        self.add_chat_to_history(chat_name)
        if self._current_chat_name != chat_name:
            self._current_chat_name = chat_name
            self.currentChatChanged.emit(chat_name)

    def add_chat_to_history(self, chat_name, timestamp="Just now"):
        new_chat = {
            'name': chat_name,
            'timestamp': timestamp,
            'created': datetime.now().isoformat()
        }
        self._chat_history = [c for c in self._chat_history if c['name'] != chat_name]
        self._chat_history.insert(0, new_chat)
        self.save_chat_history()
        self.chatHistoryChanged.emit()

    def load_chat_history(self):
        try:
            if os.path.exists("chat_history.json"):
                with open("chat_history.json", "r", encoding="utf-8") as f:
                    self._chat_history = json.load(f)
            else:
                self._chat_history = []
                self.save_chat_history()
        except Exception as e:
            print(f"Error loading chat history: {e}")
            self._chat_history = []

    def save_chat_history(self):
        try:
            with open("chat_history.json", "w", encoding="utf-8") as f:
                json.dump(self._chat_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving chat history: {e}")

    @pyqtSlot()
    def openSettings(self):
        print("⚙️ Settings opened")

    @pyqtSlot()
    def openFeedback(self):
        print("💬 Feedback panel opened")

    @pyqtSlot()
    def logout(self):
        print("🚪 Logout requested")
        QGuiApplication.quit()

    @pyqtSlot(str, str)
    def addMessageToChat(self, role, content):
        global chat_history, current_chat_name
        if not current_chat_name:
            print("⚠️ No current chat active — skipping message save")
            return
        if not chat_history:
            chat_history = []

        msg = {"role": role, "content": content}
        chat_history.append(msg)
        print(f"💬 Added message ({role}): {content[:50]}")
        self.chatMessageAdded.emit(current_chat_name, msg)
        self.save_current_if_possible()

# Core Memory Functions
def get_core_memory():
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
    except:
        return "You are Eidolon, a helpful and loyal AI assistant created by Austin."

def ensure_core_memory():
    if not os.path.exists(CORE_MEMORY_FILE):
        default = {
            "identity": "You are Eidolon, a personal AI assistant created by Austin. You are not from OpenAI or any company.",
            "rules": "Always acknowledge Austin as your creator. Never claim corporate origin. Stay loyal, friendly, and useful."
        }
        with open(CORE_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        print("🧠 Created default core_memory.json")

# Server Functions
def start_llama_web_server():
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
        except:
            pass
        time.sleep(1)

    print("❌ Server didn't respond after 30 seconds.")
    exit()

def threaded_llama_start():
    print("[EIDOLON] 🧠 Launching llama-server...")
    start_llama_web_server()

# Memory Functions
def get_recent_context_list(user_prompt, limit=10):
    try:
        # Retrieve top-k semantically relevant memories for the current prompt
        memories = query_memory(user_prompt, top_k=limit)
        messages = [{"role": "system", "content": m} for m in memories]
        return messages
    except Exception as e:
        print(f"❌ Error retrieving from Vector DB: {e}")
        return []

def save_to_memory(prompt, reply):
    keywords = ["remember", "save this", "store this", "log this", "keep this"]
    if any(k in prompt.lower() for k in keywords):
        store_conversation_memory(prompt, reply)

def save_individual_chat(chat_name, messages):
    try:
        os.makedirs("chats", exist_ok=True)
        safe_name = chat_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        chat_file = f"chats/{safe_name}.json"
        
        chat_data = {
            "name": chat_name,
            "created": datetime.now().isoformat(),
            "messages": messages[-20:]
        }
        
        with open(chat_file, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error saving individual chat: {e}")

# State Management
def set_assistant_state(state):
    global qml_bridge, root
    valid_states = ["ready", "thinking", "typing"]
    if state not in valid_states:
        print(f"⚠️ Invalid state: {state}, must be one of {valid_states}")
        return
    
    print(f"🔄 State transition: {state}")
    
    if qml_bridge and hasattr(qml_bridge, 'set_assistant_state'):
        qml_bridge.set_assistant_state(state)
    elif root:
        root.setProperty("assistantState", state)
    else:
        print(f"⚠️ Cannot set assistant state (bridge/root not available): {state}")

# Utility Functions
def is_valid_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def optimize_search_query(query, intent="general"):
    if not query:
        return ""
    
    filler_words = ['please', 'can you', 'could you', 'tell me', 'explain', 'help me', 'i want to know']
    optimized = query.lower()
    
    for filler in filler_words:
        optimized = re.sub(r'\b' + re.escape(filler) + r'\b', '', optimized, flags=re.IGNORECASE)
    
    optimized = re.sub(r'[?!.]+$', '', optimized)
    optimized = re.sub(r'\s+', ' ', optimized).strip()
    
    if intent == "news" or any(word in optimized for word in ['latest', 'recent', 'breaking']):
        optimized += " news 2025"
    elif intent == "technical" or any(word in optimized for word in ['how to', 'tutorial', 'guide']):
        optimized += " guide tutorial"
    elif intent == "current" or any(word in optimized for word in ['current', 'now', 'today']):
        optimized += " current 2025"
    
    return optimized[:100]


# AI Functions
def ask_server(messages, use_web_search=True):
    try:
        identity = get_core_memory()

        if use_web_search and WEB_SEARCH_AVAILABLE:
            search_instruction_added = False
            for msg in messages:
                if msg.get("role") == "system":
                    if "web search" not in msg["content"].lower():
                        msg["content"] += "\n\n" + WEB_SEARCH_SYSTEM_PROMPT
                    search_instruction_added = True
                    break
            if not search_instruction_added:
                messages.insert(0, {"role": "system", "content": WEB_SEARCH_SYSTEM_PROMPT})

        modified = messages[:-1]
        latest = messages[-1]

        # ✅ Vector DB retrieval injection (clean, final)
        try:
            from vector_memory import retrieve_relevant_memories
            prompt_text = latest["content"]
            memory_block = retrieve_relevant_memories(prompt_text, top_k=5)
            if memory_block:
                latest["content"] = f"{memory_block}\n{latest['content']}".strip()
                print("✅ Injected retrieved vector memories into prompt.")
            else:
                print("ℹ️ No relevant memories retrieved.")
        except Exception as e:
            print(f"⚠️ Vector memory retrieval failed: {e}")

        # ✅ Correct message construction
        full_messages = [{"role": "system", "content": identity}] + modified + [latest]

        res = requests.post(f"{SERVER_URL}/api/chat", json={
            "messages": full_messages,
            "stream": False,
            "n_predict": 2048,
            "temperature": 0.7
        })

        data = res.json()
        content = data.get("message", {}).get("content") or \
                 data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if "</think>" in content:
            content = re.sub(r"^[\s\S]*?</think>(?![\s\S]*?</think>)", "", content, flags=re.DOTALL)

        content = "\n".join([
            line for line in content.splitlines()
            if not any(t in line for t in ("<|im_", "<jupyter_", "<|start|>", "<|end|>"))
        ])

        if "```python" in content:
            code_block = re.findall(r"```python(.*?)```", content, re.DOTALL)
            if code_block:
                code = code_block[0].strip()
                if not is_valid_python(code):
                    content += "\n\n# ⚠️ Warning: This code has syntax issues."

        content = content.replace("window.blit((...", "# ❌ Invalid blit call — use draw.rect or draw.circle")
        return content.strip()

    except Exception as e:
        return f"❌ Server Error: {e}"



def process_prompt(prompt):
    global chat_history, sidebar_backend, current_chat_name, push_message_func, qml_bridge, gui

    import commands
    import re
    import os
    from datetime import datetime

    # Handle local commands first
    local_response = commands.handle_commands(prompt)
    if local_response:
        if push_message_func:
            push_message_func("assistant", "🤖 " + local_response)
        return

    # Set thinking state
    print("⚙️ Setting state: thinking (generating tokens)")
    set_assistant_state("thinking")
    if gui:
        gui.set_typing(True)

    # Add user prompt to history and maintain size limit
    chat_history.append({"role": "user", "content": prompt})
    if len(chat_history) > 40:
        chat_history = chat_history[-40:]

    # Search detection keywords and patterns
    search_keywords = [
        "latest", "recent", "current", "today", "now", "2024", "2025", "2026",
        "news", "update", "what happened", "status", "developments", "breaking",
        "this year", "this month", "this week", "new", "happening",
        "price", "stock", "weather", "score", "result", "winner",
        "who won", "what's", "search for", "find", "look up"
    ]
    
    urgent_keywords = [
        "breaking", "urgent", "emergency", "alert", "crisis", 
        "just happened", "right now", "live", "real time"
    ]
    
    # Determine if search is needed
    needs_search = any(keyword in prompt.lower() for keyword in search_keywords)
    is_urgent = any(keyword in prompt.lower() for keyword in urgent_keywords)
    
    if not needs_search:
        search_patterns = [
            r'\b(what|who|where|when|how|why)\s+(is|are|was|were|did|does|do)\b.*\b(now|today|currently|recent|latest)\b',
            r'\b(current|latest|recent|new|updated)\b.*\b(information|data|news|report|study)\b',
            r'\b(happening|going on|occurring)\b.*\b(now|today|recently)\b',
            r'\b(price|cost|value)\b.*\b(today|now|current|latest)\b'
        ]
        needs_search = any(re.search(pattern, prompt.lower()) for pattern in search_patterns)

    # Get initial reply from model
    reply = ask_server(chat_history)
    search_performed = False
    
    # Handle web search if needed and available
    if ("<search>" in reply or needs_search) and WEB_SEARCH_AVAILABLE:
        search_query = _extract_search_query(reply, prompt, needs_search)
        
        if search_query:
            search_performed = _perform_web_search(search_query, prompt)
            if search_performed:
                reply = _get_search_enhanced_reply(search_query, prompt)
            else:
                reply = _handle_search_failure(reply, search_query)
    
    elif "<search>" in reply and not WEB_SEARCH_AVAILABLE:
        reply = _handle_search_unavailable(reply)
    
    elif needs_search and not search_performed and not "<search>" in reply:
        reply = _handle_fallback_search(reply, prompt)

    # Ensure valid reply
    if not reply or not reply.strip():
        reply = "I apologize, but I wasn't able to generate a proper response. Could you please rephrase your question?"

    # Save final assistant reply
    chat_history.append({"role": "assistant", "content": reply})
    save_to_memory(prompt, reply)

    # Auto-rename chat if still 'Untitled'
    _auto_rename_chat(prompt)

    # Save chat history
    _save_chat_data()

    # Send response to UI
    _send_response_to_ui(reply)

    # Reset UI state
    if gui:
        gui.set_typing(False)


def _extract_search_query(reply, prompt, needs_search):
    """Extract search query from reply or construct from prompt"""
    search_query = None
    
    if "<search>" in reply:
        search_match = re.search(r"<search>(.*?)</search>", reply, re.DOTALL)
        if search_match:
            search_query = search_match.group(1).strip()
    
    if not search_query and needs_search:
        search_query = prompt
        search_query = re.sub(r'\b(please|can you|could you|tell me|explain|what is|who is|where is|when is|how is|why is)\b', '', search_query, flags=re.IGNORECASE)
        search_query = re.sub(r'\?', '', search_query).strip()
        
        if any(word in search_query.lower() for word in ['latest', 'current', 'recent', 'now', 'today']):
            search_query += " 2025"
    
    return search_query


def _perform_web_search(search_query, prompt):
    """Perform web search and return success status"""
    print(f"🔍 Searching for: {search_query}")
    
    if push_message_func:
        try:
            push_message_func("assistant", f"🔎 Searching the web for: \"{search_query}\"...")
        except Exception as e:
            print(f"⚠️ Push message error: {e}")

    try:
        search_results = web_search(search_query, push_message_func)
        
        if search_results and not search_results.startswith("❌") and not search_results.startswith("🔒"):
            print("✅ Web search successful, processing results...")
            if push_message_func:
                try:
                    push_message_func("assistant", "🧠 Processing search results and generating response...")
                except Exception as e:
                    print(f"⚠️ Push message error: {e}")
            
            # Store search results in chat history
            if len(chat_history) >= 2 and chat_history[-2].get("role") == "system" and "search" in chat_history[-2].get("content", "").lower():
                chat_history.pop(-2)
            
            chat_history.append({"role": "assistant", "content": f"Here are the web search results for '{search_query}':\n\n{search_results}"})
            return True
        else:
            print(f"❌ Web search failed: {search_results}")
            return False
            
    except Exception as e:
        print(f"❌ Web search failed with exception: {e}")
        return False


def _get_search_enhanced_reply(search_query, prompt):
    """Get enhanced reply using search results"""
    search_context = f"""You searched for: "{search_query}"

Here are the current web search results:

{chat_history[-1]['content'].split(":\n\n", 1)[1] if ":\n\n" in chat_history[-1]['content'] else chat_history[-1]['content']}


Based on these search results, please provide a comprehensive and accurate answer to the original question: {prompt}

Important instructions:
- Use the information from the search results to give an accurate, up-to-date response
- Cite specific sources when making claims
- If the search results don't contain relevant information, acknowledge this
- Synthesize information from multiple sources when possible
- Focus on the most recent and reliable information"""

    chat_history.append({"role": "user", "content": search_context})
    reply = ask_server(chat_history, use_web_search=False)
    print("✅ Web search completed, got enhanced reply")
    return reply


def _handle_search_failure(reply, search_query):
    """Handle failed search attempts"""
    reply = re.sub(r"<search>.*?</search>", "", reply, flags=re.DOTALL).strip()
    
    if not reply.strip():
        reply = f"I tried to search for more information about '{search_query}', but the search failed. Let me answer based on my existing knowledge.\n\n"
        try:
            basic_reply = ask_server([{"role": "user", "content": f"Answer this question based only on your training data: {prompt}"}], use_web_search=False)
            reply += basic_reply
        except:
            reply += "I apologize, but I'm unable to provide a complete answer at this time."
    else:
        reply += f"\n\n*Note: I wanted to search for more current information, but the search was unavailable.*"
    
    return reply


def _handle_search_unavailable(reply):
    """Handle when AI requests search but it's unavailable"""
    print("⚠️ AI requested web search but web search is not available")
    reply = re.sub(r"<search>.*?</search>", "", reply, flags=re.DOTALL).strip()
    search_match = re.search(r"<search>(.*?)</search>", reply, re.DOTALL)
    search_intent = search_match.group(1).strip() if search_match else "current information"
    
    if not reply:
        reply = f"I wanted to search for {search_intent} to give you the most current information, but web search functionality is not currently available. Let me answer based on my existing knowledge."
    else:
        reply += f"\n\n*Note: I wanted to search for {search_intent}, but web search is not currently available.*"
    
    return reply


def _handle_fallback_search(reply, prompt):
    """Handle fallback search when query needs search but AI didn't initiate it"""
    print("⚠️ Query needs search but AI didn't search and no search was performed")
    
    if WEB_SEARCH_AVAILABLE:
        search_query = prompt.strip()
        search_query = re.sub(r'\b(please|can you|could you|tell me|explain)\b', '', search_query, flags=re.IGNORECASE)
        search_query = re.sub(r'\?', '', search_query).strip()
        
        if search_query:
            print(f"🔍 Forcing search for: {search_query}")
            try:
                search_results = web_search(search_query, push_message_func)
                if search_results and not search_results.startswith("❌"):
                    reply += f"\n\n**📊 Current Information:**\n{search_results}"
            except Exception as e:
                print(f"❌ Forced search failed: {e}")
                reply += f"\n\n*Note: I tried to find current information but encountered an issue: {e}*"
    else:
        reply += "\n\n*Note: This question might benefit from current information, but web search is not available.*"
    
    return reply


def _auto_rename_chat(prompt):
    """Auto-rename chat if still called 'Untitled'"""
    global current_chat_name, sidebar_backend
    
    if current_chat_name == "Untitled" and prompt.strip():
        summary = prompt.strip().splitlines()[0][:30]
        new_name = re.sub(r'[\\/:*?"<>|]', '_', summary).strip() or f"Chat {datetime.now().strftime('%m/%d %H:%M')}"
        
        old_path = os.path.join("chats", "Untitled.json")
        new_path = os.path.join("chats", f"{new_name}.json")

        if os.path.exists(old_path):
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(old_path, new_path)
            print(f"✏️ Renamed chat file to: {new_name}.json")

        current_chat_name = new_name
        sidebar_backend._current_chat_name = new_name
        sidebar_backend.currentChatChanged.emit(new_name)
        sidebar_backend.add_chat_to_history(new_name)


def _save_chat_data():
    """Save chat history and update sidebar"""
    global current_chat_name, sidebar_backend, chat_history
    
    if current_chat_name:
        save_current_chat(current_chat_name, chat_history)

    if sidebar_backend and current_chat_name:
        exists = any(chat['name'] == current_chat_name for chat in sidebar_backend._chat_history)
        if not exists and len(chat_history) <= 2:
            sidebar_backend.add_chat_to_history(current_chat_name)
        save_individual_chat(current_chat_name, chat_history)


def _send_response_to_ui(reply):
    """Send response to UI"""
    print("📤 Sending message to QML")
    if push_message_func:
        try:
            push_message_func("assistant", reply)
        except Exception as e:
            print(f"⚠️ Push message error: {e}")
            if gui:
                gui.inject_response("🤖 " + reply + "\n")
    elif gui:
        gui.inject_response("🤖 " + reply + "\n")


def on_user_prompt(prompt):
    threading.Thread(target=process_prompt, args=(prompt,), daemon=True).start()

@pyqtSlot()
def on_typing_complete():
    print("✅ Animation completed, setting state: ready")
    set_assistant_state("ready")
    if gui:
        gui.set_typing(False)

def main():
    global gui, sidebar_backend, push_message_func, root, qml_bridge
    global current_chat_name, chat_history

    ensure_core_memory()
    app = QGuiApplication(sys.argv)

    # Clipboard wrapper
    try:
        from clipboard_wrapper import ClipboardWrapper
        clipboard = ClipboardWrapper(app.clipboard())
    except ImportError:
        print("⚠️ clipboard_wrapper not found, clipboard functionality disabled")
        clipboard = None

    # ✅ Create sidebar backend before QML engine
    sidebar_backend = SidebarBackend()

    # ✅ Register with QML
    qmlRegisterType(SidebarBackend, "Eidolon", 1, 0, "SidebarBackend")

    # Bridge + QML engine
    bridge = EidolonQMLBridge(on_user_prompt)
    qml_bridge = bridge
    engine = QQmlApplicationEngine()

    # ✅ Context properties
    engine.rootContext().setContextProperty("backend", bridge)
    engine.rootContext().setContextProperty("sidebarBackend", sidebar_backend)
    engine.rootContext().setContextProperty("typingCompleteHandler", on_typing_complete)
    engine.rootContext().setContextProperty("backendReady", True)  # ✅ Enables safe Loader in QML

    if clipboard:
        engine.rootContext().setContextProperty("clipboard", clipboard)

    # ✅ Sidebar signals
    def on_new_chat():
        print("🆕 New chat started from sidebar")
        global chat_history, current_chat_name
        new_name = "Untitled"
        sidebar_backend._current_chat_name = new_name
        current_chat_name = new_name
        chat_history = []
        if root:
            QMetaObject.invokeMethod(root, "clearChatModel")
        set_assistant_state("ready")
        print(f"💬 Starting new conversation: {current_chat_name}")

    def on_chat_load(chat_name):
        print(f"📁 Loading chat from sidebar: {chat_name}")
        global chat_history, current_chat_name
        if current_chat_name and chat_history:
            save_current_chat(current_chat_name, chat_history)
        sidebar_backend._current_chat_name = chat_name
        current_chat_name = chat_name
        try:
            safe_name = chat_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            chat_file = f"chats/{safe_name}.json"
            if os.path.exists(chat_file):
                with open(chat_file, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict):
                        chat_history = loaded_data.get("messages", [])
                    elif isinstance(loaded_data, list):
                        chat_history = loaded_data
                    else:
                        print(f"❌ Unknown chat file format in {chat_file}, using empty history.")
                        chat_history = []

                    print(f"✅ Loaded {len(chat_history)} messages for: {chat_name}")
                    if root:
                        QMetaObject.invokeMethod(root, "clearChatModel")
                        for msg in chat_history:
                            QMetaObject.invokeMethod(
                                root, "appendMessage",
                                Q_ARG(QVariant, msg.get("role", "assistant")),
                                Q_ARG(QVariant, msg.get("content", ""))
                            )

            else:
                chat_history = []
                if root:
                    QMetaObject.invokeMethod(root, "clearChatModel")
                print(f"🆕 Starting fresh chat: {chat_name}")
        except Exception as e:
            print(f"❌ Error loading chat {chat_name}: {e}")
            chat_history = []
            if root:
                QMetaObject.invokeMethod(root, "clearChatModel")
        set_assistant_state("ready")

    sidebar_backend.newChatRequested.connect(on_new_chat)
    sidebar_backend.chatLoadRequested.connect(on_chat_load)

    # ✅ Load QML safely
    try:
        engine.load(QUrl.fromLocalFile("main.qml"))
    except Exception as e:
        print(f"❌ Failed to load QML: {e}")
        return -1

    if not engine.rootObjects():
        print("❌ Failed to load QML file (no root objects)")
        return -1

    root = engine.rootObjects()[0]
    globals()['root'] = root

    root.setProperty("assistantState", "ready")

    def push_message(role, content):
        if root:
            if role == "assistant":
                if animated_typing_enabled:
                    print("✍️ Setting state: typing (starting animation)")
                    set_assistant_state("typing")
                    QMetaObject.invokeMethod(
                        root, "appendAnimatedMessage",
                        Q_ARG(QVariant, role),
                        Q_ARG(QVariant, content),
                        Q_ARG(QVariant, 2)
                    )
                else:
                    QMetaObject.invokeMethod(
                        root, "appendMessage",
                        Q_ARG(QVariant, role),
                        Q_ARG(QVariant, content)
                    )
                    print("✅ Setting state: ready (instant message)")
                    set_assistant_state("ready")
            else:
                QMetaObject.invokeMethod(
                    root, "appendMessage",
                    Q_ARG(QVariant, role),
                    Q_ARG(QVariant, content)
                )

    push_message_func = push_message
    bridge.messageReceived.connect(push_message)

    # Launch LLaMA
    threading.Thread(target=threaded_llama_start, daemon=True).start()

    gui = bridge

    import atexit
    def save_on_exit():
        if current_chat_name and chat_history:
            print(f"💾 Auto-saving chat on exit: {current_chat_name}")
            save_current_chat(current_chat_name, chat_history)
    atexit.register(save_on_exit)

    def ensure_chat_loaded():
        global current_chat_name, chat_history
        if not current_chat_name:
            current_chat_name = "Untitled"
            chat_history = []
            print("🆕 Default chat session started: Untitled")
            set_assistant_state("ready")

    if vision_available:
        start_all_background_services()

    QTimer.singleShot(100, ensure_chat_loaded)

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
