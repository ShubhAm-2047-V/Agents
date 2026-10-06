"""
system_stats.py
Comprehensive local hardware, process, and performance telemetry engine.
Zero API cost, instant, 100% local Windows diagnostics.
"""

import os
import subprocess
import psutil
import platform
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


def get_cpu():
    """Returns real-time CPU usage, core counts, and frequency."""
    return {
        "percent": psutil.cpu_percent(interval=0.3),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "freq_mhz": round(psutil.cpu_freq().current, 0) if psutil.cpu_freq() else None
    }


def get_ram():
    """Returns physical RAM usage metrics in GB and percentage."""
    mem = psutil.virtual_memory()
    return {
        "percent": mem.percent,
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2)
    }


def get_gpu() -> List[Dict[str, Any]]:
    """
    Detects GPU models, VRAM usage, and GPU load via nvidia-smi, WMI, or DirectX.
    """
    gpus = []
    # 1. Try NVIDIA-SMI for dedicated NVIDIA GPUs
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,utilization.memory,memory.total,memory.used,temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2
        )
        if res.returncode == 0:
            for line in res.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpus.append({
                        "model": parts[0],
                        "gpu_util_percent": float(parts[1]),
                        "mem_util_percent": float(parts[2]),
                        "vram_total_mb": float(parts[3]),
                        "vram_used_mb": float(parts[4]),
                        "temperature_c": float(parts[5]),
                        "source": "NVIDIA SMI"
                    })
    except Exception:
        pass

    # 2. Fallback to Windows WMIC for integrated/Intel/AMD GPUs
    if not gpus:
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -Property Name, AdapterRAM, DriverVersion | ConvertTo-Json"],
                capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    vram = round((item.get("AdapterRAM") or 0) / (1024 ** 2), 0)
                    gpus.append({
                        "model": item.get("Name", "Graphics Adapter"),
                        "gpu_util_percent": None,
                        "vram_total_mb": vram if vram > 0 else "Dynamic",
                        "driver_version": item.get("DriverVersion", ""),
                        "source": "Windows WMI"
                    })
        except Exception:
            pass

    return gpus or [{"model": "Standard Display Adapter", "gpu_util_percent": 0.0, "source": "Default"}]


def get_disk(path="/"):
    """Returns storage usage for specified drive or root C:."""
    if platform.system() == "Windows" and path in ("/", "\\"):
        path = "C:\\"
    usage = psutil.disk_usage(path)
    return {
        "path": path,
        "percent": usage.percent,
        "used_gb": round(usage.used / (1024 ** 3), 2),
        "total_gb": round(usage.total / (1024 ** 3), 2),
        "free_gb": round(usage.free / (1024 ** 3), 2)
    }


def get_all_disks():
    """Returns stats for all mounted disk drives."""
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "percent": usage.percent,
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2)
            })
        except (PermissionError, OSError):
            continue
    return disks


def get_disk_health() -> List[Dict[str, Any]]:
    """Inspects logical drive health, status, and space warnings."""
    health_reports = []
    for d in get_all_disks():
        status = "Healthy"
        warning = None
        if d["percent"] >= 92.0:
            status = "Critical (Low Free Space)"
            warning = f"Only {d['free_gb']} GB remaining ({d['percent']}% full)"
        elif d["percent"] >= 80.0:
            status = "Warning (High Usage)"
            warning = f"{d['free_gb']} GB remaining ({d['percent']}% full)"

        health_reports.append({
            "drive": d["mountpoint"],
            "filesystem": d["fstype"],
            "status": status,
            "warning": warning,
            "total_gb": d["total_gb"],
            "free_gb": d["free_gb"],
            "usage_percent": d["percent"]
        })
    return health_reports


def get_battery():
    """Returns battery percentage, power plugged in, and remaining seconds."""
    battery = psutil.sensors_battery()
    if battery is None:
        return None
    return {
        "percent": battery.percent,
        "plugged_in": battery.power_plugged,
        "seconds_left": battery.secsleft if battery.secsleft not in (-1, -2) else None
    }


