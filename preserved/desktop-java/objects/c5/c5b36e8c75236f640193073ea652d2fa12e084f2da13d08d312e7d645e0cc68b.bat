@echo off
TITLE Register God Mind Windows Service
cd /d "%~dp0"

echo ==================================================
echo  [WINDOWS SERVICE] Deploying God Mind Core Substrate
echo ==================================================

REM Ensure file exists locally
if not exist "GodMindWindowsDaemon.java" (
    echo [-] Error: GodMindWindowsDaemon.java not found in this directory.
    pause
    exit /b 1
)

REM Compile the daemon source
javac GodMindWindowsDaemon.java
if %errorlevel% neq 0 (
    echo [-] Compilation failed. Check syntax.
    pause
    exit /b %errorlevel%
)
echo [+] Compilation successful.

REM Clean up any old service instance
sc stop GodMindAgiCore >nul 2>&1
sc delete GodMindAgiCore >nul 2>&1
timeout /t 2 >nul

echo [+] Registering service with exact parameters...
sc create GodMindAgiCore binPath= "java -cp ""%~dp0"" GodMindWindowsDaemon" start= auto DisplayName= "God Mind AGI Sovereign Core"

echo [+] Service registration complete. Starting service...
net start GodMindAgiCore

echo ==================================================
echo [STATUS CHECK] Querying service state:
sc query GodMindAgiCore
pause