@echo off
title Orion Agent - Email
cd /d "%~dp0"
echo Starting Email Agent...
echo.
python email_agent.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred.
    pause
)
