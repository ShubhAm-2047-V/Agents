"""
browser_media_controller.py
Provides smart browser actions, media playback, YouTube transcript summarization,
webpage screenshots, and browser keyboard controls.
"""

import os
import re
import sys
import time
import subprocess
import webbrowser
import requests

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

import config
import search_backend

try:
    from google import genai
except ImportError:
    genai = None


def _get_client():
    if genai and config.GEMINI_API_KEY and config.GEMINI_API_KEY != "PASTE_YOUR_GEMINI_API_KEY_HERE":
        return genai.Client(api_key=config.GEMINI_API_KEY)
    return None


def extract_youtube_id(url_or_text: str) -> str | None:
    """Extracts YouTube video ID from various URL formats."""
    patterns = [
        r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/watch\?v=|\&v=)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for p in patterns:
        m = re.search(p, url_or_text)
        if m:
            return m.group(1)
    return None


def play_media(query: str, platform: str = "youtube") -> tuple[bool, str, str]:
    """
    Searches YouTube or Spotify and opens the best matching media in the default browser.
    Returns: (success: bool, title: str, url: str)
    """
    clean_q = re.sub(r'^(?:play\s+|listen\s+to\s+|watch\s+)', '', query, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r'\s+(?:on\s+youtube|on\s+spotify|on\s+web)$', '', clean_q, flags=re.IGNORECASE).strip()

    if "spotify" in platform.lower() or "spotify" in query.lower():
        url = f"https://open.spotify.com/search/{requests.utils.quote(clean_q)}"
        webbrowser.open(url)
        return True, f"Spotify Search: {clean_q.title()}", url

    # Default to YouTube: Find top video
    search_term = f"{clean_q} site:youtube.com/watch"
    results = search_backend.search_web(search_term, max_results=3)

    target_url = None
    target_title = clean_q.title()

    for r in results:
        vid_id = extract_youtube_id(r.get("url", ""))
        if vid_id:
            target_url = f"https://www.youtube.com/watch?v={vid_id}"
            target_title = r.get("title", clean_q.title())
            break

    if not target_url:
        target_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(clean_q)}"

    webbrowser.open(target_url)
    return True, target_title, target_url


def summarize_youtube_video(url_or_query: str) -> str:
    """
    Extracts transcript from a YouTube video and generates a concise AI summary with key takeaways.
    """
    vid_id = extract_youtube_id(url_or_query)
    
    if not vid_id:
        # Try finding video from query
        results = search_backend.search_web(f"{url_or_query} site:youtube.com/watch", max_results=2)
        for r in results:
            vid_id = extract_youtube_id(r.get("url", ""))
            if vid_id:
                break

    if not vid_id:
        return f"⚠️ Could not identify a valid YouTube video ID from '{url_or_query}'."

    video_url = f"https://www.youtube.com/watch?v={vid_id}"

    # Fetch Transcript
    transcript_text = ""
    if YouTubeTranscriptApi:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(vid_id)
            transcript_text = " ".join(item.get("text", "") for item in transcript_list)
        except Exception as e:
            transcript_text = ""

    if not transcript_text:
        # Fallback: Scrape page text or description
        page_text = search_backend.fetch_page_text(video_url)
        if page_text:
            transcript_text = page_text[:4000]

    if not transcript_text:
        return f"⚠️ Could not retrieve transcripts or captions for video {video_url} (Captions may be disabled)."

    client = _get_client()
    if not client:
        return f"📋 Video Transcript Preview ({len(transcript_text)} chars):\n\n{transcript_text[:1200]}..."

    prompt = f"""You are an executive video briefing analyst. Summarize the following YouTube video content cleanly for a terminal CLI.

VIDEO URL: {video_url}
TRANSCRIPT CONTENT:
{transcript_text[:12000]}

FORMATTING RULES:
1. Do not use markdown tables.
2. Structure strictly as:

📺 VIDEO ESSENCE
(1-2 sentence core message of what this video explains or demonstrates)

🎯 KEY TAKEAWAYS & TIMESTAMPS
• Key point 1 with concise explanation
• Key point 2 with concise explanation
• Key point 3 with concise explanation
• Key point 4 (if relevant)

💡 ACTIONABLE INSIGHT / VERDICT
(One concluding takeaway)
"""
    try:
        response = client.models.generate_content(model=config.MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating summary: {e}\n\nTranscript preview:\n{transcript_text[:800]}..."


def capture_screenshot(url_or_target: str) -> tuple[bool, str]:
    """
    Captures a full webpage screenshot using headless browser and saves it in exports/.
    Returns: (success: bool, file_path_or_error: str)
    """
    from browser_navigator import resolve_url
    name, target_url = resolve_url(url_or_target)

    os.makedirs(config.EXPORT_DIR, exist_ok=True)
    filename = f"screenshot_{re.sub(r'[^a-zA-Z0-9]', '_', name.lower())}_{int(time.time())}.png"
    output_path = os.path.join(config.EXPORT_DIR, filename)

    # Search for browser executables on Windows
    browser_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]

    executable = next((p for p in browser_paths if os.path.exists(p)), None)
    if not executable:
        return False, "Neither Chrome nor Edge was found in standard system locations."

    cmd = [
        executable,
        "--headless=new",
        "--disable-gpu",
        "--window-size=1280,900",
        f"--screenshot={os.path.abspath(output_path)}",
        target_url
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            if getattr(config, "AUTO_OPEN_EXPORTS", True):
                try:
                    os.startfile(output_path)
                except Exception:
                    pass
            return True, output_path
        return False, "Screenshot file was not generated."
    except Exception as e:
        return False, str(e)


def send_browser_key_action(action: str) -> tuple[bool, str]:
    """
    Sends browser key actions (scroll down, scroll up, refresh, zoom in, zoom out).
    """
    if sys.platform != "win32":
        return False, "Keyboard automation currently supported on Windows."

    import ctypes
    user32 = ctypes.windll.user32
    action_lower = action.lower()

    # Keycodes
    VK_CONTROL = 0x11
    VK_F5 = 0x74
    VK_NEXT = 0x22   # Page Down
    VK_PRIOR = 0x21  # Page Up
    VK_PLUS = 0xBB
    VK_MINUS = 0xBD
    KEYEVENTF_KEYUP = 0x0002

    if "scroll down" in action_lower or "page down" in action_lower:
        user32.keybd_event(VK_NEXT, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(VK_NEXT, 0, KEYEVENTF_KEYUP, 0)
        return True, "Scrolled down active page."
    elif "scroll up" in action_lower or "page up" in action_lower:
        user32.keybd_event(VK_PRIOR, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(VK_PRIOR, 0, KEYEVENTF_KEYUP, 0)
        return True, "Scrolled up active page."
    elif "refresh" in action_lower or "reload" in action_lower:
        user32.keybd_event(VK_F5, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(VK_F5, 0, KEYEVENTF_KEYUP, 0)
        return True, "Reloaded active webpage."
    elif "zoom in" in action_lower:
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_PLUS, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(VK_PLUS, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        return True, "Zoomed in."
    elif "zoom out" in action_lower:
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_MINUS, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(VK_MINUS, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        return True, "Zoomed out."

    return False, f"Unknown browser action '{action}'."
