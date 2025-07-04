import pvporcupine
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import sys
import os
import threading
from eidolon.voice import voice_controller

# ✅ Add Eidolon root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

recognizer = sr.Recognizer()
mic = sr.Microphone()

def listen_and_process(app_context, process_prompt_func, persistent=False):
    while True if not persistent else voice_controller.is_hands_free_active():
        with mic as source:
            if persistent:
                print("🎤 Listening for command (hands-free mode)...")
            else:
                print("🎤 Wake word detected. Listening for command...")
            recognizer.adjust_for_ambient_noise(source, duration=0.3)  # type: ignore
            audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)  # type: ignore
            print(f"🗣️ You said: {text}")
            process_prompt_func(text, app_context)
            if not persistent:
                break  # Only listen once if not persistent
        except sr.UnknownValueError:
            print("❌ Could not understand audio.")
            if not persistent:
                break
        except sr.RequestError as e:
            print(f"❌ API error: {e}")
            if not persistent:
                break

def start_wake_word_listener(app_context, process_prompt_func):
    print("🎤 Using pvporcupine for wake word detection with custom 'Eidolon' keyword.")
    try:
        ACCESS_KEY = "gfeb6xRp4KneyQRGk+JgdXjcOiYXADOOU9hSlvzNzFqnxajehBllvA=="
        # ✅ Use your custom 'Eidolon' wake word file
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=["E:/Eidolon/eidolon/voice/Eidolon_en_windows_v3_0_0.ppn"]
        )
    except Exception as e:
        print(f"❌ Failed to initialize Porcupine: {e}")
        return

    def callback(indata, frames, time, status):
        pcm = np.frombuffer(indata, dtype=np.int16).tolist()
        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("✅ Wake word 'Eidolon' detected! Entering hands-free mode.")
            voice_controller.start_hands_free()
            listen_and_process(app_context, process_prompt_func, persistent=True)
            print("🔴 Say 'Eidolon' again to re-enter hands-free mode.")

    def run_listener():
        with sd.RawInputStream(samplerate=porcupine.sample_rate,
                               blocksize=porcupine.frame_length,
                               dtype='int16',
                               channels=1,
                               callback=callback):
            print("🔴 Say 'Eidolon' to trigger hands-free mode (Ctrl+C to exit).")
            try:
                while True:
                    sd.sleep(100)
            except KeyboardInterrupt:
                print("🛑 Stopping wake word listener.")
            finally:
                porcupine.delete()

    t = threading.Thread(target=run_listener, daemon=True)
    t.start()
