#!/usr/bin/env python3
"""
Server-Waechter mit Telegram + lokaler KI
==========================================
Ueberwacht den Streaming-Laptop, meldet Probleme als Telegram-Push, repariert
selbststaendig (Auto-Heal), macht woechentliche Backups und liefert nach jedem
Stream einen Bericht.

Befehle vom Handy:
    /status      -> Gesundheits-Check (CPU, RAM, Temp, OBS, Stream, ...)
    /foto        -> Foto der aktuellen OBS-Szene aufs Handy
    /golive      -> Uebertragung an + Szene LIVE
    /standby     -> Szene 'Start Soon' (Uebertragung an)
    /streamstop  -> Uebertragung beenden
    /ki [Frage]  -> lokale KI analysiert den Zustand
    /aus /neustart /abbrechen -> Server herunterfahren/neustarten/stoppen
    /hilfe       -> Uebersicht

Benoetigt: pip install psutil requests obsws-python
Konfiguration: config.ini (Vorlage: config.example.ini)
"""

import base64
import configparser
import hashlib
import hmac
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Optionaler Moblin-Handy-Status (Akku/Waerme/Bitrate). Fehlt die Datei oder
# das websockets-Modul, laeuft der Waechter normal weiter.
try:
    from moblin_status import moblin_start, moblin_werte
except Exception:
    def moblin_start():
        return None

    def moblin_werte():
        return {"akku": None, "laedt": None, "flamme": None,
                "bitrate": None, "live": None, "zeit": 0.0}

try:
    import psutil
    import requests
except ImportError:
    print("Fehlt: python -m pip install psutil requests obsws-python")
    sys.exit(1)

try:
    import obsws_python as obsws
except ImportError:
    obsws = None  # OBS-Checks werden dann uebersprungen

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
CFG_PATH = Path(__file__).with_name("config.ini")
if not CFG_PATH.exists():
    print(f"config.ini fehlt. Kopiere config.example.ini -> config.ini "
          f"und fuelle sie aus. (Erwartet: {CFG_PATH})")
    sys.exit(1)

cfg = configparser.ConfigParser()
cfg.read(CFG_PATH, encoding="utf-8")

TG_TOKEN = cfg.get("telegram", "token").strip()
TG_CHAT = cfg.get("telegram", "chat_id", fallback="").strip()
TG_API = f"https://api.telegram.org/bot{TG_TOKEN}"

OBS_HOST = cfg.get("obs", "host", fallback="localhost")
OBS_PORT = cfg.getint("obs", "port", fallback=4455)
OBS_PASSWORD = cfg.get("obs", "password", fallback="")
SRT_SOURCE = cfg.get("obs", "srt_source", fallback="Handy SRT")
SCENE_START = cfg.get("obs", "scene_start", fallback="Start Soon")
SCENE_LIVE = cfg.get("obs", "scene_live", fallback="Live")
SCENE_BRB = cfg.get("obs", "scene_brb", fallback="BRB")
SCENE_ENDE = cfg.get("obs", "scene_ende", fallback="Ende")

OLLAMA_URL = cfg.get("ollama", "url", fallback="http://localhost:11434")
OLLAMA_MODEL = cfg.get("ollama", "model", fallback="qwen3:4b")
OLLAMA_ENABLED = cfg.getboolean("ollama", "enabled", fallback=True)
# False = KI rechnet auf der CPU (GPU bleibt frei fuer OBS/NVENC - empfohlen!)
OLLAMA_GPU = cfg.getboolean("ollama", "use_gpu", fallback=False)

TH_CPU = cfg.getint("thresholds", "cpu", fallback=92)
TH_RAM = cfg.getint("thresholds", "ram", fallback=92)
TH_DISK = cfg.getint("thresholds", "disk", fallback=90)
TH_TEMP = cfg.getint("thresholds", "temp", fallback=90)
TH_SKIP = cfg.getfloat("thresholds", "skipped_percent", fallback=5.0)
INTERVAL = cfg.getint("thresholds", "check_interval", fallback=60)
ALERT_COOLDOWN = cfg.getint("thresholds", "alert_cooldown", fallback=900)

# Auto-Heal: abgestuerzte Programme selbst neu starten
AH_ENABLED = cfg.getboolean("autoheal", "enabled", fallback=True)
AH_OBS = cfg.get("autoheal", "obs_pfad",
                 fallback=r"C:\Program Files\obs-studio\bin\64bit\obs64.exe")
AH_BOT = cfg.get("autoheal", "chatbot_bat", fallback="").strip()
# Pfad zur start_goirl.bat -> Waechter startet/ueberwacht go-irl mit
AH_GOIRL_BAT = cfg.get("autoheal", "goirl_bat", fallback="").strip()

# Ruhemodus: OBS/go-irl/Chat-Bot aus, Waechter laeuft weiter
IDLE_DATEI = Path(__file__).with_name("idle.flag")
_idle = IDLE_DATEI.exists()

# Woechentliches Backup auf die grosse Platte
BK_ENABLED = cfg.getboolean("backup", "enabled", fallback=True)
BK_ZIEL = cfg.get("backup", "ziel", fallback=r"D:\Backups")
BK_TAGE = cfg.getint("backup", "intervall_tage", fallback=7)
BK_CHATBOT = cfg.get("backup", "chatbot_ordner", fallback="").strip()

# Handy-Dashboard: kleine Webseite mit Live-Werten, Grafiken und Knoepfen.
# Erreichbar nur aus Heimnetz/Tailscale (FritzBox gibt diesen Port NICHT frei).
DB_ENABLED = cfg.getboolean("dashboard", "enabled", fallback=True)
DB_PORT = cfg.getint("dashboard", "port", fallback=8181)
DB_KEY = cfg.get("dashboard", "key", fallback="").strip()  # leer = ohne Schluessel
# Externer Totmann-Schalter (z.B. healthchecks.io): Waechter pingt regelmaessig;
# bleibt der Ping aus (Laptop eingefroren/aus), alarmiert der Dienst dich per Mail.
HB_URL = cfg.get("heartbeat", "url", fallback="").strip()

# Schlauer Auto-Switcher: schaltet bei zu niedriger Eingangs-Bitrate (Matsch-Bild)
# selbst auf BRB - nicht erst beim Totalausfall. Liest go-irl-Statistik (WebSocket).
SW_ENABLED = cfg.getboolean("switcher", "enabled", fallback=False)
SW_WS = cfg.get("switcher", "ws_url", fallback="ws://127.0.0.1:8888/ws").strip()
SW_MIN_KBIT = cfg.getint("switcher", "min_kbit", fallback=500)
SW_BRB_SEK = cfg.getint("switcher", "brb_sekunden", fallback=4)
SW_LIVE_SEK = cfg.getint("switcher", "live_sekunden", fallback=8)

# Streamer-App (eigene Web-App fuer die Streamerin + Mods, mit Login + Rollen)
# Erreichbar ueber den Cloudflare-Tunnel; eigener Port (NICHT der Technik-Port).
APP_ENABLED = cfg.getboolean("app", "enabled", fallback=False)
APP_PORT = cfg.getint("app", "port", fallback=8182)
APP_SECRET = cfg.get("app", "secret", fallback="").strip()
# Nutzer: "name:passwort:rolle" komma-getrennt; rolle = voll | mod
APP_USERS = {}
for _e in cfg.get("app", "users", fallback="").split(","):
    _t = _e.strip().split(":")
    if len(_t) >= 2 and _t[0].strip():
        APP_USERS[_t[0].strip()] = (_t[1].strip(),
                                    _t[2].strip() if len(_t) >= 3 else "mod")
if APP_ENABLED and not APP_SECRET:
    _sf = Path(__file__).with_name("app_secret.dat")
    try:
        APP_SECRET = _sf.read_text().strip() if _sf.exists() else ""
        if not APP_SECRET:
            APP_SECRET = base64.urlsafe_b64encode(os.urandom(24)).decode()
            _sf.write_text(APP_SECRET)
    except Exception:
        APP_SECRET = base64.urlsafe_b64encode(os.urandom(24)).decode()

# Twitch-Anbindung (Titel/Kategorie setzen, spaeter Raid) via Helix-API
TW_CLIENT_ID = cfg.get("twitch", "client_id", fallback="").strip()
TW_CLIENT_SECRET = cfg.get("twitch", "client_secret", fallback="").strip()
TW_REDIRECT = cfg.get("twitch", "redirect",
                      fallback="https://steuerung.deine-domain.com/oauth/callback").strip()
TW_SCOPE = "channel:manage:broadcast channel:manage:raids clips:edit"
TW_KANAL = cfg.get("twitch", "kanal", fallback="").strip().lstrip("#").lower()
TW_TOKEN_DATEI = Path(__file__).with_name("twitch_token.json")
_tw_access = {"token": "", "exp": 0}

KI_SYSTEM = (
    "WICHTIG: Du antwortest AUSSCHLIESSLICH auf Deutsch, niemals auf Englisch. "
    "Du bist der Wartungs-Assistent eines IRL-Streaming-Laptops (Windows 11, "
    "i7-7700HQ, GTX 1060, 16 GB RAM). Aufbau: Handy (Moblin) sendet per SRT "
    "(UDP-Port ueber FritzBox-Portfreigabe) an OBS; OBS streamt zu Twitch "
    "(NVENC, 720p30). Ein Twitch-Chat-Bot steuert OBS-Szenen via obs-websocket. "
    "Fernzugriff via Tailscale + RustDesk. Antworte auf Deutsch, kurz und fuer "
    "einen Laien verstaendlich: 1) Was ist los? 2) Was tun, Schritt fuer "
    "Schritt? Erfinde nichts; wenn Daten fehlen, sage das."
)

# ---------------------------------------------------------------------------
# Temperaturen
# ---------------------------------------------------------------------------
def gpu_temp():
    """GPU-Temperatur ueber den NVIDIA-Treiber (zuverlaessig)."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=8).stdout.strip()
        if out:
            return int(float(out.splitlines()[0].strip()))
    except Exception:
        pass
    return None


def cpu_temp():
    """CPU-/Gehaeusetemperatur ueber Windows-ACPI (nicht jedes Geraet kann das)."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance -Namespace root/wmi -ClassName "
             "MSAcpi_ThermalZoneTemperature).CurrentTemperature"],
            capture_output=True, text=True, timeout=12).stdout.split()
        if out:
            kelvin10 = float(out[0])          # Zehntel-Kelvin
            grad = kelvin10 / 10.0 - 273.15
            if 5 <= grad <= 120:              # Plausibilitaetscheck
                return round(grad)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Messwerte sammeln
# ---------------------------------------------------------------------------
def obs_client():
    if obsws is None:
        return None
    return obsws.ReqClient(host=OBS_HOST, port=OBS_PORT,
                           password=OBS_PASSWORD, timeout=4)


def _obs_schliessen(cl):
    """Schliesst eine OBS-Verbindung wieder. Wichtig: jeder obs_client()-Aufruf
    macht eine NEUE WebSocket-Verbindung - ohne Schliessen sammeln sie sich an
    (Verbindungs-Leck, sichtbar als viele 'disconnected'-Zeilen im OBS-Log)."""
    if cl is None:
        return
    try:
        cl.disconnect()
    except Exception:
        pass


def obs_running():
    for p in psutil.process_iter(["name"]):
        n = (p.info.get("name") or "").lower()
        if n.startswith("obs64") or n == "obs.exe":
            return True
    return False


def chatbot_running():
    for p in psutil.process_iter(["cmdline"]):
        try:
            cmd = " ".join(p.info.get("cmdline") or [])
        except Exception:
            continue
        if "bot.py" in cmd:
            return True
    return False


