@echo off
setlocal
cd /d "%~dp0"
set "OUT=%~dp0build"
if not exist "%OUT%" mkdir "%OUT%"

javac -encoding UTF-8 -d "%OUT%" "%~dp0AllPrevUnifiedEngine.java"
if errorlevel 1 (
    echo.
    echo Build failed. Install a JDK and make sure javac is on PATH.
    pause
    exit /b 1
)

java -cp "%OUT%" AllPrevUnifiedEngine
endlocal
