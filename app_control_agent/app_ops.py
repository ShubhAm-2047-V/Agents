"""
app_ops.py
Low-level Windows app/window control. No AI calls here - pure Python.

Requires (on Windows):
    pip install pywin32 psutil pygetwindow
"""

import os
import re
import subprocess
import time
import psutil
try:
    from . import config
except ImportError:
    import config

try:
    import win32gui
    import win32process
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import pygetwindow as gw
    HAS_GW = True
except ImportError:
    HAS_GW = False


# Common aliases and executable mappings on Windows
KNOWN_PROCESS_MAPPINGS = {
    "notepad": ["notepad.exe", "notepad"],
    "note pad": ["notepad.exe", "notepad"],
    "notes": ["notepad.exe", "notepad"],
    "calculator": ["calc.exe", "calculatorapp.exe", "calculator.exe", "calc"],
    "calc": ["calc.exe", "calculatorapp.exe", "calculator.exe", "calc"],
    "chrome": ["chrome.exe", "chrome"],
    "google chrome": ["chrome.exe", "chrome"],
    "browser": ["chrome.exe", "msedge.exe", "brave.exe", "firefox.exe"],
    "my browser": ["chrome.exe", "msedge.exe", "brave.exe", "firefox.exe"],
    "edge": ["msedge.exe", "msedge"],
    "msedge": ["msedge.exe", "msedge"],
    "brave": ["brave.exe", "brave"],
    "firefox": ["firefox.exe", "firefox"],
    "vscode": ["code.exe", "code"],
    "vs code": ["code.exe", "code"],
    "code": ["code.exe", "code", "antigravity.exe", "antigravity"],
    "antigravity": ["antigravity.exe", "antigravity ide.exe", "antigravity"],
    "antigravity ide": ["antigravity.exe", "antigravity ide.exe", "antigravity"],
    "editor": ["antigravity.exe", "antigravity ide.exe", "code.exe", "antigravity", "code"],
    "code editor": ["antigravity.exe", "antigravity ide.exe", "code.exe", "antigravity", "code"],
    "ide": ["antigravity.exe", "antigravity ide.exe", "code.exe", "antigravity", "code"],
    "cmd": ["cmd.exe", "windowsterminal.exe"],
    "terminal": ["cmd.exe", "windowsterminal.exe", "powershell.exe", "pwsh.exe"],
    "command prompt": ["cmd.exe", "windowsterminal.exe"],
    "prompt": ["cmd.exe", "windowsterminal.exe"],
    "powershell": ["powershell.exe", "pwsh.exe"],
    "power shell": ["powershell.exe", "pwsh.exe"],
    "git bash": ["git-bash.exe", "bash.exe"],
    "task manager": ["taskmgr.exe", "taskmgr"],
    "taskmgr": ["taskmgr.exe", "taskmgr"],
    "spotify": ["spotify.exe", "spotify"],
    "discord": ["discord.exe", "discord"],
    "whatsapp": ["whatsapp.exe", "whatsapp.root.exe", "whatsapp"],
    "whats app": ["whatsapp.exe", "whatsapp.root.exe", "whatsapp"],
    "postman": ["postman.exe", "postman"],
    "post man": ["postman.exe", "postman"],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "files": ["explorer.exe"],
    "file": ["explorer.exe"],
    "youtube": ["youtube", "you tube"],
    "you tube": ["youtube", "you tube"],
    "chatgpt": ["chatgpt.exe", "chatgpt", "chat gpt"],
    "chat gpt": ["chatgpt.exe", "chatgpt", "chat gpt"],
    "chat": ["chatgpt.exe", "chatgpt", "chat gpt"],
}


def resolve_app_name(name):
    """Look up a friendly name in APP_ALIASES, fall back to the raw name."""
    clean = str(name).lower().strip()
    if clean in config.APP_ALIASES:
        return config.APP_ALIASES[clean]
    no_spaces = clean.replace(" ", "")
    if no_spaces in config.APP_ALIASES:
        return config.APP_ALIASES[no_spaces]
    return name


def get_search_candidates(name):
    """
    Returns a set of search tokens (lowercase) for matching process names,
    exe names, and window titles.
    """
    raw = str(name).strip().lower()
    candidates = set()

    # Clean prefixes
    clean_raw = re.sub(r"^(?:close|shut\s*down|kill|exit|terminate|stop|switch\s+to|focus\s+on|open|launch|start|run|to)\s+", "", raw).strip()
    clean_raw = re.sub(r"^(?:my|the|a|an)\s+", "", clean_raw).strip()
    
    tokens_to_check = [clean_raw]
    no_spaces = clean_raw.replace(" ", "")
    if no_spaces and no_spaces != clean_raw:
        tokens_to_check.append(no_spaces)

    for tok in tokens_to_check:
        if not tok:
            continue
        candidates.add(tok)
        if not tok.endswith(".exe"):
            candidates.add(f"{tok}.exe")

        # Check KNOWN_PROCESS_MAPPINGS
        if tok in KNOWN_PROCESS_MAPPINGS:
            for item in KNOWN_PROCESS_MAPPINGS[tok]:
                candidates.add(item.lower())

        # Check APP_ALIASES in config
        alias_target = config.APP_ALIASES.get(tok, "")
        if alias_target:
            if not alias_target.startswith("hotkey:"):
                exe_match = re.search(r'([a-zA-Z0-9_\-\.]+\.exe)', alias_target, re.IGNORECASE)
                if exe_match:
                    exe_name = exe_match.group(1).lower()
                    candidates.add(exe_name)
                    candidates.add(exe_name.replace(".exe", ""))
                else:
                    target_clean = alias_target.strip().lower()
                    candidates.add(target_clean)
                    if not target_clean.endswith(".exe"):
                        candidates.add(f"{target_clean}.exe")

    return candidates