def goirl_running():
    for p in psutil.process_iter(["name"]):
        n = (p.info.get("name") or "").lower()
        if n.startswith("go-irl"):
            return True
    return False


def _goirl_cmd():
    """Liest aus der start_goirl.bat die go-irl.exe-Zeile und macht daraus ein
    Startkommando OHNE 45-s-Wartezeit und unabhaengig von der .bat-Zuordnung.
    Gibt (kommando, ordner) zurueck oder (None, None)."""
    if not AH_GOIRL_BAT:
        return None, None
    bat = Path(AH_GOIRL_BAT)
    if not bat.exists():
        return None, None
    for zeile in bat.read_text(encoding="utf-8", errors="ignore").splitlines():
        z = zeile.strip()
        if z.lower().startswith("go-irl") and ".exe" in z.lower():
            return z, bat.parent
    return None, None


def internet_ok(host="1.1.1.1", port=443):
    try:
        s = socket.create_connection((host, port), timeout=4)
        s.close()
        return True
    except OSError:
        return False


def collect_status():
    """Sammelt alle Messwerte in ein Woerterbuch."""
    st = {}
    st["cpu"] = psutil.cpu_percent(interval=1.0)
    st["ram"] = psutil.virtual_memory().percent
    st["disk"] = psutil.disk_usage("C:\\").percent
    st["gpu_temp"] = gpu_temp()
    st["cpu_temp"] = cpu_temp()
    st["internet"] = internet_ok()
    st["obs_offen"] = obs_running()
    st["chatbot"] = chatbot_running()
    st["goirl"] = goirl_running() if AH_GOIRL_BAT else None
    st["stream_aktiv"] = None
    st["reconnect"] = None
    st["skipped_total"] = None
    st["frames_total"] = None
    st["szene"] = None
    st["handy_signal"] = None
    st["bytes_total"] = None

    if st["obs_offen"]:
        cl = None
        try:
            cl = obs_client()
            if cl:
                s = cl.get_stream_status()
                st["stream_aktiv"] = bool(getattr(s, "output_active", False))
                st["reconnect"] = bool(getattr(s, "output_reconnecting", False))
                st["skipped_total"] = getattr(s, "output_skipped_frames", None)
                st["frames_total"] = getattr(s, "output_total_frames", None)
                st["bytes_total"] = getattr(s, "output_bytes", None)
                try:
                    sc = cl.get_current_program_scene()
                    st["szene"] = getattr(sc, "current_program_scene_name", None)
                except Exception:
                    pass
                try:
                    m = cl.get_media_input_status(SRT_SOURCE)
                    state = str(getattr(m, "media_state", ""))
                    st["handy_signal"] = ("PLAYING" in state)
                except Exception:
                    st["handy_signal"] = None
        except Exception:
            pass  # OBS laeuft, aber WebSocket nicht erreichbar
        finally:
            _obs_schliessen(cl)
    # Handy-Signal AUSSCHLIESSLICH aus der go-irl-Bitrate, wenn der Switcher laeuft.
    # (Die OBS-UDP-Quelle meldet sonst faelschlich dauernd "kommt an".)
    if SW_ENABLED:
        frisch = bool(_srt_zeit) and (time.time() - _srt_zeit) < 8
        if frisch and _srt_kbit is not None:
            st["handy_signal"] = _srt_kbit > 30
            st["srt_kbit"] = round(_srt_kbit)
            st["srt_loss"] = round(_srt_loss, 1) if _srt_loss is not None else None
            st["srt_rtt"] = round(_srt_rtt) if _srt_rtt is not None else None
        else:
            st["handy_signal"] = None   # keine go-irl-Daten -> unbekannt, NICHT "kommt an"
            st["srt_kbit"] = st["srt_loss"] = st["srt_rtt"] = None
    else:
        st["srt_kbit"] = st["srt_loss"] = st["srt_rtt"] = None
    return st


def collect_live():
    """Schnelle Live-Werte (ohne die langsame 1s-CPU-Messung) - fuer 5s-Anzeige."""
    st = {"obs_offen": obs_running(), "stream_aktiv": None,
          "reconnect": None, "szene": None, "aufnahme": None, "aufnahme_zeit": ""}
    st["idle"] = _idle
    if st["obs_offen"]:
        cl = None
        try:
            cl = obs_client()
            if cl:
                s = cl.get_stream_status()
                st["stream_aktiv"] = bool(getattr(s, "output_active", False))
                st["reconnect"] = bool(getattr(s, "output_reconnecting", False))
                try:
                    sc = cl.get_current_program_scene()
                    st["szene"] = getattr(sc, "current_program_scene_name", None)
                except Exception:
                    pass
                try:
                    rs = cl.get_record_status()
                    st["aufnahme"] = bool(getattr(rs, "output_active", False))
                    st["aufnahme_zeit"] = getattr(rs, "output_timecode", "") or ""
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            _obs_schliessen(cl)
    if SW_ENABLED and _srt_zeit and (time.time() - _srt_zeit) < 8 and _srt_kbit is not None:
        st["handy_signal"] = _srt_kbit > 30
        st["srt_kbit"] = round(_srt_kbit)
        st["srt_loss"] = round(_srt_loss, 1) if _srt_loss is not None else None
        st["srt_rtt"] = round(_srt_rtt) if _srt_rtt is not None else None
    else:
        st["handy_signal"] = None
        st["srt_kbit"] = st["srt_loss"] = st["srt_rtt"] = None
    # Handy-Status aus Moblin (Akku/Waerme/Bitrate)
    mb = moblin_werte()
    st["hakku"] = mb.get("akku")
    st["hladt"] = mb.get("laedt")
    st["hflamme"] = mb.get("flamme")
    return st


def collect_sys():
    """CPU/RAM/Temperatur/Twitch-Frames frisch auf Abruf (fuer 10/30s-Anzeige)."""
    st = {"cpu": psutil.cpu_percent(interval=0.3),
          "ram": psutil.virtual_memory().percent,
          "cpu_temp": cpu_temp(), "gpu_temp": gpu_temp(), "drop": None}
    if obs_running():
        cl = None
        try:
            cl = obs_client()
            if cl:
                s = cl.get_stream_status()
                if getattr(s, "output_active", False):
                    tot = getattr(s, "output_total_frames", 0) or 0
                    sk = getattr(s, "output_skipped_frames", 0) or 0
                    if tot > 0:
                        st["drop"] = round(100.0 * sk / tot, 1)
        except Exception:
            pass
        finally:
            _obs_schliessen(cl)
    return st


def status_text(st):
    """Macht aus den Messwerten eine lesbare Handy-Nachricht."""
    ok = "✅"; warn = "⚠️"; bad = "❌"; unk = "❓"

    def mark(val, w, b):
        return bad if val >= b else (warn if val >= w else ok)

    z = []
    z.append("📊 Server-Status")
    z.append(f"{mark(st['cpu'], 80, TH_CPU)} CPU: {st['cpu']:.0f} %")
    z.append(f"{mark(st['ram'], 80, TH_RAM)} RAM: {st['ram']:.0f} %")
    z.append(f"{mark(st['disk'], 80, TH_DISK)} Speicher C: {st['disk']:.0f} %")

    temps = []
    if st.get("cpu_temp") is not None:
        temps.append(f"CPU {st['cpu_temp']} °C")
    if st.get("gpu_temp") is not None:
        temps.append(f"GPU {st['gpu_temp']} °C")
    if temps:
        heiss = max(st.get("cpu_temp") or 0, st.get("gpu_temp") or 0)
        z.append(f"{mark(heiss, 80, TH_TEMP)} Temperatur: {', '.join(temps)}")
    else:
        z.append(f"{unk} Temperatur: nicht messbar")

    z.append(f"{ok if st['internet'] else bad} Internet")
    z.append(f"{ok if st['obs_offen'] else bad} OBS "
             f"{'laeuft' if st['obs_offen'] else 'ist ZU'}")
    z.append(f"{ok if st['chatbot'] else warn} Chat-Bot "
             f"{'laeuft' if st['chatbot'] else 'laeuft NICHT'}")
    if st.get("goirl") is not None:
        z.append(f"{ok if st['goirl'] else warn} go-irl "
                 f"{'laeuft' if st['goirl'] else 'laeuft NICHT'}")

    if st["stream_aktiv"] is None:
        z.append(f"{unk} Stream: unbekannt (WebSocket?)")
    elif st["stream_aktiv"]:
        extra = " (RECONNECT!)" if st["reconnect"] else ""
        z.append(f"{warn if st['reconnect'] else ok} Stream: LIVE{extra}")
        if st["frames_total"]:
            q = 100.0 * (st["skipped_total"] or 0) / max(st["frames_total"], 1)
            z.append(f"{warn if q >= TH_SKIP else ok} "
                     f"Verworfene Frames: {q:.1f} %")
        if st["szene"]:
            z.append(f"Szene: {st['szene']}")
        if st["handy_signal"] is True:
            z.append(f"{ok} Handy-Signal kommt an")
        elif st["handy_signal"] is False:
            z.append(f"{bad} KEIN Handy-Signal!")
    else:
        z.append("Stream: aus")
    return "\n".join(z)


# ---------------------------------------------------------------------------
# OBS-Steuerung (Stream + Szenen + Foto)
# ---------------------------------------------------------------------------
def set_scene(name):
    obs_client().set_current_program_scene(name)


def stream_start():
    cl = obs_client()
    try:
        s = cl.get_stream_status()
        if getattr(s, "output_active", False):
            return
    except Exception:
        pass
    cl.start_stream()


def stream_stop():
    """Stoppt die Uebertragung. False = sie war bereits aus."""
    cl = obs_client()
    try:
        st = cl.get_stream_status()
        if not getattr(st, "output_active", False):
            return False
    except Exception:
        pass
    try:
        cl.stop_stream()
    except Exception as e:
        if "501" in str(e):       # OBS: "Output laeuft nicht" -> schon aus
            return False
        raise
    return True


def foto_machen():
    """Screenshot der aktuellen Programm-Szene. Gibt (bytes, szenenname) zurueck."""
    cl = obs_client()
    if cl is None:
        return None, "obsws-python fehlt"
    sc = cl.get_current_program_scene()
    name = getattr(sc, "current_program_scene_name", None)
    if not name:
        return None, "keine aktive Szene"
    try:
        r = cl.get_source_screenshot(name, "jpg", 1280, 720, 80)
    except Exception:
        r = cl.get_source_screenshot(name, "png", 1280, 720, -1)
    data = getattr(r, "image_data", "")
    if "," in data:
        return base64.b64decode(data.split(",", 1)[1]), name
    return None, "kein Bilddaten erhalten"


# ---------------------------------------------------------------------------
# Lokale KI (Ollama)
# ---------------------------------------------------------------------------
def ki_saeubern(text):
    """Entfernt qwen3-Denk-Bloecke und uebrig gebliebenes Selbstgespraech."""
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    t = re.sub(r"</?think>", "", t)           # offene/leere Tags
    # Falls das Modell trotzdem laut nachdenkt: ab dem letzten Denk-Marker abschneiden
    marker = ["Final answer:", "Finale Antwort:", "Zusammenfassung:",
              "Antwort:", "Hier die Zusammenfassung"]
    for m in marker:
        i = t.rfind(m)
        if i != -1:
            t = t[i + len(m):]
            break
    return t.strip()


