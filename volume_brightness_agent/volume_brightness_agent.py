"""
volume_brightness_agent.py
Main entry point for Orion's Brightness & Volume Control Agent.

Provides zero-cost, instant hardware control over:
1. Screen Brightness (all monitors, relative/absolute adjustments, min/max)
2. Master Audio Volume (0-100%, relative adjustments, mute/unmute)
3. Per-App Volume & Muting (Chrome, Spotify, Discord, Games, etc.)
4. Media Playback Keys (Play/Pause, Next Track, Previous Track, Stop)
5. Atmosphere Presets (Movie, Night, Gaming, Study, Work, Daylight, Sleep)

Works 100% offline via rule-based parser, with optional Gemini AI fallback.
"""

import os
import sys
import re
import json
import time
from typing import Dict, Any, List, Optional

# Enable UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from . import config, media_ops
except ImportError:
    import config, media_ops

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLOR_SUPPORT = True
except ImportError:
    COLOR_SUPPORT = False
    class Fore:
        CYAN = GREEN = YELLOW = RED = MAGENTA = BLUE = WHITE = LIGHTBLUE_EX = LIGHTCYAN_EX = LIGHTGREEN_EX = LIGHTYELLOW_EX = LIGHTRED_EX = RESET = ""
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ""


# =====================================================================
# DIRECT ZERO-COST OPERATIONS
# =====================================================================

def get_volume():
    """Get current master volume and mute status."""
    return media_ops.get_volume()


def set_volume(level: int):
    """Set master volume (0-100)."""
    return media_ops.set_volume(level)


def volume_up(step: Optional[int] = None):
    """Increase master volume."""
    return media_ops.volume_up(step)


def volume_down(step: Optional[int] = None):
    """Decrease master volume."""
    return media_ops.volume_down(step)


def mute():
    """Mute master audio."""
    return media_ops.mute()


def unmute():
    """Unmute master audio."""
    return media_ops.unmute()


def toggle_mute():
    """Toggle mute state."""
    return media_ops.toggle_mute()


def get_brightness():
    """Get screen brightness level."""
    return media_ops.get_brightness()


def set_brightness(level: int):
    """Set screen brightness (0-100)."""
    return media_ops.set_brightness(level)


def brightness_up(step: Optional[int] = None):
    """Increase screen brightness."""
    return media_ops.brightness_up(step)


def brightness_down(step: Optional[int] = None):
    """Decrease screen brightness."""
    return media_ops.brightness_down(step)


def max_brightness():
    """Set screen brightness to 100%."""
    return media_ops.max_brightness()


def min_brightness():
    """Set screen brightness to minimum."""
    return media_ops.min_brightness()


def play_pause():
    """Toggle play / pause for active media player."""
    return media_ops.media_play_pause()


def next_track():
    """Skip to next media track."""
    return media_ops.media_next()


def prev_track():
    """Return to previous media track."""
    return media_ops.media_previous()


def stop_media():
    """Stop media playback."""
    return media_ops.media_stop()


def apply_preset(name: str):
    """Apply an atmosphere preset (movie, night, gaming, study, work, etc.)."""
    return media_ops.apply_preset(name)


def list_presets():
    """List available presets."""
    return media_ops.list_presets()


def list_apps():
    """List running apps with audio sessions."""
    return media_ops.list_app_audio_sessions()


def set_app_volume(app: str, level: int):
    """Set volume for a specific app."""
    return media_ops.set_app_volume(app, level)


def mute_app(app: str):
    """Mute a specific app."""
    return media_ops.mute_app(app, mute_state=True)


def unmute_app(app: str):
    """Unmute a specific app."""
    return media_ops.mute_app(app, mute_state=False)


def get_status():
    """Get overall snapshot."""
    return media_ops.get_full_status()


# =====================================================================
# ADVANCED DIRECT HARDWARE & MEDIA OPERATIONS
# =====================================================================

def list_devices():
    """List all audio output devices."""
    return media_ops.list_audio_devices()


def switch_device(name: str):
    """Switch default audio output device (speakers, headphones, bluetooth, etc.)."""
    return media_ops.switch_audio_device(name)


def get_mic():
    """Get microphone volume and mute status."""
    return media_ops.get_mic_status()


def set_mic_volume(level: int):
    """Set microphone recording volume (0-100)."""
    return media_ops.set_mic_volume(level)


def mute_mic():
    """Mute the microphone."""
    return media_ops.mute_mic()


def unmute_mic():
    """Unmute the microphone."""
    return media_ops.unmute_mic()


def toggle_mic():
    """Toggle microphone mute."""
    return media_ops.toggle_mic_mute()


def now_playing():
    """Get currently playing song, artist, and app."""
    return media_ops.get_now_playing()


