#!/usr/bin/env bash
# ───────────────────────────────────────────────────────
# Database restore script.
# Usage:  ./scripts/restore-db.sh <backup-file> [db-url]
#
# The restore command is chosen based on the file extension:
#   .sql / .sql.gz  →  psql  (plain SQL dump)
#   .dump / .custom →  pg_restore  (custom-format dump)
#
# If no db-url is given, reads LEARNHOUSE_SQL_CONNECTION_STRING.
# ───────────────────────────────────────────────────────

set -euo pipefail

BACKUP_FILE="${1:-}"
DB_URL="${2:-${LEARNHOUSE_SQL_CONNECTION_STRING:-}}"

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup-file> [db-url]" >&2
  echo "ERROR: Backup file not found or not specified." >&2
  exit 1
fi

if [ -z "$DB_URL" ]; then
  echo "ERROR: No database URL provided. Set LEARNHOUSE_SQL_CONNECTION_STRING or pass as arg." >&2
  exit 1
fi

BASENAME=$(basename "$BACKUP_FILE")
EXT="${BASENAME##*.}"

echo "==> Restoring ${BACKUP_FILE} to ${DB_URL} ..."

case "$EXT" in
  gz)
    echo "==> Detected gzip-compressed SQL — using zcat + psql"
    zcat "$BACKUP_FILE" | psql "$DB_URL"
    ;;
  sql)
    echo "==> Detected plain SQL — using psql"
    psql -f "$BACKUP_FILE" "$DB_URL"
    ;;
  dump|custom)
    echo "==> Detected custom-format dump — using pg_restore"
    pg_restore --no-owner --no-acl --clean --if-exists -d "$DB_URL" "$BACKUP_FILE"
    ;;
  *)
    echo "==> Unknown format — trying pg_restore as fallback"
    pg_restore --no-owner --no-acl --clean --if-exists -d "$DB_URL" "$BACKUP_FILE" 2>/dev/null \
      || { echo "Falling back to psql ..."; psql -f "$BACKUP_FILE" "$DB_URL"; }
    ;;
esac

echo "==> Restore complete."
