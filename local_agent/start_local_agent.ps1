$env:ADA_LOCAL_TOKEN = "ADA-LOCAL-CHANGE-ME"

if (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" -m uvicorn local_agent.desktop_agent:app --host 127.0.0.1 --port 8765
} else {
    & python -m uvicorn local_agent.desktop_agent:app --host 127.0.0.1 --port 8765
}
