$ErrorActionPreference = 'Stop'
$appDirectory = $PSScriptRoot
$moduleDirectory = Split-Path -Parent $appDirectory
$connectionPath = Join-Path $appDirectory 'data\connection.json'
$runtimePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (!(Test-Path -LiteralPath $runtimePython)) {
    $runtimePython = (Get-Command python -ErrorAction Stop).Source
}
$appPort = 7851
if (Test-Path -LiteralPath $connectionPath) {
    $existing = Get-Content -LiteralPath $connectionPath -Raw | ConvertFrom-Json
    $appPort = $existing.port
    try {
        $headers = @{ Authorization = "Bearer $($existing.token)" }
        $runningApp = Invoke-RestMethod -Uri "http://127.0.0.1:$appPort/api/state" -Headers $headers -TimeoutSec 2
        if ($runningApp.name -eq 'Postscarcity Observatory' -and $runningApp.version -eq '4.0' -and $runningApp.module_root -eq $moduleDirectory) {
            Start-Process "http://127.0.0.1:$appPort/#flux"
            exit
        }
    } catch { }
}
$portReady = $false
for ($candidate = $appPort; $candidate -lt [Math]::Min(65536, $appPort + 20); $candidate++) {
    $tcpProbe = $null
    $udpProbe = $null
    try {
        $tcpProbe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $candidate)
        $tcpProbe.Start()
        $udpProbe = [System.Net.Sockets.UdpClient]::new()
        $udpProbe.ExclusiveAddressUse = $true
        $udpProbe.Client.Bind([System.Net.IPEndPoint]::new([System.Net.IPAddress]::Loopback, $candidate))
        $appPort = $candidate
        $portReady = $true
        break
    } catch { }
    finally {
        if ($tcpProbe) { $tcpProbe.Stop() }
        if ($udpProbe) { $udpProbe.Close() }
    }
}
if (!$portReady) { throw 'No available local port was found near the configured port.' }
$ollamaExecutable = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
if (Test-Path -LiteralPath $ollamaExecutable) {
    try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2 }
    catch {
        $env:OLLAMA_NOPRUNE = 'true'
        Start-Process -FilePath $ollamaExecutable -ArgumentList 'serve' -WindowStyle Hidden
    }
}
$dataDirectory = Join-Path $appDirectory 'data'
New-Item -ItemType Directory -Path $dataDirectory -Force | Out-Null
$arguments = '"' + (Join-Path $appDirectory 'app.py') + '" --no-browser --port ' + $appPort
Start-Process -FilePath $runtimePython -ArgumentList $arguments -WorkingDirectory $moduleDirectory -WindowStyle Hidden -RedirectStandardOutput (Join-Path $dataDirectory 'runtime.log') -RedirectStandardError (Join-Path $dataDirectory 'runtime-errors.log')
for ($attempt = 0; $attempt -lt 25; $attempt++) {
    Start-Sleep -Milliseconds 500
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$appPort/" -TimeoutSec 2 -UseBasicParsing
        if ($response.StatusCode -eq 200) { Start-Process "http://127.0.0.1:$appPort/#flux"; exit }
    } catch { }
}
$launchError = 'The runtime did not start. See graphical_app/data/runtime-errors.log in your Postscarcity folder.'
Write-Host $launchError
try { $null = (New-Object -ComObject WScript.Shell).Popup($launchError, 0, 'Postscarcity Observatory', 16) } catch { }
exit 1
