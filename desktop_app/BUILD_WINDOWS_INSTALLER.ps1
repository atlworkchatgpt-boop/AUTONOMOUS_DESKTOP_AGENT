$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (!(Test-Path ".venv\Scripts\python.exe")) { py -3 -m venv .venv }
$Py=".venv\Scripts\python.exe"
& $Py -m pip install -U pip pyinstaller keyring
if (Test-Path requirements.txt) { & $Py -m pip install -r requirements.txt }
& $Py -m pip install python-chess fastapi uvicorn google-genai pypdf python-docx python-multipart groq pyautogui psutil Pillow SpeechRecognition
& $Py -m PyInstaller --noconfirm --clean --onedir --windowed --name AutonomousAI `
  --add-data "web;web" --add-data "agent;agent" --add-data "tools;tools" --add-data "config;config" --add-data "security;security" --add-data "knowledge;knowledge" `
  desktop_app\secure_launcher.py
$Iss=Join-Path $Root "installer\AutonomousAI.iss"
$Iscc=@("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe","C:\Program Files (x86)\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (!$Iscc -and (Get-Command winget -ErrorAction SilentlyContinue)) { winget install --id JRSoftware.InnoSetup -e --accept-source-agreements --accept-package-agreements; $Iscc=@("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe","C:\Program Files (x86)\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1 }
if ($Iscc) { & $Iscc $Iss; Write-Host "Installer created in installer_output" } else { Write-Host "Portable app created in dist\AutonomousAI. Install Inno Setup later to build Setup.exe." }
Read-Host "Press ENTER"
