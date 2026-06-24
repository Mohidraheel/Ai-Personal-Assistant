import json
import os
from datetime import datetime, date
from openai import OpenAI
import config
from brain.tools import web_search

client = OpenAI(api_key=config.OPENAI_API_KEY)

PREFS_FILE = "brief_prefs.json"
BRIEF_LOG  = "brief_log.json"

def get_preferences() -> dict:
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_preferences(topics: list, language: str = "en"):
    prefs = {
        "topics": topics,
        "language": language,
        "saved_at": datetime.now().isoformat()
    }
    with open(PREFS_FILE, "w") as f:
        json.dump(prefs, f, indent=2)

def has_preferences() -> bool:
    return bool(get_preferences().get("topics"))

def update_topics(topics: list):
    prefs = get_preferences()
    prefs["topics"] = topics
    prefs["saved_at"] = datetime.now().isoformat()
    with open(PREFS_FILE, "w") as f:
        json.dump(prefs, f, indent=2)

def already_shown_today() -> bool:
    if not os.path.exists(BRIEF_LOG):
        return False
    try:
        with open(BRIEF_LOG, "r") as f:
            log = json.load(f)
        return log.get("last_date") == str(date.today())
    except Exception:
        return False

def mark_shown_today():
    with open(BRIEF_LOG, "w") as f:
        json.dump({"last_date": str(date.today())}, f)

def fetch_news_for_topics(topics: list) -> dict:
    results = {}
    for topic in topics:
        query = f"latest news {topic} today 2025"
        results[topic] = web_search(query)
    return results

def generate_brief(topics: list, lang: str = "en") -> str:
    raw_news = fetch_news_for_topics(topics)

    news_context = ""
    for topic, content in raw_news.items():
        news_context += f"\n\n--- {topic.upper()} ---\n{content}"

    prompt = f"""You are a morning news assistant. Based on the news below, create a TLDR morning brief.

Format it like this:
- Start with a warm good morning greeting
- Cover each topic in 2-3 sentences max, TLDR style
- End with one motivational line
- Keep total length under 200 words — it will be read aloud
- Be conversational, not formal. Like a friend telling you the news.

Today's date: {date.today().strftime("%B %d, %Y")}
Topics requested: {", ".join(topics)}

NEWS DATA:
{news_context}

Write the morning brief now:"""

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def extract_topics_from_message(user_message: str) -> list:
    prompt = f"""Extract news topics from this message as a JSON array.
User said: "{user_message}"
Return ONLY a JSON array like: ["AI news", "cricket", "crypto"]
Keep each topic short. No explanation, just the array."""

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return [t.strip() for t in user_message.split(",") if t.strip()]