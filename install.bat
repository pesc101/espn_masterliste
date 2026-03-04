@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  Masterliste Updater - Installation
echo ============================================================
echo.

:: ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python wurde nicht gefunden.
    echo.
    echo Bitte Python 3.10 oder neuer installieren:
    echo   https://www.python.org/downloads/
    echo.
    echo Wichtig: Beim Installieren den Haken bei
    echo   "Add Python to PATH" setzen!
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Python %PYVER% gefunden.
echo.

:: ── Create virtual environment ────────────────────────────────────────────────
if exist ".venv" (
    echo Virtuelle Umgebung bereits vorhanden, wird uebersprungen.
) else (
    echo Erstelle virtuelle Umgebung...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Konnte virtuelle Umgebung nicht erstellen.
        pause
        exit /b 1
    )
    echo Virtuelle Umgebung erstellt.
)
echo.

:: ── Install dependencies ──────────────────────────────────────────────────────
echo Installiere Abhaengigkeiten (kann einige Minuten dauern)...
echo.
call .venv\Scripts\activate.bat

python -m pip install --upgrade pip --quiet
python -m pip install streamlit pandas pdfplumber --quiet

if errorlevel 1 (
    echo [ERROR] Installation fehlgeschlagen.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Installation abgeschlossen!
echo  Starte die App mit:  run.bat
echo ============================================================
echo.
pause