def sleep_timer(minutes: int, action: str = "mute", fade_duration_mins: int = 5):
    """Start sleep timer with smooth volume fade-out."""
    return media_ops.start_sleep_timer(minutes, action, fade_duration_mins)


def cancel_sleep_timer():
    """Cancel sleep timer."""
    return media_ops.cancel_sleep_timer()


def circadian_sync():
    """Sync brightness to current time of day."""
    return media_ops.sync_circadian_brightness()


def toggle_circadian(enable: Optional[bool] = None):
    """Toggle automatic day/night circadian brightness loop."""
    return media_ops.toggle_circadian(enable)


def night_light(enable: Optional[bool] = None):
    """Toggle or set Night Light display mode."""
    return media_ops.night_light_control(enable)


def switch_display(mode: str = "extend"):
    """Switch multi-monitor mode: extend, clone, internal, external."""
    return media_ops.switch_display(mode)


def detect_displays():
    """Detect connected monitors and display properties."""
    return media_ops.detect_current_display()


def detect_audio_devices():
    """List audio playback devices."""
    return media_ops.list_audio_devices()


def create_profile(name: str, brightness: int, volume: int, mute: bool = False):
    """Create custom atmosphere profile."""
    return media_ops.save_preset(name, brightness=brightness, volume=volume, mute=mute)


def context_control(active_app: Optional[str] = None):
    """Context-aware automatic volume and brightness tuning."""
    return media_ops.context_aware_control(active_app=active_app)




# =====================================================================
# SPOKEN / TELEMETRY SUMMARY
# =====================================================================

def get_spoken_summary() -> str:
    """
    Returns a natural language summary of current brightness and audio volume.
    """
    vol = get_volume()
    bri = get_brightness()
    mic = get_mic()
    now_p = now_playing()

    v_level = vol.get("level", 50)
    is_muted = vol.get("is_muted", False)
    b_level = bri.get("level", 50)
    mic_str = "muted" if mic.get("is_muted") else f"active at {mic.get('level')}%"

    vol_str = "muted" if is_muted else f"at {v_level} percent"
    track_str = f" Currently playing {now_p.get('title')} by {now_p.get('artist')}." if now_p.get("playing") and now_p.get("title") != "Audio Active" else ""

    return f"Master volume is {vol_str}, microphone is {mic_str}, and display brightness is at {b_level} percent.{track_str}"


# =====================================================================
# OFFLINE NATURAL LANGUAGE COMMAND PARSER
# =====================================================================

def _extract_percent_or_int(text: str, default: int = 10) -> int:
    """Extract integer or percentage number from text."""
    match = re.search(r"(\d+)\s*%?", text)
    if match:
        return int(match.group(1))
    return default


