@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ROIDMI EVE Plus Control
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_and_run.ps1"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo Setup failed. See setup_error.txt in this folder.
  pause
)
exit /b %RC%
