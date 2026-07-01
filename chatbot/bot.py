#!/usr/bin/env python3
"""
Twitch-Chat-Steuerung fuer den IRL-Relay-Server
================================================
Liest den Twitch-Chat eines Kanals mit und steuert OBS per obs-websocket:

  !start  ->  Twitch-Uebertragung STARTEN + Startszene ("Gleich geht's los", Clips)
  !live   ->  auf die LIVE-Szene wechseln (Handybild)
  !stop   ->  Twitch-Uebertragung STOPPEN (optional Offline-Szene)

Nur die Streamerin (Broadcaster), Mods oder Namen aus der Erlaubnisliste
duerfen die Befehle ausloesen.

Benoetigt: Python 3, Paket "obsws-python"  (pip install -r requirements.txt)
Konfiguration: config.ini  (Vorlage: config.example.ini)
Start:        python bot.py     (oder start_bot.bat unter Windows)
"""

import configparser
import socket
import ssl
import sys
import threading
import time
from pathlib import Path

try:
    import obsws_python as obs
except ImportError:
    print("Fehlt: pip install obsws-python")
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None  # !tts ist dann deaktiviert

# ---------------------------------------------------------------------------
# Konfiguration laden
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).with_name("config.ini")
if not CONFIG_PATH.exists():
    print(f"Keine config.ini gefunden. Kopiere config.example.ini nach config.ini "
          f"und trage deine Werte ein.\n(Erwartet: {CONFIG_PATH})")
    sys.exit(1)

cfg = configparser.ConfigParser()
cfg.read(CONFIG_PATH, encoding="utf-8")

# Twitch
BOT_USER = cfg.get("twitch", "bot_username").strip().lower()
OAUTH = cfg.get("twitch", "oauth_token").strip()           # Form: oauth:xxxxxxxx
CHANNEL = cfg.get("twitch", "channel").strip().lower()     # ihr Kanal, klein
if not OAUTH.startswith("oauth:"):
    OAUTH = "oauth:" + OAUTH

# OBS
OBS_HOST = cfg.get("obs", "host", fallback="localhost")
OBS_PORT = cfg.getint("obs", "port", fallback=4455)
OBS_PASSWORD = cfg.get("obs", "password", fallback="")

# Szenen
SCENE_START = cfg.get("scenes", "start", fallback="Start Soon")
SCENE_LIVE = cfg.get("scenes", "live", fallback="Live")
SCENE_STOP = cfg.get("scenes", "stop", fallback="").strip()   # leer = nichts
# eigene Pausen-Szene fuer !brb (leer = Start-Szene verwenden)
SCENE_BRB = cfg.get("scenes", "brb", fallback="").strip() or SCENE_START

# Automatische Szenenwechsel (z.B. go-irl bei Funkloch) im Chat ankuendigen.
# scenes -> ansagen = false  schaltet das ab.
ANSAGEN_AN = cfg.getboolean("scenes", "ansagen", fallback=True)
SZENE_ANSAGEN = {
    SCENE_BRB:  "⚠️ Kurze Verbindungspause – gleich wieder da! 🐾",
    SCENE_LIVE: "🔴 Und weiter geht's, wir sind zurück!",
}
_sock = None             # aktueller IRC-Socket (fuer Ansage aus dem Watcher-Thread)
_letzter_befehl = 0.0    # Zeit des letzten Bot-Befehls (Echo-Unterdrueckung)
_letzte_szene = None

# Befehle (anpassbar)
CMD_START = cfg.get("commands", "start", fallback="!start").lower()
CMD_LIVE = cfg.get("commands", "live", fallback="!live").lower()
CMD_STOP = cfg.get("commands", "stop", fallback="!stop").lower()
CMD_BRB = cfg.get("commands", "brb", fallback="!brb").lower()
CMD_TTS = cfg.get("commands", "tts", fallback="!tts").lower()

# !tts -> Nachricht als Telegram-Push an das Handy der Streamerin
TG_TOKEN = cfg.get("telegram", "token", fallback="").strip()
TTS_CHAT = cfg.get("telegram", "streamer_chat_id", fallback="").strip()

