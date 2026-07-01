# Schritt 16 – Autoswitcher: automatisch in die Pause bei Funkloch

Ziel: Bricht unterwegs das Handy-Signal ab, schaltet OBS **von selbst** von der
Live-Szene auf die BRB-Pause – und zurück auf Live, sobald das Bild wieder da
ist. Niemand muss mehr `!brb` tippen. Werkzeug: das OBS-Plugin **Advanced Scene
Switcher** (ASS). Es schaltet nur Szenen um; der Twitch-Stream läuft durch.

> Wichtig: ASS reagiert in ~1–2 Sekunden (prüft laufend). Der Telegram-Wächter
> bleibt parallel aktiv für Alarme/Status – beide stören sich nicht.

---

## 16.1 – Plugin installieren

1. Auf dem Laptop: <https://github.com/WarmUpTill/SceneSwitcher/releases>
2. Beim neuesten Release das **Windows-Installer** (`.exe`, Name enthält
   „windows-installer") herunterladen und ausführen. Es findet OBS automatisch.
3. OBS **neu starten**.

**✓ Erfolgskontrolle:** In OBS oben im Menü **Werkzeuge (Tools)** gibt es jetzt
den Eintrag **„Advanced Scene Switcher"**.

---

## 16.2 – Zwei Makros anlegen

OBS → Werkzeuge → Advanced Scene Switcher → Reiter **Makros (Macros)**.

### Makro 1: „Funkloch → BRB"
1. Unten links **+** → Name: `Funkloch zu BRB` → OK.
2. **Wenn (If) / Bedingungen:**
   - Bedingungstyp **Media** wählen.
   - Quelle: deine SRT-Quelle (exakt der Name, z. B. `handy srt`).
   - Zustand: **„state" – „is" – „Ended"** (bzw. zusätzlich „None"/„Error"/
     „Stopped" – mehrere Zustände über „is one of" möglich; alles außer
     „Playing").
   - Häkchen **„For"** setzen → **3 Sekunden** (entprellt kurze Aussetzer).
   - Zweite Bedingung **+** mit **UND**: Typ **Scene** → „current scene is" →
     **Live**. (Nur von Live weg schalten.)
3. **Dann (Then) / Aktionen:**
   - Aktionstyp **Scene** → „Switch scene to" → **BRB**.

### Makro 2: „Signal zurück → Live"
1. Wieder **+** → Name: `Signal zu Live` → OK.
2. **Bedingungen:**
   - **Media** → Quelle `handy srt` → **„state is Playing"** → **„For" 5
     Sekunden** (etwas länger, damit es erst bei stabilem Bild zurückschaltet).
   - **UND** **Scene** → „current scene is" → **BRB**.
3. **Aktionen:**
   - **Scene** → „Switch scene to" → **Live**.

---

## 16.3 – Einschalten & Grundeinstellung

1. Im ASS-Fenster oben sicherstellen, dass der Schalter auf **„Active/Running"**
   steht (nicht „Stop"). Prüfintervall (General-Reiter) Standard ~300 ms ist ok.
2. ASS startet mit OBS automatisch mit – nichts Weiteres nötig.

**✓ Erfolgskontrolle (Trockentest):**
1. Moblin sendet, in OBS auf **Live** schalten (Handybild läuft).
2. Am Handy kurz **Flugmodus an** (Signal weg) → nach ~3 Sek springt OBS von
   selbst auf **BRB**.
3. Flugmodus aus → nach ~5 Sek zurück auf **Live**. 🎉

---

## Feinschliff / Fehlersuche

- **Schaltet gar nicht:** Quellenname im Media-Makro stimmt nicht exakt
  (Groß/Klein!). Muss identisch zur OBS-Quelle sein – derselbe Name wie
  `srt_source` in der Wächter-config.
- **Flackert hin und her:** „For"-Zeiten erhöhen (z. B. BRB 5 s, Live 8 s).
- **Geht nie auf BRB:** Die SRT-Medienquelle braucht den Haken „Wiedergabe neu
  starten, wenn Quelle aktiv wird" – und darf NICHT auf „dauerhaft puffern"
  stehen, sonst meldet sie nie „Ended". Im Zweifel die Quelle so lassen wie sie
  ist und im Makro zusätzlich den Zustand „None" mit aufnehmen.
- ASS macht **nur Szenen**, kein Start/Stop. Das Beenden bleibt bei `!stop`
  bzw. `/streamstop`.

---

## Verhältnis zu go-irl (später optional)

ASS deckt den Auto-Switch vollständig ab. go-irl (Datei 13) bräuchtest du nur,
wenn du zusätzlich **Bonding** (Mobilfunk + WLAN gleichzeitig) oder die
**Live-Statistik im Bild** willst. Beides ist unabhängig nachrüstbar.
