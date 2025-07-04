from flask import Flask, request, jsonify
from TTS.api import TTS
import os

app = Flask(__name__)

# Load Coqui TTS model (female, English)
tts = TTS(model_name="tts_models/en/jenny/jenny", progress_bar=False)
tts.to('cuda')


@app.route("/speak", methods=["POST"])
def speak():
    data = request.json
    text = data.get("text", "")
    if not text:
        return jsonify({"status": "error", "message": "No text provided"}), 400

    print(f"🗣️ Speaking: {text}")

    tts.tts_to_file(text=text, file_path="tts_output.wav")
    os.system("start tts_output.wav")  # Windows-only playback

    return jsonify({"status": "success", "message": "Speech played"})

if __name__ == "__main__":
    app.run(port=5000)

