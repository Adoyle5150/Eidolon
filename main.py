import sys
import os
os.environ["CHROMA_TELEMETRY"] = "OFF"
try:
    import posthog

    def noop_capture(*args, **kwargs):
        pass

    posthog.capture = noop_capture

    print("✅ PostHog telemetry fully disabled.")
except ImportError:
    pass

import json
import time
import re
import ast
import threading
import subprocess
import requests
from datetime import datetime
from clipboard_wrapper import ClipboardWrapper



# ✅ Force Fusion style to allow QML background/contentItem customization
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Fusion"

# ✅ Fix for Pylance import errors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append("E:/Eidolon")
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Vision"))

# =====================================================
# ✅ Qt Imports FIRST to avoid DPI policy error
# =====================================================
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QUrl, QObject, QMetaObject, 
    Q_ARG, QVariant, pyqtProperty, pyqtSlot
)
from PyQt6.QtGui import QGuiApplication, QSurfaceFormat
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType

# ✅ Set DPI scaling policy BEFORE any QGuiApplication instance
QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

# ✅ Set OpenGL and translucency for frameless resizing
fmt = QSurfaceFormat()
fmt.setAlphaBufferSize(8)
QSurfaceFormat.setDefaultFormat(fmt)

# =====================================================
# ✅ Import AppContext instead of globals_state
# =====================================================
from eidolon.core.app_context import AppContext
app_context = AppContext()

# =====================================================
# ✅ Now safe to import heavy Eidolon modules
# =====================================================
from eidolon.gui.sidebar_backend import SidebarBackend
from eidolon.memory.core_memory import get_core_memory, ensure_core_memory
from eidolon.core.server_utils import start_llama_web_server, threaded_llama_start
from eidolon.core.state_manager import set_assistant_state
from eidolon.utils.helpers import is_valid_python, optimize_search_query
from eidolon.core.ai_handler import ask_server
from eidolon import config
from eidolon.core.prompt_processor import process_prompt
from eidolon.memory.chat_storage import save_current_chat
from eidolon.gui.eidolon_qml_bridge import setup_qml_bridge
from eidolon.memory.chat_storage import save_individual_chat


# =====================================================
# ✅ Web search imports
# =====================================================
try:
    from web.searcher import web_search, get_searcher
    WEB_SEARCH_AVAILABLE = True
    print("✅ Web search module loaded successfully from searcher.py")
except ImportError as e:
    WEB_SEARCH_AVAILABLE = False
    print(f"⚠️ Web search not available: {e}")

# =====================================================
# ✅ Vision system imports
# =====================================================
try:
    from eidolon_vision import EidolonVision
    from startup import start_all_background_services
    vision_available = True
    print("✅ Eidolon Vision module loaded")
except Exception as e:
    vision_available = False
    print(f"⚠️ Eidolon Vision not available: {e}")

# =====================================================
# ✅ Web search system prompt (keep here for clarity)
# =====================================================
WEB_SEARCH_SYSTEM_PROMPT = (
    "You are a helpful assistant. Rephrase the user's request into a clear, concise web search query "
    "that can be used to find real-time information on the web."
)

# =====================================================
# ✅ Event handlers
# =====================================================
def on_user_prompt(prompt):
    threading.Thread(target=process_prompt, args=(prompt, app_context), daemon=True).start()

@pyqtSlot()
def on_typing_complete():
    print("✅ Animation completed, setting state: ready")
    set_assistant_state("ready")
    if app_context.gui:
        app_context.gui.set_typing(False)

