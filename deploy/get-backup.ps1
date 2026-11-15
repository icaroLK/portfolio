# Downloads the newest backup from the server into the backups\ folder on your PC.
#
#   .\deploy\get-backup.ps1
#
# How to restore it is in DEPLOY.md.

. "$PSScriptRoot\common.ps1"

$Latest = gcloud compute ssh @Gcloud $Vm --command "ls -1t /opt/portfolio/backups/portfolio-*.tar.gz 2>/dev/null | head -1"
if ($LASTEXITCODE -ne 0 -or -not $Latest) {
    Write-Host "No backup on the server yet. The first one runs tonight at 00:30 (Brasilia time)." -ForegroundColor Yellow
    exit 1
}
$Latest = "$Latest".Trim()

New-Item -ItemType Directory -Force backups | Out-Null
Invoke-Step "downloading $Latest" { gcloud compute scp @Gcloud "${Vm}:$Latest" "backups\" }
Write-Host "Saved in backups\$(Split-Path $Latest -Leaf)" -ForegroundColor Green
