$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$py = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"

if (!(Test-Path $py)) {
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) {
        $py = "py"
    } else {
        Write-Host "Python 3.12 was not found." -ForegroundColor Red
        Read-Host "Press ENTER to close"
        exit 1
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "        AUTONOMOUS DESKTOP AI - PRO LAUNCHER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# Check required files individually
# ------------------------------------------------------------

$files = @(
    ".\dashboard.py",
    ".\agent\pro_groq_agent.py",
    ".\agent\tools_registry.py",
    ".\agent\authentication.py"
)

foreach ($file in $files) {
    if (!(Test-Path $file)) {
        Write-Host "MISSING: $file" -ForegroundColor Red
        Read-Host "Press ENTER to close"
        exit 1
    }

    Write-Host "FOUND:   $file" -ForegroundColor Green
}

# ------------------------------------------------------------
# Syntax-check EACH file separately
# ------------------------------------------------------------

Write-Host ""
Write-Host "Checking Python syntax..." -ForegroundColor Yellow

foreach ($file in $files) {

    Write-Host "Checking $file ..." -ForegroundColor Gray

    & $py -m py_compile $file

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "SYNTAX ERROR IN: $file" -ForegroundColor Red
        Read-Host "Press ENTER to close"
        exit 1
    }
}

# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------

Write-Host ""
Write-Host "Checking Groq environment..." -ForegroundColor Yellow

$envFile = Join-Path $PSScriptRoot ".env"

if (Test-Path $envFile) {

    Write-Host ".env found." -ForegroundColor Green

} else {

    Write-Host ".env not found." -ForegroundColor Yellow
    Write-Host "The dashboard will try the current environment." -ForegroundColor Yellow
}

# ------------------------------------------------------------
# Launch
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "                 PRO AI READY" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "OWNER                 : Shreyansh Ray" -ForegroundColor White
Write-Host "GROQ                  : ENABLED" -ForegroundColor White
Write-Host "LOCAL TOOLS           : ENABLED" -ForegroundColor White
Write-Host "MULTI-STEP TASKS      : ENABLED" -ForegroundColor White
Write-Host "WEB SEARCH            : ENABLED" -ForegroundColor White
Write-Host "TOOL VERIFICATION     : ENABLED" -ForegroundColor White
Write-Host "PASSWORD SECURITY     : ENABLED" -ForegroundColor White
Write-Host "HIDDEN REASONING      : HIDDEN" -ForegroundColor White
Write-Host "TYPEWRITER ANIMATION  : ENABLED" -ForegroundColor White
Write-Host "UPLOADS               : ENABLED" -ForegroundColor White
Write-Host "CHESS                 : ENABLED" -ForegroundColor White
Write-Host "COPY                  : ENABLED" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Starting dashboard..." -ForegroundColor Cyan
Write-Host ""

& $py ".\dashboard.py"

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "Dashboard exited with code: $exitCode" -ForegroundColor Yellow
Read-Host "Press ENTER to close"
