import os
import sys
import tkinter as tk


PROJECT_ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROJECT_ROOT
    )


from agent.security_ui import startup_auth


def main():

    root = tk.Tk()

    root.withdraw()

    # --------------------------------------------------------
    # AESTHETIC STARTUP PASSWORD
    # --------------------------------------------------------

    authorized = startup_auth(
        root
    )

    if not authorized:

        root.destroy()

        return

    # --------------------------------------------------------
    # IMPORT DASHBOARD ONLY AFTER AUTH
    # --------------------------------------------------------

    try:

        root.destroy()

        import dashboard

        dashboard.launch()

    except Exception as e:

        error_root = tk.Tk()

        error_root.withdraw()

        from tkinter import messagebox

        messagebox.showerror(
            "GNG AI Startup Error",
            "Dashboard could not start:\n\n"
            + str(e)
        )

        error_root.destroy()


if __name__ == "__main__":

    main()
