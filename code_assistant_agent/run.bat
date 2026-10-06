@echo off
title Orion Agent - Code Assistant
cd /d "%~dp0"
echo Starting Code Assistant Agent...
echo.
python code_assistant_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred.
    pause
)
