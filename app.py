from flask import Flask, request, jsonify, send_file
from piper import PiperVoice
from pydub import AudioSegment
import wave
import os

app = Flask(__name__)

# Load your model
voice = PiperVoice.load(
    model_path="en_US-hfc_female-medium.onnx",
    config_path="en_US-hfc_female-medium.onnx.json",
)

# Temporary file paths
output_wav_file = "output.wav"
output_mp3_file = "output.mp3"


@app.route("/synthesize", methods=["POST"])
def synthesize():
    try:
        # Get input text and speed from the request
        data = request.json
        text = data.get("text", "").strip()
        speed = data.get("speed", 1.0)  # Default speed is 1.0 (normal speed)

        if not text:
            return jsonify({"error": "Text input is required"}), 400

        if not (0.5 <= speed <= 2.0):  # Limit speed to a reasonable range
            return jsonify({"error": "Speed must be between 0.5 and 2.0"}), 400

        # Generate WAV file
        with wave.open(output_wav_file, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes (16-bit)
            wav_file.setframerate(voice.config.sample_rate)  # Use default sample rate
            voice.synthesize(text, wav_file)

        # Adjust speed using pydub
        audio_segment = AudioSegment.from_wav(output_wav_file)
        new_frame_rate = int(audio_segment.frame_rate * speed)
        audio_segment = audio_segment._spawn(
            audio_segment.raw_data, overrides={"frame_rate": new_frame_rate}
        )
        audio_segment = audio_segment.set_frame_rate(voice.config.sample_rate)

        # Export adjusted audio to MP3
        audio_segment.export(output_mp3_file, format="mp3")

        # Return the MP3 file as a response
        return send_file(output_mp3_file, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary files
        if os.path.exists(output_wav_file):
            os.remove(output_wav_file)
        if os.path.exists(output_mp3_file):
            os.remove(output_mp3_file)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
