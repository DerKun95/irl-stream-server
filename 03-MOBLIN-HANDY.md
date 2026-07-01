# Schritt 3 – Handy mit Moblin einrichten (SRT senden)

Moblin ist die kostenlose App, die dein Handybild per SRT an den Laptop schickt.
(Moblin gibt es für iPhone; für Android nutzt du eine vergleichbare SRT-App wie
„IRL Pro“ oder „Larix Broadcaster“ – die Werte sind dieselben.)

---

## 3.1 – Voraussetzung: Laptop-Adresse kennen

Damit das Handy den Laptop findet, brauchst du dessen Adresse. **Zwei Wege:**

- **Über das VPN (empfohlen, funktioniert auch mobil/unterwegs):** die
  **Tailscale-IP** des Laptops (Form `100.x.y.z`). Wie du Tailscale einrichtest und
  die IP findest, steht in **`04-FERNZUGRIFF.md`**. Richte das am besten zuerst ein.
- **Nur im Heimnetz (zum Testen):** die lokale IP des Laptops. Auf dem Laptop:
  Eingabeaufforderung öffnen, `ipconfig` eingeben, „IPv4-Adresse“ ablesen
  (z. B. `192.168.0.50`).

> Für echtes IRL unterwegs nimmst du **immer die Tailscale-IP**, weil das Handy dann
> über Mobilfunk sicher zum Laptop kommt – ohne Portfreigabe am Router.

---

## 3.2 – Moblin einrichten

1. Moblin im App Store laden und öffnen.
2. Neuen Stream/„Connection“ anlegen.
3. **Protokoll:** **SRT** (nicht RTMP).
4. **Server-URL / Ziel** eintragen (Beispiel mit Tailscale-IP des Laptops und
   Port 9999):

   ```
   srt://100.x.y.z:9999?latency=2000000
   ```
   *Erklärt: gleiche IP wie der Laptop, gleicher Port wie in OBS (9999), gleicher
   latency-Wert (2000 ms Puffer). `100.x.y.z` durch deine echte Tailscale-IP ersetzen.*

5. **Auflösung:** 1280×720 · **FPS:** 30 (passt zu OBS).
6. **Bitrate:** 2500–3500 kbit/s als Start. **Adaptive Bitrate aktivieren**, falls
   vorhanden – dann senkt Moblin bei schlechtem Netz automatisch die Bitrate.

---

## 3.3 – Test

1. Auf dem Laptop muss OBS laufen und die SRT-Medienquelle aktiv sein.
2. In Moblin auf **„Go Live“ / Start** tippen.
3. Nach 1–3 Sekunden erscheint dein Handybild in OBS.

**Erfolgskontrolle:** Das Bild vom Handy ist in OBS sichtbar und flüssig.

---

## 3.4 – Tipps für unterwegs

- **latency höher** bei bekannt schlechter Strecke: in Moblin **und** OBS auf
  `3000000` (3000 ms) setzen – mehr Puffer, etwas mehr Verzögerung.
- **Adaptive Bitrate immer an** – das ist der wichtigste Schalter gegen Abbrüche.
- Handy möglichst mit gutem Empfang halten; in Funklöchern (Tiefgarage, Aufzug)
  reißt jeder Stream ab – dafür ist die Stand-by-Szene in OBS da.

Mehr dazu in **`06-PROBLEMHILFE.md`**.
