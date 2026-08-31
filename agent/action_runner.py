import shutil
import subprocess
from pathlib import Path

import psutil

from agent.safety import dangerous_command

from tools.basic_tools import (
    launch_app,
    open_folder,
    open_url,
    process_list,
    read_file,
    screenshot,
    search_google,
    system_info,
    type_text,
    write_file,
    press_key,
    hotkey,
    move_mouse,
    click_mouse,
)

try:
    from tools.youtube import YouTubeController
except Exception:
    YouTubeController = None


class ActionRunner:

    def __init__(
        self,
        authentication,
        approval_callback,
    ):

        self.authentication = authentication

        self.approval_callback = (
            approval_callback
        )

        if YouTubeController is not None:
            self.youtube = YouTubeController(
                authentication
            )
        else:
            self.youtube = None

    def _cancelled(
        self,
        message="Operation cancelled.",
    ):

        return {
            "ok": False,
            "cancelled": True,
            "message": message,
        }

    # ========================================================
    # APP
    # ========================================================

    def open_app(
        self,
        command,
    ):

        if not self.authentication.require_action(
            f"Starting program:\n{command}"
        ):
            return self._cancelled()

        try:
            return launch_app(command)
        except Exception as exc:
            return {
                "ok": False,
                "message": str(exc),
            }

    # ========================================================
    # URL
    # ========================================================

    def open_url(
        self,
        url,
    ):

        if not self.authentication.require_action(
            f"Opening browser URL:\n{url}"
        ):
            return self._cancelled()

        try:
            return open_url(url)
        except Exception as exc:
            return {
                "ok": False,
                "message": str(exc),
            }

    # ========================================================
    # GOOGLE
    # ========================================================

    def search_google(
        self,
        query,
    ):

        if not self.authentication.require_action(
            f"Searching Google for:\n{query}"
        ):
            return self._cancelled()

        try:
            return search_google(query)
        except Exception as exc:
            return {
                "ok": False,
                "message": str(exc),
            }

    # ========================================================
    # YOUTUBE
    # ========================================================

    def youtube_channel(
        self,
        channel_name,
    ):

        if self.youtube is None:
            return {
                "ok": False,
                "message": (
                    "YouTube controller is unavailable."
                ),
            }

        return self.youtube.open_channel(
            channel_name
        )

    def youtube_search(
        self,
        query,
    ):

        if self.youtube is None:
            return {
                "ok": False,
                "message": (
                    "YouTube controller is unavailable."
                ),
            }

        return self.youtube.search(
            query
        )

    def youtube_account(
        self,
        account=None,
    ):

        if not self.authentication.require_action(
            (
                "Opening YouTube"
                + (
                    f" using account {account}"
                    if account
                    else ""
                )
            )
        ):
            return self._cancelled()

        try:

            result = open_url(
                "https://www.youtube.com/"
            )

            if account:

                result["message"] = (
                    "YouTube opened.\n"
                    f"Requested account: {account}\n"
                    "The assistant did not sign into "
                    "the account or enter a password."
                )

            return result

        except Exception as exc:

            return {
                "ok": False,
                "message": str(exc),
            }

    # ========================================================
    # FOLDER
    # ========================================================

    def open_folder(
        self,
        path,
    ):

        if not self.authentication.require_action(
            f"Opening folder:\n{path}"
        ):
            return self._cancelled()

        try:
            return open_folder(path)
        except Exception as exc:
            return {
                "ok": False,
                "message": str(exc),
            }

    # ========================================================
    # SCREENSHOT
    # ========================================================

    def screenshot(self):

        try:
            return screenshot()
        except Exception as exc:
            return {
                "ok": False,
                "message": str(exc),
            }

    # ========================================================
    # KEYBOARD
    # ========================================================

    def type_text(
        self,
        text,
    ):

        if not self.authentication.require_action(
            "Typing text."
        ):
            return self._cancelled()

        return type_text(text)

    def press_key(
        self,
        key,
    ):

        if not self.authentication.require_action(
            f"Pressing key: {key}"
        ):
            return self._cancelled()

        return press_key(key)

    def press_hotkey(
        self,
        keys,
    ):

        if not self.authentication.require_action(
            f"Pressing shortcut: {' + '.join(keys)}"
        ):
            return self._cancelled()

        return hotkey(keys)

    # ========================================================
    # MOUSE
    # ========================================================

    def move_mouse(
        self,
        x,
        y,
    ):

        if not self.authentication.require_action(
            f"Moving mouse to {x}, {y}"
        ):
            return self._cancelled()

        return move_mouse(x, y)

    def click_mouse(
        self,
        x=None,
        y=None,
        button="left",
    ):

        if not self.authentication.require_action(
            "Clicking mouse."
        ):
            return self._cancelled()

        return click_mouse(
            x,
            y,
            button,
        )

    # ========================================================
    # FILES
    # ========================================================

    def read_file(
        self,
        path,
    ):

        return read_file(path)

    def write_file(
        self,
        path,
        content,
    ):

        if not self.authentication.require_action(
            f"Changing file:\n{path}"
        ):
            return self._cancelled()

        return write_file(
            path,
            content,
        )

    # ========================================================
    # SYSTEM
    # ========================================================

    def system_info(self):
        return system_info()

    def processes(self):
        return process_list()

    # ========================================================
    # TERMINAL
    # ========================================================

    def terminal(
        self,
        command,
    ):

        if dangerous_command(command):

            return {
                "ok": False,
                "message": (
                    "Command blocked by safety firewall."
                ),
            }

        if not self.authentication.require_action(
            f"Running terminal command:\n{command}"
        ):
            return self._cancelled()

        try:

            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = (
                completed.stdout or ""
            ) + (
                completed.stderr or ""
            )

            return {
                "ok": completed.returncode == 0,
                "message": output[-12000:],
            }

        except Exception as exc:

            return {
                "ok": False,
                "message": str(exc),
            }

    # ========================================================
    # DELETE
    # ========================================================

    def delete(
        self,
        path,
    ):

        if not self.authentication.require_action(
            f"Deleting:\n{path}"
        ):
            return self._cancelled()

        target = (
            Path(path)
            .expanduser()
            .resolve()
        )

        approval = self.approval_callback(
            "DELETE",
            str(target),
        )

        if not approval.get(
            "approved",
            False,
        ):

            return {
                "ok": False,
                "message": "Delete cancelled.",
            }

        try:

            if not target.exists():

                return {
                    "ok": False,
                    "message": f"Not found: {target}",
                }

            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

            return {
                "ok": True,
                "message": f"Deleted: {target}",
            }

        except Exception as exc:

            return {
                "ok": False,
                "message": str(exc),
            }

    # ========================================================
    # INSTALL
    # ========================================================

    def install(
        self,
        command,
    ):

        if not self.authentication.require_action(
            f"Installing:\n{command}"
        ):
            return self._cancelled()

        if dangerous_command(command):

            return {
                "ok": False,
                "message": "Installer command blocked.",
            }

        approval = self.approval_callback(
            "INSTALL",
            command,
        )

        if not approval.get(
            "approved",
            False,
        ):

            return {
                "ok": False,
                "message": "Installation cancelled.",
            }

        try:

            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
            )

            output = (
                completed.stdout or ""
            ) + (
                completed.stderr or ""
            )

            return {
                "ok": completed.returncode == 0,
                "message": output[-12000:],
            }

        except Exception as exc:

            return {
                "ok": False,
                "message": str(exc),
            }

    # ========================================================
    # CLOSE
    # ========================================================

    def close(
        self,
        process_name,
    ):

        if not self.authentication.require_action(
            f"Closing:\n{process_name}"
        ):
            return self._cancelled()

        approval = self.approval_callback(
            "CLOSE",
            process_name,
        )

        if not approval.get(
            "approved",
            False,
        ):

            return {
                "ok": False,
                "message": "Close cancelled.",
            }

        for process in psutil.process_iter(
            ["pid", "name"]
        ):

            try:

                name = process.info["name"]

                if (
                    name
                    and name.lower()
                    == process_name.lower()
                ):

                    process.terminate()

            except Exception:

                continue

        return {
            "ok": True,
            "message": (
                f"Close request sent to {process_name}."
            ),
        }