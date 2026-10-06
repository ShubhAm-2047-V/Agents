"""
app_control_agent.py
Main entry point for Orion's App Control Agent.

Direct operations (open/close/switch/list) are zero-cost, instant, and
handled by app_ops.py. The only AI-assisted piece is parse_command(),
which turns a natural language instruction into a structured action -
useful when the voice/text input isn't a clean "open chrome" command.

Usage from your main Orion router:

    from app_control_agent import app_control_agent as apps

    apps.open("chrome")
    apps.close("spotify")
    apps.switch_to("notepad")

    action = apps.parse_command("shut down discord and open vs code instead")
    # -> execute the returned action(s) yourself
"""

import os
import sys
import json

try:
    from . import config, app_ops
except ImportError:
    import config, app_ops


def _get_client():
    return genai.Client(api_key=config.GEMINI_API_KEY)


# ---------- Direct, zero-cost operations ----------

def open(name, use_search=None):
    return app_ops.open_app(name, use_search=use_search)


def close(name, force=False):
    return app_ops.close_app(name, force=force)


def switch_to(title_contains):
    return app_ops.switch_to_window(title_contains)


def minimize(title_contains):
    return app_ops.minimize_window(title_contains)


def side_by_side(left, right):
    return app_ops.tile_side_by_side(left, right)


def maximize(name):
    return app_ops.maximize_app(name)


def snap(name, direction="left"):
    return app_ops.snap_window(name, direction=direction)


def center(name):
    return app_ops.center_app(name)


def focus_only(name):
    return app_ops.focus_only_app(name)


def minimize_all():
    return app_ops.minimize_all_windows()


def grid_4(app1, app2, app3, app4):
    return app_ops.tile_grid_4(app1, app2, app3, app4)


def tile_3(app_main, app_tr, app_br):
    return app_ops.tile_layout_3(app_main, app_tr, app_br)


def is_running(name):
    return app_ops.is_running(name)


def list_running():
    return app_ops.list_running_apps()


def list_windows():
    return app_ops.list_open_windows()


def restart(name, wait_sec=2):
    return app_ops.restart_app(name, wait_sec=wait_sec)


def find_installed(query=""):
    return app_ops.find_installed_apps(query)


def open_file(file_path, app_name=None):
    return app_ops.open_file_with_app(file_path, app_name=app_name)


def open_folder(folder_path):
    return app_ops.open_folder(folder_path)


def launch_website(url_or_domain, browser=None):
    return app_ops.launch_website(url_or_domain, browser=browser)


def launch_dev_tool(tool_name):
    return app_ops.launch_dev_tool(tool_name)


def open_project(project_path, ide_name="code"):
    return app_ops.open_project_in_ide(project_path, ide_name=ide_name)


def start_server(project_path, command="npm run dev", port=None):
    return app_ops.start_dev_server(project_path, command=command, port=port)


def stop_server(server_id_or_pid):
    return app_ops.stop_dev_server(server_id_or_pid)


def list_servers():
    return app_ops.list_dev_servers()


def open_terminal(cwd=None, shell="powershell"):
    return app_ops.open_terminal(cwd=cwd, shell=shell)


def execute_safe_command(command_str, cwd=None, timeout=20):
    return app_ops.execute_safe_command(command_str, cwd=cwd, timeout=timeout)


def list_startup_apps():
    return app_ops.list_startup_apps()


def detect_frozen():
    return app_ops.detect_frozen_apps()


def force_close_unresponsive():
    return app_ops.force_close_unresponsive_apps()


def open_workspace(app_list, layout=None):
    return app_ops.open_workspace(app_list, layout=layout)


def create_workspace(name, apps=None, files=None, urls=None, folders=None, layout="side_by_side"):
    return app_ops.create_project_workspace(name, apps=apps, files=files, urls=urls, folders=folders, layout=layout)


def launch_workspace(name):
    return app_ops.launch_project_workspace(name)


def track_running():
    return app_ops.get_running_apps_detailed()


def confirm_dangerous_action(action_type, target, confirmed=False):
    return app_ops.confirm_dangerous_action(action_type, target, confirmed=confirmed)



# ---------- AI-assisted: natural language command parsing ----------

