# Puts the latest commit online at icarokucha.com.
#
#   .\deploy\deploy.ps1
#
# The server cannot download from GitHub (GitHub has no IPv6), so this script packs
# the code on your PC, copies it to the server and starts it there. See DEPLOY.md.

. "$PSScriptRoot\common.ps1"

# Only committed code goes online, so the live site always matches a commit.
if (git status --porcelain) {
    Write-Host "You have changes that are not committed. Commit them first, then deploy again." -ForegroundColor Yellow
    exit 1
}

$Commit = git rev-parse --short HEAD
$Archive = Join-Path $env:TEMP "portfolio-$Commit.tar.gz"
Invoke-Step "packing the code" { git archive --format=tar.gz -o $Archive HEAD }

Write-Host "Uploading commit $Commit..." -ForegroundColor Cyan
Invoke-Step "uploading the code" { gcloud compute scp @Gcloud $Archive "${Vm}:/tmp/portfolio.tar.gz" }
Remove-Item $Archive

# Server settings and secrets live in .env.production on your PC (never committed).
if (Test-Path ".env.production") {
    Invoke-Step "uploading .env.production" { gcloud compute scp @Gcloud ".env.production" "${Vm}:/tmp/portfolio.env" }
}

Write-Host "Building and restarting on the server (a few minutes the first time)..." -ForegroundColor Cyan
$Remote = "set -e; rm -rf /tmp/portfolio-new; mkdir /tmp/portfolio-new; " +
          "tar -xzf /tmp/portfolio.tar.gz -C /tmp/portfolio-new; rm /tmp/portfolio.tar.gz; " +
          "sudo bash /tmp/portfolio-new/deploy/server-deploy.sh /tmp/portfolio-new $Commit"
Invoke-Step "starting the site on the server" { gcloud compute ssh @Gcloud $Vm --command $Remote }

Write-Host "Done: https://icarokucha.com" -ForegroundColor Green
