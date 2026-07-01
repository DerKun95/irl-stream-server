# Konzept: Stream-Steuerungs-App für die Streamerin (+ Mods)

Stand: Entwurf. Auf Basis deiner Auswahl:
**Web-App · Zugang über Cloud-Vermittler · voller Umfang · die Streamerin + Mods.**

---

## 1. Idee in einem Satz

Eine kleine **Web-App** (Link im Browser, per „Zum Home-Bildschirm" wie eine echte
App), mit der die Streamerin und ihre Mods den Stream per **großen Knöpfen** steuern —
erreichbar von überall, **ohne Tailscale und ohne offenen Port** zu Hause.

---

## 2. Architektur (der „Cloud-Vermittler")

Damit ihr Handy den Server zu Hause erreicht, **ohne ein Tor am Router zu öffnen**,
baut der Server selbst eine Verbindung **nach außen** zu einem Cloud-Punkt auf.
Empfohlener, wartungsarmer Weg: **Cloudflare Tunnel** (kostenlos).

```
der Streamerin Handy (Web-App)
        |
   Internet / HTTPS
        |
  Cloudflare (Vermittler + Login-Schutz)   <-- kein eigener Server noetig
        |
   Tunnel (vom Heim-Server nach AUSSEN aufgebaut)
        |
  Heim-Server: Wächter-Dashboard-API (Szenen, Stream, Foto, Status)
        |
   obs-websocket -> OBS / go-irl
```

Vorteile:
- **Kein offener Port** zu Hause (der Tunnel geht von innen nach außen).
- **HTTPS + Login** kommen von Cloudflare (Cloudflare Access: Login per E-Mail-Code
  oder PIN) — wir müssen keinen eigenen Server-Code für Auth schreiben.
- Wir nutzen die **bereits vorhandene Dashboard-API** weiter; wir bauen vor allem
  die hübsche Streamer-Oberfläche und ein paar neue Funktionen.

