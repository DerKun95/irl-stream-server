# -*- coding: utf-8 -*-
"""
Setup-Checker fuer den IRL-Streaming-Server.
Prueft, ob in allen Configs und Start-Dateien alles zusammenpasst.
Bedienung: Setup-pruefen.bat doppelklicken  (oder:  python check-setup.py)
Optional, fuer den OBS-Live-Check:  python -m pip install obsws-python
"""
import configparser, os, re, sys
from pathlib import Path

G="\033[92m"; Y="\033[93m"; R="\033[91m"; N="\033[0m"
try:
    os.system("")  # aktiviert Farben in der Windows-Konsole
except Exception:
    pass
zaehler={"ok":0,"warn":0,"bad":0}
def ok(m):   zaehler["ok"]+=1;   print(f"{G}[ OK ]{N} {m}")
def warn(m): zaehler["warn"]+=1; print(f"{Y}[WARN]{N} {m}")
def bad(m):  zaehler["bad"]+=1;  print(f"{R}[FEHLER]{N} {m}")
def titel(t): print(f"\n=== {t} ===")

# ---------------------------------------------------------------------------
# Ordner automatisch finden (Desktop, Downloads, Dokumente, C:\go-irl)
# ---------------------------------------------------------------------------
def finde(marker):
    wurzeln=[Path.home()/"Desktop", Path.home()/"Downloads",
             Path.home()/"Documents", Path("C:/go-irl"), Path.home()]
    gesehen=set()
    for w in wurzeln:
        if not w.exists() or w in gesehen: continue
        gesehen.add(w)
        for root,dirs,files in os.walk(w):
            tiefe=root[len(str(w)):].count(os.sep)
            if tiefe>3: dirs[:]=[]; continue
            if marker in files: return Path(root)
    return None

def lade(pfad):
    cp=configparser.ConfigParser()
    try:
        cp.read(pfad,encoding="utf-8"); return cp,None
    except configparser.Error as e:
        return None,str(e)

print("="*60)
print("  SETUP-CHECK  -  IRL-Streaming-Server")
print("="*60)

chatbot = finde("bot.py")
monitor = finde("watchdog.py")
goirl   = finde("go-irl.exe")

titel("Ordner gefunden")
for name,p in [("Chat-Bot",chatbot),("Waechter/Monitoring",monitor),("go-irl",goirl)]:
    (ok if p else warn)(f"{name}: {p if p else 'NICHT gefunden (Pfad pruefen)'}")

cb_scenes={}; cb_obs_pw=None; wd_scenes={}; wd_obs_pw=None; wd_srtsource=None

# ---------------------------------------------------------------------------
# Chat-Bot config.ini
# ---------------------------------------------------------------------------
titel("Chat-Bot  (config.ini)")
if chatbot:
    cfgp=chatbot/"config.ini"
    if not cfgp.exists():
        bad("config.ini fehlt im Chat-Bot-Ordner (config.example.ini kopieren!)")
    else:
        cp,err=lade(cfgp)
        if err: bad(f"config.ini kann nicht gelesen werden: {err}")
        else:
            bu=cp.get("twitch","bot_username",fallback="").strip()
            tok=cp.get("twitch","oauth_token",fallback="").strip()
            ch=cp.get("twitch","channel",fallback="").strip()
            ok(f"Bot-Account: {bu}") if bu else bad("bot_username fehlt")
            if not tok: bad("oauth_token fehlt")
            elif not tok.startswith("oauth:"): warn("oauth_token sollte mit 'oauth:' beginnen")
            else: ok("oauth_token gesetzt (Format ok)")
            if not ch: bad("channel fehlt")
            elif ch=="DEIN_TEST_KANAL": warn(f"channel = {ch}  (noch Test-Kanal - fuer echt: DEIN_KANAL)")
            else: ok(f"channel = {ch}")
            for s in ("start","live","stop","brb"):
                v=cp.get("scenes",s,fallback="").strip()
                cb_scenes[s]=v
                ok(f"Szene {s} = '{v}'") if v else warn(f"[scenes] {s} fehlt")
            cb_obs_pw=cp.get("obs","password",fallback="").strip()

