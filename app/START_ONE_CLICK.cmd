@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "%~dp0INSTALL_PILLOW_ONLY.cmd"
exit /b %ERRORLEVEL%
