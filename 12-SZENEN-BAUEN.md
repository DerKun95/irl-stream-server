# Schritt 12 – Die Szenen schön bauen (Overlays + Clips)

Drei Szenen, fertig gestylt:

| Szene        | Inhalt                                            | Wer schaltet hin               |
|--------------|----------------------------------------------------|--------------------------------|
| `Start Soon` | animiertes Overlay „Gleich geht's los“ (+ Clips)   | `!start`, `!brb`, `/standby`   |
| `Live`       | das Handybild (SRT)                                | `!live`, `/golive`             |
| `Ende`       | „Danke fürs Zuschauen“-Screen                      | `!stop` (optional)             |

Die Overlays liegen in **`irl-relay\overlays\`**:
- `start-soon.html` – animierter Lila-Verlauf, schwebende Punkte, pulsierender
  Text, Ladebalken, Uhrzeit
- `ende.html` – Sternenhimmel, schlagendes Herz, „Danke fürs Zuschauen“

> **Texte/Name ändern:** Datei mit dem Editor öffnen – ganz oben stehen
> `KANALNAME`, `ZEILE_GROSS`, `ZEILE_KLEIN` zum Anpassen.

---

## 12.1 – Overlays auf den Laptop kopieren

Den Ordner `overlays` per RustDesk auf den Laptop kopieren, z. B. nach
**`C:\overlays`**. (Pfad merken.)

## 12.2 – Szene „Start Soon“ aufhübschen

1. In OBS die Szene **Start Soon** anklicken.
2. Den alten Text (GDI+) löschen (Rechtsklick auf die Quelle → Entfernen).
3. Quellen → **+ → „Browser“** → Name `Overlay Start` → OK. Im Fenster:
   - Haken bei **„Lokale Datei“** setzen
   - **Durchsuchen** → `C:\overlays\start-soon.html`
   - **Breite 1920, Höhe 1080** → OK.
4. Das Overlay sollte sofort animiert in der Vorschau laufen.

## 12.3 – Clip-Schleife dahinter (sobald Clips da sind)

1. Clips als Videodateien (mp4) auf den Laptop, z. B. nach **`D:\Clips`**.
   *(Twitch-Clips kann sie im Creator-Dashboard herunterladen.)*
2. Einmalig **VLC Media Player** installieren (<https://www.videolan.org/>).
3. OBS neu starten → Szene Start Soon → Quellen → **+ → „VLC-Videoquelle“** →
   Name `Clips`. Im Fenster: bei Wiedergabeliste **+ → „Verzeichnis hinzufügen“**
   → `D:\Clips` → Haken **„Wiedergabeliste wiederholen“** (+ optional
   „Zufällige Wiedergabe“) → OK.
4. In der Quellenliste muss `Clips` **unter** `Overlay Start` liegen
   (Reihenfolge per Pfeil/Ziehen).
5. **Wichtig:** Damit die Clips durchs Overlay sichtbar sind, in
   `start-soon.html` oben **`HINTERGRUND = false`** setzen (Editor) – dann ist
   der Lila-Hintergrund weg und nur Vignette + Text liegen über den Clips.
   In OBS: Rechtsklick auf `Overlay Start` → **„Aktualisieren“**.
6. **Ton der Clips stummschalten**, falls unerwünscht: im Audiomixer bei
   „Clips“ auf das Lautsprechersymbol klicken.

## 12.4 – Szene „Ende“ (optional, für !stop)

1. Neue Szene anlegen: exakt **`Ende`**.
2. Quellen → **+ → Browser** → lokale Datei → `C:\overlays\ende.html` →
   1920×1080 → OK.
3. Damit `!stop` vor dem Beenden kurz diese Szene zeigt:
   in **`chatbot\config.ini`** unter `[scenes]` ändern:
   ```
   stop  = Ende
   ```
   → speichern → Chat-Bot neu starten (`start_bot.bat`).

## 12.5 – Test

- `/standby` (Telegram) → Start-Soon-Overlay läuft animiert
- `/foto` → das Overlay kommt als Bild aufs Handy
- `!stop` (Twitch-Chat) → kurz „Ende“-Screen, dann Übertragung aus
