import os
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import psutil
import pyautogui

from config.config import SCREENSHOT_DIR


def launch_app(command):

    subprocess.Popen(
        command,
        shell=True
    )

    return {
        "ok": True,
        "message": (
            f"Started: {command}"
        ),
    }


def open_folder(path):

    target = (
        Path(path)
        .expanduser()
        .resolve()
    )

    os.startfile(
        str(target)
    )

    return {
        "ok": True,
        "message": (
            f"Opened: {target}"
        ),
    }


def open_url(url):

    webbrowser.open(
        url
    )

    return {
        "ok": True,
        "message": (
            f"Opened: {url}"
        ),
    }


def search_google(query):

    url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    webbrowser.open(
        url
    )

    return {
        "ok": True,
        "message": (
            f"Searched Google for: {query}"
        ),
    }


def screenshot():

    filename = datetime.now().strftime(
        "screen_%Y%m%d_%H%M%S.png"
    )

    path = (
        SCREENSHOT_DIR
        / filename
    )

    image = pyautogui.screenshot()

    image.save(
        path
    )

    return {
        "ok": True,
        "message": (
            f"Screenshot saved: {path}"
        ),
        "path": str(path),
    }


def type_text(text):

    pyautogui.write(
        text,
        interval=0.01,
    )

    return {
        "ok": True,
        "message": "Text typed.",
    }


def press_key(key):

    pyautogui.press(
        key
    )

    return {
        "ok": True,
        "message": f"Pressed {key}.",
    }


def hotkey(keys):

    pyautogui.hotkey(
        *keys
    )

    return {
        "ok": True,
        "message": (
            f"Pressed {' + '.join(keys)}."
        ),
    }


def move_mouse(x, y):

    pyautogui.moveTo(
        x,
        y,
        duration=0.15
    )

    return {
        "ok": True,
        "message": (
            f"Moved mouse to ({x}, {y})."
        ),
    }


def click_mouse(
    x=None,
    y=None,
    button="left",
):

    pyautogui.click(
        x=x,
        y=y,
        button=button,
    )

    return {
        "ok": True,
        "message": "Mouse clicked.",
    }


def system_info():

    memory = psutil.virtual_memory()

    return {
        "ok": True,
        "message": (
            f"CPU: {psutil.cpu_percent(interval=0.2)}%\n"
            f"Memory: {memory.percent}%\n"
            f"RAM: {round(memory.total / (1024**3), 2)} GB"
        ),
    }


def process_list():

    rows = []

    for process in psutil.process_iter(
        ["pid", "name"]
    ):

        try:

            rows.append(
                f"{process.info['pid']}: "
                f"{process.info['name']}"
            )

        except Exception:

            continue

    return {
        "ok": True,
        "message": "\n".join(
            rows[:150]
        ),
    }


def read_file(path):

    target = (
        Path(path)
        .expanduser()
        .resolve()
    )

    if not target.is_file():

        return {
            "ok": False,
            "message": (
                f"File not found: {target}"
            ),
        }

    try:

        return {
            "ok": True,
            "content": target.read_text(
                encoding="utf-8",
                errors="replace",
            )[:30000],
            "message": (
                f"Read: {target}"
            ),
        }

    except Exception as exc:

        return {
            "ok": False,
            "message": str(exc),
        }


def write_file(
    path,
    content,
):

    target = (
        Path(path)
        .expanduser()
        .resolve()
    )

    try:

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        return {
            "ok": True,
            "message": (
                f"File written: {target}"
            ),
        }

    except Exception as exc:

        return {
            "ok": False,
            "message": str(exc),
        }