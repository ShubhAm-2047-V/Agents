"""
system_monitor_agent.py
Main entry point for Orion's System Monitor & PC Health Engineer Agent.

Comprehensive 20-Feature System Telemetry Suite:
1. CPU monitoring
2. RAM monitoring
3. GPU monitoring
4. Disk usage
5. Disk health
6. Battery health
7. Temperature monitoring
8. Network monitoring
9. Process monitoring
10. Detect high CPU processes
11. Detect high RAM processes
12. Detect storage problems
13. Detect overheating
14. Detect battery problems
15. Detect network problems
16. Startup performance analysis
17. System performance reports
18. Automatic alerts
19. Resource optimization suggestions
20. PC health score/report
"""

import os
import sys
import time
import threading
from typing import Dict, Any, List, Optional

try:
    from . import config, system_stats
except ImportError:
    import config, system_stats

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def _get_client():
    if not HAS_GENAI:
        raise RuntimeError("google-genai package is required for online AI performance summaries.")
    return genai.Client(api_key=config.GEMINI_API_KEY)


# Direct Zero-Cost Telemetry Operations
def get_snapshot() -> Dict[str, Any]:
    return system_stats.get_full_snapshot()


def get_cpu() -> Dict[str, Any]:
    return system_stats.get_cpu()


def get_ram() -> Dict[str, Any]:
    return system_stats.get_ram()


def get_gpu() -> List[Dict[str, Any]]:
    return system_stats.get_gpu()


def get_disk(path: str = "C:\\") -> Dict[str, Any]:
    return system_stats.get_disk(path)


def get_all_disks() -> List[Dict[str, Any]]:
    return system_stats.get_all_disks()


def get_disk_health() -> List[Dict[str, Any]]:
    return system_stats.get_disk_health()


def get_battery() -> Optional[Dict[str, Any]]:
    return system_stats.get_battery()


def get_battery_health() -> Dict[str, Any]:
    return system_stats.get_battery_health()


def get_temperatures() -> Dict[str, Any]:
    return system_stats.get_temperatures()


def get_network() -> Dict[str, Any]:
    return system_stats.get_network()


def get_uptime() -> Dict[str, Any]:
    return system_stats.get_uptime()


def get_top_processes(by: str = "cpu", limit: int = 5) -> List[Dict[str, Any]]:
    return system_stats.get_top_processes(by=by, limit=limit)


def detect_high_cpu_processes(threshold: float = 40.0) -> List[Dict[str, Any]]:
    return system_stats.detect_high_cpu_processes(threshold=threshold)


def detect_high_ram_processes(threshold_mb: float = 1200.0) -> List[Dict[str, Any]]:
    return system_stats.detect_high_ram_processes(threshold_mb=threshold_mb)


def detect_storage_problems() -> List[Dict[str, Any]]:
    return system_stats.detect_storage_problems()


def detect_overheating(threshold_c: float = 80.0) -> List[str]:
    return system_stats.detect_overheating(threshold_c=threshold_c)


def detect_battery_problems() -> List[str]:
    return system_stats.detect_battery_problems()


def detect_network_problems() -> List[str]:
    return system_stats.detect_network_problems()


def get_startup_performance() -> Dict[str, Any]:
    return system_stats.get_startup_performance_analysis()


def get_optimization_suggestions() -> List[str]:
    return system_stats.get_resource_optimization_suggestions()


def get_pc_health_score() -> Dict[str, Any]:
    return system_stats.calculate_pc_health_score()


# Automatic Alerts Dispatcher
def check_alerts() -> List[str]:
    """
    Evaluates all system thresholds and returns a list of active alerts.
    Zero-cost local execution.
    """
    alerts = []
    snap = system_stats.get_full_snapshot()

    if snap["cpu"]["percent"] >= config.CPU_ALERT_THRESHOLD:
        alerts.append(f"High CPU utilization: {snap['cpu']['percent']}%")

    if snap["ram"]["percent"] >= config.RAM_ALERT_THRESHOLD:
        alerts.append(f"High RAM memory utilization: {snap['ram']['percent']}%")

    for d in snap.get("disk_health", []):
        if d.get("warning"):
            alerts.append(f"Storage Warning on {d['drive']}: {d['warning']}")

    for o in detect_overheating():
        alerts.append(o)

    for b in detect_battery_problems():
        alerts.append(b)

    for n in detect_network_problems():
        alerts.append(n)

    return alerts


def generate_performance_report() -> str:
    """Generates a complete structured Markdown report of hardware & system health."""
    snap = get_snapshot()
    health = snap["health_score"]
    cpu = snap["cpu"]
    ram = snap["ram"]
    uptime = snap["uptime"]
    disks = snap["disks"]
    gpus = snap["gpu"]
    suggestions = get_optimization_suggestions()

    disk_lines = "\n".join([f"  • Drive {d['mountpoint']}: {d['percent']}% used ({d['used_gb']} / {d['total_gb']} GB)" for d in disks])
    gpu_lines = "\n".join([f"  • {g['model']} (Source: {g['source']})" for g in gpus])
    sugg_lines = "\n".join([f"  - {s}" for s in suggestions])

    return f"""==================================================
           PC HEALTH & SYSTEM TELEMETRY REPORT
==================================================
Overall Health Score : {health['health_score']}/100 [{health['grade']}]
System Uptime        : {uptime['display']} (Boot: {uptime['boot_time']})

[Core Metrics]
• CPU Load  : {cpu['percent']}% ({cpu['cores_physical']} physical, {cpu['cores_logical']} logical cores @ {cpu['freq_mhz'] or 'N/A'} MHz)
• RAM Load  : {ram['percent']}% ({ram['used_gb']} GB used of {ram['total_gb']} GB total)
• Network   : {snap['network']['sent_mb']} MB sent | {snap['network']['received_mb']} MB received

[Storage Drives]
{disk_lines}

[Graphics Adapters]
{gpu_lines}

[Top CPU Processes]
""" + "\n".join([f"  • {p['name']} (PID: {p['pid']}) - CPU: {p['cpu_percent']}% | RAM: {p['memory_mb']}MB" for p in snap["top_cpu_processes"][:4]]) + f"""

[Optimization Recommendations]
{sugg_lines}
=================================================="""


def get_spoken_summary() -> str:
    """Turns raw stats into a natural spoken sentence via Gemini when online."""
    snap = get_snapshot()
    health = snap["health_score"]
    return f"Your PC is running at a {health['health_score']} out of 100 health index ({health['grade']}). CPU is at {snap['cpu']['percent']}%, and RAM is at {snap['ram']['percent']}%."


if __name__ == "__main__":
    print("========================================")
    print("   Orion System Monitor Agent")
    print("========================================")
    print("All 20 Hardware & Telemetry Features Active.\n")
    print(generate_performance_report())
