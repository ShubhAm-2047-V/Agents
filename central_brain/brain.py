"""
brain.py
Core Centralized Brain Orchestration Engine for Orion.
Coordinates user input, classifies intent, transfers the command to the
target agent, executes the operation, and formats the output.
"""

import os
import sys
import time
import json
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR_OK = True
except ImportError:
    COLOR_OK = False
    class Fore:
        CYAN = GREEN = YELLOW = RED = MAGENTA = BLUE = WHITE = LIGHTBLUE_EX = LIGHTCYAN_EX = LIGHTGREEN_EX = LIGHTYELLOW_EX = LIGHTRED_EX = RESET = ""
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ""

# Ensure workspace root in sys.path
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

try:
    from . import config, agent_registry, classifier
    from .classifier import RoutingDecision
except ImportError:
    import config, agent_registry, classifier
    from classifier import RoutingDecision


class BrainResult:
    """Structured response from the Central Brain execution."""
    def __init__(
        self,
        command: str,
        agent_id: str,
        agent_name: str,
        intent: str,
        success: bool,
        output: Any,
        execution_time_ms: float,
        is_fast_path: bool,
        explanation: str
    ):
        self.command = command
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.intent = intent
        self.success = success
        self.output = output
        self.execution_time_ms = execution_time_ms
        self.is_fast_path = is_fast_path
        self.explanation = explanation

    def __str__(self) -> str:
        if isinstance(self.output, (dict, list)):
            return json.dumps(self.output, indent=2)
        return str(self.output)


