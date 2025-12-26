import whisper
import os

# Load once (important)
MODEL_NAME = "base"  # fast + good enough
model = whisper.load_model(MODEL_NAME)

def transcribe(audio_path: str) -> str:
    result = model.transcribe(
        audio_path,
        language="en",
        fp16=False
    )
    text = result["text"].strip()
    return text
