# Schritt 2 – OBS Studio installieren & einrichten

OBS ist das Programm, das den SRT-Stream vom Handy empfängt und an Twitch sendet.
Diese Werte sind auf deine GTX 1060, Twitch und mobiles IRL-Streaming abgestimmt.

---

## 2.1 – OBS installieren

1. Gehe auf **<https://obsproject.com/de>** und lade **OBS Studio für Windows**.
2. Installiere es (Doppelklick, „Weiter“ – Standardeinstellungen sind okay).
3. Starte OBS. Beim ersten Start fragt der **Auto-Konfigurations-Assistent** – du
   kannst **„Nein/Abbrechen“** wählen, weil wir alles selbst einstellen.

---

## 2.2 – Mit Twitch verbinden

1. **Einstellungen** (rechts unten) → **Stream**.
2. **Dienst:** Twitch.
3. Klicke **„Konto verbinden (empfohlen)“** und melde dich bei Twitch an.
   *Alternativ: „Stream-Schlüssel verwenden“ und den Schlüssel aus dem
   Twitch-Dashboard (Creator-Dashboard → Einstellungen → Stream) einfügen.*
4. Lass den Server auf **„Automatisch“**.

---

## 2.3 – Video-Einstellungen (Auflösung & Bildrate)

**Einstellungen → Video:**

- **Basis-(Leinwand-)Auflösung:** 1920×1080
- **Ausgabe-(skalierte) Auflösung:** **1280×720** (720p ist ideal für mobiles IRL)
- **Herunterskalierungsfilter:** Bikubisch
- **FPS-Wert:** **30** (stabiler bei wenig Bandbreite als 60)

---

## 2.4 – Ausgabe-Einstellungen (Encoder & Bitrate)

**Einstellungen → Ausgabe** → oben **Ausgabemodus: „Erweitert“**.

Reiter **„Streaming“:**

- **Encoder:** **NVIDIA NVENC H.264** (nutzt die GTX 1060, schont die CPU)
- **Ratensteuerung:** **CBR** (konstante Bitrate – von Twitch empfohlen)
- **Bitrate:**
  - Gute Verbindung: **4000–4500 kbit/s**
  - Normal unterwegs: **2500–3500 kbit/s**
  - Schwaches Netz: **1500–2500 kbit/s**
- **Keyframe-Intervall:** **2** (Sekunden) – nicht auf 0/automatisch lassen!
- **Voreinstellung:** **P5: Langsam (Qualität)** – bei Last **P4: Mittel**
- **Profil:** high
- **Look-ahead:** aus · **Psycho Visual Tuning:** aus (spart GPU)
- **Max. B-Frames:** 2

Reiter **„Audio“:**

- **Audio-Bitrate (Spur 1):** 160

---

## 2.5 – Audio-Sampling

**Einstellungen → Audio → Allgemein → Abtastrate:** **48 kHz**.

---

## 2.6 – Den SRT-Stream vom Handy in OBS holen (Kernstück)

Das Handy sendet per SRT, OBS wartet als „listener“ darauf.

1. Im Hauptfenster bei **„Quellen“** auf **+** → **„Medienquelle“** → Name z. B.
   „Handy SRT“ → OK.
2. Im Fenster den Haken bei **„Lokale Datei“ ENTFERNEN**.
3. In das Feld **„Eingang“ (Input)** trägst du ein:

   ```
   srt://0.0.0.0:9999?mode=listener&latency=2000000
   ```
   *Erklärt: `0.0.0.0` = „auf allen Netzwerken lauschen“. `9999` = Port (am Handy
   denselben nutzen). `latency=2000000` = 2000 ms Puffer gegen Verbindungsschwankungen
   (Wert in Mikrosekunden).*

4. Setze den Haken bei **„Bei Inaktivität der Quelle neu verbinden“** (Reconnect).
5. **„Eingangsformat“ (Input Format):** `mpegts`.
6. OK klicken. Sobald das Handy sendet, erscheint das Bild im Vorschaufenster.

> Die genauen Handy-Einstellungen stehen in **`03-MOBLIN-HANDY.md`**.

---

## 2.7 – Backup: lokale Aufnahme auf die HDD

Damit du bei einem Abriss trotzdem eine saubere Aufnahme hast.

1. **Einstellungen → Ausgabe → Reiter „Aufnahme“.**
2. **Aufnahmepfad:** `D:\Aufnahmen` (deine große HDD).
3. **Aufnahmeformat:** **mkv** (übersteht Abstürze besser als mp4).
4. **Encoder:** falls wählbar, ebenfalls NVENC – oder „Streamcodierung verwenden“,
   um die GPU nicht doppelt zu belasten.
5. Vor dem Live-Gehen optional **„Aufnahme starten“** mitlaufen lassen.

---

## 2.8 – Ausfallsicherheit einrichten

1. **Stand-by-Szene anlegen:** Unten bei „Szenen“ auf **+** → „Verbindung verloren“.
   Füge dort ein Standbild + Text ein („Signal weg – gleich zurück“). Wenn das
   Handysignal abreißt, wechselst du auf diese Szene.
2. **Hotkeys:** **Einstellungen → Hotkeys** → für den Szenenwechsel eine Taste
   festlegen (z. B. F1 = Live-Szene, F2 = Stand-by).
3. **Twitch-Ausfallschutz:** im Twitch-Dashboard unter Stream-Einstellungen
   „Disconnect Protection“ aktivieren – dann beendet ein kurzer Abriss den Stream
   nicht sofort.

---

## 2.9 – Schnelltest in OBS

- Statistik-Fenster öffnen: **Docks → Statistiken**. Dort siehst du „Übersprungene
  Frames“ und „Verworfene Frames (Netzwerk)“ – beide sollten nahe 0 bleiben.
- „Stream starten“ erst, wenn das Handybild in der Vorschau erscheint.

**Erfolgskontrolle:** Handybild erscheint in OBS, NVENC ist als Encoder aktiv,
Aufnahmeziel ist D:\Aufnahmen.

---

Weiter mit **`03-MOBLIN-HANDY.md`**.
