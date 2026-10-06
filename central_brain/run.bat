@echo off
title Orion Central Brain
cd /d "%~dp0.."
python -m central_brain.brain
pause