def _parse_command_offline(command_text):
    """
    Offline regex/rule-based command parser. No API calls or local LLM required.
    Parses sentences like 'open chrome', 'close discord and launch vs code',
    'switch to notepad', 'minimize spotify', 'list running apps', 'chatgpt and chrome side by side'.
    """
    import re
    import difflib

    text = command_text.strip().lower()
    actions = []

    # Common synonym normalization for Shubham's setup
    synonyms = {
        "editor": "antigravity",
        "code editor": "antigravity",
        "ide": "antigravity",
        "antigravity": "antigravity",
        "code": "antigravity",
        "browser": "chrome",
        "my browser": "chrome",
        "terminal": "cmd",
        "command prompt": "cmd",
        "prompt": "cmd",
        "cmd": "cmd",
        "shell": "cmd",
        "calc": "calculator",
        "files": "file explorer",
        "file": "file explorer",
        "file manager": "file explorer",
        "explorer": "file explorer",
        "note pad": "notepad",
        "notes": "notepad",
        "notepad": "notepad",
        "whats app": "whatsapp",
        "whatsapp": "whatsapp",
        "you tube": "youtube",
        "you": "youtube",
        "youtube": "youtube",
        "chat gpt": "chatgpt",
        "chat": "chatgpt",
        "ai": "chatgpt",
        "gpt": "chatgpt",
        "chatgpt": "chatgpt",
        "power shell": "powershell",
        "powershell": "powershell",
        "vs code": "vscode",
        "vscode": "vscode",
        "antigravity ide": "antigravity",
        "c": "chrome",
        "a": "antigravity",
        "g": "chatgpt",
        "n": "notepad",
        "t": "cmd",
        "w": "whatsapp",
        "y": "youtube",
    }

    # Check for listing commands
    if re.search(r"\b(list|show|get)\b.*\b(apps|running|processes|windows)\b", text) or text in ["running apps", "list apps", "list windows"]:
        return {"actions": [{"action": "list_running", "target": None}]}

    # Check for Minimize All / Clean Desktop
    if re.search(r"\b(?:minimize\s+all|clean\s+desktop|show\s+desktop|clear\s+screen)\b", text) or text in ["desktop", "min all"]:
        return {"actions": [{"action": "minimize_all"}]}

    # Check for Solo / Focus Only mode
    m_solo = re.search(r"\b(?:focus\s+only|solo(?:\s+mode)?|only\s+keep|only\s+show|hide\s+others|hide\s+distractions)\s+([a-zA-Z0-9_\-\. ]+)\b", text)
    if m_solo:
        target = m_solo.group(1).strip()
        target = re.sub(r"^(?:my|the|a|an)\s+", "", target).strip()
        target = synonyms.get(target, target)
        return {"actions": [{"action": "focus_only", "target": target}]}

    # Check for 4-App Quadrant Grid: grid a, b, c, d
    m_g4 = re.search(r"\b(?:grid(?:\s+4)?|4\s+way|quadrant)\s+([a-zA-Z0-9_\-\. ]+?)[,;\s]+([a-zA-Z0-9_\-\. ]+?)[,;\s]+([a-zA-Z0-9_\-\. ]+?)[,;\s]+(?:and\s+)?([a-zA-Z0-9_\-\. ]+)\b", text)
    if m_g4:
        raw_apps = [m_g4.group(i).strip() for i in range(1, 5)]
        clean_apps = [synonyms.get(re.sub(r"^(?:my|the|a|an)\s+", "", a).strip(), a) for a in raw_apps]
        return {"actions": [{"action": "grid_4", "apps": clean_apps}]}

    # Check for 3-App Layout: layout 3 a, b, c
    m_t3 = re.search(r"\b(?:layout\s+3|tile\s+3|3\s+way)\s+([a-zA-Z0-9_\-\. ]+?)[,;\s]+([a-zA-Z0-9_\-\. ]+?)[,;\s]+(?:and\s+)?([a-zA-Z0-9_\-\. ]+)\b", text)
    if m_t3:
        raw_apps = [m_t3.group(i).strip() for i in range(1, 4)]
        clean_apps = [synonyms.get(re.sub(r"^(?:my|the|a|an)\s+", "", a).strip(), a) for a in raw_apps]
        return {"actions": [{"action": "tile_3", "apps": clean_apps}]}

    # Check for Side-by-Side / Split Screen commands
    m_split = re.search(r"\b(?:give\s+me\s+|show\s+|put\s+|arrange\s+|open\s+|split\s+screen\s+|split\s+view\s+|split\s+|tile\s+)?([a-zA-Z0-9_\-\. ]+?)\s+and\s+([a-zA-Z0-9_\-\. ]+?)\s+(?:side\s+by\s+side|split\s+screen|split\s+view|split)\b", text)
    if not m_split:
        m_split = re.search(r"\b(?:split\s+screen|split\s+view|split|tile|side\s+by\s+side)\s+([a-zA-Z0-9_\-\. ]+?)\s+and\s+([a-zA-Z0-9_\-\. ]+)\b", text)

    if m_split:
        left = m_split.group(1).strip()
        right = m_split.group(2).strip()
        left = re.sub(r"^(?:my|the|a|an)\s+", "", left).strip()
        right = re.sub(r"^(?:my|the|a|an)\s+", "", right).strip()
        left = re.sub(r"^(?:split\s+screen(?:\s+for)?|split\s+view(?:\s+for)?|split(?:\s+screen)?|tile|give\s+me|show\s+me|show|put|arrange|open|launch|get)\s+", "", left).strip()
        right = re.sub(r"^(?:split\s+screen(?:\s+for)?|split\s+view(?:\s+for)?|split|tile|open|launch)\s+", "", right).strip()
        left = synonyms.get(left, left)
        right = synonyms.get(right, right)
        return {"actions": [{"action": "side_by_side", "left": left, "right": right}]}

    # Workspace Mode macros
    if re.search(r"\b(?:back\s+to\s+work|work\s+mode|start\s+work(?:ing)?|resume\s+work|get\s+back\s+to\s+work)\b", text):
        return {"actions": [
            {"action": "open", "target": "back to work"},
            {"action": "open", "target": "chatgpt"}
        ], "macro": "back_to_work"}

    if re.search(r"\b(?:back\s+from\s+work|done\s+work(?:ing)?|stop\s+work(?:ing)?|end\s+work|off\s+work|finish\s+work|wrap\s+up)\b", text):
        return {"actions": [
            {"action": "close", "target": "antigravity"},
            {"action": "close", "target": "chatgpt"}
        ], "macro": "back_from_work"}

    if re.search(r"\b(?:start\s+coding|coding\s+mode|dev\s+mode|setup\s+workspace)\b", text):
        return {"actions": [
            {"action": "open", "target": "antigravity"},
            {"action": "open", "target": "cmd"},
            {"action": "open", "target": "chrome"}
        ], "macro": "coding_mode"}

    if re.search(r"\b(?:study\s+mode|research\s+mode)\b", text):
        return {"actions": [
            {"action": "open", "target": "chrome"},
            {"action": "open", "target": "notepad"}
        ], "macro": "study_mode"}

    if re.search(r"\b(?:music\s+mode|chill\s+mode|relax\s+mode)\b", text):
        return {"actions": [
            {"action": "open", "target": "youtube"}
        ], "macro": "music_mode"}

    import difflib

    # Split multi-action commands connected with 'and', 'then', ';' or ','
    parts = re.split(r"\b(?:and|then)\b|[;,]", text)
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Maximize / Fullscreen
        m_max = re.search(r"\b(?:maximize|fullscreen|maximise)\s+([a-zA-Z0-9_\-\. ]+)", part)
        if m_max:
            target = m_max.group(1).strip()
            clean_target = re.sub(r"^(?:my|the|a|an)\s+", "", target).strip()
            target = synonyms.get(clean_target, synonyms.get(target, target))
            actions.append({"action": "maximize", "target": target})
            continue

        # Center window
        m_center = re.search(r"\b(?:center|centre)\s+([a-zA-Z0-9_\-\. ]+)", part)
        if m_center:
            target = m_center.group(1).strip()
            clean_target = re.sub(r"^(?:my|the|a|an)\s+", "", target).strip()
            target = synonyms.get(clean_target, synonyms.get(target, target))
            actions.append({"action": "center", "target": target})
            continue

        # Snap window left/right/top/bottom
        m_snap = re.search(r"\b(?:snap|position|align)\s+([a-zA-Z0-9_\-\. ]+?)\s+(?:to\s+)?(left|right|top|bottom|top_left|top_right|bottom_left|bottom_right)\b", part)
        if m_snap:
            target = m_snap.group(1).strip()
            direction = m_snap.group(2).strip()
            clean_target = re.sub(r"^(?:my|the|a|an)\s+", "", target).strip()
            target = synonyms.get(clean_target, synonyms.get(target, target))
            actions.append({"action": "snap", "target": target, "direction": direction})
            continue

        # Switch patterns (handles switch to, swiitch to, swtich to, focus, goto, etc.)
        m_switch = re.search(r"\b(?:sw+i+t+c?h(?:\s+to)?|swtich(?:\s+to)?|swich(?:\s+to)?|swtch(?:\s+to)?|switchto|focus(?:\s+on)?|bring\s+up|goto|go\s+to|jump\s+to)\s+([a-zA-Z0-9_\-\. ]+)", part)
        if m_switch:
            target = m_switch.group(1).strip()
            clean_target = re.sub(r"^(?:my|the|a|an)\s+", "", target).strip()
            target = synonyms.get(clean_target, synonyms.get(target, target))
            actions.append({"action": "switch_to", "target": target})
            continue

        # Open patterns (handles open, opne, oppen, launch, launhc, start, run, etc.)
        m_open = re.search(r"\b(?:o+p+e+n|opne|oppen|launch|launhc|luanch|start|run)\s+([a-zA-Z0-9_\-\. ]+)", part)
        if m_open:
            target = m_open.group(1).strip().replace("instead", "").strip()
            clean_target = re.sub(r"^(?:my|the|a|an)\s+", "", target).strip()
            target = synonyms.get(clean_target, synonyms.get(target, target))
            actions.append({"action": "open", "target": target})
            continue

        # Close patterns (handles close, clsoe, cose, shut down, shutdown, kill, exit, terminate, stop)
        m_close = re.search(r"\b(?:c+l+o+s+e|clsoe|cose|shut\s*down|shutdown|kill|exit|terminate|stop|quit)\s+([a-zA-Z0-9_\-\. ]+)", part)
        if m_close:
            target = m_close.group(1).strip().replace("instead", "").strip()
            clean_target = re.sub(r"^(?:my|the|a|an)\s+", "", target).strip()
            target = synonyms.get(clean_target, synonyms.get(target, target))
            actions.append({"action": "close", "target": target})
            continue

        # Minimize patterns (handles minimize, minimise, minmise, min)
        m_min = re.search(r"\b(?:m+i+n+i+m+i+[zs]e|minmise|minimize|minimise|min)\s+([a-zA-Z0-9_\-\. ]+)", part)
        if m_min:
            target = m_min.group(1).strip()
            clean_target = re.sub(r"^(?:my|the|a|an)\s+", "", target).strip()
            target = synonyms.get(clean_target, synonyms.get(target, target))
            actions.append({"action": "minimize", "target": target})
            continue

    if not actions:
        # Fallback: check if the whole input is just an app name to open or fuzzy match
        clean_name = text.strip()
        clean_target = re.sub(r"^(?:my|the|a|an)\s+", "", clean_name).strip()
        clean_name = synonyms.get(clean_target, synonyms.get(clean_name, clean_name))

        if clean_name in config.APP_ALIASES or clean_name in synonyms:
            resolved = synonyms.get(clean_name, clean_name)
            actions.append({"action": "open", "target": resolved})
        else:
            # Fuzzy match known apps
            all_known = list(config.APP_ALIASES.keys()) + list(synonyms.keys())
            close_app = difflib.get_close_matches(clean_target, all_known, n=1, cutoff=0.7)
            if close_app:
                resolved = synonyms.get(close_app[0], close_app[0])
                actions.append({"action": "open", "target": resolved})
            else:
                actions.append({"action": "unknown", "target": text})

    return {"actions": actions}


