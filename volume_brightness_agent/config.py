"""
config.py
Configuration and Presets for Orion's Brightness & Volume Control Agent.
"""

import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# OFFLINE_MODE = True allows running 100% offline without API keys or Ollama.
OFFLINE_MODE = os.environ.get("ORION_OFFLINE_MODE", "true").lower() in ("true", "1", "yes")

# Model used for parsing complex natural language commands into structured actions when online.
MODEL = "gemini-2.5-flash-lite"

# Standard step size (%) for volume up/down commands when not specified
DEFAULT_VOLUME_STEP = 10

# Standard step size (%) for brightness up/down commands when not specified
DEFAULT_BRIGHTNESS_STEP = 10

# Maximum volume warning threshold (%)
MAX_SAFE_VOLUME = 100

# App aliases for targeting specific audio processes
APP_ALIASES = {
    "chrome": "chrome.exe",
    "browser": "chrome.exe",
    "spotify": "spotify.exe",
    "music": "spotify.exe",
    "youtube": "chrome.exe",
    "vlc": "vlc.exe",
    "media player": "wmplayer.exe",
    "discord": "discord.exe",
    "game": "game.exe",
    "whatsapp": "whatsapp.exe",
    "telegram": "telegram.exe",
    "antigravity": "antigravity.exe",
    "code": "code.exe"
}

# Atmosphere and environment presets
PRESETS = {
    "movie": {
        "brightness": 30,
        "volume": 75,
        "mute": False,
        "description": "Dim screen and cinematic audio for watching movies/shows"
    },
    "cinema": {
        "brightness": 25,
        "volume": 80,
        "mute": False,
        "description": "Dark theater environment with immersive audio"
    },
    "night": {
        "brightness": 15,
        "volume": 20,
        "mute": False,
        "description": "Ultra-low screen glare and quiet sound for late night"
    },
    "sleep": {
        "brightness": 0,
        "volume": 0,
        "mute": True,
        "description": "Minimal brightness and full silence for sleeping"
    },
    "reading": {
        "brightness": 35,
        "volume": 0,
        "mute": True,
        "description": "Comfortable soft backlight with muted distraction-free audio"
    },
    "study": {
        "brightness": 45,
        "volume": 15,
        "mute": False,
        "description": "Balanced gentle screen with low background study music"
    },
    "focus": {
        "brightness": 55,
        "volume": 30,
        "mute": False,
        "description": "Balanced work productivity lighting and low sound"
    },
    "work": {
        "brightness": 65,
        "volume": 40,
        "mute": False,
        "description": "Crisp daytime brightness for coding and development"
    },
    "gaming": {
        "brightness": 95,
        "volume": 85,
        "mute": False,
        "description": "Maximum visual clarity and high-intensity gaming audio"
    },
    "daylight": {
        "brightness": 100,
        "volume": 80,
        "mute": False,
        "description": "Full brightness to combat direct sun and ambient glare"
    },
    "outdoor": {
        "brightness": 100,
        "volume": 90,
        "mute": False,
        "description": "Maximum brightness and loud volume for outdoors"
    },
    "presentation": {
        "brightness": 100,
        "volume": 65,
        "mute": False,
        "description": "High brightness for external screens/projectors and clear audio"
    },
    "default": {
        "brightness": 60,
        "volume": 50,
        "mute": False,
        "description": "Standard everyday default settings"
    },
    "reset": {
        "brightness": 60,
        "volume": 50,
        "mute": False,
        "description": "Reset brightness to 60% and volume to 50%"
    }
}
