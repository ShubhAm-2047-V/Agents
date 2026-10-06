"""
config.py
Gemini API key + settings for the Code Assistant Agent.

Get a free key at: https://aistudio.google.com/apikey
"""

import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# Model for code generation/explanation/debugging.
# Flash-Lite = cheaper/faster, good for quick snippets and simple debugging.
# Flash = better reasoning, worth it for trickier bugs or longer code.
MODEL_FAST = "gemini-2.5-flash-lite"
MODEL_STRONG = "gemini-2.5-flash"

# Max characters of code to send in one prompt - keeps requests fast and
# within free-tier token comfort zone. Large files get truncated with a
# clear note rather than silently cut.
MAX_CODE_CHARS = 12000

# Default language preferences for Shubham's stack
DEFAULT_LANGUAGE = "python"
PREFERRED_LANGUAGES = ["python", "javascript", "react", "nodejs", "express", "flask", "java", "c", "cpp", "sql"]

# Whether to run generated/fixed code automatically after producing it.
# Keep this False by default - executing AI-generated code without review
# is risky. Only your router/user should decide to run something.
AUTO_EXECUTE = False