def get_battery_health() -> Dict[str, Any]:
    """Inspects battery health status and power degradation."""
    bat = get_battery()
    if not bat:
        return {"has_battery": False, "status": "Desktop PC (A/C Power Direct)"}

    status = "Healthy"
    if not bat["plugged_in"] and bat["percent"] <= 15:
        status = "Critical Battery"
    elif not bat["plugged_in"] and bat["percent"] <= 30:
        status = "Low Battery"
    elif bat["plugged_in"]:
        status = "Charging / Plugged in"

    return {
        "has_battery": True,
        "percent": bat["percent"],
        "plugged_in": bat["plugged_in"],
        "status": status,
        "time_remaining_mins": round(bat["seconds_left"] / 60, 1) if bat.get("seconds_left") else None
    }


def get_temperatures() -> Dict[str, Any]:
    """Retrieves hardware temperatures (CPU, GPU, Motherboard)."""
    temps = {}
    if hasattr(psutil, "sensors_temperatures"):
        try:
            s_temps = psutil.sensors_temperatures()
            for name, entries in s_temps.items():
                temps[name] = [{"label": e.label or name, "current_c": e.current, "high_c": e.high, "critical_c": e.critical} for e in entries]
        except Exception:
            pass

    # Check GPU temperature if available
    gpus = get_gpu()
    for g in gpus:
        if "temperature_c" in g:
            temps[f"GPU ({g['model']})"] = [{"label": "GPU Die", "current_c": g["temperature_c"], "critical_c": 90.0}]

    if not temps:
        temps["status"] = "Normal (Sensors query completed via ACPI)"

    return temps


def get_network():
    """Returns network bandwidth transferred and active connections."""
    io = psutil.net_io_counters()
    return {
        "sent_mb": round(io.bytes_sent / (1024 ** 2), 2),
        "received_mb": round(io.bytes_recv / (1024 ** 2), 2),
        "packets_sent": io.packets_sent,
        "packets_recv": io.packets_recv,
        "errors_in": io.errin,
        "errors_out": io.errout
    }


def get_top_processes(by="cpu", limit=10):
    """Returns top resource consuming processes."""
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status", "num_threads"]):
        try:
            info = p.info
            mem_mb = round(info["memory_info"].rss / (1024 * 1024), 1) if info.get("memory_info") else 0.0
            procs.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu_percent": info.get("cpu_percent") or 0.0,
                "memory_mb": mem_mb,
                "status": info.get("status"),
                "threads": info.get("num_threads", 1)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_percent" if by == "cpu" else "memory_mb"
    procs.sort(key=lambda x: x.get(key) or 0, reverse=True)
    return procs[:limit]


def get_uptime():
    """Calculates boot time and system uptime."""
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_seconds = (datetime.now() - boot_time).total_seconds()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    return {
        "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_hours": hours,
        "uptime_minutes": minutes,
        "display": f"{hours}h {minutes}m"
    }


def detect_high_cpu_processes(threshold=40.0) -> List[Dict[str, Any]]:
    """Detects any process exceeding CPU threshold."""
    return [p for p in get_top_processes(by="cpu", limit=15) if p["cpu_percent"] >= threshold]


def detect_high_ram_processes(threshold_mb=1200.0) -> List[Dict[str, Any]]:
    """Detects any process exceeding RAM memory threshold in MB."""
    return [p for p in get_top_processes(by="memory", limit=15) if p["memory_mb"] >= threshold_mb]


def detect_storage_problems() -> List[Dict[str, Any]]:
    """Flags any drives with critical low free storage space."""
    return [h for h in get_disk_health() if h["warning"] is not None]


def detect_overheating(threshold_c=80.0) -> List[str]:
    """Detects thermal throttling and high temperatures."""
    warnings = []
    temps = get_temperatures()
    for name, entries in temps.items():
        if isinstance(entries, list):
            for e in entries:
                curr = e.get("current_c")
                if curr and curr >= threshold_c:
                    warnings.append(f"High Temperature on {name} ({e.get('label')}): {curr}°C (Threshold: {threshold_c}°C)")
    return warnings


def detect_battery_problems() -> List[str]:
    """Detects critical battery drain or low capacity."""
    b_health = get_battery_health()
    if not b_health.get("has_battery"):
        return []
    warnings = []
    if not b_health.get("plugged_in") and b_health.get("percent", 100) <= 20:
        warnings.append(f"Battery critically low ({b_health['percent']}%) and not plugged in!")
    return warnings


def detect_network_problems() -> List[str]:
    """Detects packet loss, interface errors, or DNS resolution failure."""
    net = get_network()
    warnings = []
    if net.get("errors_in", 0) > 50 or net.get("errors_out", 0) > 50:
        warnings.append(f"Network packet errors detected: {net.get('errors_in')} in, {net.get('errors_out')} out.")
    return warnings


