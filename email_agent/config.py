"""
config.py
Gemini API key + Gmail API settings for the Email Agent.

Gemini key (free): https://aistudio.google.com/apikey
Gmail API credentials (free): https://console.cloud.google.com/
  -> Enable "Gmail API" -> Create OAuth Client ID (Desktop app) ->
     download as credentials.json -> place it in this folder.

See README.md for the full step-by-step Gmail setup - it's a one-time
process and completely free for personal use.
"""

import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# Model used for drafting/summarizing emails.
MODEL = "gemini-2.5-flash-lite"

BASE_DIR = os.path.dirname(__file__)

# Path to the OAuth client file you download from Google Cloud Console.
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

# Where the agent stores your login token after first-time authorization,
# so you don't have to log in again every run.
TOKEN_PATH = os.path.join(BASE_DIR, "data", "token.json")

# Gmail API scopes. Using the narrower "gmail.modify" instead of full
# "mail.google.com" - lets the agent read/send/label but not, e.g.,
# permanently delete your whole account's mail.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Whether send_email() actually sends, or just prints what it would send.
# Keep this False until you've tested drafting and are confident - flip
# to True only when you're ready for Orion to send real emails.
LIVE_SEND_ENABLED = False
