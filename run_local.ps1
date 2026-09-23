$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not (Test-Path "$ScriptDir\backend\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv "$ScriptDir\backend\venv"
    & "$ScriptDir\backend\venv\Scripts\pip.exe" install --upgrade pip
    & "$ScriptDir\backend\venv\Scripts\pip.exe" install -r "$ScriptDir\backend\requirements.txt"
}

if (-not (Test-Path "$ScriptDir\frontend\dist\index.html")) {
    Write-Host "Compiling frontend assets..."
    Set-Location "$ScriptDir\frontend"
    cmd /c "npm install && npm run build"
    Set-Location $ScriptDir
    New-Item -ItemType Directory -Path "$ScriptDir\backend\static" -Force | Out-Null
    Copy-Item -Path "$ScriptDir\frontend\dist\*" -Destination "$ScriptDir\backend\static" -Recurse -Force
}

Write-Host "Launching DocIntel Production Server on http://127.0.0.1:8000"
$env:PYTHONPATH = "$ScriptDir\backend"
& "$ScriptDir\backend\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend --reload
