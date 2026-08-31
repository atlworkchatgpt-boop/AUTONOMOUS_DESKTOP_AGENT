import pyautogui


def move(
    x,
    y,
    duration=0.15
):

    pyautogui.moveTo(
        x,
        y,
        duration=duration,
    )


def click(
    x=None,
    y=None,
    button="left"
):

    pyautogui.click(
        x=x,
        y=y,
        button=button,
    )
