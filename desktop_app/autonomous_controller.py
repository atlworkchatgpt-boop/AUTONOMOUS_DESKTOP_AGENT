from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any

# ============================================================
# AUTONOMOUS AI - LOCAL WINDOWS CONTROLLER
# Owner: Shreyansh Ray
#
# PURPOSE
# ------------------------------------------------------------
# Understand a request
# Decide whether AI reasoning is required
# Decide whether a desktop action is required
# Execute the required plan
# Verify the result
#
# Example:
#
# "Open Notepad and write an essay on humans in it and
# save as HUMANS.txt on Desktop"
#
# Plan:
#   1. Generate essay
#   2. Open Notepad
#   3. Put essay into Notepad
#   4. Save as HUMANS.txt
#   5. Verify file
#
# ============================================================


OWNER_NAME = "Shreyansh Ray"
OWNER_EMAIL = "atlworkchatgpt@gmail.com"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESKTOP = Path.home() / "Desktop"

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

MODEL_CANDIDATES = [
    "qwen2.5:7b",
    "qwen2.5:3b",
    "qwen2.5:1.5b",
    "llama3.2:3b",
    "llama3.2:1b",
]


# ============================================================
# OPTIONAL DEPENDENCIES
# ============================================================

try:
    import requests
except Exception:
    requests = None

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import pyperclip
except Exception:
    pyperclip = None


# ============================================================
# OUTPUT
# ============================================================

def log(message: str) -> None:
    print(f"[AUTONOMOUS AI] {message}")


def result(success: bool, message: str, **extra: Any) -> dict:
    data = {
        "success": success,
        "message": message,
    }
    data.update(extra)
    return data


# ============================================================
# OWNER IDENTITY
# ============================================================

def owner_answer(text: str) -> str | None:

    lower = text.lower()

    owner_questions = [
        "who is your owner",
        "who's your owner",
        "who is your creator",
        "who's your creator",
        "who created you",
        "who made you",
        "who built you",
        "who owns you",
    ]

    if any(q in lower for q in owner_questions):

        return (
            f"My owner and creator is {OWNER_NAME}. "
            f"I am Autonomous AI, the desktop AI project created by "
            f"{OWNER_NAME}."
        )

    return None


# ============================================================
# OLLAMA
# ============================================================

class LocalAI:

    def __init__(self):
        self.model = None

    def available(self) -> bool:

        if requests is None:
            return False

        try:
            response = requests.get(
                "http://127.0.0.1:11434/api/tags",
                timeout=3,
            )

            if response.status_code != 200:
                return False

            models = response.json().get("models", [])

            names = []

            for item in models:
                if isinstance(item, dict):
                    name = (
                        item.get("name")
                        or item.get("model")
                    )

                    if name:
                        names.append(name)

            for preferred in MODEL_CANDIDATES:

                if preferred in names:
                    self.model = preferred
                    return True

            for preferred in MODEL_CANDIDATES:

                base = preferred.split(":")[0]

                for name in names:

                    if name.startswith(base):
                        self.model = name
                        return True

        except Exception:
            pass

        return False

    def ask(
        self,
        prompt: str,
        temperature: float = 0.25,
    ) -> str | None:

        if requests is None:
            return None

        if not self.model:

            if not self.available():
                return None

        system = f"""
You are Autonomous AI.

Owner:
{OWNER_NAME}

You are a reasoning engine connected to a local Windows
desktop controller.

Your job is to understand requests accurately.

You may be asked to:
- answer questions
- write content
- plan computer tasks
- explain things
- generate text that another tool will place into an application

Never claim that a computer action happened unless the
controller actually confirms it.

Do not invent tool results.

For content-generation tasks, produce only the requested
content unless instructions say otherwise.
"""

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "options": {
                "temperature": temperature,
                "num_ctx": 4096,
            },
        }

        try:

            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=120,
            )

            response.raise_for_status()

            data = response.json()

            text = (
                data
                .get("message", {})
                .get("content", "")
                .strip()
            )

            return text or None

        except Exception as exc:

            log(f"Local AI unavailable: {exc}")
            return None


# ============================================================
# DESKTOP CONTROL
# ============================================================

