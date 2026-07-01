# Schritt 8 – Einfacher Zugang für die Streamerin (ohne Tailscale)

Ziel: Ihre Seite ist **so einfach wie möglich**. Sie trägt in Moblin **eine feste
Adresse** ein und tippt „Go Live“ – sonst nichts. Die ganze Einrichtung passiert
einmalig bei dir am **Router** und am **Laptop**.

So funktioniert es: Dein Router leitet den SRT-Port von außen zum Server-Laptop
weiter (**Portfreigabe**). Ein fester Internet-Name (**DynDNS**) sorgt dafür, dass
dein Zuhause immer unter derselben Adresse erreichbar ist. Ein **SRT-Passwort
(Passphrase)** schützt davor, dass Fremde senden können.

> Wichtiger Vorab-Check (Schritt 8.2): Manche Internetanschlüsse haben **keine
> echte öffentliche IPv4** (Stichwort „CGNAT“/„DS-Lite“). Dann funktioniert die
> Portfreigabe nicht – in dem Fall bleibt nur der Tailscale-Weg auf ihrem Handy.
> Deshalb prüfen wir das zuerst.

---

## 8.1 – Laptop bekommt eine feste lokale IP

Damit die Weiterleitung im Router immer zum richtigen Gerät zeigt.

1. Laptop-IP herausfinden: `Win + R` → `cmd` → `ipconfig`. Beim **Ethernet-Adapter**
   die **IPv4-Adresse** ablesen (z. B. `192.168.0.50`) – **nicht** die Tailscale-
   Adresse (100.x).
2. Im Router unter **DHCP / Geräteliste** dem Laptop diese IP **fest zuweisen**
   (DHCP-Reservierung), damit sie sich nie ändert.

---

## 8.2 – Hast du eine öffentliche IPv4? (CGNAT-Check)

1. Im Router-Menü die **„Internet“-/„Online“-Statusseite** öffnen und die dort
   angezeigte **WAN-IP** ablesen.
2. Auf dem PC eine Seite wie <https://www.wieistmeineip.de/> öffnen und die
   **öffentliche IPv4** vergleichen.
   - **Beide gleich** → super, du hast eine öffentliche IP, Portfreigabe geht.
   - **Router zeigt `100.64.x.x`–`100.127.x.x`** oder die IPs sind verschieden →
     wahrscheinlich **CGNAT/DS-Lite**. Dann funktioniert die Portfreigabe nicht.
     Lösung: entweder beim Provider eine „echte IPv4“ freischalten lassen
     (oft kostenlos), **oder** doch Tailscale auf ihrem Handy (einmalig, dann
     ebenfalls dauerhaft einfach).

> Telekom-DSL hat meist eine öffentliche IPv4 (gut). Bei Kabel/Vodafone oder
> reinen Mobilfunk-Anschlüssen ist CGNAT häufiger.

---

## 8.3 – DynDNS einrichten (fester Name für dein Zuhause)

Deine öffentliche IP kann sich ändern. DynDNS gibt dir einen **gleichbleibenden
Namen**, z. B. `meinserver.duckdns.org`.

**Variante A – DynDNS im Router (am einfachsten, falls vorhanden):**
- Viele Router haben das eingebaut (FritzBox: „Internet → Freigaben → DynDNS“;
  Speedport: „Internet → DynDNS“). Dort einen Anbieter wählen und die Zugangsdaten
  eintragen.

**Variante B – DuckDNS (kostenlos, falls der Router nichts bietet):**
1. Auf <https://www.duckdns.org/> mit Google/GitHub anmelden.
2. Einen Namen anlegen, z. B. `meinserver` → du bekommst `meinserver.duckdns.org`.
3. Den **Token** von DuckDNS notieren.
4. Entweder trägst du DuckDNS direkt im Router ein (falls „benutzerdefinierter
   Anbieter“ unterstützt wird), oder du installierst auf dem Laptop ein kleines
   Update-Programm von DuckDNS, das die IP aktuell hält.

---

## 8.4 – Portfreigabe (Port Forwarding) im Router

Der Router schickt ankommende SRT-Daten zum Laptop.

1. Im Router-Menü **„Portfreigaben“ / „Port Forwarding“** öffnen (oft unter
   „Internet → Freigaben“).
