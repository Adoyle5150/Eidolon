import os
import json
import threading
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QMetaObject, Q_ARG, QVariant
from chat_storage import save_current_chat
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine


class EidolonQMLBridge(QObject):
    def __init__(self, assistant_core):
        super().__init__()
        self.assistant_core = assistant_core

    @pyqtSlot(str)
    def sendMessage(self, text):
        self.assistant_core.handle_user_message(text)

def start_gui(assistant_core):
    app = QGuiApplication([])

    engine = QQmlApplicationEngine()

    # Create the SidebarBackend and Bridge
    backend = EidolonQMLBridge(assistant_core)
    sidebar_backend = SidebarBackend(assistant_core)

    # Inject properties for QML
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty("sidebarBackend", sidebar_backend)

    # Load your QML
    engine.load("main.qml")
    if not engine.rootObjects():
        raise SystemExit("❌ Failed to load QML. Check your main.qml path and syntax.")

    # Capture root for push messaging
    root = engine.rootObjects()[0]

    # Hook up assistant_core push messaging
    def push_message(role, content):
        push_message_to_ui(role, content, root=root, animated_typing_enabled=True)

    assistant_core.set_push_message_callback(push_message)

    return app.exec()



# Sidebar Backend Class
class SidebarBackend(QObject):
    sidebarVisibilityChanged = pyqtSignal(bool)
    chatHistoryChanged = pyqtSignal()
    newChatRequested = pyqtSignal()
    currentChatChanged = pyqtSignal(str)
    chatLoadRequested = pyqtSignal(str)
    chatMessageAdded = pyqtSignal(str, dict)

    def __init__(self, assistant_core):
        super().__init__()
        self.assistant_core = assistant_core
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
        current_chat_name = self.assistant_core.get_current_chat_name()
        chat_history = self.assistant_core.get_chat_history()
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
        except Exception as e:
            print(f"⚠️ Error checking unsaved changes: {e}")
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

        # Update global state
        self.assistant_core.set_global_chat_state(new_name, [])

        
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

        # Update global state
        self.assistant_core.set_global_chat_state(chat_name, chat_history)

        
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
            current_chat_name = self.assistant_core.get_current_chat_name()
            chat_history = self.assistant_core.get_chat_history()
            
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
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    @pyqtSlot(str, str)
    def addMessageToChat(self, role, content):
        current_chat_name = self.assistant_core.get_current_chat_name()
        chat_history = self.assistant_core.get_chat_history()

        if not current_chat_name:
            print("⚠️ No current chat active — skipping message save")
            return
        if not chat_history:
            self.assistant_core.set_global_chat_state(current_chat_name, [])
            chat_history = self.assistant_core.get_chat_history()

        msg = {"role": role, "content": content}
        chat_history.append(msg)
        print(f"💬 Added message ({role}): {content[:50]}")
        self.chatMessageAdded.emit(current_chat_name, msg)
        self.save_current_if_possible()


# State Management
def set_assistant_state(state, qml_bridge=None, root=None):
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

# UI Response Functions
def push_message_to_ui(role, content, root=None, animated_typing_enabled=True):
    """Send message to UI with proper state management"""
    if root:
        if role == "assistant":
            if animated_typing_enabled:
                print("✍️ Setting state: typing (starting animation)")
                set_assistant_state("typing", root=root)
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
                set_assistant_state("ready", root=root)
        else:
            QMetaObject.invokeMethod(
                root, "appendMessage",
                Q_ARG(QVariant, role),
                Q_ARG(QVariant, content)
            )

def on_typing_complete(gui=None):
    """Handle completion of typing animation"""
    print("✅ Animation completed, setting state: ready")
    set_assistant_state("ready")
    if gui:
        gui.set_typing(False)