class WindowsDesktop:

    def __init__(self):
        self.available = (
            os.name == "nt"
            and pyautogui is not None
        )

    def open_notepad(self) -> dict:

        if os.name != "nt":
            return result(
                False,
                "Desktop control requires Windows.",
            )

        try:

            process = subprocess.Popen(
                ["notepad.exe"]
            )

            time.sleep(1.5)

            return result(
                True,
                "Notepad opened.",
                process_id=process.pid,
            )

        except Exception as exc:

            return result(
                False,
                f"Could not open Notepad: {exc}",
            )

    def put_text_in_active_window(
        self,
        text: str,
    ) -> dict:

        if pyautogui is None:
            return result(
                False,
                "pyautogui is not installed.",
            )

        try:

            # Clipboard is used instead of pyautogui.write()
            # because it correctly handles Unicode text.
            if pyperclip is not None:

                pyperclip.copy(text)

                pyautogui.hotkey(
                    "ctrl",
                    "v",
                )

            else:

                # Fallback for ordinary ASCII.
                pyautogui.write(
                    text,
                    interval=0.001,
                )

            return result(
                True,
                "Text entered successfully.",
            )

        except Exception as exc:

            return result(
                False,
                f"Could not enter text: {exc}",
            )

    def save_active_document(
        self,
        filename: str,
    ) -> dict:

        if pyautogui is None:
            return result(
                False,
                "pyautogui is not installed.",
            )

        try:

            target = DESKTOP / filename

            target = target.resolve()

            # Make sure the requested save stays on Desktop.
            if target.parent != DESKTOP.resolve():

                return result(
                    False,
                    "Save target must be on the Desktop.",
                )

            pyautogui.hotkey(
                "ctrl",
                "shift",
                "s",
            )

            time.sleep(1)

            # Notepad save dialog.
            if pyperclip is not None:

                pyperclip.copy(
                    str(target)
                )

                pyautogui.hotkey(
                    "ctrl",
                    "v",
                )

            else:

                pyautogui.write(
                    str(target),
                    interval=0.002,
                )

            time.sleep(0.3)

            pyautogui.press(
                "enter"
            )

            time.sleep(1)

            # If Windows asks about replacing an existing file,
            # confirm it.
            pyautogui.press(
                "left"
            )

            pyautogui.press(
                "enter"
            )

            time.sleep(1)

            return result(
                True,
                "Save command completed.",
                path=str(target),
            )

        except Exception as exc:

            return result(
                False,
                f"Could not save document: {exc}",
            )

    def verify_file(
        self,
        path: Path,
    ) -> dict:

        path = path.resolve()

        if not path.exists():

            return result(
                False,
                "File verification failed.",
                path=str(path),
            )

        try:

            size = path.stat().st_size

        except Exception:

            size = -1

        return result(
            True,
            "File verified.",
            path=str(path),
            size=size,
        )


# ============================================================
# INTENT DETECTION
# ============================================================

class Intent:

    @staticmethod
    def wants_desktop(text: str) -> bool:

        lower = text.lower()

        desktop_words = [
            "open ",
            "launch ",
            "start ",
            "close ",
            "type ",
            "write ",
            "enter ",
            "save ",
            "click ",
            "press ",
            "desktop",
            "notepad",
            "calculator",
            "paint",
            "chrome",
            "edge",
            "vscode",
            "file",
        ]

        return any(
            word in lower
            for word in desktop_words
        )

    @staticmethod
    def wants_notepad(text: str) -> bool:

        return bool(
            re.search(
                r"\bnotepad\b",
                text,
                re.I,
            )
        )

    @staticmethod
    def wants_writing(text: str) -> bool:

        patterns = [
            r"\bwrite\b",
            r"\btype\b",
            r"\benter\b",
            r"\bcreate\b.*\btext\b",
            r"\bmake\b.*\bfile\b",
        ]

        return any(
            re.search(
                pattern,
                text,
                re.I | re.S,
            )
            for pattern in patterns
        )

    @staticmethod
    def extract_filename(text: str) -> str:

        patterns = [
            r"\bsave\s+(?:it\s+)?as\s+([A-Za-z0-9_. -]+)",
            r"\bsave\s+(?:the\s+)?file\s+as\s+([A-Za-z0-9_. -]+)",
            r"\bname\s+(?:it|the file)\s+([A-Za-z0-9_. -]+)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.I,
            )

            if match:

                name = match.group(1).strip()

                name = re.split(
                    r"\b(?:on|to|in)\s+(?:the\s+)?desktop\b",
                    name,
                    flags=re.I,
                )[0].strip()

                name = name.strip(
                    "\"'"
                )

                if "." not in name:
                    name += ".txt"

                return name

        return "AUTONOMOUS_AI_OUTPUT.txt"

    @staticmethod
    def extract_topic(text: str) -> str:

        patterns = [
            r"\bessay\s+on\s+(.+?)(?:\s+in\s+it|\s+and\s+save|\s+save\s+as|\s+on\s+desktop|$)",
            r"\bwrite\s+(?:an?\s+)?essay\s+(?:about|on)\s+(.+?)(?:\s+and\s+save|\s+save\s+as|\s+on\s+desktop|$)",
            r"\bwrite\s+about\s+(.+?)(?:\s+and\s+save|\s+save\s+as|\s+on\s+desktop|$)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.I | re.S,
            )

            if match:
                return match.group(1).strip()

        return "the requested topic"


# ============================================================
# AUTONOMOUS PLANNER
# ============================================================