def ki_antwort(frage, st):
    if not OLLAMA_ENABLED:
        return "KI ist in der config.ini deaktiviert."
    prompt = (f"{KI_SYSTEM}\n\n=== AKTUELLE MESSWERTE ===\n{status_text(st)}\n\n"
              f"=== FRAGE ===\n{frage}\n\n"
              f"Erinnerung: Antworte NUR auf Deutsch! /no_think")
    opts = {"num_predict": 300}      # Antwortlaenge begrenzen (haelt es fix)
    if not OLLAMA_GPU:
        opts["num_gpu"] = 0          # 0 GPU-Schichten = reine CPU-Berechnung
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate",
                          json={"model": OLLAMA_MODEL, "prompt": prompt,
                                "stream": False, "think": False,
                                "keep_alive": "30m", "options": opts},
                          timeout=240)
        r.raise_for_status()
        text = ki_saeubern(r.json().get("response", ""))
        return text or "(leere Antwort der KI)"
    except requests.ConnectionError:
        return ("KI nicht erreichbar. Laeuft Ollama? "
                "(Startmenue -> Ollama, dann nochmal versuchen)")
    except Exception as e:
        return f"KI-Fehler: {e}"


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
# Feste Knoepfe unter dem Telegram-Chat - nie wieder Befehle tippen.
TASTATUR = {"keyboard": [["/status", "/foto"],
                         ["/standby", "/live"],
                         ["/brb", "/streamstop"],
                         ["/ki", "/abbrechen"],
                         ["/hilfe"]],
            "resize_keyboard": True, "is_persistent": True}


def tg_send(chat_id, text, tastatur=False):
    payload = {"chat_id": chat_id, "text": text}
    if tastatur:
        payload["reply_markup"] = TASTATUR
    try:
        r = requests.post(f"{TG_API}/sendMessage", json=payload, timeout=10)
        if not r.ok and tastatur:
            # Telegram mag die Tastatur nicht -> Text trotzdem ohne sie senden
            print(f"[Telegram] Tastatur abgelehnt: {r.text}")
            payload.pop("reply_markup", None)
            requests.post(f"{TG_API}/sendMessage", json=payload, timeout=10)
        elif not r.ok:
            print(f"[Telegram-Sendefehler] {r.text}")
    except Exception as e:
        print(f"[Telegram-Sendefehler] {e}")


def tg_send_photo(chat_id, img_bytes, caption=""):
    try:
        requests.post(f"{TG_API}/sendPhoto",
                      data={"chat_id": chat_id, "caption": caption},
                      files={"photo": ("szene.jpg", img_bytes)}, timeout=30)
    except Exception as e:
        print(f"[Telegram-Foto-Fehler] {e}")


def tg_updates(offset):
    try:
        r = requests.get(f"{TG_API}/getUpdates",
                         params={"timeout": 20, "offset": offset}, timeout=30)
        return r.json().get("result", [])
    except Exception:
        return []


HILFE = ("Befehle:\n"
         "/status - Gesundheits-Check des Servers\n"
         "/foto - Foto der aktuellen OBS-Szene\n"
         "/standby - Uebertragung an + Szene 'Start Soon'\n"
         "/live - auf die Live-Szene (Kamera) schalten\n"
         "/brb - kurze Pause (BRB-Szene)\n"
         "/streamstop - Uebertragung beenden\n"
         "/ki - KI analysiert den aktuellen Zustand\n"
         "/ki <Frage> - Frage mit Server-Kontext an die lokale KI\n"
         "/aus - Server herunterfahren (15 s Countdown)\n"
         "/neustart - Server neu starten\n"
         "/abbrechen - Herunterfahren/Neustart stoppen\n"
         "/logbuch - letzte Ereignisse\n"
         "/hilfe - diese Uebersicht\n\n"
         f"📱 Dashboard im Browser (Tailscale an):\n"
         f"http://DEINE-TAILSCALE-IP:{DB_PORT}/")


def handle_message(chat_id, text):
    global TG_CHAT
    if not TG_CHAT:
        # Erster Kontakt: Absender wird Besitzer dieser Sitzung
        TG_CHAT = str(chat_id)
        tg_send(chat_id, f"Hallo! Deine Chat-ID ist {chat_id}.\n"
                         f"Trage sie in der config.ini bei chat_id ein, damit "
                         f"nur du diesen Waechter steuern kannst.\n\n{HILFE}",
                tastatur=True)
        print(f"[Info] Chat-ID des Absenders: {chat_id} -> in config.ini "
              f"eintragen!")
        return
    if str(chat_id) != TG_CHAT:
        return  # Fremde ignorieren

    low = text.strip().lower()
    if low.startswith("/status"):
        tg_send(chat_id, status_text(collect_status()))
    elif low.startswith("/foto"):
        tg_send(chat_id, "Mache Foto der aktuellen Szene ...")
        try:
            img, info = foto_machen()
            if img:
                tg_send_photo(chat_id, img, f"Szene: {info}")
            else:
                tg_send(chat_id, f"Kein Foto moeglich: {info}")
        except Exception as e:
            tg_send(chat_id, f"Foto-Fehler: {e} (laeuft OBS?)")
    elif low.startswith("/standby"):
        try:
            stream_start()
            set_scene(SCENE_START)
            tg_send(chat_id, "Uebertragung an - Szene 'Start Soon'. "
                             "Wenn bereit: /live")
        except Exception as e:
            tg_send(chat_id, f"Fehler: {e} (laeuft OBS?)")
    elif low.startswith("/live"):
        try:
            stream_start()
            set_scene(SCENE_LIVE)
            tg_send(chat_id, "Auf LIVE (Kamera) geschaltet. 🔴")
        except Exception as e:
            tg_send(chat_id, f"Fehler: {e} (laeuft OBS?)")
    elif low.startswith("/brb"):
        try:
            set_scene(SCENE_BRB)
            tg_send(chat_id, "Kurze Pause - BRB-Szene. Weiter mit /live.")
        except Exception as e:
            tg_send(chat_id, f"Fehler: {e} (laeuft OBS?)")
    elif low.startswith("/streamstop"):
        try:
            if stream_stop():
                tg_send(chat_id, "Uebertragung beendet.")
            else:
                tg_send(chat_id, "Uebertragung war bereits aus.")
        except Exception as e:
            tg_send(chat_id, f"Fehler: {e} (laeuft OBS?)")
    elif low.startswith("/ki"):
        frage = text[3:].strip() or ("Analysiere den Zustand. Gibt es Probleme? "
                                     "Wenn ja: was tun?")
        tg_send(chat_id, "KI denkt nach (CPU-Modus, kann ~30 s dauern) ...")
        tg_send(chat_id, ki_antwort(frage, collect_status()))
    elif low.startswith("/neustart"):
        tg_send(chat_id, "Starte den Server in 15 Sekunden NEU. "
                         "/abbrechen zum Stoppen.")
        subprocess.run(["shutdown", "/r", "/t", "15"])
    elif low.startswith("/aus"):
        tg_send(chat_id, "Fahre den Server in 15 Sekunden HERUNTER. "
                         "/abbrechen zum Stoppen.\n"
                         "Wieder einschalten: FritzBox -> Heimnetz -> "
                         "'Computer starten' (Anleitung 11).")
        subprocess.run(["shutdown", "/s", "/t", "15"])
    elif low.startswith("/abbrechen"):
        subprocess.run(["shutdown", "/a"])
        tg_send(chat_id, "Abgebrochen - der Server bleibt an.")
    elif low.startswith("/logbuch"):
        eintraege = list(LOGBUCH)[-15:]
        if not eintraege:
            tg_send(chat_id, "Logbuch ist noch leer.")
        else:
            txt = "📋 Logbuch (letzte 15):\n" + "\n".join(
                f"{datetime.fromtimestamp(e['zeit']).strftime('%d.%m %H:%M')} {e['text']}"
                for e in eintraege)
            tg_send(chat_id, txt[:3800])
    elif low.startswith("/hilfe") or low.startswith("/start"):
        tg_send(chat_id, HILFE, tastatur=True)


# ---------------------------------------------------------------------------
# Auto-Heal: abgestuerzte Programme selbst neu starten
# ---------------------------------------------------------------------------
_heal_zeit = {}
_down_count = {}       # wie oft ein Programm in Folge "weg" war (gegen Fehlalarm)
_start_zeit = time.time()


def autoheal_versuch(art):
    """Versucht OBS bzw. Chat-Bot neu zu starten. True = Versuch gemacht."""
    if not AH_ENABLED:
        return False
    if time.time() - _start_zeit < 180:
        return False        # Startphase: erst den Autostart machen lassen
    if time.time() - _heal_zeit.get(art, 0) < 600:
        return False        # max. ein Versuch alle 10 Minuten
    _heal_zeit[art] = time.time()
    try:
        if art == "obs" and Path(AH_OBS).exists():
            if obs_running():
                return False        # laeuft doch -> kein zweites OBS (Port-Streit)
            subprocess.Popen([AH_OBS, "--disable-shutdown-check"],
                             cwd=str(Path(AH_OBS).parent))
            return True
        if art == "chatbot" and AH_BOT and Path(AH_BOT).exists():
            if chatbot_running():
                return False        # laeuft doch -> keinen zweiten Bot starten
            os.startfile(AH_BOT)
            return True
        if art == "goirl":
            # Sicherheitsnetz: kurz vor dem Start nochmal pruefen. Laeuft go-irl
            # doch (Fehlalarm), KEIN zweites starten -> sonst Port-Streit.
            if goirl_running():
                return False
            cmd, ordner = _goirl_cmd()
            if cmd:
                # direkt die go-irl.exe-Zeile starten (ohne 45-s-Wartezeit)
                subprocess.Popen(cmd, cwd=str(ordner), shell=True)
                return True
    except Exception as e:
        print(f"[Autoheal-Fehler] {art}: {e}")
    return False


def _prozesse_beenden(pred):
    n = 0
    for pr in psutil.process_iter(["name", "cmdline"]):
        try:
            if pred(pr):
                pr.terminate(); n += 1
        except Exception:
            pass
    return n


def idle_stop_programme():
    nm = lambda pr: (pr.info.get("name") or "").lower()
    cl = lambda pr: " ".join(pr.info.get("cmdline") or []).lower()
    _prozesse_beenden(lambda pr: nm(pr).startswith("obs64") or nm(pr) == "obs.exe")
    _prozesse_beenden(lambda pr: nm(pr).startswith("go-irl"))
    _prozesse_beenden(lambda pr: nm(pr) in ("python.exe", "pythonw.exe")
                      and "bot.py" in cl(pr) and "watchdog.py" not in cl(pr))


def idle_start_programme():
    try:
        if Path(AH_OBS).exists():
            subprocess.Popen([AH_OBS, "--disable-shutdown-check"],
                             cwd=str(Path(AH_OBS).parent))
    except Exception as e:
        print(f"[Wake-OBS] {e}")
    try:
        if AH_BOT and Path(AH_BOT).exists():
            os.startfile(AH_BOT)
    except Exception as e:
        print(f"[Wake-Bot] {e}")
    try:
        cmd, ordner = _goirl_cmd()
        if cmd:
            subprocess.Popen(cmd, cwd=str(ordner), shell=True)
    except Exception as e:
        print(f"[Wake-goirl] {e}")


def idle_setzen(an):
    global _idle
    _idle = bool(an)
    try:
        if an:
            IDLE_DATEI.write_text("1")
        elif IDLE_DATEI.exists():
            IDLE_DATEI.unlink()
    except Exception:
        pass
    if an:
        idle_stop_programme()
        print("[Idle] Ruhemodus an - OBS/go-irl/Chat-Bot gestoppt")
    else:
        try:
            _heal_zeit.clear()
        except Exception:
            pass
        idle_start_programme()
        print("[Idle] Aufgeweckt - starte OBS/go-irl/Chat-Bot")


