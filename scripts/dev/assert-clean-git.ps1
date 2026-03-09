$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '../..')
Set-Location $Root

$unstaged = git diff --name-only --ignore-cr-at-eol
$staged = git diff --cached --name-only --ignore-cr-at-eol

if ($unstaged -or $staged) {
    Write-Host "Advisory: working tree has local changes."
    Write-Host "Unstaged:"
    Write-Host $unstaged
    Write-Host "Staged:"
    Write-Host $staged
}
else {
    Write-Host "Working tree looks clean."
}
