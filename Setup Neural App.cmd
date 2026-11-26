@echo off
setlocal
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" tools\fetch_java_dependencies.py
if errorlevel 1 goto failed
if not exist data mkdir data
".venv\Scripts\python.exe" -m neural_app.rebuild_java
if errorlevel 1 goto failed
echo Setup completed. Run Start Neural App.cmd.
pause
exit /b 0
:failed
echo Setup stopped. Read the error above before retrying.
pause
exit /b 1