class CentralBrain:
    """
    Central Brain of the Orion Multi-Agent System.
    Receives user commands, identifies the target agent, dispatches the task,
    and returns a unified result.
    """

    def __init__(self):
        self.history: List[BrainResult] = []
        self._boot_time = time.time()

    def get_status(self) -> Dict[str, Any]:
        """Returns health status of the Central Brain and all connected agents."""
        agent_status = agent_registry.check_all_agents_health()
        active_count = sum(1 for a in agent_status.values() if a["available"])
        return {
            "title": config.APP_TITLE,
            "version": config.VERSION,
            "uptime_sec": int(time.time() - self._boot_time),
            "total_agents": len(agent_status),
            "active_agents": active_count,
            "agents": agent_status,
            "history_count": len(self.history)
        }

    def route_only(self, command: str) -> RoutingDecision:
        """Determines routing destination without executing."""
        return classifier.classify_command(command)

    def process_command(self, command: str) -> BrainResult:
        """
        Main interface: Analyzes command, routes to target agent, executes,
        and returns formatted result.
        """
        start_t = time.perf_counter()
        cmd_clean = command.strip()
        if not cmd_clean:
            return BrainResult(
                command=command,
                agent_id="none",
                agent_name="None",
                intent="empty",
                success=False,
                output="No command provided.",
                execution_time_ms=0.0,
                is_fast_path=True,
                explanation="Command was empty."
            )

        # 1. Routing classification
        decision = self.route_only(cmd_clean)
        agent_meta = agent_registry.get_agent(decision.agent_id)
        agent_name = agent_meta.name if agent_meta else decision.agent_id

        # 2. Execution dispatch
        success = True
        output = None
        try:
            output = self._dispatch(decision, cmd_clean)
        except Exception as e:
            success = False
            output = f"Execution Error on {agent_name}: {str(e)}"

        elapsed_ms = (time.perf_counter() - start_t) * 1000

        result = BrainResult(
            command=cmd_clean,
            agent_id=decision.agent_id,
            agent_name=agent_name,
            intent=decision.intent,
            success=success,
            output=output,
            execution_time_ms=round(elapsed_ms, 2),
            is_fast_path=decision.is_fast_path,
            explanation=decision.explanation
        )

        if config.LOG_ROUTING_HISTORY:
            self.history.append(result)
            if len(self.history) > config.MAX_HISTORY_ENTRIES:
                self.history.pop(0)

        return result

    def _dispatch(self, decision: RoutingDecision, raw_command: str) -> Any:
        """Executes the specific action on the selected agent."""
        agent_meta = agent_registry.get_agent(decision.agent_id)
        if not agent_meta:
            raise ValueError(f"Unknown agent '{decision.agent_id}'")

        module = agent_meta.module
        if module is None:
            raise RuntimeError(f"Could not load module for agent '{decision.agent_id}': {agent_meta._load_error}")

        agent_id = decision.agent_id
        intent = decision.intent
        args = decision.arguments

        # -------------------------------------------------------------
        # 1. Volume & Brightness Agent
        # -------------------------------------------------------------
        if agent_id == "volume_brightness_agent":
            if intent == "set_volume":
                return module.set_volume(args.get("level", 50))
            elif intent == "volume_up":
                return module.volume_up(args.get("delta", 10))
            elif intent == "volume_down":
                return module.volume_down(args.get("delta", 10))
            elif intent == "mute":
                return module.mute()
            elif intent == "unmute":
                return module.unmute()
            elif intent == "set_brightness":
                return module.set_brightness(args.get("level", 70))
            elif intent == "brightness_up":
                return module.brightness_up(args.get("delta", 10))
            elif intent == "brightness_down":
                return module.brightness_down(args.get("delta", 10))
            elif intent == "apply_preset":
                return module.apply_preset(args.get("preset_name", "movie"))
            elif intent == "media_play_pause":
                return module.media_play_pause()
            elif intent == "media_next":
                return module.media_next()
            elif intent == "media_prev":
                return module.media_prev()
            else:
                # Fallback to general process
                return module.get_volume()

        # -------------------------------------------------------------
        # 2. App Control Agent
        # -------------------------------------------------------------
        elif agent_id == "app_control_agent":
            if intent == "open_app":
                return module.open(args.get("app_name", ""))
            elif intent == "close_app":
                return module.close(args.get("app_name", ""))
            elif intent == "switch_to":
                return module.switch_to(args.get("title_contains", ""))
            elif intent == "minimize":
                return module.minimize(args.get("title_contains", ""))
            elif intent == "maximize":
                return module.maximize(args.get("app_name", ""))
            elif intent == "minimize_all":
                return module.minimize_all()
            elif intent == "list_running":
                apps = module.list_running()
                return {"running_apps_count": len(apps), "sample_apps": apps[:20]}
            else:
                parsed = module.parse_command(raw_command)
                return module.execute_parsed_actions(parsed)

        # -------------------------------------------------------------
        # 3. System Monitor Agent
        # -------------------------------------------------------------
        elif agent_id == "system_monitor_agent":
            if intent == "get_cpu":
                return module.get_cpu()
            elif intent == "get_ram":
                return module.get_ram()
            elif intent == "get_gpu":
                return module.get_gpu()
            elif intent == "get_all_disks":
                return module.get_all_disks()
            elif intent == "get_battery":
                return module.get_battery() or {"status": "No battery detected / Desktop PC"}
            elif intent == "get_temperatures":
                return module.get_temperatures()
            elif intent == "get_high_cpu_processes":
                return module.get_high_cpu_processes(limit=args.get("limit", 5))
            elif intent == "get_high_ram_processes":
                return module.get_high_ram_processes(limit=args.get("limit", 5))
            elif intent == "get_snapshot":
                return module.get_snapshot()
            else:
                return module.get_snapshot()

        # -------------------------------------------------------------
        # 4. Reminder Agent
        # -------------------------------------------------------------
        elif agent_id == "reminder_agent":
            if intent == "create_reminder_natural":
                # Check if parse_and_create or create_reminder exists
                if hasattr(module, "parse_and_create"):
                    return module.parse_and_create(args.get("text", raw_command))
                else:
                    return module.create_reminder(message=args.get("text", raw_command))
            elif intent == "list_reminders":
                return module.list_reminders()
            elif intent == "morning_briefing":
                return module.morning_briefing()
            elif intent == "evening_briefing":
                return module.evening_briefing()
            else:
                return module.list_reminders()

        # -------------------------------------------------------------
        # 5. File Manager Agent
        # -------------------------------------------------------------
        elif agent_id == "file_manager_agent":
            if intent == "clean_desktop":
                return module.clean_desktop()
            elif intent == "clean_downloads":
                return module.clean_downloads()
            elif intent == "duplicates":
                return module.duplicates(args.get("target", "Downloads"))
            elif intent == "storage_hogs":
                return module.storage_hogs(args.get("target", "Downloads"), limit=args.get("limit", 10))
            elif intent == "search":
                return module.search(args.get("pattern", "*"))
            else:
                return module.search(args.get("pattern", "*"))

        # -------------------------------------------------------------
        # 6. Memory Agent
        # -------------------------------------------------------------
        elif agent_id == "memory_agent":
            if intent == "remember_preference":
                return module.remember_preference(args.get("text", raw_command))
            elif intent == "list_all_memories":
                return module.store.get_all_memories()
            elif intent == "search_memory":
                return module.search_memory(args.get("query", raw_command))
            else:
                return module.search_memory(raw_command)

        # -------------------------------------------------------------
        # 7. Code Assistant Agent
        # -------------------------------------------------------------
        elif agent_id == "code_assistant_agent":
            if intent == "explain_code":
                return module.explain_code(args.get("code", raw_command))
            elif intent == "generate_code":
                return module.generate_code(args.get("prompt", raw_command))
            elif intent == "fix_bugs":
                return module.fix_bugs(code=args.get("code", raw_command), error_log=args.get("error", ""))
            else:
                return module.generate_code(raw_command)

        # -------------------------------------------------------------
        # 8. Email Agent
        # -------------------------------------------------------------
        elif agent_id == "email_agent":
            if intent == "read_emails":
                return module.read_emails(max_results=args.get("max_results", 5))
            elif intent == "find_unread_emails":
                return module.find_unread_emails()
            elif intent == "find_important_emails":
                return module.find_important_emails()
            elif intent == "daily_briefing":
                return module.daily_briefing()
            else:
                return module.read_emails(max_results=5)

        # -------------------------------------------------------------
        # 9. Web Search Agent
        # -------------------------------------------------------------
        elif agent_id == "web_search_agent":
            if intent == "open_website":
                success, site_name, url = module.browser_navigator.open_website(args.get("target", "https://shubh-deep-labs.vercel.app/"))
                return f"Successfully opened {site_name}: {url}" if success else f"Could not open {site_name}: {url}"
            elif intent == "weather_lookup":
                return module.weather_lookup(args.get("city", "New York"))
            elif intent == "stock_lookup":
                return module.stock_lookup(args.get("symbol", "AAPL"))
            elif intent == "raw_news":
                return module.raw_news(args.get("query", "news"))
            elif intent == "smart_search":
                return module.smart_search(args.get("query", raw_command))
            else:
                return module.smart_search(raw_command)

        # Generic fallback
        return f"Dispatched command to {agent_meta.name} successfully."


