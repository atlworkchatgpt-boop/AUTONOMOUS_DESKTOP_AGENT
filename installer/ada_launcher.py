import os
import sys
import time
import threading
import webbrowser

def open_browser():
    time.sleep(3)

    try:
        webbrowser.open(
            "http://127.0.0.1:8765/"
        )
    except Exception:
        pass

def main():

    base = os.path.dirname(
        os.path.abspath(sys.executable)
        if getattr(sys, "frozen", False)
        else os.path.abspath(__file__)
    )

    if base not in sys.path:
        sys.path.insert(0, base)

    os.environ["ADA_DESKTOP_APP"] = "1"

    try:
        import uvicorn
    except Exception as e:
        print("")
        print("Autonomous AI could not load Uvicorn.")
        print(str(e))
        input("Press ENTER to close...")
        return

    threading.Thread(
        target=open_browser,
        daemon=True
    ).start()

    try:

        uvicorn.run(
            "web.main:app",
            host="127.0.0.1",
            port=8765,
            reload=False
        )

    except Exception as e:

        print("")
        print("================================================")
        print(" AUTONOMOUS AI STARTUP ERROR")
        print("================================================")
        print("")
        print(str(e))
        print("")
        input("Press ENTER to close...")

if __name__ == "__main__":
    main()
