$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '../..')
Set-Location (Join-Path $Root 'backend')

Write-Host "Running backend validation..."
Write-Host "Optional manual Python formatting step if Ruff is installed: ruff check . && ruff format ."

mypy .
pytest tests/