# ---------------------------------------------------------------------
# Interactive CLI Loop
# ---------------------------------------------------------------------
def print_banner(brain: CentralBrain):
    os.system("cls" if os.name == "nt" else "clear")
    status = brain.get_status()
    print(Fore.CYAN + Style.BRIGHT + "=" * 64)
    print(Fore.CYAN + Style.BRIGHT + f"   🧠 {config.APP_TITLE} (v{config.VERSION})")
    print(Fore.WHITE + "   Central Orchestrator & Command Dispatch Router")
    print(Fore.CYAN + Style.BRIGHT + "=" * 64)
    print(Fore.GREEN + f"  ● Status: ONLINE  |  Active Agents: {status['active_agents']}/{status['total_agents']}")
    print(Fore.WHITE + Style.DIM + "  Connected Agents:")
    for a_id, info in status["agents"].items():
        bullet = Fore.GREEN + "✓" if info["available"] else Fore.RED + "✗"
        print(f"    {bullet} {Fore.WHITE}{info['name']:<32} {Fore.LIGHTBLUE_EX}[{a_id}]")
    print(Fore.CYAN + "-" * 64)
    print(Fore.YELLOW + "  Type any command to transfer to the right agent.")
    print(Fore.YELLOW + "  Commands: /status, /agents, /history, /clear, /help, exit")
    print(Fore.CYAN + "=" * 64 + "\n")


