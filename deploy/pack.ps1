# Makes portfolio-upload.tar.gz in the project folder: the latest commit plus .env.production,
# in one file you upload through the browser SSH window. The easy way to deploy, see DEPLOY.md.
#
#   .\deploy\pack.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (git status --porcelain) {
    Write-Host "You have changes that are not committed. Commit them first, then pack again." -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path ".env.production")) {
    Write-Host ".env.production is missing (see DEPLOY.md)." -ForegroundColor Red
    exit 1
}

$Commit = git rev-parse --short HEAD
$Tar = Join-Path $env:TEMP "portfolio-$Commit.tar"
git archive --format=tar -o $Tar HEAD
if ($LASTEXITCODE -ne 0) { exit 1 }

# Add .env.production (never committed) next to the code, then compress.
$Out = "portfolio-upload.tar.gz"
& tar -rf $Tar .env.production
if ($LASTEXITCODE -ne 0) { exit 1 }
Remove-Item $Out -ErrorAction SilentlyContinue
& tar -czf $Out "@$Tar"
if ($LASTEXITCODE -ne 0) { exit 1 }
Remove-Item $Tar

Write-Host "Ready: $Out (commit $Commit). Upload it in the browser SSH window." -ForegroundColor Green
