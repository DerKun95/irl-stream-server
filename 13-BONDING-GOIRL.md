# Schritt 13 – Bonding mit go-irl (Mobilfunk + WLAN gleichzeitig)

Ziel: Maximale Stabilität unterwegs. **Moblin bündelt am Handy** Mobilfunk und
WLAN (SRTLA) – der Server setzt die Teilströme mit **go-irl** wieder zusammen.
Fällt ein Netz aus, läuft der Stream über das andere einfach weiter.

**Bonus von go-irl:**
- **Live-Statistik im Bild** (Bitrate, Ping, Paketverlust) als kleine Anzeige
- **Automatischer Szenenwechsel**: Signal bricht ein → OBS schaltet von selbst
  auf die BRB-Szene und zurück, sobald es wieder stabil ist. Kein manuelles
  `!brb` mehr nötig bei Funklöchern!

Quelle: <https://github.com/e04/go-irl> (kostenlos, Open Source, läuft als
einfache Windows-exe – kein Docker, kein Linux).

---

## 13.1 – go-irl herunterladen

1. Auf dem Laptop: <https://github.com/e04/go-irl/releases> öffnen.
2. Beim neuesten Release das **Windows-Paket** herunterladen (zip mit
   `go-irl-windows.exe`).
3. Entpacken nach **`C:\go-irl`**.
4. Die mitgelieferte **`start_goirl.bat`** (aus `irl-relay\goirl\`) ebenfalls
   nach `C:\go-irl` kopieren – sie startet go-irl mit unserem eigenen Port.

## 13.2 – FritzBox: neuen Port freigeben

go-irl lauscht bei uns auf Port **DEIN-PORT2** (eigener Zufallsport statt Standard
5000 – gleiche Schutz-Idee wie beim SRT-Port).

1. FritzBox → Internet → Freigaben → Portfreigaben → beim Laptop-Eintrag die
   Freigaben bearbeiten → **neue Portfreigabe**:
   - Protokoll: **UDP**
   - Port (von/bis/an Gerät): **DEIN-PORT2**
2. Übernehmen. *(Die alte DEIN-PORT-Freigabe bleibt als Plan B bestehen!)*

## 13.3 – OBS umstellen

go-irl liefert den fertigen Stream **lokal** an OBS – die Quelle zeigt also
nicht mehr ins Internet, sondern auf den eigenen Rechner:

1. Quelle **„Handy SRT“** (in der Live-Szene) doppelklicken und ändern:
   - **Eingang:** `udp://127.0.0.1:5002`
   - **Eingangsformat:** `mpegts`
   - Haken **ENTFERNEN** bei „Wiedergabe neu starten, wenn Quelle aktiv wird“
     (sonst ruckelt es bei jedem Szenenwechsel)
   - OK.
2. **Statistik + Auto-Szenenwechsel** einbauen – in der Szene **Live**:
   - Quelle **+ → Browser** → Name `go-irl Stats` → **URL** (eine Zeile):
     ```
     http://127.0.0.1:9999/app?wsport=8888&onlineSceneName=Live&offlineSceneName=BRB&type=simple
     ```
   - Breite/Höhe z. B. 600 × 200, Anzeige in eine Ecke schieben.
   - **WICHTIG:** Im selben Fenster unten bei **„Seitenberechtigungen“** →
     **„Erweiterter Zugriff auf OBS“** wählen – sonst kann es die Szenen nicht
     umschalten.
   - `type=simple` = kleine Zahlenanzeige. Alternativen: `graph` (Verlaufskurve)
     oder `none` (unsichtbar, nur Auto-Umschalten).

## 13.4 – go-irl starten

1. OBS muss laufen.
2. Doppelklick auf **`C:\go-irl\start_goirl.bat`** → schwarzes Fenster bleibt
   offen (Schließen = Bonding aus).
3. **Autostart:** Verknüpfung der bat nach `shell:startup` legen. Die Datei
   wartet beim Start automatisch 45 Sekunden, damit OBS zuerst da ist.

## 13.5 – Moblin umstellen (ihr Handy)

1. Stream-URL ändern auf:
   ```
   srtla://DEIN-NAME.duckdns.org:DEIN-PORT2
   ```
   (statt `srt://...:DEIN-PORT` – beachte: **srtla** und der **neue Port**!)
2. **Bonding aktivieren:** In Moblin sind unter den Stream-Einstellungen die
   Netzwerk-Pfade wählbar – **Mobilfunk + WLAN** erlauben. Sobald beide
   verfügbar sind, sendet Moblin über beide gleichzeitig.
3. Rest bleibt: 1280×720, 30 fps, ~3500 kbit/s, adaptive Bitrate an.

## 13.6 – Test

1. go-irl läuft, OBS läuft → Moblin „Go Live“ (mobile Daten **und** WLAN an).
2. Bild erscheint in der Live-Szene, die **Stats-Anzeige** zeigt Bitrate/RTT.
3. **Bonding-Probe:** Am Handy das WLAN ausschalten → Stream läuft über
   Mobilfunk weiter (kurzer Qualitätsdip ist ok).
4. **Auto-Switch-Probe:** Handy kurz in den Flugmodus → OBS springt von selbst
   auf **BRB** → Flugmodus aus → automatisch zurück auf **Live**.

## Plan B (Rückfallebene)

Der alte Direktweg bleibt funktionsfähig: Moblin-Profil mit
`srt://DEIN-NAME.duckdns.org:DEIN-PORT` + OBS-Quelle zurück auf
`srt://0.0.0.0:DEIN-PORT?mode=listener&latency=2000000`. Am besten in Moblin
**zwei Stream-Profile** anlegen („Bonding“ und „Direkt“), dann ist der Wechsel
unterwegs ein Fingertipp.

## Hinweise

- Der **Wächter** funktioniert unverändert (er prüft die Quelle „Handy SRT“ –
  Name bleibt ja gleich). Chat-Befehle `!start/!live/!brb/!stop` ebenso.
- Auto-Szenenwechsel und Chat-Befehle können sich theoretisch „streiten“
  (go-irl schaltet zurück auf Live, wenn das Signal gut ist). Stört das beim
  Start-Soon-Warten, in der Stats-URL `type=none` setzen oder die
  Seitenberechtigung wieder herausnehmen – dann ist nur das Bonding aktiv.


## Praxis-Erkenntnisse (08.06.2026, beim echten Einrichten gelernt)

- Die exe heisst je nach Build **`go-irl.exe`** (nicht `go-irl-windows.exe`) –
  die Start-bat muss den richtigen Namen verwenden.
- Browser-Quelle: **`127.0.0.1` statt `localhost`** in der URL, sonst verbindet
  sie sich evtl. nicht (IPv6-Aufloesung) -> keine Zahlen, kein Schalten.
- Browser-Quelle: **„Quelle herunterfahren, wenn nicht sichtbar" = AUS** und
  **„Browser aktualisieren, wenn Szene aktiv wird" = AUS**. Sonst schaltet er
  auf BRB, aber nicht zurueck auf Live (Steuerung wird in der BRB-Szene sonst
  abgeschaltet).
- Erster Start: Windows-Firewall fragt -> **„Zugriff zulassen"** (Privat +
  Oeffentlich), sonst kommt nichts an.
