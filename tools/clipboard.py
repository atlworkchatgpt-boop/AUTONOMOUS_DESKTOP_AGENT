import tkinter as tk


def read_clipboard():

    root = tk.Tk()
    root.withdraw()

    try:
        value = root.clipboard_get()
    except Exception:
        value = ""
    finally:
        root.destroy()

    return {
        "ok": True,
        "text": value,
    }


def write_clipboard(
    text,
):

    root = tk.Tk()
    root.withdraw()

    try:

        root.clipboard_clear()

        root.clipboard_append(
            text
        )

        root.update()

    finally:

        root.destroy()

    return {
        "ok": True,
        "message": "Clipboard updated.",
    }