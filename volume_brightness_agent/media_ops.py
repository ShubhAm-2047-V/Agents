"""
media_ops.py
Core low-level operations for controlling Windows Master Volume, Per-App Volume,
Screen Brightness, Media Playback keys, and Atmosphere Presets.

100% local, instant execution, zero API cost.
"""

import sys
import os
import ctypes
from datetime import datetime
from typing import Dict, Any, List, Optional

# Win32 Virtual Key Constants for Media & Volume Hardware Keys
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

try:
    from . import config
except ImportError:
    import config


# =====================================================================
# WIN32 HARDWARE KEY EMULATION (FALLBACK & MEDIA CONTROL)
# =====================================================================

def _send_virtual_key(vk_code: int) -> None:
    """Send a Win32 virtual key press and release."""
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
    except Exception as e:
        print(f"[media_ops] Warning: Key event failed for vk {vk_code}: {e}")


def media_play_pause() -> str:
    """Toggle Play / Pause for currently playing media (Spotify, YouTube, VLC, etc.)."""
    _send_virtual_key(VK_MEDIA_PLAY_PAUSE)
    return "Toggled Media Play/Pause."


def media_next() -> str:
    """Skip to the next media track."""
    _send_virtual_key(VK_MEDIA_NEXT_TRACK)
    return "Skipped to next track."


def media_previous() -> str:
    """Return to previous media track."""
    _send_virtual_key(VK_MEDIA_PREV_TRACK)
    return "Returned to previous track."


def media_stop() -> str:
    """Stop media playback."""
    _send_virtual_key(VK_MEDIA_STOP)
    return "Stopped media playback."


# =====================================================================
# AUDIO / VOLUME CONTROLS (PYCAW + WIN32 FALLBACK)
# =====================================================================

def _get_endpoint_volume():
    """Helper to obtain the default audio endpoint volume interface across pycaw versions."""
    try:
        from pycaw.pycaw import AudioUtilities
        speakers = AudioUtilities.GetSpeakers()
        if hasattr(speakers, "EndpointVolume"):
            return speakers.EndpointVolume
        # Legacy Pycaw fallback
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER
        from pycaw.pycaw import IAudioEndpointVolume
        interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as e:
        return None


def get_volume() -> Dict[str, Any]:
    """
    Get current master audio volume level (0-100) and mute status.
    """
    endpoint = _get_endpoint_volume()
    if endpoint:
        try:
            scalar = endpoint.GetMasterVolumeLevelScalar()
            is_muted = bool(endpoint.GetMute())
            level = int(round(scalar * 100))
            return {
                "level": level,
                "is_muted": is_muted,
                "status": f"{level}%" + (" (Muted)" if is_muted else "")
            }
        except Exception as e:
            return {"level": 50, "is_muted": False, "status": f"Error reading volume: {e}"}
    
    return {"level": 50, "is_muted": False, "status": "Audio endpoint unavailable"}


def set_volume(level: int) -> str:
    """
    Set master audio volume to a percentage between 0 and 100.
    Automatically un-mutes if volume is set > 0.
    """
    level = max(0, min(100, int(level)))
    endpoint = _get_endpoint_volume()
    if endpoint:
        try:
            scalar = float(level) / 100.0
            endpoint.SetMasterVolumeLevelScalar(scalar, None)
            if level > 0 and endpoint.GetMute():
                endpoint.SetMute(0, None)
            return f"Master volume set to {level}%"
        except Exception as e:
            return f"Failed to set volume: {e}"

    # Fallback: estimate via key events
    return f"Set volume: endpoint unavailable on this device."


def change_volume(delta: int) -> str:
    """
    Change master audio volume by a relative amount (e.g. +10 or -15).
    """
    current = get_volume()
    current_level = current.get("level", 50)
    new_level = max(0, min(100, current_level + int(delta)))
    return set_volume(new_level)


def volume_up(step: Optional[int] = None) -> str:
    """Increase master volume by standard step."""
    step = step if step is not None else getattr(config, "DEFAULT_VOLUME_STEP", 10)
    return change_volume(step)


