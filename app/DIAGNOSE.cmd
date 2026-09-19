@echo off
setlocal EnableExtensions
cd /d "%~dp0"
(
 echo === Windows ===
 ver
 echo.
 echo === py launcher ===
 where py 2^>nul
 py -0p 2^>nul
 echo.
 echo === python ===
 where python 2^>nul
 python --version 2^>nul
 echo.
 echo === venv ===
 if exist ".venv\Scripts\python.exe" ".venv\Scripts\python.exe" --version
) > "diagnostic.txt" 2>&1
type "diagnostic.txt"
echo.
echo Saved to diagnostic.txt
pause
