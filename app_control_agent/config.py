"""
config.py
Gemini API key + settings for the App Control Agent.

Get a free key at: https://aistudio.google.com/apikey
"""

import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# OFFLINE_MODE = True allows running 100% offline without API keys or Ollama.
OFFLINE_MODE = os.environ.get("ORION_OFFLINE_MODE", "true").lower() in ("true", "1", "yes")

# When True, searches the app in Windows Search and hits Enter (supports all Store/installed apps).
USE_WINDOWS_SEARCH_LAUNCHER = True

# Model used for parsing natural language commands into structured actions when online.
MODEL = "gemini-2.5-flash-lite"

# Map friendly names -> actual executable / process names / hotkeys on Windows.
# Keys should be lowercase.
APP_ALIASES = {
    # Primary Browser (Profile 1)
    "chrome": r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 1"',
    "browser": r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 1"',
    "my browser": r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 1"',
    
    # Primary Code Editor: Antigravity
    "antigravity": "Antigravity",
    "editor": "Antigravity",
    "code editor": "Antigravity",
    "ide": "Antigravity",
    "code": "Antigravity",
    "vscode": "Code.exe",
    "vs code": "Code.exe",

    # Terminal: Cmd
    "cmd": "cmd.exe",
    "terminal": "cmd.exe",
    "command prompt": "cmd.exe",
    "prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "git bash": "git-bash.exe",

    # Top Daily Apps
    "whatsapp": "whatsapp",
    "youtube": "hotkey:ctrl+alt+x",
    "you": "hotkey:ctrl+alt+x",
    "you tube": "hotkey:ctrl+alt+x",
    
    # File Explorer
    "file explorer": r"C:\Windows\explorer.exe",
    "file": r"C:\Windows\explorer.exe",
    "files": r"C:\Windows\explorer.exe",
    "explorer": r"C:\Windows\explorer.exe",

    # ChatGPT (Hotkey Ctrl+Alt+A)
    "chatgpt": "hotkey:ctrl+alt+a",
    "gpt": "hotkey:ctrl+alt+a",
    "chat": "hotkey:ctrl+alt+a",
    "chat gpt": "hotkey:ctrl+alt+a",
    "ai": "hotkey:ctrl+alt+a",

    # Work Routine (Hotkey Ctrl+Alt+S)
    "back to work": "hotkey:ctrl+alt+s",
    "work mode": "hotkey:ctrl+alt+s",

    # Other common tools
    "postman": "Postman.exe",
    "spotify": "Spotify.exe",
    "calculator": "calc.exe",
    "notepad": "notepad.exe",
    "task manager": "Taskmgr.exe",
    "discord": "Discord.exe",
}

# Apps that should never be closed by this agent, even if asked -
# closing these can be disruptive or system-critical.
PROTECTED_PROCESSES = {
    "explorer.exe",
    "csrss.exe",
    "winlogon.exe",
    "services.exe",
    "svchost.exe",
    "system",
    "smss.exe",
    "lsass.exe",
    "antigravity.exe",
    "antigravity ide.exe",
}

