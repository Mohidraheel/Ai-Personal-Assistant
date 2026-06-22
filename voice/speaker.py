import io
import threading
import pygame
from openai import OpenAI
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

_speaking = False
_lock = threading.Lock()

def speak(text: str, on_start=None, on_done=None):
    """Convert text to speech via OpenAI TTS and play it."""
    global _speaking

    def _run():
        global _speaking
        with _lock:
            _speaking = True
            if on_start:
                on_start()

            try:
                response = client.audio.speech.create(
                    model=config.TTS_MODEL,
                    voice=config.TTS_VOICE,
                    input=text,
                    response_format="mp3"
                )
                audio_file = io.BytesIO(response.content)
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.wait(50)

            except Exception as e:
                print(f"[TTS Error] {e}")
            finally:
                _speaking = False
                if on_done:
                    on_done()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread

def stop():
    pygame.mixer.music.stop()

def is_speaking() -> bool:
    return _speaking
