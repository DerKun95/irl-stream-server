# Schritt 10 – Server vom Handy überwachen (Telegram + lokale KI)

Ziel: Wenn der Laptop in der Ecke steht, siehst du Probleme **sofort auf dem
Handy** – und eine **lokale KI** (läuft komplett auf dem Laptop, keine Cloud)
erklärt dir auf Nachfrage, was los ist und was zu tun ist.

**So funktioniert es:** Ein Wächter-Programm (`monitoring/watchdog.py`) läuft
dauerhaft auf dem Laptop. Es prüft jede Minute CPU, RAM, Speicher, Internet,
OBS, Stream-Status, verworfene Frames und ob das Handy-Signal ankommt. Bei
Problemen schickt es dir eine Telegram-Nachricht. Vom Handy aus kannst du
`/status` und `/ki` schicken.

| Befehl       | Was passiert                                              |
|--------------|-----------------------------------------------------------|
| `/status`    | kompletter Gesundheits-Check als Nachricht                 |
| `/ki`        | lokale KI analysiert den aktuellen Zustand                 |
| `/ki <Frage>`| beliebige Frage, KI kennt dabei die aktuellen Messwerte    |
| `/hilfe`     | Befehlsübersicht                                          |

---

## 10.1 – Telegram-Bot anlegen (5 Minuten)

1. Telegram auf dem Handy öffnen → nach **`@BotFather`** suchen (blauer Haken).
2. `/newbot` senden → Namen vergeben (z. B. „Server Wächter“) → Benutzernamen
   vergeben (muss auf `bot` enden, z. B. `streamer_server_bot`).
3. BotFather antwortet mit einem **Token** (Form `123456789:AAE...`).
   **Kopieren** – kommt gleich in die config.

---

## 10.2 – Ollama + Qwen3 4B auf dem Laptop installieren

1. Auf dem Laptop <https://ollama.com/download/windows> öffnen →
   **OllamaSetup.exe** herunterladen und installieren (läuft danach unsichtbar
   im Hintergrund, Symbol unten rechts).
2. Eingabeaufforderung öffnen (`Win + R` → `cmd`) und das Modell laden:
   ```
   ollama pull qwen3:4b
   ```
   (~2,5 GB Download, einmalig.)
3. Kurztest:
   ```
   ollama run qwen3:4b "Sag Hallo"
   ```
   → kommt eine Antwort, läuft die KI. (Mit `/bye` beenden.)

> Die KI rechnet auf dem Laptop. Während eines laufenden Streams `/ki` sparsam
> nutzen – Antworten dauern ein paar Sekunden und erzeugen kurz Last.

---

## 10.3 – Wächter einrichten

1. Den Ordner **`monitoring`** auf den Laptop kopieren (z. B. nach
   `C:\monitoring`, per RustDesk-Dateiübertragung wie beim Chat-Bot).
2. Auf dem Laptop im Ordner: Adressleiste → `cmd` → Enter →
   ```
   python -m pip install -r requirements.txt
   ```
3. `config.example.ini` kopieren → in **`config.ini`** umbenennen → ausfüllen:
   - `token` = der BotFather-Token aus 10.1
   - `chat_id` = **erstmal leer lassen** (kommt in 10.4)
   - `password` = dein OBS-WebSocket-Passwort (dasselbe wie beim Chat-Bot)
   - `srt_source` = exakter Name deiner SRT-Quelle (Standard: `Handy SRT`)
4. **`start_watchdog.bat`** doppelklicken → „Server-Wächter gestartet.“

---

## 10.4 – Verbinden & testen

1. In Telegram deinen neuen Bot suchen (der Benutzername aus 10.1) →
   **`/start`** senden.
2. Der Bot antwortet mit deiner **Chat-ID** → diese in der `config.ini` bei
   `chat_id =` eintragen → Wächter-Fenster schließen → `start_watchdog.bat`
   neu starten. (Ab jetzt gehorcht der Bot **nur dir**.)
3. Testen:
   - `/status` → Statusübersicht kommt aufs Handy
   - `/ki` → die lokale KI analysiert den Zustand
   - Alarm-Probe: OBS kurz schließen → nach ≤1 Minute kommt
     „⚠️ OBS ist NICHT geöffnet!“ → OBS wieder starten → „✅ OBS läuft wieder.“

---

## 10.5 – Autostart

`Win + R` → `shell:startup` → Verknüpfung von **`start_watchdog.bat`**
hineinlegen (zusätzlich zu OBS und `start_bot.bat`). Nach jedem Neustart laufen
dann: OBS, Chat-Bot, Wächter, Tailscale, RustDesk – der Server meldet sich von
selbst, wenn etwas klemmt.

