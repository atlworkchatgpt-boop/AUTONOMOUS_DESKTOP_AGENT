$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
Write-Host "============================================================"
Write-Host " AUTONOMOUS AI - WINDOWS APP + INSTALLER BUILDER"
Write-Host "============================================================"
Write-Host ""
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Python launcher 'py' was not found. Install Python 3.12+ first." }
if (-not (Test-Path ".venv\Scripts\python.exe")) { py -3 -m venv .venv }
$Py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $Py -m pip install --upgrade pip
if (Test-Path "requirements.txt") { & $Py -m pip install -r requirements.txt }
& $Py -m pip install pyinstaller python-chess google-genai python-multipart pypdf python-docx
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
& $Py -m PyInstaller --noconfirm --clean --onedir --windowed --name AutonomousAI --add-data "web;web" --add-data "agent;agent" --add-data "tools;tools" --add-data "config;config" --add-data "security;security" --add-data "knowledge;knowledge" main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }
$Iscc = @(
 "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
 "C:\Program Files\Inno Setup 6\ISCC.exe",
 "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) {
 Write-Host ""
 Write-Host "Portable build created: dist\AutonomousAI"
 Write-Host "Inno Setup 6 is not installed, so Setup.exe cannot be built yet."
 Write-Host "Install Inno Setup 6, then run this script again."
 Read-Host "Press ENTER"
 exit 0
}
& $Iscc (Join-Path $PSScriptRoot "installer\AutonomousAI.iss")
Write-Host ""
Write-Host "============================================================"
Write-Host " SETUP CREATED"
Write-Host "============================================================"
Write-Host ""
Write-Host (Join-Path $PSScriptRoot "installer_output\AutonomousAI_Setup.exe")
Read-Host "Press ENTER"
