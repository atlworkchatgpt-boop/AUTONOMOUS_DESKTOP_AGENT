AUTONOMOUS DESKTOP AGENT - EVERYTHING FIXED BUILD

Project root: ada_test_project

Included:
- repaired frontend base
- chat/sidebar/scroll UI
- chess backend + history/review/PGN endpoints
- chess legal-move/animation support
- file upload/read support
- owner identity: Shreyansh Ray
- desktop app security/installer files
- requirements for cloud deployment

IMPORTANT MEDIA NOTE:
Image/video generation still requires a Google API project/key with quota/access for the selected image/video models. A 429 RESOURCE_EXHAUSTED response with quota limit 0 is an API quota/access problem, not something a frontend patch can bypass.

Windows local setup:
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-cloud.txt
.\.venv\Scripts\python.exe -m uvicorn web.main:app --host 127.0.0.1 --port 8000

Open:
http://127.0.0.1:8000

Installer build:
powershell -ExecutionPolicy Bypass -File .\desktop_app\BUILD_WINDOWS_INSTALLER.ps1
