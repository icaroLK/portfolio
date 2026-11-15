# Shared by the deploy scripts. Not run on its own.

$ErrorActionPreference = "Stop"

$Project = "icarokucha-portfolio"   # Google Cloud project ID (docs/INFRA.md)
$Vm = "portfolio-vm"

# Run everything from the project folder, wherever the script was started from.
Set-Location (Split-Path $PSScriptRoot -Parent)

# Stops the script when a command like git or gcloud fails
# (Windows PowerShell does not do this on its own for programs).
function Invoke-Step([string]$What, [scriptblock]$Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed: $What" -ForegroundColor Red
        exit 1
    }
}

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "The Google Cloud CLI (gcloud) is not installed. See DEPLOY.md, step 1." -ForegroundColor Red
    exit 1
}

# The server has no public IPv4, so every connection goes through Google's IAP tunnel.
$Zone = gcloud compute instances list --project $Project --filter "name=$Vm" --format "value(zone.basename())"
if ($LASTEXITCODE -ne 0 -or -not $Zone) {
    Write-Host "Could not find $Vm. Are you logged in? Run: gcloud auth login" -ForegroundColor Red
    exit 1
}
$Gcloud = @("--project", $Project, "--zone", $Zone, "--tunnel-through-iap")
