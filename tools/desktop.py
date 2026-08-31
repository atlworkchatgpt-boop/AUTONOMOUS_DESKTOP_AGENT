import pyautogui


def type_text(
    text,
):

    pyautogui.write(
        text,
        interval=0.01,
    )

    return {
        "ok": True,
        "message": "Text typed.",
    }


def press_key(
    key,
):

    pyautogui.press(
        key
    )

    return {
        "ok": True,
        "message": f"Pressed {key}.",
    }


def press_hotkey(
    keys,
):

    pyautogui.hotkey(
        *keys
    )

    return {
        "ok": True,
        "message": (
            f"Pressed {' + '.join(keys)}."
        ),
    }


def move_mouse(
    x,
    y,
):

    pyautogui.moveTo(
        x,
        y,
        duration=0.15,
    )

    return {
        "ok": True,
        "message": (
            f"Mouse moved to ({x}, {y})."
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