# ---------------------------------------------------------------------------
# Waechter config.ini
# ---------------------------------------------------------------------------
titel("Waechter  (config.ini)")
if monitor:
    cfgp=monitor/"config.ini"
    if not cfgp.exists():
        bad("config.ini fehlt im Monitoring-Ordner")
    else:
        roh=cfgp.read_text(encoding="utf-8",errors="ignore")
        absn=re.findall(r"^\s*\[([^\]]+)\]",roh,re.M)
        dupl=set(x for x in absn if absn.count(x)>1)
        if dupl: bad(f"Doppelte Abschnitte in der config: {', '.join(sorted(dupl))}  -> jeden nur EINMAL!")
        else: ok("keine doppelten [Abschnitte]")
        cp,err=lade(cfgp)
        if err: bad(f"config.ini kann nicht gelesen werden: {err}")
        else:
            tok=cp.get("telegram","token",fallback="").strip()
            cid=cp.get("telegram","chat_id",fallback="").strip()
            ok("Telegram-Token gesetzt") if tok else bad("Telegram-Token fehlt")
            ok(f"chat_id = {cid}") if cid else warn("chat_id leer (Bot gehorcht sonst jedem) - /start an den Bot senden")
            wd_obs_pw=cp.get("obs","password",fallback="").strip()
            ok("OBS-WebSocket-Passwort gesetzt") if wd_obs_pw else warn("OBS-Passwort leer")
            wd_srtsource=cp.get("obs","srt_source",fallback="").strip()
            ok(f"srt_source = '{wd_srtsource}'") if wd_srtsource else warn("srt_source fehlt")
            for k,s in (("scene_start","start"),("scene_live","live"),("scene_brb","brb")):
                wd_scenes[s]=cp.get("obs",k,fallback="").strip()
            port=cp.get("dashboard","port",fallback="8181").strip()
            ok(f"Dashboard-Port = {port}")
        if not (monitor/"dashboard.html").exists():
            bad("dashboard.html fehlt im Monitoring-Ordner (Dashboard zeigt sonst Fehler)")
        else: ok("dashboard.html vorhanden")

# ---------------------------------------------------------------------------
# Konsistenz zwischen Chat-Bot und Waechter
# ---------------------------------------------------------------------------
titel("Stimmen Chat-Bot und Waechter ueberein?")
if cb_obs_pw is not None and wd_obs_pw is not None:
    if cb_obs_pw==wd_obs_pw and cb_obs_pw: ok("OBS-WebSocket-Passwort in beiden gleich")
    elif not cb_obs_pw or not wd_obs_pw: warn("OBS-Passwort in einer Datei leer - kann nicht vergleichen")
    else: bad("OBS-Passwort in Chat-Bot und Waechter UNTERSCHIEDLICH!")
for s in ("start","live","brb"):
    a=cb_scenes.get(s,""); b=wd_scenes.get(s,"")
    if a and b:
        ok(f"Szene '{s}' identisch: '{a}'") if a==b else bad(f"Szene '{s}' unterschiedlich: Bot '{a}' vs Waechter '{b}'")

