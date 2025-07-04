# eidolon_qml_bridge.py

from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QTimer
from PyQt6.QtGui import QGuiApplication
import threading
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from eidolon.core.prompt_processor import process_prompt

class EidolonQMLBridge(QObject):
    messageReceived = pyqtSignal(str, str)    # role, content
    typingSignal = pyqtSignal(bool)
    animatedTypingEnabledChanged = pyqtSignal()
    messageSent = pyqtSignal(str)
    responseReceived = pyqtSignal(str)

    _continue_function = None

    def __init__(self, app_context, on_prompt_callback):
        super().__init__()
        self.app_context = app_context
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

    def get_animated_typing_enabled(self) -> bool:
        return self.app_context.animated_typing_enabled

    def set_animated_typing_enabled(self, value: bool) -> None:
        if value != self.app_context.animated_typing_enabled:
            self.app_context.animated_typing_enabled = value
            self.animatedTypingEnabledChanged.emit()

# ✅ Wiring function to simplify main.py
def setup_qml_bridge(engine, app_context):
    def on_user_prompt(prompt):
        threading.Thread(target=process_prompt, args=(prompt, app_context), daemon=True).start()

    qml_bridge = EidolonQMLBridge(app_context, on_prompt_callback=on_user_prompt)

    engine.rootContext().setContextProperty("backend", qml_bridge)
    engine.rootContext().setContextProperty("backendReady", True)


    # Register push_message_func directly
    app_context.push_message_func = lambda role, content: qml_bridge.messageReceived.emit(role, content)
    app_context.gui = qml_bridge

    print("✅ QML Bridge fully initialized and injected")
    return qml_bridge