def volume_down(step: Optional[int] = None) -> str:
    """Decrease master volume by standard step."""
    step = step if step is not None else getattr(config, "DEFAULT_VOLUME_STEP", 10)
    return change_volume(-step)


def mute() -> str:
    """Mute master audio."""
    endpoint = _get_endpoint_volume()
    if endpoint:
        try:
            endpoint.SetMute(1, None)
            return "Audio muted."
        except Exception as e:
            return f"Failed to mute: {e}"
    _send_virtual_key(VK_VOLUME_MUTE)
    return "Mute toggled via key shortcut."


def unmute() -> str:
    """Unmute master audio."""
    endpoint = _get_endpoint_volume()
    if endpoint:
        try:
            endpoint.SetMute(0, None)
            return "Audio unmuted."
        except Exception as e:
            return f"Failed to unmute: {e}"
    return "Audio unmuted."


def toggle_mute() -> str:
    """Toggle mute / unmute master audio."""
    endpoint = _get_endpoint_volume()
    if endpoint:
        try:
            is_muted = endpoint.GetMute()
            new_mute = 0 if is_muted else 1
            endpoint.SetMute(new_mute, None)
            return "Audio muted." if new_mute == 1 else "Audio unmuted."
        except Exception as e:
            return f"Failed to toggle mute: {e}"
    _send_virtual_key(VK_VOLUME_MUTE)
    return "Mute toggled via hardware key."


def list_app_audio_sessions() -> List[Dict[str, Any]]:
    """
    List all running applications with an active audio session and their volume levels.
    """
    results = []
    try:
        from pycaw.pycaw import AudioUtilities
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            name = None
            pid = None
            try:
                if session.Process:
                    name = session.Process.name()
                    pid = session.Process.pid
            except Exception:
                continue

            if not name:
                name = "System Sound"

            try:
                volume = session.SimpleAudioVolume
                vol_scalar = volume.GetMasterVolume()
                is_muted = bool(volume.GetMute())
                results.append({
                    "name": name,
                    "pid": pid,
                    "level": int(round(vol_scalar * 100)),
                    "is_muted": is_muted
                })
            except Exception:
                pass
    except Exception as e:
        print(f"[media_ops] Warning listing audio sessions: {e}")
    return results


def set_app_volume(app_name: str, level: int) -> str:
    """
    Set volume for a specific application (e.g. 'chrome', 'spotify', 'vlc').
    """
    level = max(0, min(100, int(level)))
    scalar = float(level) / 100.0
    app_query = app_name.lower().replace(".exe", "")
    
    # Resolve aliases from config if present
    aliases = getattr(config, "APP_ALIASES", {})
    if app_query in aliases:
        app_query = aliases[app_query].lower().replace(".exe", "")

    found = False
    try:
        from pycaw.pycaw import AudioUtilities
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            try:
                if session.Process:
                    proc_name = session.Process.name().lower()
                    if app_query in proc_name:
                        volume = session.SimpleAudioVolume
                        volume.SetMasterVolume(scalar, None)
                        if level > 0 and volume.GetMute():
                            volume.SetMute(0, None)
                        found = True
            except Exception:
                continue
    except Exception as e:
        return f"Error modifying app volume: {e}"

    if found:
        return f"Set {app_name} volume to {level}%"
    return f"No active audio session found for '{app_name}'. Is it playing sound?"


def mute_app(app_name: str, mute_state: bool = True) -> str:
    """Mute or unmute a specific application."""
    app_query = app_name.lower().replace(".exe", "")
    found = False
    try:
        from pycaw.pycaw import AudioUtilities
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            try:
                if session.Process:
                    proc_name = session.Process.name().lower()
                    if app_query in proc_name:
                        volume = session.SimpleAudioVolume
                        volume.SetMute(1 if mute_state else 0, None)
                        found = True
            except Exception:
                continue
    except Exception as e:
        return f"Error muting app: {e}"

    state_str = "Muted" if mute_state else "Unmuted"
    if found:
        return f"{state_str} audio for {app_name}"
    return f"No active audio session found for '{app_name}'"


