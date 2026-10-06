# Autonomous Multi-Agent System

An intelligent, modular multi-agent automation ecosystem built with Python.

## 🌟 Overview

This repository contains an extensible suite of specialized autonomous agents coordinated by a **Central Brain** routing system.

### Included Agents

1. **Central Brain (`central_brain/`)**:
   - Master coordinator and intent classifier.
   - Dispatches tasks to appropriate specialized agents and includes a management UI.

2. **Code Assistant Agent (`code_assistant_agent/`)**:
   - Code analysis, execution, refactoring, and debugging assistance.

3. **Web Search Agent (`web_search_agent/`)**:
   - Advanced web search, live lookups, research reporting, PDF/HTML/CSV export, browser media control, and voice engine.

4. **Email Agent (`email_agent/`)**:
   - Gmail integration for drafting, organizing, searching, and sending emails.

5. **File Manager Agent (`file_manager_agent/`)**:
   - Intelligent local file operations, searching, organizing, and batch processing.

6. **Memory Agent (`memory_agent/`)**:
   - Persistent memory and vector embeddings for long-term context retention across sessions.

7. **Reminder Agent (`reminder_agent/`)**:
   - Scheduling, alerting, and notification engine for tasks and events.

8. **System Monitor Agent (`system_monitor_agent/`)**:
   - Real-time CPU, RAM, disk, network, and battery performance monitoring.

9. **Volume & Brightness Agent (`volume_brightness_agent/`)**:
   - System media, sound, and screen brightness controls with a web dashboard server.

10. **App Control Agent (`app_control_agent/`)**:
    - Application launcher, window manager, and process controller.

---

## 🚀 Getting Started

### Quick Launch Scripts (Windows)

- **Main Menu**: Double-click `run_menu.bat`
- **Central Brain CLI**: Double-click `run_brain.bat`
- **Central Brain UI**: Double-click `run_brain_ui.bat`

### Individual Agent Execution

Each agent directory includes its own `run.bat` and `requirements.txt`. To run any agent standalone:

```bash
cd <agent_folder>
pip install -r requirements.txt
python <agent_name>.py
```