def _parse_command_offline(command_text: str) -> Dict[str, Any]:
    """
    100% offline regex & semantic rule-based parser.
    Parses commands for Volume, Brightness, Presets, App Mixer,
    Device Switching, Mic Control, Now Playing, Sleep Timer, and Circadian Sync.
    """
    text = command_text.strip().lower()
    actions = []

    # 1. Check for Preset Keywords First
    presets = getattr(config, "PRESETS", {})
    for p_name in presets:
        patterns = [
            rf"\b{p_name}\s+mode\b",
            rf"\b{p_name}\s+preset\b",
            rf"\bmode\s+{p_name}\b",
            rf"\bpreset\s+{p_name}\b",
            rf"\bapply\s+{p_name}\b",
            rf"^{p_name}$"
        ]
        if any(re.search(pat, text) for pat in patterns):
            actions.append({"action": "apply_preset", "preset": p_name})
            return {"actions": actions, "raw": command_text, "source": "offline_preset"}

    # 2. Split compound commands separated by 'and', '&', ',', ';'
    sub_clauses = re.split(r"\s+(?:and|then|&)\s+|\s*[,;]\s*", text)

    for clause in sub_clauses:
        clause = clause.strip()
        if not clause:
            continue

        # Feature 3: Now Playing / Song Detector
        if any(k in clause for k in ("what's playing", "whats playing", "now playing", "current song", "what song", "song name", "track info")) or clause == "song":
            actions.append({"action": "now_playing"})
            continue

        # Feature 1: Audio Output Device Switcher
        if re.search(r"\b(switch|change|set|select)\s+(?:audio\s+|sound\s+|output\s+)?(?:to\s+|device\s+)?(headphones?|speakers?|bluetooth|tws|earbuds?|airbass|buds|hands-free|realtek)\b", clause):
            m = re.search(r"\b(headphones?|speakers?|bluetooth|tws|earbuds?|airbass|buds|hands-free|realtek)\b", clause)
            dev_target = m.group(1) if m else "headphones"
            actions.append({"action": "switch_device", "device": dev_target})
            continue
        elif clause in ("devices", "list devices", "audio devices", "show devices", "list outputs"):
            actions.append({"action": "list_devices"})
            continue

        # Feature 2: Microphone Controls
        if "mic" in clause or "microphone" in clause:
            if "unmute" in clause or "sound on" in clause or "live" in clause:
                actions.append({"action": "unmute_mic"})
                continue
            elif "mute" in clause or "silence" in clause:
                actions.append({"action": "mute_mic"})
                continue
            elif "toggle" in clause:
                actions.append({"action": "toggle_mic"})
                continue
            elif any(k in clause for k in ("volume", "vol", "level", "%")):
                val = _extract_percent_or_int(clause, 80)
                actions.append({"action": "set_mic_volume", "level": val})
                continue
            elif clause in ("mic status", "mic", "microphone"):
                actions.append({"action": "get_mic"})
                continue

        # Feature 4: Sleep Timer & Volume Fade
        if "sleep timer" in clause or "fade volume" in clause or re.search(r"\b(turn off in|sleep in|fade in)\b", clause):
            if "cancel" in clause or "stop" in clause:
                actions.append({"action": "cancel_sleep_timer"})
                continue
            mins = _extract_percent_or_int(clause, 30)
            act = "screen_off" if "screen" in clause else "mute"
            actions.append({"action": "sleep_timer", "minutes": mins, "timer_action": act})
            continue

        # Feature 5: Circadian Auto-Brightness
        if any(k in clause for k in ("circadian", "auto brightness", "day night sync", "sync brightness")):
            if "off" in clause or "disable" in clause:
                actions.append({"action": "toggle_circadian", "enable": False})
            elif "on" in clause or "enable" in clause:
                actions.append({"action": "toggle_circadian", "enable": True})
            else:
                actions.append({"action": "circadian_sync"})
            continue

        # Media Playback Controls
        if clause in ("play", "pause", "play/pause", "toggle music", "resume", "play music", "pause music"):
            actions.append({"action": "media_play_pause"})
            continue
        elif clause in ("next", "next song", "next track", "skip", "skip song"):
            actions.append({"action": "media_next"})
            continue
        elif clause in ("prev", "previous", "previous song", "previous track", "back song"):
            actions.append({"action": "media_previous"})
            continue
        elif clause in ("stop", "stop music", "stop media", "stop playback"):
            actions.append({"action": "media_stop"})
            continue

        # Master Mute / Unmute
        if re.search(r"\b(unmute|un-mute|sound on|audio on)\b", clause):
            actions.append({"action": "unmute"})
            continue
        elif re.search(r"\b(mute|silence|quiet|shut up|shh|mute all)\b", clause) and not any(app in clause for app in ("chrome", "spotify", "discord", "youtube", "vlc", "app", "mic")):
            actions.append({"action": "mute"})
            continue
        elif re.search(r"\b(toggle mute|switch mute)\b", clause):
            actions.append({"action": "toggle_mute"})
            continue

        # Per-App Volume & Mute (e.g. 'mute chrome', 'spotify volume 30%', 'set discord to 50')
        app_match = re.search(r"\b(chrome|spotify|discord|vlc|youtube|whatsapp|telegram|browser|music|game)\b", clause)
        if app_match:
            app_name = app_match.group(1)
            if "mute" in clause and "unmute" not in clause:
                actions.append({"action": "mute_app", "app": app_name})
                continue
            elif "unmute" in clause:
                actions.append({"action": "unmute_app", "app": app_name})
                continue
            elif any(k in clause for k in ("volume", "vol", "level", "sound", "%")):
                val = _extract_percent_or_int(clause, 50)
                actions.append({"action": "set_app_volume", "app": app_name, "level": val})
                continue

        # General Volume phrases (even without the word 'volume')
        if re.search(r"\b(turn\s+it\s+up|turn\s+up|crank\s+it\s+up|raise\s+it|make\s+it\s+louder|louder)\b", clause):
            delta = _extract_percent_or_int(clause, config.DEFAULT_VOLUME_STEP)
            actions.append({"action": "volume_up", "step": delta})
            continue
        elif re.search(r"\b(turn\s+it\s+down|turn\s+down|lower\s+it|make\s+it\s+quieter|make\s+it\s+softer|quieter|softer|quiet\s+down)\b", clause):
            delta = _extract_percent_or_int(clause, config.DEFAULT_VOLUME_STEP)
            actions.append({"action": "volume_down", "step": delta})
            continue

        # Brightness Controls
        is_brightness = any(k in clause for k in ("brightness", "bright", "screen", "display", "dim", "dark", "backlight", "glare", "darken", "brighter"))
        is_volume = any(k in clause for k in ("volume", "vol", "sound", "audio", "loud", "soft", "louder", "quieter", "noise"))

        if is_brightness:
            if re.search(r"\b(max|maximum|full|100%|highest)\s*(brightness|screen|display)?\b", clause):
                actions.append({"action": "max_brightness"})
            elif re.search(r"\b(min|minimum|lowest|darkest|0%)\s*(brightness|screen|display)?\b", clause):
                actions.append({"action": "min_brightness"})
            elif re.search(r"\b(dim|darken|darker|lower\s+screen|decrease\s+screen|screen\s+down|brightness\s+down|less\s+bright)\b", clause):
                delta = _extract_percent_or_int(clause, config.DEFAULT_BRIGHTNESS_STEP)
                actions.append({"action": "brightness_down", "step": delta})
            elif re.search(r"\b(brighter|increase\s+brightness|brightness\s+up|screen\s+up|more\s+bright|boost\s+brightness|light\s+up)\b", clause):
                delta = _extract_percent_or_int(clause, config.DEFAULT_BRIGHTNESS_STEP)
                actions.append({"action": "brightness_up", "step": delta})
            elif re.search(r"\b(set|make|change|adjust)?\s*(brightness|screen|display)\s*(to|=)?\s*(\d+)\s*%?\b", clause):
                val = _extract_percent_or_int(clause, 50)
                actions.append({"action": "set_brightness", "level": val})
            elif re.search(r"\b(brightness|screen|b)\s+(\d+)\b", clause):
                val = _extract_percent_or_int(clause, 50)
                actions.append({"action": "set_brightness", "level": val})

        # Volume Controls
        if is_volume and not is_brightness:
            if re.search(r"\b(max|maximum|full|100%|highest)\s*(volume|sound|audio)?\b", clause):
                actions.append({"action": "set_volume", "level": 100})
            elif re.search(r"\b(min|minimum|lowest|0%)\s*(volume|sound|audio)?\b", clause):
                actions.append({"action": "set_volume", "level": 0})
            elif re.search(r"\b(louder|increase\s+volume|volume\s+up|vol\s+up|sound\s+up|raise\s+volume|more\s+sound|boost\s+volume)\b", clause):
                delta = _extract_percent_or_int(clause, config.DEFAULT_VOLUME_STEP)
                actions.append({"action": "volume_up", "step": delta})
            elif re.search(r"\b(quieter|softer|decrease\s+volume|volume\s+down|vol\s+down|sound\s+down|lower\s+volume|less\s+sound)\b", clause):
                delta = _extract_percent_or_int(clause, config.DEFAULT_VOLUME_STEP)
                actions.append({"action": "volume_down", "step": delta})
            elif re.search(r"\b(set|make|change|adjust)?\s*(volume|vol|sound|audio)\s*(to|=)?\s*(\d+)\s*%?\b", clause):
                val = _extract_percent_or_int(clause, 50)
                actions.append({"action": "set_volume", "level": val})
            elif re.search(r"\b(volume|vol|v)\s+(\d+)\b", clause):
                val = _extract_percent_or_int(clause, 50)
                actions.append({"action": "set_volume", "level": val})

        # Short single keyword / number fallbacks (e.g. '50%', 'v50', 'b70', '+10', '-10')
        if not actions:
            if clause.startswith("v ") or clause.startswith("vol "):
                val = _extract_percent_or_int(clause, 50)
                actions.append({"action": "set_volume", "level": val})
            elif clause.startswith("b ") or clause.startswith("bri "):
                val = _extract_percent_or_int(clause, 50)
                actions.append({"action": "set_brightness", "level": val})
            elif clause.startswith("mic "):
                val = _extract_percent_or_int(clause, 80)
                actions.append({"action": "set_mic_volume", "level": val})
            elif clause in ("+v", "v+", "vol+", "+vol"):
                actions.append({"action": "volume_up", "step": config.DEFAULT_VOLUME_STEP})
            elif clause in ("-v", "v-", "vol-", "-vol"):
                actions.append({"action": "volume_down", "step": config.DEFAULT_VOLUME_STEP})
            elif clause in ("+b", "b+", "bri+", "+bri"):
                actions.append({"action": "brightness_up", "step": config.DEFAULT_BRIGHTNESS_STEP})
            elif clause in ("-b", "b-", "bri-", "-bri"):
                actions.append({"action": "brightness_down", "step": config.DEFAULT_BRIGHTNESS_STEP})

    if not actions:
        # Final fallback check: if only a number was provided, set volume or ask
        match = re.match(r"^(\d+)\s*%?$", text)
        if match:
            actions.append({"action": "set_volume", "level": int(match.group(1))})

    return {
        "actions": actions,
        "raw": command_text,
        "source": "offline_parser"
    }


