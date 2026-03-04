@echo off
setlocal enabledelayedexpansion

:: ── Check installation ────────────────────────────────────────────────────────
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] App ist noch nicht installiert.
    echo Bitte zuerst install.bat ausfuehren.
    echo.
    pause
    exit /b 1
)

:: ── Activate venv and launch ──────────────────────────────────────────────────
call .venv\Scripts\activate.bat

echo Starte Masterliste Updater...
echo Die App oeffnet sich gleich im Browser.
echo Dieses Fenster offen lassen - beim Schliessen stoppt die App.
echo.
echo Zum Beenden: Strg+C druecken
echo.

python -m streamlit run app.py --server.headless false
