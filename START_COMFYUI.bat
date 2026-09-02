@echo off
title ADA - ComfyUI

cd /d "C:\Users\ADMIN\Desktop\ComfyUI-master\ComfyUI-master"

if exist ".venv\Scripts\python.exe" (
    start "ADA ComfyUI" /min ".venv\Scripts\python.exe" main.py --cpu --listen 127.0.0.1 --port 8188
    exit /b
)

if exist "venv\Scripts\python.exe" (
    start "ADA ComfyUI" /min "venv\Scripts\python.exe" main.py --cpu --listen 127.0.0.1 --port 8188
    exit /b
)

py -3.12 main.py --cpu --listen 127.0.0.1 --port 8188
