@echo off
setlocal
cd /d "%~dp0"
set "CORE_PY="
if defined CORE_PYTHON if exist "%CORE_PYTHON%" set "CORE_PY=%CORE_PYTHON%"
if not defined CORE_PY for /d %%D in ("%LocalAppData%\Python\pythoncore-*") do if exist "%%~fD\python.exe" set "CORE_PY=%%~fD\python.exe"
if not defined CORE_PY for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do if exist "%%~fD\python.exe" set "CORE_PY=%%~fD\python.exe"
if not defined CORE_PY for /d %%D in ("%USERPROFILE%\AppData\Local\Python\pythoncore-*") do if exist "%%~fD\python.exe" set "CORE_PY=%%~fD\python.exe"
if not defined CORE_PY for /d %%D in ("%USERPROFILE%\AppData\Local\Programs\Python\Python*") do if exist "%%~fD\python.exe" set "CORE_PY=%%~fD\python.exe"
if not defined CORE_PY if defined PYTHONHOME if exist "%PYTHONHOME%\python.exe" set "CORE_PY=%PYTHONHOME%\python.exe"
if defined CORE_PY goto run_selected
where py >nul 2>nul
if not errorlevel 1 goto run_py
where python >nul 2>nul
if not errorlevel 1 goto run_python
echo Python 3.10 or newer with Tkinter is required. Install it from python.org.
echo Or set CORE_PYTHON to the full path of your Python executable.
pause
exit /b 1
:run_selected
"%CORE_PY%" "%~dp0core_interaction_system.py" %*
goto finished
:run_py
py -3 "%~dp0core_interaction_system.py" %*
goto finished
:run_python
python "%~dp0core_interaction_system.py" %*
:finished
if not errorlevel 1 exit /b 0
echo.
echo The app could not start. The error is shown above.
pause
exit /b 1
