param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$radarRoot = $PSScriptRoot
$radarLocal = Join-Path $radarRoot '.local'
New-Item -ItemType Directory -Path $radarLocal -Force | Out-Null
try {
    $radarStatus = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/status' -TimeoutSec 2
    if ($radarStatus.local -eq $true) {
        if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765' }
        Write-Output 'Radar läuft bereits: http://127.0.0.1:8765'
        exit 0
    }
} catch { }
$radarPython = $null
foreach ($radarCommand in @('python', 'python3', 'py')) {
    $radarCandidate = Get-Command $radarCommand -ErrorAction SilentlyContinue
    if ($radarCandidate -and $radarCandidate.Source -notlike '*Microsoft\WindowsApps*') {
        & $radarCandidate.Source -c 'import sys; assert sys.version_info >= (3, 11)' 2>$null
        if ($LASTEXITCODE -eq 0) { $radarPython = $radarCandidate.Source; break }
    }
}
if (-not $radarPython) {
    $radarBundled = 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1116-1220-0_26.1116.1220.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $radarBundled) { $radarPython = $radarBundled }
}
if (-not $radarPython) {
    $radarRuntime = Get-ChildItem -Path 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.*\dependencies\python\python.exe' -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
    if ($radarRuntime) { $radarPython = $radarRuntime.FullName }
}
if (-not $radarPython) { throw 'Python 3.11 oder neuer fehlt. Installiere kostenlos Python oder nutze die Codex-Laufzeit.' }
$radarProcess = Start-Process -FilePath $radarPython -ArgumentList @('"' + (Join-Path $radarRoot 'server.py') + '"') -WorkingDirectory $radarRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $radarLocal 'server.log') -RedirectStandardError (Join-Path $radarLocal 'error.log') -PassThru
$radarProcess.Id | Set-Content -LiteralPath (Join-Path $radarLocal 'server.pid')
for ($radarTry = 0; $radarTry -lt 30; $radarTry++) {
    Start-Sleep -Milliseconds 200
    try {
        $radarReady = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/status' -TimeoutSec 1
        if ($radarReady.local -eq $true) {
            if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765' }
            Write-Output 'Radar gestartet: http://127.0.0.1:8765 · Stoppen mit stop.ps1'
            exit 0
        }
    } catch { }
}
throw 'Radar startet nicht. Siehe .local/error.log; möglicherweise ist Port 8765 belegt.'
