@echo off
title Orion Agent - Brightness & Volume Control
cd /d "%~dp0"
echo Starting Brightness & Volume Control Agent...
echo.
python volume_brightness_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred.
    pause
)