# zusaetzlich erlaubte Nutzer (Komma-getrennt, klein)
ALLOW = {u.strip().lower() for u in
         cfg.get("permissions", "extra_allowed", fallback="").split(",")
         if u.strip()}

COOLDOWN = cfg.getint("permissions", "cooldown_seconds", fallback=3)

IRC_HOST = "irc.chat.twitch.tv"
IRC_PORT = 6697  # TLS

# ---------------------------------------------------------------------------
# OBS-Steuerung (mit Wiederverbindung, falls OBS gerade nicht laeuft)
# ---------------------------------------------------------------------------
def obs_client():
    """Baut bei jedem Befehl frisch eine Verbindung auf (robust, simpel)."""
    return obs.ReqClient(host=OBS_HOST, port=OBS_PORT,
                         password=OBS_PASSWORD, timeout=5)


def obs_set_scene(name):
    cl = obs_client()
    cl.set_current_program_scene(name)


def obs_start_stream():
    cl = obs_client()
    try:
        st = cl.get_stream_status()
        if getattr(st, "output_active", False):
            return  # laeuft schon
    except Exception:
        pass
    cl.start_stream()


def obs_stop_stream():
    cl = obs_client()
    try:
        cl.stop_stream()
    except Exception:
        pass


def szenen_watcher():
    """Pollt die OBS-Szene und kuendigt AUTOMATISCHE Wechsel im Chat an
    (z.B. go-irl bei Funkloch). Eigene Befehls-Wechsel werden unterdrueckt."""
    global _letzte_szene
    while True:
        try:
            sc = obs_client().get_current_program_scene()
            szene = getattr(sc, "current_program_scene_name", None)
            if szene:
                if _letzte_szene is None:
                    _letzte_szene = szene
                elif szene != _letzte_szene:
                    _letzte_szene = szene
                    if time.time() - _letzter_befehl >= 6 and _sock:
                        msg = SZENE_ANSAGEN.get(szene)
                        if msg:
                            send_chat(_sock, msg)
                            print(f"[Auto-Szene] {szene} -> angekuendigt")
        except Exception:
            pass
        time.sleep(3)


# ---------------------------------------------------------------------------
# IRC-Hilfsfunktionen
# ---------------------------------------------------------------------------
def connect_irc():
    raw = socket.create_connection((IRC_HOST, IRC_PORT), timeout=15)
    ctx = ssl.create_default_context()
    sock = ctx.wrap_socket(raw, server_hostname=IRC_HOST)
    sock.sendall(b"CAP REQ :twitch.tv/tags twitch.tv/commands\r\n")
    sock.sendall(f"PASS {OAUTH}\r\n".encode())
    sock.sendall(f"NICK {BOT_USER}\r\n".encode())
    sock.sendall(f"JOIN #{CHANNEL}\r\n".encode())
    return sock


def send_chat(sock, text):
    try:
        sock.sendall(f"PRIVMSG #{CHANNEL} :{text}\r\n".encode())
    except Exception:
        pass