(Alternative wäre ein eigener Mini-Cloud-Dienst/VPS ~4 €/Monat — mehr Pflege.
Cloudflare Tunnel ist der einfachste „Cloud-Vermittler".)

---

## 3. Funktionsumfang (voll)

**Steuern (groß & einfach):**
- Start Soon · Live · BRB · Stop (mit „Wirklich?"-Nachfrage bei Live/Stop).

**Sehen:**
- „Läuft alles?"-Ampel: Signal vom Handy, OBS, Stream, Drops.
- Szenen-Vorschaubild (auf Knopfdruck).
- aktuelle Szene + Laufzeit.

**Erweitert:**
- **Stream-Titel & Kategorie** auf Twitch setzen (z. B. „Spaziergang durch …").
- **Nachrichten an die Mods / von den Mods** (Chat-/tts-Funktion).

**Mehrnutzer:**
- Eigener Zugang für **die Streamerin** (volle Rechte) und **Mods** (z. B. nur Szenen +
  BRB, kein Stream-Stop) — per Login geregelt.

**Look:** Pastell-Branding wie die Overlays, Dark Mode, „Home-Screen-App"-Gefühl.

---

## 4. Was neu gebaut werden muss

1. **Cloudflare-Tunnel** auf dem Heim-Server einrichten (cloudflared, einmalig).
2. **Streamer-Oberfläche** (eigene, schlanke Web-App, getrennt vom Technik-Dashboard).
3. **Mehrnutzer + Rollen** (die Streamerin voll / Mods eingeschränkt) via Cloudflare Access.
4. **Twitch-Titel/Kategorie:** braucht eine kleine **Twitch-App-Registrierung**
   (Client-ID/Secret) + einmaligen Login von die Streamerin (Berechtigung „Kanal verwalten").
5. **Messaging Mods <-> die Streamerin** (baut auf der vorhandenen tts/Telegram-Brücke auf).

---

## 5. Vorschlag: in Stufen bauen

- **Stufe 1 (Kern):** Tunnel + Steuer-Knöpfe + Ampel + Login. → Sie kann von überall
  starten/umschalten/stoppen. Das ist der größte Nutzen.
- **Stufe 2:** Szenen-Vorschau + Rollen (die Streamerin/Mods).
- **Stufe 3:** Twitch-Titel/Kategorie (Twitch-App nötig).
- **Stufe 4:** Messaging/tts-Komfort + PWA-Feinschliff (Home-Screen, Icon).

---

## 6. Ehrliche Einordnung

- Das ist **das größte Einzel-Feature bisher** — mehrere Bausteine, ein Cloud-Teil,
  eine Twitch-App. Kein Wochenend-Schnipsel, aber gut machbar in Stufen.
- **Kosten:** mit Cloudflare Tunnel **0 €** (kostenloser Plan reicht). Optional
  eigener Domain-Name (~10 €/Jahr) für eine schöne Adresse — nicht nötig.
- **Sicherheit:** deutlich besser als ein offener Port (kein Tor am Router, Login
  über Cloudflare). Wir behandeln Secrets serverseitig, nie im Browser.
- **Voraussetzung:** ein (kostenloses) Cloudflare-Konto; für Titel/Kategorie eine
  (kostenlose) Twitch-App-Registrierung.

---

## 7. Festgelegt (deine Entscheidungen)

- **Vermittler:** Cloudflare Tunnel (kostenlos, kein offener Port).
- **Adresse:** Cloudflare-Adresse (kein eigener Wunsch-Domainname) — dazu unten ein
  wichtiger Hinweis.
- **Twitch-Titel/Kategorie:** von Anfang an dabei.
- **Vorgehen:** erst sauber planen, dann in Stufen bauen.

---

## 8. Wichtiger Hinweis zur Adresse (bitte hier entscheiden)

Cloudflare Tunnel gibt es in zwei Varianten:

- **Schnell-URL (ganz ohne Domain):** kostenlos, aber die Adresse ist
  **zufällig und ändert sich bei jedem Neustart** (`xyz123.trycloudflare.com`).
  Zum dauerhaften Ablegen als App **ungeeignet** (Link wäre ständig anders).
- **Feste Adresse mit Login (Cloudflare Access):** stabil und abgesichert —
  **braucht aber eine Domain im Cloudflare-Konto.** Eine günstige reicht
  (~**10 €/Jahr**), z. B. `steuerung.deinname.xyz`.

**Konsequenz:** Für eine *dauerhafte, eingeloggte App* führt praktisch kein Weg an
einer kleinen Domain vorbei (~10 €/Jahr). Das ist der einzige reale Kostenpunkt.

→ **Zu entscheiden:** günstige Domain (~10 €/Jahr) akzeptieren? (Empfehlung: ja —
sonst ist die App nicht dauerhaft nutzbar.) Alternativ: doch ein kleiner VPS mit
fester Adresse, oder Tailscale-Funnel (feste Gratis-Adresse, aber Tailscale-Konto).

---

## 9. Voraussetzungen (anzulegen, bevor gebaut wird)

1. **Cloudflare-Konto** (kostenlos) + eine **Domain** darin (siehe Punkt 8).
2. **Cloudflare Access** für den Login einrichten (E-Mail-Code) — je ein Zugang
   für **die Streamerin** und die **Mods**, mit unterschiedlichen Rechten (Policies/Gruppen).
3. **Twitch-Entwickler-App** (kostenlos) für Titel/Kategorie:
   Client-ID/Secret anlegen, Scope `channel:manage:broadcast`; die Streamerin loggt sich
   einmalig ein und erteilt die Berechtigung.
4. **cloudflared** (Tunnel-Programm) auf dem Heim-Server installieren.

---

## 10. Technischer Plan im Detail

**Bausteine:**
- *Heim-Server:* die vorhandene Wächter-Dashboard-API wird erweitert um neue
  Endpunkte (Titel/Kategorie setzen, Messaging). cloudflared baut den Tunnel auf.
- *Cloudflare:* Tunnel + Access (Login/Rollen) + die feste Adresse.
- *Web-App (Frontend):* eigene, schlanke Streamer-Seite (getrennt vom
  Technik-Dashboard), PWA-fähig.

**Funktion → Technik:**
| Funktion | Umsetzung |
|---|---|
| Start/Live/BRB/Stop | vorhandene `/api/cmd` (golive/standby/live/brb/streamstop) |
| „Läuft alles?"-Ampel | vorhandene `/api/status` |
| Szenen-Vorschau | vorhandene `/api/foto.jpg` |
| Titel/Kategorie | **neu**: Twitch-Helix-API (broadcaster-Token, serverseitig) |
| Mod-Messaging/tts | baut auf vorhandener tts/Telegram-Brücke auf |
| Rollen (die Streamerin/Mods) | Cloudflare-Access-Policies + serverseitige Rechteprüfung |

**Sicherheit:**
- Kein offener Port (Tunnel nur ausgehend). Login + HTTPS via Cloudflare Access.
- Twitch-Token und Secrets **nur serverseitig**, nie im Browser.
- Mods sehen/dürfen weniger (z. B. kein endgültiges Stream-Stop).

---

## 11. Bau-Roadmap (wenn's losgeht)

- **Stufe 1:** cloudflared-Tunnel + feste Adresse + Access-Login + Streamer-Seite
  mit Steuer-Knöpfen + Ampel. → Sie kann von überall steuern. (größter Nutzen)
- **Stufe 2:** Szenen-Vorschau + Rollen (die Streamerin voll / Mods eingeschränkt).
- **Stufe 3:** Twitch-Titel/Kategorie (Twitch-App + der Streamerin Login).
- **Stufe 4:** Mod-Messaging/tts-Komfort + PWA-Feinschliff (Icon, Home-Screen).

---

## 12. Nächster Schritt (Planung)

Offen ist nur noch die **Adress-/Domain-Frage (Punkt 8)**. Sobald die geklärt ist,
ist das Konzept komplett und wir können mit **Stufe 1** starten.
