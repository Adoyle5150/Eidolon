import requests

def speak(text):
    try:
        response = requests.post("http://127.0.0.1:5000/speak", json={"text": text})
        if response.ok:
            print("🔊 Eidolon spoke the response.")
        else:
            print(f"❌ TTS server error: {response.text}")
    except Exception as e:
        print(f"❌ Could not connect to TTS server: {e}")
