# Schritt 7 – Stream über den Twitch-Chat steuern

Ziel: Der Stream wird über den Twitch-Chat **ihres Kanals** gesteuert – von ihr, dir
oder anderen Mods:

- **`!start`** → Twitch-Übertragung beginnt **und** die Startszene („Gleich geht's
  los“, Clips laufen) wird gezeigt.
- **`!live`** → Wechsel zur **Live-Szene** (Handybild).
- **`!stop`** → Übertragung wird **beendet**.

Wie das zusammenspielt: Ein kleines Programm (der **Chat-Bot**) liest den Chat mit
und sagt **OBS** per „obs-websocket“, was es tun soll. Alles läuft auf dem
**Server-Laptop** bei dir zu Hause.

> Reihenfolge: erst OBS vorbereiten (7.1–7.3), dann Bot-Account + Token (7.4–7.5),
> dann Bot einrichten und starten (7.6–7.8).

---

## 7.1 – obs-websocket in OBS aktivieren

Damit der Bot OBS fernsteuern darf.

1. In OBS oben im Menü auf **„Werkzeuge“** → **„WebSocket-Servereinstellungen“**.
2. Haken bei **„WebSocket-Server aktivieren“** setzen.
3. **Server-Port:** `4455` lassen.
4. Haken bei **„Authentifizierung aktivieren“** setzen und auf
   **„Passwort anzeigen“** / „Passwort generieren“ – **dieses Passwort kopieren**,
   du trägst es gleich in die Bot-Konfiguration ein.
5. **„Übernehmen“ / „OK“**.

---

## 7.2 – OBS auf IHREN Twitch-Kanal stellen

Der Server sendet auf den Kanal der Streamerin – also braucht OBS **ihren**
Stream-Schlüssel.

1. OBS → **Einstellungen → Stream**.
2. **Dienst:** Twitch.
3. **„Stream-Schlüssel verwenden“** wählen und **ihren** Stream-Schlüssel eintragen.
   - Den findet sie in ihrem **Twitch Creator-Dashboard → Einstellungen → Stream →
     „Primärer Stream-Schlüssel“ → Kopieren**. Sie schickt ihn dir vertraulich.
4. „Übernehmen“ → „OK“.

> Der Stream-Schlüssel ist wie ein Passwort. Nicht weitergeben, nicht zeigen.

---

## 7.3 – Die zwei Szenen anlegen

Unten im OBS-Kästchen **„Szenen“** legst du zwei Szenen an (mit dem **+**):

### Szene „Live“ (Handybild)
1. Szene anlegen, exakt **`Live`** nennen.
2. Da hinein kommt deine **SRT-Medienquelle „Handy SRT“** (aus Schritt 02). Falls sie
   in einer anderen Szene liegt: in der Quelle Rechtsklick → Kopieren, in „Live“ →
   Einfügen (Referenz).

