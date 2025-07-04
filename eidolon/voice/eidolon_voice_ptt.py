import os
import sys
import keyboard
import speech_recognition as sr
from eidolon.core.app_context import AppContext

# Dynamically add the project root to sys.path for importing process_prompt from main.py
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.append(project_root)
from main import process_prompt

recognizer = sr.Recognizer()
mic = sr.Microphone()

def listen_and_process():
    with mic as source:
        print("🎤 F10 pressed: Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)  # type: ignore
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)  # type: ignore
        print(f"🗣️ You said: {text}")
        app_context = AppContext()
        process_prompt(text, app_context)
    except sr.UnknownValueError:
        print("❌ Could not understand audio.")
    except sr.RequestError as e:
        print(f"❌ API error: {e}")

def main():
    print("🔴 Press F10 to speak. Press ESC to exit.")
    keyboard.add_hotkey('F10', listen_and_process)
    keyboard.wait('esc')
    print("🛑 Exiting PTT listener.")

if __name__ == "__main__":
    main()
