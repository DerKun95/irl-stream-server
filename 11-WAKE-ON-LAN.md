# Schritt 11 – Server fernsteuern: Aus per Telegram, An per FritzBox (WoL)

Ziel: Den Server-Laptop **herunterfahren per Telegram** und **wieder einschalten
per Wake-on-LAN** über die FritzBox – auch von unterwegs.

## So funktioniert es

- **Ausschalten/Neustart:** Der Wächter läuft auf dem Laptop und führt die
  Befehle direkt aus. Neue Telegram-Befehle:

  | Befehl       | Wirkung                                            |
  |--------------|-----------------------------------------------------|
  | `/aus`       | fährt den Server in 15 s herunter                   |
  | `/neustart`  | startet den Server in 15 s neu                      |
  | `/abbrechen` | stoppt einen laufenden Countdown (Notbremse)        |

- **Einschalten:** Ein ausgeschalteter Laptop kann keine Telegram-Nachricht
  empfangen. Stattdessen schickt die **FritzBox** das „Weck-Signal“
  (Wake-on-LAN). Den Knopf dafür erreichst du von überall über dein
  MyFRITZ!-Konto im Browser.

> ⚠️ **Wichtigste Voraussetzung: LAN-Kabel!** Wake-on-LAN funktioniert bei
> Laptops praktisch nur über die Kabel-Netzwerkbuchse. Über WLAN geht es nicht.
> Außerdem muss das **Netzteil angeschlossen** bleiben.

---

## 11.1 – Windows für Wake-on-LAN vorbereiten (am Laptop)

1. **Schnellstart ausschalten** (sonst „schläft“ die Netzwerkkarte zu tief):
   - `Win + R` → `control powercfg.cpl` → links „Auswählen, was beim Drücken
     des Netzschalters geschehen soll“ → „Einige Einstellungen sind momentan
     nicht verfügbar“ anklicken → Haken bei **„Schnellstart aktivieren“
     ENTFERNEN** → Speichern.
2. **Netzwerkkarte scharf stellen:**
   - Rechtsklick auf Start → **Geräte-Manager** → **Netzwerkadapter** →
     deinen **Ethernet/LAN-Adapter** (Realtek/Intel, NICHT WLAN) doppelklicken.
   - Reiter **„Energieverwaltung“**: alle drei Haken setzen, insbesondere
     **„Gerät kann den Computer aus dem Ruhezustand aktivieren“** und
     **„Nur Magic Packet kann den Computer ... aktivieren“**.
   - Reiter **„Erweitert“**: Eintrag **„Wake on Magic Packet“** (o. ä.) auf
     **„Aktiviert/Enabled“**.
3. **BIOS prüfen** (nur falls es später nicht klappt): Beim Start F2/Entf →
   nach „Wake on LAN“ / „Power on by PCI-E“ suchen → aktivieren. Nicht jedes
   Laptop-BIOS hat den Punkt – oft reicht Schritt 2.

---

## 11.2 – FritzBox: Weck-Knopf nutzen

1. FritzBox-Oberfläche → **Heimnetz → Netzwerk** → in der Geräteliste beim
   **Server-Laptop** auf **„Details“/Bearbeiten** (Stift).
2. Dort gibt es den Knopf **„Computer starten“** – das ist der Weck-Knopf.
3. Empfehlung: Auf derselben Seite den Haken
   **„Diesen Computer automatisch starten, sobald aus dem Internet darauf
   zugegriffen wird“** setzen – dann weckt die FritzBox den Laptop sogar
   von selbst, wenn z. B. ein SRT-Stream oder RustDesk-Zugriff ankommt.

---

## 11.3 – FritzBox von unterwegs erreichen (MyFRITZ!)

Damit du den Weck-Knopf auch unterwegs drücken kannst:

1. FritzBox → **Internet → MyFRITZ!-Konto**: ist schon eingerichtet (Schritt 8).
2. FritzBox → **System → FRITZ!Box-Benutzer**: deinen Benutzer öffnen →
   Haken bei **„Zugang auch aus dem Internet erlaubt“** setzen. Starkes
   Passwort!
3. Von unterwegs: Im Handy-Browser **<https://www.myfritz.net>** öffnen → mit
   dem MyFRITZ!-Konto anmelden → deine FritzBox auswählen → **Heimnetz →
   Netzwerk → Laptop → „Computer starten“**.

---

## 11.4 – Der komplette Fernsteuer-Zyklus (Test)

1. **Telegram:** `/aus` → Laptop fährt herunter (Countdown läuft; `/abbrechen`
   würde stoppen).
2. **Browser (myfritz.net):** FritzBox → „Computer starten“ → Laptop bootet.
3. **Warten ~2–3 Min:** Autostart bringt OBS, Chat-Bot, Wächter, Tailscale,
   RustDesk hoch.
4. **Telegram:** `/status` → alles grün = Zyklus komplett. 🎉

> Hinweis: Der Test funktioniert erst **nach dem Umzug ans LAN-Kabel**.
> Solange der Laptop nur im WLAN hängt, klappt zwar `/aus`, aber das
> Aufwecken nicht.
