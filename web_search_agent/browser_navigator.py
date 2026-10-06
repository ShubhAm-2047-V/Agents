"""
browser_navigator.py
Handles browser navigation, website launching, and direct web portal access for Orion.
Supports commands like:
- 'open instagram on web' / 'open youtube'
- 'visit github.com'
- 'go to reddit'
- 'launch netflix'
"""

import os
import json
import re
import webbrowser
import search_backend

# Quick dictionary of popular web platforms + user's personal website
POPULAR_SITES = {
    "my website": "https://shubh-deep-labs.vercel.app/",
    "my site": "https://shubh-deep-labs.vercel.app/",
    "my own website": "https://shubh-deep-labs.vercel.app/",
    "shubdeep labs": "https://shubh-deep-labs.vercel.app/",
    "shubh deep labs": "https://shubh-deep-labs.vercel.app/",
    "shubdeep": "https://shubh-deep-labs.vercel.app/",
    "instagram": "https://www.instagram.com",
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://www.x.com",
    "x": "https://www.x.com",
    "linkedin": "https://www.linkedin.com",
    "facebook": "https://www.facebook.com",
    "chatgpt": "https://chatgpt.com",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "wikipedia": "https://www.wikipedia.org",
    "whatsapp": "https://web.whatsapp.com",
    "telegram": "https://web.telegram.org",
    "discord": "https://discord.com/app",
    "claude": "https://claude.ai",
    "gemini": "https://gemini.google.com"
}

CUSTOM_SITES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "custom_sites.json")


