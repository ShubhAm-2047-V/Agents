"""
classifier.py
Hybrid dual-layer Intent Classifier and Router for Orion Central Brain.
Layer 1: Zero-latency Regex & Rule-based Fast-Path (<1ms)
Layer 2: Gemini 2.5 Flash / Flash-Lite Semantic Reasoner (for complex queries)
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple

try:
    from . import config, agent_registry
except ImportError:
    import config, agent_registry


class RoutingDecision:
    def __init__(
        self,
        agent_id: str,
        confidence: float,
        intent: str,
        arguments: Dict[str, Any],
        explanation: str,
        is_fast_path: bool = False
    ):
        self.agent_id = agent_id
        self.confidence = confidence
        self.intent = intent
        self.arguments = arguments
        self.explanation = explanation
        self.is_fast_path = is_fast_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "confidence": self.confidence,
            "intent": self.intent,
            "arguments": self.arguments,
            "explanation": self.explanation,
            "is_fast_path": self.is_fast_path
        }


# =====================================================================
# LAYER 1: FAST-PATH RULE MATCHERS (<1ms, ZERO COST, 100% OFFLINE)
# =====================================================================

def _match_volume_brightness(query_lower: str) -> Optional[RoutingDecision]:
    # Master Volume Set
    m = re.search(r'\b(?:set\s+)?volume\s+(?:to\s+)?(\d{1,3})%?', query_lower)
    if m:
        level = max(0, min(100, int(m.group(1))))
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.99,
            intent="set_volume",
            arguments={"level": level},
            explanation=f"Set master volume to {level}%",
            is_fast_path=True
        )

    # Volume Up/Down
    if any(p in query_lower for p in ["volume up", "increase volume", "louder", "turn up sound"]):
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.98,
            intent="volume_up",
            arguments={"delta": 10},
            explanation="Increase master volume by 10%",
            is_fast_path=True
        )
    if any(p in query_lower for p in ["volume down", "decrease volume", "lower volume", "quieter", "turn down sound"]):
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.98,
            intent="volume_down",
            arguments={"delta": 10},
            explanation="Decrease master volume by 10%",
            is_fast_path=True
        )

    # Mute / Unmute
    if query_lower in ["mute", "mute audio", "mute sound", "mute volume", "silence audio"]:
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.99,
            intent="mute",
            arguments={},
            explanation="Mute master audio",
            is_fast_path=True
        )
    if query_lower in ["unmute", "unmute audio", "unmute sound", "restore sound"]:
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.99,
            intent="unmute",
            arguments={},
            explanation="Unmute master audio",
            is_fast_path=True
        )

    # Brightness Set
    m = re.search(r'\b(?:set\s+)?brightness\s+(?:to\s+)?(\d{1,3})%?', query_lower)
    if m:
        level = max(0, min(100, int(m.group(1))))
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.99,
            intent="set_brightness",
            arguments={"level": level},
            explanation=f"Set display brightness to {level}%",
            is_fast_path=True
        )

    # Brightness Up/Down
    if any(p in query_lower for p in ["brightness up", "increase brightness", "brighter", "make screen brighter"]):
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.98,
            intent="brightness_up",
            arguments={"delta": 10},
            explanation="Increase screen brightness",
            is_fast_path=True
        )
    if any(p in query_lower for p in ["brightness down", "decrease brightness", "dim screen", "dim display", "lower brightness"]):
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.98,
            intent="brightness_down",
            arguments={"delta": 10},
            explanation="Decrease screen brightness",
            is_fast_path=True
        )

    # Presets
    presets = ["movie", "gaming", "night", "study", "work", "daylight", "sleep"]
    for p in presets:
        if f"{p} mode" in query_lower or f"{p} preset" in query_lower or query_lower == p:
            return RoutingDecision(
                agent_id="volume_brightness_agent",
                confidence=0.98,
                intent="apply_preset",
                arguments={"preset_name": p},
                explanation=f"Activate {p.capitalize()} atmosphere preset",
                is_fast_path=True
            )

    # Media Playback Keys
    if query_lower in ["play", "pause", "play pause", "pause music", "resume music", "play media"]:
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.95,
            intent="media_play_pause",
            arguments={},
            explanation="Toggle media playback",
            is_fast_path=True
        )
    if query_lower in ["next track", "next song", "skip track", "skip song"]:
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.95,
            intent="media_next",
            arguments={},
            explanation="Skip to next audio/media track",
            is_fast_path=True
        )
    if query_lower in ["prev track", "previous track", "prev song", "previous song"]:
        return RoutingDecision(
            agent_id="volume_brightness_agent",
            confidence=0.95,
            intent="media_prev",
            arguments={},
            explanation="Go to previous audio/media track",
            is_fast_path=True
        )

    return None


def _match_app_control(query_lower: str) -> Optional[RoutingDecision]:
    # Open app
    m = re.match(r'^(?:open|launch|start)\s+([a-zA-Z0-9_\-\.\s]+)$', query_lower)
    if m:
        target = m.group(1).strip()
        # Direct website aliases should be handled by WebSearch/Browser
        if target in ["my website", "my site", "my own website", "shubdeep labs", "shubh deep labs", "shubdeep"]:
            return RoutingDecision(
                agent_id="web_search_agent",
                confidence=0.99,
                intent="open_website",
                arguments={"target": "https://shubh-deep-labs.vercel.app/"},
                explanation="Launch user's official website: Shubdeep Labs (https://shubh-deep-labs.vercel.app/)",
                is_fast_path=True
            )
        # Avoid conflict with web search / common queries like "open google"
        if target not in ["chrome and search", "web"]:
            return RoutingDecision(
                agent_id="app_control_agent",
                confidence=0.96,
                intent="open_app",
                arguments={"app_name": target},
                explanation=f"Launch application '{target}'",
                is_fast_path=True
            )

    # Close / Kill app
    m = re.match(r'^(?:close|quit|kill|terminate|stop)\s+([a-zA-Z0-9_\-\.\s]+)$', query_lower)
    if m:
        target = m.group(1).strip()
        return RoutingDecision(
            agent_id="app_control_agent",
            confidence=0.96,
            intent="close_app",
            arguments={"app_name": target},
            explanation=f"Close application '{target}'",
            is_fast_path=True
        )

    # Switch to / focus
    m = re.match(r'^(?:switch to|focus on|focus)\s+([a-zA-Z0-9_\-\.\s]+)$', query_lower)
    if m:
        target = m.group(1).strip()
        return RoutingDecision(
            agent_id="app_control_agent",
            confidence=0.95,
            intent="switch_to",
            arguments={"title_contains": target},
            explanation=f"Switch focus to window matching '{target}'",
            is_fast_path=True
        )

    # Minimize / Maximize / Snap
    if query_lower in ["minimize all", "show desktop"]:
        return RoutingDecision(
            agent_id="app_control_agent",
            confidence=0.98,
            intent="minimize_all",
            arguments={},
            explanation="Minimize all open windows",
            is_fast_path=True
        )
    m = re.match(r'^minimize\s+([a-zA-Z0-9_\-\.\s]+)$', query_lower)
    if m:
        return RoutingDecision(
            agent_id="app_control_agent",
            confidence=0.95,
            intent="minimize",
            arguments={"title_contains": m.group(1).strip()},
            explanation=f"Minimize window '{m.group(1).strip()}'",
            is_fast_path=True
        )
    m = re.match(r'^maximize\s+([a-zA-Z0-9_\-\.\s]+)$', query_lower)
    if m:
        return RoutingDecision(
            agent_id="app_control_agent",
            confidence=0.95,
            intent="maximize",
            arguments={"app_name": m.group(1).strip()},
            explanation=f"Maximize window '{m.group(1).strip()}'",
            is_fast_path=True
        )

    # List running / List windows
    if query_lower in ["list running apps", "running apps", "what apps are open", "list processes", "show open windows", "list windows"]:
        return RoutingDecision(
            agent_id="app_control_agent",
            confidence=0.97,
            intent="list_running",
            arguments={},
            explanation="List all currently running apps and active windows",
            is_fast_path=True
        )

    return None


def _match_system_monitor(query_lower: str) -> Optional[RoutingDecision]:
    # CPU
    if query_lower in ["cpu", "cpu usage", "cpu load", "check cpu", "get cpu", "how is cpu"]:
        return RoutingDecision(
            agent_id="system_monitor_agent",
            confidence=0.98,
            intent="get_cpu",
            arguments={},
            explanation="Inspect live CPU usage and clock speeds",
            is_fast_path=True
        )

    # RAM
    if query_lower in ["ram", "ram usage", "memory usage", "check ram", "how much ram is free", "get ram"]:
        return RoutingDecision(
            agent_id="system_monitor_agent",
            confidence=0.98,
            intent="get_ram",
            arguments={},
            explanation="Inspect RAM usage and available memory",
            is_fast_path=True
        )

    # GPU
    if query_lower in ["gpu", "gpu usage", "gpu stats", "graphics card", "check gpu"]:
        return RoutingDecision(
            agent_id="system_monitor_agent",
            confidence=0.98,
            intent="get_gpu",
            arguments={},
            explanation="Inspect GPU usage and memory",
            is_fast_path=True
        )

    # Disks / Storage
    if query_lower in ["disk", "disk space", "storage", "hard drive", "check disks", "disk usage"]:
        return RoutingDecision(
            agent_id="system_monitor_agent",
            confidence=0.98,
            intent="get_all_disks",
            arguments={},
            explanation="Check storage capacity and disk usage",
            is_fast_path=True
        )

    # Battery
    if query_lower in ["battery", "battery percentage", "battery health", "power status", "check battery"]:
        return RoutingDecision(
            agent_id="system_monitor_agent",
            confidence=0.98,
            intent="get_battery",
            arguments={},
            explanation="Check battery level, status, and health",
            is_fast_path=True
        )

    # Temperatures
    if query_lower in ["temperature", "temperatures", "cpu temp", "thermal status", "overheating", "check temps"]:
        return RoutingDecision(
            agent_id="system_monitor_agent",
            confidence=0.98,
            intent="get_temperatures",
            arguments={},
            explanation="Check system thermal sensors and temperatures",
            is_fast_path=True
        )

    # Full System Snapshot / Health
    if query_lower in ["system stats", "system monitor", "pc health", "health score", "system snapshot", "pc stats", "telemetry"]:
        return RoutingDecision(
            agent_id="system_monitor_agent",
            confidence=0.99,
            intent="get_snapshot",
            arguments={},
            explanation="Retrieve full system telemetry snapshot and PC health metrics",
            is_fast_path=True
        )

    # High CPU / RAM processes
    if "high cpu" in query_lower or "cpu hogs" in query_lower:
        return RoutingDecision(
            agent_id="system_monitor_agent",
            confidence=0.97,
            intent="get_high_cpu_processes",
            arguments={"limit": 5},
            explanation="Identify top processes consuming the most CPU",
            is_fast_path=True
        )
    if "high ram" in query_lower or "ram hogs" in query_lower or "memory hogs" in query_lower:
        return RoutingDecision(
            agent_id="system_monitor_agent",
            confidence=0.97,
            intent="get_high_ram_processes",
            arguments={"limit": 5},
            explanation="Identify top processes consuming the most RAM",
            is_fast_path=True
        )

    return None


def _match_reminder(query_lower: str) -> Optional[RoutingDecision]:
    if query_lower.startswith("remind me to ") or query_lower.startswith("remind me "):
        text = re.sub(r'^remind me (?:to )?', '', query_lower).strip()
        return RoutingDecision(
            agent_id="reminder_agent",
            confidence=0.98,
            intent="create_reminder_natural",
            arguments={"text": text},
            explanation=f"Create a scheduled reminder for: '{text}'",
            is_fast_path=True
        )

    if query_lower in ["list reminders", "show reminders", "get reminders", "my reminders", "what are my reminders"]:
        return RoutingDecision(
            agent_id="reminder_agent",
            confidence=0.98,
            intent="list_reminders",
            arguments={},
            explanation="List active scheduled reminders",
            is_fast_path=True
        )

    if query_lower in ["morning briefing", "daily briefing", "morning brief"]:
        return RoutingDecision(
            agent_id="reminder_agent",
            confidence=0.98,
            intent="morning_briefing",
            arguments={},
            explanation="Generate morning briefing with pending tasks & agenda",
            is_fast_path=True
        )

    if query_lower in ["evening briefing", "evening brief", "end of day summary"]:
        return RoutingDecision(
            agent_id="reminder_agent",
            confidence=0.98,
            intent="evening_briefing",
            arguments={},
            explanation="Generate evening recap and review completed reminders",
            is_fast_path=True
        )

    return None


def _match_file_manager(query_lower: str) -> Optional[RoutingDecision]:
    if query_lower in ["clean desktop", "organize desktop", "tidy desktop"]:
        return RoutingDecision(
            agent_id="file_manager_agent",
            confidence=0.99,
            intent="clean_desktop",
            arguments={},
            explanation="Organize files on Desktop into categorized folders",
            is_fast_path=True
        )

    if query_lower in ["clean downloads", "organize downloads", "tidy downloads"]:
        return RoutingDecision(
            agent_id="file_manager_agent",
            confidence=0.99,
            intent="clean_downloads",
            arguments={},
            explanation="Organize files in Downloads folder",
            is_fast_path=True
        )

    if query_lower in ["find duplicates", "find duplicate files", "check duplicates", "detect duplicates"]:
        return RoutingDecision(
            agent_id="file_manager_agent",
            confidence=0.98,
            intent="duplicates",
            arguments={"target": "Downloads"},
            explanation="Detect duplicate files by MD5 checksum to reclaim space",
            is_fast_path=True
        )

    if query_lower in ["storage hogs", "find large files", "large files", "biggest files"]:
        return RoutingDecision(
            agent_id="file_manager_agent",
            confidence=0.98,
            intent="storage_hogs",
            arguments={"target": "Downloads", "limit": 10},
            explanation="Scan and rank the largest files consuming disk space",
            is_fast_path=True
        )

    m = re.match(r'^(?:search file|find file|search for file)\s+([a-zA-Z0-9_\-\.\*\?]+)$', query_lower)
    if m:
        pattern = m.group(1).strip()
        return RoutingDecision(
            agent_id="file_manager_agent",
            confidence=0.96,
            intent="search",
            arguments={"pattern": pattern},
            explanation=f"Search filesystem for files matching '{pattern}'",
            is_fast_path=True
        )

    return None


def _match_memory(query_lower: str) -> Optional[RoutingDecision]:
    if query_lower.startswith("remember that ") or query_lower.startswith("remember: ") or query_lower.startswith("remember "):
        fact = re.sub(r'^remember (?:that )?:?\s*', '', query_lower).strip()
        return RoutingDecision(
            agent_id="memory_agent",
            confidence=0.97,
            intent="remember_preference",
            arguments={"text": fact},
            explanation=f"Store persistent memory/preference: '{fact}'",
            is_fast_path=True
        )

    if query_lower in ["list memories", "show memories", "all memories", "what do you remember"]:
        return RoutingDecision(
            agent_id="memory_agent",
            confidence=0.97,
            intent="list_all_memories",
            arguments={},
            explanation="List all saved memories and user preferences",
            is_fast_path=True
        )

    m = re.match(r'^(?:search memory for|search memory|recall)\s+([a-zA-Z0-9_\-\.\s]+)$', query_lower)
    if m:
        query_term = m.group(1).strip()
        return RoutingDecision(
            agent_id="memory_agent",
            confidence=0.96,
            intent="search_memory",
            arguments={"query": query_term},
            explanation=f"Search memory store for '{query_term}'",
            is_fast_path=True
        )

    return None


def _match_email(query_lower: str) -> Optional[RoutingDecision]:
    if query_lower in ["read emails", "check emails", "check inbox", "show emails", "my emails", "get emails"]:
        return RoutingDecision(
            agent_id="email_agent",
            confidence=0.98,
            intent="read_emails",
            arguments={"max_results": 10},
            explanation="Fetch recent emails from Gmail inbox",
            is_fast_path=True
        )

    if query_lower in ["unread emails", "check unread emails", "find unread emails"]:
        return RoutingDecision(
            agent_id="email_agent",
            confidence=0.98,
            intent="find_unread_emails",
            arguments={},
            explanation="Retrieve unread messages from inbox",
            is_fast_path=True
        )

    if query_lower in ["important emails", "find important emails"]:
        return RoutingDecision(
            agent_id="email_agent",
            confidence=0.98,
            intent="find_important_emails",
            arguments={},
            explanation="Filter and list important emails",
            is_fast_path=True
        )

    if query_lower in ["email briefing", "daily email briefing", "summarize inbox"]:
        return RoutingDecision(
            agent_id="email_agent",
            confidence=0.98,
            intent="daily_briefing",
            arguments={},
            explanation="Compile daily email briefing and summary",
            is_fast_path=True
        )

    return None


def _match_web_search(query_lower: str) -> Optional[RoutingDecision]:
    # User's personal website & direct site opening
    if any(q == query_lower for q in ["open my website", "open my site", "my website", "my site", "open shubdeep labs", "shubdeep labs", "open shubh deep labs", "shubh deep labs"]):
        return RoutingDecision(
            agent_id="web_search_agent",
            confidence=0.99,
            intent="open_website",
            arguments={"target": "https://shubh-deep-labs.vercel.app/"},
            explanation="Launch user's official website: Shubdeep Labs (https://shubh-deep-labs.vercel.app/)",
            is_fast_path=True
        )

    # Weather
    m = re.match(r'^(?:what is the |check )?weather(?:\s+in\s+|\s+for\s+)([a-zA-Z\s]+)$', query_lower)
    if m:
        city = m.group(1).strip()
        return RoutingDecision(
            agent_id="web_search_agent",
            confidence=0.98,
            intent="weather_lookup",
            arguments={"city": city},
            explanation=f"Fetch live weather forecast for {city}",
            is_fast_path=True
        )

    # Stock price
    m = re.match(r'^(?:stock price of|stock price|stock|share price of)\s+([a-zA-Z0-9\.\^]+)$', query_lower)
    if m:
        symbol = m.group(1).strip()
        return RoutingDecision(
            agent_id="web_search_agent",
            confidence=0.98,
            intent="stock_lookup",
            arguments={"symbol": symbol},
            explanation=f"Retrieve live stock data for symbol {symbol.upper()}",
            is_fast_path=True
        )

    # Search web for / search for / google / latest news on
    m = re.match(r'^(?:search the web for|search web for|search for|google|bing)\s+(.+)$', query_lower)
    if m:
        q = m.group(1).strip()
        return RoutingDecision(
            agent_id="web_search_agent",
            confidence=0.97,
            intent="smart_search",
            arguments={"query": q},
            explanation=f"Perform live search and synthesized intelligence on: '{q}'",
            is_fast_path=True
        )

    m = re.match(r'^(?:latest news on|news on|news about|latest news)\s*(.*)$', query_lower)
    if m:
        topic = m.group(1).strip() or "top headlines"
        return RoutingDecision(
            agent_id="web_search_agent",
            confidence=0.97,
            intent="raw_news",
            arguments={"query": topic},
            explanation=f"Fetch latest breaking news for '{topic}'",
            is_fast_path=True
        )

    return None


def fast_path_classify(command: str) -> Optional[RoutingDecision]:
    """Evaluates rule-based fast-path engines in optimal priority order."""
    q = command.strip().lower()
    if not q:
        return None

    # Priority 1: Hardware control (instant)
    res = _match_volume_brightness(q)
    if res:
        return res

    # Priority 2: System Monitor
    res = _match_system_monitor(q)
    if res:
        return res

    # Priority 3: App Control
    res = _match_app_control(q)
    if res:
        return res

    # Priority 4: Reminder
    res = _match_reminder(q)
    if res:
        return res

    # Priority 5: File Manager
    res = _match_file_manager(q)
    if res:
        return res

    # Priority 6: Memory
    res = _match_memory(q)
    if res:
        return res

    # Priority 7: Email
    res = _match_email(q)
    if res:
        return res

    # Priority 8: Web Search
    res = _match_web_search(q)
    if res:
        return res

    return None


# =====================================================================
# LAYER 2: GEMINI AI SEMANTIC REASONER & MULTI-AGENT CLASSIFIER
# =====================================================================

def ai_classify(command: str) -> RoutingDecision:
    """Uses Gemini to reason about nuanced or ambiguous user commands."""
    try:
        from google import genai
        client = genai.Client(api_key=config.GEMINI_API_KEY)
    except Exception as e:
        # Fallback to keyword match if Gemini is not available
        return _fallback_keyword_classify(command, error_note=str(e))

    agent_descriptions = []
    for agent_id, meta in agent_registry.REGISTRY.items():
        agent_descriptions.append(f"- {agent_id}: {meta.description} (Keywords: {', '.join(meta.keywords[:6])})")

    prompt = f"""You are the Central Brain Router for Orion, an intelligent multi-agent PC assistant.
