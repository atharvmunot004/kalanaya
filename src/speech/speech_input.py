import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import tempfile
import os
import threading
import queue

SAMPLE_RATE = 16000  # Whisper prefers 16kHz


def record_audio(duration: int = 5) -> str:
    """
    Records audio from microphone for a fixed duration and saves to a temporary WAV file.
    Returns file path.
    
    Args:
        duration: Recording duration in seconds
        
    Returns:
        Path to the recorded audio file
    """
    print(f"🎙️ Listening for {duration} seconds...")
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.float32
    )
    sd.wait()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    write(tmp_file.name, SAMPLE_RATE, audio)
    return tmp_file.name


def record_audio_until_stop() -> str:
    """
    Records audio from microphone until Enter is pressed.
    Press Enter to start recording, then press Enter again to stop.
    Returns file path.
    
    Returns:
        Path to the recorded audio file
    """
    import time
    
    audio_queue = queue.Queue()
    recording = threading.Event()
    audio_data = []
    
    def audio_callback(indata, frames, time, status):
        """Callback function for audio stream."""
        if status:
            print(f"⚠️  Audio status: {status}")
        if recording.is_set():
            audio_queue.put(indata.copy())
    
    print("🎙️  Press Enter to start recording...")
    input()  # Wait for Enter to start
    
    recording.set()
    print("🔴 Recording... Press Enter to stop.")
    
    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=np.float32,
            callback=audio_callback
        ):
            # Wait for Enter to stop recording
            input()
            recording.clear()
            
            # Give a small delay to ensure all queued audio is processed
            time.sleep(0.1)
            
            # Collect all audio data from queue
            while not audio_queue.empty():
                audio_data.append(audio_queue.get())
            
            print("⏹️  Recording stopped.")
            
    except Exception as e:
        recording.clear()
        raise Exception(f"Error during recording: {str(e)}")
    
    if not audio_data:
        raise Exception("No audio data recorded")
    
    # Concatenate all audio chunks
    audio = np.concatenate(audio_data, axis=0)
    
    # Save to temporary file
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    write(tmp_file.name, SAMPLE_RATE, audio)
    return tmp_file.name