# ---------------------------------------------------------------------------
# Stream-Sitzung verfolgen (fuer den Abschlussbericht)
# ---------------------------------------------------------------------------
_session = {"aktiv": False, "start": 0.0, "sk0": 0, "fr0": 0,
            "max_temp": 0, "reconnects": 0, "reconnect_war": False,
            "signal_weg": 0, "signal_war_weg": False}


def session_update(st):
    akt = bool(st["stream_aktiv"])
    if akt and not _session["aktiv"]:
        _session.update(aktiv=True, start=time.time(),
                        sk0=st["skipped_total"] or 0,
                        fr0=st["frames_total"] or 0,
                        max_temp=0, reconnects=0, reconnect_war=False,
                        signal_weg=0, signal_war_weg=False)
        if TG_CHAT:
            tg_send(TG_CHAT, "🔴 Stream gestartet - ich passe auf.")
        logbuch("stream", "Stream gestartet")
    if akt:
        heiss = max(st.get("cpu_temp") or 0, st.get("gpu_temp") or 0)
        _session["max_temp"] = max(_session["max_temp"], heiss)
        if st["reconnect"] and not _session["reconnect_war"]:
            _session["reconnects"] += 1
        _session["reconnect_war"] = bool(st["reconnect"])
        weg = st["handy_signal"] is False
        if weg and not _session["signal_war_weg"]:
            _session["signal_weg"] += 1
        _session["signal_war_weg"] = weg
    if not akt and _session["aktiv"]:
        _session["aktiv"] = False
        dauer = max(1, int((time.time() - _session["start"]) / 60))
        sk = (st["skipped_total"] or 0) - _session["sk0"]
        fr = (st["frames_total"] or 0) - _session["fr0"]
        quote = f"{100.0 * sk / fr:.1f} %" if fr > 0 else "unbekannt"
        if TG_CHAT:
            tg_send(TG_CHAT, "📝 Stream-Bericht:\n"
                             f"Dauer: ca. {dauer} Min\n"
                             f"Verworfene Frames: {quote}\n"
                             f"Twitch-Reconnects: {_session['reconnects']}\n"
                             f"Signal-Ausfaelle: {_session['signal_weg']}\n"
                             f"Max. Temperatur: {_session['max_temp']} °C")
        streams_add({"dauer_min": dauer, "drop": quote,
                     "reconnects": _session["reconnects"],
                     "ausfaelle": _session["signal_weg"],
                     "max_temp": _session["max_temp"]})
        logbuch("stream", f"Stream-Ende: {dauer} Min, Drops {quote}, "
                          f"{_session['reconnects']} Reconnects, "
                          f"{_session['signal_weg']} Ausfaelle, max {_session['max_temp']} C")


# ---------------------------------------------------------------------------
# Woechentliches Backup
# ---------------------------------------------------------------------------
def backup_pruefen():
    if not BK_ENABLED:
        return
    try:
        ziel = Path(BK_ZIEL)
        marker = ziel / "letztes_backup.txt"
        if marker.exists():
            try:
                letzte = float(marker.read_text().strip() or 0)
            except ValueError:
                letzte = 0
            if time.time() - letzte < BK_TAGE * 86400:
                return
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        ordner = ziel / f"backup_{stamp}"
        ordner.mkdir(parents=True, exist_ok=True)

        # 1) Waechter-Konfiguration
        shutil.copy2(CFG_PATH, ordner / "watchdog_config.ini")
        # 2) Chat-Bot-Ordner (falls in config.ini angegeben)
        if BK_CHATBOT and Path(BK_CHATBOT).exists():
            shutil.copytree(BK_CHATBOT, ordner / "chatbot", dirs_exist_ok=True)
        # 3) OBS-Szenen und Profile
        obs_basic = Path(os.environ.get("APPDATA", "")) / "obs-studio" / "basic"
        if obs_basic.exists():
            shutil.copytree(obs_basic, ordner / "obs_szenen",
                            dirs_exist_ok=True)

        marker.write_text(str(time.time()))
        print(f"[Backup] erstellt: {ordner}")
        if TG_CHAT:
            tg_send(TG_CHAT, f"💾 Backup erstellt: {ordner}")
    except Exception as e:
        print(f"[Backup-Fehler] {e}")


# ---------------------------------------------------------------------------
# Verlaufs-Daten: ein Messpunkt pro Pruefung (fuer die Dashboard-Grafiken)
# ---------------------------------------------------------------------------
VERLAUF_CSV = Path(__file__).with_name("verlauf.csv")
VERLAUF_MAX = 1440                      # ~24 Stunden bei 60-Sekunden-Takt
_verlauf = deque(maxlen=VERLAUF_MAX)
_vl_alt = {"zeit": 0.0, "bytes": 0, "skipped": 0, "frames": 0}
_last_status = {}
_srt_kbit = None      # zuletzt gemeldete Eingangs-Bitrate von go-irl (kbit/s)
_srt_loss = None      # Paketverlust Handy->OBS in % (aus go-irl)
_srt_rtt = None       # Ping (RTT) Handy->OBS in ms (aus go-irl)
_srt_zeit = 0.0       # wann zuletzt Daten kamen
_srt_lastraw = ""     # letzte Roh-Nachricht von go-irl (Diagnose)
_srt_msgs = 0         # Anzahl empfangener Nachrichten (Diagnose)
_auto_brb = False     # True = der Switcher selbst hat auf BRB geschaltet


def _verlauf_laden():
    """Beim Start alte Punkte zuruecklesen, damit die Grafik nicht leer ist."""
    try:
        if not VERLAUF_CSV.exists():
            return
        zeilen = VERLAUF_CSV.read_text(encoding="utf-8").splitlines()
        for zeile in zeilen[-VERLAUF_MAX:]:
            t = zeile.split(";")
            if len(t) != 8:
                continue
            try:
                _verlauf.append({
                    "zeit": float(t[0]),
                    "cpu": float(t[1]), "ram": float(t[2]),
                    "cpu_temp": float(t[3]) if t[3] else None,
                    "gpu_temp": float(t[4]) if t[4] else None,
                    "drop": float(t[5]) if t[5] else None,
                    "kbit": float(t[6]) if t[6] else None,
                    "live": t[7] == "1"})
            except ValueError:
                continue
    except Exception as e:
        print(f"[Verlauf] Laden fehlgeschlagen: {e}")


def verlauf_punkt(st):
    """Haengt einen Messpunkt an (Arbeitsspeicher + verlauf.csv)."""
    now = time.time()
    drop = kbit = None
    sk = st.get("skipped_total") or 0
    fr = st.get("frames_total") or 0
    by = st.get("bytes_total") or 0
    if st.get("stream_aktiv"):
        d_fr = fr - _vl_alt["frames"]
        d_sk = sk - _vl_alt["skipped"]
        if d_fr > 0:
            drop = max(0.0, round(100.0 * d_sk / d_fr, 2))
        d_t = now - _vl_alt["zeit"]
        d_by = by - _vl_alt["bytes"]
        if 0 < d_t < 600 and d_by >= 0:
            kbit = round(d_by * 8 / 1000 / d_t)
    _vl_alt.update(zeit=now, bytes=by, skipped=sk, frames=fr)
    punkt = {"zeit": now, "cpu": st["cpu"], "ram": st["ram"],
             "cpu_temp": st.get("cpu_temp"), "gpu_temp": st.get("gpu_temp"),
             "drop": drop, "kbit": kbit,
             "live": bool(st.get("stream_aktiv"))}
    _verlauf.append(punkt)
    try:
        def z(x):
            return "" if x is None else f"{x:g}"
        zeile = ";".join([f"{now:.0f}", z(punkt["cpu"]), z(punkt["ram"]),
                          z(punkt["cpu_temp"]), z(punkt["gpu_temp"]),
                          z(punkt["drop"]), z(punkt["kbit"]),
                          "1" if punkt["live"] else "0"])
        with open(VERLAUF_CSV, "a", encoding="utf-8") as fh:
            fh.write(zeile + "\n")
        if VERLAUF_CSV.stat().st_size > 400_000:   # Datei klein halten
            rest = VERLAUF_CSV.read_text(
                encoding="utf-8").splitlines()[-VERLAUF_MAX:]
            VERLAUF_CSV.write_text("\n".join(rest) + "\n", encoding="utf-8")
    except Exception:
        pass


def tendenz_bestimmen():
    """Vergleicht die letzten 5 Minuten mit den 5 davor (Drops + Bitrate).
    Gibt 'besser', 'schlechter', 'stabil' oder None (zu wenig Daten)."""
    pts = [p for p in list(_verlauf)[-20:] if p["live"]]
    if len(pts) < 10:
        return None
    neu, alt = pts[-5:], pts[-10:-5]

    def mittel(arr, k):
        w = [p[k] for p in arr if p[k] is not None]
        return sum(w) / len(w) if w else None

    punkte = 0
    d_neu, d_alt = mittel(neu, "drop"), mittel(alt, "drop")
    if d_neu is not None and d_alt is not None:
        if d_neu < d_alt - 0.3:
            punkte += 1
        elif d_neu > d_alt + 0.3:
            punkte -= 1
    k_neu, k_alt = mittel(neu, "kbit"), mittel(alt, "kbit")
    if k_neu and k_alt:
        if k_neu > k_alt * 1.1:
            punkte += 1
        elif k_neu < k_alt * 0.9:
            punkte -= 1
    return "besser" if punkte > 0 else ("schlechter" if punkte < 0 else "stabil")


# ---------------------------------------------------------------------------
# Automatische Alarme
# ---------------------------------------------------------------------------
_alarm_zeit = {}      # alarmname -> zeitpunkt der letzten meldung
_alarm_aktiv = set()  # aktuell aktive alarme (fuer entwarnung)
_letzte_frames = {"skipped": 0, "total": 0}


def alarm(name, text):
    now = time.time()
    if name in _alarm_aktiv and now - _alarm_zeit.get(name, 0) < ALERT_COOLDOWN:
        return
    _alarm_zeit[name] = now
    _alarm_aktiv.add(name)
    if TG_CHAT:
        tg_send(TG_CHAT, f"⚠️ {text}")
    print(f"[ALARM] {text}")
    logbuch("alarm", text)


def entwarnung(name, text):
    if name in _alarm_aktiv:
        _alarm_aktiv.discard(name)
        if TG_CHAT:
            tg_send(TG_CHAT, f"✅ {text}")
        print(f"[OK] {text}")
        logbuch("ok", text)


def heartbeat_ping():
    if not HB_URL:
        return
    try:
        requests.get(HB_URL, timeout=10)
    except Exception:
        pass


