@echo off
setlocal
cd /d "%~dp0"
set "OUT=%~dp0build\script-flux-bus"
if not exist "%OUT%" mkdir "%OUT%"

javac -encoding UTF-8 -d "%OUT%" "%~dp0net\activeinference\beacon\translation\BinaryTernaryQutritTranslator.java" "%~dp0net\activeinference\beacon\translation\ScriptFluxBusWorkbench.java"
if errorlevel 1 (
    echo.
    echo Build failed. Install a JDK 9 or newer and make sure javac is on PATH.
    pause
    exit /b 1
)

java -cp "%OUT%" net.activeinference.beacon.translation.ScriptFluxBusWorkbench
endlocal
