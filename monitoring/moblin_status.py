#!/usr/bin/env python3
"""
Moblin-Status-Empfaenger (Assistent)
====================================
Der Waechter spielt den "Assistenten" von Moblins Fernsteuerung. Moblin
(das Handy) verbindet sich hierher und schickt laufend seinen Status -
wir lesen daraus AKKU %, LADE-STATUS, WAERME-FLAMME und BITRATE.

So einrichten (am Handy in Moblin):
  Einstellungen -> Fernbedienung -> Streamer
    - Aktiviert: AN
    - Assistent-URL: ws://<PC-IP>:2345   (im Heimnetz die lokale IP,
      unterwegs die Tailscale-IP des PCs)
    - Passwort: dasselbe wie unten in der config.ini

Zum TESTEN allein (ohne Waechter):
    pip install websockets
    python moblin_status.py
  -> dann am Handy verbinden. Hier sollten die Werte erscheinen.

Wird vom Waechter importiert: moblin_start() startet den Server im Hintergrund,
moblin_werte() liefert das zuletzt empfangene Dict.
"""
import asyncio, base64, configparser, hashlib, json, os, threading, time
from pathlib import Path

CFG = Path(__file__).with_name("config.ini")
_cfg = configparser.ConfigParser()
if CFG.exists():
    _cfg.read(CFG, encoding="utf-8")

ENABLED = _cfg.getboolean("moblin", "enabled", fallback=True)
PORT = _cfg.getint("moblin", "port", fallback=2345)
PASSWORT = _cfg.get("moblin", "passwort", fallback="").strip()
# Verschluesselung: Moblin verschluesselt die Assistent-Verbindung evtl. mit AES
# (Schluessel = SHA256(Passwort)). Wenn's mit false nicht klappt -> auf true.
VERSCHLUESSELT = _cfg.getboolean("moblin", "verschluesselt", fallback=False)
INTERVALL = _cfg.getint("moblin", "status_intervall", fallback=2)
# Debug: zeigt jede empfangene Nachricht an (zum Einrichten). In config.ini
# [moblin] debug = true setzen, wenn man wieder mitlesen will.
DEBUG = _cfg.getboolean("moblin", "debug", fallback=False)
STATUS_DATEI = Path(__file__).with_name("moblin_status.json")

# Zuletzt empfangene Werte (wird laufend aktualisiert)
LATEST = {"akku": None, "laedt": None, "flamme": None,
          "bitrate": None, "live": None, "zeit": 0.0}

# Flamme (iOS-Thermal) -> Klartext
FLAMME_TEXT = {"White": "ok", "Yellow": "heiß", "Red": "kritisch"}


def _hash_passwort(challenge, salt, passwort):
    """Nachbau von remoteControlHashPassword aus Moblin (RemoteControl.swift)."""
    h = hashlib.sha256((passwort + salt).encode()).digest()
    b = base64.b64encode(h).decode()
    h2 = hashlib.sha256((b + challenge).encode()).digest()
    return base64.b64encode(h2).decode()


def _aes_key():
    return hashlib.sha256(PASSWORT.encode()).digest()


