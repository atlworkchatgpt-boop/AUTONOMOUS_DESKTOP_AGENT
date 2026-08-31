import tkinter as tk
from tkinter import messagebox
import hmac


OWNER = "Shreyansh Ray"

STARTUP_PASSWORD = "gngaistart"
ACTION_PASSWORD = "gngai"


BG = "#212121"
CARD = "#2b2b2b"
INPUT = "#383838"
TEXT = "#f1f1f1"
MUTED = "#a5a5a5"
ACCENT = "#10a37f"
RED = "#ff6b6b"


def password_dialog(
    parent,
    title,
    description,
    expected_password
):

    result = {
        "ok": False
    }

    dialog = tk.Toplevel(parent)

    dialog.title(title)

    dialog.geometry(
        "430x285"
    )

    dialog.configure(
        bg=BG
    )

    dialog.resizable(
        False,
        False
    )

    dialog.transient(
        parent
    )

    dialog.grab_set()


    # --------------------------------------------------------
    # TOP ICON
    # --------------------------------------------------------

    tk.Label(
        dialog,
        text="🔐",
        bg=BG,
        fg=TEXT,
        font=("Segoe UI Emoji", 30)
    ).pack(
        pady=(20, 4)
    )


    tk.Label(
        dialog,
        text=title,
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 16, "bold")
    ).pack()


    tk.Label(
        dialog,
        text=description,
        bg=BG,
        fg=MUTED,
        font=("Segoe UI", 9)
    ).pack(
        pady=(5, 15)
    )


    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------

    entry_frame = tk.Frame(
        dialog,
        bg=INPUT
    )

    entry_frame.pack(
        padx=35,
        fill="x"
    )


    entry = tk.Entry(
        entry_frame,
        bg=INPUT,
        fg=TEXT,
        insertbackground=TEXT,
        show="•",
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 12)
    )

    entry.pack(
        fill="x",
        padx=14,
        pady=12
    )


    error = tk.Label(
        dialog,
        text="",
        bg=BG,
        fg=RED,
        font=("Segoe UI", 8)
    )

    error.pack(
        pady=(7, 0)
    )


    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    buttons = tk.Frame(
        dialog,
        bg=BG
    )

    buttons.pack(
        pady=15
    )


    def cancel():

        result["ok"] = False

        dialog.destroy()


    def submit():

        supplied = entry.get()

        if hmac.compare_digest(
            supplied,
            expected_password
        ):

            result["ok"] = True

            dialog.destroy()

        else:

            entry.delete(
                0,
                "end"
            )

            error.configure(
                text="Incorrect password."
            )

            entry.focus_set()


    tk.Button(
        buttons,
        text="Cancel",
        command=cancel,
        bg="#333333",
        fg=TEXT,
        activebackground="#444444",
        activeforeground=TEXT,
        relief="flat",
        borderwidth=0,
        padx=20,
        pady=8,
        cursor="hand2"
    ).pack(
        side="left",
        padx=5
    )


    tk.Button(
        buttons,
        text="Unlock",
        command=submit,
        bg=ACCENT,
        fg="white",
        activebackground=ACCENT,
        activeforeground="white",
        relief="flat",
        borderwidth=0,
        padx=25,
        pady=8,
        cursor="hand2"
    ).pack(
        side="left",
        padx=5
    )


    entry.bind(
        "<Return>",
        lambda e: submit()
    )

    dialog.bind(
        "<Escape>",
        lambda e: cancel()
    )


    entry.focus_set()

    parent.wait_window(
        dialog
    )

    return result["ok"]


def startup_auth(parent):

    return password_dialog(
        parent,
        "GNG AI Secure Startup",
        "Enter the startup password to continue",
        STARTUP_PASSWORD
    )


def action_auth(
    parent,
    action
):

    return password_dialog(
        parent,
        "GNG AI — Authorization Required",
        "Authorize: " + action,
        ACTION_PASSWORD
    )
