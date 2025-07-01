import os
import json
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot
from PyQt6.QtGui import QGuiApplication

# Import the save_current_chat function from your modular memory system
try:
    from eidolon.memory.chat_storage import save_current_chat
except ImportError:
    def save_current_chat(name, history):
        print(f"⚠️ [Stub] Would save chat '{name}' with {len(history)} messages")
        return name

# Import your global state cleanly (temporary until replaced with state injection)
try:
    import globals_state as gs
except ImportError:
    class MockGlobals:
        current_chat_name = None
        chat_history = []
    gs = MockGlobals()

# Sidebar Backend Class
class SidebarBackend(QObject):
    sidebarVisibilityChanged = pyqtSignal(bool)
    chatHistoryChanged = pyqtSignal()
    newChatRequested = pyqtSignal()
    currentChatChanged = pyqtSignal(str)
    chatLoadRequested = pyqtSignal(str)
    chatMessageAdded = pyqtSignal(str, dict)

    def __init__(self, app_context):
        super().__init__()
        self.app_context = app_context  # ✅ store app_context for replacing gs

        self._sidebar_visible = True
        self._chat_history = []
        self._filtered_chat_history = []
        self._current_chat_name = ""
        self._search_filter = ""
        self.main_backend = None

        # Load chat history immediately and scan for existing chats
        self.load_chat_history()
        self.scan_existing_chats()


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
        """Return the appropriate chat history list for QML ListView"""
        result = self._filtered_chat_history if self._search_filter else self._chat_history
        print(f"[SidebarBackend] chatHistory property accessed, returning {len(result)} items")
        return result

    @pyqtProperty(bool)
    def hasUnsavedChanges(self):
        if not gs.current_chat_name or not gs.chat_history:
            return False
        try:
            safe_name = gs.current_chat_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            path = f"chats/{safe_name}.json"
            if not os.path.exists(path):
                return len(gs.chat_history) > 0
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                saved_history = saved if isinstance(saved, list) else saved.get("messages", [])
                return len(gs.chat_history) != len(saved_history)
        except:
            return True

    def scan_existing_chats(self):
        """Scan the chats/ directory and add any missing chats to history"""
        if not os.path.exists("chats"):
            return
        
        try:
            existing_names = {chat['name'] for chat in self._chat_history}
            
            for filename in os.listdir("chats"):
                if filename.endswith(".json"):
                    try:
                        filepath = os.path.join("chats", filename)
                        with open(filepath, "r", encoding="utf-8") as f:
                            chat_data = json.load(f)
                        
                        # Extract chat name and timestamps
                        if isinstance(chat_data, dict):
                            chat_name = chat_data.get("name", filename[:-5].replace('_', ' '))
                            created_str = chat_data.get("created")
                            modified_str = chat_data.get("modified")
                        else:
                            # Legacy format
                            chat_name = filename[:-5].replace('_', ' ')
                            created_str = None
                            modified_str = None
                        
                        if chat_name not in existing_names:
                            # Parse timestamps
                            if created_str:
                                try:
                                    created_time = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                                except:
                                    created_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                            else:
                                created_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                            
                            # Use modified time if available, otherwise created time
                            if modified_str:
                                try:
                                    display_time = datetime.fromisoformat(modified_str.replace('Z', '+00:00'))
                                except:
                                    display_time = created_time
                            else:
                                display_time = created_time
                            
                            timestamp = display_time.strftime("%m/%d %H:%M")
                            
                            self._chat_history.append({
                                'name': chat_name,
                                'timestamp': timestamp,
                                'created': created_time.isoformat()
                            })
                            print(f"[SidebarBackend] Added existing chat to history: {chat_name}")
                        
                    except Exception as e:
                        print(f"[SidebarBackend] Error processing chat file {filename}: {e}")
            
            # Sort by creation time (newest first)
            self._chat_history.sort(key=lambda x: x.get('created', ''), reverse=True)
            
            # Save the updated history and notify QML
            self.save_chat_history()
            self.chatHistoryChanged.emit()
            print(f"[SidebarBackend] Scan complete, total chats: {len(self._chat_history)}")
            
        except Exception as e:
            print(f"[SidebarBackend] Error scanning existing chats: {e}")

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
        print(f"[SidebarBackend] Filtered chats: {len(self._filtered_chat_history)} matches for '{search_text}'")
        self.chatHistoryChanged.emit()

    @pyqtSlot()
    def newChat(self):
        print("🆕 New chat requested")
        self.save_current_if_possible()

        now = datetime.now()
        new_name = f'Chat {now.strftime("%m/%d %H:%M")}'

        # Update global state
        gs.current_chat_name = new_name
        gs.chat_history = []
        self._current_chat_name = new_name

        # Emit signals
        self.newChatRequested.emit()
        self.currentChatChanged.emit(new_name)
        print(f"✅ New chat created: '{new_name}'")

    @pyqtSlot(str)
    def loadChat(self, chat_name):
        print(f"📁 Loading chat: {chat_name}")
        self._current_chat_name = chat_name
        gs.current_chat_name = chat_name

        try:
            safe_name = chat_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            path = f"chats/{safe_name}.json"
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    gs.chat_history = loaded if isinstance(loaded, list) else loaded.get("messages", [])
                    print(f"✅ Loaded {len(gs.chat_history)} messages for chat '{chat_name}'")
            else:
                gs.chat_history = []
                print(f"⚠️ Chat file not found: {path}")
        except Exception as e:
            gs.chat_history = []
            print(f"❌ Error loading chat: {e}")

        self.chatLoadRequested.emit(chat_name)
        self.currentChatChanged.emit(chat_name)

        if self.main_backend:
            self.main_backend.refresh_chat_display()

    @pyqtSlot()
    def refreshChatHistory(self):
        """Force refresh the chat history from disk and notify QML"""
        print("[SidebarBackend] Manual refresh requested")
        self.scan_existing_chats()  # This will emit chatHistoryChanged

    @pyqtSlot()
    def saveCurrentChat(self):
        self.save_current_if_possible()

    def save_current_if_possible(self):
        try:
            if not gs.current_chat_name:
                print("⚠️ Skipping save: current_chat_name is empty")
                return
            if not gs.chat_history or len(gs.chat_history) < 1:
                print(f"⚠️ Skipping save: not enough messages in chat ({len(gs.chat_history)})")
                return

            # Save and get the actual name used (may be auto-generated)
            actual_name = save_current_chat(gs.current_chat_name, gs.chat_history)
            
            # Update global state if name changed
            if actual_name != gs.current_chat_name:
                gs.current_chat_name = actual_name
                self._current_chat_name = actual_name
                self.currentChatChanged.emit(actual_name)
            
            print(f"💾 Auto-saved chat '{actual_name}' with {len(gs.chat_history)} messages")
            
            # Ensure this chat appears in sidebar with correct name
            self.add_chat_to_history(actual_name)
            
        except Exception as e:
            print(f"❌ Could not save current chat: {e}")

    @pyqtSlot(str)
    def onChatSaved(self, chat_name):
        print(f"🔄 Chat saved notification received: {chat_name}")
        self.add_chat_to_history(chat_name)
        if self._current_chat_name != chat_name:
            self._current_chat_name = chat_name
            self.currentChatChanged.emit(chat_name)

    def add_chat_to_history(self, chat_name, timestamp=None):
        """Add or update a chat in the history list"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%m/%d %H:%M")
        
        new_chat = {
            'name': chat_name,
            'timestamp': timestamp,
            'created': datetime.now().isoformat()
        }
        
        # Remove existing entry for this chat name
        self._chat_history = [c for c in self._chat_history if c['name'] != chat_name]
        
        # Add to beginning of list (most recent first)
        self._chat_history.insert(0, new_chat)
        
        # Save and notify
        self.save_chat_history()
        self.chatHistoryChanged.emit()
        print(f"[SidebarBackend] Added/updated chat in history: {chat_name}")

    def load_chat_history(self):
        """Load chat history from chat_history.json"""
        try:
            if os.path.exists("chat_history.json"):
                with open("chat_history.json", "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        print("⚠️ chat_history.json was empty, reinitializing.")
                        self._chat_history = []
                        self.save_chat_history()
                    else:
                        self._chat_history = json.loads(content)
                        print(f"[SidebarBackend] Loaded {len(self._chat_history)} chats from history")
            else:
                print("[SidebarBackend] No chat_history.json found, starting fresh")
                self._chat_history = []
                self.save_chat_history()
        except Exception as e:
            print(f"[SidebarBackend] Error loading chat history: {e}")
            self._chat_history = []

    def save_chat_history(self):
        """Save chat history to chat_history.json"""
        try:
            with open("chat_history.json", "w", encoding="utf-8") as f:
                json.dump(self._chat_history, f, indent=2, ensure_ascii=False)
            print(f"[SidebarBackend] Saved chat history with {len(self._chat_history)} entries")
        except Exception as e:
            print(f"[SidebarBackend] Error saving chat history: {e}")

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
        """Add a message to the current chat and update name if needed"""
        if not gs.current_chat_name:
            print("⚠️ No current chat active — skipping message save")
            return
        if not gs.chat_history:
            gs.chat_history = []

        msg = {"role": role, "content": content}
        gs.chat_history.append(msg)
        print(f"💬 Added message ({role}): {content[:50]}...")
        
        # If this is the first user message and we have a generic name, update it
        if (role == "user" and 
            gs.current_chat_name and 
            (gs.current_chat_name.startswith("Chat ") or gs.current_chat_name in ["Untitled", "Untitled Chat"])):
            
            # Generate a better name from the user message
            from eidolon.memory.chat_storage import _generate_chat_name
            new_name = _generate_chat_name(gs.chat_history)
            if new_name != gs.current_chat_name:
                gs.current_chat_name = new_name
                self._current_chat_name = new_name
                self.currentChatChanged.emit(new_name)
                print(f"🏷️ Updated chat name to: {new_name}")
        
        # Emit signal for any listeners
        self.chatMessageAdded.emit(gs.current_chat_name, msg)
        
        # Auto-save after adding message
        self.save_current_if_possible()