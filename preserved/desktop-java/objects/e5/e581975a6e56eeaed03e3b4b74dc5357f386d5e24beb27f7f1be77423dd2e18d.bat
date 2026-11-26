@echo off
setlocal
cd /d "%~dp0"
set "OUT=%~dp0build\translation"
if not exist "%OUT%" mkdir "%OUT%"
javac -encoding UTF-8 -d "%OUT%" "%~dp0net\activeinference\beacon\translation\BinaryTernaryQutritTranslator.java" "%~dp0net\activeinference\beacon\translation\TranslationWorkbench.java"
if errorlevel 1 (
    echo.
    echo Build failed. Install a JDK and ensure javac is on PATH.
    pause
    exit /b 1
)
java -cp "%OUT%" net.activeinference.beacon.translation.TranslationWorkbench
endlocal