def pruefe_alarme():
    global _last_status
    st = collect_status()
    verlauf_punkt(st)
    session_update(st)
    _last_status = dict(st, zeit=time.time(), tendenz=tendenz_bestimmen())
    _last_status["bitrate_kbit"] = (_verlauf[-1].get("kbit") if _verlauf else None)
    if _session["aktiv"]:
        _last_status["sitzung"] = {
            "start": _session["start"],
            "reconnects": _session["reconnects"],
            "signal_ausfaelle": _session["signal_weg"]}

    if st["cpu"] >= TH_CPU:
        alarm("cpu", f"CPU kritisch: {st['cpu']:.0f} % - Stream kann ruckeln. "
                     f"Tipp: /ki fragen oder unnoetige Programme schliessen.")
    else:
        entwarnung("cpu", "CPU wieder normal.")

    if st["ram"] >= TH_RAM:
        alarm("ram", f"RAM kritisch: {st['ram']:.0f} %.")
    else:
        entwarnung("ram", "RAM wieder normal.")

    if st["disk"] >= TH_DISK:
        alarm("disk", f"Speicher C: fast voll ({st['disk']:.0f} %). Alte "
                      f"Aufnahmen auf D: verschieben/loeschen.")

    heiss = max(st.get("cpu_temp") or 0, st.get("gpu_temp") or 0)
    if heiss >= TH_TEMP:
        alarm("temp", f"TEMPERATUR kritisch: {heiss} °C! Laptop drosselt "
                      f"gleich. Lueftungsschlitze frei? Staub? Geraet kuehler "
                      f"stellen.")
    elif heiss > 0:
        entwarnung("temp", f"Temperatur wieder ok ({heiss} °C).")

    if not st["internet"]:
        alarm("internet", "INTERNET WEG am Server! Router/DSL pruefen.")
    else:
        entwarnung("internet", "Internet wieder da.")

    # Handy (Moblin): Akku niedrig / wird heiss
    mb = moblin_werte()
    akku = mb.get("akku")
    if akku is not None and akku <= 20:
        alarm("hakku", f"📱 Handy-Akku niedrig: {akku}%! Laden nicht vergessen.")
    else:
        entwarnung("hakku", "Handy-Akku wieder ok.")
    if mb.get("flamme") == "kritisch":
        alarm("hflamme", "📱🔥 Handy wird zu HEISS (kritisch)! Pause/abkuehlen.")
    else:
        entwarnung("hflamme", "Handy-Temperatur wieder ok.")

    if not _idle:
        if not st["obs_offen"]:
            # Entprellung: erst nach 2 Fehlchecks in Folge handeln (gegen Fehlalarm
            # + doppeltes OBS). subprocess startet sonst evtl. ein zweites OBS.
            _down_count["obs"] = _down_count.get("obs", 0) + 1
            if _down_count["obs"] >= 2:
                if autoheal_versuch("obs"):
                    alarm("obs", "OBS war ZU - ich habe es automatisch neu gestartet. "
                                 "In 1-2 Min mit /status pruefen.")
                else:
                    alarm("obs", "OBS ist NICHT geoeffnet! Stream unmoeglich. "
                                 "Per RustDesk verbinden und OBS starten.")
        else:
            _down_count["obs"] = 0
            entwarnung("obs", "OBS laeuft wieder.")

        if not st["chatbot"]:
            _down_count["chatbot"] = _down_count.get("chatbot", 0) + 1
            if _down_count["chatbot"] >= 2:
                if autoheal_versuch("chatbot"):
                    alarm("chatbot", "Chat-Bot war aus - ich habe ihn automatisch "
                                     "neu gestartet.")
                else:
                    alarm("chatbot", "Chat-Bot laeuft nicht (start_bot.bat starten) - "
                                     "!start/!live/!stop gehen gerade nicht.")
        else:
            _down_count["chatbot"] = 0
            entwarnung("chatbot", "Chat-Bot laeuft wieder.")

        if AH_GOIRL_BAT:
            if not st["goirl"]:
                # Entprellung: erst nach 2 Fehlchecks in Folge (~2 Min) wirklich
                # heilen. Ein einzelner Aussetzer startet sonst ein zweites go-irl
                # -> Port-Streit -> Schwarzbild.
                _down_count["goirl"] = _down_count.get("goirl", 0) + 1
                if _down_count["goirl"] >= 2:
                    if autoheal_versuch("goirl"):
                        alarm("goirl", "go-irl war aus - automatisch neu gestartet "
                                       "(Bonding/Auto-Switch). In 1 Min /status pruefen.")
                    else:
                        alarm("goirl", "go-irl laeuft NICHT (Bonding/Auto-Switch fehlt). "
                                       "start_goirl starten.")
            else:
                _down_count["goirl"] = 0
                entwarnung("goirl", "go-irl laeuft wieder.")

    if st["stream_aktiv"]:
        if st["reconnect"]:
            alarm("reconnect", "Stream verbindet sich gerade NEU zu Twitch "
                               "(Verbindungsproblem).")
        # Signal-Alarm nur auf der LIVE-Szene: in Start-Soon/BRB ist fehlendes
        # Handybild normal (Intro/Pause) und soll keinen Fehlalarm ausloesen.
        if st["szene"] == SCENE_LIVE and st["handy_signal"] is False:
            alarm("handy", "Kein Signal vom Handy auf der LIVE-Szene! Funkloch "
                           "oder Moblin gestoppt? Auf Pause schalten: im "
                           "Twitch-Chat !brb oder hier /brb tippen.")
        else:
            entwarnung("handy", "Handy-Signal ist wieder da.")

        # Anstieg verworfener Frames seit letzter Pruefung
        sk, to = st["skipped_total"] or 0, st["frames_total"] or 0
        d_sk = sk - _letzte_frames["skipped"]
        d_to = to - _letzte_frames["total"]
        _letzte_frames.update(skipped=sk, total=to)
        if d_to > 0 and 100.0 * d_sk / d_to >= TH_SKIP:
            alarm("frames", f"Verworfene Frames steigen "
                            f"({100.0 * d_sk / d_to:.0f} % aktuell) - Netz zu "
                            f"schwach oder Encoder ueberlastet. /ki fragen!")


# ---------------------------------------------------------------------------
# Handy-Dashboard: Mini-Webserver (nur Heimnetz/Tailscale erreichbar)
# ---------------------------------------------------------------------------
DASH_HTML = Path(__file__).with_name("dashboard.html")


class _DashHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):          # keine Konsolen-Flut
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _erlaubt(self, qs):
        return not DB_KEY or qs.get("key", [""])[0] == DB_KEY

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if not self._erlaubt(qs):
            return self._send(403, '{"fehler":"falscher schluessel"}')
        try:
            if u.path in ("/", "/index.html"):
                return self._send(200, DASH_HTML.read_bytes(),
                                  "text/html; charset=utf-8")
            if u.path == "/api/status":
                return self._send(200, json.dumps(_last_status))
            if u.path == "/api/verlauf":
                return self._send(200, json.dumps(list(_verlauf)))
            if u.path == "/api/foto.jpg":
                img, info = foto_machen()
                if img:
                    return self._send(200, img, "image/jpeg")
                return self._send(503, json.dumps({"fehler": info}))
            return self._send(404, '{"fehler":"unbekannte adresse"}')
        except Exception as e:
            return self._send(500, json.dumps({"fehler": str(e)}))

    def do_POST(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if not self._erlaubt(qs):
            return self._send(403, '{"fehler":"falscher schluessel"}')
        if u.path != "/api/cmd":
            return self._send(404, '{"fehler":"unbekannte adresse"}')
        try:
            n = int(self.headers.get("Content-Length") or 0)
            cmd = json.loads(self.rfile.read(n) or b"{}").get("cmd", "")
            if cmd == "standby":
                stream_start()
                set_scene(SCENE_START)
                info = f"Uebertragung an - Szene '{SCENE_START}'."
            elif cmd == "live":
                stream_start()
                set_scene(SCENE_LIVE)
                info = "Auf LIVE (Kamera) geschaltet. 🔴"
            elif cmd == "brb":
                set_scene(SCENE_BRB)
                info = f"Pause - Szene '{SCENE_BRB}'."
            elif cmd == "streamstop":
                info = ("Uebertragung beendet." if stream_stop()
                        else "Uebertragung war bereits aus.")
            else:
                return self._send(400, '{"fehler":"unbekannter befehl"}')
            if TG_CHAT:
                tg_send(TG_CHAT, f"📱 Vom Dashboard: {info}")
            return self._send(200, json.dumps({"ok": True, "info": info}))
        except Exception as e:
            return self._send(500, json.dumps(
                {"fehler": f"{e} (laeuft OBS?)"}))


def dashboard_start():
    if not DB_ENABLED:
        return
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", DB_PORT), _DashHandler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        print(f"Dashboard an: im Browser http://localhost:{DB_PORT}/ "
              f"(Handy via Tailscale: http://DEINE-TAILSCALE-IP:{DB_PORT}/)")
    except Exception as e:
        print(f"[Dashboard] Start fehlgeschlagen: {e}")


# ---------------------------------------------------------------------------
# Streamer-App: eigener Mini-Webserver mit Login (Benutzer+Passwort) + Rollen
# ---------------------------------------------------------------------------
APP_HTML = Path(__file__).with_name("app.html")
LOGIN_HTML = Path(__file__).with_name("login.html")
OVERLAY_HTML = Path(__file__).with_name("standort-overlay.html")
MANIFEST_JSON = ('{"name":"Stream-Steuerung","short_name":"Stream","start_url":"/",'
                 '"display":"standalone","background_color":"#1e1230",'
                 '"theme_color":"#241430","icons":['
                 '{"src":"/icon-192.png","sizes":"192x192","type":"image/png"},'
                 '{"src":"/icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]}')
ORT_DATEI = Path(__file__).with_name("ort.json")


def ort_laden():
    try:
        return json.loads(ORT_DATEI.read_text(encoding="utf-8")).get("ort", "")
    except Exception:
        return ""


def ort_speichern(ort):
    try:
        ORT_DATEI.write_text(json.dumps({"ort": ort}, ensure_ascii=False),
                             encoding="utf-8")
        return True
    except Exception:
        return False

APP_MOD_ERLAUBT = {"standby", "live", "brb", "ende", "streamstop"}  # Mods duerfen das; "voll" alles

# ---------------------------------------------------------------------------
# Rechte-Verwaltung: Admin schaltet pro Rolle (voll = Streamer, mod) frei,
# was erlaubt ist. "admin" darf immer alles. Gespeichert in rechte.json.
# ---------------------------------------------------------------------------
RECHTE_DATEI = Path(__file__).with_name("rechte.json")
# Knopf-Features (Aktionen) + Bereich-Features (Sektionen, Prefix "sek-")
RECHTE_FEATURES = [
    "standby", "live", "brb", "ende", "stop", "foto", "clip", "raid",
    "aufnahme", "twset", "ort",
    "sek-steuer", "sek-foto", "sek-twchat", "sek-chat", "sek-tw",
    "sek-ort", "sek-verlauf", "sek-log", "sek-hist",
]
DEFAULT_RECHTE = {
    # Streamer (voll): darf standardmaessig alles
    "voll": {k: True for k in RECHTE_FEATURES},
    # Mod: sinnvolle Vorgabe (kein Stream-Ende, kein Raid/Titel/Aufnahme)
    "mod": {
        "standby": True, "live": True, "brb": True, "ende": True, "stop": False,
        "foto": True, "clip": True, "raid": False, "aufnahme": False,
        "twset": False, "ort": True,
        "sek-steuer": True, "sek-foto": True, "sek-twchat": True, "sek-chat": True,
        "sek-tw": False, "sek-ort": True, "sek-verlauf": True, "sek-log": False,
        "sek-hist": False,
    },
}


def rechte_laden():
    """Liest rechte.json und fuellt fehlende Features mit den Defaults auf."""
    daten = {}
    try:
        if RECHTE_DATEI.exists():
            daten = json.loads(RECHTE_DATEI.read_text(encoding="utf-8"))
    except Exception:
        daten = {}
    out = {}
    for rolle in ("voll", "mod"):
        out[rolle] = {}
        gespeichert = daten.get(rolle, {}) if isinstance(daten, dict) else {}
        for f in RECHTE_FEATURES:
            v = gespeichert.get(f)
            out[rolle][f] = bool(v) if v is not None else DEFAULT_RECHTE[rolle][f]
    return out


