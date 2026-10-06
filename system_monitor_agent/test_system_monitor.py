"""
test_system_monitor.py
Quick standalone test. Run this after setting your API key in config.py.

    python test_system_monitor.py
"""

from system_monitor_agent import system_monitor_agent as sysmon

print("=== Orion System Monitor Agent Test ===\n")

print("1. Full snapshot (zero API cost):")
snap = sysmon.get_snapshot()
for key, val in snap.items():
    print(f" {key}: {val}")
print()

print("2. Checking alerts (zero API cost):")
alerts = sysmon.check_alerts()
print(" Alerts:", alerts if alerts else "None - everything looks fine")
print()

print("3. Top 5 CPU-heavy processes (zero API cost):")
for p in sysmon.get_top_processes(by="cpu", limit=5):
    print(" ", p)
print()

print("4. Spoken-style AI summary (1 API call):")
summary = sysmon.get_spoken_summary()
print(summary, "\n")

print("5. Testing monitor_loop for 3 quick iterations (zero API cost, local only):")
sysmon.monitor_loop(poll_interval=1, max_iterations=3)
print("Loop finished.")