def get_all_open_windows():
    """
    Returns a list of dicts: [{'hwnd': ..., 'title': ..., 'pid': ...}]
    Uses win32gui first, with fallback to pygetwindow.
    """
    windows = []
    if HAS_WIN32:
        try:
            def enum_cb(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and title.strip():
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        windows.append({"hwnd": hwnd, "title": title.strip(), "pid": pid})

            win32gui.EnumWindows(enum_cb, None)
        except Exception:
            pass

    if not windows and HAS_GW:
        try:
            for w in gw.getAllWindows():
                if w.title and w.title.strip():
                    windows.append({"hwnd": getattr(w, "_hWnd", None), "title": w.title.strip(), "pid": None, "_win": w})
        except Exception:
            pass

    return windows


def activate_window_info(win_info):
    """Brings a window to the foreground and restores if minimized."""
    hwnd = win_info.get("hwnd")
    if hwnd and HAS_WIN32:
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            pass

    if "_win" in win_info:
        try:
            w = win_info["_win"]
            if w.isMinimized:
                w.restore()
            w.activate()
            return True
        except Exception:
            pass

    return False


def open_via_windows_search(name, wait_search=0.5, wait_enter=0.6):
    """
    Opens an application by pressing Windows Key, typing the app name
    into Windows Search, and hitting Enter.
    """
    import ctypes

    user32 = ctypes.windll.user32
    VK_LWIN = 0x5B
    VK_RETURN = 0x0D
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004

    # 1. Press and release Windows Key
    user32.keybd_event(VK_LWIN, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

    # 2. Wait for Windows Search / Start Menu to open & focus
    time.sleep(wait_search)

    # 3. Type app name character by character
    for char in str(name):
        code = ord(char)
        user32.keybd_event(0, code, KEYEVENTF_UNICODE, 0)
        time.sleep(0.01)
        user32.keybd_event(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0)
        time.sleep(0.02)

    # 4. Wait for search results to highlight the top match
    time.sleep(wait_enter)

    # 5. Press and release Enter to launch
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)

    return f"Searched '{name}' in Windows Search and launched."


def send_hotkey(hotkey_str):
    """
    Simulates pressing a hotkey like 'ctrl+alt+a' or 'win+s' or 'ctrl+shift+esc'.
    """
    import ctypes
    user32 = ctypes.windll.user32

    KEY_MAP = {
        "ctrl": 0x11,
        "control": 0x11,
        "alt": 0x12,
        "shift": 0x10,
        "win": 0x5B,
        "enter": 0x0D,
        "esc": 0x1B,
        "tab": 0x09,
        "space": 0x20
    }

    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    vk_codes = []
    for p in parts:
        if p in KEY_MAP:
            vk_codes.append(KEY_MAP[p])
        elif len(p) == 1:
            vk_codes.append(ord(p.upper()))

    # Press down in order
    for vk in vk_codes:
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.02)

    time.sleep(0.05)

    # Release in reverse order
    for vk in reversed(vk_codes):
        user32.keybd_event(vk, 0, 0x0002, 0)  # KEYEVENTF_KEYUP
        time.sleep(0.02)

    return f"Triggered hotkey: {hotkey_str}"


def open_app(name, use_search=None, auto_switch=True):
    """
    Smart Open:
    1. If auto_switch=True and window is already open, brings it to foreground instantly (Zero duplicate apps!).
    2. If not open (or is a hotkey shortcut), launches it.
    """
    raw_target = resolve_app_name(name)

    # 1. Hotkey trigger (e.g. ChatGPT on Ctrl+Alt+A or YouTube on Ctrl+Alt+X)
    if isinstance(raw_target, str) and raw_target.lower().startswith("hotkey:"):
        hotkey = raw_target.split(":", 1)[1].strip()
        return send_hotkey(hotkey)

    # 2. Smart Auto-Switch: check if matching window is already open
    if auto_switch:
        candidates = get_search_candidates(name)
        open_windows = get_all_open_windows()
        for win in open_windows:
            w_title = win["title"]
            w_title_lower = w_title.lower()
            for cand in candidates:
                c_clean = cand.replace(".exe", "") if cand.endswith(".exe") else cand
                if len(c_clean) >= 3 and c_clean in w_title_lower:
                    if activate_window_info(win):
                        return f"Switched to open window: {w_title}"

    # 3. Command line with flags or url
    if isinstance(raw_target, str) and ("--" in raw_target or "http" in raw_target):
        try:
            subprocess.Popen(raw_target, shell=True)
            return f"Launched: {name}"
        except Exception:
            pass

    # 4. Direct executable path if exists
    if isinstance(raw_target, str) and os.path.exists(raw_target):
        try:
            os.startfile(raw_target)
            return f"Opened {raw_target}"
        except Exception:
            pass

    # 5. Use Windows Search as primary smart launcher
    if use_search is None:
        use_search = getattr(config, "USE_WINDOWS_SEARCH_LAUNCHER", True)

    if use_search:
        try:
            return open_via_windows_search(name)
        except Exception:
            pass

    # Fallback to subprocess
    try:
        subprocess.Popen(raw_target, shell=True)
        return f"Opened {raw_target}"
    except Exception as e:
        raise FileNotFoundError(f"Could not find or launch '{name}'. Error: {e}")


