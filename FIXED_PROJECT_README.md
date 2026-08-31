# Autonomous Desktop Agent — Clean Current-Project Repair

This package is rebuilt from the supplied current project, while replacing the accumulated web/repair layers with one coherent web stack.

## Web architecture
- one FastAPI entry point: `web/main.py`
- one guest session router: `web/guest.py`
- one chat flow supporting guests and signed-in users
- one media feature router: `web/final_web_features.py`
- one chess service: `web/chess_service.py`
- one frontend: `web/static/index.html`, `app.js`, `style.css`
- creator page: Shreyansh Ray
- image, video, transcription, voice, copy-code features wired through the clean frontend
- chess legal-move endpoint: `/api/autonomous/chess/legal-moves`
- chess piece animation toggle and legal-destination highlighting

## Run locally

Use Python 3.12:

```powershell
cd "<this-folder>"
& "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r requirements-cloud.txt
& "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn web.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`.

## Environment

Copy `.env.example` to `.env` and provide your own API credentials. Never commit `.env`.

Required for chat:
- `GROQ_API_KEY`

Media/voice:
- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`)

Google sign-in:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

## Render

Start command:

`uvicorn web.main:app --host 0.0.0.0 --port $PORT`

Add API keys in Render Environment Variables.

The image and video implementations follow the current Google Gemini/OpenAI-compatible API patterns documented by Google. citeturn516627search1turn516627search0
