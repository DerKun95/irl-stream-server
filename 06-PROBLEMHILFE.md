# Schritt 6 – Problemhilfe (Troubleshooting)

Häufige Probleme und was du der Reihe nach tust. Immer von oben nach unten arbeiten.

---

## Kein Bild vom Handy in OBS

1. Läuft in OBS die **SRT-Medienquelle** (nicht ausgeblendet, Auge an)?
2. Stimmen **IP und Port** auf beiden Seiten? OBS: `...0.0.0.0:9999...`,
   Handy: `srt://<Tailscale-IP>:9999...` – **gleicher Port (9999)**.
3. Sind **Laptop und Handy bei Tailscale „online“**? (Taskleisten-Symbol / App)
4. Sendet das Handy wirklich (Moblin „Go Live“ aktiv)?
5. Teste zuerst im **Heimnetz** mit der lokalen IP (`ipconfig`), dann unterwegs mit
   der Tailscale-IP.

---

## Bild ruckelt / „verworfene Frames“ steigen

1. OBS **Statistiken** öffnen (Docks → Statistiken).
2. **„Verworfene Frames (Netzwerk)“ steigen** → das Netz ist zu schwach:
   - Im Handy **Bitrate senken** (z. B. auf 2000 kbit/s), **adaptive Bitrate an**.
   - **SRT latency erhöhen** (Handy + OBS) auf `3000000` (3000 ms).
3. **„Übersprungene Frames (Encoding)“ steigen** → der Laptop kommt nicht hinterher:
   - In OBS Encoder-Voreinstellung von P5 auf **P4** stellen.
   - Sicherstellen, dass **NVENC** (nicht x264/CPU) gewählt ist.

---

## Stream startet nicht / Twitch-Fehler

1. Internet am Laptop ok? Eine Webseite öffnen.
2. **Twitch-Verbindung** in OBS noch gültig? Ggf. Konto neu verbinden oder
   Stream-Schlüssel neu aus dem Twitch-Dashboard kopieren.
3. Fehlermeldung mit **„NVENC“**? → Grafiktreiber neu installieren
   (`01-WINDOWS-NEU-AUFSETZEN.md`, Abschnitt 1.5), Laptop neu starten. Notlösung:
   Encoder vorübergehend auf **x264** (CPU) stellen.

---

## Verbindung bricht unterwegs immer wieder ab (Low Connection)

Das ist bei Mobilfunk normal. So machst du es robuster:

1. **Adaptive Bitrate** im Handy IMMER aktiv.
2. **latency hoch:** `3000000`–`4000000` (3–4 Sek. Puffer) auf Handy und in OBS.
3. **Auflösung/FPS niedrig halten:** 720p/30 statt 1080p/60.
4. **Stand-by-Szene** parat haben und bei Funkloch dorthin wechseln (Hotwey).
5. **Twitch „Disconnect Protection“** aktivieren, damit kurze Abrisse den Stream
   nicht beenden.
6. Bekannt schlechte Strecken (Tunnel, Tiefgarage) lassen sich technisch nicht
   retten – kurz auf Stand-by gehen.

> Für maximale Stabilität gibt es **SRTLA** (bündelt WLAN + Mobilfunk). Das braucht
> aber zusätzliche Technik vor OBS und ist eine spätere Ausbaustufe. Frag mich, wenn
> du das einmal angehen willst.

---

## Laptop schläft ein / Stream stoppt von selbst

- Energieeinstellungen prüfen (`01-WINDOWS-NEU-AUFSETZEN.md`, Abschnitt 1.6):
  Energiesparmodus auf **„Nie“**, beim Zuklappen **„Nichts unternehmen“**.

---

## Fernzugriff klappt nicht

1. **Tailscale** auf beiden Geräten „online“ und **gleiches Konto**?
2. RustDesk: über die **Tailscale-IP** des Laptops verbinden.
3. RustDesk-**Passwort** korrekt? Bei „unbeaufsichtigtem Zugriff“ permanentes
   Passwort gesetzt?
4. Beim Freund: ist die **Freigabe** in Tailscale noch aktiv?

---

## Ton fehlt / asynchron

- Prüfe in OBS beim Mischpult, ob die **Handy-SRT-Quelle** einen Audiopegel zeigt.
- Bei leichtem Versatz: Rechtsklick auf die Quelle → **„Audio-Eigenschaften“** →
  **Synchronisationsversatz** anpassen (in ms).

---

Kommst du an einem Punkt nicht weiter? Sag mir genau, was auf dem Bildschirm steht
(oder die Fehlermeldung) und in welchem Schritt du bist – dann gehen wir es zusammen
durch.
