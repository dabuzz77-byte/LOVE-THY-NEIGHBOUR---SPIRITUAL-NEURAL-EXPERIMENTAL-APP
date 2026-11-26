@echo off
setlocal
cd /d "%~dp0"
if not exist data mkdir data
".venv\Scripts\python.exe" -m neural_app.rebuild_java
pause
