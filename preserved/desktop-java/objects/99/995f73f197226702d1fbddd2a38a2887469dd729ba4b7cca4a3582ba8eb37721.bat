@echo off
setlocal
cd /d "%~dp0"
set "OUT=%~dp0build"
set "GOD_ENGINE_JAVAC=javac"
set "GOD_ENGINE_JAVA=java"
if defined JAVA_HOME if exist "%JAVA_HOME%\bin\javac.exe" set "GOD_ENGINE_JAVAC=%JAVA_HOME%\bin\javac.exe"
if defined JAVA_HOME if exist "%JAVA_HOME%\bin\java.exe" set "GOD_ENGINE_JAVA=%JAVA_HOME%\bin\java.exe"
if not exist "%OUT%" mkdir "%OUT%"

"%GOD_ENGINE_JAVAC%" -encoding UTF-8 -d "%OUT%" "%~dp0GodSelfInteractEngine.java"
if errorlevel 1 (
    echo.
    echo Build failed. Install JDK 14 or newer and make sure javac is on PATH.
    pause
    exit /b 1
)

"%GOD_ENGINE_JAVA%" -cp "%OUT%" GodSelfInteractEngine
endlocal
