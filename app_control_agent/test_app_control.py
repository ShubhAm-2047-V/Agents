"""
test_app_control.py
Quick standalone test.

    python test_app_control.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app_control_agent import app_control_agent as apps
except (ImportError, ModuleNotFoundError):
    import app_control_agent as apps

print("=== Orion App Control Agent Test ===\n")

print("1. Listing currently running apps (first 15):")
running = apps.list_running()
for name in running[:15]:
    print(" ", name)
print(f"... {len(running)} total\n")

print("2. Checking if chrome is running:")
print(" chrome running:", apps.is_running("chrome"), "\n")

print("3. Parsing a natural language command:")
parsed = apps.parse_command("close spotify and open notepad")
print(parsed, "\n")

print("4. Listing open windows (requires pygetwindow on Windows):")
try:
    windows = apps.list_windows()
    for w in windows[:10]:
        print(" ", w)
except Exception as e:
    print("Skipped:", e)

# --- Real actions - uncomment to actually test opening/closing apps ---
# print(apps.open("notepad"))
# print(apps.close("notepad"))
# print(apps.switch_to("notepad"))

# --- Execute a parsed command for real ---
# results = apps.execute_parsed_actions(parsed)
# print(results)
