@echo off
title Server-Waechter
cd /d "%~dp0"
:schleife
echo [%date% %time%] Waechter startet ...
python watchdog.py
echo.
echo [%date% %time%] Waechter wurde beendet - automatischer Neustart in 10 Sekunden.
echo (Fenster schliessen, um ihn wirklich zu beenden.)
timeout /t 10 /nobreak >nul
goto schleife
