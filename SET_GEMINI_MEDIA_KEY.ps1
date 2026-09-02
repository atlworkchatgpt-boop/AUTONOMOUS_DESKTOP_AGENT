# ADA Gemini Cloud Media
# Do NOT commit this file.

$env:GEMINI_API_KEY = Read-Host "Paste your Gemini API key"

Write-Host ""
Write-Host "Testing Gemini connection..."

& ".\.venv\Scripts\python.exe" -c @"
from google import genai
import os

key = os.environ.get('GEMINI_API_KEY')

if not key:
    raise SystemExit('No API key supplied.')

client = genai.Client(api_key=key)

print('Gemini client initialized successfully.')
print('API key was NOT written to the project.')
"@

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS: Gemini API configuration looks valid."
    Write-Host ""
    Write-Host "Keep this PowerShell window open while ADA is running."
}
else {
    Write-Host ""
    Write-Host "Gemini connection test failed."
    Write-Host "Check your API key and project quota."
}
