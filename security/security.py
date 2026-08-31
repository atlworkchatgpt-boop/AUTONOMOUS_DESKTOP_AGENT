import os
import json
import hashlib
import getpass
from datetime import datetime

SECURITY_DIR = os.path.abspath("security")
PASSWORD_FILE = os.path.join(SECURITY_DIR, "password.json")
LOG_FILE = os.path.abspath("logs/security.log")


def _hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def setup_password():
    os.makedirs(SECURITY_DIR, exist_ok=True)

    if os.path.exists(PASSWORD_FILE):
        return False

    print()
    print("=" * 60)
    print(" CREATE AUTONOMOUS AI SECURITY PASSWORD")
    print("=" * 60)

    while True:
        p1 = getpass.getpass("Create password: ")
        p2 = getpass.getpass("Confirm password: ")

        if not p1:
            print("Password cannot be empty.")
            continue

        if p1 != p2:
            print("Passwords do not match.")
            continue

        with open(PASSWORD_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "password_hash": _hash(p1)
            }, f)

        print("Security password created.")
        return True


def verify_password():
    if not os.path.exists(PASSWORD_FILE):
        setup_password()

    try:
        with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        password = getpass.getpass("AI SECURITY PASSWORD: ")

        return _hash(password) == data["password_hash"]

    except Exception:
        return False


def require_password(action):
    print()
    print(f"[SECURITY] Password required for: {action}")

    if verify_password():
        log_security(action, True)
        return True

    log_security(action, False)
    print("[SECURITY] ACCESS DENIED")
    return False


def log_security(action, allowed):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().isoformat()} | "
            f"{action} | "
            f"{'ALLOWED' if allowed else 'DENIED'}\n"
        )
