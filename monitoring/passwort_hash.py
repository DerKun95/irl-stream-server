#!/usr/bin/env python3
"""
Erzeugt einen sicheren Passwort-Hash fuer die config.ini, Abschnitt [app], users.

So gehst du vor:
    1) In diesem Ordner ausfuehren:  python passwort_hash.py
    2) Benutzername, Rolle und Passwort eingeben.
    3) Die ausgegebene Zeile in config.ini bei [app] users eintragen
       (mehrere Nutzer mit Komma trennen), dann watchdog.py neu starten.

Format des Hashes:  pbkdf2$<iterationen>$<salt-hex>$<hash-hex>
Der Server (watchdog.py -> pw_pruefen) erkennt dieses Format automatisch.
Alte Klartext-Passwoerter funktionieren uebergangsweise weiter, sollten aber
nach und nach durch Hashes ersetzt werden.
"""
import hashlib
import os
import getpass

ITERATIONEN = 200_000  # PBKDF2-SHA256; hoeher = langsamer/sicherer


def hash_pw(passwort: str, iterationen: int = ITERATIONEN) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", passwort.encode("utf-8"),
                            salt, iterationen).hex()
    return f"pbkdf2${iterationen}${salt.hex()}${h}"


def main() -> int:
    print("=== Passwort-Hash fuer die Stream-App ===\n")
    name = input("Benutzername: ").strip()
    if not name or ":" in name:
        print("Ungueltiger Name (darf keinen Doppelpunkt enthalten).")
        return 1
    rolle = (input("Rolle (admin / voll / mod) [mod]: ").strip() or "mod").lower()
    if rolle not in ("admin", "voll", "mod"):
        print("Rolle muss admin, voll oder mod sein.")
        return 1
    pw = getpass.getpass("Passwort: ")
    pw2 = getpass.getpass("Passwort wiederholen: ")
    if pw != pw2:
        print("Die Passwoerter stimmen nicht ueberein.")
        return 1
    if len(pw) < 8:
        print("Bitte mindestens 8 Zeichen verwenden.")
        return 1

    zeile = f"{name}:{hash_pw(pw)}:{rolle}"
    print("\n--- Diese Zeile in config.ini bei [app] users eintragen ---")
    print("(mehrere Nutzer mit Komma trennen)\n")
    print(zeile)
    print("\nDanach watchdog.py neu starten. Fertig.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
