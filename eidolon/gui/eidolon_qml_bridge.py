# eidolon_qml_bridge.py

from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QTimer, pyqtProperty
from PyQt6.QtGui import QGuiApplication
import threading

import globals_state as gs
from eidolon.core.prompt_processor import process_prompt

class EidolonQMLBridge(QObject):
    messageReceived = pyqtSignal(str, str)    # role, content
    typingSignal = pyqtSignal(bool)
    animatedTypingEnabledChanged = pyqtSignal()
    messageSent = pyqtSignal(str)
    responseReceived = pyqtSignal(str)

    _continue_function = None

    def __init__(self, on_prompt_callback):
        super().__init__()
        self.on_prompt_callback = on_prompt_callback

    @pyqtSlot(str)
    def sendMessage(self, text):
        print("📨 sendMessage called with:", text)
        self.messageSent.emit(text)
        self.messageReceived.emit("user", text)
        QTimer.singleShot(100, lambda: self.on_prompt_callback(text))

    def inject_response(self, reply):
        print("📩 inject_response called with:", reply)
        self.responseReceived.emit(reply)
        self.messageReceived.emit("assistant", reply)

    @pyqtSlot()
    def sendVoiceInput(self):
        print("🎙️ Voice input requested (placeholder)")
        text = "[Voice input not implemented]"
        self.sendMessage(text)

    @pyqtSlot()
    def openMemory(self):
        print("🧠 Memory viewer requested (placeholder)")

    @pyqtSlot(bool)
    def set_typing(self, is_typing):
        self.typingSignal.emit(is_typing)
        self.set_assistant_state("typing" if is_typing else "ready")

    @pyqtSlot(str)
    def set_assistant_state(self, state):
        try:
            for window in QGuiApplication.allWindows():
                if window and window.objectName() == "windowRoot":
                    window.setProperty("assistantState", state)
                    print(f"🔄 Assistant state set to: {state}")
                    return
        except Exception as e:
            print(f"⚠️ Could not update assistantState: {e}")

    @pyqtSlot()
    def continueAfterThinking(self):
        if self._continue_function:
            threading.Thread(target=self._continue_function, daemon=True).start()
            self._continue_function = None

    @pyqtProperty(bool, notify=animatedTypingEnabledChanged)
    def animatedTypingEnabled(self):
        from globals_state import animated_typing_enabled
        return animated_typing_enabled

    @animatedTypingEnabled.setter
    def animatedTypingEnabled(self, value):
        from globals_state import animated_typing_enabled
        if value != animated_typing_enabled:
            animated_typing_enabled = value
            self.animatedTypingEnabledChanged.emit()

# ✅ Wiring function to simplify main.py
def setup_qml_bridge(engine):
    def on_user_prompt(prompt):
        threading.Thread(target=process_prompt, args=(prompt,), daemon=True).start()

    qml_bridge = EidolonQMLBridge(on_prompt_callback=on_user_prompt)

    engine.rootContext().setContextProperty("backend", qml_bridge)
    engine.rootContext().setContextProperty("backendReady", True)

    gs.set_qml_bridge(qml_bridge)
    gs.set_gui_instance(qml_bridge)
    gs.set_push_message_func(lambda role, content: qml_bridge.messageReceived.emit(role, content))

    print("✅ QML Bridge fully initialized and injected")
    return qml_bridge
