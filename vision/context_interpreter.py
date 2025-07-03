# vision/context_interpreter.py
import os
import psutil
import platform
from typing import Dict, List, Any, Optional

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("⚠️ OCR tools not found. Please install pytesseract and pillow.")

class ContextInterpreter:
    def __init__(self) -> None:
        pass

    def get_active_window_info(self) -> str:
        if platform.system() == "Windows":
            try:
                import win32gui
                window = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(window)
                return title
            except Exception as e:
                return f"❌ Could not get active window: {e}"
        else:
            return "🔒 Unsupported OS for active window tracking"

    def infer_context(self, ocr_text: str, window_title: str) -> List[str]:
        tags: List[str] = []

        if "vscode" in window_title.lower():
            tags.append("vscode")
            if "error" in ocr_text.lower():
                tags.append("error")
            if "terminal" in ocr_text.lower() or "$" in ocr_text:
                tags.append("terminal")
            if any(word in ocr_text.lower() for word in ["function", "class", "def", "import", "return"]):
                tags.append("coding")
        elif "chrome" in window_title.lower() or "browser" in window_title.lower():
            tags.append("chrome")
            if "stackoverflow" in ocr_text.lower():
                tags.append("stackoverflow")
            if "github" in ocr_text.lower():
                tags.append("github")
        elif "explorer" in window_title.lower():
            tags.append("file_explorer")
        elif "discord" in window_title.lower():
            tags.append("discord")
        elif "whatsapp" in window_title.lower():
            tags.append("whatsapp")

        if not tags:
            tags.append("unknown")

        return tags

    def analyze_screenshot(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Analyze a screenshot and return context information"""
        return self.analyze_context(image_path)

    def analyze_context(self, image_path: str) -> Optional[Dict[str, Any]]:
        # OCR Pass
        text = ""
        if os.path.exists(image_path):
            try:
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image)
            except Exception as e:
                print(f"❌ OCR error: {e}")
                text = ""

        window_title = self.get_active_window_info()
        tags = self.infer_context(text, window_title)

        # Determine app from window title
        app = "unknown"
        if "vscode" in window_title.lower():
            app = "vscode"
        elif "chrome" in window_title.lower() or "browser" in window_title.lower():
            app = "chrome"

        print(f"🪟 Active window: {window_title}")
        print(f"🧠 Inferred context tags: {tags}")
        return {
            "app": app,
            "window_title": window_title,
            "tags": tags,
            "ocr_text": text.strip(),
            "errors": []  # Placeholder for error detection
        }

# For testing
if __name__ == "__main__":
    ci = ContextInterpreter()
    result = ci.analyze_context("captures/screen_20250627_004437.png")
    print("🧩 Context:", result)