def parse_message(line):
    """Zerlegt eine IRC-Zeile. Gibt (tags, user, command, channel, text) zurueck."""
    tags = {}
    rest = line
    if rest.startswith("@"):
        tagpart, rest = rest[1:].split(" ", 1)
        for kv in tagpart.split(";"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                tags[k] = v
    prefix = ""
    if rest.startswith(":"):
        prefix, rest = rest[1:].split(" ", 1)
    parts = rest.split(" ", 2)
    command = parts[0] if parts else ""
    channel = parts[1] if len(parts) > 1 else ""
    text = ""
    if len(parts) > 2 and parts[2].startswith(":"):
        text = parts[2][1:]
    user = prefix.split("!", 1)[0] if "!" in prefix else prefix
    return tags, user.lower(), command, channel, text.strip()


def is_allowed(tags, user):
    """Broadcaster, Mods oder Erlaubnisliste duerfen Befehle nutzen."""
    if tags.get("mod") == "1":
        return True
    badges = tags.get("badges", "")
    if "broadcaster/" in badges:
        return True
    # der Kanalinhaber selbst
    if user == CHANNEL:
        return True
    if user in ALLOW:
        return True
    return False


# ---------------------------------------------------------------------------
# Hauptschleife
# ---------------------------------------------------------------------------
def handle_command(sock, cmd, user="", text=""):
    """Fuehrt den Befehl aus und meldet sich im Chat zurueck."""
    global _letzter_befehl
    _letzter_befehl = time.time()   # eigene Wechsel nicht doppelt ansagen
    try:
        if cmd == CMD_START:
            obs_start_stream()
            obs_set_scene(SCENE_START)
            send_chat(sock, "Stream wird gestartet - gleich geht's los! 🎬")
        elif cmd == CMD_LIVE:
            obs_set_scene(SCENE_LIVE)
            send_chat(sock, "Wir sind LIVE! 🔴")
        elif cmd == CMD_BRB:
            obs_set_scene(SCENE_BRB)
            send_chat(sock, "Kurze Pause - gleich geht's weiter! ⏸")
        elif cmd == CMD_TTS:
            inhalt = text[len(CMD_TTS):].strip().strip('"').strip()
            if requests is None or not TG_TOKEN or not TTS_CHAT:
                send_chat(sock, "!tts ist noch nicht eingerichtet "
                                "([telegram] in der config.ini fehlt).")
            elif not inhalt:
                send_chat(sock, "So geht's:  !tts deine Nachricht an die Streamerin")
            else:
                requests.post(
                    f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                    json={"chat_id": TTS_CHAT,
                          "text": f"📢 {user}: {inhalt}"}, timeout=10)
                send_chat(sock, "Nachricht ist unterwegs zur Streamerin 📨")
        elif cmd == CMD_STOP:
            if SCENE_STOP:
                try:
                    obs_set_scene(SCENE_STOP)
                except Exception:
                    pass
            obs_stop_stream()
            send_chat(sock, "Stream beendet. Bis zum naechsten Mal! 👋")
    except Exception as e:
        send_chat(sock, "Fehler bei der OBS-Steuerung - laeuft OBS? "
                        "(Details siehe Server-Konsole)")
        print(f"[OBS-FEHLER] {cmd}: {e}")


def run():
    global _sock
    print(f"Verbinde mit Twitch-Chat #{CHANNEL} als {BOT_USER} ...")
    last_used = 0.0
    known_cmds = {CMD_START, CMD_LIVE, CMD_STOP, CMD_BRB, CMD_TTS}
    if ANSAGEN_AN and obs is not None:
        threading.Thread(target=szenen_watcher, daemon=True).start()
        print("Szenen-Ansage aktiv (automatische Wechsel werden im Chat gemeldet).")

    while True:  # aeussere Schleife = Wiederverbindung
        try:
            sock = connect_irc()
            _sock = sock
            sock.settimeout(330)   # Chat-Stille ueberbruecken (Twitch pingt ~5 Min)
            buffer = ""
            print("Verbunden. Warte auf Befehle (!start / !live / !stop).")
            while True:
                try:
                    data = sock.recv(4096).decode("utf-8", errors="ignore")
                except socket.timeout:
                    # lange Stille -> Verbindung aktiv pruefen statt neu verbinden
                    sock.sendall(b"PING :tmi.twitch.tv\r\n")
                    continue
                if not data:
                    raise ConnectionError("Verbindung getrennt")
                buffer += data
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    if not line:
                        continue
                    if line.startswith("PING"):
                        sock.sendall(("PONG " + line.split(" ", 1)[1] +
                                      "\r\n").encode())
                        continue
                    tags, user, command, channel, text = parse_message(line)
                    if command != "PRIVMSG":
                        continue
                    cmd = text.lower().split(" ", 1)[0]
                    if cmd not in known_cmds:
                        continue
                    if not is_allowed(tags, user):
                        print(f"[abgelehnt] {user}: {cmd} (keine Rechte)")
                        continue
                    now = time.time()
                    if now - last_used < COOLDOWN:
                        continue
                    last_used = now
                    print(f"[Befehl] {user}: {cmd}")
                    handle_command(sock, cmd, user, text)
        except KeyboardInterrupt:
            print("\nBeendet.")
            return
        except Exception as e:
            print(f"[Verbindungsfehler] {e} - neuer Versuch in 10 s ...")
            time.sleep(10)


if __name__ == "__main__":
    run()