def _load_custom_sites() -> dict:
    if os.path.exists(CUSTOM_SITES_PATH):
        try:
            with open(CUSTOM_SITES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_custom_site(alias: str, url: str) -> bool:
    """Saves a custom alias and URL persistently."""
    os.makedirs(os.path.dirname(CUSTOM_SITES_PATH), exist_ok=True)
    sites = _load_custom_sites()
    clean_alias = alias.strip().lower()
    sites[clean_alias] = url.strip()
    try:
        with open(CUSTOM_SITES_PATH, "w", encoding="utf-8") as f:
            json.dump(sites, f, indent=2)
        POPULAR_SITES[clean_alias] = url.strip()
        return True
    except Exception:
        return False


# State tracking for previously opened websites
_LAST_OPENED_NAME = "Shubdeep Labs"
_LAST_OPENED_URL = "https://shubh-deep-labs.vercel.app/"


def resolve_url(target: str) -> tuple[str, str]:
    """
    Resolves a website name, domain, or raw URL to a full URL.
    Returns: (display_name, full_url)
    """
    clean = target.strip()
    
    # Strip phrases like 'on web', 'on browser', 'website', 'in browser'
    clean = re.sub(r'\s+(?:on\s+web|on\s+browser|in\s+browser|in\s+web|website|site|page|app)$', '', clean, flags=re.IGNORECASE).strip()
    # Strip leading action words like 'open ', 'visit ', 'launch ', 'go to ', 'goto ', 'to ', 'the '
    clean = re.sub(r'^(?:open\s+|visit\s+|launch\s+|browse\s+to\s+|browse\s+|go\s+to\s+|goto\s+|to\s+|the\s+)', '', clean, flags=re.IGNORECASE).strip()

    lower = clean.lower()

    # 1. Direct match in popular sites dictionary
    if lower in POPULAR_SITES:
        return clean.title(), POPULAR_SITES[lower]

    # 2. Raw URL starting with http:// or https://
    if clean.startswith("http://") or clean.startswith("https://"):
        return clean, clean

    # 3. Domain pattern like 'example.com', 'news.ycombinator.com'
    if re.match(r'^[a-zA-Z0-9\-\.]+\.(com|org|net|io|ai|co|in|edu|gov|dev|app|me|tech|xyz)(\/.*)?$', clean, re.IGNORECASE):
        return clean, f"https://{clean}"

    # 4. Fallback: Search DuckDuckGo for official website
    try:
        results = search_backend.search_web(f"{clean} official website", max_results=3)
        if results and results[0].get("url"):
            return clean.title(), results[0]["url"]
    except Exception:
        pass

    # Generic fallback
    return clean.title(), f"https://www.google.com/search?q={clean}"


def open_website(target: str) -> tuple[bool, str, str]:
    """
    Opens a website or web platform in the default web browser.
    Returns: (success: bool, site_name: str, url: str)
    """
    global _LAST_OPENED_NAME, _LAST_OPENED_URL
    name, url = resolve_url(target)
    try:
        webbrowser.open(url)
        _LAST_OPENED_NAME = name
        _LAST_OPENED_URL = url
        return True, name, url
    except Exception as e:
        return False, name, str(e)


def is_close_command(text: str) -> tuple[bool, str]:
    """
    Detects if a user input is a command to close an opened website, tab, or browser.
    Returns: (is_close: bool, target: str)
    """
    t = text.strip().lower()

    # Direct generic close phrases
    generic_patterns = [
        r'^(?:please\s+)?close\s+(?:it|this|that|website|the\s+website|site|the\s+site|page|the\s+page|tab|the\s+tab|browser|the\s+browser|window|the\s+window)$',
        r'^(?:please\s+)?(?:shut\s+it|shut\s+this|shut\s+down\s+(?:the\s+)?website|exit\s+(?:the\s+)?website|exit\s+(?:the\s+)?browser)$',
        r'^(?:he\s+should\s+|please\s+)?close\s+(?:the\s+)?website$',
        r'^(?:close\s+it|close\s+tab|close\s+browser|close\s+website|shut\s+it|close)$',
        r'^close\s+opened\s+website$'
    ]
    for p in generic_patterns:
        if re.match(p, t):
            return True, "last"

    # Targeted close commands (e.g. 'close instagram', 'close youtube on web')
    m = re.match(r'^(?:please\s+)?(?:close|shut|exit)\s+([a-zA-Z0-9\.\-\_\s]+)$', t)
    if m:
        target = m.group(1).strip()
        # Filter out questions or common non-navigation terms
        non_site_words = (
            "what", "why", "how", "when", "who", "where", "is", "are", "to", "deals",
            "friend", "call", "door", "case", "account", "all pdf", "all pdfs", "pdf", "pdfs"
        )
        if not target.startswith(non_site_words) and len(target.split()) <= 4:
            # Clean up modifiers like 'on web'
            target = re.sub(r'\s+(?:on\s+web|on\s+browser|website|site|app)$', '', target, flags=re.IGNORECASE).strip()
            return True, target

    return False, ""


def close_website(target: str = None) -> tuple[bool, str, str]:
    """
    Closes the opened website tab or browser window.
    Works natively on Windows via user32 / keyboard events.
    Returns: (success: bool, site_name: str, message: str)
    """
    global _LAST_OPENED_NAME, _LAST_OPENED_URL

    site_name = _LAST_OPENED_NAME or "website"
    if target and target != "last":
        site_name = target.title()

    import sys
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            import time

            user32 = ctypes.windll.user32

            # Try to locate window by title matching site_name or popular browsers
            target_keywords = [site_name.lower(), "chrome", "edge", "brave", "firefox", "opera"]
            found_hwnd = None

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
            user32.EnumWindows.restype = wintypes.BOOL

            def enum_proc(hwnd, lparam):
                nonlocal found_hwnd
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        wtitle = buff.value.lower()
                        for kw in target_keywords:
                            if kw in wtitle:
                                found_hwnd = hwnd
                                return False  # Stop enumeration
                return True

            cb = WNDENUMPROC(enum_proc)
            try:
                user32.EnumWindows(cb, 0)
            except Exception:
                pass

            if found_hwnd:
                # Bring target browser window to foreground
                user32.ShowWindow(found_hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(found_hwnd)
                time.sleep(0.1)

            # Send Ctrl+W to close active tab
            VK_CONTROL = 0x11
            VK_W = 0x57
            KEYEVENTF_KEYUP = 0x0002

            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_W, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_W, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

            _LAST_OPENED_NAME = None
            _LAST_OPENED_URL = None
            return True, site_name, f"Closed {site_name} tab in browser."
        except Exception as e:
            return False, site_name, str(e)
    else:
        return True, site_name, f"Close signal sent for {site_name}."

