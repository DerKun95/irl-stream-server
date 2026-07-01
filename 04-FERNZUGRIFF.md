# Schritt 4 – Fernzugriff: Tailscale (VPN) + RustDesk

Damit du den Laptop vom Gaming-PC aus bedienen kannst und ein Freund bei Bedarf
hilft – sicher, ohne Portfreigaben am Router.

- **Tailscale** = sicheres privates Netz. Verbindet Laptop, Handy, Gaming-PC und
  Freund, und liefert die Adresse, über die das Handy den SRT-Stream schickt.
- **RustDesk** = Bildschirm des Laptops sehen und fernsteuern.

---

## 4.1 – Tailscale auf dem Laptop installieren

1. Gehe auf **<https://tailscale.com/download/windows>** und lade Tailscale.
2. Installiere es und melde dich an (kostenloses Konto, z. B. mit Google/Microsoft).
3. Nach dem Login ist der Laptop im Netz. **Tailscale-IP anzeigen:**
   - Auf das Tailscale-Symbol unten rechts (Taskleiste) klicken → die IP
     (`100.x.y.z`) wird angezeigt. **Diese IP brauchst du fürs Handy (Moblin).**
4. Damit der Laptop dauerhaft erreichbar bleibt: In der Tailscale-Admin-Konsole
   (**<https://login.tailscale.com/admin/machines>**) beim Laptop den
   **Schlüssel-Ablauf deaktivieren** („Disable key expiry“).

---

## 4.2 – Tailscale auf dem Gaming-PC

1. Gleiche Installation auf deinem Gaming-PC, mit **demselben Konto** anmelden.
2. Jetzt sehen sich Laptop und Gaming-PC gegenseitig im privaten Netz.

---

## 4.3 – Einem Freund Zugriff geben (nur bei Bedarf)

So bekommt der Freund Zugriff auf **genau den Laptop**, nicht auf dein ganzes Netz:

1. In der Tailscale-Admin-Konsole den Laptop auswählen → **„Share“**.
2. Es wird ein **Einladungslink** erzeugt – den schickst du dem Freund.
3. Der Freund installiert Tailscale, öffnet den Link und sieht dann nur den Laptop.
4. **Nach der Hilfe** die Freigabe wieder entfernen.

---

## 4.4 – RustDesk installieren (Bildschirmsteuerung)

**Auf dem Laptop:**

1. Gehe auf **<https://rustdesk.com/>** und lade RustDesk für Windows (.exe).
2. Starte RustDesk. Du siehst eine **ID** und ein **Einmal-Passwort**.
3. Für dauerhaften Zugriff: **Einstellungen → Sicherheit → „Permanentes Passwort
   setzen“** (ein starkes, einzigartiges Passwort).
4. Optional: **„Unbeaufsichtigter Zugriff“** aktivieren, damit du dich auch
   verbinden kannst, wenn niemand am Laptop sitzt.

**Auf dem Gaming-PC / beim Freund:** ebenfalls RustDesk installieren. Verbinden über
die **ID** des Laptops + Passwort. Tipp: am stabilsten klappt es, wenn du die
**Tailscale-IP** des Laptops als Adresse nutzt.

---

## 4.5 – Autostart: Laptop kommt betriebsbereit hoch

Damit nach einem Neustart alles von selbst läuft:

- **Tailscale** startet standardmäßig automatisch mit Windows (nichts zu tun).
- **RustDesk** in den Autostart legen: RustDesk **Einstellungen → Allgemein →
  „Mit Systemstart starten“** aktivieren.
- **OBS** (optional) automatisch starten: Drücke `Win + R`, tippe `shell:startup`,
  Enter. In den geöffneten Ordner eine **Verknüpfung von OBS** hineinziehen. So
  startet OBS beim Anmelden mit. (Den eigentlichen Stream startest du bewusst von
  Hand, wenn du live gehst.)

> Für unbeaufsichtigten Betrieb müsste Windows sich automatisch anmelden. Das ist
> bequem, aber weniger sicher – nur einrichten, wenn der Laptop an einem sicheren
> Ort steht. Sonst meldest du dich per RustDesk an.

---

## 4.6 – Sicherheit (kurz & wichtig)

- **Starke, unterschiedliche Passwörter** für Windows und RustDesk.
- **Tailscale-Konto mit Zwei-Faktor (MFA)** absichern.
- Fernzugriff möglichst **über Tailscale** laufen lassen (privates Netz).
- **Windows-Firewall anlassen** (Standard). Für SRT über Tailscale ist **keine**
  Portfreigabe am Router nötig.
- Freundes-Freigabe in Tailscale nach der Hilfe wieder **entfernen**; bei RustDesk
  das Passwort danach **ändern**, wenn du es weitergegeben hast.

---

Weiter mit **`05-TESTPLAN.md`**.
