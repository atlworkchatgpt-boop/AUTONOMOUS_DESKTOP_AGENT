@echo off
title Autonomous AI

cd /d "%~dp0"

echo ==========================================
echo       AUTONOMOUS AI
echo ==========================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m web.main
    pause
    exit /b
)

if exist "web\main.py" (
    py -3 -m web.main
    pause
    exit /b
)

echo.
echo Autonomous AI could not find its Python application.
echo.
pause
