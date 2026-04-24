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
        throw "Cannot find a usable Python interpreter. Install Python 3.11 or run 'py -3.11' manually."
    }
    $python = 'py -3.11'
}

Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue

$env:PYTHONPATH = $sitePackages
$env:PYTHONUNBUFFERED = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

Set-Location $apiRoot

Write-Host "Using Python: $python"
Write-Host "PYTHONPATH: $env:PYTHONPATH"
Write-Host "Starting Celery worker..."

if ($python -is [string] -and $python.Contains(' ')) {
    $parts = $python.Split(' ', 2)
    & $parts[0] $parts[1] -m celery -A app.http.app:celery worker --loglevel=info --pool=solo
} else {
    & $python -m celery -A app.http.app:celery worker --loglevel=info --pool=solo
}
