@echo off
setlocal
cd /d "%~dp0"
if exist "CLOUD_SESSION.json" del /f /q "CLOUD_SESSION.json"
if exist "xiaomi_captcha.jpg" del /f /q "xiaomi_captcha.jpg"
if exist "cloud_debug.log" del /f /q "cloud_debug.log"
echo Xiaomi Cloud session reset. AUTO_CONFIG.json was NOT deleted.
pause