class AutonomousPlanner:

    def __init__(
        self,
        ai: LocalAI,
        desktop: WindowsDesktop,
    ):

        self.ai = ai
        self.desktop = desktop

    def make_plan(
        self,
        request: str,
    ) -> dict:

        lower = request.lower()

        owner = owner_answer(request)

        if owner:

            return {
                "type": "answer",
                "answer": owner,
            }

        # ----------------------------------------------------
        # Explicit Notepad + writing workflow
        # ----------------------------------------------------

        if (
            Intent.wants_notepad(request)
            and Intent.wants_writing(request)
        ):

            topic = Intent.extract_topic(
                request
            )

            filename = Intent.extract_filename(
                request
            )

            return {
                "type": "notepad_write",
                "topic": topic,
                "filename": filename,
                "needs_ai": True,
            }

        # ----------------------------------------------------
        # Simple application launch
        # ----------------------------------------------------

        apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
        }

        for name, executable in apps.items():

            if re.search(
                rf"\b(?:open|launch|start)\s+{re.escape(name)}\b",
                lower,
            ):

                return {
                    "type": "open_app",
                    "application": executable,
                }

        # ----------------------------------------------------
        # General AI question
        # ----------------------------------------------------

        return {
            "type": "ai_answer",
            "needs_ai": True,
        }

    def execute(
        self,
        request: str,
    ) -> dict:

        log("Understanding request...")

        plan = self.make_plan(
            request
        )

        log(
            "Decision: "
            + json.dumps(
                plan,
                ensure_ascii=False,
            )
        )

        # ----------------------------------------------------
        # NORMAL ANSWER
        # ----------------------------------------------------

        if plan["type"] == "answer":

            return result(
                True,
                plan["answer"],
            )

        # ----------------------------------------------------
        # OPEN APP
        # ----------------------------------------------------

        if plan["type"] == "open_app":

            executable = plan["application"]

            try:

                subprocess.Popen(
                    [executable]
                )

                return result(
                    True,
                    f"Opened {executable}.",
                )

            except Exception as exc:

                return result(
                    False,
                    f"Could not open {executable}: {exc}",
                )

        # ----------------------------------------------------
        # NOTEPAD AUTONOMOUS WORKFLOW
        # ----------------------------------------------------

        if plan["type"] == "notepad_write":

            topic = plan["topic"]
            filename = plan["filename"]

            log(
                f"AI content required for topic: {topic}"
            )

            prompt = f"""
Write a good school-level essay about:

{topic}

Requirements:
- clear title
- introduction
- several well-developed paragraphs
- conclusion
- natural readable language
- no markdown code fences
- no discussion of being an AI
"""

            essay = self.ai.ask(
                prompt,
                temperature=0.35,
            )

            if not essay:

                return result(
                    False,
                    (
                        "I understood the task, but the local AI "
                        "model is unavailable. Start Ollama and "
                        "install one of the configured models."
                    ),
                    plan=plan,
                )

            log("Essay generated.")

            opened = self.desktop.open_notepad()

            if not opened["success"]:
                return opened

            log("Notepad opened.")

            time.sleep(0.8)

            typed = self.desktop.put_text_in_active_window(
                essay
            )

            if not typed["success"]:
                return typed

            log("Essay entered into Notepad.")

            saved = self.desktop.save_active_document(
                filename
            )

            if not saved["success"]:
                return saved

            target = DESKTOP / filename

            # Give Windows a moment to finish saving.
            time.sleep(1)

            verified = self.desktop.verify_file(
                target
            )

            if not verified["success"]:

                return result(
                    False,
                    "The save command completed but file verification failed.",
                    plan=plan,
                    path=str(target),
                )

            return result(
                True,
                (
                    f"Completed the task. I generated the essay, "
                    f"opened Notepad, entered it, saved it as "
                    f"{filename}, and verified the file on the Desktop."
                ),
                plan=plan,
                path=str(target),
                content=essay,
            )

        # ----------------------------------------------------
        # GENERAL AI
        # ----------------------------------------------------

        if plan["type"] == "ai_answer":

            answer = self.ai.ask(
                request
            )

            if answer:

                return result(
                    True,
                    answer,
                )

            return result(
                False,
                (
                    "I understood the request, but the local AI "
                    "model is unavailable. Start Ollama and make "
                    "sure a supported model is installed."
                ),
            )

        return result(
            False,
            "No executable plan was produced.",
        )


# ============================================================
# PUBLIC AGENT
# ============================================================

class AutonomousAI:

    def __init__(self):

        self.ai = LocalAI()

        self.desktop = WindowsDesktop()

        self.planner = AutonomousPlanner(
            self.ai,
            self.desktop,
        )

    def run(
        self,
        request: str,
    ) -> dict:

        request = request.strip()

        if not request:

            return result(
                False,
                "Empty request.",
            )

        return self.planner.execute(
            request
        )


# ============================================================
# COMMAND LINE
# ============================================================

def main():

    print()
    print("=" * 68)
    print(" AUTONOMOUS AI - LOCAL WINDOWS AGENT")
    print("=" * 68)
    print()
    print(f"Owner: {OWNER_NAME}")
    print("Desktop control: Windows")
    print()

    agent = AutonomousAI()

    print(
        "Type a request or type EXIT."
    )
    print()

    while True:

        try:

            request = input(
                "You > "
            ).strip()

        except (
            EOFError,
            KeyboardInterrupt,
        ):

            print()
            break

        if request.lower() in {
            "exit",
            "quit",
        }:

            break

        if not request:
            continue

        print()

        output = agent.run(
            request
        )

        print()
        print(
            "AI >",
            output["message"],
        )

        if output.get("path"):

            print(
                "File:",
                output["path"],
            )

        print()


if __name__ == "__main__":
    main()