def rechte_speichern(daten):
    """Speichert nur bekannte Features/Rollen (gegen Muell)."""
    sauber = {}
    for rolle in ("voll", "mod"):
        sauber[rolle] = {}
        quelle = (daten or {}).get(rolle, {})
        for f in RECHTE_FEATURES:
            sauber[rolle][f] = bool(quelle.get(f))
    try:
        RECHTE_DATEI.write_text(json.dumps(sauber, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def darf(rolle, feature):
    """True, wenn die Rolle das Feature nutzen darf. admin = immer alles."""
    if rolle == "admin":
        return True
    if rolle == "voll" and feature not in RECHTE_FEATURES:
        return True
    return bool(rechte_laden().get(rolle, {}).get(feature, False))

# Mod-Chat (in der Steuerungs-App)
APP_CHAT = deque(maxlen=60)
APP_CHAT_DATEI = Path(__file__).with_name("app_chat.json")
try:
    if APP_CHAT_DATEI.exists():
        APP_CHAT.extend(json.loads(APP_CHAT_DATEI.read_text(encoding="utf-8")))
except Exception:
    pass


def app_chat_add(name, text):
    text = (text or "").strip()[:300]
    if not text:
        return
    APP_CHAT.append({"name": name, "text": text, "zeit": int(time.time())})
    try:
        APP_CHAT_DATEI.write_text(json.dumps(list(APP_CHAT)), encoding="utf-8")
    except Exception:
        pass


# --- Logbuch (Ereignisse) + Stream-Historie ---
LOGBUCH_DATEI = Path(__file__).with_name("logbuch.jsonl")
STREAMS_DATEI = Path(__file__).with_name("streams.jsonl")
LOGBUCH = deque(maxlen=500)
try:
    if LOGBUCH_DATEI.exists():
        for _z in LOGBUCH_DATEI.read_text(encoding="utf-8").splitlines()[-500:]:
            try:
                LOGBUCH.append(json.loads(_z))
            except Exception:
                pass
except Exception:
    pass


def logbuch(typ, text):
    e = {"zeit": int(time.time()), "typ": typ, "text": text}
    LOGBUCH.append(e)
    try:
        with open(LOGBUCH_DATEI, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        if LOGBUCH_DATEI.stat().st_size > 600000:
            rest = LOGBUCH_DATEI.read_text(encoding="utf-8").splitlines()[-500:]
            LOGBUCH_DATEI.write_text("\n".join(rest) + "\n", encoding="utf-8")
    except Exception:
        pass


def streams_add(d):
    d = dict(d, zeit=int(time.time()))
    try:
        with open(STREAMS_DATEI, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    except Exception:
        pass


def streams_laden(n=50):
    try:
        zs = STREAMS_DATEI.read_text(encoding="utf-8").splitlines()[-n:]
        return [json.loads(z) for z in zs if z.strip()]
    except Exception:
        return []


def logbuch_ki():
    if not OLLAMA_ENABLED:
        return "KI ist deaktiviert."
    eintraege = list(LOGBUCH)[-60:]
    if not eintraege:
        return "Noch keine Ereignisse im Logbuch."
    zeilen = [f"{datetime.fromtimestamp(e['zeit']).strftime('%d.%m. %H:%M')} "
              f"[{e['typ']}] {e['text']}" for e in eintraege]
    prompt = (KI_SYSTEM + "\n\n=== EREIGNIS-LOGBUCH ===\n" + "\n".join(zeilen) +
              "\n\nFasse auf Deutsch in 3-5 kurzen Saetzen zusammen: Was ist "
              "passiert? Gab es wiederkehrende Probleme? Was sollte der Admin beachten? "
              "Schreibe NUR die fertige deutsche Zusammenfassung, kein Selbstgespraech, "
              "keine englischen Woerter. /no_think")
    opts = {"num_predict": 350}
    if not OLLAMA_GPU:
        opts["num_gpu"] = 0
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate",
                          json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                                "think": False, "keep_alive": "30m", "options": opts}, timeout=240)
        r.raise_for_status()
        return ki_saeubern(r.json().get("response", "")) or "(leere Antwort)"
    except Exception as e:
        return f"KI-Fehler: {e}"


# --- Twitch (Helix) ---
def tw_konfig_ok():
    return bool(TW_CLIENT_ID and TW_CLIENT_SECRET)


def tw_state_laden():
    try:
        return json.loads(TW_TOKEN_DATEI.read_text(encoding="utf-8"))
    except Exception:
        return {}


def tw_state_speichern(d):
    try:
        TW_TOKEN_DATEI.write_text(json.dumps(d), encoding="utf-8")
    except Exception:
        pass


def tw_verbunden():
    return bool(tw_state_laden().get("refresh_token"))


def _tw_state_token():
    return _app_sign("twitch-oauth")[:24]


def tw_access_token():
    st = tw_state_laden()
    rt = st.get("refresh_token")
    if not rt:
        return None
    if _tw_access["token"] and _tw_access["exp"] > time.time() + 30:
        return _tw_access["token"]
    try:
        r = requests.post("https://id.twitch.tv/oauth2/token", data={
            "grant_type": "refresh_token", "refresh_token": rt,
            "client_id": TW_CLIENT_ID, "client_secret": TW_CLIENT_SECRET}, timeout=10)
        if r.status_code != 200:
            return None
        j = r.json()
        _tw_access["token"] = j["access_token"]
        _tw_access["exp"] = time.time() + j.get("expires_in", 3600)
        if j.get("refresh_token"):
            st["refresh_token"] = j["refresh_token"]; tw_state_speichern(st)
        return _tw_access["token"]
    except Exception:
        return None


def _tw_headers():
    t = tw_access_token()
    return {"Client-Id": TW_CLIENT_ID, "Authorization": "Bearer " + t} if t else None


def tw_callback_tausch(code):
    if not code:
        return False, "kein Code"
    try:
        r = requests.post("https://id.twitch.tv/oauth2/token", data={
            "client_id": TW_CLIENT_ID, "client_secret": TW_CLIENT_SECRET, "code": code,
            "grant_type": "authorization_code", "redirect_uri": TW_REDIRECT}, timeout=10)
        if r.status_code != 200:
            return False, f"Token-Tausch fehlgeschlagen ({r.status_code})"
        j = r.json()
        at = j["access_token"]
        u = requests.get("https://api.twitch.tv/helix/users",
                         headers={"Client-Id": TW_CLIENT_ID, "Authorization": "Bearer " + at},
                         timeout=10)
        bid = u.json()["data"][0]["id"]
        tw_state_speichern({"refresh_token": j.get("refresh_token", ""), "broadcaster_id": bid})
        _tw_access["token"] = at
        _tw_access["exp"] = time.time() + j.get("expires_in", 3600)
        return True, "ok"
    except Exception as e:
        return False, str(e)


def tw_channel_info():
    h = _tw_headers(); bid = tw_state_laden().get("broadcaster_id")
    if not h or not bid:
        return None
    try:
        r = requests.get("https://api.twitch.tv/helix/channels",
                         params={"broadcaster_id": bid}, headers=h, timeout=10)
        d = r.json().get("data", [])
        if d:
            return {"title": d[0].get("title", ""), "game_name": d[0].get("game_name", ""),
                    "game_id": d[0].get("game_id", "")}
    except Exception:
        pass
    return None


def tw_search(q):
    h = _tw_headers()
    if not h or not q:
        return []
    try:
        r = requests.get("https://api.twitch.tv/helix/search/categories",
                         params={"query": q, "first": 8}, headers=h, timeout=10)
        return [{"id": g["id"], "name": g["name"]} for g in r.json().get("data", [])]
    except Exception:
        return []


def tw_set(title, game_id):
    h = _tw_headers(); bid = tw_state_laden().get("broadcaster_id")
    if not h or not bid:
        return False, "nicht mit Twitch verbunden"
    body = {}
    if title is not None:
        body["title"] = str(title)[:140]
    if game_id:
        body["game_id"] = str(game_id)
    if not body:
        return False, "nichts zu setzen"
    try:
        r = requests.patch("https://api.twitch.tv/helix/channels",
                           params={"broadcaster_id": bid},
                           headers={**h, "Content-Type": "application/json"},
                           json=body, timeout=10)
        if r.status_code in (200, 204):
            return True, "Titel/Kategorie gesetzt"
        return False, f"Twitch-Fehler {r.status_code}"
    except Exception as e:
        return False, str(e)


def tw_clip():
    h = _tw_headers(); bid = tw_state_laden().get("broadcaster_id")
    if not h or not bid:
        return False, "nicht mit Twitch verbunden"
    try:
        r = requests.post("https://api.twitch.tv/helix/clips",
                          params={"broadcaster_id": bid}, headers=h, timeout=10)
        if r.status_code in (200, 202):
            d = r.json().get("data", [])
            if d:
                return True, (d[0].get("edit_url")
                              or f"https://clips.twitch.tv/{d[0].get('id','')}")
            return True, ""
        if r.status_code == 401:
            return False, "Twitch-Rechte fehlen - bitte neu verbinden (Clip-Recht)"
        if r.status_code == 404:
            return False, "Clip geht nur, solange der Stream LIVE ist"
        return False, f"Twitch-Fehler {r.status_code}"
    except Exception as e:
        return False, str(e)


def tw_raid(ziel):
    h = _tw_headers(); bid = tw_state_laden().get("broadcaster_id")
    if not h or not bid:
        return False, "nicht mit Twitch verbunden"
    ziel = (ziel or "").strip().lstrip("@")
    if not ziel:
        return False, "kein Raid-Ziel angegeben"
    try:
        u = requests.get("https://api.twitch.tv/helix/users",
                         params={"login": ziel}, headers=h, timeout=10)
        d = u.json().get("data", [])
        if not d:
            return False, f"Kanal '{ziel}' nicht gefunden"
        tid = d[0]["id"]
        r = requests.post("https://api.twitch.tv/helix/raids",
                          params={"from_broadcaster_id": bid, "to_broadcaster_id": tid},
                          headers=h, timeout=10)
        if r.status_code == 200:
            return True, f"Raid zu {ziel} gestartet (10 Sek Countdown)"
        if r.status_code == 409:
            return False, "Es laeuft bereits ein Raid"
        if r.status_code == 401:
            return False, "Twitch-Login abgelaufen - bitte neu verbinden"
        return False, f"Twitch-Fehler {r.status_code}"
    except Exception as e:
        return False, str(e)


def _app_sign(msg):
    return hmac.new(APP_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()


def app_cookie_bauen(name, rolle):
    exp = int(time.time()) + 30 * 24 * 3600
    payload = f"{name}|{rolle}|{exp}"
    roh = f"{payload}|{_app_sign(payload)}"
    return base64.urlsafe_b64encode(roh.encode()).decode()


def app_cookie_pruefen(c):
    try:
        roh = base64.urlsafe_b64decode(c.encode()).decode()
        name, rolle, exp, sig = roh.rsplit("|", 3)
        if _app_sign(f"{name}|{rolle}|{exp}") != sig:
            return None
        if int(exp) < time.time():
            return None
        return {"name": name, "rolle": rolle}
    except Exception:
        return None


def pw_pruefen(gespeichert, eingabe):
    """Prueft ein Passwort. Unterstuetzt 'pbkdf2$iter$salt$hash' und
    (uebergangsweise) Klartext, damit Alt-Eintraege weiter funktionieren."""
    try:
        if gespeichert.startswith("pbkdf2$"):
            _, it, salt, h = gespeichert.split("$", 3)
            probe = hashlib.pbkdf2_hmac("sha256", eingabe.encode(),
                                        bytes.fromhex(salt), int(it)).hex()
            return hmac.compare_digest(probe, h)
        return hmac.compare_digest(gespeichert, eingabe)
    except Exception:
        return False


# Security-Header fuer alle App-Antworten. 'unsafe-inline' ist noetig, weil
# app.html Inline-Skripte/onclick nutzt; script/frame nur fuer Chart.js-CDN
# und den Twitch-Chat-Embed.
APP_CSP = ("default-src 'self'; "
           "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
           "style-src 'self' 'unsafe-inline'; "
           "img-src 'self' data: https:; "
           "connect-src 'self'; font-src 'self'; "
           "frame-src https://www.twitch.tv; "
           "base-uri 'self'; form-action 'self'; frame-ancestors 'self'")

# Brute-Force-Bremse fuer /login: pro Client-IP Fehlversuche zaehlen + sperren.
_login_fails = {}            # ip -> [anzahl, sperre_bis_epoch]
_LOGIN_MAX = 5               # ab so vielen Fehlversuchen wird gesperrt
_LOGIN_BASIS = 60            # Basis-Sperre in Sekunden (verdoppelt sich je Fehler)


class _AppHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", cookie=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Content-Security-Policy", APP_CSP)
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _user(self):
        ck = self.headers.get("Cookie", "")
        for teil in ck.split(";"):
            teil = teil.strip()
            if teil.startswith("sess="):
                return app_cookie_pruefen(teil[5:])
        return None

    def _client_ip(self):
        # Hinter Cloudflare steht die echte IP im Header, nicht im lokalen Socket.
        return (self.headers.get("CF-Connecting-IP")
                or self.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                or self.client_address[0])

    def do_GET(self):
        u = urlparse(self.path)
        user = self._user()
        if u.path in ("/", "/index.html"):
            if user:
                return self._send(200, APP_HTML.read_bytes(),
                                  "text/html; charset=utf-8")
            return self._send(200, LOGIN_HTML.read_bytes(),
                              "text/html; charset=utf-8")
        if u.path == "/logout":
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header("Set-Cookie", "sess=; Max-Age=0; Path=/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if u.path == "/overlay":
            return self._send(200, OVERLAY_HTML.read_bytes(),
                              "text/html; charset=utf-8")
        if u.path == "/overlay/ort.json":
            return self._send(200, json.dumps({"ort": ort_laden()}))
        if u.path == "/manifest.json":
            return self._send(200, MANIFEST_JSON,
                              "application/manifest+json; charset=utf-8")
        if u.path in ("/icon-192.png", "/icon-512.png", "/apple-touch-icon.png"):
            try:
                fp = Path(__file__).with_name(u.path.lstrip("/"))
                return self._send(200, fp.read_bytes(), "image/png")
            except Exception:
                return self._send(404, '{"fehler":"icon fehlt"}')
        if not user:
            return self._send(401, '{"fehler":"nicht angemeldet"}')
        try:
            if u.path == "/twitch/login":
                if user["rolle"] not in ("voll", "admin"):
                    return self._send(403, '{"fehler":"nur Streamerin/Admin"}')
                if not tw_konfig_ok():
                    return self._send(400, "Twitch nicht konfiguriert (client_id/secret in config.ini).",
                                      "text/plain; charset=utf-8")
                from urllib.parse import urlencode
                url = "https://id.twitch.tv/oauth2/authorize?" + urlencode({
                    "client_id": TW_CLIENT_ID, "redirect_uri": TW_REDIRECT,
                    "response_type": "code", "scope": TW_SCOPE,
                    "state": _tw_state_token(), "force_verify": "true"})
                self.send_response(302); self.send_header("Location", url); self.end_headers()
                return
            if u.path == "/oauth/callback":
                if user["rolle"] not in ("voll", "admin"):
                    return self._send(403, "nur Streamerin/Admin", "text/plain; charset=utf-8")
                qs = parse_qs(u.query)
                if qs.get("state", [""])[0] != _tw_state_token():
                    return self._send(400, "<meta charset=utf-8>Ungueltiger Zustand (state).",
                                      "text/html; charset=utf-8")
                ok, msg = tw_callback_tausch(qs.get("code", [""])[0])
                html = ("<h2>Twitch verbunden &#9989;</h2><p>Du kannst dieses Fenster "
                        "schliessen und zur App zurueck.</p>" if ok
                        else f"<h2>Fehler</h2><p>{msg}</p>")
                return self._send(200, "<meta charset=utf-8>" + html, "text/html; charset=utf-8")
            if u.path == "/api/twitch/status":
                return self._send(200, json.dumps(
                    {"konfig": tw_konfig_ok(), "verbunden": tw_verbunden()}))
            if u.path == "/api/twitch/info":
                return self._send(200, json.dumps(tw_channel_info() or {}))
            if u.path == "/api/twitch/search":
                return self._send(200, json.dumps(tw_search(parse_qs(u.query).get("q", [""])[0])))
            if u.path == "/api/whoami":
                eff = {f: darf(user["rolle"], f) for f in RECHTE_FEATURES}
                return self._send(200, json.dumps(dict(
                    user, kanal=TW_KANAL,
                    admin=(user["rolle"] == "admin"), rechte=eff)))
            if u.path == "/api/rechte":
                if user["rolle"] != "admin":
                    return self._send(403, '{"fehler":"nur Admin"}')
                return self._send(200, json.dumps(
                    {"features": RECHTE_FEATURES, "rechte": rechte_laden()}))
            if u.path == "/api/status":
                return self._send(200, json.dumps(_last_status))
            if u.path == "/api/szene":
                return self._send(200, json.dumps({"szene": aktuelle_szene()}))
            if u.path == "/api/live":
                return self._send(200, json.dumps(collect_live()))
            if u.path == "/api/sys":
                return self._send(200, json.dumps(collect_sys()))
            if u.path == "/api/srtdebug":
                return self._send(200, json.dumps({
                    "switcher": SW_ENABLED,
                    "kbit": (round(_srt_kbit) if _srt_kbit is not None else None),
                    "loss": _srt_loss, "rtt": _srt_rtt,
                    "alter_s": (round(time.time() - _srt_zeit) if _srt_zeit else None),
                    "nachrichten": _srt_msgs, "roh": _srt_lastraw}))
            if u.path == "/api/verlauf":
                return self._send(200, json.dumps(list(_verlauf)))
            if u.path == "/api/logbuch":
                return self._send(200, json.dumps(list(LOGBUCH)[-200:]))
            if u.path == "/api/streams":
                return self._send(200, json.dumps(streams_laden()))
            if u.path == "/api/logbuch/ki":
                if user["rolle"] not in ("voll", "admin"):
                    return self._send(403, '{"fehler":"nur Streamerin/Admin"}')
                return self._send(200, json.dumps({"text": logbuch_ki()}))
            if u.path == "/api/chat":
                return self._send(200, json.dumps(list(APP_CHAT)))
            if u.path == "/api/ort":
                return self._send(200, json.dumps({"ort": ort_laden()}))
            if u.path == "/api/foto.jpg":
                img, info = foto_machen()
                if img:
                    return self._send(200, img, "image/jpeg")
                return self._send(503, json.dumps({"fehler": info}))
            return self._send(404, '{"fehler":"unbekannte adresse"}')
        except Exception as e:
            return self._send(500, json.dumps({"fehler": str(e)}))

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/login":
            ip = self._client_ip()
            jetzt = time.time()
            vorher = _login_fails.get(ip)
            if vorher and vorher[1] > jetzt:
                wart = int(vorher[1] - jetzt)
                return self._send(429, json.dumps(
                    {"fehler": f"Zu viele Fehlversuche. Bitte {wart}s warten."}))
            n = int(self.headers.get("Content-Length") or 0)
            from urllib.parse import parse_qs as _pq
            form = _pq(self.rfile.read(n).decode("utf-8", "ignore"))
            name = form.get("user", [""])[0].strip()
            pw = form.get("pass", [""])[0]
            eintrag = APP_USERS.get(name)
            if eintrag and pw_pruefen(eintrag[0], pw):
                _login_fails.pop(ip, None)
                logbuch("login", f"Login OK: {name} ({ip})")
                ck = (f"sess={app_cookie_bauen(name, eintrag[1])}; "
                      f"Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=2592000")
                return self._send(200, json.dumps({"ok": True}), cookie=ck)
            # Fehlversuch zaehlen und ab _LOGIN_MAX zeitlich sperren
            cnt = (vorher[0] + 1) if vorher else 1
            if cnt >= _LOGIN_MAX:
                wartesek = min(3600, _LOGIN_BASIS * (2 ** (cnt - _LOGIN_MAX)))
                _login_fails[ip] = [cnt, jetzt + wartesek]
                if cnt == _LOGIN_MAX and TG_CHAT:
                    tg_send(TG_CHAT, f"🔒 App-Login: {cnt} Fehlversuche von {ip} "
                                     f"(Name '{name}') – {int(wartesek)}s gesperrt.")
            else:
                _login_fails[ip] = [cnt, 0]
            if len(_login_fails) > 500:
                _login_fails.clear()
            logbuch("alarm", f"Login FEHLGESCHLAGEN: '{name}' von {ip} (#{cnt})")
            return self._send(401, json.dumps({"fehler": "Falscher Name oder Passwort"}))

        user = self._user()
        if not user:
            return self._send(401, '{"fehler":"nicht angemeldet"}')
        if u.path == "/api/rechte":
            if user["rolle"] != "admin":
                return self._send(403, json.dumps({"fehler": "nur Admin"}))
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(n) or b"{}")
            ok = rechte_speichern(d.get("rechte") or d)
            return self._send(200 if ok else 500, json.dumps({"ok": ok}))
        if u.path == "/api/chat":
            n = int(self.headers.get("Content-Length") or 0)
            text = json.loads(self.rfile.read(n) or b"{}").get("text", "")
            app_chat_add(user["name"], text)
            return self._send(200, json.dumps({"ok": True}))
        if u.path == "/api/ort":
            if not darf(user["rolle"], "ort"):
                return self._send(403, json.dumps({"fehler": "keine Rechte"}))
            n = int(self.headers.get("Content-Length") or 0)
            ort = json.loads(self.rfile.read(n) or b"{}").get("ort", "").strip()[:60]
            ok = ort_speichern(ort)
            return self._send(200 if ok else 500,
                              json.dumps({"ok": ok, "ort": ort}))
        if u.path == "/api/twitch/set":
            if not darf(user["rolle"], "twset"):
                return self._send(403, json.dumps({"fehler": "keine Rechte"}))
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(n) or b"{}")
            ok, msg = tw_set(d.get("title"), d.get("game_id"))
            return self._send(200 if ok else 502,
                              json.dumps({"ok": ok, "info": msg} if ok else {"fehler": msg}))
        if u.path == "/api/twitch/clip":
            if not darf(user["rolle"], "clip"):
                return self._send(403, json.dumps({"fehler": "keine Rechte"}))
            ok, info = tw_clip()
            if ok:
                logbuch("aktion", f"{user['name']}: Clip erstellt")
                app_chat_add("⚙️ Aktion", f"{user['name']}: Clip erstellt")
            return self._send(200 if ok else 502,
                              json.dumps({"ok": ok, "url": info} if ok else {"fehler": info}))
        if u.path == "/api/twitch/raid":
            if not darf(user["rolle"], "raid"):
                return self._send(403, json.dumps({"fehler": "keine Rechte"}))
            n = int(self.headers.get("Content-Length") or 0)
            ziel = json.loads(self.rfile.read(n) or b"{}").get("ziel", "")
            ok, info = tw_raid(ziel)
            if ok:
                logbuch("aktion", f"{user['name']}: Raid -> {ziel}")
                app_chat_add("⚙️ Aktion", f"{user['name']}: Raid zu {ziel}")
            return self._send(200 if ok else 502,
                              json.dumps({"ok": ok, "info": info} if ok else {"fehler": info}))
        if u.path == "/api/idle":
            n = int(self.headers.get("Content-Length") or 0)
            an = json.loads(self.rfile.read(n) or b"{}").get("an")
            if an and user["rolle"] != "admin":
                return self._send(403, json.dumps({"fehler": "Ruhemodus nur Admin"}))
            idle_setzen(bool(an))
            info = "Ruhemodus an" if an else "Aufgeweckt - Programme starten (~30 s)"
            logbuch("idle", f"{user['name']}: {info}")
            app_chat_add("⚙️ Aktion", f"{user['name']}: {info}")
            if TG_CHAT:
                tg_send(TG_CHAT, ("💤 " if an else "☀️ ") + info)
            return self._send(200, json.dumps({"ok": True, "idle": _idle, "info": info}))
        if u.path == "/api/aufnahme":
            if not darf(user["rolle"], "aufnahme"):
                return self._send(403, json.dumps({"fehler": "keine Rechte"}))
            n = int(self.headers.get("Content-Length") or 0)
            an = json.loads(self.rfile.read(n) or b"{}").get("an")
            try:
                cl = obs_client()
                if not cl:
                    return self._send(502, '{"fehler":"OBS nicht erreichbar"}')
                if an:
                    cl.start_record(); info = "Aufnahme gestartet"
                else:
                    cl.stop_record(); info = "Aufnahme gestoppt"
                logbuch("aktion", f"{user['name']}: {info}")
                app_chat_add("⚙️ Aktion", f"{user['name']}: {info}")
                return self._send(200, json.dumps({"ok": True, "info": info}))
            except Exception as e:
                return self._send(502, json.dumps({"fehler": f"{e} (laeuft OBS?)"}))
        if u.path != "/api/cmd":
            return self._send(404, '{"fehler":"unbekannte adresse"}')
        try:
            n = int(self.headers.get("Content-Length") or 0)
            cmd = json.loads(self.rfile.read(n) or b"{}").get("cmd", "")
            _cmdfeat = {"standby": "standby", "live": "live", "brb": "brb",
                        "ende": "ende", "streamstop": "stop"}.get(cmd)
            if _cmdfeat and not darf(user["rolle"], _cmdfeat):
                return self._send(403, json.dumps(
                    {"fehler": "Dafuer fehlen dir die Rechte."}))
            switcher_manuell()   # Hand-Schaltung: Auto-Rueckkehr zu Live aussetzen
            if cmd == "standby":
                stream_start(); set_scene(SCENE_START)
                info = f"Uebertragung an - Szene '{SCENE_START}'."
            elif cmd == "live":
                stream_start(); set_scene(SCENE_LIVE)
                info = "Auf LIVE geschaltet."
            elif cmd == "brb":
                set_scene(SCENE_BRB); info = "Pause."
            elif cmd == "ende":
                set_scene(SCENE_ENDE)
                info = "Ende-Bild (Stream laeuft weiter - Zeit zum Raiden)."
            elif cmd == "streamstop":
                info = ("Uebertragung beendet." if stream_stop()
                        else "Uebertragung war bereits aus.")
            else:
                return self._send(400, '{"fehler":"unbekannter befehl"}')
            logbuch("aktion", f"{user['name']}: {info}")
            app_chat_add("⚙️ Aktion", f"{user['name']}: {info}")
            if TG_CHAT:
                tg_send(TG_CHAT, f"📱 App ({user['name']}): {info}")
            return self._send(200, json.dumps({"ok": True, "info": info}))
        except Exception as e:
            return self._send(500, json.dumps({"fehler": f"{e} (laeuft OBS?)"}))


def app_start():
    if not APP_ENABLED:
        return
    if not APP_USERS:
        print("[App] keine Nutzer in [app] users -> App nicht gestartet.")
        return
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", APP_PORT), _AppHandler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        print(f"Streamer-App an: http://localhost:{APP_PORT}/ "
              f"({len(APP_USERS)} Nutzer) - via Cloudflare-Tunnel erreichbar")
    except Exception as e:
        print(f"[App] Start fehlgeschlagen: {e}")


