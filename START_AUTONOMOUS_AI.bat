@echo off
setlocal

title Autonomous AI

cd /d "%~dp0"

echo.
echo ============================================================
echo                  AUTONOMOUS AI
echo ============================================================
echo.

if exist "python\python.exe" (
    echo Starting bundled Python...
    "python\python.exe" -m uvicorn web.main:app --host 127.0.0.1 --port 8765
    goto END
)

if exist ".venv\Scripts\python.exe" (
    echo Starting project virtual environment...
    ".venv\Scripts\python.exe" -m uvicorn web.main:app --host 127.0.0.1 --port 8765
    goto END
)

where py >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo Starting installed Python...
    py -3 -m uvicorn web.main:app --host 127.0.0.1 --port 8765
    goto END
)

echo.
echo ERROR:
echo Python was not found.
echo.
echo Install Python and try again.
echo.

:END
pause
endlocal
