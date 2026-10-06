@echo off
title Orion Agent - Memory
cd /d "%~dp0"
echo Starting Memory Agent...
echo.
python memory_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred.
    pause
)