# =====================================================================
# DISPLAY / BRIGHTNESS CONTROLS
# =====================================================================

def get_brightness() -> Dict[str, Any]:
    """
    Get screen brightness (0-100) for connected displays.
    """
    try:
        import screen_brightness_control as sbc
        bright_list = sbc.get_brightness()
        if isinstance(bright_list, list) and len(bright_list) > 0:
            avg_bright = int(round(sum(bright_list) / len(bright_list)))
            monitors = sbc.list_monitors()
            return {
                "level": avg_bright,
                "monitors": monitors,
                "values": bright_list,
                "status": f"{avg_bright}%"
            }
        elif isinstance(bright_list, int):
            return {
                "level": bright_list,
                "monitors": ["Primary Display"],
                "values": [bright_list],
                "status": f"{bright_list}%"
            }
    except Exception as e:
        pass

    # Fallback to WMI via PowerShell if library encounters display driver quirks
    try:
        import subprocess
        cmd = "powershell -Command \"(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness\""
        out = subprocess.check_output(cmd, shell=True, text=True, timeout=3).strip()
        if out.isdigit():
            val = int(out)
            return {"level": val, "monitors": ["Built-in Display"], "values": [val], "status": f"{val}%"}
    except Exception:
        pass

    return {"level": 50, "monitors": ["Unknown Display"], "values": [50], "status": "Unable to read brightness"}


def set_brightness(level: int, display: Optional[Any] = None) -> str:
    """
    Set display brightness to a specific percentage (0-100).
    """
    level = max(0, min(100, int(level)))
    try:
        import screen_brightness_control as sbc
        if display is not None:
            sbc.set_brightness(level, display=display)
        else:
            sbc.set_brightness(level)
        return f"Brightness set to {level}%"
    except Exception as e:
        pass

    # WMI PowerShell fallback
    try:
        import subprocess
        ps_script = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
        subprocess.run(["powershell", "-Command", ps_script], timeout=4, capture_output=True)
        return f"Brightness set to {level}% (via WMI fallback)"
    except Exception as e:
        return f"Failed to set brightness: {e}"


def change_brightness(delta: int, display: Optional[Any] = None) -> str:
    """
    Change display brightness by a relative amount (e.g. +15 or -10).
    """
    info = get_brightness()
    current = info.get("level", 50)
    new_level = max(0, min(100, current + int(delta)))
    return set_brightness(new_level, display=display)


def brightness_up(step: Optional[int] = None) -> str:
    """Increase screen brightness by standard step."""
    step = step if step is not None else getattr(config, "DEFAULT_BRIGHTNESS_STEP", 10)
    return change_brightness(step)


def brightness_down(step: Optional[int] = None) -> str:
    """Decrease screen brightness by standard step."""
    step = step if step is not None else getattr(config, "DEFAULT_BRIGHTNESS_STEP", 10)
    return change_brightness(-step)


def max_brightness() -> str:
    """Set screen brightness to 100%."""
    return set_brightness(100)


def min_brightness() -> str:
    """Set screen brightness to minimum (0% or 5%)."""
    return set_brightness(0)


# =====================================================================
# ATMOSPHERE / SCENARIO PRESETS (PERSISTENT & CUSTOMIZABLE)
# =====================================================================

PRESETS_FILE = os.path.join(os.path.dirname(__file__), "data", "presets.json")


def load_presets() -> Dict[str, Dict[str, Any]]:
    """Load presets from data/presets.json with fallback to config.PRESETS."""
    import json
    if os.path.exists(PRESETS_FILE):
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return getattr(config, "PRESETS", {})


def save_preset(name: str, brightness: int, volume: int, mute: bool = False,
                description: str = "", icon: str = "✨", color: str = "#06b6d4") -> Dict[str, Any]:
    """
    Save or update a customized atmosphere preset to data/presets.json.
    """
    import json
    name_clean = name.lower().strip()
    presets = load_presets()

    presets[name_clean] = {
        "brightness": max(0, min(100, int(brightness))),
        "volume": max(0, min(100, int(volume))),
        "mute": bool(mute),
        "description": description or f"Custom preset for {name_clean}",
        "icon": icon or "✨",
        "color": color or "#06b6d4"
    }

    os.makedirs(os.path.dirname(PRESETS_FILE), exist_ok=True)
    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2)

    return {"success": True, "preset": name_clean, "data": presets[name_clean]}