def main():
    ensure_core_memory()
    app = QGuiApplication(sys.argv)

    # ✅ Correct clipboard setup
    qt_clipboard = app.clipboard()
    clipboard = ClipboardWrapper(qt_clipboard)

    # ✅ Create sidebar backend before QML engine
    sidebar_backend = SidebarBackend(app_context)
    app_context.sidebar_backend = sidebar_backend

    # ✅ Register with QML BEFORE loading QML file
    qmlRegisterType(SidebarBackend, "Eidolon", 1, 0, "SidebarBackend")

    # Bridge + QML engine
    engine = QQmlApplicationEngine()
    bridge = setup_qml_bridge(engine, app_context)
    app_context.qml_bridge = bridge

    # ✅ Context properties - SET BEFORE LOADING QML
    engine.rootContext().setContextProperty("sidebarBackend", app_context.sidebar_backend)
    engine.rootContext().setContextProperty("typingCompleteHandler", on_typing_complete)
    engine.rootContext().setContextProperty("clipboard", clipboard)

    # ✅ Sidebar signals - CONNECT BEFORE LOADING QML
    def on_new_chat():
        print("🆕 New chat started from sidebar")
        new_name = "Untitled"
        app_context.sidebar_backend._current_chat_name = new_name
        app_context.current_chat_name = new_name
        app_context.chat_history = []
        if app_context.root:
            QMetaObject.invokeMethod(app_context.root, "clearChatModel")
        set_assistant_state("ready", qml_bridge=app_context.qml_bridge, root=app_context.root)
        print(f"💬 Starting new conversation: {app_context.current_chat_name}")

    def on_chat_load(chat_name):
        print(f"📁 Loading chat from sidebar: {chat_name}")
        if app_context.current_chat_name and app_context.chat_history:
            save_current_chat(app_context.current_chat_name, app_context.chat_history)
        app_context.sidebar_backend._current_chat_name = chat_name
        app_context.current_chat_name = chat_name
        try:
            safe_name = chat_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            chat_file = f"chats/{safe_name}.json"
            if os.path.exists(chat_file):
                with open(chat_file, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict):
                        app_context.chat_history = loaded_data.get("messages", [])
                    elif isinstance(loaded_data, list):
                        app_context.chat_history = loaded_data
                    else:
                        print(f"❌ Unknown chat file format in {chat_file}, using empty history.")
                        app_context.chat_history = []

                    print(f"✅ Loaded {len(app_context.chat_history)} messages for: {chat_name}")
                    if app_context.root:
                        QMetaObject.invokeMethod(app_context.root, "clearChatModel")
                        for msg in app_context.chat_history:
                            QMetaObject.invokeMethod(
                                app_context.root, "appendMessage",
                                Q_ARG(QVariant, msg.get("role", "assistant")),
                                Q_ARG(QVariant, msg.get("content", ""))
                            )
            else:
                app_context.chat_history = []
                if app_context.root:
                    QMetaObject.invokeMethod(app_context.root, "clearChatModel")
                print(f"🆕 Starting fresh chat: {chat_name}")
        except Exception as e:
            print(f"❌ Error loading chat {chat_name}: {e}")
            app_context.chat_history = []
            if app_context.root:
                QMetaObject.invokeMethod(app_context.root, "clearChatModel")
        set_assistant_state("ready", qml_bridge=app_context.qml_bridge, root=app_context.root)

    app_context.sidebar_backend.newChatRequested.connect(on_new_chat)
    app_context.sidebar_backend.chatLoadRequested.connect(on_chat_load)

    # ✅ Load QML safely
    try:
        engine.load(QUrl.fromLocalFile("main.qml"))
    except Exception as e:
        print(f"❌ Failed to load QML: {e}")
        return -1

    if not engine.rootObjects():
        print("❌ Failed to load QML file (no root objects)")
        return -1

    app_context.root = engine.rootObjects()[0]
    app_context.root.setProperty("assistantState", "ready")

    def push_message(role, content):
        if app_context.root:
            if role == "assistant":
                if app_context.animated_typing_enabled:
                    print("✍️ Assistant typing with animation")
                    set_assistant_state("typing", qml_bridge=app_context.qml_bridge, root=app_context.root)
                    QMetaObject.invokeMethod(
                        app_context.root, "appendAnimatedMessage",
                        Q_ARG(QVariant, role),
                        Q_ARG(QVariant, content),
                        Q_ARG(QVariant, 2)
                    )
                else:
                    QMetaObject.invokeMethod(
                        app_context.root, "appendMessage",
                        Q_ARG(QVariant, role),
                        Q_ARG(QVariant, content)
                    )
                    print("✅ Assistant message displayed instantly")
                    set_assistant_state("ready", qml_bridge=app_context.qml_bridge, root=app_context.root)

                if app_context.current_chat_name:
                    app_context.chat_history.append({"role": role, "content": content})
                    actual_name = save_current_chat(app_context.current_chat_name, app_context.chat_history)
                    if actual_name != app_context.current_chat_name:
                        app_context.current_chat_name = actual_name
                        app_context.sidebar_backend._current_chat_name = actual_name
                        app_context.sidebar_backend.currentChatChanged.emit(actual_name)

                    # ✅ Only reorder to top when sending/receiving a message
                    app_context.sidebar_backend.add_chat_to_history(actual_name, force_top=True)

    app_context.push_message_func = push_message
    bridge.messageReceived.connect(push_message)

    # Launch LLaMA in the background
    threading.Thread(target=threaded_llama_start, daemon=True).start()

    app_context.gui = bridge

    import atexit
    def save_on_exit():
        if app_context.current_chat_name and app_context.chat_history:
            print(f"💾 Auto-saving chat on exit: {app_context.current_chat_name}")
            save_current_chat(app_context.current_chat_name, app_context.chat_history)
    atexit.register(save_on_exit)

    def ensure_chat_loaded():
        if not app_context.current_chat_name:
            app_context.current_chat_name = "Untitled"
            app_context.chat_history = []
            print("🆕 Default chat session started: Untitled")
            set_assistant_state("ready", qml_bridge=app_context.qml_bridge, root=app_context.root)

    if vision_available:
        start_all_background_services()

    QTimer.singleShot(100, ensure_chat_loaded)

    app_context.config = config

    if WEB_SEARCH_AVAILABLE:
        app_context.web_search_func = web_search

    if vision_available:
        try:
            app_context.vision_service = EidolonVision()
        except Exception as e:
            print(f"⚠️ Could not initialize vision service: {e}")

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
