@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run Setup Neural App.cmd first.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" desktop.py
if errorlevel 1 pause
