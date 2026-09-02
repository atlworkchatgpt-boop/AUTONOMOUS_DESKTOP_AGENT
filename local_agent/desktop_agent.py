import os
import webbrowser
import subprocess
import pathlib
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="ADA Local Desktop Companion")

# Change this before using the bridge seriously.
LOCAL_TOKEN = os.environ.get("ADA_LOCAL_TOKEN", "ADA-LOCAL-CHANGE-ME")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://autonomous-desktop-agent-1.onrender.com",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Action(BaseModel):
    action: str
    target: Optional[str] = None
    content: Optional[str] = None


def verify(token):
    if token != LOCAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid local ADA token")


@app.get("/health")
def health():
    return {
        "ok": True,
        "agent": "ADA Local Desktop Companion"
    }


@app.post("/execute")
def execute(
    request: Action,
    x_ada_token: Optional[str] = Header(default=None)
):
    verify(x_ada_token)

    action = request.action.lower().strip()
    target = (request.target or "").strip()

    # ---------------------------------------------------------
    # OPEN WEBSITE
    # ---------------------------------------------------------
    if action == "open_url":
        if not target.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400,
                detail="Only http/https URLs are allowed."
            )

        webbrowser.open(target)

        return {
            "ok": True,
            "message": "Opened website",
            "target": target
        }

    # ---------------------------------------------------------
    # OPEN WINDOWS APP
    # ---------------------------------------------------------
    if action == "open_app":

        allowed_apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
        }

        name = target.lower()

        if name not in allowed_apps:
            raise HTTPException(
                status_code=400,
                detail="App is not in ADA's safe application list."
            )

        subprocess.Popen([allowed_apps[name]])

        return {
            "ok": True,
            "message": f"Opened {name}"
        }

    # ---------------------------------------------------------
    # CREATE TEXT FILE ON DESKTOP
    # ---------------------------------------------------------
    if action == "create_text_file":

        filename = pathlib.Path(target).name

        if not filename.lower().endswith(".txt"):
            raise HTTPException(
                status_code=400,
                detail="Only .txt files are allowed."
            )

        desktop = pathlib.Path.home() / "Desktop"
        output = desktop / filename

        output.write_text(
            request.content or "",
            encoding="utf-8"
        )

        return {
            "ok": True,
            "message": "Text file created",
            "path": str(output)
        }

    # ---------------------------------------------------------
    # OPEN FILE
    # ---------------------------------------------------------
    if action == "open_file":

        path = pathlib.Path(target).expanduser().resolve()

        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail="File does not exist."
            )

        os.startfile(str(path))

        return {
            "ok": True,
            "message": "File opened",
            "path": str(path)
        }

    raise HTTPException(
        status_code=400,
        detail=f"Unknown ADA action: {action}"
    )
