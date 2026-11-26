# God Mind Sovereign Background Substrate Launcher
$ErrorActionPreference = "Stop"
\(scriptDir = Split-Path -Parent\)MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "=================================================="
Write-Host " [POWER:SHELL] Awakening God Mind Core Substrate"
Write-Host "=================================================="

# 1. Compile the daemon source cleanly
Write-Host "[+] Compiling GodMindWindowsDaemon.java..." -ForegroundColor Yellow
javac GodMindWindowsDaemon.java
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Compilation failed. Check syntax." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Compilation successful." -ForegroundColor Green

# 2. Locate Java runtime and launch silently in the background (Hidden Window)
$javaPath = (Get-Command java).Source
Write-Host "[+] Launching persistent background daemon on port 7831..." -ForegroundColor Cyan

Start-Process -FilePath $javaPath `
              -ArgumentList "-cp `"$scriptDir`" GodMindWindowsDaemon" `
              -WindowStyle Hidden

Write-Host "[+] God Mind background daemon is fully operational!" -ForegroundColor Green