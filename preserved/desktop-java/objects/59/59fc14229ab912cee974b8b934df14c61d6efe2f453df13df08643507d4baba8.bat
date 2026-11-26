@echo off
setlocal
cd /d "%~dp0"
set "OUT=%~dp0build\live-grid"
if not exist "%OUT%" mkdir "%OUT%"
javac -encoding UTF-8 -d "%OUT%" "%~dp0net\activeinference\beacon\translation\BinaryTernaryQutritTranslator.java" "%~dp0net\activeinference\beacon\translation\LiveTranslationWorkbench.java"
if errorlevel 1 (
    echo.
    echo Build failed. This version requires a JDK 9 or newer with javac on PATH.
    pause
    exit /b 1
)
java -cp "%OUT%" net.activeinference.beacon.translation.LiveTranslationWorkbench
endlocal