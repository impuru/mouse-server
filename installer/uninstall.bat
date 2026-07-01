@echo off
setlocal
title Remote Mouse Server - Uninstaller
set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%uninstall.ps1"
echo.
pause