Given a user command, select the single best specialized agent to handle it, determine the specific intent/action, and extract parameters.

Available Agents:
{chr(10).join(agent_descriptions)}

User Command: "{command}"

Respond ONLY with valid JSON in this exact structure:
{{
  "agent_id": "<one of the available agent_ids>",
  "confidence": <float between 0.0 and 1.0>,
  "intent": "<short descriptive intent, e.g. open_app, explain_code, search_web, write_code, etc.>",
  "arguments": {{
     "<param_key>": "<param_value>"
  }},
  "explanation": "<1 sentence rationale explaining why this agent was chosen>"
}}
"""

    try:
        response = client.models.generate_content(
            model=config.MODEL_ROUTER_FAST,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text.strip())
        return RoutingDecision(
            agent_id=data.get("agent_id", "web_search_agent"),
            confidence=float(data.get("confidence", 0.85)),
            intent=data.get("intent", "process_query"),
            arguments=data.get("arguments", {}),
            explanation=data.get("explanation", "Routed via Central Brain semantic reasoning."),
            is_fast_path=False
        )
    except Exception as e:
        return _fallback_keyword_classify(command, error_note=f"Gemini routing error: {e}")


def _fallback_keyword_classify(command: str, error_note: str = "") -> RoutingDecision:
    """Zero-AI keyword scoring fallback if Gemini API is unreachable or offline."""
    q = command.lower()
    scores: Dict[str, int] = {}

    for agent_id, meta in agent_registry.REGISTRY.items():
        score = 0
        for kw in meta.keywords:
            if kw in q:
                score += len(kw)
        scores[agent_id] = score

    best_agent = max(scores, key=scores.get)
    if scores[best_agent] > 0:
        return RoutingDecision(
            agent_id=best_agent,
            confidence=0.75,
            intent="general_request",
            arguments={"query": command},
            explanation=f"Routed to {agent_registry.REGISTRY[best_agent].name} based on keyword match.",
            is_fast_path=False
        )

    # If nothing matched, default to web_search_agent or code_assistant_agent
    if any(term in q for term in ["def ", "class ", "function", "import ", "error", "traceback"]):
        default_agent = "code_assistant_agent"
    else:
        default_agent = "web_search_agent"

    return RoutingDecision(
        agent_id=default_agent,
        confidence=0.60,
        intent="general_query",
        arguments={"query": command},
        explanation=f"Default routing to {agent_registry.REGISTRY[default_agent].name}. {error_note}",
        is_fast_path=False
    )


def classify_command(command: str) -> RoutingDecision:
    """Main routing pipeline: attempts Fast-Path first, then AI Semantic reasoning."""
    if config.FAST_PATH_REGEX_ENABLED:
        fast_result = fast_path_classify(command)
        if fast_result is not None:
            return fast_result

    if config.ENABLE_AI_FALLBACK:
        return ai_classify(command)
    else:
        return _fallback_keyword_classify(command)
