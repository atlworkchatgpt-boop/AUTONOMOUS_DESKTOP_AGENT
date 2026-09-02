@echo off
title Autonomous AI

echo.
echo ============================================================
echo                 AUTONOMOUS AI
echo ============================================================
echo.
echo Starting local ComfyUI...
echo.

start "ADA ComfyUI" "%~dp0START_COMFYUI.bat"

timeout /t 8 /nobreak >nul

echo.
echo Starting Autonomous AI...
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn web.main:app --host 127.0.0.1 --port 8000
    pause
    exit /b
)

py -3.12 -m uvicorn web.main:app --host 127.0.0.1 --port 8000

pause
