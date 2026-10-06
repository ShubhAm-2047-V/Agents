@echo off
title Orion Agent - Reminder & Scheduler
cd /d "%~dp0"
echo Starting Reminder Agent...
echo.
python reminder_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred.
    pause
)