# ---------------------------------------------------------------------------
# Schlauer Auto-Switcher (Bitrate-Schwelle) - liest go-irl-WebSocket
# ---------------------------------------------------------------------------
def aktuelle_szene():
    cl = None
    try:
        cl = obs_client()
        if not cl:
            return None
        sc = cl.get_current_program_scene()
        return getattr(sc, "current_program_scene_name", None)
    except Exception:
        return None
    finally:
        _obs_schliessen(cl)


def switcher_manuell():
    """Von Hand geschaltet (App/Chat) -> Auto-Rueckkehr zu Live aussetzen."""
    global _auto_brb
    _auto_brb = False


def switcher_ws_reader():
    """Liest dauerhaft die Eingangs-Bitrate aus go-irl (srt-live-reporter)."""
    global _srt_kbit, _srt_zeit, _srt_loss, _srt_rtt, _srt_lastraw, _srt_msgs
    try:
        from websocket import create_connection
    except Exception:
        print("[Switcher] Modul 'websocket-client' fehlt. Bitte einmalig: "
              "pip install websocket-client  -> Switcher bleibt aus.")
        return
    aktiv = False          # True = wir empfangen echte Daten (nur dann loggen)
    while True:
        ws = None
        daten = False      # in DIESER Verbindung ueberhaupt etwas empfangen?
        try:
            ws = create_connection(SW_WS, timeout=10)
            while True:
                roh = ws.recv()
                if not roh:
                    break
                if not daten:
                    daten = True
                    if not aktiv:
                        aktiv = True
                        print(f"[Switcher] mit go-irl verbunden, Daten kommen an ({SW_WS})")
                _srt_lastraw = (roh if isinstance(roh, str) else str(roh))[:700]
                _srt_msgs += 1
                try:
                    d = json.loads(roh)
                except Exception:
                    continue
                if d.get("type") != "reader":
                    continue
                stats = d.get("stats") or {}
                inter = stats.get("Interval") or {}
                inst = stats.get("Instantaneous") or {}
                mbps = inter.get("MbpsRecvRate")
                if mbps is None:
                    mbps = inst.get("MbpsRecvRate")
                if mbps is not None:
                    _srt_kbit = float(mbps) * 1000.0
                    _srt_zeit = time.time()
                # Paketverlust (Handy->OBS) aus den Intervall-Zaehlern berechnen
                pr = inter.get("PktRecv")
                pl = inter.get("PktRecvLoss")
                if pr is not None and pl is not None and (pr + pl) > 0:
                    _srt_loss = 100.0 * float(pl) / float(pr + pl)
                elif inst.get("PktRecvLossRate") is not None:
                    _srt_loss = float(inst.get("PktRecvLossRate"))
                if inst.get("MsRTT") is not None:
                    _srt_rtt = float(inst.get("MsRTT"))
        except Exception:
            _srt_kbit = None
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass
        # Nur EINMAL melden, wenn ein zuvor aktiver Datenstrom abreisst.
        if aktiv and not daten:
            print("[Switcher] go-irl-Datenstrom weg (kein Signal) - warte ...")
            aktiv = False
        # Im Leerlauf (go-irl ohne Stream schliesst die Stats sofort) ruhig und
        # laenger warten -> kein Log-Spam. Bei echtem Stream nur kurze Pause.
        time.sleep(5 if daten else 15)