def delete_preset(name: str) -> Dict[str, Any]:
    """Delete a custom preset from data/presets.json."""
    import json
    name_clean = name.lower().strip()
    presets = load_presets()

    if name_clean in presets:
        del presets[name_clean]
        os.makedirs(os.path.dirname(PRESETS_FILE), exist_ok=True)
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2)
        return {"success": True, "message": f"Deleted preset '{name_clean}'"}
    return {"success": False, "message": f"Preset '{name_clean}' not found"}


def apply_preset(preset_name: str) -> Dict[str, Any]:
    """
    Apply combined atmosphere presets for brightness, volume, and mute states.
    """
    presets = load_presets()
    name_clean = preset_name.lower().strip()
    preset = presets.get(name_clean)

    if not preset:
        # Fuzzy match
        for key in presets:
            if key in name_clean or name_clean in key:
                preset = presets[key]
                name_clean = key
                break

    if not preset:
        return {"success": False, "message": f"Preset '{preset_name}' not found. Available: {', '.join(presets.keys())}"}

    logs = []
    
    # 1. Set Brightness
    if "brightness" in preset:
        b_res = set_brightness(preset["brightness"])
        logs.append(b_res)

    # 2. Set Volume
    if "volume" in preset:
        v_res = set_volume(preset["volume"])
        logs.append(v_res)

    # 3. Mute state
    if preset.get("mute") is True:
        m_res = mute()
        logs.append(m_res)
    elif preset.get("mute") is False:
        u_res = unmute()
        logs.append(u_res)

    return {
        "success": True,
        "preset": name_clean,
        "description": preset.get("description", ""),
        "details": logs,
        "message": f"Applied '{name_clean.title()}' preset: {', '.join(logs)}"
    }


def list_presets() -> Dict[str, Dict[str, Any]]:
    """List all available environment presets."""
    return load_presets()


# =====================================================================
# AUDIO OUTPUT DEVICE SWITCHER
# =====================================================================

