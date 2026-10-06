@echo off
title Orion Agent - Web Search
cd /d "%~dp0"
echo Starting Web Search Agent...
echo.
python web_search_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred.
    pause
)
