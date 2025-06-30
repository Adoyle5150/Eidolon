# startup.py
from config import VISION_ENABLED, CAPTURE_INTERVAL, TESSERACT_PATH
from vision.context_interpreter import ContextInterpreter
from vision.eidolon_vision_memory import EidolonVisionMemory
from vision.screen_capture import start_screen_capture
import threading, time, glob
import pytesseract

# Set tesseract path (Windows only)
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def vision_loop():
    ci = ContextInterpreter()
    memory = EidolonVisionMemory()

    while True:
        latest = sorted(glob.glob("captures/*.png"), reverse=True)
        if latest:
            context = ci.analyze_context(latest[0])
            memory.remember(context)
        time.sleep(CAPTURE_INTERVAL)

def start_all_background_services():
    if VISION_ENABLED:
        vision_capture_thread = threading.Thread(
            target=start_screen_capture,
            kwargs={"interval": CAPTURE_INTERVAL},
            daemon=True
        )
        vision_capture_thread.start()

        vision_thread = threading.Thread(target=vision_loop, daemon=True)
        vision_thread.start()
        print("✅ Vision system launched.")


        vision_thread = threading.Thread(target=vision_loop, daemon=True)
        vision_thread.start()
        print("✅ Vision system launched.")