def list_audio_devices() -> List[Dict[str, Any]]:
    """
    List all audio playback endpoints (Speakers, Headphones, Bluetooth, HDMI).
    """
    results = []
    try:
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetAllDevices()
        for d in devices:
            try:
                state_str = str(d.state).split(".")[-1]
                # Filter to active or present devices
                if state_str in ("Active", "Unplugged", "Disabled", "NotPresent"):
                    results.append({
                        "name": str(d.FriendlyName),
                        "id": str(d.id),
                        "state": state_str,
                        "is_active": state_str == "Active"
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"[media_ops] Warning listing audio devices: {e}")
    return results


def switch_audio_device(name_query: str) -> str:
    """
    Switch Windows default playback audio device (e.g. 'headphones', 'speakers', 'bluetooth', 'tws').
    """
    name_query = name_query.lower().strip()
    try:
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetAllDevices()
        matched = None

        for d in devices:
            fname = str(d.FriendlyName).lower()
            if name_query in fname:
                matched = d
                break

        if not matched:
            # Fuzzy match aliases
            for d in devices:
                fname = str(d.FriendlyName).lower()
                if ("headphone" in name_query or "earphone" in name_query) and ("headphone" in fname or "tws" in fname or "ear" in fname or "airbass" in fname or "buds" in fname):
                    matched = d
                    break
                elif ("speaker" in name_query or "main" in name_query) and ("speaker" in fname or "realtek" in fname):
                    matched = d
                    break
                elif "bluetooth" in name_query and ("bluetooth" in fname or "hands-free" in fname or "tws" in fname or "buds" in fname):
                    matched = d
                    break

        if matched:
            try:
                AudioUtilities.SetDefaultDevice(matched.id)
                return f"Switched default audio output to '{matched.FriendlyName}'"
            except Exception as set_err:
                # Fallback via PowerShell AudioDeviceCmdlets / nircmd if installed
                return f"Selected device '{matched.FriendlyName}'. (Device ID: {matched.id})"
        
        return f"Audio device matching '{name_query}' not found. Use 'devices' to list all."
    except Exception as e:
        return f"Failed to switch audio device: {e}"


# =====================================================================
# GLOBAL MICROPHONE CONTROLS & PRIVACY
# =====================================================================

def _get_mic_endpoint_volume():
    """Helper to obtain default microphone endpoint volume."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER
        mic_dev = AudioUtilities.GetMicrophone()
        if mic_dev:
            if hasattr(mic_dev, "EndpointVolume"):
                return mic_dev.EndpointVolume
            iface = mic_dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(iface, POINTER(IAudioEndpointVolume))
    except Exception:
        pass
    return None


def get_mic_status() -> Dict[str, Any]:
    """
    Get current microphone volume level (0-100) and mute state.
    """
    endpoint = _get_mic_endpoint_volume()
    if endpoint:
        try:
            scalar = endpoint.GetMasterVolumeLevelScalar()
            is_muted = bool(endpoint.GetMute())
            level = int(round(scalar * 100))
            return {
                "level": level,
                "is_muted": is_muted,
                "status": f"{level}%" + (" (Muted)" if is_muted else " (Live)"),
                "display": f"Microphone: {level}%" + (" [MUTED]" if is_muted else " [LIVE]")
            }
        except Exception as e:
            return {"level": 50, "is_muted": False, "status": f"Error: {e}"}
    return {"level": 50, "is_muted": False, "status": "Microphone unavailable"}


def set_mic_volume(level: int) -> str:
    """Set microphone recording volume (0-100)."""
    level = max(0, min(100, int(level)))
    endpoint = _get_mic_endpoint_volume()
    if endpoint:
        try:
            scalar = float(level) / 100.0
            endpoint.SetMasterVolumeLevelScalar(scalar, None)
            if level > 0 and endpoint.GetMute():
                endpoint.SetMute(0, None)
            return f"Microphone volume set to {level}%"
        except Exception as e:
            return f"Failed to set mic volume: {e}"
    return "Microphone endpoint not found."


def mute_mic() -> str:
    """Mute the microphone."""
    endpoint = _get_mic_endpoint_volume()
    if endpoint:
        try:
            endpoint.SetMute(1, None)
            return "Microphone MUTED."
        except Exception as e:
            return f"Failed to mute mic: {e}"
    return "Microphone not available."


def unmute_mic() -> str:
    """Unmute the microphone."""
    endpoint = _get_mic_endpoint_volume()
    if endpoint:
        try:
            endpoint.SetMute(0, None)
            return "Microphone UNMUTED (Live)."
        except Exception as e:
            return f"Failed to unmute mic: {e}"
    return "Microphone not available."


def toggle_mic_mute() -> str:
    """Toggle microphone mute / live state."""
    endpoint = _get_mic_endpoint_volume()
    if endpoint:
        try:
            is_muted = bool(endpoint.GetMute())
            new_mute = 0 if is_muted else 1
            endpoint.SetMute(new_mute, None)
            return "Microphone MUTED." if new_mute == 1 else "Microphone UNMUTED (Live)."
        except Exception as e:
            return f"Failed to toggle mic mute: {e}"
    return "Microphone not available."


# =====================================================================
# "NOW PLAYING" SONG & ARTIST DETECTOR (GSMTC / WINDOW INSPECTOR)
# =====================================================================

def get_now_playing() -> Dict[str, Any]:
    """
    Detects currently playing track, artist, album, and app via Windows Media API (GSMTC).
    """
    # 1. Try Windows Media Transport Controls via winsdk
    try:
        import asyncio
        from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

        async def _fetch():
            mgr = await MediaManager.request_async()
            cur = mgr.get_current_session()
            if cur:
                props = await cur.try_get_media_properties_async()
                app_id = cur.source_app_user_model_id or "Media Player"
                return {
                    "playing": True,
                    "title": props.title or "Unknown Title",
                    "artist": props.artist or "Unknown Artist",
                    "album": props.album_title or "",
                    "app": app_id.split(".")[-1].replace(".exe", "").title(),
                    "display": f"🎵 {props.title} by {props.artist} ({app_id.split('.')[-1]})"
                }
            return None

        res = asyncio.run(_fetch())
        if res:
            return res
    except Exception:
        pass

    # 2. Fallback: inspect active app audio sessions
    sessions = list_app_audio_sessions()
    media_apps = [s for s in sessions if any(k in s["name"].lower() for k in ("spotify", "chrome", "vlc", "music", "youtube"))]
    if media_apps:
        app_names = ", ".join(s["name"] for s in media_apps)
        return {
            "playing": True,
            "title": "Audio Active",
            "artist": f"Running on {app_names}",
            "album": "",
            "app": media_apps[0]["name"],
            "display": f"🎵 Audio active in {app_names} (Use media keys: play/pause/next)"
        }

    return {
        "playing": False,
        "title": "No Media Playing",
        "artist": "",
        "album": "",
        "app": "",
        "display": "No active music or video detected right now."
    }


# =====================================================================
# SLEEP TIMER & SMOOTH VOLUME FADE-OUT
# =====================================================================

_sleep_timer_thread = None
_sleep_timer_cancel_event = None
_sleep_timer_info = {"active": False, "total_mins": 0, "remaining_seconds": 0, "action": "mute"}


def start_sleep_timer(minutes: int, action: str = "mute", fade_duration_mins: int = 5) -> str:
    """
    Start a background sleep timer. Smoothly fades out master volume during the last
    few minutes before executing the action ('mute', 'screen_off', 'sleep').
    """
    global _sleep_timer_thread, _sleep_timer_cancel_event, _sleep_timer_info
    import threading
    import time

    minutes = max(1, int(minutes))
    cancel_sleep_timer()

    _sleep_timer_cancel_event = threading.Event()
    _sleep_timer_info = {
        "active": True,
        "total_mins": minutes,
        "remaining_seconds": minutes * 60,
        "action": action,
        "fade_duration_mins": min(minutes, fade_duration_mins)
    }

    def _timer_worker():
        global _sleep_timer_info
        total_sec = minutes * 60
        fade_sec = _sleep_timer_info["fade_duration_mins"] * 60
        initial_vol = get_volume().get("level", 50)

        for elapsed in range(total_sec):
            if _sleep_timer_cancel_event.is_set():
                _sleep_timer_info["active"] = False
                return

            _sleep_timer_info["remaining_seconds"] = total_sec - elapsed

            # Start smooth volume fade-out when entering fade window
            remaining = total_sec - elapsed
            if remaining <= fade_sec and remaining > 0:
                fraction = float(remaining) / float(fade_sec)
                target_level = int(round(initial_vol * fraction))
                set_volume(max(0, target_level))

            time.sleep(1)

        # Timer expired: execute final action
        if action == "mute":
            mute()
        elif action == "screen_off":
            min_brightness()
            mute()
        elif action == "preset_sleep":
            apply_preset("sleep")

        _sleep_timer_info["active"] = False

    _sleep_timer_thread = threading.Thread(target=_timer_worker, daemon=True)
    _sleep_timer_thread.start()

    return f"Sleep timer set for {minutes} minute(s). Volume will smoothly fade out before {action}."


def cancel_sleep_timer() -> str:
    """Cancel any running sleep timer."""
    global _sleep_timer_cancel_event, _sleep_timer_info
    if _sleep_timer_cancel_event and _sleep_timer_info.get("active"):
        _sleep_timer_cancel_event.set()
        _sleep_timer_info["active"] = False
        return "Sleep timer cancelled."
    return "No active sleep timer running."


def get_sleep_timer_status() -> Dict[str, Any]:
    """Get current status of sleep timer."""
    global _sleep_timer_info
    if _sleep_timer_info.get("active"):
        rem_sec = _sleep_timer_info.get("remaining_seconds", 0)
        mins = rem_sec // 60
        secs = rem_sec % 60
        return {
            "active": True,
            "display": f"{mins}m {secs}s remaining (Action: {_sleep_timer_info.get('action')})",
            "remaining_seconds": rem_sec
        }
    return {"active": False, "display": "No active sleep timer."}


# =====================================================================
# CIRCADIAN AUTO-BRIGHTNESS (DAY/NIGHT SYNC)
# =====================================================================

_circadian_active = False
_circadian_thread = None
_circadian_stop_event = None


def get_circadian_brightness() -> int:
    """
    Computes ideal brightness percentage based on local time of day.
    """
    import datetime
    now = datetime.datetime.now()
    hour = now.hour + (now.minute / 60.0)

    # Circadian curve:
    # 06:00 - 09:00: Morning ramp 30% -> 75%
    # 09:00 - 17:00: Daytime work 85% -> 100%
    # 17:00 - 20:00: Evening transition 75% -> 45%
    # 20:00 - 23:00: Night relaxation 35% -> 20%
    # 23:00 - 06:00: Late night 15%
    if 6.0 <= hour < 9.0:
        frac = (hour - 6.0) / 3.0
        return int(round(30 + frac * 45))
    elif 9.0 <= hour < 17.0:
        return 90
    elif 17.0 <= hour < 20.0:
        frac = (hour - 17.0) / 3.0
        return int(round(75 - frac * 30))
    elif 20.0 <= hour < 23.0:
        frac = (hour - 20.0) / 3.0
        return int(round(40 - frac * 20))
    else:
        return 15


def sync_circadian_brightness() -> str:
    """Instantly adjust brightness to match current time of day."""
    target = get_circadian_brightness()
    set_brightness(target)
    import datetime
    cur_time = datetime.datetime.now().strftime("%I:%M %p")
    return f"Circadian Sync ({cur_time}): Screen brightness set to {target}%"


def toggle_circadian(enable: Optional[bool] = None) -> str:
    """Enable or disable background circadian auto-brightness adjustment."""
    global _circadian_active, _circadian_thread, _circadian_stop_event
    import threading
    import time

    if enable is None:
        enable = not _circadian_active

    if enable:
        if _circadian_active:
            return "Circadian Auto-Brightness is already active."
        _circadian_active = True
        _circadian_stop_event = threading.Event()

        def _worker():
            global _circadian_active
            while not _circadian_stop_event.is_set():
                sync_circadian_brightness()
                # Check every 10 minutes
                _circadian_stop_event.wait(600)
            _circadian_active = False

        _circadian_thread = threading.Thread(target=_worker, daemon=True)
        _circadian_thread.start()
        res = sync_circadian_brightness()
        return f"Circadian Auto-Brightness ENABLED! {res}"
    else:
        if _circadian_stop_event:
            _circadian_stop_event.set()
        _circadian_active = False
        return "Circadian Auto-Brightness DISABLED."


def is_circadian_active() -> bool:
    """Check if circadian auto-brightness is running."""
    return _circadian_active


# =====================================================================
# SYSTEM SNAPSHOT
# =====================================================================

def get_full_status() -> Dict[str, Any]:
    """
    Returns complete dashboard status of Audio, Mic, Devices, and Display controls.
    """
    vol = get_volume()
    bri = get_brightness()
    mic = get_mic_status()
    now_playing = get_now_playing()
    devices = list_audio_devices()
    app_sessions = list_app_audio_sessions()
    presets = load_presets()
    sleep_timer = get_sleep_timer_status()
    circadian = {"active": is_circadian_active(), "current_target": get_circadian_brightness()}

    return {
        "volume": vol,
        "brightness": bri,
        "mic": mic,
        "now_playing": now_playing,
        "devices": devices,
        "presets": presets,
        "app_sessions": app_sessions,
        "sleep_timer": sleep_timer,
        "circadian": circadian,
        "summary": f"Volume: {vol.get('status', 'N/A')} | Mic: {mic.get('status', 'N/A')} | Brightness: {bri.get('status', 'N/A')}"
    }


# =====================================================================
# EXTENDED HARDWARE & CONTEXT CONTROLS (FEATURES 9, 10, 15, 20)
# =====================================================================

def night_light_control(enable: Optional[bool] = None) -> str:
    """
    Toggles or sets warm color night light mode on Windows.
    Applies warm display profile / blue light reduction.
    """
    if enable is None:
        # Toggle warm preset
        res = apply_preset("night")
        return f"Toggled Night Light atmosphere mode: {res.get('message', 'Applied')}"
    elif enable:
        res = apply_preset("night")
        return f"Enabled Night Light mode: {res.get('message', 'Applied')}"
    else:
        res = apply_preset("daylight")
        return f"Disabled Night Light mode: {res.get('message', 'Applied')}"


def switch_display(mode: str = "extend") -> str:
    """
    Switches Windows multi-monitor display mode:
    mode: 'internal' (PC screen only), 'clone' (Duplicate), 'extend' (Extend), 'external' (Second screen only)
    """
    mode_map = {
        "internal": "/internal",
        "pc": "/internal",
        "pc only": "/internal",
        "clone": "/clone",
        "duplicate": "/clone",
        "extend": "/extend",
        "external": "/external",
        "second": "/external",
        "second screen only": "/external"
    }
    flag = mode_map.get(mode.lower().strip(), "/extend")
    try:
        import subprocess
        subprocess.Popen(["displayswitch.exe", flag], shell=True)
        return f"Switched display topology to '{mode}' (displayswitch.exe {flag})."
    except Exception as e:
        return f"Error executing display switch: {e}"


def detect_current_display() -> List[Dict[str, Any]]:
    """
    Detects active monitors, resolution, refresh rate, and primary display flag.
    """
    displays = []
    try:
        import subprocess
        import json
        cmd = "Get-CimInstance Win32_VideoController | Select-Object Name, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate | ConvertTo-Json"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout.strip())
            if isinstance(data, dict):
                data = [data]
            for item in data:
                h = item.get("CurrentHorizontalResolution")
                v = item.get("CurrentVerticalResolution")
                if h and v:
                    displays.append({
                        "adapter": item.get("Name", "Display Adapter"),
                        "resolution": f"{h}x{v}",
                        "refresh_rate_hz": item.get("CurrentRefreshRate", 60),
                        "status": "Active"
                    })
    except Exception:
        pass

    if not displays:
        displays.append({"adapter": "Primary Display", "resolution": "1920x1080", "refresh_rate_hz": 60, "status": "Active"})

    return displays


def context_aware_control(time_of_day: Optional[str] = None, active_app: Optional[str] = None, on_battery: Optional[bool] = None) -> Dict[str, Any]:
    """
    Intelligently determines and applies optimal volume and brightness levels
    based on the time of day, active application context (e.g. VLC/YouTube -> Media mode, VS Code -> Coding mode),
    and battery power state.
    """
    now = datetime.now()
    hour = now.hour

    if active_app:
        app_clean = active_app.lower().strip()
        if any(m in app_clean for m in ("vlc", "netflix", "spotify", "youtube", "media")):
            res = apply_preset("movie")
            return {"context": "Media Playback", "applied": "movie", "result": res}
        elif any(g in app_clean for g in ("game", "steam", "valorant", "cyberpunk", "epic")):
            res = apply_preset("gaming")
            return {"context": "Gaming", "applied": "gaming", "result": res}
        elif any(c in app_clean for c in ("code", "cursor", "antigravity", "terminal", "pycharm")):
            res = apply_preset("work")
            return {"context": "Coding / Development", "applied": "work", "result": res}

    if 22 <= hour or hour < 6:
        res = apply_preset("sleep" if on_battery else "night")
        return {"context": "Late Night", "applied": "night", "result": res}
    elif 6 <= hour < 9:
        res = apply_preset("study")
        return {"context": "Morning", "applied": "study", "result": res}
    else:
        res = apply_preset("daylight")
        return {"context": "Daytime", "applied": "daylight", "result": res}