def is_running(name):
    """Check if a process matching the given app name or alias is currently running."""
    candidates = get_search_candidates(name)
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            pname = (proc.info["name"] or "").lower()
            pexe = (proc.info["exe"] or "").lower()
            for c in candidates:
                if c == pname or c == pexe or (len(c) >= 3 and c in pname):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def list_running_apps():
    """Return a list of currently running process names (deduplicated)."""
    names = set()
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"]:
                names.add(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(names)


def close_window_by_title(title_contains):
    """
    Attempts to close visible windows matching the given title or candidate tokens.
    Returns the list of closed window titles.
    """
    closed_titles = []
    candidates = get_search_candidates(title_contains)
    open_windows = get_all_open_windows()

    for win in open_windows:
        w_title = win["title"]
        w_title_lower = w_title.lower()
        matched = False
        for c in candidates:
            c_clean = c.replace(".exe", "") if cand.endswith(".exe") else cand
            if len(c_clean) >= 3 and c_clean in w_title_lower:
                matched = True
                break
        if matched:
            hwnd = win.get("hwnd")
            if hwnd and HAS_WIN32:
                try:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    closed_titles.append(w_title)
                except Exception:
                    pass
            elif "_win" in win:
                try:
                    win["_win"].close()
                    closed_titles.append(w_title)
                except Exception:
                    pass

    return closed_titles


def close_app(name, force=True):
    """
    Closes all processes and/or open windows matching the given app name.
    1. Checks open windows and closes matching windows first (graceful).
    2. Identifies matching running processes and terminates/kills them.
    Refuses to close anything in PROTECTED_PROCESSES.
    """
    candidates = get_search_candidates(name)

    # Check protected processes
    for cand in candidates:
        if cand in config.PROTECTED_PROCESSES:
            raise PermissionError(f"Refusing to close protected system process: {cand}")

    closed_procs = set()
    closed_windows = []

    # 1. Try closing visible matching window(s) first
    try:
        closed_windows = close_window_by_title(name)
    except Exception:
        pass

    # 2. Match and kill processes via psutil
    target_procs = []
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            pname = (proc.info["name"] or "").lower()
            pexe = (proc.info["exe"] or "").lower()
            
            # Skip protected processes
            if pname in config.PROTECTED_PROCESSES:
                continue

            matched = False
            for cand in candidates:
                if cand == pname or cand == pexe:
                    matched = True
                    break
                elif len(cand) >= 3 and (cand in pname or (pexe and cand in os.path.basename(pexe))):
                    matched = True
                    break

            if matched:
                target_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    for proc in target_procs:
        try:
            proc_name = proc.name()
            # Kill children processes first
            try:
                children = proc.children(recursive=True)
                for child in children:
                    try:
                        child.kill()
                    except Exception:
                        pass
            except Exception:
                pass

            if force:
                proc.kill()
            else:
                proc.terminate()
            closed_procs.add(proc_name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            pass

    # 3. Fallback taskkill
    if not closed_procs and not closed_windows:
        for cand in candidates:
            if cand.endswith(".exe") and cand not in config.PROTECTED_PROCESSES:
                try:
                    res = subprocess.run(
                        f"taskkill /F /IM {cand}",
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    if "SUCCESS" in res.stdout or "terminated" in res.stdout:
                        closed_procs.add(cand)
                except Exception:
                    pass

    results_summary = []
    if closed_procs:
        results_summary.append(f"Terminated processes: {', '.join(closed_procs)}")
    if closed_windows:
        results_summary.append(f"Closed windows: {', '.join(closed_windows)}")

    if not results_summary:
        return f"No running application or window matching '{name}' was found."
    return "; ".join(results_summary)


def list_open_windows():
    """
    Returns a list of visible window titles.
    """
    windows = get_all_open_windows()
    return [w["title"] for w in windows]


def switch_to_window(title_contains):
    """
    Brings the first window whose title contains the given substring or candidate to foreground.
    If no window is open, automatically opens/launches it or triggers its hotkey!
    """
    candidates = get_search_candidates(title_contains)
    open_windows = get_all_open_windows()

    for win in open_windows:
        w_title = win["title"]
        w_title_lower = w_title.lower()
        for cand in candidates:
            c_clean = cand.replace(".exe", "") if cand.endswith(".exe") else cand
            if len(c_clean) >= 3 and c_clean in w_title_lower:
                if activate_window_info(win):
                    return f"Switched to: {w_title}"

    # If no window title matched, check if app target is a hotkey (e.g. ChatGPT on Ctrl+Alt+A)
    alias = config.APP_ALIASES.get(title_contains.lower().strip(), "")
    if not alias:
        no_spaces = title_contains.lower().replace(" ", "").strip()
        alias = config.APP_ALIASES.get(no_spaces, "")

    if alias.startswith("hotkey:"):
        hotkey = alias.split(":", 1)[1].strip()
        send_hotkey(hotkey)
        return f"Focused {title_contains} via shortcut ({hotkey})"

    # Auto-launch if not open
    return open_app(title_contains, auto_switch=False)


def minimize_window(title_contains):
    """Minimizes matching window(s)."""
    candidates = get_search_candidates(title_contains)
    open_windows = get_all_open_windows()
    minimized = []

    for win in open_windows:
        w_title = win["title"]
        w_title_lower = w_title.lower()
        for cand in candidates:
            c_clean = cand.replace(".exe", "") if cand.endswith(".exe") else cand
            if len(c_clean) >= 3 and c_clean in w_title_lower:
                hwnd = win.get("hwnd")
                if hwnd and HAS_WIN32:
                    try:
                        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                        minimized.append(w_title)
                    except Exception:
                        pass
                elif "_win" in win:
                    try:
                        win["_win"].minimize()
                        minimized.append(w_title)
                    except Exception:
                        pass
                break

    if not minimized:
        return f"No open window matching '{title_contains}'"
    return f"Minimized: {', '.join(minimized)}"


def get_screen_work_area():
    """Returns (start_x, start_y, width, height) of primary monitor work area (excluding taskbar)."""
    import ctypes
    user32 = ctypes.windll.user32
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    rect = RECT()
    SPI_GETWORKAREA = 0x0030
    if user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        return rect.left, rect.top, w, h
    else:
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        return 0, 0, w, h


def find_window_by_app(name, auto_launch=True):
    """
    Finds the window dict {'hwnd': ..., 'title': ...} for an app.
    If not currently open and auto_launch=True, launches it or sends shortcut, waits, and finds it.
    """
    candidates = get_search_candidates(name)
    open_windows = get_all_open_windows()

    for win in open_windows:
        w_title_lower = win["title"].lower()
        for cand in candidates:
            c_clean = cand.replace(".exe", "") if cand.endswith(".exe") else cand
            if len(c_clean) >= 3 and c_clean in w_title_lower:
                return win

    if auto_launch:
        # Launch or trigger hotkey
        open_app(name, auto_switch=False)
        time.sleep(0.7)
        # Re-check open windows
        open_windows = get_all_open_windows()
        for win in open_windows:
            w_title_lower = win["title"].lower()
            for cand in candidates:
                c_clean = cand.replace(".exe", "") if cand.endswith(".exe") else cand
                if len(c_clean) >= 3 and c_clean in w_title_lower:
                    return win

    return None


def position_window(win_info, x, y, width, height):
    """Restores (if minimized/maximized) and moves window to specified rect."""
    hwnd = win_info.get("hwnd")
    if hwnd and HAS_WIN32:
        try:
            if win32gui.IsIconic(hwnd) or win32gui.GetWindowPlacement(hwnd)[1] == win32con.SW_SHOWMAXIMIZED:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            pass

    if "_win" in win_info:
        try:
            w = win_info["_win"]
            if w.isMinimized or w.isMaximized:
                w.restore()
            w.moveTo(x, y)
            w.resizeTo(width, height)
            w.activate()
            return True
        except Exception:
            pass

    return False


def tile_side_by_side(left_name, right_name):
    """
    Arranges two apps side by side (left half and right half of the screen).
    Automatically launches either app if not currently open.
    """
    start_x, start_y, total_w, total_h = get_screen_work_area()
    half_w = total_w // 2

    # 1. Find or launch left app
    left_win = find_window_by_app(left_name, auto_launch=True)
    # 2. Find or launch right app
    right_win = find_window_by_app(right_name, auto_launch=True)

    results = []
    if left_win:
        position_window(left_win, start_x, start_y, half_w, total_h)
        results.append(f"Positioned Left: {left_win['title']}")
    else:
        results.append(f"Could not locate window for '{left_name}'")

    if right_win:
        position_window(right_win, start_x + half_w, start_y, half_w, total_h)
        results.append(f"Positioned Right: {right_win['title']}")
    else:
        results.append(f"Could not locate window for '{right_name}'")

def maximize_app(name):
    """Restores (if needed) and maximizes the target window."""
    win = find_window_by_app(name, auto_launch=True)
    if not win:
        return f"Could not find or launch window for '{name}'"

    hwnd = win.get("hwnd")
    if hwnd and HAS_WIN32:
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            win32gui.SetForegroundWindow(hwnd)
            return f"Maximized: {win['title']}"
        except Exception:
            pass

    if "_win" in win:
        try:
            win["_win"].maximize()
            return f"Maximized: {win['title']}"
        except Exception:
            pass

    return f"Maximized '{name}'"


def snap_window(name, direction="left"):
    """
    Snaps window to 'left', 'right', 'top', 'bottom', 'top_left', 'top_right', 'bottom_left', 'bottom_right'.
    """
    win = find_window_by_app(name, auto_launch=True)
    if not win:
        return f"Could not find window for '{name}'"

    start_x, start_y, total_w, total_h = get_screen_work_area()
    half_w = total_w // 2
    half_h = total_h // 2
    d = direction.lower().strip()

    if d in ("left", "l"):
        x, y, w, h = start_x, start_y, half_w, total_h
    elif d in ("right", "r"):
        x, y, w, h = start_x + half_w, start_y, half_w, total_h
    elif d in ("top", "t"):
        x, y, w, h = start_x, start_y, total_w, half_h
    elif d in ("bottom", "b"):
        x, y, w, h = start_x, start_y + half_h, total_w, half_h
    elif d in ("top_left", "tl"):
        x, y, w, h = start_x, start_y, half_w, half_h
    elif d in ("top_right", "tr"):
        x, y, w, h = start_x + half_w, start_y, half_w, half_h
    elif d in ("bottom_left", "bl"):
        x, y, w, h = start_x, start_y + half_h, half_w, half_h
    elif d in ("bottom_right", "br"):
        x, y, w, h = start_x + half_w, start_y + half_h, half_w, half_h
    else:
        x, y, w, h = start_x, start_y, half_w, total_h

    if position_window(win, x, y, w, h):
        return f"Snapped '{win['title']}' to {d.upper()}"
    return f"Failed to snap '{name}'"


def center_app(name, width_pct=0.75, height_pct=0.8):
    """Centers the target window on the screen with a clean proportional size."""
    win = find_window_by_app(name, auto_launch=True)
    if not win:
        return f"Could not find window for '{name}'"

    start_x, start_y, total_w, total_h = get_screen_work_area()
    w = int(total_w * width_pct)
    h = int(total_h * height_pct)
    x = start_x + (total_w - w) // 2
    y = start_y + (total_h - h) // 2

    if position_window(win, x, y, w, h):
        return f"Centered '{win['title']}' ({w}x{h})"
    return f"Failed to center '{name}'"


def focus_only_app(name):
    """
    Solo / Focus Mode: Minimizes all other open windows and brings target window to front & center!
    """
    win = find_window_by_app(name, auto_launch=True)
    if not win:
        return f"Could not find window for '{name}'"

    target_hwnd = win.get("hwnd")
    open_windows = get_all_open_windows()
    minimized_count = 0

    for w in open_windows:
        hwnd = w.get("hwnd")
        if hwnd and hwnd != target_hwnd:
            if HAS_WIN32:
                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    minimized_count += 1
                except Exception:
                    pass

    # Center or maximize target
    center_app(name)
    return f"Solo Focus: Activated '{win['title']}' and minimized {minimized_count} other window(s)."


def minimize_all_windows():
    """Minimizes all windows to show the clean desktop."""
    return send_hotkey("win+d")


def tile_grid_4(app_tl, app_tr, app_bl, app_br):
    """
    4-Way Quadrant Grid Layout: Snaps 4 apps into the 4 corners of the screen.
    """
    start_x, start_y, total_w, total_h = get_screen_work_area()
    half_w = total_w // 2
    half_h = total_h // 2

    slots = [
        (app_tl, start_x, start_y, "Top-Left"),
        (app_tr, start_x + half_w, start_y, "Top-Right"),
        (app_bl, start_x, start_y + half_h, "Bottom-Left"),
        (app_br, start_x + half_w, start_y + half_h, "Bottom-Right"),
    ]

    results = []
    for app_name, x, y, label in slots:
        win = find_window_by_app(app_name, auto_launch=True)
        if win and position_window(win, x, y, half_w, half_h):
            results.append(f"{label}: {win['title']}")
        else:
            results.append(f"{label}: Could not place '{app_name}'")

    return " | ".join(results)


def tile_layout_3(app_main, app_tr, app_br):
    """
    3-Way Layout: Main app on Left (50% width, 100% height), and 2 apps stacked on Right.
    """
    start_x, start_y, total_w, total_h = get_screen_work_area()
    half_w = total_w // 2
    half_h = total_h // 2

    slots = [
        (app_main, start_x, start_y, half_w, total_h, "Left Main"),
        (app_tr, start_x + half_w, start_y, half_w, half_h, "Top-Right"),
        (app_br, start_x + half_w, start_y + half_h, half_w, half_h, "Bottom-Right"),
    ]

    results = []
    for app_name, x, y, w, h, label in slots:
        win = find_window_by_app(app_name, auto_launch=True)
        if win and position_window(win, x, y, w, h):
            results.append(f"{label}: {win['title']}")
        else:
            results.append(f"{label}: Could not place '{app_name}'")

    return " | ".join(results)


def wait_for_app(name, timeout=10):
    """Poll until an app appears running, or timeout (seconds) elapses."""
    start = time.time()
    while time.time() - start < timeout:
        if is_running(name):
            return True
        time.sleep(0.5)
    return False


# =====================================================================
# EXTENDED APP CONTROL FEATURES (ALL 20 FEATURES SUPPORT)
# =====================================================================

# In-memory registry for active dev servers
_DEV_SERVERS = {}


def restart_app(name, wait_sec=2):
    """Closes an application and restarts it after a short delay."""
    close_res = close_app(name, force=True)
    time.sleep(wait_sec)
    open_res = open_app(name)
    return f"Restarted '{name}': {close_res} -> {open_res}"


def find_installed_apps(query=""):
    """
    Scans Start Menu folders, Registry uninstall paths, and common directories
    to discover all installed applications on the Windows system.
    """
    found_apps = {}
    query_clean = query.strip().lower()

    # 1. Start Menu Shortcuts
    start_menu_paths = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs")
    ]

    for base_dir in start_menu_paths:
        if os.path.exists(base_dir):
            for root, _, files in os.walk(base_dir):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4]
                        full_path = os.path.join(root, f)
                        if not query_clean or query_clean in name.lower():
                            found_apps[name.lower()] = {
                                "name": name,
                                "type": "Shortcut",
                                "path": full_path
                            }

    # 2. Windows Registry Uninstall Keys
    try:
        import winreg
        uninstall_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        for hkey, subkey in uninstall_keys:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as app_key:
                                disp_name, _ = winreg.QueryValueEx(app_key, "DisplayName")
                                if disp_name:
                                    name_clean = disp_name.strip()
                                    if not query_clean or query_clean in name_clean.lower():
                                        loc = ""
                                        try:
                                            loc, _ = winreg.QueryValueEx(app_key, "InstallLocation")
                                        except Exception:
                                            pass
                                        found_apps[name_clean.lower()] = {
                                            "name": name_clean,
                                            "type": "Installed Software",
                                            "path": loc or "Registered Application"
                                        }
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass

    # Sort results
    results = sorted(found_apps.values(), key=lambda x: x["name"].lower())
    return results


def open_file_with_app(file_path, app_name=None):
    """Opens a specific file with its default application or a specified app."""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return f"File not found: '{file_path}'"

    if not app_name:
        try:
            os.startfile(abs_path)
            return f"Opened '{os.path.basename(abs_path)}' with default system application."
        except Exception as e:
            return f"Error opening file: {e}"
    else:
        resolved = resolve_app_name(app_name)
        try:
            subprocess.Popen([resolved, abs_path], shell=True)
            return f"Opened '{os.path.basename(abs_path)}' with '{app_name}'."
        except Exception as e:
            return f"Error opening with '{app_name}': {e}"


def open_folder(folder_path):
    """Opens Windows File Explorer at the specified folder path."""
    abs_path = os.path.abspath(folder_path)
    if not os.path.exists(abs_path):
        os.makedirs(abs_path, exist_ok=True)
    try:
        subprocess.Popen(["explorer.exe", abs_path])
        return f"Opened folder: {abs_path}"
    except Exception as e:
        return f"Error opening folder: {e}"


def launch_website(url_or_domain, browser=None):
    """Launches a website URL in the preferred or default browser."""
    url = url_or_domain.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    if browser:
        resolved = resolve_app_name(browser)
        try:
            subprocess.Popen(f'{resolved} "{url}"', shell=True)
            return f"Launched {url} in {browser}."
        except Exception:
            pass

    import webbrowser
    webbrowser.open(url)
    return f"Launched {url} in default browser."


def launch_dev_tool(tool_name):
    """
    Launches developer tools (VS Code, Cursor, Antigravity, Postman, Git Bash,
    Docker Desktop, Windows Terminal, PyCharm, etc.).
    """
    dev_tools_map = {
        "vscode": "code",
        "vs code": "code",
        "cursor": "cursor",
        "antigravity": "antigravity",
        "postman": "postman",
        "git bash": "git-bash",
        "terminal": "wt.exe",
        "windows terminal": "wt.exe",
        "docker": "Docker Desktop",
        "docker desktop": "Docker Desktop",
        "pycharm": "pycharm64.exe",
        "intellij": "idea64.exe",
        "dbeaver": "dbeaver",
        "sublime": "sublime_text.exe"
    }
    tool_key = tool_name.strip().lower()
    target = dev_tools_map.get(tool_key, tool_name)
    return open_app(target)


def open_project_in_ide(project_path, ide_name="code"):
    """Opens an IDE (VS Code, Cursor, Antigravity) loaded with a project folder."""
    abs_path = os.path.abspath(project_path)
    if not os.path.exists(abs_path):
        return f"Project path does not exist: {project_path}"

    ide_key = ide_name.strip().lower()
    if ide_key in ("code", "vscode", "vs code"):
        cmd = ["code", abs_path]
    elif ide_key in ("cursor",):
        cmd = ["cursor", abs_path]
    elif ide_key in ("antigravity",):
        cmd = ["antigravity", abs_path]
    else:
        cmd = [ide_name, abs_path]

    try:
        subprocess.Popen(cmd, shell=True)
        return f"Opened project '{os.path.basename(abs_path)}' in {ide_name}."
    except Exception as e:
        return f"Failed to open project in {ide_name}: {e}"


def start_dev_server(project_path, command="npm run dev", port=None):
    """Starts a development server in the background and tracks it."""
    abs_path = os.path.abspath(project_path)
    if not os.path.exists(abs_path):
        return {"success": False, "error": f"Path not found: {project_path}"}

    server_id = f"{os.path.basename(abs_path)}_{int(time.time())}"
    try:
        proc = subprocess.Popen(
            command,
            cwd=abs_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0
        )
        _DEV_SERVERS[server_id] = {
            "id": server_id,
            "project_path": abs_path,
            "command": command,
            "pid": proc.pid,
            "port": port,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "proc": proc
        }
        return {
            "success": True,
            "server_id": server_id,
            "pid": proc.pid,
            "command": command,
            "project_path": abs_path
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def stop_dev_server(server_id_or_pid):
    """Stops a running development server by its ID or PID."""
    target = str(server_id_or_pid)
    for sid, info in list(_DEV_SERVERS.items()):
        if sid == target or str(info.get("pid")) == target:
            try:
                proc = info.get("proc")
                if proc:
                    proc.terminate()
                ps_proc = psutil.Process(info["pid"])
                for child in ps_proc.children(recursive=True):
                    child.kill()
                ps_proc.kill()
            except Exception:
                pass
            del _DEV_SERVERS[sid]
            return f"Dev server '{sid}' (PID: {info['pid']}) stopped."

    # Fallback to kill by PID directly
    if target.isdigit():
        try:
            p = psutil.Process(int(target))
            p.kill()
            return f"Process PID {target} killed."
        except Exception as e:
            return f"Could not kill PID {target}: {e}"

    return f"No active dev server found matching '{server_id_or_pid}'."


def list_dev_servers():
    """Lists all active development servers tracked by this agent."""
    active = []
    for sid, info in list(_DEV_SERVERS.items()):
        pid = info.get("pid")
        is_alive = False
        try:
            p = psutil.Process(pid)
            if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                is_alive = True
        except Exception:
            is_alive = False

        if is_alive:
            active.append({
                "server_id": sid,
                "project": os.path.basename(info["project_path"]),
                "command": info["command"],
                "pid": pid,
                "started": info["start_time"]
            })
        else:
            del _DEV_SERVERS[sid]
    return active


def open_terminal(cwd=None, shell="powershell"):
    """Opens a Terminal or PowerShell prompt at the specified directory."""
    dir_path = os.path.abspath(cwd) if cwd else os.path.expanduser("~")
    shell_lower = shell.lower().strip()

    if shell_lower in ("powershell", "pwsh"):
        cmd = f'start powershell -NoExit -Command "Set-Location \'{dir_path}\'"'
    elif shell_lower in ("wt", "windows terminal", "windowsterminal"):
        cmd = f'start wt -d "{dir_path}"'
    else:
        cmd = f'start cmd /k "cd /d {dir_path}"'

    try:
        subprocess.Popen(cmd, shell=True)
        return f"Opened {shell} at '{dir_path}'."
    except Exception as e:
        return f"Error opening terminal: {e}"


def execute_safe_command(command_str, cwd=None, timeout=20):
    """
    Executes a predefined safe/whitelisted developer or system command.
    Blocks dangerous commands like format, del /f /s, rm -rf, drop table, etc.
    """
    cmd_clean = command_str.strip()
    first_token = cmd_clean.split()[0].lower() if cmd_clean else ""

    SAFE_COMMAND_PREFIXES = [
        "git status", "git branch", "git log", "git diff", "git pull",
        "npm -v", "npm --version", "npm list", "npm run",
        "node -v", "node --version",
        "python --version", "python -V", "pip list", "pip show",
        "docker ps", "docker images", "docker version",
        "ipconfig", "whoami", "hostname", "systeminfo", "netstat", "ping",
        "dir", "echo", "where", "tasklist"
    ]

    is_safe = any(cmd_clean.lower().startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES)
    if not is_safe:
        return {
            "success": False,
            "error": f"Command '{cmd_clean}' is not in the predefined safe commands whitelist. Confirmation required."
        }

    try:
        res = subprocess.run(
            cmd_clean,
            cwd=cwd or os.getcwd(),
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": res.returncode == 0,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "returncode": res.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout} seconds."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_startup_apps():
    """Lists applications configured to run at Windows startup."""
    startup_entries = []
    try:
        import winreg
        keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "CurrentUser"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "LocalMachine")
        ]
        for root, subkey, scope in keys:
            try:
                with winreg.OpenKey(root, subkey) as key:
                    count = winreg.QueryInfoKey(key)[1]
                    for i in range(count):
                        name, val, _ = winreg.EnumValue(key, i)
                        startup_entries.append({
                            "name": name,
                            "command": val,
                            "scope": scope
                        })
            except Exception:
                pass
    except Exception:
        pass

    # Also check user Startup folder
    startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
    if os.path.exists(startup_dir):
        for f in os.listdir(startup_dir):
            startup_entries.append({
                "name": f,
                "command": os.path.join(startup_dir, f),
                "scope": "StartupFolder"
            })

    return startup_entries


def detect_frozen_apps():
    """
    Detects unresponsive or frozen application windows using Windows API
    (IsHungAppWindow) and process telemetry.
    """
    frozen = []
    if HAS_WIN32:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            
            def enum_proc(hwnd, lparam):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if user32.IsHungAppWindow(hwnd):
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        try:
                            p = psutil.Process(pid)
                            pname = p.name()
                        except Exception:
                            pname = "Unknown"
                        frozen.append({
                            "hwnd": hwnd,
                            "title": title,
                            "pid": pid,
                            "process_name": pname
                        })
                return True

            win32gui.EnumWindows(enum_proc, None)
        except Exception:
            pass

    return frozen


def force_close_unresponsive_apps():
    """Finds and forcefully terminates all frozen/hung applications."""
    frozen = detect_frozen_apps()
    if not frozen:
        return "No frozen or unresponsive applications detected."

    closed = []
    for app in frozen:
        pid = app.get("pid")
        try:
            p = psutil.Process(pid)
            p.kill()
            closed.append(f"{app['title']} (PID: {pid})")
        except Exception as e:
            closed.append(f"Failed to kill PID {pid}: {e}")

    return f"Force-closed {len(closed)} frozen app(s): " + ", ".join(closed)


def open_workspace(app_list, layout=None):
    """
    Opens multiple applications simultaneously as a configured workspace
    and arranges them according to layout ('side_by_side', 'grid_4', 'tile_3', or 'default').
    """
    if isinstance(app_list, str):
        app_list = [a.strip() for a in app_list.split(",") if a.strip()]

    opened = []
    for app in app_list:
        res = open_app(app)
        opened.append(f"{app} ({res})")
        time.sleep(0.6)

    if layout == "side_by_side" and len(app_list) >= 2:
        tile_side_by_side(app_list[0], app_list[1])
    elif layout == "grid_4" and len(app_list) >= 4:
        tile_grid_4(app_list[0], app_list[1], app_list[2], app_list[3])
    elif layout == "tile_3" and len(app_list) >= 3:
        tile_layout_3(app_list[0], app_list[1], app_list[2])

    return f"Opened workspace with {len(opened)} app(s): " + ", ".join(opened)


_WORKSPACES_FILE = os.path.join(os.path.dirname(__file__), "data", "workspaces.json")


def _load_workspaces():
    if os.path.exists(_WORKSPACES_FILE):
        try:
            with open(_WORKSPACES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_workspaces_file(data):
    os.makedirs(os.path.dirname(_WORKSPACES_FILE), exist_ok=True)
    with open(_WORKSPACES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_project_workspace(name, apps=None, files=None, urls=None, folders=None, layout="side_by_side"):
    """Saves a project-specific workspace configuration to disk."""
    data = _load_workspaces()
    data[name.strip().lower()] = {
        "name": name.strip(),
        "apps": apps or [],
        "files": files or [],
        "urls": urls or [],
        "folders": folders or [],
        "layout": layout,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    _save_workspaces_file(data)
    return f"Project workspace '{name}' saved successfully."


def launch_project_workspace(name):
    """Loads and launches all apps, files, folders, and urls in a saved project workspace."""
    data = _load_workspaces()
    ws = data.get(name.strip().lower())
    if not ws:
        return f"Project workspace '{name}' not found. Available: {list(data.keys())}"

    actions = []
    # 1. Folders
    for folder in ws.get("folders", []):
        open_folder(folder)
        actions.append(f"Folder: {folder}")

    # 2. URLs
    for url in ws.get("urls", []):
        launch_website(url)
        actions.append(f"Web: {url}")

    # 3. Files
    for f in ws.get("files", []):
        open_file_with_app(f)
        actions.append(f"File: {f}")

    # 4. Apps & Layout
    apps = ws.get("apps", [])
    if apps:
        open_workspace(apps, layout=ws.get("layout"))
        actions.append(f"Apps: {', '.join(apps)}")

    return f"Launched workspace '{name}':\n • " + "\n • ".join(actions)


def get_running_apps_detailed():
    """
    Returns a comprehensive, real-time list of all running graphical and background
    applications with PID, Window Titles, Memory (MB), CPU %, and status.
    """
    tracked = []
    windows_map = {}
    for win in get_all_open_windows():
        pid = win.get("pid")
        if pid:
            windows_map.setdefault(pid, []).append(win.get("title", ""))

    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
        try:
            pid = proc.info['pid']
            pname = proc.info['name'] or ""
            # Filter out kernel/system idle
            if pid in (0, 4) or not pname:
                continue

            mem_mb = round(proc.info['memory_info'].rss / (1024 * 1024), 1) if proc.info.get('memory_info') else 0.0
            titles = windows_map.get(pid, [])
            
            # Keep apps with visible windows or substantial memory usage
            if titles or mem_mb > 25.0:
                tracked.append({
                    "pid": pid,
                    "name": pname,
                    "window_titles": titles,
                    "memory_mb": mem_mb,
                    "cpu_percent": proc.info.get('cpu_percent', 0.0),
                    "status": proc.info.get('status', 'running')
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    tracked.sort(key=lambda x: x["memory_mb"], reverse=True)
    return tracked


def confirm_dangerous_action(action_type, target, confirmed=False):
    """
    Safety gate: Checks whether an action (like force-closing critical processes or
    executing arbitrary shell commands) is dangerous, and enforces explicit confirmation.
    """
    target_clean = str(target).lower().strip()
    is_protected = target_clean in config.PROTECTED_PROCESSES or target_clean.endswith(".exe") and target_clean in config.PROTECTED_PROCESSES

    if is_protected:
        return {
            "allowed": False,
            "requires_confirmation": False,
            "message": f"Action BLOCKED: '{target}' is a protected Windows system process and cannot be terminated."
        }

    if not confirmed:
        return {
            "allowed": False,
            "requires_confirmation": True,
            "message": f"Confirmation Required: Are you sure you want to {action_type} '{target}'? (Pass confirmed=True to proceed)"
        }

    return {
        "allowed": True,
        "requires_confirmation": False,
        "message": f"Action confirmed for {action_type} on '{target}'."
    }



