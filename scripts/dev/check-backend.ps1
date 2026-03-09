$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '../..')
Set-Location $Root

pre-commit run --all-files

$status = git status --porcelain
if ($status) {
    Write-Host ""
    Write-Host "pre-commit modified files or the git tree is not clean."
    Write-Host "Review the diff, stage changes, amend/commit, and rerun this script."
    git status --short
    exit 1
}

Set-Location (Join-Path $Root 'backend')
mypy .
pytest tests/
