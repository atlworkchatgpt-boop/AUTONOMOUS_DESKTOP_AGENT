import os
import sys
import threading
import time
import webbrowser

def open_browser():
    time.sleep(3)
    try:
        webbrowser.open("http://127.0.0.1:8765/")
    except Exception:
        pass

def main():
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    try:
        import uvicorn
    except Exception as e:
        print("Could not load Uvicorn:")
        print(e)
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
        print("Autonomous AI failed to start.")
        print(e)
        print("")
        input("Press ENTER to close...")

if __name__ == "__main__":
    main()
