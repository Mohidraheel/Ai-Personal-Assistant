import numpy as np
import sounddevice as sd
import tempfile
import wave
import os
from openai import OpenAI
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

def record_until_silence(on_speaking=None, on_silence=None) -> np.ndarray:
    """Record from mic and stop after silence is detected."""
    sample_rate = config.SAMPLE_RATE
    chunk_size = int(sample_rate * 0.1)
    max_chunks = int(config.MAX_RECORDING_SECONDS / 0.1)
    silence_chunks = int(config.SILENCE_DURATION / 0.1)

    audio_chunks = []
    silent_count = 0
    speaking_started = False

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32', blocksize=chunk_size) as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            audio_chunks.append(chunk.copy())
            rms = np.sqrt(np.mean(chunk ** 2))

            if rms > config.SILENCE_THRESHOLD:
                silent_count = 0
                if not speaking_started:
                    speaking_started = True
                    if on_speaking:
                        on_speaking()
            else:
                if speaking_started:
                    silent_count += 1
                    if silent_count >= silence_chunks:
                        if on_silence:
                            on_silence()
                        break

    return np.concatenate(audio_chunks, axis=0).flatten()

def transcribe(audio: np.ndarray) -> str:
    """Send audio to OpenAI Whisper API and return transcribed text."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name

    try:
        with wave.open(tmp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(config.SAMPLE_RATE)
            pcm = (audio * 32767).astype(np.int16)
            wf.writeframes(pcm.tobytes())

        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=config.WHISPER_LANGUAGE
            )
        return result.text.strip()

    except Exception as e:
        print(f"[Whisper Error] {e}")
        return ""
    finally:
        os.unlink(tmp_path)

def listen(on_speaking=None, on_silence=None) -> str:
    """Record from mic and return transcribed text."""
    audio = record_until_silence(on_speaking=on_speaking, on_silence=on_silence)
    if len(audio) < config.SAMPLE_RATE * 0.5:
        return ""
    return transcribe(audio)

def get_model():
    pass  # No local model needed
