import os
import sys
import time
import hashlib
import hmac
import subprocess
import shutil
import webbrowser
from pathlib import Path
from getpass import getpass


# ============================================================
# GNG AI SECURITY / COMPUTER CONTROL
# ============================================================

OWNER = "Shreyansh Ray"

STARTUP_PASSWORD = "gngaistart"
ACTION_PASSWORD = "gngai"


# ============================================================
# PASSWORD CHECK
# ============================================================

def verify_password(expected, prompt):

    try:
        supplied = getpass(prompt)
    except Exception:
        supplied = input(prompt)

    return hmac.compare_digest(
        supplied,
        expected
    )


def require_startup_password():

    print()
    print("=" * 55)
    print(" GNG AI — SECURE STARTUP")
    print("=" * 55)

    if not verify_password(
        STARTUP_PASSWORD,
        "Startup password: "
    ):
        print()
        print("ACCESS DENIED.")
        return False

    print("ACCESS GRANTED.")
    return True


def require_action_password(action):

    print()
    print(f"GNG AI wants to: {action}")

    return verify_password(
        ACTION_PASSWORD,
        "Action password: "
    )


# ============================================================
# SAFE PATH HANDLING
# ============================================================

PROJECT_ROOT = Path(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
).resolve()


def safe_path(path):

    p = Path(path).expanduser().resolve()

    try:
        p.relative_to(PROJECT_ROOT)
    except ValueError:
        raise PermissionError(
            "Path is outside the GNG AI project directory."
        )

    return p


# ============================================================
# CONTROLLED COMPUTER ACTIONS
# ============================================================

class ComputerController:

    def __init__(self):

        self.allowed_apps = {

            "notepad": [
                "notepad.exe"
            ],

            "calculator": [
                "calc.exe"
            ],

            "paint": [
                "mspaint.exe"
            ]
        }


    # --------------------------------------------------------
    # OPEN APPLICATION
    # --------------------------------------------------------

    def open_app(self, app):

        app = app.lower().strip()

        if app not in self.allowed_apps:

            raise ValueError(
                "Application is not in the allowed application list."
            )

        if not require_action_password(
            f"open {app}"
        ):
            return "Action cancelled: incorrect password."

        subprocess.Popen(
            self.allowed_apps[app],
            shell=False
        )

        return f"Opened {app}."


    # --------------------------------------------------------
    # OPEN WEBSITE
    # --------------------------------------------------------

    def open_website(self, url):

        if not (
            url.startswith("https://")
            or
            url.startswith("http://")
        ):
            raise ValueError(
                "Only normal HTTP/HTTPS websites are allowed."
            )

        if not require_action_password(
            f"open website {url}"
        ):
            return "Action cancelled: incorrect password."

        webbrowser.open(url)

        return f"Opened {url}."


    # --------------------------------------------------------
    # OPEN PROJECT FILE
    # --------------------------------------------------------

    def open_file(self, path):

        p = safe_path(path)

        if not p.exists():

            return "File does not exist."

        if not require_action_password(
            f"open file {p}"
        ):
            return "Action cancelled: incorrect password."

        os.startfile(str(p))

        return f"Opened {p}."


    # --------------------------------------------------------
    # LIST DIRECTORY
    # --------------------------------------------------------

    def list_directory(self, path="."):

        p = safe_path(path)

        if not p.exists():

            return "Directory does not exist."

        if not p.is_dir():

            return "That path is not a directory."

        items = []

        for item in p.iterdir():

            kind = "DIR " if item.is_dir() else "FILE"

            items.append(
                f"{kind}  {item.name}"
            )

        if not items:

            return "Directory is empty."

        return "\n".join(
            sorted(items)
        )


    # --------------------------------------------------------
    # READ TEXT FILE
    # --------------------------------------------------------

    def read_text_file(self, path):

        p = safe_path(path)

        if not p.exists():

            return "File does not exist."

        if p.stat().st_size > 2_000_000:

            return "File is too large for direct reading."

        allowed = {
            ".txt",
            ".py",
            ".json",
            ".md",
            ".csv",
            ".yaml",
            ".yml",
            ".ini",
            ".xml"
        }

        if p.suffix.lower() not in allowed:

            return "File type is not approved for text reading."

        return p.read_text(
            encoding="utf-8",
            errors="replace"
        )


    # --------------------------------------------------------
    # CREATE DIRECTORY
    # --------------------------------------------------------

    def create_directory(self, path):

        p = safe_path(path)

        if not require_action_password(
            f"create folder {p}"
        ):
            return "Action cancelled: incorrect password."

        p.mkdir(
            parents=True,
            exist_ok=True
        )

        return f"Created folder: {p}"


    # --------------------------------------------------------
    # COPY FILE
    # --------------------------------------------------------

    def copy_file(self, source, destination):

        src = safe_path(source)
        dst = safe_path(destination)

        if not src.exists():

            return "Source does not exist."

        if not require_action_password(
            f"copy {src} to {dst}"
        ):
            return "Action cancelled: incorrect password."

        dst.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copy2(
            src,
            dst
        )

        return f"Copied {src} to {dst}."


    # --------------------------------------------------------
    # DELETE FILE
    # --------------------------------------------------------

    def delete_file(self, path):

        p = safe_path(path)

        if not p.exists():

            return "File does not exist."

        if p.is_dir():

            return (
                "Directory deletion is disabled for safety. "
                "Use the dashboard manually if necessary."
            )

        if not require_action_password(
            f"DELETE file {p}"
        ):
            return "Deletion cancelled: incorrect password."

        p.unlink()

        return f"Deleted file: {p}"


    # --------------------------------------------------------
    # CLOSE CONTROLLED APPLICATION
    # --------------------------------------------------------

    def close_app(self, app):

        app = app.lower().strip()

        allowed_processes = {

            "notepad": "notepad.exe",

            "calculator": "CalculatorApp.exe",

            "paint": "mspaint.exe"
        }

        if app not in allowed_processes:

            raise ValueError(
                "Application is not in the allowed close list."
            )

        if not require_action_password(
            f"close {app}"
        ):
            return "Action cancelled: incorrect password."

        process = allowed_processes[app]

        subprocess.run(
            [
                "taskkill",
                "/IM",
                process,
                "/F"
            ],
            shell=False,
            capture_output=True,
            text=True
        )

        return f"Close request sent for {app}."


# ============================================================
# MARKDOWN CLEANER
# ============================================================

def clean_ai_text(text):

    text = str(text)

    # Remove common Markdown emphasis markers
    text = text.replace("**", "")
    text = text.replace("__", "")

    # Remove accidental Markdown headings
    lines = []

    for line in text.splitlines():

        stripped = line.lstrip()

        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()

        lines.append(stripped)

    text = "\n".join(lines)

    return text.strip()
