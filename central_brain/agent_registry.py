"""
agent_registry.py
Registry and wrapper for all 9 Orion agents in the system.
Handles lazy loading, capability definitions, and unified dispatching.
"""

import os
import sys
import importlib
from typing import Dict, Any, Callable, Optional, List

# Add parent workspace to sys.path if not present
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)


class AgentMetadata:
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        keywords: List[str],
        module_loader: Callable,
        default_dispatcher: Optional[Callable] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.keywords = keywords
        self.module_loader = module_loader
        self.default_dispatcher = default_dispatcher
        self._module = None
        self._is_available = None
        self._load_error = None

    @property
    def module(self):
        if self._module is None and self._load_error is None:
            try:
                self._module = self.module_loader()
                self._is_available = True
            except Exception as e:
                self._is_available = False
                self._load_error = str(e)
        return self._module

    def is_available(self) -> bool:
        if self._is_available is None:
            _ = self.module
        return bool(self._is_available)


# ---------------- Lazy Loaders ----------------
def _load_agent_module(agent_dir_name: str, module_name: str):
    agent_dir = os.path.join(WORKSPACE_ROOT, agent_dir_name)
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
    if "config" in sys.modules:
        del sys.modules["config"]
    return importlib.import_module(module_name)


def _load_app_control():
    return _load_agent_module("app_control_agent", "app_control_agent")

def _load_system_monitor():
    return _load_agent_module("system_monitor_agent", "system_monitor_agent")

def _load_reminder():
    return _load_agent_module("reminder_agent", "reminder_agent")

def _load_memory():
    return _load_agent_module("memory_agent", "memory_agent")

def _load_file_manager():
    return _load_agent_module("file_manager_agent", "file_manager_agent")

def _load_code_assistant():
    return _load_agent_module("code_assistant_agent", "code_assistant_agent")

def _load_web_search():
    return _load_agent_module("web_search_agent", "web_search_agent")

def _load_email():
    return _load_agent_module("email_agent", "email_agent")

def _load_volume_brightness():
    return _load_agent_module("volume_brightness_agent", "volume_brightness_agent")


# ---------------- Agent Registry Definitions ----------------
REGISTRY: Dict[str, AgentMetadata] = {
    "volume_brightness_agent": AgentMetadata(
        agent_id="volume_brightness_agent",
        name="Brightness & Volume Agent",
        description="Controls hardware audio volume (up, down, set, mute), display brightness, presets (movie, gaming, night, study), and media playback keys.",
        keywords=[
            "volume", "mute", "unmute", "sound", "audio", "brightness", "dim", "screen brightness",
            "louder", "quieter", "max volume", "min volume", "preset", "movie mode", "night mode",
            "gaming mode", "play", "pause", "next track", "previous track"
        ],
        module_loader=_load_volume_brightness
    ),
    "app_control_agent": AgentMetadata(
        agent_id="app_control_agent",
        name="App Control Agent",
        description="Opens, closes, minimizes, maximizes, snaps, switches, restarts, and tiles applications and windows.",
        keywords=[
            "open", "launch", "start", "run app", "close", "kill app", "terminate", "switch to",
            "minimize", "maximize", "snap left", "snap right", "side by side", "tile", "focus",
            "restart app", "show windows", "running apps"
        ],
        module_loader=_load_app_control
    ),
    "system_monitor_agent": AgentMetadata(
        agent_id="system_monitor_agent",
        name="System Monitor Agent",
        description="Monitors PC telemetry: CPU, RAM, GPU, Disks, Battery, Temperatures, Network, PC health score, and high-resource processes.",
        keywords=[
            "cpu", "ram", "memory usage", "gpu", "disk space", "storage", "battery", "temperature",
            "thermal", "network usage", "pc health", "system stats", "telemetry", "health score",
            "high cpu", "high ram", "system report", "uptime"
        ],
        module_loader=_load_system_monitor
    ),
    "reminder_agent": AgentMetadata(
        agent_id="reminder_agent",
        name="Reminder & Scheduling Agent",
        description="Schedules alarms, reminders, recurring alerts, deadlines, snooze, morning/evening briefings.",
        keywords=[
            "remind", "reminder", "alarm", "schedule", "alert", "deadline", "snooze", "appointment",
            "meeting reminder", "briefing", "morning briefing", "evening briefing", "remind me to"
        ],
        module_loader=_load_reminder
    ),
    "file_manager_agent": AgentMetadata(
        agent_id="file_manager_agent",
        name="File Manager Agent",
        description="Finds files, cleans Desktop/Downloads, detects duplicate files, analyzes large storage hogs, summarizes text files, zips/unzips archives.",
        keywords=[
            "file", "folder", "search file", "find file", "clean desktop", "clean downloads",
            "duplicate files", "storage hogs", "large files", "zip folder", "unzip", "archive",
            "summarize file", "organize files", "rename files"
        ],
        module_loader=_load_file_manager
    ),
    "memory_agent": AgentMetadata(
        agent_id="memory_agent",
        name="Memory Agent",
        description="Saves and recalls persistent facts, user preferences, projects, important notes, coding habits, and past conversations.",
        keywords=[
            "remember", "memory", "recall", "store fact", "save note", "forget", "what is my preference",
            "what do you know about", "search memory", "my favorite", "my project", "user profile"
        ],
        module_loader=_load_memory
    ),
    "code_assistant_agent": AgentMetadata(
        agent_id="code_assistant_agent",
        name="Code Assistant Agent",
        description="Writes, explains, debugs, optimizes, documents, reviews code, generates tests, and runs Python/scripts.",
        keywords=[
            "code", "python", "javascript", "function", "write script", "explain code", "debug",
            "fix bug", "refactor", "optimize code", "unit test", "write code", "generate code",
            "syntax error", "regex", "git"
        ],
        module_loader=_load_code_assistant
    ),
    "email_agent": AgentMetadata(
        agent_id="email_agent",
        name="Email Agent",
        description="Reads inbox, searches emails, summarizes messages, drafts formal/client replies, detects urgent emails.",
        keywords=[
            "email", "inbox", "gmail", "unread emails", "send email", "draft reply", "summarize email",
            "urgent emails", "client email", "mail briefing", "read emails"
        ],
        module_loader=_load_email
    ),
    "web_search_agent": AgentMetadata(
        agent_id="web_search_agent",
        name="Web Search & Intelligence Agent",
        description="Performs live web searches, news research, weather checks, stock lookups, deep topic dossiers, and report exports.",
        keywords=[
            "search", "google", "web search", "browse", "news", "weather", "stock price",
            "research", "dossier", "fact check", "who is", "what is", "latest info on"
        ],
        module_loader=_load_web_search
    ),
}


def get_agent(agent_id: str) -> Optional[AgentMetadata]:
    return REGISTRY.get(agent_id)


def list_agents() -> List[AgentMetadata]:
    return list(REGISTRY.values())


def check_all_agents_health() -> Dict[str, Dict[str, Any]]:
    """Checks the operational status of all 9 agents."""
    status = {}
    for agent_id, meta in REGISTRY.items():
        is_ok = meta.is_available()
        status[agent_id] = {
            "name": meta.name,
            "available": is_ok,
            "error": meta._load_error if not is_ok else None
        }
    return status
