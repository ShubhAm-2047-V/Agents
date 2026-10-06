# Orion App Control Agent

Open, close, switch between, and list apps/windows on Windows. Direct
control is pure Python (zero API cost) - only natural language command
parsing uses Gemini Flash-Lite.

## ⚠️ Safety first

- `close()` refuses to touch anything in `config.PROTECTED_PROCESSES`
  (explorer.exe, system processes, etc.) - don't remove these unless you
  really know what you're doing.
- `close()` matches by substring on process name, so double-check the
  target before calling it with `force=True` on something broad.
- `parse_command()` never executes actions itself - it only returns intent.
  Your router decides whether to run `execute_parsed_actions()`, and
  should confirm with you first for anything that closes apps.

## Setup

1. Copy this whole `app_control_agent` folder into `E:\Orion\`

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   (`pygetwindow` and `pywin32` are Windows-only - window switching won't
   work without them, but open/close still function via psutil.)

3. Add your free Gemini API key - either:
   - Set an environment variable `GEMINI_API_KEY`, OR
   - Paste it directly into `config.py`

4. Edit `APP_ALIASES` in `config.py` to match apps you actually use -
   add full paths if an exe isn't on your system PATH.

5. Test it:
   ```
   python test_app_control.py
   ```

## How it fits into Orion

```python
from app_control_agent import app_control_agent as apps

# Zero-cost, instant
apps.open("chrome")
apps.close("spotify")
apps.switch_to("notepad")
apps.list_running()

# AI-assisted (1 API call) - parses intent only, doesn't execute
parsed = apps.parse_command("close discord and open vs code")

# Your router confirms with user if needed, then:
results = apps.execute_parsed_actions(parsed)
```

## Files

| File | Purpose |
|---|---|
| `app_ops.py` | Pure app/window control - open/close/switch/list via psutil + pygetwindow |
| `app_control_agent.py` | AI layer - parses natural language into structured actions |
| `config.py` | API key, app name aliases, protected processes |
| `test_app_control.py` | Safe test script (destructive actions commented out) |

## Functions reference

**Zero-cost (no API call):**
- `open(name)` - launch an app by alias or exe name
- `close(name, force=False)` - terminate (or kill) matching processes
- `switch_to(title_contains)` - bring a window to foreground by partial title match
- `minimize(title_contains)` - minimize a window by partial title match
- `is_running(name)` - check if a process is active
- `list_running()` - list all running process names
- `list_windows()` - list all visible window titles

**AI-assisted (1 Gemini Flash-Lite call):**
- `parse_command(text)` - converts natural language into `{"actions": [...]}`
- `execute_parsed_actions(parsed)` - runs each action from a parsed result

## Quota notes

Only `parse_command()` touches the API. Everything else is instant local
Python via `psutil`/`pygetwindow` - safe to call as often as you like
without worrying about rate limits.
