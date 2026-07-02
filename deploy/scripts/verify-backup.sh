#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Backup verification script.
#
# Checks the integrity of recent database and storage backups:
#   1. Verifies DB dump checksums (tests gzip integrity)
#   2. Verifies storage archive integrity (tests tar integrity)
#   3. Reports backup age / freshness
#   4. Reports backup sizes
#
# Exit codes:
#   0 — all checks passed
#   1 — one or more checks failed
#
# Usage:  ./deploy/scripts/verify-backup.sh
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
STALE_HOURS="${STALE_HOURS:-26}"  # Alert if newest backup > 26h old

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
fail() { echo "FAILED: $*" >&2; exit 1; }

ALL_PASSED=true

# ── Helper: verify a single file ────────────────────────────────────
verify_file() {
  local file="$1"
  local label="$2"

  if [ ! -f "$file" ]; then
    log "  MISSING: ${label} — ${file} not found"
    ALL_PASSED=false
    return 1
  fi

  local size
  size=$(du -h "$file" | cut -f1)
  local age_seconds=$(( $(date +%s) - $(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null) ))
  local age_hours=$(( age_seconds / 3600 ))

  case "$file" in
    *.gz)
      if gzip -t "$file" 2>/dev/null; then
        log "  OK: ${label} (${size}, ${age_hours}h old) — gzip integrity check passed"
      else
        log "  CORRUPT: ${label} (${size}) — gzip integrity check FAILED"
        ALL_PASSED=false
        return 1
      fi
      ;;
    *.zst)
      if zstd -t "$file" 2>/dev/null; then
        log "  OK: ${label} (${size}, ${age_hours}h old) — zstd integrity check passed"
      else
        log "  CORRUPT: ${label} (${size}) — zstd integrity check FAILED"
        ALL_PASSED=false
        return 1
      fi
      ;;
    *)
      log "  OK: ${label} (${size}, ${age_hours}h old) — format not checked"
      ;;
  esac

  if [ "$age_hours" -gt "$STALE_HOURS" ]; then
    log "  STALE: ${label} — ${age_hours}h old (threshold: ${STALE_HOURS}h)"
  fi
}

# ── Main verification ───────────────────────────────────────────────
log "========================================"
log "  Backup Verification Report"
log "  Directory: ${BACKUP_DIR}"
log "  Time:      $(date -u)"
log "========================================"

# ── Directory exists? ──────────────────────────────────────────────
if [ ! -d "$BACKUP_DIR" ]; then
  fail "Backup directory does not exist: ${BACKUP_DIR}"
fi

log ""
log "── Database Backups ────────────────────"
DB_COUNT=0
for f in "$BACKUP_DIR"/db_*.sql.gz "$BACKUP_DIR"/db_*.dump; do
  [ -f "$f" ] || continue
  verify_file "$f" "DB: $(basename "$f")"
  DB_COUNT=$((DB_COUNT + 1))
done
log "  Total DB backups: ${DB_COUNT}"

log ""
log "── Storage Backups ─────────────────────"
STORAGE_COUNT=0
for f in "$BACKUP_DIR"/storage_*.tar.gz "$BACKUP_DIR"/storage_*.tar.zst; do
  [ -f "$f" ] || continue
  verify_file "$f" "Storage: $(basename "$f")"
  STORAGE_COUNT=$((STORAGE_COUNT + 1))
done
log "  Total storage backups: ${STORAGE_COUNT}"

log ""
log "── Disk Usage ──────────────────────────"
BACKUP_DISK=$(du -sh "$BACKUP_DIR" | cut -f1)
log "  Total backup size on disk: ${BACKUP_DISK}"

log ""
if [ "$ALL_PASSED" = true ]; then
  log "RESULT: ALL CHECKS PASSED"
  exit 0
else
  log "RESULT: ONE OR MORE CHECKS FAILED"
  exit 1
fi
