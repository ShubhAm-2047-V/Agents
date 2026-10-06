"""
config.py
Gemini API key + settings for the System Monitor Agent.

Get a free key at: https://aistudio.google.com/apikey
"""

import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# OFFLINE_MODE = True allows running 100% offline without API keys or Ollama.
OFFLINE_MODE = os.environ.get("ORION_OFFLINE_MODE", "true").lower() in ("true", "1", "yes")

# Model used only for the optional natural-language summary of stats when online.
MODEL = "gemini-2.5-flash-lite"

# Alert thresholds (percent) calibrated for your 16GB / Multi-drive PC.
CPU_ALERT_THRESHOLD = 90
RAM_ALERT_THRESHOLD = 90
DISK_ALERT_THRESHOLD = 95
BATTERY_LOW_THRESHOLD = 20

# How often (seconds) a background monitor loop should poll, if you use one.
# This is a LOCAL, zero-API-cost loop - only reading psutil stats, never
# calling Gemini on every tick (see monitor_loop in system_monitor_agent.py).
POLL_INTERVAL_SECONDS = 30
