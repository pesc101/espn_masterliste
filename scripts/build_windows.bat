@echo off
setlocal

REM Convenience wrapper for users who prefer CMD over PowerShell.
powershell -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1"

endlocal
