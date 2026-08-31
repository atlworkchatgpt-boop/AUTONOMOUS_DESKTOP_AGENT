import os
import subprocess
import time
import webbrowser
from pathlib import Path
from datetime import datetime

import psutil

from config.config import SCREENSHOT_DIR
from tools.screenshot import take_screenshot

try:
    from tools.web_search import search_web as _search_web
except Exception:
    _search_web = None

try:
    import pyautogui
except Exception:
    pyautogui = None


APP_COMMANDS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "firefox": "firefox.exe",
    "vscode": "code.exe",
    "visual studio code": "code.exe",
    "word": "winword.exe",
    "microsoft word": "winword.exe",
    "excel": "excel.exe",
    "microsoft excel": "excel.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
}


def _approval_ok(value):
    return isinstance(value, dict) and value.get("approved") is True


class ToolRegistry:

    def __init__(self, approval_callback):
        self.approval_callback = approval_callback

        self.functions = {
            "take_screenshot": self.take_screenshot,
            "open_application": self.open_application,
            "open_folder": self.open_folder,
            "list_files": self.list_files,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "type_text": self.type_text,
            "press_key": self.press_key,
            "hotkey": self.hotkey,
            "open_url": self.open_url,
            "search_web": self.search_web,
            "get_current_time": self.get_current_time,
            "run_command": self.run_command,
            "delete_path": self.delete_path,
            "install_software": self.install_software,
            "close_application": self.close_application,
        }

    def schemas(self):
        return TOOL_SCHEMAS

    def execute(self, name, args):
        fn = self.functions.get(name)

        if not fn:
            return {
                "ok": False,
                "error": f"Unknown tool: {name}"
            }

        try:
            return fn(**args)

        except TypeError as exc:
            return {
                "ok": False,
                "error": f"Invalid arguments for {name}: {exc}"
            }

        except Exception as exc:
            return {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}"
            }

    # ========================================================
    # SCREENSHOT
    # ========================================================

    def take_screenshot(self):
        try:
            return take_screenshot()
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # OPEN APPLICATION
    # ========================================================

    def open_application(self, app):

        key = str(app).strip().lower()
        command = APP_COMMANDS.get(key)

        if not command:
            return {
                "ok": False,
                "error": f"Application not in allowlist: {app}"
            }

        try:

            process = subprocess.Popen(
                [command],
                shell=False
            )

            # Give Windows time to create the application window.
            time.sleep(1.5)

            # Try to bring the new application to the foreground.
            if pyautogui is not None:

                try:
                    import pygetwindow as gw

                    wanted = key.lower()

                    windows = gw.getAllWindows()

                    for window in windows:

                        title = (window.title or "").lower()

                        if (
                            wanted in title
                            or (
                                key == "notepad"
                                and "notepad" in title
                            )
                            or (
                                key in ("chrome", "google chrome")
                                and "chrome" in title
                            )
                            or (
                                key in ("edge", "microsoft edge")
                                and "edge" in title
                            )
                            or (
                                key in ("vscode", "visual studio code")
                                and "visual studio code" in title
                            )
                        ):

                            try:
                                if window.isMinimized:
                                    window.restore()

                                window.activate()
                                time.sleep(0.5)
                                break

                            except Exception:
                                pass

                except Exception:
                    # pygetwindow is optional. The application
                    # still launched successfully.
                    pass

            return {
                "ok": True,
                "application": key,
                "pid": process.pid,
                "message": f"{key} opened and focus was requested."
            }

        except FileNotFoundError:
            return {
                "ok": False,
                "error": f"{command} was not found on this computer."
            }

        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # OPEN FOLDER
    # ========================================================

    def open_folder(self, path):

        try:

            p = Path(path).expanduser().resolve()

            if not p.exists() or not p.is_dir():
                return {
                    "ok": False,
                    "error": f"Folder not found: {p}"
                }

            os.startfile(str(p))

            time.sleep(0.7)

            return {
                "ok": True,
                "path": str(p),
                "message": "Folder opened."
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # FILE LIST
    # ========================================================

    def list_files(self, path):

        try:

            p = Path(path).expanduser().resolve()

            if not p.is_dir():
                return {
                    "ok": False,
                    "error": f"Directory not found: {p}"
                }

            items = []

            for item in sorted(
                p.iterdir(),
                key=lambda x: (
                    not x.is_dir(),
                    x.name.lower()
                )
            ):

                items.append({
                    "name": item.name,
                    "type": (
                        "directory"
                        if item.is_dir()
                        else "file"
                    ),
                    "path": str(item)
                })

            return {
                "ok": True,
                "path": str(p),
                "items": items
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # READ FILE
    # ========================================================

    def read_file(self, path):

        try:

            p = Path(path).expanduser().resolve()

            if not p.is_file():
                return {
                    "ok": False,
                    "error": f"File not found: {p}"
                }

            content = p.read_text(
                encoding="utf-8",
                errors="replace"
            )

            return {
                "ok": True,
                "path": str(p),
                "content": content[:30000]
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # WRITE FILE
    # ========================================================

    def write_file(self, path, content):

        target = Path(path).expanduser().resolve()

        approval = self.approval_callback(
            "write",
            str(target)
        )

        if not _approval_ok(approval):

            return {
                "ok": False,
                "cancelled": True,
                "message": "File change was not approved."
            }

        try:

            target.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            target.write_text(
                str(content),
                encoding="utf-8"
            )

            return {
                "ok": True,
                "path": str(target),
                "message": "File updated successfully."
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # TYPE TEXT
    # ========================================================

    def type_text(self, text):

        if pyautogui is None:

            return {
                "ok": False,
                "error": "PyAutoGUI is unavailable."
            }

        value = str(text)

        try:

            # Small delay prevents paste from occurring while
            # Windows is still switching the active window.
            time.sleep(0.7)

            # Clipboard is much more reliable for long essays,
            # newlines and Unicode than pyautogui.write().
            import tkinter as tk

            clip = tk.Tk()
            clip.withdraw()

            clip.clipboard_clear()
            clip.clipboard_append(value)
            clip.update()

            time.sleep(0.25)

            pyautogui.hotkey(
                "ctrl",
                "v"
            )

            time.sleep(
                min(
                    2.0,
                    max(
                        0.2,
                        len(value) / 5000
                    )
                )
            )

            clip.destroy()

            return {
                "ok": True,
                "message": f"Pasted {len(value)} characters into the active application.",
                "characters": len(value)
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # KEY
    # ========================================================

    def press_key(self, key):

        if pyautogui is None:
            return {
                "ok": False,
                "error": "PyAutoGUI is unavailable."
            }

        try:

            pyautogui.press(str(key))

            return {
                "ok": True,
                "message": f"Pressed {key}."
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # HOTKEY
    # ========================================================

    def hotkey(self, keys):

        if pyautogui is None:
            return {
                "ok": False,
                "error": "PyAutoGUI is unavailable."
            }

        if not isinstance(keys, list) or not keys:

            return {
                "ok": False,
                "error": "keys must be a non-empty list."
            }

        try:

            pyautogui.hotkey(
                *[str(k) for k in keys]
            )

            return {
                "ok": True,
                "message": "Hotkey executed."
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # URL
    # ========================================================

    def open_url(self, url):

        value = str(url).strip()

        if not value.startswith(
            ("http://", "https://")
        ):

            return {
                "ok": False,
                "error": "Only http/https URLs are allowed."
            }

        try:

            ok = webbrowser.open(value)

            return {
                "ok": bool(ok),
                "url": value
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # WEB SEARCH
    # ========================================================

    def search_web(
        self,
        query,
        max_results=5
    ):

        if _search_web is None:

            return {
                "ok": False,
                "error": "Web search package is unavailable."
            }

        try:

            return _search_web(
                str(query),
                int(max_results)
            )

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # TIME
    # ========================================================

    def get_current_time(self):

        now = datetime.now().astimezone()

        return {
            "ok": True,
            "datetime": now.isoformat(),
            "timezone": str(now.tzinfo)
        }

    # ========================================================
    # COMMAND
    # ========================================================

    def run_command(self, command):

        text = str(command).strip()
        low = text.lower()

        dangerous = (
            "del ",
            "erase ",
            "rmdir",
            "remove-item",
            "format ",
            "shutdown",
            "restart-computer",
            "taskkill",
            "diskpart",
            "reg delete",
            "reg add",
            "set-executionpolicy",
            "winget install",
            "pip install",
            "python -m pip install"
        )

        if any(x in low for x in dangerous):

            approval = self.approval_callback(
                "command",
                text
            )

            if not _approval_ok(approval):

                return {
                    "ok": False,
                    "cancelled": True,
                    "message": "Command was not approved."
                }

        try:

            cp = subprocess.run(
                text,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                "ok": cp.returncode == 0,
                "exit_code": cp.returncode,
                "output": (
                    (cp.stdout or "")
                    +
                    (cp.stderr or "")
                )[-12000:]
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # DELETE
    # ========================================================

    def delete_path(self, path):

        target = str(
            Path(path).expanduser().resolve()
        )

        approval = self.approval_callback(
            "delete",
            target
        )

        if not _approval_ok(approval):

            return {
                "ok": False,
                "cancelled": True,
                "message": "Deletion was not approved."
            }

        try:

            p = Path(target)

            if not p.exists():

                return {
                    "ok": False,
                    "error": "Target does not exist."
                }

            if p.is_dir():

                import shutil
                shutil.rmtree(p)

            else:

                p.unlink()

            return {
                "ok": True,
                "message": f"Deleted {target}."
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # INSTALL
    # ========================================================

    def install_software(self, command):

        approval = self.approval_callback(
            "install",
            command
        )

        if not _approval_ok(approval):

            return {
                "ok": False,
                "cancelled": True,
                "message": "Installation was not approved."
            }

        try:

            cp = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )

            return {
                "ok": cp.returncode == 0,
                "exit_code": cp.returncode,
                "output": (
                    (cp.stdout or "")
                    +
                    (cp.stderr or "")
                )[-12000:]
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # CLOSE APPLICATION
    # ========================================================

    def close_application(self, process_name):

        approval = self.approval_callback(
            "close",
            process_name
        )

        if not _approval_ok(approval):

            return {
                "ok": False,
                "cancelled": True,
                "message": "Closing was not approved."
            }

        closed = []

        for proc in psutil.process_iter(
            ["pid", "name"]
        ):

            try:

                if (
                    proc.info["name"] or ""
                ).lower() == str(
                    process_name
                ).lower():

                    proc.terminate()
                    closed.append(
                        proc.info["pid"]
                    )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied
            ):

                pass

        return {
            "ok": True,
            "closed": closed
        }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the Windows desktop.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open an allowed Windows application and wait for it to start. Use this BEFORE type_text when the user asks you to open an application and then type something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app": {
                        "type": "string"
                    }
                },
                "required": ["app"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "open_folder",
            "description": "Open a folder in Windows File Explorer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["path"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["path"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file before analyzing or modifying it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["path"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Modify or create a text file. Requires owner approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "content": {
                        "type": "string"
                    }
                },
                "required": [
                    "path",
                    "content"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Paste text into the CURRENTLY FOCUSED Windows application. Use AFTER open_application. Suitable for long essays and multiline text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string"
                    }
                },
                "required": ["text"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press one keyboard key in the active application.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string"
                    }
                },
                "required": ["key"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "hotkey",
            "description": "Press a keyboard shortcut.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["keys"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open an http or https URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
                    }
                },
                "required": ["url"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the live web for current or useful information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    },
                    "max_results": {
                        "type": "integer"
                    }
                },
                "required": ["query"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get current local time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a Windows command. Potentially changing commands require owner approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string"
                    }
                },
                "required": ["command"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "delete_path",
            "description": "Delete a file or folder. Requires owner approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    }
                },
                "required": ["path"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "install_software",
            "description": "Install software. Requires owner approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string"
                    }
                },
                "required": ["command"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Close a Windows process. Requires owner approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_name": {
                        "type": "string"
                    }
                },
                "required": ["process_name"]
            }
        }
    }
]
