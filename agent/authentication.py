import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog


APP_NAME = "Autonomous Desktop AI"

APPDATA = Path(
    os.getenv(
        "APPDATA",
        str(Path.home())
    )
)

SECURITY_DIR = APPDATA / "AutonomousAI"
SECURITY_FILE = SECURITY_DIR / "security.json"

PBKDF2_ITERATIONS = 600000
SALT_BYTES = 32
HASH_BYTES = 32

_prompt_lock = threading.Lock()


def _ensure_directory():
    SECURITY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        str(password).encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=HASH_BYTES
    )


def _load_security():
    try:

        if not SECURITY_FILE.exists():
            return None

        with SECURITY_FILE.open(
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None

        if data.get("version") != 1:
            return None

        if not data.get("salt"):
            return None

        if not data.get("password_hash"):
            return None

        return data

    except Exception:
        return None


def password_exists():
    return _load_security() is not None


def set_password(password):

    password = str(password or "")

    if len(password) < 6:
        raise ValueError(
            "Password must contain at least 6 characters."
        )

    _ensure_directory()

    salt = secrets.token_bytes(
        SALT_BYTES
    )

    password_hash = _hash_password(
        password,
        salt
    )

    data = {
        "version": 1,
        "algorithm": "PBKDF2-HMAC-SHA256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": base64.b64encode(
            salt
        ).decode("ascii"),
        "password_hash": base64.b64encode(
            password_hash
        ).decode("ascii")
    }

    temporary = SECURITY_FILE.with_suffix(
        ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2
        )

    temporary.replace(
        SECURITY_FILE
    )

    return True


def check_action_password(password):

    data = _load_security()

    if not data:
        return False

    try:

        salt = base64.b64decode(
            data["salt"]
        )

        expected = base64.b64decode(
            data["password_hash"]
        )

        actual = _hash_password(
            password,
            salt
        )

        return hmac.compare_digest(
            actual,
            expected
        )

    except Exception:
        return False


def check_startup_password(password):
    return check_action_password(password)


def authenticate_action(password):
    return check_action_password(password)


def authenticate_startup(password):
    return check_startup_password(password)


def _create_password():

    root = tk.Tk()
    root.withdraw()

    try:

        try:
            root.attributes(
                "-topmost",
                True
            )
        except Exception:
            pass

        while True:

            password = simpledialog.askstring(
                APP_NAME,
                "Create your computer-change password.\n\n"
                "This password protects actions that change your computer.\n\n"
                "Minimum 6 characters.",
                parent=root,
                show="*"
            )

            if password is None:
                return False

            password = str(password)

            if len(password) < 6:

                messagebox.showerror(
                    APP_NAME,
                    "Password must contain at least 6 characters.",
                    parent=root
                )

                continue

            confirmation = simpledialog.askstring(
                APP_NAME,
                "Confirm your computer-change password.",
                parent=root,
                show="*"
            )

            if confirmation is None:
                return False

            if password != confirmation:

                messagebox.showerror(
                    APP_NAME,
                    "The passwords do not match.",
                    parent=root
                )

                continue

            set_password(
                password
            )

            messagebox.showinfo(
                APP_NAME,
                "Password created successfully.\n\n"
                "Computer-changing actions are now protected.",
                parent=root
            )

            return True

    finally:

        try:
            root.destroy()
        except Exception:
            pass


def ensure_password():

    if password_exists():
        return True

    return _create_password()


def request_action_password(
    action="Protected computer action"
):

    with _prompt_lock:

        root = tk.Tk()
        root.withdraw()

        try:

            try:
                root.attributes(
                    "-topmost",
                    True
                )
            except Exception:
                pass

            password = simpledialog.askstring(
                APP_NAME,
                "PASSWORD REQUIRED\n\n"
                + str(action),
                parent=root,
                show="*"
            )

            if password is None:
                return False

            if check_action_password(
                password
            ):
                return True

            messagebox.showerror(
                APP_NAME,
                "Incorrect password.\n\n"
                "The computer action was blocked.",
                parent=root
            )

            return False

        finally:

            try:
                root.destroy()
            except Exception:
                pass


def authorize(
    action=None,
    password=None,
    *args,
    **kwargs
):

    if not password_exists():

        if not ensure_password():
            return False

    if password is not None:
        return check_action_password(
            password
        )

    return request_action_password(
        action or "Protected computer action"
    )


def is_owner(value):
    return check_action_password(value)


def require_action_password(value):

    if not check_action_password(value):
        raise PermissionError(
            "Owner authorization required."
        )

    return True


class AuthWindow:

    def __init__(
        self,
        mode="startup"
    ):
        self.mode = mode
        self.result = False

    def show(self):

        if self.mode == "startup":
            self.result = ensure_password()
        else:
            self.result = request_action_password()

        return self.result


PASSWORD = None
SECURITY_PASSWORD = None
OWNER_PASSWORD = None
STARTUP_PASSWORD = None
ACTION_PASSWORD = None
