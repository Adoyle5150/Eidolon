from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QTimer, pyqtProperty
from PyQt6.QtGui import QGuiApplication
import threading

from globals_state import animated_typing_enabled, toggle_animated_typing

class EidolonQMLBridge(QObject):
    messageReceived = pyqtSignal(str, str)  # role, content
    typingSignal = pyqtSignal(bool)
    animatedTypingEnabledChanged = pyqtSignal()  # Required for QML bindings

    # ✅ Added signals for your QML Connections
    messageSent = pyqtSignal(str)
    responseReceived = pyqtSignal(str)

    _continue_function = None

    def __init__(self, on_prompt_callback):
        super().__init__()
        self.on_prompt_callback = on_prompt_callback

    @pyqtSlot(str)
    def sendMessage(self, text):
        self.messageSent.emit(text)  # ✅ Emit signal for QML when a message is sent
        self.messageReceived.emit("user", text)
        QTimer.singleShot(200, lambda: self.on_prompt_callback(text))

    def inject_response(self, reply):
        self.responseReceived.emit(reply)  # ✅ Emit signal for QML when a response is received
        self.messageReceived.emit("bot", reply)

    @pyqtSlot()
    def sendVoiceInput(self):
        try:
            from voice_input import listen_and_transcribe
            text = listen_and_transcribe()
        except Exception:
            text = "[Error: Microphone not available]"
        self.messageSent.emit(text)  # ✅ Emit for voice input as well
        self.messageReceived.emit("user", "🎙 " + text)
        self.on_prompt_callback(text)

    @pyqtSlot()
    def openMemory(self):
        print("🧠 Memory viewer triggered from QML")

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
                    print(f"🔄 Setting assistant state: {state}")
                    return
        except Exception as e:
            print(f"⚠️ Could not update assistantState: {e}")

    @pyqtSlot()
    def continueAfterThinking(self):
        if self._continue_function:
            threading.Thread(target=self._continue_function, daemon=True).start()
            self._continue_function = None

    # ✅ Fully bindable animatedTypingEnabled property for QML
    @pyqtProperty(bool, notify=animatedTypingEnabledChanged)
    def animatedTypingEnabled(self):
        return animated_typing_enabled

    @animatedTypingEnabled.setter
    def animatedTypingEnabled(self, value):
        global animated_typing_enabled
        if value != animated_typing_enabled:
            animated_typing_enabled = value
            self.animatedTypingEnabledChanged.emit()
