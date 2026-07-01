# Schritt 5 – Testplan (vor dem ersten echten Stream)

Hake jeden Punkt ab. Erst live gehen, wenn alles passt.

## A) Laptop-Grundlagen

| # | Test | Aktion | Erwartet |
|---|------|--------|----------|
| A1 | Windows frisch | Desktop aufgeräumt, Updates installiert | ja |
| A2 | Grafiktreiber | Rechtsklick Desktop → „NVIDIA Systemsteuerung“ vorhanden | ja |
| A3 | Schläft nicht | 10 Min nichts tun | Bildschirm/Gerät bleibt an |
| A4 | HDD bereit | Ordner `D:\Aufnahmen` existiert | ja |

## B) OBS

| # | Test | Aktion | Erwartet |
|---|------|--------|----------|
| B1 | Twitch verbunden | Einstellungen → Stream | Twitch-Konto/Schlüssel hinterlegt |
| B2 | Encoder | Einstellungen → Ausgabe | NVIDIA NVENC H.264, CBR, Keyframe 2 |
| B3 | Video | Einstellungen → Video | 720p, 30 FPS |
| B4 | SRT-Quelle | „Handy SRT“ Medienquelle vorhanden | listener-URL Port 9999 |
| B5 | Aufnahme-Ziel | Ausgabe → Aufnahme | Pfad `D:\Aufnahmen`, Format mkv |
| B6 | Stand-by-Szene | Szene „Verbindung verloren“ | vorhanden + Hotkey |

## C) Fernzugriff

| # | Test | Aktion | Erwartet |
|---|------|--------|----------|
| C1 | Tailscale Laptop | Taskleisten-Symbol | zeigt IP `100.x.y.z` |
| C2 | Tailscale Gaming-PC | gleiches Konto | sieht den Laptop |
| C3 | RustDesk | vom Gaming-PC verbinden | Laptop-Bildschirm sichtbar/steuerbar |
| C4 | Freund-Freigabe | teilen, testen, entfernen | klappt + wieder entzogen |

## D) Streaming-Kette (Hauptprobe)

| # | Test | Aktion | Erwartet | Bei Fehler |
|---|------|--------|----------|------------|
| D1 | Handy → Laptop | Moblin „Go Live“ an `srt://<Tailscale-IP>:9999?latency=2000000` | Bild in OBS | 06-PROBLEMHILFE.md |
| D2 | Laptop → Twitch | OBS „Stream starten“ | Bild auf Twitch sichtbar | 06-PROBLEMHILFE.md |
| D3 | Qualität | OBS-Statistiken ansehen | dropped frames nahe 0 | Bitrate senken |
| D4 | Schlechtes Netz | Handy kurz abdecken / Bitrate senken | Bild bleibt, kein Totalabriss | latency erhöhen |
| D5 | Abriss-Verhalten | SRT trennen | auf Stand-by-Szene wechseln können | Hotkey prüfen |
| D6 | Aufnahme | nach dem Test `D:\Aufnahmen` prüfen | mkv-Datei vorhanden | Aufnahme-Pfad prüfen |

## E) Dauerbetrieb

| # | Test | Aktion | Erwartet |
|---|------|--------|----------|
| E1 | Neustart-Test | Laptop neu starten | Tailscale + RustDesk laufen automatisch |
| E2 | Deckel zu | Laptopdeckel schließen (Netzbetrieb) | Stream läuft weiter |

## Abnahme

Bereit für echtes IRL, wenn **A, B, C, D** vollständig bestanden sind.
Empfehlung: den ersten echten Stream kurz und „privat“ (Twitch nur für dich
sichtbar) testen.
