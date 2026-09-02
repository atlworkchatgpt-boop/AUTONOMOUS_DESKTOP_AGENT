import os
import sys
import time
import socket
import subprocess
import webbrowser
import urllib.request

import webview


# ============================================================
# AUTONOMOUS DESKTOP AI
# Native Desktop Launcher
# ============================================================

HOST = "127.0.0.1"
START_PORT = 8765

WINDOW_TITLE = "Autonomous Desktop AI"

WINDOW_WIDTH = 1450
WINDOW_HEIGHT = 900

MIN_WIDTH = 1000
MIN_HEIGHT = 650


# ============================================================
# FIND FREE PORT
# ============================================================

def find_free_port(start=START_PORT):

    port = start

    while port < start + 100:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        try:
            sock.bind((HOST, port))
            sock.close()
            return port

        except OSError:
            sock.close()
            port += 1

    raise RuntimeError(
        "Could not find a free local port."
    )


# ============================================================
# WAIT FOR SERVER
# ============================================================

def wait_for_server(url, timeout=30):

    deadline = time.time() + timeout

    while time.time() < deadline:

        try:

            with urllib.request.urlopen(
                url,
                timeout=1
            ) as response:

                if response.status < 500:
                    return True

        except Exception:
            pass

        time.sleep(0.25)

    return False


# ============================================================
# OPEN GOOGLE LOGIN IN REAL BROWSER
# ============================================================

def open_google_login():

    login_url = (
        f"http://{HOST}:{PORT}/auth/google"
    )

    print()
    print("Opening Google sign-in in your default browser...")
    print(login_url)

    webbrowser.open(
        login_url,
        new=2
    )


# ============================================================
# MAIN
# ============================================================

PORT = None
backend = None
window = None


def main():

    global PORT
    global backend
    global window

    PORT = find_free_port()

    print("=" * 64)
    print(" AUTONOMOUS DESKTOP AI")
    print("=" * 64)
    print()
    print("Local port:", PORT)
    print()

    # --------------------------------------------------------
    # START FASTAPI
    # --------------------------------------------------------

    backend = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "web.main:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
            "--no-access-log",
        ],
        cwd=os.path.dirname(
            os.path.abspath(__file__)
        ),
        creationflags=(
            subprocess.CREATE_NO_WINDOW
            if os.name == "nt"
            else 0
        ),
    )

    local_url = (
        f"http://{HOST}:{PORT}"
    )

    print("Starting ADA backend...")
    print()

    if not wait_for_server(local_url):

        print()
        print("ERROR: ADA backend did not start.")
        print()

        if backend:
            backend.terminate()

        raise RuntimeError(
            "FastAPI backend failed to start."
        )

    print("ADA backend is ready.")
    print()

    # --------------------------------------------------------
    # CREATE NATIVE WINDOW
    # --------------------------------------------------------

    window = webview.create_window(
        WINDOW_TITLE,
        local_url,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(
            MIN_WIDTH,
            MIN_HEIGHT
        ),
        resizable=True,
        text_select=True,
        confirm_close=True,
    )

    # --------------------------------------------------------
    # GOOGLE LOGIN HANDLER
    #
    # We expose this to JavaScript so the website can request
    # the real system browser for Google authentication.
    # --------------------------------------------------------

    class API:

        def google_login(self):

            open_google_login()

            return {
                "success": True
            }

    # --------------------------------------------------------
    # START PYWEBVIEW
    # --------------------------------------------------------

    print("Opening native ADA window...")
    print()
    print("=" * 64)

    try:

        webview.start(
            func=None,
            gui="edgechromium",
            debug=False,
        )

    finally:

        print()
        print("Closing ADA...")

        if backend:

            try:
                backend.terminate()
                backend.wait(timeout=5)

            except Exception:

                try:
                    backend.kill()

                except Exception:
                    pass

        print("ADA closed.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()