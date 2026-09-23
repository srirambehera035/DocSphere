@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

if not exist "backend\venv\Scripts\python.exe" (
    echo Setting up Python virtual environment...
    python -m venv backend\venv
    backend\venv\Scripts\pip.exe install --upgrade pip
    backend\venv\Scripts\pip.exe install -r backend\requirements.txt
)

if not exist "frontend\dist\index.html" (
    echo Building frontend distribution...
    cd frontend
    call npm install
    call npm run build
    cd ..
    mkdir backend\static 2>nul
    xcopy /s /e /y frontend\dist\* backend\static\
)

echo Starting DocIntel server at http://127.0.0.1:8000
set PYTHONPATH=%cd%\backend
backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend --reload