def run_interactive_cli():
    brain = CentralBrain()
    print_banner(brain)

    while True:
        try:
            user_input = input(Fore.LIGHTGREEN_EX + Style.BRIGHT + "Orion Brain > " + Style.RESET_ALL).strip()
            if not user_input:
                continue

            # Special commands
            cmd_lower = user_input.lower()
            if cmd_lower in ["exit", "quit", "q"]:
                print(Fore.YELLOW + "\nShutting down Central Brain. Goodbye!\n")
                break
            elif cmd_lower == "/clear":
                print_banner(brain)
                continue
            elif cmd_lower == "/status":
                status = brain.get_status()
                print(Fore.CYAN + "\n--- Agent Status Matrix ---")
                for a_id, info in status["agents"].items():
                    stat = Fore.GREEN + "READY" if info["available"] else Fore.RED + f"FAIL ({info['error']})"
                    print(f"  [{a_id}] {info['name']}: {stat}")
                print(Fore.CYAN + "---------------------------\n")
                continue
            elif cmd_lower == "/agents":
                print(Fore.CYAN + "\n--- Available Agents & Capabilities ---")
                for meta in agent_registry.list_agents():
                    print(Fore.LIGHTYELLOW_EX + f"• {meta.name} ({meta.agent_id})")
                    print(Fore.WHITE + f"  {meta.description}")
                    print(Fore.LIGHTBLUE_EX + f"  Keywords: {', '.join(meta.keywords[:8])}\n")
                continue
            elif cmd_lower == "/history":
                print(Fore.CYAN + f"\n--- Command History ({len(brain.history)} entries) ---")
                for idx, h in enumerate(brain.history[-10:], 1):
                    route_type = "⚡ FAST-PATH" if h.is_fast_path else "🧠 AI SEMANTIC"
                    print(f"  {idx}. [{route_type}] '{h.command}' -> {h.agent_name} ({h.execution_time_ms}ms)")
                print(Fore.CYAN + "--------------------------------------\n")
                continue
            elif cmd_lower == "/help":
                print(Fore.YELLOW + "\n--- Example Commands you can give to the Central Brain ---")
                print("  • Volume & Brightness: 'volume 70', 'mute', 'dim screen', 'movie mode', 'pause music'")
                print("  • App Control: 'open chrome', 'close notepad', 'list running apps', 'minimize all'")
                print("  • System Monitor: 'cpu usage', 'how much ram is free', 'battery status', 'pc health'")
                print("  • Reminders: 'remind me to call John at 5pm', 'morning briefing', 'show reminders'")
                print("  • File Manager: 'clean desktop', 'find duplicates in downloads', 'storage hogs'")
                print("  • Memory: 'remember that my preferred language is python', 'what do you remember'")
                print("  • Code Assistant: 'write python script to fetch a REST api', 'explain this function'")
                print("  • Email: 'read emails', 'find unread emails', 'email briefing'")
                print("  • Web Search: 'search latest news on AI', 'weather in Tokyo', 'stock price of NVDA'")
                print(Fore.YELLOW + "---------------------------------------------------------\n")
                continue

            # Process natural language command through Central Brain
            print(Fore.LIGHTBLUE_EX + "⚡ Routing command...", end="\r")
            result = brain.process_command(user_input)

            route_badge = Fore.LIGHTGREEN_EX + "[⚡ FAST-PATH]" if result.is_fast_path else Fore.MAGENTA + "[🧠 AI-ROUTED]"
            print(f"{route_badge} {Fore.CYAN}→ Transferred to: {Fore.YELLOW}{result.agent_name} {Fore.WHITE}({result.execution_time_ms}ms)")
            print(Fore.WHITE + Style.DIM + f"   Intent: {result.intent} | {result.explanation}")
            print(Fore.CYAN + "─" * 50)

            # Print Output cleanly
            if isinstance(result.output, (dict, list)):
                formatted_json = json.dumps(result.output, indent=2)
                print(Fore.LIGHTWHITE_EX + formatted_json)
            else:
                print(Fore.LIGHTWHITE_EX + str(result.output))
            print(Fore.CYAN + "─" * 50 + "\n")

        except KeyboardInterrupt:
            print(Fore.YELLOW + "\nCentral Brain session ended.\n")
            break
        except Exception as e:
            print(Fore.RED + f"\nError processing command: {e}\n")


if __name__ == "__main__":
    run_interactive_cli()