---

## 10.6 – Für tiefe Eingriffe: RustDesk auch auf dem Handy

Wenn der Wächter ein Problem meldet, das du „per Hand“ beheben musst:

1. **Tailscale-App** aufs Handy (App Store) → mit deinem Konto anmelden → VPN an.
2. **RustDesk-App** aufs Handy → Laptop-ID (oder `DEINE-TAILSCALE-IP`) + dein
   RustDesk-Passwort → du steuerst den Laptop-Bildschirm vom Handy.

Damit hast du die komplette Werkstatt in der Hosentasche: Wächter meldet,
KI erklärt, RustDesk repariert.

---

## Typischer Ablauf bei einer Störung

1. 📳 Push: „⚠️ Verworfene Frames steigen (12 %)…“
2. Du: `/ki` → KI: „Das Netz zum Handy ist zu schwach. Bitrate in Moblin
   senken oder latency erhöhen; bei Funkloch Stand-by-Szene…“
3. Du (oder ein Mod) im Twitch-Chat: `!start` (Stand-by) bis das Signal wieder
   stabil ist, dann `!live`.

---

## NACHTRAG: Ausbaustufe 2 (Juni 2026)

Der Waechter kann inzwischen deutlich mehr:

| Neu | Was es tut |
|-----|------------|
| `/foto` | schickt ein Bild der aktuellen OBS-Szene aufs Handy |
| `/golive` | Uebertragung an + Szene "Live" |
| `/standby` | Szene "Start Soon" zeigen (Uebertragung an) |
| `/streamstop` | Uebertragung beenden |
| `/aus` `/neustart` `/abbrechen` | Server herunterfahren/neustarten (siehe Datei 11) |
| Auto-Heal | stuerzt OBS oder der Chat-Bot ab, startet der Waechter sie selbst neu und meldet es |
| Stream-Bericht | nach jedem Stream: Dauer, Drop-Quote, Reconnects, Max-Temperatur |
| Wochen-Backup | sichert Configs + OBS-Szenen automatisch nach D:\Backups |
| `!brb` (Twitch-Chat) | kurze Pause: Szene "Start Soon", ohne den Stream zu beenden |

**Einmalig in der `config.ini` des Waechters ergaenzen** (neue Abschnitte, siehe
config.example.ini): `[autoheal]` mit dem Pfad zur `start_bot.bat` und
`[backup]` mit dem Chat-Bot-Ordner. Ohne diese Eintraege laufen die neuen
Funktionen mit sinnvollen Standardwerten; nur der Auto-Neustart des Chat-Bots
und dessen Backup brauchen die Pfade.

---

## NACHTRAG: Ausbaustufe 3 (Juni 2026) – Dashboard, Grafiken, Tastatur

| Neu | Was es tut |
|-----|------------|
| 📱 **Handy-Dashboard** | Webseite mit Live-Werten, Szenen-Foto, Verlaufs-Grafiken und großen Knöpfen (Go Live / Standby / Stream beenden). Adresse vom Handy (Tailscale an): `http://DEINE-TAILSCALE-IP:8181/` – im Heimnetz auch `http://<Laptop-IP>:8181/`. Tipp: in Safari/Chrome **„Zum Home-Bildschirm hinzufügen“** → fühlt sich an wie eine App. |
| 📈 **Verlaufs-Grafiken** | Der Wächter zeichnet jede Minute Temperatur, CPU/RAM, Bitrate und Drop-Quote auf (24 h, Datei `verlauf.csv`). Die Kurven siehst du im Dashboard. |
| 🔘 **Telegram-Tastatur** | Nach einmal `/hilfe` senden erscheinen feste Knöpfe unter dem Chat – nie wieder Befehle tippen. (`/aus` ist absichtlich KEIN Knopf – Tippschutz.) |

**Sicherheit:** Der Dashboard-Port 8181 ist in der FritzBox **nicht freigegeben** –
aus dem Internet unerreichbar, nur Heimnetz + Tailscale. Optional kann in der
`config.ini` unter `[dashboard]` ein `key` gesetzt werden, dann lautet die
Adresse `http://...:8181/?key=DEINSCHLUESSEL`.

**Einrichtung:** Neue `watchdog.py` + neue Datei `dashboard.html` in den
`monitoring`-Ordner auf dem Laptop kopieren, Wächter-Fenster schließen,
`start_watchdog.bat` neu starten. Fertig – keine Config-Änderung nötig.