- `handy srt` muss in der Szene **sichtbar** sein (Auge an); Eingang
  `udp://127.0.0.1:5002`, Format `mpegts`, „Wiedergabe neu starten…" AUS.
- Bild UND Ton laufen ueber `handy srt`; `go-irl Stats` ist nur Anzeige +
  Umschaltung (kein eigener Ton).
- Bonding bestaetigt: go-irl registrierte zwei Netzpfade gleichzeitig.


## Verschluesselung mit Passphrase (Sicherheit)

Damit niemand Fremdes einen Stream auf den offenen Port schicken kann, bekommt
go-irl eine **Passphrase** (geht mit go-irl problemlos, anders als frueher beim
direkten OBS-Weg).

1. Eine Passphrase ausdenken: **10-79 Zeichen**, am besten Buchstaben + Zahlen,
   **keine Leerzeichen** (einfacher). Beispiel-Format: `Wonderlnd2026Pink`.
2. In **beiden** Start-Dateien (`start_goirl.bat` + `start_goirl_TEST.bat`) in der
   go-irl-Zeile den Platzhalter ersetzen:
   ```
   go-irl.exe -mode=standalone -srtla-port=DEIN-PORT2 -passphrase "DEINE_PASSPHRASE_HIER"
   ```
   -> `DEINE_PASSPHRASE_HIER` durch die echte Passphrase ersetzen (in Anfuehrungszeichen lassen).
3. In **Moblin** (Handy der Streamerin): im go-irl-Stream-Profil das Feld
   **„SRT(LA) Passphrase"** mit **exakt derselben** Passphrase ausfuellen.
4. go-irl neu starten (Fenster zu, bat neu), Moblin neu verbinden.

**Wichtig:** Server und Handy muessen **exakt dieselbe** Passphrase haben, sonst
kommt keine Verbindung zustande. Die Passphrase NICHT oeffentlich teilen.
