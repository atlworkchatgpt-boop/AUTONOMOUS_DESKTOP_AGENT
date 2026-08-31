@echo off

title Build Autonomous AI Installer

where ISCC.exe >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    ISCC.exe "%~dp0installer\AutonomousAI.iss"
    echo.
    echo Installer build finished.
    pause
    exit /b
)

if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%~dp0installer\AutonomousAI.iss"
    echo.
    echo Installer build finished.
    pause
    exit /b
)

if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    "%ProgramFiles%\Inno Setup 6\ISCC.exe" "%~dp0installer\AutonomousAI.iss"
    echo.
    echo Installer build finished.
    pause
    exit /b
)

echo.
echo Inno Setup was not found.
echo Install Inno Setup, then run this file again.
echo.
pause
