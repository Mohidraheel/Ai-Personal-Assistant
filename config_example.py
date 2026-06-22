import os

# ─── API Keys ─────────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# ─── OpenAI Settings ──────────────────────────────────────────────────────────
OPENAI_MODEL      = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 1024
OPENAI_SYSTEM_PROMPT = """You are a helpful voice assistant running on the user's Windows PC.
Keep responses concise and conversational — they will be spoken aloud via text-to-speech.
Avoid markdown formatting, bullet points, or long lists. Speak naturally.
You can open and close apps, open websites, control volume, take screenshots, shutdown or restart the PC.
When the user says 'open X', always use the open_app tool.
When the user says 'go to X.com' or 'open youtube', use open_website tool.
When you search the web, summarize findings in 2-3 sentences max.
When setting reminders, confirm what the reminder is and when it will trigger."""

# ─── OpenAI TTS Settings ──────────────────────────────────────────────────────
TTS_MODEL = "tts-1"
TTS_VOICE = "alloy"   # alloy | echo | fable | onyx | nova | shimmer

# ─── OpenAI Whisper Settings ──────────────────────────────────────────────────
WHISPER_LANGUAGE = "en"

# ─── Reminder Storage ─────────────────────────────────────────────────────────
REMINDERS_FILE = "reminders.json"

# ─── App Settings ─────────────────────────────────────────────────────────────
APP_NAME              = "Personal Assistant"
APP_VERSION           = "2.0.0"
SILENCE_THRESHOLD     = 0.01
SILENCE_DURATION      = 1.5
MAX_RECORDING_SECONDS = 30
SAMPLE_RATE           = 16000
