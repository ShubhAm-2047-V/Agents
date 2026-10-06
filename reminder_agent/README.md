# Orion Reminder/Scheduler Agent

Set one-time and recurring reminders/alarms. Storage and the checker loop
are pure local SQLite (zero API cost). The only AI-assisted piece is
parsing natural language ("remind me to call mom tomorrow at 5pm") into a
structured reminder.

## Setup

1. Copy this whole `reminder_agent` folder into `E:\Orion\`

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   (`win10toast` is optional - only needed if you set `NOTIFY_METHOD =
   "windows_toast"` in config.py for real Windows popup notifications.
   Default is console print, which needs nothing extra.)

3. Add your free Gemini API key - either:
   - Set an environment variable `GEMINI_API_KEY`, OR
   - Paste it directly into `config.py`

4. Test it:
   ```
   python test_reminder_agent.py
   ```

## How it fits into Orion

```python
from reminder_agent import reminder_agent as reminders
from datetime import datetime

# Direct scheduling - zero API cost
reminders.add("Call mom", due_at=datetime(2026, 8, 23, 17, 0))
reminders.add("Drink water", due_at=datetime.now(), recurrence="daily")

# Natural language - 1 API call, resolves relative dates ("tomorrow", "in 2 hours")
reminders.add_from_text("remind me to submit my assignment tomorrow at 6pm")

# Start the background checker once, when Orion boots up
reminders.start_background_checker(interval=30)

# Manage reminders
reminders.list_active()
reminders.cancel(reminder_id)
reminders.delete(reminder_id)
```

## Files

| File | Purpose |
|---|---|
| `reminder_store.py` | SQLite storage - add/list/complete/delete, recurrence logic |
| `notifier.py` | Delivers reminders (console print or Windows toast) |
| `reminder_agent.py` | Main agent - scheduling, checker loop, AI text parsing |
| `config.py` | API key, poll interval, notification method |
| `test_reminder_agent.py` | Test script |

## Functions reference

**Zero-cost (no API call):**
- `add(message, due_at, recurrence=None)` - recurrence: `None`/`"daily"`/`"weekly"`/`"monthly"`/`"weekdays"`
- `list_active()` / `list_all()` - view reminders
- `cancel(reminder_id)` - mark done without deleting
- `delete(reminder_id)` - remove permanently
- `check_and_fire_due()` - checks + fires due reminders once
- `run_checker_loop(interval=30)` - blocking loop, run in a background thread
- `start_background_checker(interval=30)` - convenience wrapper that starts the loop in a daemon thread automatically

**AI-assisted (1 Gemini Flash-Lite call):**
- `add_from_text(text, reference_time=None)` - parses natural language into a scheduled reminder

## Quota notes

The checker loop that fires reminders on time is entirely local - it just
reads SQLite and prints/toasts. It can run every 30 seconds forever
without touching your Gemini quota at all. Only `add_from_text()` costs
one API call, and only when you actually create a reminder via natural
language (as opposed to calling `add()` directly with a Python datetime).

## Recurrence notes

- `"daily"` - fires once per day, refires next calendar day
- `"weekly"` - fires once per ISO week
- `"monthly"` - fires once per calendar month (clamped to day 28 if the
  original day doesn't exist in the next month, e.g. Jan 31 → Feb 28)
- `"weekdays"` - fires Mon-Fri only, skips Sat/Sun automatically
