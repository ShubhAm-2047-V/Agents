"""
config.py
Configuration settings for the Orion Central Brain & Orchestrator.
"""

import os

# Gemini API Key (reads from environment variable, falls back to common key)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# Model configurations
# Flash-Lite for instant, low-latency zero-cost semantic intent classification
MODEL_ROUTER_FAST = "gemini-2.5-flash-lite"
# Strong model for complex multi-agent orchestration or query decomposition
MODEL_ORCHESTRATOR = "gemini-2.5-flash"

# Routing preferences
ENABLE_AI_FALLBACK = True
FAST_PATH_REGEX_ENABLED = True
LOG_ROUTING_HISTORY = True
MAX_HISTORY_ENTRIES = 100

# UI Colors & Styling
APP_TITLE = "ORION CENTRAL BRAIN"
VERSION = "2.0.0"
