import os
import hmac
import tkinter as tk
from tkinter import messagebox

OWNER_NAME = "Shreyansh Ray"

STARTUP_PASSWORD = os.getenv("GNG_STARTUP_PASSWORD", "gngaistart")
ACTION_PASSWORD = os.getenv("GNG_ACTION_PASSWORD", "gngai")

PASSWORD = ACTION_PASSWORD
SECURITY_PASSWORD = ACTION_PASSWORD
OWNER_PASSWORD = ACTION_PASSWORD

BG = "#0f1117"
CARD = "#171a23"
CARD2 = "#1d212c"
BORDER = "#303746"
TEXT = "#f4f7fb"
MUTED = "#8d96a8"
ACCENT = "#10a37f"
ACCENT_HOVER = "#13b88f"
ERROR = "#ff647c"


def _check(value, expected):
    if value is None:
        return False
    return hmac.compare_digest(str(value), str(expected))


def check_startup_password(value):
    return _check(value, STARTUP_PASSWORD)


def check_action_password(value):
    return _check(value, ACTION_PASSWORD)


def authenticate_startup(value):
    return check_startup_password(value)


def authenticate_action(value):
    return check_action_password(value)


def authorize(action=None, password=None, *args, **kwargs):
    if password is None and isinstance(action, str):
        return check_action_password(action)

    if password is not None:
        return check_action_password(password)

    return False


class AuthWindow:
    def __init__(self, mode="startup"):
        self.mode = mode
        self.result = False
        self.root = tk.Tk()

        self.root.title(
            "Autonomous Desktop AI — Authentication"
        )
        self.root.geometry("470x430")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.cancel
        )

        self.build()

        self.root.after(
            120,
            self.focus_password
        )

    def build(self):
        # Outer padding
        outer = tk.Frame(
            self.root,
            bg=BG
        )
        outer.pack(
            fill="both",
            expand=True,
            padx=24,
            pady=24
        )

        # Main card
        card = tk.Frame(
            outer,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        card.pack(
            fill="both",
            expand=True
        )

        # AI icon
        icon = tk.Canvas(
            card,
            width=72,
            height=72,
            bg=CARD,
            highlightthickness=0
        )
        icon.pack(pady=(24, 8))

        icon.create_oval(
            7, 7, 65, 65,
            fill=ACCENT,
            outline=""
        )

        icon.create_text(
            36,
            36,
            text="AI",
            fill="white",
            font=("Segoe UI", 18, "bold")
        )

        tk.Label(
            card,
            text="AUTONOMOUS DESKTOP AI",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 15, "bold")
        ).pack()

        tk.Label(
            card,
            text=(
                "Secure owner authentication"
                if self.mode == "startup"
                else "Protected computer action"
            ),
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(pady=(4, 15))

        # Owner
        owner = tk.Frame(
            card,
            bg=CARD2
        )
        owner.pack(
            fill="x",
            padx=28
        )

        tk.Label(
            owner,
            text="OWNER",
            bg=CARD2,
            fg=MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(
            anchor="w",
            padx=14,
            pady=(10, 0)
        )

        tk.Label(
            owner,
            text=OWNER_NAME,
            bg=CARD2,
            fg=TEXT,
            font=("Segoe UI", 11, "bold")
        ).pack(
            anchor="w",
            padx=14,
            pady=(2, 10)
        )

        # Password label
        tk.Label(
            card,
            text=(
                "Startup password"
                if self.mode == "startup"
                else "Owner authorization password"
            ),
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(
            anchor="w",
            padx=28,
            pady=(18, 6)
        )

        password_frame = tk.Frame(
            card,
            bg=CARD2,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        password_frame.pack(
            fill="x",
            padx=28
        )

        self.password = tk.Entry(
            password_frame,
            bg=CARD2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            bd=0,
            show="•",
            font=("Segoe UI", 11)
        )

        self.password.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(12, 4),
            pady=11
        )

        self.visible = False

        self.show_button = tk.Button(
            password_frame,
            text="SHOW",
            command=self.toggle_password,
            bg=CARD2,
            fg=MUTED,
            activebackground=CARD2,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2"
        )

        self.show_button.pack(
            side="right",
            padx=10
        )

        # Status
        self.status = tk.Label(
            card,
            text="Enter your password to continue.",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 8)
        )

        self.status.pack(
            pady=(10, 4)
        )

        # Authenticate button
        self.login_button = tk.Button(
            card,
            text="UNLOCK",
            command=self.submit,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        )

        self.login_button.pack(
            fill="x",
            padx=28,
            pady=(4, 8),
            ipady=8
        )

        # Cancel
        tk.Button(
            card,
            text="Cancel",
            command=self.cancel,
            bg=CARD,
            fg=MUTED,
            activebackground=CARD,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 9),
            cursor="hand2"
        ).pack(
            pady=(0, 15)
        )

        self.password.bind(
            "<Return>",
            lambda e: self.submit()
        )

    def focus_password(self):
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.password.focus_force()

            self.root.after(
                700,
                lambda: self.root.attributes(
                    "-topmost",
                    False
                )
            )
        except Exception:
            pass

    def toggle_password(self):
        self.visible = not self.visible

        self.password.configure(
            show="" if self.visible else "•"
        )

        self.show_button.configure(
            text="HIDE" if self.visible else "SHOW"
        )

    def submit(self):
        value = self.password.get()

        if not value:
            self.status.configure(
                text="Please enter your password.",
                fg=ERROR
            )
            self.shake()
            return

        self.login_button.configure(
            text="VERIFYING...",
            state="disabled"
        )

        self.status.configure(
            text="Verifying owner credentials...",
            fg=ACCENT
        )

        self.root.after(
            350,
            lambda: self.verify(value)
        )

    def verify(self, value):
        if self.mode == "startup":
            valid = check_startup_password(value)
        else:
            valid = check_action_password(value)

        if valid:
            self.status.configure(
                text="✓ Authentication successful",
                fg=ACCENT
            )

            self.root.after(
                350,
                self.success
            )

        else:
            self.status.configure(
                text="✕ Incorrect password — try again.",
                fg=ERROR
            )

            self.password.delete(
                0,
                "end"
            )

            self.login_button.configure(
                text="UNLOCK",
                state="normal"
            )

            self.shake()

    def shake(self):
        original = self.root.geometry()
        x = self.root.winfo_x()
        y = self.root.winfo_y()

        offsets = [-8, 8, -6, 6, -3, 3, 0]

        def move(i=0):
            if i >= len(offsets):
                self.root.geometry(
                    f"470x430+{x}+{y}"
                )
                return

            self.root.geometry(
                f"470x430+{x + offsets[i]}+{y}"
            )

            self.root.after(
                35,
                lambda: move(i + 1)
            )

        move()

    def success(self):
        self.result = True
        self.root.destroy()

    def cancel(self):
        self.result = False
        self.root.destroy()

    def show(self):
        self.root.mainloop()
        return self.result


def ensure_password():
    return AuthWindow("startup").show()


def request_action_password():
    return AuthWindow("action").show()


def is_owner(value):
    return check_action_password(value)


def require_action_password(value):
    if not check_action_password(value):
        raise PermissionError(
            "Owner authorization required."
        )
    return True
