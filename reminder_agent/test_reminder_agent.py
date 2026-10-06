"""
test_reminder_agent.py
Quick standalone test. Run this after setting your API key in config.py.

    python test_reminder_agent.py
"""

from datetime import datetime, timedelta
from reminder_agent import reminder_agent as reminders

print("=== Orion Reminder Agent Test ===\n")

print("1. Adding a direct reminder (zero API cost) - due in 2 seconds:")
due_soon = datetime.now() + timedelta(seconds=2)
rid = reminders.add("Test reminder - check the oven", due_soon)
print(f" Added reminder id={rid}, due at {due_soon}\n")

print("2. Adding a recurring daily reminder (zero API cost):")
rid2 = reminders.add("Drink water", datetime.now() + timedelta(seconds=5), recurrence="daily")
print(f" Added recurring reminder id={rid2}\n")

print("3. Listing active reminders:")
for r in reminders.list_active():
    print(" ", r)
print()

print("4. Adding a reminder from natural language (1 API call):")
result = reminders.add_from_text("remind me to submit my assignment tomorrow at 6pm")
print(" Parsed result:", result, "\n")

print("5. Waiting 3 seconds then checking for due reminders (zero API cost)...")
import time
time.sleep(3)
fired = reminders.check_and_fire_due()
print(" Fired:", fired, "\n")

print("6. Full list including completed:")
for r in reminders.list_all():
    print(" ", r)
