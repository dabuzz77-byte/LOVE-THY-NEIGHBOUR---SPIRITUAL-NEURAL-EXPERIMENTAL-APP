param([Parameter(Mandatory=$true)][string]$RequestPath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$speechRequest = Get-Content -LiteralPath $RequestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $speaker.Rate = [int]$speechRequest.rate
    $speaker.SetOutputToWaveFile([string]$speechRequest.output)
    $speaker.Speak([string]$speechRequest.text)
} finally {
    $speaker.Dispose()
}
