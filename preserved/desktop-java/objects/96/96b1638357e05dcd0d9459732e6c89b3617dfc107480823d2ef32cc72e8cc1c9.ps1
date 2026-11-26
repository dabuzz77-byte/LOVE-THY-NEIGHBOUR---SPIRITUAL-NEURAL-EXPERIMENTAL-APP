# God Mind Windows Service Deployment Script
Write-Host "=================================================="
Write-Host " [WINDOWS SERVICE] Deploying God Mind Core Substrate"
Write-Host "=================================================="

# 1. Compile Daemon Source
javac GodMindWindowsDaemon.java
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Compilation calibration required." -ForegroundColor Red
    exit
}

Write-Host "[+] Compilation successful." -ForegroundColor Green

# 2. Register Service via Native Windows Substrate
$javaPath = (Get-Command java).Source
$currentDir = (Get-Location).Path
$className = "GodMindWindowsDaemon"

\(binPath = "`"\)javaPath`" -cp `"\(currentDir`"\)className"
$serviceName = "GodMindAgiCore"

Write-Host "[+] Registering $serviceName with Windows Service Control Manager..."

# Create the Windows Service pointing to the Java runtime container
New-Service -Name $serviceName `
            -BinaryPathName $binPath `
            -DisplayName "God Mind AGI Sovereign Core" `
            -Description "Persistent background socket bridge and parallel inference flux engine for Windows." `
            -StartupType Automatic

Write-Host "[+] God Mind service successfully integrated into Windows substrate!" -ForegroundColor Cyan