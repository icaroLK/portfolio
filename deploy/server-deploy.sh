#!/usr/bin/env bash
# Runs on the server as root, started by deploy.ps1. Not meant to be run on your PC.
#
#   server-deploy.sh <folder with the new code> <commit>
#
# Layout on the server:
#   /opt/portfolio/app        the code of the live commit (replaced on every deploy)
#   /opt/portfolio/.env       settings and secrets (from .env.production on your PC)
#   /opt/portfolio/data       db.sqlite3
#   /opt/portfolio/media      uploaded images and the resume
#   /opt/portfolio/logs       Django error log
#   /opt/portfolio/backups    daily backups, 14 days
set -euo pipefail

NEW="$1"
COMMIT="${2:-unknown}"
HOME_DIR=/opt/portfolio
APP_UID=10001  # the "app" user inside the Docker image (see Dockerfile)

mkdir -p "$HOME_DIR"/data "$HOME_DIR"/media "$HOME_DIR"/logs "$HOME_DIR"/backups
chown -R "$APP_UID:$APP_UID" "$HOME_DIR"/data "$HOME_DIR"/media "$HOME_DIR"/logs

if [ -f /tmp/portfolio.env ]; then
  install -m 600 /tmp/portfolio.env "$HOME_DIR/.env"  # readable by root only
  rm -f /tmp/portfolio.env
fi
if [ ! -f "$HOME_DIR/.env" ]; then
  echo "Missing $HOME_DIR/.env. Create .env.production on your PC (see DEPLOY.md) and deploy again."
  exit 1
fi

# Swap in the new code and keep the previous version next to it.
rm -rf "$HOME_DIR/app.previous"
if [ -d "$HOME_DIR/app" ]; then mv "$HOME_DIR/app" "$HOME_DIR/app.previous"; fi
mv "$NEW" "$HOME_DIR/app"
echo "$COMMIT" > "$HOME_DIR/app/REVISION"
cd "$HOME_DIR/app"

# The placeholder nginx page from before Sprint 7 holds port 8000. Gone after the first deploy.
docker rm -f test-page >/dev/null 2>&1 || true

docker compose build --pull
# --force-recreate: Caddy must pick up the Caddyfile from the new app folder too.
docker compose up -d --force-recreate --remove-orphans
docker image prune -f >/dev/null  # old images would slowly fill the 30 GB disk

# Nightly backup (systemd timer, like a cron job).
install -m 644 deploy/portfolio-backup.service deploy/portfolio-backup.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now portfolio-backup.timer >/dev/null 2>&1

# Wait until the site answers through Caddy, the same way Cloudflare will ask.
HOST=$(grep -E '^CANONICAL_HOST=' "$HOME_DIR/.env" | cut -d= -f2- | tr -d "\"' \r")
for _ in $(seq 1 30); do
  if curl -fsS -o /dev/null -H "Host: ${HOST:-localhost}" -H "X-Forwarded-Proto: https" \
      http://127.0.0.1:8000/healthz/; then
    echo "Live: commit $COMMIT is online."
    exit 0
  fi
  sleep 2
done

echo "The site did not answer after 60 seconds. Last log lines:"
docker compose logs --tail 40 web caddy
exit 1
