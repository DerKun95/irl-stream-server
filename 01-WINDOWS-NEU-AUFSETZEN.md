# Schritt 1 – Windows 10 sauber zurücksetzen & einrichten

Ziel: einen frischen, aufgeräumten Windows-Stand ohne den ganzen alten Müll – ganz
ohne USB-Stick. Danach Treiber, Updates und Energieeinstellungen, damit der Laptop
als Dauer-Relay zuverlässig läuft.

---

## 1.1 – Vorher sichern (wichtig!)

Beim Zurücksetzen wird **alles gelöscht**. Wenn auf dem Laptop noch wichtige Dateien
liegen (Fotos, Dokumente), kopiere sie jetzt auf einen anderen Computer oder in die
Cloud. Danach gibt es kein Zurück mehr.

---

## 1.2 – Windows zurücksetzen („Diesen PC zurücksetzen“)

1. Klicke auf **Start** → **Einstellungen** (Zahnrad-Symbol).
2. Gehe zu **Update und Sicherheit** → **Wiederherstellung**.
3. Unter **„Diesen PC zurücksetzen“** auf **„Los geht's“** klicken.
4. Wähle **„Alles entfernen“**.
   *Erklärt: löscht alle Programme, Einstellungen und persönlichen Dateien – genau
   das, was du willst, um den Müll loszuwerden.*
5. Du wirst gefragt, woher Windows neu kommen soll:
   - **„Cloud-Download“** (empfohlen, wenn deine Internetverbindung gut ist – lädt
     ein frisches Windows herunter) oder
   - **„Lokale Neuinstallation“** (nutzt die auf dem Laptop vorhandenen Dateien).
6. Bei der Frage zur Datenlöschung: für einen sauberen Verkauf wäre „Daten
   bereinigen“ gründlicher, dauert aber lange. Für deinen Eigengebrauch reicht die
   **normale Entfernung** (schneller).
7. Auf **„Zurücksetzen“** klicken und warten. Der Laptop startet mehrfach neu –
   das ist normal. Dauer: 30–90 Minuten.

**Erfolgskontrolle:** Du landest in der frischen Windows-Ersteinrichtung
(Region/Sprache wählen).

---

## 1.3 – Windows-Ersteinrichtung

1. Folge dem Assistenten: Region **Deutschland**, Tastatur **Deutsch**.
2. **Netzwerk:** schließe jetzt das **LAN-Kabel** an – dann ist der Laptop sofort
   online.
3. **Konto:** Ein **Microsoft-Konto** ist okay. Wer es schlichter mag, kann ein
   lokales Konto anlegen (bei manchen Windows-Versionen muss man dafür erst die
   Internetverbindung kurz trennen). Beides funktioniert.
4. Vergib einen Benutzernamen und ein **starkes Passwort** (brauchst du später für
   den Fernzugriff).
5. Datenschutz-/Cortana-Optionen: alles, was du nicht brauchst, kannst du **aus**
   schalten.

**Erfolgskontrolle:** Du siehst den frischen Windows-Desktop.

---

## 1.4 – Windows aktualisieren

1. **Start → Einstellungen → Update und Sicherheit → Windows Update.**
2. **„Nach Updates suchen“** klicken, alle installieren, ggf. neu starten und das
   so lange wiederholen, bis keine Updates mehr kommen.

> Hinweis: Windows 10 bekommt seit Oktober 2025 offiziell keine neuen
> Sicherheitsupdates mehr. Für einen Einzweck-Relay hinter dem VPN (Tailscale) ist
> das vertretbar. Vorhandene Updates trotzdem installieren.

---

## 1.5 – NVIDIA-Grafiktreiber installieren (für NVENC/Encoding)

OBS nutzt die Grafikkarte zum Encodieren – dafür braucht es einen aktuellen Treiber.

1. Gehe im Browser auf **<https://www.nvidia.com/de-de/drivers/>**.
2. Wähle: Produktreihe **GeForce**, Produkt **GeForce GTX 1060**, Betriebssystem
   **Windows 10 64-bit**. (Notebook-Variante – falls gefragt.)
3. Lade den **Game Ready Treiber** herunter und installiere ihn (bei der
   Installationsart **„Benutzerdefiniert“** → Haken bei **„Neuinstallation
   durchführen“** setzen, das räumt Reste auf).
4. Nach der Installation **neu starten**.

**Erfolgskontrolle:** Rechtsklick auf den Desktop zeigt „NVIDIA Systemsteuerung“.

---

## 1.6 – Energieeinstellungen (damit der Relay nicht einschläft)

Ein Server darf nicht in den Ruhezustand gehen, sonst bricht der Stream ab.

1. **Start → Einstellungen → System → Netzbetrieb und Energiesparen.**
2. Bei **„Bildschirm“** und **„Energiesparmodus“** jeweils auf **„Nie“** stellen
   (zumindest im Netzbetrieb).
3. Zusätzlich: **Systemsteuerung → Energieoptionen** → Energiesparplan
   **„Höchstleistung“** wählen (falls vorhanden).
4. **Wichtig beim Laptop:** Unter „Energieoptionen → Auswählen, was beim Zuklappen
   geschieht“ → **„Beim Zuklappen: Nichts unternehmen“** (Netzbetrieb). So kannst
   du den Deckel schließen, ohne dass der Stream stoppt.

**Erfolgskontrolle:** Der Laptop geht im Betrieb nicht mehr von selbst aus.

---

## 1.7 – Die große Festplatte (HDD) für Aufnahmen vorbereiten

Deine 1-TB-HDD ist ideal, um lokale Aufnahmen/Backups abzulegen, ohne die SSD
vollzumachen.

1. Rechtsklick auf **Start** → **Datenträgerverwaltung**.
2. Prüfe, ob die 1-TB-HDD (Toshiba) bereits einen Laufwerksbuchstaben hat (z. B. **D:**).
   - Falls nicht: Rechtsklick auf den freien Bereich der HDD → **„Neues einfaches
     Volume“** → Assistent durchklicken → als **NTFS** formatieren, Buchstabe **D:**.
3. Lege auf **D:** einen Ordner an, z. B. **D:\Aufnahmen**. Den stellst du später
   in OBS als Aufnahme-Ziel ein.

**Erfolgskontrolle:** Im Datei-Explorer existiert **D:\Aufnahmen**.

---

Weiter geht's mit **`02-OBS-EINRICHTEN.md`**.
