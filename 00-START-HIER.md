# IRL-Streaming-Relay auf Windows 10 – Start hier

Dein Laptop wird ein **dauerhaft laufender IRL-Streaming-Server** bei dir zu Hause:

**Handy (Moblin-App) → SRT/Tailscale → Server-Laptop (OBS) → Twitch-Kanal der Streamerin**

Der Laptop steht bei dir in der Ecke und ist immer an. Eine befreundete Streamerin
nutzt ihn: Unterwegs sendet sie mit Moblin über das VPN zum Server, und der Server
streamt auf **ihren** Twitch-Kanal. Gesteuert wird der Stream bequem **über den
Twitch-Chat** (`!start`, `!live`, `!stop`) – durch dich, sie oder andere Mods.

Kein Schnickschnack, keine KI, keine Docker-Container. Alles ist für Einsteiger
erklärt.

## Deine Hardware

| Teil      | Wert                                      | Rolle im Relay                          |
|-----------|-------------------------------------------|-----------------------------------------|
| CPU       | Intel i7-7700HQ (4 Kerne / 8 Threads)     | reicht locker für 720p-Relay            |
| GPU       | NVIDIA GTX 1060 Mobile (6 GB)             | Encoding über NVENC (entlastet die CPU) |
| RAM       | 16 GB                                     | mehr als genug                          |
| SSD       | 256 GB Micron 1100                        | **Windows + OBS** (schnell)             |
| HDD       | 1 TB Toshiba MQ01ABD100                   | **lokale Aufnahmen / Backup** (Archiv)  |
| Netzwerk  | LAN-Kabel zum Router                      | stabile Anbindung                       |

> **Festplatten-Aufteilung merken:** Windows und OBS laufen auf der **schnellen SSD
> (C:)**. Die große **HDD (D:)** nutzt du nur, um Aufnahmen/Backups abzulegen – so
> bleibt die SSD frei und schnell.

## Reihenfolge – arbeite die Dateien so ab

1. **`01-WINDOWS-NEU-AUFSETZEN.md`** – Windows sauber zurücksetzen (Müll weg),
   Treiber, Updates, Energieeinstellungen.
2. **`02-OBS-EINRICHTEN.md`** – OBS installieren und für Twitch + SRT einstellen.
3. **`03-MOBLIN-HANDY.md`** – die Streaming-App auf dem Handy einrichten.
4. **`04-FERNZUGRIFF.md`** – Tailscale (VPN) + RustDesk, damit du und ein Freund
   den Laptop von überall bedienen könnt.
5. **`05-TESTPLAN.md`** – alles testen, bevor du live gehst.
6. **`06-PROBLEMHILFE.md`** – was tun bei Rucklern, Abbrüchen, schlechtem Netz.
7. **`07-CHAT-STEUERUNG.md`** – den Stream über den Twitch-Chat steuern
   (`!start` / `!live` / `!stop`), Szenen „Start Soon“ + „Live“, Bot einrichten.
   Der Chat-Bot selbst liegt im Ordner **`chatbot/`**.

## Was du vorher bereitlegen solltest

- Deine **Twitch-Zugangsdaten** (für den Stream-Schlüssel).
- Dein **Handy** mit installierter **Moblin-App** (kostenlos im App Store).
- Ein **LAN-Kabel** vom Laptop zum Router.
- Etwas Zeit: das Zurücksetzen + Einrichten dauert zusammen ca. 2–3 Stunden
  (viel davon ist Wartezeit beim Herunterladen).

> Wichtig: Beim Zurücksetzen werden **alle Daten auf dem Laptop gelöscht**. Falls
> doch noch etwas Wichtiges drauf ist, vorher auf einen anderen Computer oder in
> die Cloud sichern.
