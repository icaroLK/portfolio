#!/usr/bin/env bash
# Nightly backup of the database and uploads, kept on the server for 14 days.
# Started by the portfolio-backup timer. Run it by hand with:
#   sudo systemctl start portfolio-backup
set -euo pipefail

HOME_DIR="${PORTFOLIO_HOME:-/opt/portfolio}"
DEST="$HOME_DIR/backups"
FILE="$DEST/portfolio-$(date +%Y-%m-%d).tar.gz"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$DEST"

# SQLite's own backup copy: safe even while someone is saving in the admin
# (a plain cp could catch the file halfway through a write).
python3 - "$HOME_DIR/data/db.sqlite3" "$WORK/db.sqlite3" <<'PY'
import sqlite3, sys
source = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
target = sqlite3.connect(sys.argv[2])
source.backup(target)
target.close()
source.close()
PY

tar -czf "$FILE" -C "$WORK" db.sqlite3 -C "$HOME_DIR" media

# Keep 14 days: delete backups older than that.
find "$DEST" -name 'portfolio-*.tar.gz' -mtime +13 -delete

echo "Backup saved: $FILE ($(du -h "$FILE" | cut -f1))"
