# Shared by the deploy scripts. Not run on its own.
#
# Your PC reaches the server through the same Cloudflare Tunnel that serves the site:
#   PC (ssh + cloudflared) -> Cloudflare (your login) -> tunnel -> portfolio-vm:22
# The server has no public IPv4 and no open ports, so this is the way in. See DEPLOY.md.

$ErrorActionPreference = "Stop"

$SshHost = "ssh.icarokucha.com"   # tunnel route to the server's SSH (DEPLOY.md, step 1)
$SshUser = "deploy"               # server user made for deploys (DEPLOY.md, step 1)
$SshKey = Join-Path $HOME ".ssh\icarokucha_deploy"

# Run everything from the project folder, wherever the script was started from.
Set-Location (Split-Path $PSScriptRoot -Parent)

$Cloudflared = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $Cloudflared) {
    Write-Host "cloudflared is not installed on this PC. See DEPLOY.md, step 1." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $SshKey)) {
    Write-Host "Deploy key $SshKey not found. See DEPLOY.md, step 1." -ForegroundColor Red
    exit 1
}

# A small ssh config, written fresh each run, so your own ~/.ssh/config is never touched.
# cloudflared opens your browser for the Cloudflare login when needed.
$SshConfig = Join-Path $env:TEMP "icarokucha-ssh-config"
@"
Host server
    HostName $SshHost
    User $SshUser
    IdentityFile "$SshKey"
    IdentitiesOnly yes
    ProxyCommand "$Cloudflared" access ssh --hostname %h
    StrictHostKeyChecking accept-new
    ServerAliveInterval 30
"@ | Set-Content -Encoding ascii $SshConfig

# Stops the script when a program like git or ssh fails
# (Windows PowerShell does not do this on its own for programs).
function Invoke-Step([string]$What, [scriptblock]$Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed: $What" -ForegroundColor Red
        exit 1
    }
}

# Run a command on the server. -Tty gives it a real terminal, so it can ask questions.
function Invoke-Server([string]$Command, [switch]$Tty) {
    if ($Tty) { & ssh -F $SshConfig -t server $Command } else { & ssh -F $SshConfig server $Command }
}

# Copy a file to or from the server ("server:/path" marks the server side).
function Copy-Server([string]$From, [string]$To) {
    & scp -F $SshConfig -q $From $To
}
