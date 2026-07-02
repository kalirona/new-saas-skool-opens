#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Storage backup script — archives uploaded content (local filesystem).
# For S3-backed storage, see the S3 bucket replication / versioning
# documentation — this script handles the local filesystem case.
#
# Usage:  ./deploy/scripts/backup-storage.sh
#
# Environment variables:
#   BACKUP_DIR       — where to store backups (default: ./backups)
#   STORAGE_DIR      — content storage directory (default: ./content)
#   RETENTION_DAYS   — days to keep backups (default: 30)
#   BACKUP_S3_DEST   — optional S3 destination (e.g. s3://bucket/backups/)
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
STORAGE_DIR="${STORAGE_DIR:-./content}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_DEST="${BACKUP_S3_DEST:-}"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
FILENAME="storage_${TIMESTAMP}.tar.zst"
LOCAL_PATH="${BACKUP_DIR}/${FILENAME}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
fail() { echo "FAILED: $*" >&2; exit 1; }

# ── Check prerequisites ─────────────────────────────────────────────
command -v tar &>/dev/null || fail "tar is required"
if ! command -v zstd &>/dev/null; then
  log "zstd not found, falling back to gzip"
  FILENAME="storage_${TIMESTAMP}.tar.gz"
  LOCAL_PATH="${BACKUP_DIR}/${FILENAME}"
  COMPRESS="gzip"
else
  COMPRESS="zstd"
fi

[ -d "$STORAGE_DIR" ] || fail "Storage directory not found: $STORAGE_DIR"

mkdir -p "$BACKUP_DIR"

# ── Backup ──────────────────────────────────────────────────────────
STORAGE_SIZE=$(du -sh "$STORAGE_DIR" 2>/dev/null | cut -f1 || echo "unknown")
log "Archiving ${STORAGE_DIR} (${STORAGE_SIZE}) -> ${LOCAL_PATH} ..."

if [ "$COMPRESS" = "zstd" ]; then
  tar -cf - -C "$(dirname "$STORAGE_DIR")" "$(basename "$STORAGE_DIR")" | zstd -3 -o "$LOCAL_PATH"
else
  tar -czf "$LOCAL_PATH" -C "$(dirname "$STORAGE_DIR")" "$(basename "$STORAGE_DIR")"
fi

BACKUP_SIZE=$(du -h "$LOCAL_PATH" | cut -f1)
log "Storage backup complete: ${BACKUP_SIZE}"

# ── Upload to S3 if configured ─────────────────────────────────────
if [ -n "$S3_DEST" ]; then
  log "Uploading to ${S3_DEST}${FILENAME} ..."
  if command -v aws &>/dev/null; then
    aws s3 cp "$LOCAL_PATH" "${S3_DEST}${FILENAME}"
  else
    log "WARNING: aws CLI not found, skipping S3 upload."
  fi
fi

# ── Retention ──────────────────────────────────────────────────────
log "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name 'storage_*' -mtime "+${RETENTION_DAYS}" -delete 2>/dev/null || true

log "Storage backup completed successfully."
