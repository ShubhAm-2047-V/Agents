@echo off
title Orion Multi-Agent Launcher
cd /d "%~dp0"

:menu
cls
echo ====================================================
echo             ORION PC JARVIS AGENT LAUNCHER
echo ====================================================
echo.
echo   [*] CENTRALIZED BRAIN COMMAND CENTER
echo   [U] Launch Central Brain UI (Always-on-Top Floating HUD)
echo   [B] Launch Central Brain CLI (Terminal Dispatcher)
echo.
echo   [*] INDIVIDUAL SPECIALIZED AGENTS
echo   [1] App Control Agent      (Apps, Windows, Process Control)
echo   [2] System Monitor Agent   (CPU, RAM, Disks, Live Telemetry)
echo   [3] Reminder Agent         (Alarms, Reminders, Background Loop)
echo   [4] Memory Agent           (Persistent SQLite Memory Store)
echo   [5] File Manager Agent     (Search, Organize, Summarize Files)
echo   [6] Code Assistant Agent   (Write, Explain, Debug, Run Code)
echo   [7] Web Search Agent       (DuckDuckGo Search & News)
echo   [8] Email Agent            (Gmail Reader, Summarizer, Drafter)
echo   [9] Brightness & Volume    (In-CMD Live Dashboard, Presets & Mixer)
echo.
echo   [0] Exit
echo ====================================================
set /p choice="Select an option (U, B, 1-9, 0): "

if /i "%choice%"=="U" (
    start "Orion Central Brain HUD" cmd /k "cd /d "%~dp0" && run_brain_ui.bat"
    goto menu
)
if /i "%choice%"=="B" (
    start "Orion Central Brain CLI" cmd /k "cd /d "%~dp0" && run_brain.bat"
    goto menu
)
if "%choice%"=="1" (
    start "App Control Agent" cmd /k "cd /d "%~dp0app_control_agent" && run.bat"
    goto menu
)
if "%choice%"=="2" (
    start "System Monitor Agent" cmd /k "cd /d "%~dp0system_monitor_agent" && run.bat"
    goto menu
)
if "%choice%"=="3" (
    start "Reminder Agent" cmd /k "cd /d "%~dp0reminder_agent" && run.bat"
    goto menu
)
if "%choice%"=="4" (
    start "Memory Agent" cmd /k "cd /d "%~dp0memory_agent" && run.bat"
    goto menu
)
if "%choice%"=="5" (
    start "File Manager Agent" cmd /k "cd /d "%~dp0file_manager_agent" && run.bat"
    goto menu
)
if "%choice%"=="6" (
    start "Code Assistant Agent" cmd /k "cd /d "%~dp0code_assistant_agent" && run.bat"
    goto menu
)
if "%choice%"=="7" (
    start "Web Search Agent" cmd /k "cd /d "%~dp0web_search_agent" && run.bat"
    goto menu
)
if "%choice%"=="8" (
    start "Email Agent" cmd /k "cd /d "%~dp0email_agent" && run.bat"
    goto menu
)
if "%choice%"=="9" (
    start "Brightness & Volume Agent" cmd /k "cd /d "%~dp0volume_brightness_agent" && run.bat"
    goto menu
)
if "%choice%"=="0" exit

echo Invalid selection.
timeout /t 2 >nul
goto menu
