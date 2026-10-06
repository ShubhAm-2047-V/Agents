"""
config.py
Gemini API key + settings for the Reminder/Scheduler Agent.

Get a free key at: https://aistudio.google.com/apikey
"""

import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# OFFLINE_MODE = True allows running 100% offline without API keys or Ollama.
OFFLINE_MODE = os.environ.get("ORION_OFFLINE_MODE", "true").lower() in ("true", "1", "yes")

# Model used for natural language parsing when online.
MODEL = "gemini-2.5-flash-lite"

# How often (seconds) the local checker loop polls for due reminders.
# This is zero-API-cost - it only reads the local SQLite DB.
CHECK_INTERVAL_SECONDS = 30

# Notification method when a reminder fires. Options: "console", "windows_toast"
# "windows_toast" requires: pip install win10toast
NOTIFY_METHOD = "console"
