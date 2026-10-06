@echo off
title Orion Agent - System Monitor
cd /d "%~dp0"
echo Starting System Monitor Agent...
echo.
python system_monitor_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred.
    pause
)
