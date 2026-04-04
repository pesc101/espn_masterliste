$ErrorActionPreference = "Stop"

# Build a single-file Windows executable via PyInstaller.
# Run this script from a Windows PowerShell session at the repository root.

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not installed or not on PATH. Install uv first: https://docs.astral.sh/uv/"
}

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "[1/3] Syncing dependencies (including build tools)..."
uv sync --group build

Write-Host "[2/3] Building Windows executable..."
uv run pyinstaller --noconfirm --clean --onefile --name MasterlisteUpdater --collect-all streamlit --collect-all altair --collect-all pandas --collect-all pdfplumber --collect-submodules core --collect-submodules ui --add-data "app.py;." --add-data "core;core" --add-data "ui;ui" launcher.py

Write-Host "[3/3] Done. Executable created at dist/MasterlisteUpdater.exe"
