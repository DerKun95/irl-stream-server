@echo off
title Setup-Check IRL-Server
cd /d "%~dp0"
python check-setup.py
echo.
echo Fertig. Taste druecken zum Schliessen.
pause >nul
