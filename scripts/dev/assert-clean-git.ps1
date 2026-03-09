$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '../..')
Set-Location $Root

$status = git status --porcelain
if ($status) {
    Write-Host "Git working tree is not clean."
    git status --short
    exit 1
}

Write-Host "Git working tree is clean."