def _entschluesseln(roh):
    """roh (bytes) -> Klartext-String. AES-GCM combined = nonce(12)+ct+tag."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce, rest = roh[:12], roh[12:]
    return AESGCM(_aes_key()).decrypt(nonce, rest, None).decode("utf-8")


def _verschluesseln(text):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = os.urandom(12)
    ct = AESGCM(_aes_key()).encrypt(nonce, text.encode("utf-8"), None)
    return nonce + ct


def _dekodieren(roh):
    """Eingehende Nachricht (str ODER bytes) -> dict. Erkennt Klartext/AES selbst."""
    if isinstance(roh, str):
        try:
            return json.loads(roh)
        except Exception:
            return None
    # bytes: erst als UTF-8-JSON versuchen, sonst AES
    try:
        return json.loads(roh.decode("utf-8"))
    except Exception:
        pass
    try:
        return json.loads(_entschluesseln(roh))
    except Exception:
        return None


def _setze(status):
    """Uebernimmt Werte aus einem Status-Block (general/topRight)."""
    gen = status.get("general") or {}
    tr = status.get("topRight") or {}
    neu = False
    if "batteryLevel" in gen:
        LATEST["akku"] = gen.get("batteryLevel"); neu = True
    if "batteryCharging" in gen:
        LATEST["laedt"] = gen.get("batteryCharging"); neu = True
    if "flame" in gen and gen.get("flame") is not None:
        LATEST["flamme"] = FLAMME_TEXT.get(gen.get("flame"), gen.get("flame")); neu = True
    if "isLive" in gen:
        LATEST["live"] = gen.get("isLive")
    bit = tr.get("bitrate")
    if isinstance(bit, dict) and bit.get("message"):
        LATEST["bitrate"] = bit.get("message"); neu = True
    if neu:
        LATEST["zeit"] = time.time()
        try:
            STATUS_DATEI.write_text(json.dumps(LATEST), encoding="utf-8")
        except Exception:
            pass
        print(f"[Moblin] Akku {LATEST['akku']}%"
              f"{' (lädt)' if LATEST['laedt'] else ''} · "
              f"Wärme {LATEST['flamme']} · Bitrate {LATEST['bitrate']}")


def _status_aus_nachricht(m):
    if not isinstance(m, dict):
        return None
    if "event" in m:
        data = (m["event"] or {}).get("data") or {}
        if "status" in data:
            return data["status"]
    if "response" in m:
        d = (m["response"] or {}).get("data")
        if isinstance(d, dict) and "getStatus" in d:
            return d["getStatus"]
    return None


async def _sende(ws, obj, verschluesselt):
    text = json.dumps(obj)
    if verschluesselt:
        await ws.send(_verschluesseln(text))
    else:
        await ws.send(text)


async def _handler(ws, *_):
    print("[Moblin] Streamer verbindet ...")
    verschl = VERSCHLUESSELT          # Sende-Modus (wird ggf. angepasst)
    challenge = base64.b64encode(os.urandom(32)).decode()
    salt = base64.b64encode(os.urandom(32)).decode()
    await _sende(ws, {"hello": {"apiVersion": "0.1",
                 "authentication": {"challenge": challenge, "salt": salt}}}, verschl)
    try:
        roh = await asyncio.wait_for(ws.recv(), timeout=20)
    except Exception:
        print("[Moblin] Keine Antwort auf hello. Tipp: 'verschluesselt' "
              "in config.ini umstellen (true/false).")
        return
    # Empfangs-Modus an dem erkennen, was wirklich ankam (Klartext oder AES):
    m = _dekodieren(roh)
    if isinstance(roh, (bytes, bytearray)):
        try:
            json.loads(roh.decode("utf-8")); verschl = False   # war doch Klartext
        except Exception:
            verschl = True                                     # echtes AES
    else:
        verschl = False
    if not m or "identify" not in m:
        print(f"[Moblin] Erwartete 'identify', bekam: {str(m)[:120]}")
        return
    got = (m["identify"] or {}).get("authentication")
    erwartet = _hash_passwort(challenge, salt, PASSWORT)
    if got != erwartet:
        await _sende(ws, {"identified": {"result": {"wrongPassword": {}}}}, verschl)
        print("[Moblin] Falsches Passwort - in config.ini [moblin] passwort prüfen.")
        return
    await _sende(ws, {"identified": {"result": {"ok": {}}}}, verschl)
    # einmal vollen Status holen ...
    await _sende(ws, {"request": {"id": 1, "data": {"getStatus": {}}}}, verschl)
    # ... und laufende Status-Updates anfordern
    await _sende(ws, {"request": {"id": 2, "data": {"startStatus": {
        "interval": INTERVALL, "filter": {"topRight": True}}}}}, verschl)
    print("[Moblin] Verbunden + angemeldet. Warte auf Status ...")
    try:
        async for roh in ws:
            m = _dekodieren(roh)
            if not isinstance(m, dict):
                continue
            if DEBUG:
                print("[Moblin-DEBUG] empfangen:", list(m.keys()),
                      "->", json.dumps(m)[:300])
            if "ping" in m:
                await _sende(ws, {"pong": {}}, verschl)
                continue
            st = _status_aus_nachricht(m)
            if st:
                _setze(st)
    except Exception as e:
        print(f"[Moblin] Verbindung beendet ({type(e).__name__}). Warte auf neue ...")


async def _server():
    import websockets
    print(f"[Moblin] Assistent-Server läuft auf ws://0.0.0.0:{PORT}  "
          f"(Handy: Assistent-URL = ws://<PC-IP>:{PORT})")
    # ping_interval=None: unser Server soll die Verbindung NICHT selbst kappen,
    # wenn Moblin nicht auf WebSocket-Pings antwortet.
    async with websockets.serve(_handler, "0.0.0.0", PORT, max_size=4_000_000,
                                ping_interval=None, ping_timeout=None):
        await asyncio.Future()


def _thread_main():
    try:
        asyncio.run(_server())
    except Exception as e:
        print(f"[Moblin] Server-Fehler: {e}")


def moblin_start():
    """Startet den Assistent-Server im Hintergrund (vom Waechter aufgerufen)."""
    if not ENABLED:
        return
    if not PASSWORT:
        print("[Moblin] Kein Passwort in config.ini [moblin] -> Anbindung aus.")
        return
    threading.Thread(target=_thread_main, daemon=True).start()


def moblin_werte():
    """Liefert die zuletzt empfangenen Werte (oder None-Werte, wenn nichts da)."""
    frisch = LATEST["zeit"] and (time.time() - LATEST["zeit"] < 120)
    return dict(LATEST) if frisch else {"akku": None, "laedt": None,
                                        "flamme": None, "bitrate": None,
                                        "live": None, "zeit": 0.0}


if __name__ == "__main__":
    if not PASSWORT:
        print("WARNUNG: kein Passwort gesetzt. Lege in config.ini an:\n"
              "[moblin]\nenabled = true\nport = 2345\npasswort = DEIN-MOBLIN-PASSWORT\n"
              "verschluesselt = false\n")
    _thread_main()
