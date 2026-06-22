from openai import OpenAI
import json
import config
from brain import tools as tool_module
from brain import computer

client = OpenAI(api_key=config.OPENAI_API_KEY)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information, news, or facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set a reminder at a specific time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "time": {"type": "string", "description": "e.g. 'in 10 minutes', '3:00 PM'"}
                },
                "required": ["message", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_reminders",
            "description": "Get upcoming reminders.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open an application on the user's PC. Use when user says 'open', 'launch', 'start' followed by an app name like Steam, Chrome, Discord, Spotify, Notepad, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app to open e.g. 'Steam', 'Chrome', 'Discord'"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_app",
            "description": "Close or quit a running application. Use when user says 'close', 'quit', 'kill' an app.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app to close"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Open a website in the browser. Use when user says 'open', 'go to', 'visit' a website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL e.g. 'youtube.com', 'google.com'"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "system_control",
            "description": "Control PC power: shutdown, restart, sleep, lock, or cancel shutdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: shutdown, restart, sleep, lock, cancel shutdown"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "volume_control",
            "description": "Control system volume: increase, decrease, mute, or unmute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "up, down, mute, unmute"},
                    "level": {"type": "integer", "description": "How many steps to change (optional, default 5)"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot and save it to the Desktop.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

def _execute_tool(name: str, arguments: dict) -> str:
    if name == "web_search":
        return tool_module.web_search(arguments["query"])
    elif name == "set_reminder":
        return tool_module.set_reminder(arguments["message"], arguments["time"])
    elif name == "get_reminders":
        return tool_module.get_reminders()
    elif name == "open_app":
        return computer.open_app(arguments["app_name"])
    elif name == "close_app":
        return computer.close_app(arguments["app_name"])
    elif name == "open_website":
        return computer.open_website(arguments["url"])
    elif name == "system_control":
        return computer.system_control(arguments["action"])
    elif name == "volume_control":
        return computer.get_volume(arguments["action"], arguments.get("level"))
    elif name == "take_screenshot":
        return computer.take_screenshot()
    return "Unknown tool."

class Agent:
    def __init__(self):
        self.history = [{"role": "system", "content": config.OPENAI_SYSTEM_PROMPT}]

    def clear_history(self):
        self.history = [{"role": "system", "content": config.OPENAI_SYSTEM_PROMPT}]

    def chat(self, user_message: str, on_tool_call=None) -> str:
        self.history.append({"role": "user", "content": user_message})

        while True:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                max_tokens=config.OPENAI_MAX_TOKENS,
                tools=TOOLS,
                messages=self.history
            )

            msg = response.choices[0].message
            self.history.append(msg)

            if msg.tool_calls:
                for call in msg.tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments)
                    if on_tool_call:
                        on_tool_call(name, args)
                    result = _execute_tool(name, args)
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result
                    })
            else:
                return (msg.content or "").strip()
