@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

start "" backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend
timeout /t 3 /nobreak >nul

echo Starting public Cloudflare tunnel...
cloudflared.exe tunnel --url http://127.0.0.1:8000
