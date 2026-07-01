# IRL-Stream-Steuerung

Ein Setup, um **IRL** (unterwegs, nur mit dem Handy) stabil auf Twitch zu streamen –
inklusive einer **Web-App** für Streamer & Mods, mit der sich der Stream von überall
steuern und überwachen lässt.

## Aufbau (kurz)

- **Handy (Moblin)** sendet das Bild per SRT/SRTLA an einen **Stream-PC zu Hause**.
- Auf dem PC läuft **OBS** (Bild + Overlays) und sendet zu Twitch.
- **go-irl** setzt die gebündelte Handy-Verbindung wieder zusammen.
- Der **Wächter** (`monitoring/watchdog.py`) überwacht alles, heilt Abstürze,
  schaltet bei schwachem Signal automatisch auf Pause (Auto-Switch), macht Backups
  und alarmiert per Telegram.
- Die **Streamer-App** (`monitoring/app.html`) ist die Fernbedienung: Live/BRB/Ende,
  Status-Ampel, Mod-Chat, Twitch-Titel/Clip/Raid, Aufnahme, Logbuch u. v. m.

## Ordner

| Ordner | Inhalt |
|--------|--------|
| `monitoring/` | Wächter (Python) + Web-App, Login, Overlays-Anbindung |
| `chatbot/`    | Twitch-Chat-Bot (!start/!live/!brb/!stop) |
| `goirl/`      | Start-Dateien für das SRTLA-Bonding (go-irl) |
| `overlays/`   | Browser-Overlays (Start Soon, BRB, Ende, Standort) |
| `tools/`      | Setup-Check |
| `01-…18-*.md` | Schritt-für-Schritt-Anleitungen |

## Einrichtung

1. Python 3 installieren.
2. Pro Ordner die Abhängigkeiten installieren:
   `pip install -r monitoring/requirements.txt` (und `chatbot/requirements.txt`),
   außerdem `pip install websocket-client`.
3. **Konfiguration anlegen:** jeweils `config.example.ini` nach `config.ini` kopieren
   und die eigenen Werte (Tokens, Passwörter, Nutzer) eintragen.
   > ⚠️ `config.ini` und Token-Dateien sind per `.gitignore` ausgeschlossen –
   > niemals echte Geheimnisse committen.
4. OBS mit obs-websocket einrichten (Szenen: Start Soon / Live / BRB / Ende).
5. Wächter starten: `monitoring/start_watchdog.bat`.

Details stehen in den nummerierten `*.md`-Anleitungen.

## Sicherheit

Echte Tokens/Passwörter gehören **nur** in die lokale `config.ini` (nicht im Repo).
Die App ist über einen Cloudflare-Tunnel mit eigenem Login erreichbar – kein offener
Port am Router.
