import os
import time
import subprocess
import shutil

try:
    import pyautogui
except Exception:
    pyautogui = None

from pathlib import Path

from .authentication import authorize


class DesktopExecutor:

    def __init__(self):
        self.last_action = None

    def _approval(self, action):
        return authorize(action)

    def open_application(self, application):

        if not self._approval(
            f"Open application: {application}"
        ):
            return {
                "success": False,
                "error": "Security approval denied."
            }

        aliases = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "vscode": "code.exe"
        }

        executable = aliases.get(
            application.lower().strip(),
            application
        )

        try:

            if shutil.which(executable):
                subprocess.Popen(
                    [executable],
                    shell=False
                )
            else:
                subprocess.Popen(
                    application,
                    shell=True
                )

            time.sleep(1)

            return {
                "success": True,
                "action": "open_application",
                "application": application
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

    def type_text(self, text):

        if pyautogui is None:
            return {
                "success": False,
                "error": "pyautogui is not installed."
            }

        if not self._approval(
            "Type text into the active application"
        ):
            return {
                "success": False,
                "error": "Security approval denied."
            }

        try:

            pyautogui.write(
                text,
                interval=0.002
            )

            return {
                "success": True,
                "action": "type_text",
                "characters": len(text)
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

    def hotkey(self, *keys):

        if pyautogui is None:
            return {
                "success": False,
                "error": "pyautogui is not installed."
            }

        if not self._approval(
            "Keyboard shortcut: " + "+".join(keys)
        ):
            return {
                "success": False,
                "error": "Security approval denied."
            }

        try:

            pyautogui.hotkey(*keys)

            return {
                "success": True,
                "action": "hotkey",
                "keys": list(keys)
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }

    def wait(self, seconds=1):
        time.sleep(max(0, min(seconds, 30)))

        return {
            "success": True,
            "action": "wait"
        }


desktop = DesktopExecutor()
