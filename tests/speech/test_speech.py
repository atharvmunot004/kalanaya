import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.speech import record_audio, transcribe
import os

if __name__ == "__main__":
    audio_file = record_audio(duration=6)
    try:
        text = transcribe(audio_file)
        print("🧠 Transcribed text:")
        print(text)
    finally:
        os.remove(audio_file)
