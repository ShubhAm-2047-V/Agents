@echo off
title Orion Agent - App Control
cd /d "%~dp0"
echo Starting App Control Agent...
echo.
python app_control_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred.
    pause
)