def parse_command(command_text: str) -> Dict[str, Any]:
    """Main parser entry point."""
    return _parse_command_offline(command_text)


# =====================================================================
# ACTION EXECUTION ENGINE
# =====================================================================

def execute_parsed_actions(parsed: Dict[str, Any]) -> List[str]:
    """
    Executes an array of actions returned by parse_command().
    """
    actions = parsed.get("actions", [])
    if not actions:
        return ["No recognized volume, brightness, mic, or media actions."]

    results = []
    for item in actions:
        action = item.get("action")
        try:
            # Volume & Brightness
            if action == "set_volume":
                results.append(set_volume(item.get("level", 50)))
            elif action == "volume_up":
                results.append(volume_up(item.get("step", config.DEFAULT_VOLUME_STEP)))
            elif action == "volume_down":
                results.append(volume_down(item.get("step", config.DEFAULT_VOLUME_STEP)))
            elif action == "mute":
                results.append(mute())
            elif action == "unmute":
                results.append(unmute())
            elif action == "toggle_mute":
                results.append(toggle_mute())
            elif action == "set_brightness":
                results.append(set_brightness(item.get("level", 50)))
            elif action == "brightness_up":
                results.append(brightness_up(item.get("step", config.DEFAULT_BRIGHTNESS_STEP)))
            elif action == "brightness_down":
                results.append(brightness_down(item.get("step", config.DEFAULT_BRIGHTNESS_STEP)))
            elif action == "max_brightness":
                results.append(max_brightness())
            elif action == "min_brightness":
                results.append(min_brightness())

            # App Volume & Mute
            elif action == "set_app_volume":
                results.append(set_app_volume(item.get("app", ""), item.get("level", 50)))
            elif action == "mute_app":
                results.append(mute_app(item.get("app", "")))
            elif action == "unmute_app":
                results.append(unmute_app(item.get("app", "")))

            # Media Keys
            elif action == "media_play_pause":
                results.append(play_pause())
            elif action == "media_next":
                results.append(next_track())
            elif action == "media_previous":
                results.append(prev_track())
            elif action == "media_stop":
                results.append(stop_media())

            # Presets
            elif action == "apply_preset":
                res = apply_preset(item.get("preset", ""))
                results.append(res.get("message", "Preset applied"))

            # Feature 1: Device Switcher
            elif action == "switch_device":
                results.append(switch_device(item.get("device", "")))
            elif action == "list_devices":
                devs = list_devices()
                dev_lines = [f"• {d['name']} ({d['state']})" for d in devs[:8]]
                results.append(f"Audio Devices ({len(devs)}):\n" + "\n".join(dev_lines))

            # Feature 2: Microphone
            elif action == "set_mic_volume":
                results.append(set_mic_volume(item.get("level", 80)))
            elif action == "mute_mic":
                results.append(mute_mic())
            elif action == "unmute_mic":
                results.append(unmute_mic())
            elif action == "toggle_mic":
                results.append(toggle_mic())
            elif action == "get_mic":
                m_st = get_mic()
                results.append(m_st.get("display", "Mic status available"))

            # Feature 3: Now Playing
            elif action == "now_playing":
                np_info = now_playing()
                results.append(np_info.get("display", "No track playing"))

            # Feature 4: Sleep Timer
            elif action == "sleep_timer":
                mins = item.get("minutes", 30)
                act = item.get("timer_action", "mute")
                results.append(sleep_timer(mins, action=act))
            elif action == "cancel_sleep_timer":
                results.append(cancel_sleep_timer())

            # Feature 5: Circadian Sync
            elif action == "circadian_sync":
                results.append(circadian_sync())
            elif action == "toggle_circadian":
                results.append(toggle_circadian(item.get("enable", True)))

            else:
                results.append(f"Unknown action: '{action}'")
        except Exception as e:
            results.append(f"Error on '{action}': {e}")

    return results


