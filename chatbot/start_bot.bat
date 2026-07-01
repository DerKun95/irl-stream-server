@echo off
REM ==========================================================================
REM  Startet den Twitch-Chat-Bot. Doppelklick zum Starten.
REM  Beim ersten Mal vorher einmal die Pakete installieren:
REM      pip install -r requirements.txt
REM ==========================================================================
cd /d "%~dp0"
echo Starte Chat-Bot... (Fenster offen lassen! Schliessen = Bot aus)
python bot.py
echo.
echo Bot wurde beendet. Taste druecken zum Schliessen.
pause >nul