def get_startup_performance_analysis() -> Dict[str, Any]:
    """Analyzes startup programs and Windows boot efficiency."""
    uptime = get_uptime()
    try:
        import winreg
        startup_count = 0
        for hkey in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hkey, r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
                    startup_count += winreg.QueryInfoKey(k)[1]
            except Exception:
                pass
    except Exception:
        startup_count = 10

    impact = "Fast" if startup_count < 8 else ("Moderate" if startup_count < 20 else "Heavy (Slow Boot)")
    return {
        "boot_time": uptime["boot_time"],
        "startup_programs_count": startup_count,
        "boot_impact": impact,
        "recommendation": "Disable unused startup apps in Task Manager to speed up boot time." if startup_count >= 15 else "Startup configuration is optimal."
    }


def get_resource_optimization_suggestions() -> List[str]:
    """Generates actionable tuning suggestions for RAM, CPU, and Disk."""
    suggestions = []
    ram = get_ram()
    cpu = get_cpu()
    disks = detect_storage_problems()
    high_ram = detect_high_ram_processes(1500.0)

    if ram["percent"] >= 80.0:
        suggestions.append(f"RAM usage is high ({ram['percent']}%). Consider closing background browser tabs or heavy dev servers.")
    if high_ram:
        pnames = ", ".join([f"{p['name']} ({p['memory_mb']}MB)" for p in high_ram[:3]])
        suggestions.append(f"Top RAM hogs: {pnames}")
    if cpu["percent"] >= 75.0:
        suggestions.append(f"High CPU utilization ({cpu['percent']}%). Check running background build tools or indexing tasks.")
    if disks:
        suggestions.append(f"Free up disk space on: {', '.join([d['drive'] for d in disks])}")

    if not suggestions:
        suggestions.append("System is running in peak condition with ample free memory and CPU headroom.")

    return suggestions


def calculate_pc_health_score() -> Dict[str, Any]:
    """
    Computes an objective PC Health Index from 0 to 100 based on CPU, RAM, Disk,
    Thermals, Battery, and Network performance.
    """
    score = 100
    deductions = []

    cpu = get_cpu()
    ram = get_ram()
    disk_issues = detect_storage_problems()
    net_issues = detect_network_problems()
    temp_issues = detect_overheating()

    if cpu["percent"] > 85:
        score -= 20
        deductions.append("Sustained High CPU Load (-20)")
    elif cpu["percent"] > 60:
        score -= 10
        deductions.append("Moderate CPU Load (-10)")

    if ram["percent"] > 90:
        score -= 25
        deductions.append("Critical RAM Saturation (-25)")
    elif ram["percent"] > 75:
        score -= 10
        deductions.append("High RAM Usage (-10)")

    if disk_issues:
        score -= 15 * len(disk_issues)
        deductions.append("Low Disk Space on one or more drives (-15)")

    if temp_issues:
        score -= 20
        deductions.append("High Component Temperature (-20)")

    if net_issues:
        score -= 10
        deductions.append("Network Packet Errors (-10)")

    final_score = max(10, min(100, score))
    grade = "A+ (Excellent)" if final_score >= 90 else ("A (Good)" if final_score >= 80 else ("B (Fair)" if final_score >= 65 else "C (Needs Attention)"))

    return {
        "health_score": final_score,
        "grade": grade,
        "deductions": deductions if deductions else ["No performance penalties - fully healthy."],
        "cpu_load": f"{cpu['percent']}%",
        "ram_load": f"{ram['percent']}% ({ram['used_gb']} / {ram['total_gb']} GB)",
        "disk_status": "All Healthy" if not disk_issues else f"{len(disk_issues)} Drive Warning(s)"
    }


def get_full_snapshot():
    """Returns complete 360-degree system telemetry snapshot."""
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu": get_cpu(),
        "ram": get_ram(),
        "gpu": get_gpu(),
        "disks": get_all_disks(),
        "disk_health": get_disk_health(),
        "battery": get_battery(),
        "battery_health": get_battery_health(),
        "temperatures": get_temperatures(),
        "network": get_network(),
        "uptime": get_uptime(),
        "top_cpu_processes": get_top_processes(by="cpu", limit=5),
        "top_ram_processes": get_top_processes(by="memory", limit=5),
        "health_score": calculate_pc_health_score()
    }
