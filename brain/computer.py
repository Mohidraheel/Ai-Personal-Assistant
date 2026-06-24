import subprocess
import os
import webbrowser
import platform

# ─── Common Windows App Paths ─────────────────────────────────────────────────
APP_ALIASES = {
    # Games & Launchers
    "steam":        r"D:\Program Files (x86)\steam.exe",
    "epic":         r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
    "discord":      r"C:\Users\pc\AppData\Local\Discord\app-1.0.9242\Discord.exe",
    "minecraft":    r"C:\Program Files (x86)\Minecraft Launcher\MinecraftLauncher.exe",

    # Browsers
    "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":      r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":         r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "copilot":      r"",

    # Microsoft Office
    "word":         r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":   r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",

    # System apps (these work via 'start' command)
    "notepad":      "notepad",
    "calculator":   "calc",
    "paint":        "mspaint",
    "file explorer": "explorer",
    "explorer":     "explorer",
    "task manager": "taskmgr",
    "control panel": "control",
    "settings":     "ms-settings:",
    "camera":       "microsoft.windows.camera:",
    "spotify":      r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "vlc":          r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vscode":       r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "obs":          r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "telegram":     r"C:\Users\{user}\AppData\Roaming\Telegram Desktop\Telegram.exe",
    "whatsapp":     r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
}

def _resolve_path(path: str) -> str:
    user = os.environ.get("USERNAME", "pc")
    return path.replace("{user}", user)

def open_app(app_name: str) -> str:
    """Open an application by name."""
    name = app_name.lower().strip()

    # Check aliases
    for alias, path in APP_ALIASES.items():
        if alias in name or name in alias:
            resolved = _resolve_path(path)

            # ms-settings and similar URI schemes
            if resolved.endswith(":"):
                os.startfile(resolved)
                return f"Opening {app_name}."

            # Simple commands like notepad, calc
            if not resolved.startswith("C:\\") and not resolved.startswith(r"C:\U"):
                subprocess.Popen(resolved, shell=True)
                return f"Opening {app_name}."

            # Full path
            if os.path.exists(resolved):
                subprocess.Popen([resolved])
                return f"Opening {app_name}."
            else:
                # Try via start command as fallback
                subprocess.Popen(f'start "" "{resolved}"', shell=True)
                return f"Trying to open {app_name}."

    # Try directly via Windows start command (works for many apps in PATH)
    try:
        subprocess.Popen(f'start "" "{app_name}"', shell=True)
        return f"Trying to open {app_name}."
    except Exception as e:
        return f"Could not find {app_name}. Make sure it is installed."

def open_website(url: str) -> str:
    """Open a URL in the default browser."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url} in your browser."

def close_app(app_name: str) -> str:
    """Close/kill a running application by process name."""
    process_map = {
        "steam":    "steam.exe",
        "chrome":   "chrome.exe",
        "firefox":  "firefox.exe",
        "edge":     "msedge.exe",
        "discord":  "discord.exe",
        "spotify":  "spotify.exe",
        "notepad":  "notepad.exe",
        "vlc":      "vlc.exe",
        "obs":      "obs64.exe",
        "word":     "WINWORD.EXE",
        "excel":    "EXCEL.EXE",
        "telegram": "telegram.exe",
        "whatsapp": "whatsapp.exe",
    }

    name = app_name.lower().strip()
    process = None
    for key, proc in process_map.items():
        if key in name:
            process = proc
            break

    if not process:
        process = app_name if app_name.endswith(".exe") else app_name + ".exe"

    result = subprocess.run(f"taskkill /F /IM {process}", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return f"Closed {app_name}."
    else:
        return f"Could not close {app_name}. It may not be running."

def system_control(action: str) -> str:
    """Control system power states."""
    action = action.lower().strip()
    if "shutdown" in action or "shut down" in action:
        subprocess.Popen("shutdown /s /t 10", shell=True)
        return "Shutting down your PC in 10 seconds."
    elif "restart" in action or "reboot" in action:
        subprocess.Popen("shutdown /r /t 10", shell=True)
        return "Restarting your PC in 10 seconds."
    elif "sleep" in action or "hibernate" in action:
        subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        return "Putting your PC to sleep."
    elif "lock" in action:
        subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "Locking your PC."
    elif "cancel shutdown" in action or "abort" in action:
        subprocess.Popen("shutdown /a", shell=True)
        return "Shutdown cancelled."
    return "Unknown system action."

def get_volume(action: str, level: int = None) -> str:
    """Control system volume using PowerShell."""
    action = action.lower()
    if "mute" in action:
        script = "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
    elif "unmute" in action:
        script = "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
    elif "up" in action or "increase" in action:
        times = level if level else 5
        script = f"1..{times} | ForEach-Object {{ (New-Object -ComObject WScript.Shell).SendKeys([char]175) }}"
    elif "down" in action or "decrease" in action:
        times = level if level else 5
        script = f"1..{times} | ForEach-Object {{ (New-Object -ComObject WScript.Shell).SendKeys([char]174) }}"
    else:
        return "Unknown volume action."

    subprocess.Popen(["powershell", "-Command", script])
    return f"Volume {action}."

def take_screenshot() -> str:
    """Take a screenshot and save to Desktop."""
    script = """
    Add-Type -AssemblyName System.Windows.Forms
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
    $path = "$env:USERPROFILE\\Desktop\\screenshot_$(Get-Date -Format 'yyyyMMdd_HHmmss').png"
    $bitmap.Save($path)
    Write-Output $path
    """
    result = subprocess.run(["powershell", "-Command", script], capture_output=True, text=True)
    path = result.stdout.strip()
    if path:
        return f"Screenshot saved to your Desktop."
    return "Could not take screenshot."
