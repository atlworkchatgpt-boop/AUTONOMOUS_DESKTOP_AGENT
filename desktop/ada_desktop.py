import os
import sys
import time
import socket
import threading
import traceback

# ------------------------------------------------------------
# FORCE SOFTWARE RENDERING BEFORE QT STARTS
# ------------------------------------------------------------

os.environ["QT_OPENGL"] = "software"
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--disable-gpu "
    "--disable-gpu-compositing "
    "--disable-gpu-rasterization "
    "--disable-gpu-sandbox "
    "--disable-software-rasterizer "
    "--use-angle=swiftshader"
)

os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView


HOST = "127.0.0.1"
PORT = 8765

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


def wait_for_server(
    host,
    port,
    timeout=60
):

    deadline = time.time() + timeout

    while time.time() < deadline:

        try:

            sock = socket.create_connection(
                (host, port),
                timeout=0.5
            )

            sock.close()

            return True

        except OSError:

            time.sleep(0.25)

    return False


def start_backend():

    try:

        os.chdir(ROOT)

        # Direct import is much safer with PyInstaller
        # than asking uvicorn to dynamically import a string.
        from web.main import app
        import uvicorn

        config = uvicorn.Config(
            app,
            host=HOST,
            port=PORT,
            log_level="warning",
            reload=False
        )

        server = uvicorn.Server(config)

        thread = threading.Thread(
            target=server.run,
            daemon=True
        )

        thread.start()

        return server

    except Exception:

        error = traceback.format_exc()

        try:

            with open(
                os.path.join(
                    ROOT,
                    "ADA_BACKEND_ERROR.txt"
                ),
                "w",
                encoding="utf-8"
            ) as f:

                f.write(error)

        except Exception:
            pass

        print(error)

        return None


class ADAWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Autonomous Desktop AI"
        )

        self.resize(
            1440,
            920
        )

        self.browser = QWebEngineView()

        self.browser.settings().setAttribute(
            self.browser.settings().WebAttribute.JavascriptEnabled,
            True
        )

        self.browser.settings().setAttribute(
            self.browser.settings().WebAttribute.LocalContentCanAccessRemoteUrls,
            True
        )

        self.browser.setUrl(
            QUrl(
                f"http://{HOST}:{PORT}/"
            )
        )

        self.setCentralWidget(
            self.browser
        )


def main():

    os.chdir(ROOT)

    server = start_backend()

    if server is None:

        raise RuntimeError(
            "ADA backend failed. "
            "See ADA_BACKEND_ERROR.txt"
        )

    if not wait_for_server(
        HOST,
        PORT
    ):

        raise RuntimeError(
            "ADA backend did not become ready."
        )

    app = QApplication(
        sys.argv
    )

    window = ADAWindow()

    window.show()

    return app.exec()


if __name__ == "__main__":

    try:

        sys.exit(
            main()
        )

    except Exception:

        error = traceback.format_exc()

        try:

            with open(
                "ADA_DESKTOP_ERROR.txt",
                "w",
                encoding="utf-8"
            ) as f:

                f.write(error)

        except Exception:
            pass

        print(error)

        input(
            "\nPress ENTER to close..."
        )

        sys.exit(1)