# =====================================================================
# PROFESSIONAL IN-TERMINAL CMD DASHBOARD & INTERFACE
# =====================================================================

def _render_bar(percent: int, length: int = 20, is_muted: bool = False) -> str:
    """Render a modern visual terminal progress gauge."""
    percent = max(0, min(100, percent))
    filled = int(round((percent / 100.0) * length))
    empty = length - filled
    if is_muted:
        bar = "×" * length
        return f"[{Fore.RED}{bar}{Fore.RESET}] {percent:>3}%"
    bar = "█" * filled + "░" * empty
    color = Fore.LIGHTCYAN_EX if percent > 60 else (Fore.LIGHTGREEN_EX if percent > 25 else Fore.YELLOW)
    return f"[{color}{bar}{Fore.RESET}] {percent:>3}%"


def show_cmd_dashboard():
    """Display clean, modern, executive-grade CMD dashboard."""
    vol = get_volume()
    bri = get_brightness()
    mic = get_mic()
    now_p = now_playing()
    apps = list_apps()
    presets = list_presets()
    sleep_st = media_ops.get_sleep_timer_status()
    circ_on = media_ops.is_circadian_active()

    v_lvl = vol.get("level", 50)
    v_mut = vol.get("is_muted", False)
    b_lvl = bri.get("level", 50)
    m_lvl = mic.get("level", 80)
    m_mut = mic.get("is_muted", False)
    monitors = bri.get("monitors", ["Main Display"])
    mon_name = monitors[0] if monitors else "Main Display"

    # Header Card
    print(Fore.CYAN + "┌" + "─" * 70 + "┐" + Style.RESET_ALL)
    header_title = f"  {Style.BRIGHT}ORION HARDWARE & ATMOSPHERE MANAGER{Style.RESET_ALL}"
    badge = f"{Fore.GREEN}[● Online]{Fore.CYAN}"
    print(Fore.CYAN + f"│{header_title:<55}{badge:>25} │" + Style.RESET_ALL)
    print(Fore.CYAN + "└" + "─" * 70 + "┘" + Style.RESET_ALL)

    # 1. System Telemetry Section
    print(f"\n {Fore.WHITE}{Style.BRIGHT}HARDWARE TELEMETRY{Style.RESET_ALL}")
    print(Fore.LIGHTBLACK_EX + "  " + "─" * 68 + Style.RESET_ALL)
    
    v_status = f"{Fore.RED}○ Muted{Style.RESET_ALL}" if v_mut else f"{Fore.GREEN}● Active{Style.RESET_ALL}"
    m_status = f"{Fore.RED}○ Muted{Style.RESET_ALL}" if m_mut else f"{Fore.GREEN}● Live{Style.RESET_ALL}"
    
    print(f"  Volume        {_render_bar(v_lvl, 18, v_mut)}   {v_status}")
    print(f"  Microphone    {_render_bar(m_lvl, 18, m_mut)}   {m_status}")
    print(f"  Brightness    {_render_bar(b_lvl, 18)}   {Fore.LIGHTBLACK_EX}● {mon_name}{Style.RESET_ALL}")

    # Active Background Daemons (Only if enabled)
    badges = []
    if sleep_st.get("active"):
        badges.append(f"{Fore.MAGENTA}⏳ Sleep Timer: {sleep_st.get('display')}{Style.RESET_ALL}")
    if circ_on:
        badges.append(f"{Fore.CYAN}⏰ Circadian Sync: Active ({media_ops.get_circadian_brightness()}% target){Style.RESET_ALL}")
    if badges:
        print(f"  {' | '.join(badges)}")

    # 2. Now Playing Banner (Only if active)
    if now_p.get("playing") and now_p.get("title") not in ("No Media Playing", "Unknown Title"):
        print(f"\n {Fore.WHITE}{Style.BRIGHT}NOW PLAYING{Style.RESET_ALL}")
        print(Fore.LIGHTBLACK_EX + "  " + "─" * 68 + Style.RESET_ALL)
        track = now_p.get('title', 'Unknown')
        artist = now_p.get('artist', 'Various')
        app = now_p.get('app', 'Player')
        print(f"  🎵 {Fore.LIGHTGREEN_EX}{track}{Style.RESET_ALL} — {Fore.LIGHTCYAN_EX}{artist}{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}[{app}]{Style.RESET_ALL}")

    # 3. Atmosphere Presets (Compact 2-Column Grid)
    print(f"\n {Fore.WHITE}{Style.BRIGHT}ATMOSPHERE PRESETS{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}(Type name to activate, e.g. 'movie mode'){Style.RESET_ALL}")
    print(Fore.LIGHTBLACK_EX + "  " + "─" * 68 + Style.RESET_ALL)
    preset_items = list(presets.items())
    
    for i in range(0, len(preset_items), 2):
        p1_name, p1_val = preset_items[i]
        p1_b = p1_val.get("brightness", 50)
        p1_v = "Muted" if p1_val.get("mute") else f"{p1_val.get('volume', 50)}%"
        col1 = f"[{Fore.YELLOW}{p1_name.title():<8}{Style.RESET_ALL}]  ☀️ {p1_b:>2}%  🔊 {p1_v:<6}"

        col2 = ""
        if i + 1 < len(preset_items):
            p2_name, p2_val = preset_items[i+1]
            p2_b = p2_val.get("brightness", 50)
            p2_v = "Muted" if p2_val.get("mute") else f"{p2_val.get('volume', 50)}%"
            col2 = f"[{Fore.YELLOW}{p2_name.title():<8}{Style.RESET_ALL}]  ☀️ {p2_b:>2}%  🔊 {p2_v:<6}"

        print(f"  {col1:<40} {col2}")

    # 4. Active Audio Sessions (If any exist)
    if apps:
        print(f"\n {Fore.WHITE}{Style.BRIGHT}ACTIVE AUDIO APPS{Style.RESET_ALL}")
        print(Fore.LIGHTBLACK_EX + "  " + "─" * 68 + Style.RESET_ALL)
        for a in apps[:4]:
            a_name = a.get('name', 'Unknown')
            a_lvl = a.get('level', 50)
            a_mut = a.get('is_muted', False)
            a_st = f"{Fore.RED}Muted{Style.RESET_ALL}" if a_mut else f"{Fore.GREEN}Active{Style.RESET_ALL}"
            print(f"  • {Fore.WHITE}{a_name:<20}{Style.RESET_ALL} {_render_bar(a_lvl, 10, a_mut)}  {a_st}")

    print(Fore.LIGHTBLACK_EX + "  " + "─" * 68 + Style.RESET_ALL)
    print(f"  {Fore.LIGHTBLACK_EX}Shortcuts: [C] Customize Presets  [M] Mixer  [D] Refresh  [?] Help  [Q] Exit{Style.RESET_ALL}\n")


