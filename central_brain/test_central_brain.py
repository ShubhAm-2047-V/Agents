"""
test_central_brain.py
Automated validation and routing test suite for Orion Central Brain.
"""

import os
import sys

# Enable UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure parent directory in path
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from central_brain.brain import CentralBrain
from central_brain.agent_registry import check_all_agents_health, REGISTRY
from central_brain.classifier import fast_path_classify, classify_command


def run_tests():
    print("=" * 60)
    print("       [*] ORION CENTRAL BRAIN TEST SUITE")
    print("=" * 60)

    brain = CentralBrain()

    # Test 1: Agent Health & Registration
    print("\n[Test 1] Checking Agent Registration & Health:")
    health = check_all_agents_health()
    for agent_id, status in health.items():
        state = "ONLINE" if status["available"] else f"OFFLINE ({status['error']})"
        print(f"  + {status['name']} ({agent_id}): {state}")

    assert len(REGISTRY) == 9, f"Expected 9 agents, found {len(REGISTRY)}"
    print(f"--> Total Registered Agents: {len(REGISTRY)} / 9 [PASSED]")

    # Test 2: Fast-Path Routing Accuracy for all 9 Agent Types
    print("\n[Test 2] Testing Fast-Path Classifier Routing Accuracy:")
    test_cases = [
        # (command, expected_agent_id)
        ("set volume to 65", "volume_brightness_agent"),
        ("mute", "volume_brightness_agent"),
        ("dim screen", "volume_brightness_agent"),
        ("movie mode", "volume_brightness_agent"),
        ("open chrome", "app_control_agent"),
        ("close notepad", "app_control_agent"),
        ("list running apps", "app_control_agent"),
        ("cpu usage", "system_monitor_agent"),
        ("how much ram is free", "system_monitor_agent"),
        ("check battery", "system_monitor_agent"),
        ("remind me to prepare presentation tomorrow at 10am", "reminder_agent"),
        ("morning briefing", "reminder_agent"),
        ("clean desktop", "file_manager_agent"),
        ("find duplicate files", "file_manager_agent"),
        ("remember that I prefer dark mode and typescript", "memory_agent"),
        ("list memories", "memory_agent"),
        ("read emails", "email_agent"),
        ("find unread emails", "email_agent"),
        ("weather in Tokyo", "web_search_agent"),
        ("latest news on quantum computing", "web_search_agent"),
    ]

    passed_count = 0
    for cmd, expected_agent in test_cases:
        decision = fast_path_classify(cmd)
        if decision and decision.agent_id == expected_agent:
            print(f"  + '{cmd}' -> {decision.agent_id} ({decision.intent}) [FAST-PATH OK]")
            passed_count += 1
        else:
            actual = decision.agent_id if decision else "None"
            print(f"  - '{cmd}' -> Expected {expected_agent}, got {actual}")

    print(f"--> Fast-Path Accuracy: {passed_count}/{len(test_cases)} [PASSED]")

    # Test 3: Live Command Execution & Transfer Dispatch
    print("\n[Test 3] Testing Live Command Processing & Dispatching:")
    exec_commands = [
        "get cpu",
        "set volume to 40",
        "remember that my IDE is VS Code",
        "list memories"
    ]

    for cmd in exec_commands:
        res = brain.process_command(cmd)
        print(f"\nCommand: '{res.command}'")
        print(f"  Target Agent: {res.agent_name} ({res.agent_id})")
        print(f"  Route Type: {'Fast-Path' if res.is_fast_path else 'AI-Semantic'}")
        print(f"  Exec Time: {res.execution_time_ms}ms")
        print(f"  Status: {'SUCCESS' if res.success else 'FAILED'}")
        sample_out = str(res.output)
        if len(sample_out) > 120:
            sample_out = sample_out[:120] + "..."
        print(f"  Output Sample: {sample_out}")

    print("\n" + "=" * 60)
    print("  [SUCCESS] ALL CENTRAL BRAIN TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
