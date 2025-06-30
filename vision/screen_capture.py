# vision/screen_capture.py

import time
from PIL import ImageGrab
from datetime import datetime
import os

class ScreenCapture:
    def __init__(self, interval=5, save_dir="captures"):
        self.interval = interval
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def capture_loop(self):
        print(f"📸 Starting screen capture every {self.interval}s...")
        try:
            while True:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                img = ImageGrab.grab()
                path = os.path.join(self.save_dir, f"screen_{timestamp}.png")
                img.save(path)
                print(f"✅ Captured: {path}")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("🛑 Stopped screen capture.")

# ✅ Standalone function for Eidolon system to import
def start_screen_capture(interval=5, save_dir="captures"):
    capture = ScreenCapture(interval=interval, save_dir=save_dir)
    capture.capture_loop()

# For testing only
if __name__ == "__main__":
    cap = ScreenCapture(interval=5)
    cap.capture_loop()
