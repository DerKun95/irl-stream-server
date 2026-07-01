# Schritt 17 – Follower-/Sub-Alerts mit StreamElements

Ziel: Wenn jemand **folgt, abonniert, raidet oder Bits cheert**, ploppt eine
animierte Einblendung im Stream auf – im Pastell-Look. Wir nutzen den kostenlosen
Dienst **StreamElements** (keine Programmierung, sehr zuverlässig).

> Wichtig: Die Alerts reagieren auf **der Streamerin Kanal-Events**. Darum muss das
> StreamElements-Konto mit **der Streamerin Twitch-Account** verbunden sein.

---

## 17.1 – StreamElements mit der Streamerin Account einrichten

1. Auf **<https://streamelements.com>** gehen → **„Login"** → **„Login with Twitch"**.
2. **Mit der Streamerin Twitch-Account** anmelden (nicht mit deinem!) und die Berechtigung
   bestätigen. (Am besten macht die Streamerin das kurz selbst, oder ihr macht es zusammen.)

---

## 17.2 – Die Alert-Box-URL holen

1. Im StreamElements-Dashboard links auf **„Streaming Tools" → „Overlays"**
   (oder „My Overlays").
2. Es gibt ein Standard-Overlay (oder lege mit **„New Overlay"** eins an,
   Auflösung **1920×1080**). Öffne es im Editor.
3. Falls noch keine Alert-Box drin ist: oben **„Add Widget" → „Alertbox"**
   hinzufügen.
4. Oben/rechts gibt es **„Copy URL"** (manchmal unter den drei Punkten „⋮" →
   „Copy Overlay URL"). Diesen Link **kopieren**.
   - ⚠️ Dieser Link ist **geheim** (wer ihn hat, kann Alerts auslösen) – nicht
     öffentlich teilen.

---

## 17.3 – In OBS einbauen (auf dem Server)

1. OBS → Szene **Live** → Quellen → **+ → Browser**.
2. Name `Alerts` → bei URL den kopierten StreamElements-Link einfügen.
3. **Breite 1920, Höhe 1080** → OK.
4. Quelle in der Liste **ganz nach oben** ziehen (damit die Alerts über allem
   einblenden – auch über dem Handybild und den Overlays).

> Das funktioniert, obwohl OBS bei dir auf dem Server läuft: Die Alert-Box holt
> die Events über das Internet aus der Streamerin Kanal. Der Server braucht nur (hat ja)
> Internet.

---

## 17.4 – Im Pastell-Look stylen

Im StreamElements-Dashboard die **Alertbox** bearbeiten (im Overlay-Editor auf das
Widget klicken → Einstellungen):
- Pro Event eigene Einstellung: **Follower / Subscriber / Raid / Cheer**.
- **Schriftfarbe / Akzent:** Pink `#ff7fc3`, Lavendel `#b89aea`, Weiß.
- **Schriftart:** etwas Verspieltes (passend zu „Ink Free"/Comic-Stil).
- Optional **Sound** pro Alert (kurz, dezent).
- **Anzeigedauer:** ~4–6 Sekunden.
- Text z. B.: „💜 {name} ist jetzt dabei!", „🎉 {name} abonniert – danke!",
  „🚀 {name} raidet mit {amount} Leuten!".

---

## 17.5 – Testen

Im StreamElements-Dashboard gibt es einen **„Test"-Knopf** (Test Follower / Test
Sub / Test Raid). Auslösen → der Alert sollte in OBS (und im Vorschaufenster)
einblenden.

✓ Erfolgskontrolle: Test-Alert erscheint animiert in OBS über dem Bild.

---

## Hinweise

- Die Alert-Box-Browserquelle einfach **dauerhaft** in der Live-Szene lassen –
  sie zeigt nur was an, wenn ein Event kommt, sonst ist sie unsichtbar.
- Soll sie auch in Start Soon/BRB einblenden? Dann die Quelle zusätzlich in
  diese Szenen legen (als Referenz kopieren) – oder in einer immer sichtbaren
  „Über alles"-Ebene. Fürs Erste reicht die Live-Szene.
- StreamElements kann später noch mehr (Ziele, Chat-Overlay, Sub-Counter) –
  alles optional.