def interactive_preset_customizer():
    """Clean interactive preset customization wizard."""
    presets = list_presets()
    preset_keys = list(presets.keys())

    print("\n" + Fore.CYAN + "┌" + "─" * 58 + "┐" + Style.RESET_ALL)
    print(Fore.CYAN + f"│  {Style.BRIGHT}ATMOSPHERE PRESET CUSTOMIZER{Style.RESET_ALL}{' ':>30}│" + Style.RESET_ALL)
    print(Fore.CYAN + "└" + "─" * 58 + "┘" + Style.RESET_ALL)
    
    for idx, key in enumerate(preset_keys, 1):
        p = presets[key]
        m_tag = " [Muted]" if p.get("mute") else ""
        print(f"  [{Fore.YELLOW}{idx:>2}{Style.RESET_ALL}] {key.title():<12} Brightness: {p.get('brightness'):>2}%  |  Volume: {p.get('volume'):>2}%{m_tag}")
    print(f"  [{Fore.GREEN} +{Style.RESET_ALL}] Create New Preset")
    print(f"  [ 0] Cancel")
    print(Fore.LIGHTBLACK_EX + "  " + "─" * 56 + Style.RESET_ALL)

    try:
        choice = input(f"{Fore.CYAN}  Select preset (number/name): {Style.RESET_ALL}").strip()
        if not choice or choice in ("0", "cancel", "q", "exit"):
            return

        target_key = None
        if choice == "+":
            new_name = input(f"{Fore.CYAN}  New preset name: {Style.RESET_ALL}").strip().lower()
            if not new_name:
                return
            target_key = new_name
            current_data = {"brightness": 50, "volume": 50, "mute": False, "description": f"Custom {new_name} mode", "icon": "✨"}
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(preset_keys):
                target_key = preset_keys[idx]
                current_data = presets[target_key]
            else:
                return
        elif choice.lower() in presets:
            target_key = choice.lower()
            current_data = presets[target_key]
        else:
            return

        print(f"\n  Configuring {Fore.YELLOW}'{target_key.title()}'{Style.RESET_ALL}:")
        
        b_input = input(f"  • Brightness (0-100) [{current_data.get('brightness', 50)}%]: ").strip()
        new_b = int(b_input) if b_input.isdigit() else current_data.get('brightness', 50)
        new_b = max(0, min(100, new_b))

        v_input = input(f"  • Volume (0-100) [{current_data.get('volume', 50)}%]: ").strip()
        new_v = int(v_input) if v_input.isdigit() else current_data.get('volume', 50)
        new_v = max(0, min(100, new_v))

        cur_m = "y" if current_data.get("mute") else "n"
        m_input = input(f"  • Mute audio? (y/n) [{cur_m}]: ").strip().lower()
        new_m = (m_input == "y" or m_input == "yes") if m_input else current_data.get("mute", False)

        cur_desc = current_data.get("description", "")
        d_input = input(f"  • Description [{cur_desc}]: ").strip()
        new_desc = d_input if d_input else cur_desc

        media_ops.save_preset(
            name=target_key,
            brightness=new_b,
            volume=new_v,
            mute=new_m,
            description=new_desc,
            icon=current_data.get("icon", "✨"),
            color=current_data.get("color", "#06b6d4")
        )

        print(f"\n  {Fore.GREEN}✓ Preset '{target_key}' saved successfully!{Style.RESET_ALL}")
        
        test_now = input(f"  Apply now to test? (y/n): ").strip().lower()
        if test_now in ("y", "yes"):
            apply_res = apply_preset(target_key)
            print(f"  {Fore.GREEN}✓ {apply_res.get('message')}{Style.RESET_ALL}")

    except Exception as e:
        print(f"  {Fore.RED}Error saving preset: {e}{Style.RESET_ALL}")


