import os
import json
import webbrowser
import subprocess
import shutil
from pathlib import Path

from groq import Groq

try:
    import pyautogui
    import pyperclip
except Exception:
    pyautogui = None
    pyperclip = None

try:
    from ddgs import DDGS
except Exception:
    DDGS = None

try:
    from agent.tools_registry import ToolRegistry, TOOL_SCHEMAS
except Exception:
    ToolRegistry = None
    TOOL_SCHEMAS = []


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OWNER_NAME = "Shreyansh Ray"

MODEL = os.environ.get(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

SYSTEM_PROMPT = f"""
You are the autonomous desktop AI owned by {OWNER_NAME}.

You are connected to real Windows computer tools.

IMPORTANT:

- Do not expose chain-of-thought or hidden reasoning.
- Never pretend that an action happened.
- When the user asks you to perform a computer action, actually call
  the appropriate tool.
- After a tool call, inspect its result.
- For multi-step tasks, continue until the requested task is complete.
- If something fails, report the actual failure.
- Do not stop after merely saying that you will do something.
- For current information, use web_search.
- For files, actually read/create/modify files using tools.
- For applications, actually launch them.
- For typing, actually send the text to the focused application.
- For destructive or sensitive operations, respect the application's
  approval callback.
- Do not expose tool JSON.
- Do not expose private reasoning.
- Answer in the user's language where practical.

Examples:

User: "Open Notepad and type an essay about space."

Correct behavior:
1. Open Notepad.
2. Verify the launch result.
3. Type the requested essay.
4. Report what actually happened.

User: "Read my Python file and fix the bug."

Correct behavior:
1. Read the file.
2. Analyze it.
3. Modify it.
4. Report the actual file change.

Do not simply give instructions when the user asked you to perform
the action.
"""


class UltimateGroqAgent:

    def __init__(self, registry=None):

        key = os.environ.get("GROQ_API_KEY")

        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is missing."
            )

        self.client = Groq(api_key=key)
        self.registry = registry

        self.local_tools = {
            "open_application": self.open_application,
            "open_folder": self.open_folder,
            "read_file": self.read_file,
            "create_file": self.create_file,
            "edit_file": self.edit_file,
            "type_text": self.type_text,
            "open_url": self.open_url,
            "web_search": self.web_search,
            "take_screenshot": self.take_screenshot,
            "run_command": self.run_command,
        }

        self.schemas = self.make_schemas()

    # ========================================================
    # TOOL SCHEMAS
    # ========================================================

    def make_schemas(self):

        schemas = [
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description":
                        "Open a Windows application such as Notepad, Chrome, Edge, VS Code, Calculator, Paint, Word or Excel.",
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
                    "name": "open_folder",
                    "description":
                        "Open a folder in Windows File Explorer.",
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
                    "description":
                        "Read a text file.",
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
                    "name": "create_file",
                    "description":
                        "Create a text file.",
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
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description":
                        "Replace specific text in an existing text file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string"
                            },
                            "old_text": {
                                "type": "string"
                            },
                            "new_text": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "path",
                            "old_text",
                            "new_text"
                        ]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "type_text",
                    "description":
                        "Type/paste text into the currently focused Windows application.",
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
                    "name": "open_url",
                    "description":
                        "Open a URL in the default browser.",
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
                    "name": "web_search",
                    "description":
                        "Search the web for current information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_screenshot",
                    "description":
                        "Take a screenshot of the desktop.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description":
                        "Run a non-destructive Windows command.",
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
            }
        ]

        return schemas

    # ========================================================
    # REGISTRY BRIDGE
    # ========================================================

    def registry_call(self, name, arguments):

        if self.registry is None:
            return None

        fn = getattr(
            self.registry,
            "functions",
            {}
        ).get(name)

        if fn is None:
            return None

        try:
            return fn(**arguments)
        except TypeError:
            return fn(*arguments.values())

    # ========================================================
    # APPLICATION
    # ========================================================

    def open_application(self, command):

        result = self.registry_call(
            "open_application",
            {"command": command}
        )

        if result is not None:
            return result

        try:
            subprocess.Popen(
                command,
                shell=True
            )

            return {
                "ok": True,
                "message":
                    f"Started {command}"
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # FOLDER
    # ========================================================

    def open_folder(self, path):

        result = self.registry_call(
            "open_folder",
            {"path": path}
        )

        if result is not None:
            return result

        try:

            p = Path(path).expanduser().resolve()

            if not p.exists():

                return {
                    "ok": False,
                    "error":
                        f"Folder does not exist: {p}"
                }

            os.startfile(str(p))

            return {
                "ok": True,
                "path": str(p)
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # READ
    # ========================================================

    def read_file(self, path):

        result = self.registry_call(
            "read_file",
            {"path": path}
        )

        if result is not None:
            return result

        try:

            p = Path(path).expanduser().resolve()

            text = p.read_text(
                encoding="utf-8",
                errors="replace"
            )

            return {
                "ok": True,
                "path": str(p),
                "content": text[:50000]
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # CREATE
    # ========================================================

    def create_file(self, path, content):

        result = self.registry_call(
            "create_file",
            {
                "path": path,
                "content": content
            }
        )

        if result is not None:
            return result

        try:

            p = Path(path).expanduser().resolve()

            p.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            p.write_text(
                content,
                encoding="utf-8"
            )

            return {
                "ok": True,
                "path": str(p)
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # EDIT
    # ========================================================

    def edit_file(
        self,
        path,
        old_text,
        new_text
    ):

        try:

            p = Path(path).expanduser().resolve()

            if not p.exists():

                return {
                    "ok": False,
                    "error":
                        f"File does not exist: {p}"
                }

            original = p.read_text(
                encoding="utf-8",
                errors="replace"
            )

            if old_text not in original:

                return {
                    "ok": False,
                    "error":
                        "The requested text was not found."
                }

            backup = p.with_suffix(
                p.suffix + ".ai-backup"
            )

            shutil.copy2(
                p,
                backup
            )

            updated = original.replace(
                old_text,
                new_text,
                1
            )

            p.write_text(
                updated,
                encoding="utf-8"
            )

            return {
                "ok": True,
                "path": str(p),
                "backup": str(backup),
                "message":
                    "File modified successfully."
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # TYPE
    # ========================================================

    def type_text(self, text):

        if pyautogui is None:

            return {
                "ok": False,
                "error":
                    "PyAutoGUI is unavailable."
            }

        try:

            # Clipboard paste handles long text and Unicode
            # much more reliably than pyautogui.write().
            if pyperclip is not None:

                pyperclip.copy(text)

                pyautogui.hotkey(
                    "ctrl",
                    "v"
                )

            else:

                pyautogui.write(
                    text,
                    interval=0.002
                )

            return {
                "ok": True,
                "message":
                    "Text pasted into the focused application."
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

        try:

            webbrowser.open(url)

            return {
                "ok": True,
                "url": url
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # WEB
    # ========================================================

    def web_search(self, query):

        if DDGS is None:

            return {
                "ok": False,
                "error":
                    "DDGS web search is unavailable."
            }

        try:

            results = list(
                DDGS().text(
                    query,
                    max_results=6
                )
            )

            return {
                "ok": True,
                "query": query,
                "results": results
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # SCREENSHOT
    # ========================================================

    def take_screenshot(self):

        result = self.registry_call(
            "take_screenshot",
            {}
        )

        if result is not None:
            return result

        if pyautogui is None:

            return {
                "ok": False,
                "error":
                    "Screenshot support unavailable."
            }

        try:

            folder = PROJECT_ROOT / "screenshots"
            folder.mkdir(
                exist_ok=True
            )

            import time

            path = folder / (
                "desktop_"
                + time.strftime(
                    "%Y%m%d_%H%M%S"
                )
                + ".png"
            )

            pyautogui.screenshot(
                str(path)
            )

            return {
                "ok": True,
                "path": str(path)
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # COMMAND
    # ========================================================

    def run_command(self, command):

        result = self.registry_call(
            "run_command",
            {"command": command}
        )

        if result is not None:
            return result

        # Conservative fallback.
        blocked = (
            "format ",
            "diskpart",
            "shutdown",
            "remove-item",
            "rmdir ",
            "del ",
            "erase "
        )

        if command.lower().strip().startswith(
            blocked
        ):

            return {
                "ok": False,
                "blocked": True,
                "error":
                    "Potentially destructive command blocked."
            }

        try:

            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                "ok":
                    completed.returncode == 0,
                "exit_code":
                    completed.returncode,
                "output":
                    (
                        completed.stdout
                        + completed.stderr
                    )[-15000:]
            }

        except Exception as exc:

            return {
                "ok": False,
                "error": str(exc)
            }

    # ========================================================
    # EXECUTION LOOP
    # ========================================================

    def run(
        self,
        message,
        history=None,
        status_callback=None
    ):

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        if history:
            messages.extend(
                history[-20:]
            )

        messages.append(
            {
                "role": "user",
                "content": message
            }
        )

        for step in range(15):

            if status_callback:
                status_callback(
                    f"Working... step {step + 1}"
                )

            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=self.schemas,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=4096
            )

            msg = response.choices[0].message

            calls = (
                getattr(
                    msg,
                    "tool_calls",
                    None
                )
                or []
            )

            if not calls:

                return (
                    msg.content
                    or "No response was returned."
                )

            messages.append(
                msg.model_dump()
            )

            for call in calls:

                name = call.function.name

                try:
                    args = json.loads(
                        call.function.arguments
                        or "{}"
                    )

                    if status_callback:
                        status_callback(
                            f"Executing {name}..."
                        )

                    fn = self.local_tools.get(
                        name
                    )

                    if fn is None:

                        result = {
                            "ok": False,
                            "error":
                                f"Unknown tool: {name}"
                        }

                    else:

                        result = fn(**args)

                except Exception as exc:

                    result = {
                        "ok": False,
                        "error": str(exc)
                    }

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(
                            result,
                            ensure_ascii=False,
                            default=str
                        )
                    }
                )

        return (
            "The task reached the safe execution-step limit."
        )
