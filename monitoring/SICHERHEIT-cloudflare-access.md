# Cloudflare Access vor die Stream-App setzen

**Ziel:** Bevor überhaupt jemand deine Login-Seite (`steuerung.deine-domain.com`) zu
sehen bekommt, muss er sich bei Cloudflare mit einer **erlaubten E-Mail** anmelden.
Damit erreicht kein Fremder mehr deinen Python-Login – Scanner und Brute-Force
prallen schon an Cloudflare ab. Der App-Login (Name + Passwort) bleibt als zweite
Hürde dahinter bestehen.

Das ist der größte Sicherheitsgewinn fürs geringste Basteln und für kleine Teams
**kostenlos** (Cloudflare Zero Trust, Free-Plan bis 50 Nutzer).

---

## Voraussetzung

Deine Domain läuft bereits über Cloudflare und die App hängt an einem
**Cloudflare Tunnel** (`cloudflared`). Genau das ist bei dir der Fall
(`steuerung.deine-domain.com` -> Tunnel -> `127.0.0.1:8182`).

---

## Schritt für Schritt

### 1. Zero Trust öffnen
- Auf https://one.dash.cloudflare.com einloggen (gleicher Account wie die Domain).
- Beim ersten Mal: ein Team-Name (Team-Domain) vergeben, Free-Plan wählen
  (keine Kreditkarte nötig für Free).

### 2. Login-Methode festlegen
- **Settings -> Authentication -> Login methods.**
- „One-time PIN" (E-Mail-Code) ist schon aktiv und reicht völlig – jeder erlaubte
  Nutzer bekommt beim Login einen Zahlencode per Mail.
- Optional: „Google" o. ä. hinzufügen, wenn du dich lieber per Google-Konto anmeldest.

### 3. Anwendung anlegen
- **Access -> Applications -> Add an application -> Self-hosted.**
- **Application name:** z. B. `Stream-Steuerung`
- **Session Duration:** z. B. `24 hours` (wie oft neu bei Cloudflare anmelden).
- **Application domain:** `steuerung.deine-domain.com`
  (Subdomain + Domain exakt so eintragen, wie die App erreichbar ist.)
- Speichern/Weiter.

### 4. Zugriffs-Regel (Policy) definieren
- **Policy name:** z. B. `Nur Team`
- **Action:** `Allow`
- **Include -> Selector: `Emails`** und die erlaubten Adressen eintragen, z. B.
  deine und Alisas E-Mail. (Alternativ `Emails ending in` für eine ganze Domain.)
- Speichern. Fertig-klicken bis die Anwendung angelegt ist.

### 5. Testen
- `https://steuerung.deine-domain.com` im **privaten Fenster** öffnen.
- Es sollte jetzt zuerst die **Cloudflare-Access-Seite** kommen (E-Mail eingeben ->
  Code aus der Mail eingeben).
- Danach erscheint deine gewohnte **App-Login-Seite** (Name + Passwort).
- Mit einer *nicht* eingetragenen E-Mail testen: Zugriff muss **abgelehnt** werden.

---

## Wichtige Hinweise

- **Mods hinzufügen/entfernen** geht künftig komfortabel über die Access-Policy
  (E-Mail rein/raus) – ganz ohne Server-Neustart.
- **PWA / „Zum Homescreen":** Der E-Mail-Code kommt nur alle *Session Duration*
  (z. B. 24 h), nicht bei jedem Öffnen. Für den Alltag am Handy also kaum spürbar.
- **OAuth-Callback / Overlay:** Der Twitch-OAuth-Rücksprung läuft über dieselbe
  Domain und damit auch durch Access. Falls du das Standort-**Overlay** in OBS als
  Browser-Quelle über die öffentliche Domain lädst, würde Access es blocken –
  dann entweder das Overlay lokal über `http://127.0.0.1:8182/overlay` einbinden
  (empfohlen, OBS läuft ja auf demselben PC) **oder** in Access eine zusätzliche
  Bypass-Policy nur für den Pfad `/overlay` anlegen. Der lokale Weg ist sicherer.
- **Service-Token (optional):** Wenn mal ein Skript automatisiert an die App soll,
  dafür in Access ein „Service Token" statt einer E-Mail-Regel nutzen.

---

## Reihenfolge der Härtung (Empfehlung)

1. **Cloudflare Access** einrichten (dieses Dokument) – kappt die öffentliche Angriffsfläche.
2. **Passwörter hashen** mit `passwort_hash.py` – kein Klartext mehr in der config.
3. Rate-Limit, Login-Log und Security-Header sind bereits in `watchdog.py` eingebaut
   und aktiv, sobald du den Server neu startest.

> Merksatz: Access ist die Tür mit Türsteher, der App-Login ist der Tresor dahinter.
> Beides zusammen ist deutlich stärker als jedes allein.