def show_mixer():
    """Display dedicated clean per-app mixer."""
    apps = list_apps()
    print("\n" + Fore.CYAN + "┌" + "─" * 58 + "┐" + Style.RESET_ALL)
    print(Fore.CYAN + f"│  {Style.BRIGHT}PER-APP AUDIO MIXER{Style.RESET_ALL}{' ':>39}│" + Style.RESET_ALL)
    print(Fore.CYAN + "└" + "─" * 58 + "┘" + Style.RESET_ALL)
    if not apps:
        print("  No active audio sessions found.")
        print("  (Play audio in Spotify, Chrome, YouTube, or Discord to see sliders)")
    else:
        for a in apps:
            mute_str = f"{Fore.RED}Muted{Style.RESET_ALL}" if a.get("is_muted") else f"{Fore.GREEN}Active{Style.RESET_ALL}"
            bar = _render_bar(a.get('level', 50), 14, a.get('is_muted'))
            print(f"  • {Fore.WHITE}{a.get('name'):<20}{Style.RESET_ALL} {bar}  {mute_str}")
    print(Fore.LIGHTBLACK_EX + "  " + "─" * 56 + Style.RESET_ALL)


def print_help():
    """Display concise, structured commands help."""
    print(f"""
{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│ COMMAND REFERENCE                                                      │
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
  {Fore.GREEN}Hardware Controls:{Style.RESET_ALL}
    • Volume:        'vol 60', 'volume up', 'turn it down', 'mute', 'unmute'
    • Brightness:    'screen 80', 'dim screen', 'brighter', 'max brightness'
    • Microphone:    'mute mic', 'unmute mic', 'mic volume 80%', 'mic'
    • Audio Output:  'switch to headphones', 'switch to speakers', 'devices'

  {Fore.GREEN}Media & Atmosphere:{Style.RESET_ALL}
    • Presets:       'movie mode', 'night mode', 'gaming mode', 'study mode', 'sleep mode'
    • Now Playing:   'what\'s playing', 'song', 'play', 'pause', 'next', 'prev'
    • Per-App Audio: 'mute spotify', 'unmute chrome', 'set spotify volume to 40%'
    • Timers & Sync: 'sleep timer 30 mins', 'circadian on', 'circadian off'

  {Fore.GREEN}Navigation Shortcuts:{Style.RESET_ALL}
    • 'customize' / 'c' : Open in-terminal preset customizer wizard
    • 'dash' / 'd'      : Refresh and display clean telemetry dashboard
    • 'mixer' / 'm'     : Show per-app audio mixer
    • 'cls' / 'clear'   : Clear screen
    • 'exit' / 'q'      : Exit agent
""")


