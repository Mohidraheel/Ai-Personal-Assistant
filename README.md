# Personal Assistant — Setup Guide

A voice-enabled AI assistant for Windows. Talk to it, and it opens apps, searches the web, sets reminders, controls your PC, and more.

---

## Step 1 — Install Python

Download Python 3.10 or newer from https://python.org
During installation, make sure to check "Add Python to PATH"

---

## Step 2 — Install dependencies

Open a terminal in the project folder and run:

```
pip install -r requirements.txt
```

---

## Step 3 — Add your API keys in config.py

Open config.py and replace the placeholder values with your real keys:

```python
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
SERPER_API_KEY = "YOUR_SERPER_API_KEY"
```

### Where to get your keys:

**OpenAI API Key**
- Go to https://platform.openai.com/api-keys
- Sign in or create a free account
- Click "Create new secret key"
- Copy the key (starts with sk-...)
- Paste it as OPENAI_API_KEY

**Serper API Key**
- Go to https://serper.dev
- Sign in or create a free account (2500 free searches)
- Copy your API key from the dashboard
- Paste it as SERPER_API_KEY

### Optional settings in config.py:

**Change the TTS voice:**
```python
TTS_VOICE = "alloy"   # Your options: alloy, echo, fable, onyx, nova, shimmer
```

**Change the language:**
```python
WHISPER_LANGUAGE = "en"   # Change to your language code e.g. "ur" for Urdu
```

---

## Step 4 — Set your app paths in brain/computer.py

Open brain/computer.py and update the paths for the apps you use.
Every app has a path like this:

```python
"steam":   r"C:\Program Files (x86)\Steam\Steam.exe",
"discord": r"C:\Users\{user}\AppData\Local\Discord\Update.exe --processStart Discord.exe",
```

### How to find the correct path for any app:

1. Find the app shortcut on your Desktop or Start Menu
2. Right-click it and select "Properties"
3. Look at the "Target" field — that is the full path
4. Copy it and paste it into computer.py

### Apps you should check and update:

| App | Default path in computer.py | How to verify |
|-----|----------------------------|---------------|
| Steam | C:\Program Files (x86)\Steam\Steam.exe | Right-click Steam → Properties |
| Discord | AppData\Local\Discord\... | Right-click Discord → Properties |
| Spotify | AppData\Roaming\Spotify\Spotify.exe | Right-click Spotify → Properties |
| Chrome | C:\Program Files\Google\Chrome\Application\chrome.exe | Right-click Chrome → Properties |
| VS Code | AppData\Local\Programs\Microsoft VS Code\Code.exe | Right-click VS Code → Properties |
| Telegram | AppData\Roaming\Telegram Desktop\Telegram.exe | Right-click Telegram → Properties |
| WhatsApp | AppData\Local\WhatsApp\WhatsApp.exe | Right-click WhatsApp → Properties |
| VLC | C:\Program Files\VideoLAN\VLC\vlc.exe | Right-click VLC → Properties |
| OBS | C:\Program Files\obs-studio\bin\64bit\obs64.exe | Right-click OBS → Properties |

### Adding a custom app not in the list:

Find the section APP_ALIASES in computer.py and add your app like this:

```python
"your app name": r"C:\Full\Path\To\YourApp.exe",
```

Example — adding Valorant:
```python
"valorant": r"C:\Riot Games\VALORANT\live\VALORANT.exe",
```

After adding it, you can say "Open Valorant" and it will launch.

---

## Step 5 — Run the assistant

```
python main.py
```

---

## How to use it

| Say this | What happens |
|----------|-------------|
| "Open Steam" | Launches Steam |
| "Close Discord" | Closes Discord |
| "Open YouTube" | Opens youtube.com in your browser |
| "Search for latest news" | Searches the web and reads results |
| "Remind me to drink water in 30 minutes" | Sets a reminder |
| "What are my reminders?" | Lists upcoming reminders |
| "Volume up" / "Volume down" | Adjusts system volume |
| "Mute" / "Unmute" | Mutes or unmutes audio |
| "Take a screenshot" | Saves screenshot to Desktop |
| "Lock my PC" | Locks Windows |
| "Shutdown my PC" | Shuts down in 10 seconds |
| "Restart my PC" | Restarts in 10 seconds |

---

## File structure

```
assistant_v2/
├── main.py              — Entry point, run this
├── config.py            — Your API keys and settings (edit this)
├── requirements.txt     — Python packages
├── reminders.json       — Auto-created when you set reminders
├── voice/
│   ├── listener.py      — Mic recording + OpenAI Whisper transcription
│   └── speaker.py       — OpenAI TTS voice output
├── brain/
│   ├── agent.py         — GPT-4o-mini with all tools
│   ├── tools.py         — Web search and reminders
│   └── computer.py      — App launching and PC control (edit paths here)
└── ui/
    └── app.py           — Desktop GUI window
```

---

## Troubleshooting

**App won't open:**
The path in computer.py is wrong. Right-click the app shortcut, go to Properties, copy the Target path and update computer.py.

**Mic not working:**
Run this in terminal to list your audio devices:
```
python -c "import sounddevice; print(sounddevice.query_devices())"
```

**Voice not playing:**
Make sure your OpenAI key is valid and you have credits. TTS uses the tts-1 model which costs very little.

**Web search not working:**
Check your Serper API key in config.py. You can verify it at https://serper.dev

---

## Free tier limits

| Service | Free allowance |
|---------|---------------|
| OpenAI (GPT-4o-mini) | $5 free credits on new accounts |
| OpenAI (Whisper) | Included in $5 credits, ~$0.006 per minute |
| OpenAI (TTS) | Included in $5 credits, ~$0.015 per 1000 characters |
| Serper | 2500 free searches |

For casual personal daily use, the free credits last weeks to months.
