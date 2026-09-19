@echo off
setlocal
cd /d "%~dp0"
if exist "AUTO_CONFIG.json" del /f /q "AUTO_CONFIG.json"
if exist "CLOUD_SESSION.json" del /f /q "CLOUD_SESSION.json"
if exist "xiaomi_captcha.jpg" del /f /q "xiaomi_captcha.jpg"
echo Saved credentials and Xiaomi Cloud session deleted.
pause
