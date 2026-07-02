#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Restore testing script.
#
# Tests that the latest database backup can actually be restored
# to a temporary PostgreSQL instance (Docker). This is a destructive
# test that validates backup integrity end-to-end.
#
# WARNING: Creates a temporary Docker Postgres container. Does NOT
# touch the production database. The temp container is removed after
# the test.
#
# Usage:  ./deploy/scripts/restore-test.sh [backup-file]
#
# If no backup file is given, uses the most recent db backup in BACKUP_DIR.
#
# Environment variables:
#   BACKUP_DIR  — directory containing backup files (default: ./backups)
#   PG_IMAGE    — PostgreSQL image to use for the test (default: postgres:16-alpine)
#
# Exit codes:
#   0 — restore test passed
#   1 — restore test failed
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
PG_IMAGE="${PG_IMAGE:-postgres:16-alpine}"
TEST_CONTAINER="learnhouse-restore-test-$$"
TEST_DB="test_restore"
TEST_USER="testuser"
TEST_PASS="testpass"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
fail() { echo "FAILED: $*" >&2; exit 1; }
cleanup() {
  log "Cleaning up test container..."
  docker rm -f "$TEST_CONTAINER" 2>/dev/null || true
}
trap cleanup EXIT

# ── Find backup file ────────────────────────────────────────────────
if [ -n "${1:-}" ]; then
  BACKUP_FILE="$1"
else
  BACKUP_FILE=$(find "$BACKUP_DIR" -name 'db_*.sql.gz' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
  if [ -z "$BACKUP_FILE" ]; then
    BACKUP_FILE=$(find "$BACKUP_DIR" -name 'db_*.dump' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
  fi
fi

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  fail "No backup file found in ${BACKUP_DIR}"
fi

log "Testing restore of: ${BACKUP_FILE}"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup size: ${BACKUP_SIZE}"

# ── Start temporary PostgreSQL ─────────────────────────────────────
log "Starting temporary PostgreSQL container (${PG_IMAGE})..."
docker run -d \
  --name "$TEST_CONTAINER" \
  -e POSTGRES_USER="$TEST_USER" \
  -e POSTGRES_PASSWORD="$TEST_PASS" \
  -e POSTGRES_DB="$TEST_DB" \
  -p 0:5432 \
  "$PG_IMAGE" \
  -c 'max_connections=10'

# Wait for PG to be ready
for i in $(seq 1 30); do
  if docker exec "$TEST_CONTAINER" pg_isready -U "$TEST_USER" -d "$TEST_DB" &>/dev/null; then
    log "PostgreSQL ready after ${i}s"
    break
  fi
  if [ "$i" -eq 30 ]; then
    fail "PostgreSQL did not become ready within 30s"
  fi
  sleep 1
done

# Get the mapped port
TEST_PORT=$(docker inspect "$TEST_CONTAINER" --format '{{ (index (index .NetworkSettings.Ports "5432/tcp") 0).HostPort }}')
TEST_URL="postgresql://${TEST_USER}:${TEST_PASS}@localhost:${TEST_PORT}/${TEST_DB}"

# ── Restore ─────────────────────────────────────────────────────────
log "Restoring backup to test database..."
EXT="${BACKUP_FILE##*.}"

RESTORE_START=$(date +%s%N)
case "$EXT" in
  gz)
    zcat "$BACKUP_FILE" | docker exec -i "$TEST_CONTAINER" psql -U "$TEST_USER" -d "$TEST_DB"
    ;;
  dump|custom)
    docker exec -i "$TEST_CONTAINER" pg_restore --no-owner --no-acl --clean --if-exists -d "$TEST_DB" < "$BACKUP_FILE"
    ;;
  *)
    docker exec -i "$TEST_CONTAINER" psql -U "$TEST_USER" -d "$TEST_DB" < "$BACKUP_FILE"
    ;;
esac
RESTORE_DURATION_MS=$(( ($(date +%s%N) - RESTORE_START) / 1000000 ))

log "Restore completed in ${RESTORE_DURATION_MS}ms"

# ── Verify restore ──────────────────────────────────────────────────
log "Verifying restored data..."
VERIFY_START=$(date +%s%N)

# Check that key tables exist
TABLES=$(docker exec "$TEST_CONTAINER" psql -U "$TEST_USER" -d "$TEST_DB" -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;" 2>/dev/null | head -20)
TABLE_COUNT=$(echo "$TABLES" | grep -c '.' || true)

if [ "$TABLE_COUNT" -gt 0 ]; then
  log "Found ${TABLE_COUNT} tables in restored database"
else
  fail "No tables found in restored database — restore may have failed"
fi

# Check that alembic_version exists (migration metadata)
if docker exec "$TEST_CONTAINER" psql -U "$TEST_USER" -d "$TEST_DB" -t -c "SELECT 1 FROM alembic_version LIMIT 1;" &>/dev/null; then
  log "Migration version table found — restore looks complete"
else
  log "WARNING: alembic_version table not found (may not exist in this backup)"
fi

VERIFY_DURATION_MS=$(( ($(date +%s%N) - VERIFY_START) / 1000000 ))
log "Verification completed in ${VERIFY_DURATION_MS}ms"

# ── Summary ─────────────────────────────────────────────────────────
log ""
log "========================================"
log "  Restore Test PASSED"
log "========================================"
log "  Backup:       $(basename "$BACKUP_FILE") (${BACKUP_SIZE})"
log "  Restore:      ${RESTORE_DURATION_MS}ms"
log "  Verify:       ${VERIFY_DURATION_MS}ms"
log "  Tables:       ${TABLE_COUNT}"
log "  Container:    ${TEST_CONTAINER} (auto-removed)"
log "========================================"

exit 0
