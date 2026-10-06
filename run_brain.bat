@echo off
title Orion Central Brain Orchestrator
cd /d "%~dp0"
python -m central_brain.brain
pause
