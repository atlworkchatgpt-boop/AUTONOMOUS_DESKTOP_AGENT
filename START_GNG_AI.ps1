$PYTHON = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
$PROJECT = "C:\Users\ADMIN\Desktop\AUTONOMOUS_DESKTOP_AGENT"

Set-Location $PROJECT

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "              GNG AI STARTING" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

if (-not $env:GROQ_API_KEY) {
    Write-Host "GROQ_API_KEY is not available in this PowerShell session." -ForegroundColor Red
    Write-Host ""
    Write-Host "Load your existing Groq key first, then run this launcher again."
    Write-Host ""
    Read-Host "Press ENTER to close"
    exit 1
}

& $PYTHON -X faulthandler -u ".\dashboard.py"

Write-Host ""
Write-Host "GNG AI closed." -ForegroundColor Yellow
Read-Host "Press ENTER to close"
