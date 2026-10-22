# PowerShell 5.1+; run from the extracted project's directory.
param(
    [string]$PythonExecutable,
    [switch]$DependenciesOnly
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function New-RandomHex([int]$ByteCount = 18) {
    $bytes = New-Object byte[] $ByteCount
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

# Prefer an existing working venv, rather than Windows Store aliases.
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    $candidates = if ($PythonExecutable) { @($PythonExecutable) } else { @('py', 'python') }
    $selectedPython = $null
    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate -ErrorAction SilentlyContinue)) { continue }
        try {
            & $candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { $selectedPython = $candidate; break }
        } catch { continue }
    }
    if (-not $selectedPython) {
        throw 'Working Python 3.11+ required. Install Python or use -PythonExecutable C:\path\to\python.exe.'
    }
    & $selectedPython -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create Python environment.' }
}
& .\.venv\Scripts\python.exe -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'The existing .venv requires Python 3.11+.' }
& .\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'pip install failed.' }
& .\.venv\Scripts\python.exe -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed.' }
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed.' }
if ($DependenciesOnly) {
    Write-Host 'Dependencies and unit tests ready. Docker and live database checks have not run.'
    return
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $dockerDirectories = @(
        "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin",
        "$env:ProgramFiles\Docker\Docker\resources\bin"
    )
    foreach ($directory in $dockerDirectories) {
        if (Test-Path (Join-Path $directory 'docker.exe')) { $env:PATH = "$directory;$env:PATH"; break }
    }
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Dependencies are ready. Install WSL 2 and Docker Desktop, start Docker, then rerun setup.ps1.'
}
$dockerOsType = docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop with Linux containers, then rerun setup.ps1.' }
if ($dockerOsType -ne 'linux') { throw 'Switch Docker Desktop to Linux containers, then rerun setup.ps1.' }

if (-not (Test-Path '.env')) {
    $adminPassword = New-RandomHex
    $appPassword = New-RandomHex
    @"
POSTGRES_PASSWORD=$adminPassword
APP_DB_PASSWORD=$appPassword
"@ | Set-Content -Path '.env' -Encoding ASCII
    Write-Host 'Created .env with unique random passwords (NOT for Git).' -ForegroundColor Green
} else {
    Write-Host 'Existing .env detected; passwords will not be changed.'
}

Write-Host 'Building and starting PostgreSQL 18...'
docker compose config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Invalid Compose configuration or missing environment variables.' }
docker compose up -d --build --wait
if ($LASTEXITCODE -ne 0) { throw 'docker compose up failed. See docker compose logs db.' }

Write-Host "`nVerifying database configuration and privileges..."
& .\verify.ps1

Write-Host "`nREADY. To demonstrate the application run: .\run.ps1" -ForegroundColor Green
Write-Host 'Username: seminar_user'
Write-Host 'Password: APP_DB_PASSWORD in the local .env (not printed in logs).'
Write-Host 'Keep .env private and do not add it to Git.'