def switcher_logik():
    """Entscheidet anhand der Bitrate, ob Live<->BRB automatisch geschaltet wird."""
    global _auto_brb
    schlecht_seit = 0.0
    gut_seit = 0.0
    while True:
        time.sleep(1)
        try:
            if not SW_ENABLED or not _last_status.get("stream_aktiv"):
                schlecht_seit = gut_seit = 0.0
                continue
            if _srt_zeit == 0.0:
                continue                      # noch nie Daten -> nichts tun
            now = time.time()
            # Erst nach 30 s ohne frische Daten als "Signal weg" werten. Ein kurzer
            # WebSocket-Schluckauf (go-irl trennt die Stats-Verbindung mal) ist KEIN
            # Signalverlust und darf nicht fälschlich auf BRB schalten.
            veraltet = (now - _srt_zeit) > 30
            kbit = _srt_kbit
            schlecht = veraltet or (kbit is not None and kbit < SW_MIN_KBIT)
            gut = (not veraltet) and (kbit is not None and kbit >= SW_MIN_KBIT * 1.4)
            if schlecht:
                schlecht_seit = schlecht_seit or now
                gut_seit = 0.0
            elif gut:
                gut_seit = gut_seit or now
                schlecht_seit = 0.0
            else:
                schlecht_seit = gut_seit = 0.0
            # Szene NUR abfragen, wenn ein Wechsel wirklich faellig ist. Sonst
            # entsteht jede Sekunde eine neue OBS-Verbindung (Verbindungs-Leck).
            brb_faellig = bool(schlecht_seit) and (now - schlecht_seit >= SW_BRB_SEK)
            live_faellig = (_auto_brb and bool(gut_seit)
                            and now - gut_seit >= SW_LIVE_SEK)
            if not (brb_faellig or live_faellig):
                continue
            szene = aktuelle_szene()
            if (szene == SCENE_LIVE and schlecht_seit
                    and now - schlecht_seit >= SW_BRB_SEK):
                set_scene(SCENE_BRB)
                _auto_brb = True
                schlecht_seit = 0.0
                grund = "kein Signal" if veraltet else f"Bitrate {int(kbit)} kbit/s"
                logbuch("switch", f"Auto -> BRB ({grund})")
                if TG_CHAT:
                    tg_send(TG_CHAT, f"📉 Auto-Switch: schwaches Signal ({grund}) -> BRB")
            elif (szene == SCENE_BRB and _auto_brb and gut_seit
                    and now - gut_seit >= SW_LIVE_SEK):
                set_scene(SCENE_LIVE)
                _auto_brb = False
                gut_seit = 0.0
                logbuch("switch", f"Auto -> Live (Bitrate {int(kbit)} kbit/s)")
                if TG_CHAT:
                    tg_send(TG_CHAT, "📈 Auto-Switch: Signal wieder stabil -> Live")
        except Exception as e:
            print(f"[Switcher] {e}")


# ---------------------------------------------------------------------------
# Hauptschleife
# ---------------------------------------------------------------------------
def main():
    print("Server-Waechter gestartet. Telegram: /hilfe fuer alle Befehle.")
    _verlauf_laden()
    dashboard_start()
    app_start()
    moblin_start()      # Handy-Status (Akku/Waerme/Bitrate) empfangen, falls aktiv
    if SW_ENABLED:
        threading.Thread(target=switcher_ws_reader, daemon=True).start()
        threading.Thread(target=switcher_logik, daemon=True).start()
        print("[Switcher] schlauer Auto-Switch aktiv "
              f"(BRB unter {SW_MIN_KBIT} kbit/s).")
    if TG_CHAT:
        tg_send(TG_CHAT, "🟢 Waechter gestartet und wachsam. "
                         "(Kam diese Meldung unerwartet, hatte er sich "
                         "neu gestartet - alles ok.)")
    if not TG_CHAT:
        print("Noch keine chat_id in config.ini - schreibe dem Bot in Telegram "
              "/start, dann zeigt er dir deine ID.")
    offset = 0
    naechste_pruefung = 0.0
    while True:
        try:
            for upd in tg_updates(offset):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                text = msg.get("text", "")
                chat = (msg.get("chat") or {}).get("id")
                if chat and text:
                    handle_message(chat, text)
            if time.time() >= naechste_pruefung:
                naechste_pruefung = time.time() + INTERVAL
                pruefe_alarme()
                backup_pruefen()
                heartbeat_ping()
        except KeyboardInterrupt:
            print("\nBeendet.")
            return
        except Exception as e:
            print(f"[Fehler] {e} - weiter in 10 s")
            time.sleep(10)


if __name__ == "__main__":
    main()
