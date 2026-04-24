$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiRoot = Join-Path $repoRoot 'imooc-llmops-api\imooc-llmops-api-master'
$sitePackages = Join-Path $apiRoot '.venv\Lib\site-packages'

if (-not (Test-Path $sitePackages)) {
    throw "Cannot find site-packages at: $sitePackages"
}

$python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'
if (-not (Test-Path $python)) {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($null -eq $pyCmd) {
        throw "Cannot find a usable Python interpreter. Install a trusted Python 3 interpreter or run 'py -3' manually."
    }
    $python = 'py -3.11'
}

$env:PYTHONPATH = $sitePackages
$env:PYTHONUNBUFFERED = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

Set-Location $apiRoot

Write-Host "Using Python: $python"
Write-Host "PYTHONPATH: $env:PYTHONPATH"
Write-Host "Initializing database..."

if ($python -is [string] -and $python.Contains(' ')) {
    $parts = $python.Split(' ', 2)
    & $parts[0] $parts[1] init_db.py
} else {
    & $python init_db.py
}
if ($LASTEXITCODE -ne 0) {
    throw "Database initialization failed."
}

Write-Host "Starting API server..."
if ($python -is [string] -and $python.Contains(' ')) {
    $parts = $python.Split(' ', 2)
    & $parts[0] $parts[1] -m app.http.app
} else {
    & $python -m app.http.app
}
