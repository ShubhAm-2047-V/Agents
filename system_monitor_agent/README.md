# Orion System Monitor Agent

CPU, RAM, disk, battery, network, and process stats - all local via
`psutil`, zero API cost. The only AI-assisted piece is an on-demand
spoken-style summary using Gemini Flash-Lite.

## ⚠️ Quota design - read this before wiring into a loop

`check_alerts()` and `monitor_loop()` are **100% local** - they never call
Gemini, so it's safe to poll every few seconds continuously. Only
`get_spoken_summary()` touches the API, and it should be called **on
demand** (when the user asks "how's my PC doing"), never inside a
background polling loop - that would burn your daily quota fast for no
benefit, since raw numbers don't need AI to detect a threshold breach.

## Setup

1. Copy this whole `system_monitor_agent` folder into `E:\Orion\`

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Add your free Gemini API key - either:
   - Set an environment variable `GEMINI_API_KEY`, OR
   - Paste it directly into `config.py`

4. Adjust alert thresholds in `config.py` if the defaults (90% CPU/RAM/disk,
   20% battery) don't match what you want flagged.

5. Test it:
   ```
   python test_system_monitor.py
   ```

## How it fits into Orion

```python
from system_monitor_agent import system_monitor_agent as sysmon

# Zero-cost, call as often as you like
snap = sysmon.get_snapshot()
alerts = sysmon.check_alerts()

# Background monitoring - purely local, safe to run continuously
def handle_alert(alerts):
    for a in alerts:
        print("ALERT:", a)
        # e.g. trigger your TTS agent to speak this

sysmon.monitor_loop(on_alert=handle_alert, poll_interval=30)

# On-demand AI summary (1 API call) - only when the user actually asks
summary = sysmon.get_spoken_summary()
```

## Files

| File | Purpose |
|---|---|
| `system_stats.py` | Pure psutil stats collection - CPU/RAM/disk/battery/network/processes |
| `system_monitor_agent.py` | Alert checking, background loop, and on-demand AI summary |
| `config.py` | API key, alert thresholds, poll interval |
| `test_system_monitor.py` | Test script |

## Functions reference

**Zero-cost (no API call, safe to poll continuously):**
- `get_snapshot()` - everything at once (CPU, RAM, disk, battery, network, uptime, top processes)
- `get_cpu()`, `get_ram()`, `get_disk(path)`, `get_all_disks()`, `get_battery()`, `get_network()`, `get_uptime()`
- `get_top_processes(by="cpu"/"memory", limit=5)`
- `check_alerts()` - returns list of threshold-breach strings, empty if fine
- `monitor_loop(on_alert=callback, poll_interval=30)` - blocking background loop

**AI-assisted (1 Gemini Flash-Lite call):**
- `get_spoken_summary()` - natural language status report, call on-demand only

## Quota notes

This agent is designed so the expensive resource (API quota) is never
touched by anything that runs on a timer. Alerting, polling, and raw stats
are instant and free - call them as often as your loop needs. Only bring
Gemini in when a human actually wants a conversational answer.
