# vision/screen_capture.py

import time
import threading
from typing import Optional
from PIL import ImageGrab
from datetime import datetime
import os

class ScreenCapture:
    def __init__(self, interval: int = 5, save_dir: str = "captures") -> None:
        self.interval: int = interval
        self.save_dir: str = save_dir
        self.running: bool = False
        self.capture_thread: Optional[threading.Thread] = None
        os.makedirs(self.save_dir, exist_ok=True)

    def start(self) -> None:
        """Start the screen capture in a background thread"""
        if not self.running:
            self.running = True
            self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
            self.capture_thread.start()
            print(f"📸 Started screen capture every {self.interval}s...")

    def stop(self) -> None:
        """Stop the screen capture"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1)
        print("🛑 Stopped screen capture.")

    def capture_loop(self) -> None:
        print(f"📸 Starting screen capture every {self.interval}s...")
        try:
            while self.running:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img = ImageGrab.grab()
                path = os.path.join(self.save_dir, f"screen_{timestamp}.png")
                img.save(path)
                print(f"✅ Captured: {path}")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("🛑 Stopped screen capture.")

# ✅ Standalone function for Eidolon system to import
def start_screen_capture(interval: int = 5, save_dir: str = "captures") -> None:
    capture = ScreenCapture(interval=interval, save_dir=save_dir)
    capture.capture_loop()

# For testing only
if __name__ == "__main__":
    cap = ScreenCapture(interval=5)
    cap.capture_loop()
