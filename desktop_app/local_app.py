import os
import sys
import time
import socket
import threading
from pathlib import Path


# ============================================================
# SOFTWARE RENDERING
# Prevent QtWebEngine GPU/EGL problems on older hardware.
# ============================================================

os.environ.setdefault(
    "QT_OPENGL",
    "software"
)

os.environ.setdefault(
    "QT_QUICK_BACKEND",
    "software"
)

os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu "
    "--disable-gpu-compositing "
    "--disable-gpu-rasterization "
    "--disable-gpu-sandbox "
    "--use-angle=swiftshader"
)

os.environ.setdefault(
    "QTWEBENGINE_DISABLE_SANDBOX",
    "1"
)


ROOT = Path(__file__).resolve().parent.parent


def wait_for_backend(
    host="127.0.0.1",
    port=8765,
    timeout=40
):

    deadline = time.time() + timeout

    while time.time() < deadline:

        try:

            with socket.create_connection(
                (host, port),
                timeout=0.5
            ):
                return True

        except Exception:
            time.sleep(0.25)

    return False


def start_backend():

    import uvicorn

    from web.main import app

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8765,
        log_level="warning",
        access_log=False
    )

    server = uvicorn.Server(
        config
    )

    thread = threading.Thread(
        target=server.run,
        daemon=True
    )

    thread.start()

    return server


def run_gui():

    from PySide6.QtCore import QUrl
    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow
    )
    from PySide6.QtWebEngineWidgets import (
        QWebEngineView
    )

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Autonomous Desktop AI"
    )

    window = QMainWindow()

    window.setWindowTitle(
        "Autonomous Desktop AI"
    )

    window.resize(
        1440,
        900
    )

    browser = QWebEngineView()

    browser.setUrl(
        QUrl(
            "http://127.0.0.1:8765/"
        )
    )

    window.setCentralWidget(
        browser
    )

    window.show()

    return app.exec()


def main():

    print(
        "Starting Autonomous Desktop AI..."
    )

    from agent.authentication import ensure_password

    # --------------------------------------------------------
    # FIRST RUN PASSWORD
    # --------------------------------------------------------

    if not ensure_password():

        print(
            "Password setup cancelled."
        )

        return 2

    print(
        "Security system ready."
    )

    # --------------------------------------------------------
    # START EXISTING ADA BACKEND
    # --------------------------------------------------------

    server = start_backend()

    if not wait_for_backend():

        print(
            "ERROR: ADA backend did not become ready."
        )

        return 3

    print(
        "ADA backend ready."
    )

    try:

        return run_gui()

    finally:

        try:
            server.should_exit = True
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
