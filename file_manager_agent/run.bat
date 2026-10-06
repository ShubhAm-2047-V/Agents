@echo off
title Orion Agent - File Manager
cd /d "%~dp0"
echo Starting File Manager Agent...
echo.
python file_manager_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred.
    pause
)
