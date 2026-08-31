import os
import re
import subprocess
from pathlib import Path


class CommandRouter:

    def __init__(self, runner):
        self.runner = runner

    def handle(
        self,
        text,
    ):

        original = text.strip()
        t = original.lower()

        # ====================================================
        # OPEN APPS
        # ====================================================

        apps = {
            "chrome": "start chrome",
            "google chrome": "start chrome",
            "edge": "start msedge",
            "microsoft edge": "start msedge",
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "paint": "mspaint.exe",
            "file explorer": "explorer.exe",
            "explorer": "explorer.exe",
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

                result = self.runner.open_app(
                    command
                )

                return True, result

        # ====================================================
        # FOLDERS
        # ====================================================

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

                return True, self.runner.open_folder(
                    str(path)
                )

        # ====================================================
        # OPEN URL
        # ====================================================

        match = re.match(
            r"^(open|go to|visit)\s+(https?://\S+)$",
            original,
            re.IGNORECASE,
        )

        if match:

            return True, self.runner.open_url(
                match.group(2)
            )

        # ====================================================
        # GOOGLE SEARCH
        # ====================================================

        patterns = [
            r"^search google for (.+)$",
            r"^search for (.+)$",
            r"^google (.+)$",
        ]

        for pattern in patterns:

            match = re.match(
                pattern,
                original,
                re.IGNORECASE,
            )

            if match:

                return True, (
                    self.runner.browser_search(
                        match.group(1)
                    )
                )

        # ====================================================
        # SCREENSHOT
        # ====================================================

        if t in (
            "screenshot",
            "take screenshot",
            "take a screenshot",
            "capture screen",
            "capture a screenshot",
        ):

            return True, (
                self.runner.screenshot()
            )

        # ====================================================
        # SYSTEM INFO
        # ====================================================

        if t in (
            "system info",
            "system information",
            "check my pc",
            "check my computer",
        ):

            return True, (
                self.runner.system_info()
            )

        # ====================================================
        # PROCESS LIST
        # ====================================================

        if t in (
            "show running programs",
            "show running processes",
            "list processes",
            "what is running",
        ):

            return True, (
                self.runner.processes()
            )

        # ====================================================
        # CHAT CONTEXT
        # ====================================================

        if (
            "read our chat" in t
            or "read chat context" in t
            or "read the chat context" in t
        ):

            context_path = (
                Path(
                    self.runner.project_dir
                )
                / "data"
                / "chat_context"
                / "chat_context.txt"
            )

            return True, (
                self.runner.read_file(
                    str(context_path)
                )
            )

        return False, None