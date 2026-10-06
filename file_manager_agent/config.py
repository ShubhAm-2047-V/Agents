"""
config.py
Gemini API key + settings for the File Manager Agent.

Get a free key at: https://aistudio.google.com/apikey
"""

import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_YOUR_GEMINI_API_KEY_HERE")

# OFFLINE_MODE = True allows running 100% offline without API keys or Ollama.
OFFLINE_MODE = os.environ.get("ORION_OFFLINE_MODE", "true").lower() in ("true", "1", "yes")

# Model used for summarizing file contents and interpreting natural language commands when online.
MODEL = "gemini-2.5-flash-lite"

# Default root folder this agent is allowed to operate in.
# Default to current workspace directory (E:\Agent's)
DEFAULT_ROOT = os.environ.get("ORION_FILES_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _get_shell_folder(reg_value: str, default_subfolder: str) -> str:
    """Retrieve actual Windows Shell folder location (supports OneDrive redirection)."""
    fallback = os.path.join(os.path.expanduser("~"), default_subfolder)
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
                val, _ = winreg.QueryValueEx(k, reg_value)
                expanded = os.path.expandvars(val)
                if os.path.exists(expanded):
                    return expanded
        except Exception:
            pass
    return fallback



# Common standard user folders on Windows (OneDrive & local aware)
DESKTOP_DIR = _get_shell_folder("Desktop", "Desktop")
DOWNLOADS_DIR = _get_shell_folder("{374DE290-123F-4565-9164-39C4925E467B}", "Downloads")
DOCUMENTS_DIR = _get_shell_folder("Personal", "Documents")
PICTURES_DIR = _get_shell_folder("My Pictures", "Pictures")



# Directories to skip for high-speed scanning
IGNORE_DIRS = {
    ".git", ".github", "node_modules", "__pycache__", "appdata",
    ".gemini", ".cursor", ".venv", "venv", "env", "$recycle.bin"
}


# Max file size (bytes) to read for summarization - avoids choking on huge files.
MAX_READ_SIZE = 500_000

# File categories for smart cleaner & organizer
SMART_CATEGORIES = {
    "Documents": [".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".txt", ".rtf", ".odt", ".csv", ".tsv"],
    "Images": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico", ".tiff", ".raw"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".java", ".c", ".cpp", ".cs", ".go", ".rs", ".php", ".sh", ".bat", ".yaml", ".yml", ".sql"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    "Media": [".mp4", ".mkv", ".mov", ".avi", ".flv", ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Installers": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".apk"]
}

# File extensions considered "readable text" for summarization.
TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".json", ".csv", ".log",
    ".html", ".css", ".java", ".c", ".cpp", ".yaml", ".yml", ".xml", ".sql"
}

