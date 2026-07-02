#!/usr/bin/env bash
# ───────────────────────────────────────────────────────
# Database backup script — pg_dump with S3 upload.
# Usage:  ./scripts/backup-db.sh [db-url] [s3-destination]
# Example: ./scripts/backup-db.sh \
#            "postgresql://user:pass@host:5432/db" \
#            "s3://my-bucket/backups/"
#
# If no arguments are given, reads LEARNHOUSE_SQL_CONNECTION_STRING
# and LEARNHOUSE_S3_API_* env vars.
# ───────────────────────────────────────────────────────

set -euo pipefail

DB_URL="${1:-${LEARNHOUSE_SQL_CONNECTION_STRING:-}}"
S3_DEST="${2:-}"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-./backups}"
FILENAME="db_${TIMESTAMP}.sql.gz"
LOCAL_PATH="${BACKUP_DIR}/${FILENAME}"

if [ -z "$DB_URL" ]; then
  echo "ERROR: No database URL provided. Set LEARNHOUSE_SQL_CONNECTION_STRING or pass as arg." >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "==> Backing up database to ${LOCAL_PATH} ..."
pg_dump --no-owner --no-acl --compress=9 -f "$LOCAL_PATH" "$DB_URL"
echo "==> Backup complete: $(du -h "$LOCAL_PATH" | cut -f1)"

if [ -n "$S3_DEST" ]; then
  echo "==> Uploading to ${S3_DEST}${FILENAME} ..."
  if command -v aws &>/dev/null; then
    aws s3 cp "$LOCAL_PATH" "${S3_DEST}${FILENAME}"
  else
    echo "WARNING: aws CLI not found, skipping S3 upload."
  fi
fi

# Retention: keep only last 30 days
find "$BACKUP_DIR" -name 'db_*.sql.gz' -mtime +30 -delete 2>/dev/null || true

echo "==> Done."
