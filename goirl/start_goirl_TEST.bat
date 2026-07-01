@echo off
REM ==========================================================================
REM  TEST-Start fuer go-irl - OHNE die 45-Sekunden-Wartezeit.
REM  Nur zum Einrichten/Ausprobieren benutzen (OBS vorher manuell starten).
REM  Fuer den Autostart spaeter die normale start_goirl.bat verwenden.
REM ==========================================================================
cd /d "%~dp0"
echo Starte go-irl (SRTLA-Empfaenger) - Testmodus, Fenster offen lassen!
go-irl.exe -mode=standalone -srtla-port=53128 -passphrase "DEINE_PASSPHRASE_HIER"
echo.
echo go-irl wurde beendet. Taste druecken zum Schliessen.
pause >nul
