"""
config.py
Gemini API key + settings for the Web Search Agent.

Get a free key at: https://aistudio.google.com/apikey
"""

import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# Model used for summarizing search results.
MODEL = "gemini-2.5-flash"

# Search backend. "duckduckgo" is free and needs no API key at all.
# Options: "duckduckgo"
SEARCH_BACKEND = "duckduckgo"

# How many search results to fetch and feed to Gemini for summarization.
MAX_RESULTS = 5

# Timeout (seconds) for web requests.
REQUEST_TIMEOUT = 10

# Max characters of page content to pull per result before summarizing -
# keeps prompts small and fast.
MAX_CONTENT_CHARS = 3000

# Output directory for exported files (PDFs, HTML, CSV, screenshots, QR codes)
EXPORT_DIR = "exports"

# Automatically open generated PDF or HTML files in the default viewer
AUTO_OPEN_EXPORTS = True

# Voice output (spoken audio briefings) - toggleable via 'voice on' / 'voice off'
VOICE_ENABLED = False

