$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    throw 'Run setup.ps1 first.'
}
& .\.venv\Scripts\python.exe -m src.app
exit $LASTEXITCODE
