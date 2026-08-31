import os
import re
import subprocess
from pathlib import Path


def handle_command(
    text,
    runner,
):

    original = text.strip()
    t = original.lower()

    # ========================================================
    # OPEN APPLICATIONS
    # ========================================================

    apps = {
        "chrome": "start chrome",
        "google chrome": "start chrome",

        "edge": "start msedge",
        "microsoft edge": "start msedge",

        "notepad": "notepad.exe",

        "calculator": "calc.exe",
        "calc": "calc.exe",

        "paint": "mspaint.exe",

        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",

        "vs code": "code",
        "vscode": "code",
        "visual studio code": "code",
    }

    for name, command in apps.items():

        if t in (
            f"open {name}",
            f"launch {name}",
            f"start {name}",
        ):

            result = runner.open_app(
                command
            )

            if result.get(
                "ok",
                False
            ):

                return True, (
                    f"Opened {name.title()}."
                )

            return True, result.get(
                "error",
                result.get(
                    "message",
                    "Could not open application."
                )
            )

    # ========================================================
    # SPECIAL FOLDERS
    # ========================================================

    folders = {
        "downloads": Path.home() / "Downloads",
        "desktop": Path.home() / "Desktop",
        "documents": Path.home() / "Documents",
        "pictures": Path.home() / "Pictures",
        "videos": Path.home() / "Videos",
        "music": Path.home() / "Music",
    }

    for name, path in folders.items():

        if t in (
            f"open {name}",
            f"open my {name}",
            f"show {name}",
            f"show my {name}",
        ):

            result = runner.open_folder(
                str(path)
            )

            return True, result.get(
                "message",
                result.get(
                    "error",
                    "Folder operation finished."
                )
            )

    # ========================================================
    # OPEN URL
    # ========================================================

    match = re.match(
        r"^(open|go to|visit)\s+(https?://\S+)$",
        original,
        re.IGNORECASE,
    )

    if match:

        result = runner.open_url(
            match.group(2)
        )

        return True, result.get(
            "message",
            result.get(
                "error",
                "URL operation finished."
            )
        )

    # ========================================================
    # SCREENSHOT
    # ========================================================

    if t in (
        "screenshot",
        "take screenshot",
        "take a screenshot",
        "capture screen",
        "capture a screenshot",
    ):

        result = runner.screenshot()

        return True, result.get(
            "path",
            result.get(
                "error",
                "Screenshot operation finished."
            )
        )

    # ========================================================
    # SYSTEM INFO
    # ========================================================

    if t in (
        "system info",
        "system information",
        "check my pc",
        "check my computer",
    ):

        result = runner.system_info()

        text = (
            f"OS: {result.get('system')} "
            f"{result.get('release')}\n"
            f"CPU: {result.get('cpu_percent')}%\n"
            f"Memory: {result.get('memory_percent')}%"
        )

        return True, text

    return False, None
