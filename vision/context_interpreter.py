# vision/context_interpreter.py
import os
import psutil
import platform

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("⚠️ OCR tools not found. Please install pytesseract and pillow.")

class ContextInterpreter:
    def __init__(self):
        pass

    def get_active_window_info(self):
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

    def infer_context(self, ocr_text, window_title):
        tags = []

        if "vscode" in window_title.lower():
            tags.append("vscode")
            if "error" in ocr_text.lower():
                tags.append("vscode_error")
            if "terminal" in ocr_text.lower() or "$" in ocr_text:
                tags.append("vscode_terminal")
        elif "chrome" in window_title.lower() or "browser" in window_title.lower():
            tags.append("browser")
            if "gmail" in ocr_text.lower():
                tags.append("gmail")
        elif "explorer" in window_title.lower():
            tags.append("file_explorer")
        elif "discord" in window_title.lower():
            tags.append("discord")
        elif "whatsapp" in window_title.lower():
            tags.append("whatsapp")

        if not tags:
            tags.append("unknown")

        return tags

    def analyze_context(self, image_path):
        # OCR Pass
        text = ""
        if os.path.exists(image_path):
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)

        window_title = self.get_active_window_info()
        tags = self.infer_context(text, window_title)

        print(f"🪟 Active window: {window_title}")
        print(f"🧠 Inferred context tags: {tags}")
        return {
            "window_title": window_title,
            "tags": tags,
            "ocr_text": text.strip()
        }

# For testing
if __name__ == "__main__":
    ci = ContextInterpreter()
    result = ci.analyze_context("captures/screen_20250627_004437.png")
    print("🧩 Context:", result)
