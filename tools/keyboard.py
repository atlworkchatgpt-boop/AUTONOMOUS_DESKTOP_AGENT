import pyautogui


def type_text(
    text,
    interval=0.01
):

    pyautogui.write(
        text,
        interval=interval,
    )


def press(key):

    pyautogui.press(
        key
    )


def hotkey(*keys):

    pyautogui.hotkey(
        *keys
    )
