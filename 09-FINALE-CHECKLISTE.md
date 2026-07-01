# Finale Checkliste – System für die Streamerin scharf schalten

Stand: 06.06.2026 – Test auf deinem Kanal (DEIN_TEST_KANAL) erfolgreich:
`!start` / `!live` / `!stop` steuern OBS auf dem Server. ✅

## A) Auf ihren Kanal umstellen (wenn ihr bereit seid)

1. **`config.ini`** (im chatbot-Ordner auf dem Laptop):
   `channel = DEIN_KANAL` → speichern → Bot neu starten (`start_bot.bat`).
2. **OBS → Einstellungen → Stream:** IHREN Stream-Schlüssel eintragen.
   (Falls beim Testen `?bandwidthtest=true` am Schlüssel hing: entfernen!)
3. **Sie macht den Bot zum Mod** – in ihrem Chat: `/mod DEIN-BOT-ACCOUNT`
   (sonst kann er in vollen Chats nicht zuverlässig antworten).
4. **Wer darf steuern?** Sie + ihre Mods automatisch. Dich selbst ggf. in
   `config.ini` bei `extra_allowed = DEIN_TEST_KANAL` eintragen (falls du kein Mod bist).
5. **Ihr Moblin** (einmalig): URL `srt://DEIN-NAME.duckdns.org:DEIN-PORT?latency=2000000`,
   Stream-ID `live`, 1280x720, 30 fps, Bitrate 3500, adaptive Bitrate AN.

## B) Server-Dauerbetrieb (damit alles von selbst läuft)

- [ ] **Bot-Autostart:** `Win + R` → `shell:startup` → Verknüpfung von
      `start_bot.bat` hineinlegen.
- [ ] **OBS-Autostart:** ebenfalls Verknüpfung in `shell:startup`.
      Wichtig: In OBS unter Werkzeuge → WebSocket-Servereinstellungen bleibt
      der Server aktiviert (Haken gesetzt lassen).
- [ ] **RustDesk:** „Mit Systemstart starten“ aktiviert.
- [ ] **Tailscale:** „Run unattended“ aktiviert (erledigt).
- [ ] **Energie:** Energiesparmodus „Nie“, Zuklappen = „Nichts unternehmen“.
- [ ] **Deckel:** offen lassen ODER HDMI-Dummy-Stecker (~5 €) für Betrieb
      mit geschlossenem Deckel.

## C) Wenn der Laptop in die Ecke umzieht

- [ ] **LAN-Kabel anschließen** (stabiler als WLAN!).
- [ ] Danach in der FritzBox die **Portfreigabe (UDP DEIN-PORT)** auf das neue
      Geräte-Profil/die neue IP des Laptops umstellen
      (Internet → Freigaben → Portfreigaben → SRT bearbeiten).
- [ ] Kurzer Testlauf: Moblin über mobile Daten → Bild in OBS?

## D) Feinschliff (später, optional)

- [ ] **Clips in der „Start Soon“-Szene:** VLC installieren → in OBS
      „VLC-Videoquelle“ hinzufügen → Ordner mit ihren Clip-Videos als
      Playlist, Schleife + Zufall an. Text darüber legen.
- [ ] **Lokale Backup-Aufnahme:** OBS → Ausgabe → Aufnahme → Pfad auf die
      1-TB-HDD (z. B. `D:\Aufnahmen`), Format mkv.
- [ ] **Twitch „Disconnect Protection“** in ihrem Creator-Dashboard aktivieren.
- [ ] Bei Bedarf weitere Befehle für den Bot (z. B. `!szene xyz`, `!brb`) –
      einfach melden.

## Wichtige Eckdaten (Spickzettel)

| Was                  | Wert                                                  |
|----------------------|-------------------------------------------------------|
| SRT-Empfang (OBS)    | `srt://0.0.0.0:DEIN-PORT?mode=listener&latency=2000000`   |
| Moblin-URL           | `srt://DEIN-NAME.duckdns.org:DEIN-PORT?latency=2000000`   |
| Portfreigabe         | FritzBox UDP DEIN-PORT → Laptop                           |
| DynDNS               | DuckDNS (nur IPv4!), FritzBox hält aktuell            |
| OBS-Fernsteuerung    | WebSocket Port 4455 (Passwort in config.ini)          |
| Bot-Account          | DEIN-BOT-ACCOUNT                                          |
| Befehle              | `!start` / `!live` / `!stop` (Mods + erlaubte Namen)  |
| Szenen               | `Start Soon` / `Live` (Namen exakt!)                  |
| Fernzugriff Admin    | Tailscale + RustDesk (`DEINE-TAILSCALE-IP`)                |
