# Runs a manage.py command on the live server. Examples:
#
#   .\deploy\manage.ps1 createsuperuser     # create your admin login
#   .\deploy\manage.ps1 axes_reset          # unlock the admin login after too many wrong passwords
#   .\deploy\manage.ps1 changepassword icaro

. "$PSScriptRoot\common.ps1"

if ($args.Count -eq 0) {
    Write-Host "Say which command to run, for example: .\deploy\manage.ps1 createsuperuser" -ForegroundColor Yellow
    exit 1
}

$Command = $args -join " "
$Remote = "cd /opt/portfolio/app && sudo docker compose exec web python manage.py $Command"
Invoke-Step "running manage.py $Command" { Invoke-Server $Remote -Tty }