if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    show_cmd_dashboard()

    while True:
        try:
            cmd = input(f"{Fore.CYAN}orion > {Style.RESET_ALL}").strip()
            if not cmd:
                continue

            cmd_lower = cmd.lower()
            if cmd_lower in ("exit", "quit", "q"):
                print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                break
            elif cmd_lower in ("help", "?", "man"):
                print_help()
                continue
            elif cmd_lower in ("status", "s", "dash", "dashboard", "cls", "clear", "d"):
                os.system("cls" if os.name == "nt" else "clear")
                show_cmd_dashboard()
                continue
            elif cmd_lower in ("customize", "c", "edit", "edit preset", "custom"):
                interactive_preset_customizer()
                continue
            elif cmd_lower in ("mixer", "m", "apps", "sessions", "audio apps"):
                show_mixer()
                continue
            elif cmd_lower in ("presets", "modes", "list presets"):
                p_dict = list_presets()
                print(f"\n{Fore.LIGHTCYAN_EX}[Atmosphere Presets]:{Style.RESET_ALL}")
                for p_name, p_val in p_dict.items():
                    m_tag = " | Muted" if p_val.get("mute") else ""
                    print(f"  • {Fore.YELLOW}{p_name.title():<12}{Style.RESET_ALL} -> Brightness: {p_val.get('brightness')}%, Volume: {p_val.get('volume')}%{m_tag}")
                continue
            elif cmd_lower in ("summary", "speak"):
                print(f"\n  {Fore.GREEN}{get_spoken_summary()}{Style.RESET_ALL}\n")
                continue

            parsed = parse_command(cmd)
            results = execute_parsed_actions(parsed)
            print()
            for r in results:
                print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {r}")
            print()

        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

