$ErrorActionPreference = 'Stop'
$radarPidFile = Join-Path $PSScriptRoot '.local/server.pid'
if (-not (Test-Path -LiteralPath $radarPidFile)) { Write-Output 'Kein gestarteter Radarprozess verzeichnet.'; exit 0 }
$radarProcessId = [int](Get-Content -LiteralPath $radarPidFile)
$radarProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $radarProcessId"
$radarExpected = Join-Path $PSScriptRoot 'server.py'
if ($radarProcess -and $radarProcess.CommandLine.Contains($radarExpected)) {
    Stop-Process -Id $radarProcessId
    Write-Output 'Radar und Datensammlung gestoppt.'
} elseif ($radarProcess) { throw 'Prozesskennung gehört inzwischen zu einem anderen Programm. Nichts gestoppt.' }
Remove-Item -LiteralPath $radarPidFile