2. Neue Regel anlegen:
   - **Gerät/Ziel-IP:** die feste Laptop-IP aus 8.1 (z. B. `192.168.0.50`)
   - **Port (intern und extern):** `9999`
   - **Protokoll:** **UDP** (SRT nutzt UDP!)
3. Speichern.

---

## 8.5 – OBS: SRT-Empfang mit Passwort (Passphrase)

Damit nur sie senden kann. In OBS die SRT-Medienquelle „Handy SRT“ bearbeiten und
den **Eingang** so erweitern:

```
srt://0.0.0.0:9999?mode=listener&latency=2000000&passphrase=DEIN_GEHEIMES_PASSWORT&pbkeylen=16
```

- `passphrase=` = ein selbst ausgedachtes, langes Passwort (mind. 10 Zeichen).
- `pbkeylen=16` = Verschlüsselungsstärke (Standard, passt).

---

## 8.6 – Was SIE in Moblin einträgt (ihr einziger Schritt)

Du gibst ihr **eine fertige Adresse** – sie trägt sie einmal in Moblin ein:

```
srt://meinserver.duckdns.org:9999?latency=2000000&passphrase=DEIN_GEHEIMES_PASSWORT&pbkeylen=16
```

- `meinserver.duckdns.org` = dein DynDNS-Name aus 8.3
- gleiche `passphrase` wie in OBS
- in Moblin noch: 1280×720, 30 fps, Bitrate ~3500, **adaptive Bitrate an**

Mehr muss sie nicht tun. Ab dann: Moblin öffnen → „Go Live“. Der Rest (Szenen,
Start/Stop) läuft über den **Twitch-Chat** (Datei `07`).

---

## 8.7 – Test

1. Zum Testen kann ihr Handy ruhig über **Mobilfunk** (nicht dein WLAN) senden –
   nur so testest du die Portfreigabe von außen wirklich.
2. „Go Live“ in Moblin → das Bild sollte in OBS erscheinen.
3. Kommt kein Bild: siehe `06-PROBLEMHILFE.md` und prüfe Portfreigabe (UDP!),
   DynDNS-Name, gleiche Passphrase auf beiden Seiten.

---

## ✅ SO IST ES BEI DIR FINAL EINGERICHTET (Stand: 06.06.2026)

Nach dem Troubleshooting weicht der echte Aufbau von der Anleitung oben ab:

- **Port:** `DEIN-PORT` (UDP) statt 9999 — FritzBox-Portfreigabe zeigt auf den Laptop.
- **Keine SRT-Passphrase** — die OBS-Medienquelle nahm sie über die URL nicht an.
  Schutz stattdessen: zufälliger Port + geheimer DuckDNS-Name.
- **DynDNS: DuckDNS statt MyFRITZ!** Grund: Der myfritz-Name liefert auch eine
  IPv6-Adresse aus, und Handys im Mobilfunk bevorzugen IPv6 — dort funktioniert
  die Portweiterleitung aber nicht. Der DuckDNS-Name liefert NUR IPv4 (die
  FritzBox haelt ihn selbst aktuell, Reiter Internet → Freigaben → DynDNS).
- **OBS-Eingang:**  `srt://0.0.0.0:DEIN-PORT?mode=listener&latency=2000000`
- **Moblin-URL (ihre einzige Einstellung):**
  `srt://DEIN-NAME.duckdns.org:DEIN-PORT?latency=2000000`  (Stream-ID: `live`)

**Merkzettel fuer spaeter:**
- Wenn der Laptop ans **LAN-Kabel** kommt, bekommt er eine neue lokale IP →
  FritzBox-Portfreigabe einmal auf das neue Geraet/die neue IP umstellen.
- Die FritzBox-IPv4 aendert sich bei Neuverbindung — das faengt DuckDNS
  automatisch ab, nichts zu tun.

## Sicherheitshinweis

Eine offene Portfreigabe ist durch die **Passphrase** geschützt – ohne das richtige
Passwort kann niemand senden. Halte die Passphrase geheim und ändere sie, falls sie
mal nach außen gelangt. Für deinen eigenen Fernzugriff auf den Laptop bleibt
weiterhin **Tailscale** zuständig (privat, nicht offen im Internet).