### Szene „Start Soon“ (Clips + Text)
1. Szene anlegen, exakt **`Start Soon`** nennen.
2. **Clips in Schleife** – am einfachsten mit VLC:
   - Einmalig **VLC Media Player** installieren (<https://www.videolan.org/>).
   - In OBS bei „Quellen“ **+ → „VLC-Videoquelle“** → Name „Clips“.
   - Bei **„Wiedergabeliste“** auf **+** → den **Ordner mit ihren Clip-Videos**
     hinzufügen (z. B. `D:\Clips`).
   - Haken bei **„Schleife“** und optional **„Zufällig“** setzen → OK.
   - *(Alternative ohne VLC: eine einzelne Videodatei als „Medienquelle“ mit Haken
     „Schleife“.)*
3. **Text** „Stream geht gleich los“ darüberlegen:
   - **+ → „Text (GDI+)“** → Text eingeben, Schrift/Größe wählen, mittig platzieren.
4. Reihenfolge prüfen: Der Text muss in der Quellen-Liste **über** den Clips stehen,
   sonst ist er verdeckt.

> Wichtig: Die Szenennamen müssen **exakt** `Start Soon` und `Live` heißen (so
> stehen sie später in der Bot-Konfiguration). Groß-/Kleinschreibung zählt.

---

## 7.4 – Eigenen Bot-Account bei Twitch anlegen

1. In einem **privaten Browserfenster** (damit du nicht aus deinem Account fliegst)
   auf <https://www.twitch.tv/> → **Registrieren**.
2. Einen Namen wählen, z. B. **`IhrName_Bot`**. E-Mail bestätigen.
3. Diesen Bot-Account später in **ihrem** Kanal zum **Moderator** machen, damit er
   ungehindert schreiben darf. Dafür tippt **sie** in ihrem Chat:
   ```
   /mod IhrName_Bot
   ```

---

## 7.5 – Chat-Token für den Bot erzeugen

Der Bot meldet sich mit einem **Token** (eine Art Passwort) am Chat an. Bleib dafür
im Browser **als Bot-Account angemeldet**.

1. Gehe auf einen Token-Generator für Chat-Tokens, z. B.
   **<https://twitchtokengenerator.com/>** (oder <https://www.twitchtools.com/chat-token>).
2. Wähle die Berechtigungen **`chat:read`** und **`chat:edit`** aus.
3. Mit dem **Bot-Account** anmelden und autorisieren.
4. Du bekommst einen **„Access Token“**. Daraus wird der Wert für die Konfiguration:
   **`oauth:` + Token**, also z. B. `oauth:abcd1234...`.

> Behandle den Token wie ein Passwort: nicht weitergeben, nicht öffentlich zeigen.
> Falls er doch mal sichtbar wird, einfach neu erzeugen (der alte wird ungültig).

---

## 7.6 – Python + Bot-Pakete installieren

Auf dem **Server-Laptop**:

1. Falls noch nicht vorhanden, **Python** installieren von
   <https://www.python.org/downloads/> – beim Installer unten den Haken bei
   **„Add python.exe to PATH“** setzen!
2. Den Ordner **`irl-relay\chatbot`** öffnen (dort liegt `bot.py`).
3. In der Adressleiste des Explorers `cmd` eintippen + Enter (öffnet die
   Eingabeaufforderung in diesem Ordner). Dann:
   ```
   pip install -r requirements.txt
   ```

---

## 7.7 – Bot konfigurieren

1. Im Ordner `chatbot` die Datei **`config.example.ini`** kopieren und die Kopie in
   **`config.ini`** umbenennen.
2. `config.ini` mit dem Editor öffnen und ausfüllen:
   - `bot_username` = Login-Name deines Bot-Accounts (klein)
   - `oauth_token`  = der `oauth:...`-Token aus 7.5
   - `channel`      = ihr Kanalname (klein)
   - `password`     = das obs-websocket-Passwort aus 7.1
   - unter `[scenes]`: `start = Start Soon` und `live = Live` (müssen zu OBS passen)
   - unter `[permissions] extra_allowed`: optional weitere erlaubte Namen
     (Mods/Broadcaster dürfen sowieso immer).
3. Speichern.

> `config.ini` enthält Token und Passwort – **niemals weitergeben oder hochladen.**

---

## 7.8 – Bot starten & testen

1. Im Ordner `chatbot` einen **Doppelklick auf `start_bot.bat`**. Ein schwarzes
   Fenster öffnet sich und zeigt „Verbunden. Warte auf Befehle …“.
   (Das Fenster muss **offen bleiben** – Schließen = Bot aus.)
2. OBS muss laufen (mit aktiviertem WebSocket aus 7.1).
3. Im Twitch-Chat ihres Kanals testen:
   - **`!start`** → OBS sollte auf „Start Soon“ wechseln und die Übertragung starten.
   - **`!live`** → Wechsel zu „Live“.
   - **`!stop`** → Übertragung endet.
4. Der Bot schreibt jeweils eine kurze Bestätigung in den Chat.

**Wenn nichts passiert:**
- Schreibt der Bot „Fehler bei der OBS-Steuerung“? → Läuft OBS? Stimmt das
  WebSocket-Passwort in `config.ini`? Port 4455?
- Reagiert er gar nicht? → Stimmen `channel`, `bot_username` und Token? Steht im
  schwarzen Fenster „Verbunden“?
- Heißen die Szenen in OBS **exakt** `Start Soon` und `Live`?

---

## 7.9 – Bot automatisch mitstarten (optional)

Damit der Bot nach einem Neustart des Laptops von selbst läuft:

1. `Win + R` → `shell:startup` → Enter (öffnet den Autostart-Ordner).
2. Eine **Verknüpfung** von `start_bot.bat` hineinlegen (Rechtsklick auf
   `start_bot.bat` → „Verknüpfung erstellen“, dann in den Autostart-Ordner ziehen).

So starten nach einem Reboot automatisch: Tailscale, RustDesk und der Bot. OBS
startest du (oder per Autostart) ebenfalls – wichtig ist, dass OBS läuft, damit der
Bot es steuern kann.

---

## Wer darf die Befehle benutzen?

- **Die Streamerin** (Kanalinhaberin) – immer.
- **Moderatoren** ihres Kanals – immer. Mod wird man mit `/mod name` im Chat.
- **Zusätzliche Namen** aus `extra_allowed` in der `config.ini` (z. B. du selbst,
  falls du in ihrem Kanal kein Mod bist).
- Alle anderen Zuschauer werden ignoriert.

---

## Ablauf im echten Einsatz (Kurzfassung)

1. Laptop läuft zu Hause, OBS + Bot sind an, Tailscale verbunden.
2. Ihr seid unterwegs. Sie startet **Moblin** (sendet an den Server über Tailscale).
3. Jemand tippt **`!start`** → Startszene mit Clips, Übertragung läuft auf Twitch.
4. Wenn ihr bereit seid: **`!live`** → ihr Handybild ist live.
5. Am Ende: **`!stop`** → Stream aus.
