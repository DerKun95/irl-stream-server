@echo off
REM ==========================================================================
REM  Startet go-irl (SRTLA-Bonding-Empfaenger).
REM  - Diese Datei in den go-irl-Ordner legen (neben go-irl.exe)
REM  - WICHTIG: OBS muss bereits laufen, bevor go-irl startet!
REM  - Im Autostart wartet die Datei deshalb 45 Sekunden.
REM
REM  Ports:
REM    -srtla-port 53128 -> hierhin sendet Moblin (FritzBox: UDP 53128 freigeben!)
REM    OBS-Quelle bekommt den Stream auf udp://127.0.0.1:5002
REM ==========================================================================
cd /d "%~dp0"
echo Warte 45 Sekunden, damit OBS fertig gestartet ist...
timeout /t 45 /nobreak >nul
echo Starte go-irl (SRTLA-Empfaenger)... Fenster offen lassen!
go-irl.exe -mode=standalone -srtla-port=53128 -passphrase "DEINE_PASSPHRASE_HIER"
echo.
echo go-irl wurde beendet. Taste druecken zum Schliessen.
pause >nul
