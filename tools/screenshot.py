from datetime import datetime

import pyautogui

from config.config import (
    SCREENSHOT_DIR,
)


def take_screenshot():

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
        "path": str(path),
    }