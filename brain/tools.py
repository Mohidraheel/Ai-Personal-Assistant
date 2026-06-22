import requests
import json
import os
import threading
import time
from datetime import datetime, timedelta
import re
import config

# ─── Web Search ───────────────────────────────────────────────────────────────

def web_search(query: str) -> str:
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": config.SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        resp = requests.post(url, json={"q": query, "num": 5}, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        if "answerBox" in data:
            answer = data["answerBox"].get("answer") or data["answerBox"].get("snippet", "")
            if answer:
                results.append(f"Direct answer: {answer}")

        for r in data.get("organic", [])[:3]:
            snippet = r.get("snippet", "")
            title = r.get("title", "")
            if snippet:
                results.append(f"{title}: {snippet}")

        return "\n\n".join(results) if results else "No results found."

    except Exception as e:
        return f"Search failed: {str(e)}"


# ─── Reminders ────────────────────────────────────────────────────────────────

_reminders = []
_reminder_callbacks = []

def _load_reminders():
    global _reminders
    if os.path.exists(config.REMINDERS_FILE):
        try:
            with open(config.REMINDERS_FILE, "r") as f:
                _reminders = json.load(f)
        except Exception:
            _reminders = []

def _save_reminders():
    with open(config.REMINDERS_FILE, "w") as f:
        json.dump(_reminders, f, indent=2)

def _parse_time(time_str: str) -> datetime:
    now = datetime.now()
    time_str = time_str.lower().strip()

    m = re.search(r'in\s+(\d+)\s+(minute|hour|second)', time_str)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        if "minute" in unit:
            return now + timedelta(minutes=amount)
        elif "hour" in unit:
            return now + timedelta(hours=amount)
        elif "second" in unit:
            return now + timedelta(seconds=amount)

    m = re.search(r'(\d+)\s+(minute|hour)', time_str)
    if m:
        amount = int(m.group(1))
        unit = m.group(2)
        if "minute" in unit:
            return now + timedelta(minutes=amount)
        elif "hour" in unit:
            return now + timedelta(hours=amount)

    for fmt in ["%I:%M %p", "%H:%M", "%I %p"]:
        try:
            t = datetime.strptime(time_str, fmt)
            target = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return target
        except ValueError:
            continue

    return now + timedelta(minutes=5)

def set_reminder(message: str, time_str: str) -> str:
    _load_reminders()
    trigger_time = _parse_time(time_str)
    reminder = {
        "id": int(time.time() * 1000),
        "message": message,
        "trigger_time": trigger_time.isoformat(),
        "done": False
    }
    _reminders.append(reminder)
    _save_reminders()
    return f"Reminder set for {trigger_time.strftime('%I:%M %p')}: {message}"

def get_reminders() -> str:
    _load_reminders()
    upcoming = [r for r in _reminders if not r["done"]]
    if not upcoming:
        return "You have no upcoming reminders."
    lines = [f"• {datetime.fromisoformat(r['trigger_time']).strftime('%I:%M %p')} — {r['message']}" for r in upcoming]
    return "Upcoming reminders:\n" + "\n".join(lines)

def register_reminder_callback(cb):
    _reminder_callbacks.append(cb)

def _reminder_loop():
    _load_reminders()
    while True:
        now = datetime.now()
        changed = False
        for r in _reminders:
            if not r["done"] and now >= datetime.fromisoformat(r["trigger_time"]):
                r["done"] = True
                changed = True
                for cb in _reminder_callbacks:
                    try:
                        cb(r["message"])
                    except Exception:
                        pass
        if changed:
            _save_reminders()
        time.sleep(15)

threading.Thread(target=_reminder_loop, daemon=True).start()
