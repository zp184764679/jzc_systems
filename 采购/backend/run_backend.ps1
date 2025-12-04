# Runs on Windows PowerShell
# Creates venv, installs deps, and runs Flask
param(
    [string]$PythonPath = "python"
)

Set-Location $PSScriptRoot
$ErrorActionPreference = "Stop"

if (!(Test-Path ".venv")) {
    & $PythonPath -m venv .venv
}

# Unblock script execution for current user if needed
try {
    & .\.venv\Scripts\Activate.ps1
} catch {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    & .\.venv\Scripts\Activate.ps1
}

pip install -r requirements.txt

$env:FLASK_APP="app.py"
flask run --debug