# ---------------------------------------------------------------------------
# go-irl Start-Dateien + Passphrase
# ---------------------------------------------------------------------------
titel("go-irl  (Start-Dateien + Passphrase)")
if goirl:
    if (goirl/"go-irl.exe").exists(): ok("go-irl.exe vorhanden")
    bats=[b for b in ("start_goirl.bat","start_goirl_TEST.bat") if (goirl/b).exists()]
    if not bats: warn("keine start_goirl*.bat im go-irl-Ordner gefunden")
    phrasen={}
    for b in bats:
        t=(goirl/b).read_text(encoding="utf-8",errors="ignore")
        if "go-irl-windows.exe" in t: bad(f"{b}: verweist noch auf 'go-irl-windows.exe' - muss 'go-irl.exe' sein")
        if "-srtla-port=" in t: ok(f"{b}: -srtla-port gesetzt")
        else: warn(f"{b}: -srtla-port nicht gefunden")
        m=re.search(r'-passphrase\s+"([^"]*)"',t)
        if m:
            ph=m.group(1); phrasen[b]=ph
            if ph=="DEINE_PASSPHRASE_HIER": bad(f"{b}: Passphrase-Platzhalter noch drin (echte eintragen!)")
            elif len(ph)<10: warn(f"{b}: Passphrase nur {len(ph)} Zeichen (SRT mag 10-79)")
            else: ok(f"{b}: Passphrase gesetzt ({len(ph)} Zeichen)")
        else:
            phrasen[b]=None
            warn(f"{b}: KEINE Passphrase (dann muss Moblin auch OHNE Passphrase senden)")
    werte=set(phrasen.values())
    if len(bats)>1 and len(werte)>1:
        bad("Die beiden Start-Dateien haben UNTERSCHIEDLICHE Passphrasen - gleich machen!")
    elif len(bats)>1:
        ok("Beide Start-Dateien haben dieselbe Passphrase-Einstellung")
    p=list(werte)[0] if werte else None
    if p: print(f"       -> In Moblin EXAKT dieselbe Passphrase eintragen ({len(p)} Zeichen).")
    else: print("       -> In Moblin das Passphrase-Feld LEER lassen.")

# ---------------------------------------------------------------------------
# Optional: Live-Check gegen OBS (wenn OBS laeuft + obsws-python da ist)
# ---------------------------------------------------------------------------
titel("OBS-Live-Check (optional)")
try:
    import obsws_python as obs
    if not wd_obs_pw:
        warn("Kein OBS-Passwort in der Waechter-config - Live-Check uebersprungen")
    else:
        cl=obs.ReqClient(host="localhost",port=4455,password=wd_obs_pw,timeout=4)
        szenen=[s["sceneName"] for s in cl.get_scene_list().scenes]
        ok(f"Mit OBS verbunden. Szenen: {', '.join(szenen)}")
        for s in ("start","live","brb"):
            name=cb_scenes.get(s) or wd_scenes.get(s)
            if name:
                ok(f"Szene '{name}' existiert in OBS") if name in szenen else bad(f"Szene '{name}' fehlt in OBS!")
        if wd_srtsource:
            try:
                inputs=[i["inputName"] for i in cl.get_input_list().inputs]
                ok(f"SRT-Quelle '{wd_srtsource}' existiert in OBS") if wd_srtsource in inputs else bad(f"SRT-Quelle '{wd_srtsource}' fehlt in OBS (Name in config anpassen!)")
            except Exception:
                pass
except ImportError:
    warn("obsws-python nicht installiert - Live-Check uebersprungen (optional: pip install obsws-python)")
except Exception:
    warn("OBS nicht erreichbar (laeuft OBS? WebSocket an?) - Live-Check uebersprungen")

# ---------------------------------------------------------------------------
print("\n"+"="*60)
print(f"  ERGEBNIS:  {G}{zaehler['ok']} ok{N}   {Y}{zaehler['warn']} Warnungen{N}   {R}{zaehler['bad']} Fehler{N}")
if zaehler["bad"]==0 and zaehler["warn"]==0:
    print(f"  {G}Alles passt - bereit zum Streamen!{N}")
elif zaehler["bad"]==0:
    print(f"  {Y}Keine Fehler, nur Hinweise. Schau die [WARN]-Zeilen an.{N}")
else:
    print(f"  {R}Bitte die [FEHLER]-Zeilen oben beheben.{N}")
print("="*60)
