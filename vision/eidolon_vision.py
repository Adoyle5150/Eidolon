# eidolon_vision.py
import os
import time
import glob
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List, Protocol
from screen_capture import ScreenCapture
from context_interpreter import ContextInterpreter
from eidolon_vision_memory import EidolonVisionMemory
from config import VisionConfig
from PIL import ImageGrab
from protocols import ScreenCaptureProtocol, ContextInterpreterProtocol, EidolonVisionMemoryProtocol

# 💬 Smart dictionary of helper prompts
SMART_RESPONSE_RULES = {
    'vscode': {
        'error': "🚨 I see you're debugging in VSCode — want help?",
        'terminal': "🖥️ You're running terminal commands — want me to explain anything?",
        'coding': "💡 You're coding in VSCode. Want to save progress or get suggestions?"
    },
    'chrome': {
        'stackoverflow': "📘 Looks like you're on StackOverflow — want me to summarize this page?",
        'github': "🐙 You're on GitHub — want to clone or explore this repo?"
    }
}

class EidolonVision:
    def __init__(self):
        self.capture: ScreenCaptureProtocol = ScreenCapture(interval=VisionConfig.CAPTURE_INTERVAL)
        self.interpreter: ContextInterpreterProtocol = ContextInterpreter()
        self.memory: EidolonVisionMemoryProtocol = EidolonVisionMemory()
        self.running = False
        self.analysis_thread = None
        self.current_context: Optional[Dict[str, Any]] = None
        self.context_callbacks: List[Any] = []

    def add_context_callback(self, callback):
        self.context_callbacks.append(callback)

    def start(self):
        if not VisionConfig.VISION_ENABLED:
            print("Vision system disabled in config.")
            return

        self.running = True
        self.capture.start()
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        print("🔮 Eidolon Vision started")

    def stop(self):
        self.running = False
        self.capture.stop()
        print("🛑 Eidolon Vision stopped")

    def _analysis_loop(self):
        while self.running:
            try:
                screenshots = sorted(glob.glob(os.path.join(VisionConfig.SCREENSHOT_FOLDER, "screen_*.png")))
                if screenshots:
                    latest = screenshots[-1]
                    context = self.interpreter.analyze_screenshot(latest)

                    if context:
                        self.memory.remember(context)
                        old_context = self.current_context
                        self.current_context = context

                        if self._context_changed(old_context, context):
                            self._notify_callbacks(context)

                        self._generate_smart_response(context)

            except Exception as e:
                if VisionConfig.DEBUG_MODE:
                    print(f"❌ Vision error: {e}")

            time.sleep(VisionConfig.CAPTURE_INTERVAL)

    def _context_changed(self, old, new):
        if not old:
            return True
        return (old.get('app') != new.get('app') or 
                old.get('window_title') != new.get('window_title') or
                set(old.get('errors', [])) != set(new.get('errors', [])))

    def _notify_callbacks(self, context):
        for callback in self.context_callbacks:
            try:
                callback(context)
            except Exception as e:
                print(f"❌ Callback error: {e}")

    def _generate_smart_response(self, context):
        app = context.get('app')
        tags = context.get('tags', [])

        if not app or not tags:
            return

        rules = SMART_RESPONSE_RULES.get(app, {})
        for tag in tags:
            if tag in rules:
                print(f"🎯 EIDOLON: {rules[tag]}")
                break  # Only say one thing at a time

    def get_current_status(self):
        return {
            'running': self.running,
            'current_context': self.current_context,
            'memory_entries': len(self.memory.memory),
            'recent_contexts': self.memory.get_recent_contexts(5)
        }

    def force_analyze_now(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img = ImageGrab.grab()
            path = os.path.join(VisionConfig.SCREENSHOT_FOLDER, f"manual_{timestamp}.png")
            img.save(path)
            context = self.interpreter.analyze_screenshot(path)
            if context:
                self.memory.remember(context)
                self.current_context = context
                return context
        except Exception as e:
            print(f"❌ Manual analysis error: {e}")
        return None


# === Global instance and access functions ===

eidolon_vision = EidolonVision()

def start_vision():
    eidolon_vision.start()

def stop_vision():
    eidolon_vision.stop()

def get_current_context():
    return eidolon_vision.current_context

def analyze_now():
    return eidolon_vision.force_analyze_now()

def add_vision_callback(cb):
    eidolon_vision.add_context_callback(cb)

def get_vision_status():
    return eidolon_vision.get_current_status()


# === Example Usage ===
if __name__ == "__main__":
    print("🔍 Starting Eidolon Vision test")
    start_vision()
    try:
        while True:
            time.sleep(30)
            status = get_vision_status()
            print(f"📊 Status: {status['memory_entries']} memories stored")
    except KeyboardInterrupt:
        stop_vision()
        print("👋 Goodbye")
