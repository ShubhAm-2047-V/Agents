"""
config.py
Put your Gemini API key here, or better - set it as an environment variable
called GEMINI_API_KEY and leave the fallback below as-is.

Get a free key at: https://aistudio.google.com/apikey
"""

import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# OFFLINE_MODE = True allows running 100% offline without API keys or Ollama.
OFFLINE_MODE = os.environ.get("ORION_OFFLINE_MODE", "true").lower() in ("true", "1", "yes")

# Model used for the "should I remember this?" classification step when online.
# Flash-Lite recommended - higher free-tier RPM, cheap on quota.
CLASSIFIER_MODEL = "gemini-2.5-flash-lite"

# Whether to use semantic (embedding-based) search instead of plain keyword search.
# Keyword search works fully offline with zero API calls - keep this False
# unless you want smarter recall and don't mind the extra API usage.
USE_SEMANTIC_SEARCH = False
