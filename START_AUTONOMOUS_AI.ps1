$ErrorActionPreference = "Stop"

$Project = "C:\Users\ADMIN\Desktop\ada_test_project"

Set-Location $Project

$Python = "$Project\.venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python.exe"
}

& $Python "$Project\desktop_app\local_app.py"
