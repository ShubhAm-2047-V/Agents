"""
history_manager.py
Manages search history, bookmarks, and file launching for Orion Web Search Agent.
"""

import os
import json
import subprocess
import sys
from datetime import datetime

DATA_DIR = os.path.join(os.getcwd(), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
BOOKMARKS_FILE = os.path.join(DATA_DIR, "bookmarks.json")


def _ensure_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    if not os.path.exists(BOOKMARKS_FILE):
        with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def add_history_entry(query_type: str, query: str, summary: str = "", pdf_path: str = None, html_path: str = None):
    """Adds a completed query entry into history."""
    _ensure_files()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": query_type,
            "query": query,
            "summary": summary[:200] if summary else "",
            "pdf_path": pdf_path,
            "html_path": html_path
        }
        history.insert(0, entry)
        # Keep last 100 entries
        history = history[:100]

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass


def get_history(limit: int = 10) -> list:
    """Returns the most recent search history entries."""
    _ensure_files()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)[:limit]
    except Exception:
        return []


def add_bookmark(title: str, query: str, content: str = ""):
    """Saves a research bookmark."""
    _ensure_files()
    try:
        with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
            bookmarks = json.load(f)

        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "title": title,
            "query": query,
            "snippet": content[:250]
        }
        bookmarks.insert(0, entry)
        with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
            json.dump(bookmarks, f, indent=2)
        return True
    except Exception:
        return False


def get_bookmarks() -> list:
    """Returns saved bookmarks."""
    _ensure_files()
    try:
        with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def open_file(filepath: str):
    """Opens a generated PDF or HTML report in the user's default system viewer."""
    if not filepath or not os.path.exists(filepath):
        return
    try:
        if sys.platform == "win32":
            os.startfile(filepath)
        elif sys.platform == "darwin":
            subprocess.run(["open", filepath], check=False)
        else:
            subprocess.run(["xdg-open", filepath], check=False)
    except Exception:
        pass