def parse_command(natural_language_command, force_offline=False):
    """
    Converts a natural language instruction into structured actions.
    Runs 100% offline via rule parser if offline mode is enabled, no API key
    is found, or force_offline=True. Falls back to Gemini Flash-Lite if needed.
    """
    has_api_key = bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY != "PASTE_YOUR_GEMINI_API_KEY_HERE")
    offline = getattr(config, "OFFLINE_MODE", True) or force_offline or not has_api_key

    if offline:
        return _parse_command_offline(natural_language_command)

    try:
        known_apps = ", ".join(config.APP_ALIASES.keys())
        prompt = f"""You are a command parser for a desktop app-control assistant.
Convert the user's instruction into a JSON object listing one or more actions.

Valid action types: "open", "close", "switch_to", "minimize", "maximize", "center", "snap", "side_by_side", "grid_4", "tile_3", "focus_only", "minimize_all", "list_running", "unknown"
Known app names: {known_apps}

Reply ONLY with valid JSON:
{{"actions": [{{"action": "...", "target": "..."}}]}}

User instruction: "{natural_language_command}"
"""
        client = _get_client()
        response = client.models.generate_content(model=config.MODEL, contents=prompt)
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception:
        return _parse_command_offline(natural_language_command)


def execute_parsed_actions(parsed):
    """
    Convenience helper: takes the dict returned by parse_command() and runs each action.
    """
    import time
    results = []
    actions_list = parsed.get("actions", [])
    for idx, item in enumerate(actions_list):
        action = item.get("action")
        target = item.get("target")
        try:
            if action == "open":
                results.append(open(target))
            elif action == "close":
                results.append(close(target))
            elif action == "switch_to":
                results.append(switch_to(target))
            elif action == "minimize":
                results.append(minimize(target))
            elif action == "maximize":
                results.append(maximize(target))
            elif action == "center":
                results.append(center(target))
            elif action == "snap":
                direction = item.get("direction", "left")
                results.append(snap(target, direction=direction))
            elif action == "focus_only":
                results.append(focus_only(target))
            elif action == "minimize_all":
                results.append(minimize_all())
            elif action == "side_by_side":
                left = item.get("left")
                right = item.get("right")
                results.append(side_by_side(left, right))
            elif action == "grid_4":
                apps = item.get("apps", [])
                if len(apps) >= 4:
                    results.append(grid_4(apps[0], apps[1], apps[2], apps[3]))
                else:
                    results.append("grid_4 requires 4 app names")
            elif action == "tile_3":
                apps = item.get("apps", [])
                if len(apps) >= 3:
                    results.append(tile_3(apps[0], apps[1], apps[2]))
                else:
                    results.append("tile_3 requires 3 app names")
            elif action == "list_running":
                results.append(list_running())
            elif action == "restart":
                results.append(restart(target))
            elif action == "find_installed":
                results.append(find_installed(target or ""))
            elif action == "open_file":
                results.append(open_file(target, app_name=item.get("app")))
            elif action == "open_folder":
                results.append(open_folder(target))
            elif action == "launch_website" or action == "website":
                results.append(launch_website(target, browser=item.get("browser")))
            elif action == "launch_dev_tool" or action == "dev_tool":
                results.append(launch_dev_tool(target))
            elif action == "open_project":
                results.append(open_project(target, ide_name=item.get("ide", "code")))
            elif action == "start_server":
                results.append(start_server(target, command=item.get("command", "npm run dev"), port=item.get("port")))
            elif action == "stop_server":
                results.append(stop_server(target))
            elif action == "list_servers":
                results.append(list_servers())
            elif action == "open_terminal":
                results.append(open_terminal(cwd=target, shell=item.get("shell", "powershell")))
            elif action == "execute_safe_command":
                results.append(execute_safe_command(target, cwd=item.get("cwd")))
            elif action == "list_startup_apps":
                results.append(list_startup_apps())
            elif action == "detect_frozen":
                results.append(detect_frozen())
            elif action == "force_close_unresponsive":
                results.append(force_close_unresponsive())
            elif action == "open_workspace":
                results.append(open_workspace(target, layout=item.get("layout")))
            elif action == "launch_workspace":
                results.append(launch_workspace(target))
            elif action == "track_running":
                results.append(track_running())
            elif action == "confirm_action":
                results.append(confirm_dangerous_action(item.get("action_type", "action"), target, confirmed=item.get("confirmed", False)))
            else:
                results.append(f"Unrecognized action: {action}")
        except Exception as e:
            results.append(f"Error on '{action}': {e}")
        
        # Small delay between multiple sequential actions
        if idx < len(actions_list) - 1:
            time.sleep(0.35)

    return results


if __name__ == "__main__":
    print("========================================")
    print("   Orion App Control Agent (Interactive)")
    print("========================================")
    print("Commands:")
    print("  - Type natural language (e.g. 'open chrome', 'close spotify', 'switch to notepad')")
    print("  - 'list' to show running apps")
    print("  - 'windows' to show open windows")
    print("  - 'exit' or 'quit' to close")
    print("========================================\n")

    while True:
        try:
            cmd = input("AppControl > ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            if cmd.lower() in ("list", "list running"):
                apps_list = list_running()
                print(f"\n[Running Apps ({len(apps_list)})]:")
                print(", ".join(apps_list[:25]) + ("..." if len(apps_list) > 25 else ""))
                print()
                continue
            if cmd.lower() in ("windows", "list windows"):
                wins = list_windows()
                print(f"\n[Open Windows ({len(wins)})]:")
                for w in wins:
                    print(f"  • {w}")
                print()
                continue

            parsed = parse_command(cmd)
            print("\n-> Parsed Actions:", parsed.get("actions"))
            results = execute_parsed_actions(parsed)
            for r in results:
                print(f"   {r}")
            print()
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"Error: {e}\n")
