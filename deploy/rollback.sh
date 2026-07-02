#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# LearnHouse Rollback Procedure
# Reverts to the previous Docker image tag in case of a bad deploy.
#
# Prerequisites:
#   - Docker images tagged with :latest and :prev on the same host
#   - .env file in APP_DIR
#
# Usage:
#   # After a failed deploy, immediately roll back:
#   sudo bash deploy/rollback.sh
#
#   # Roll back to a specific version:
#   sudo bash deploy/rollback.sh v1.2.6
#
# What it does:
#   1. Tags the current :latest as :failed-<timestamp>
#   2. Tags the target image (previous or explicit) as :latest
#   3. Re-runs docker compose up -d with the restored tag
#   4. Waits for health checks to pass (up to 60s)
#   5. If health check fails, restores the failed image and aborts
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

APP_DIR="${APP_DIR:-/home/learnhouse/app}"
COMPOSE_FILE="${COMPOSE_FILE:-${APP_DIR}/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-${APP_DIR}/.env}"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-learnhouse}"
HEALTH_URL="${HEALTH_URL:-http://localhost:9000/api/v1/health/live}"
IMAGE="${IMAGE:-learnhouse/api}"
ROLLBACK_TAG="${1:-prev}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
fail() { log "FAILED: $*"; exit 1; }

# ── Sanity checks ────────────────────────────────────────────────────
command -v docker &>/dev/null || fail "Docker is not installed."
[ -f "$COMPOSE_FILE" ] || fail "Compose file not found: $COMPOSE_FILE"
[ -f "$ENV_FILE" ] || fail "Environment file not found: $ENV_FILE"

# ── Determine the image to roll back to ──────────────────────────────
if [ "$ROLLBACK_TAG" = "prev" ]; then
  TARGET_IMAGE="${IMAGE}:prev"
  log "Rolling back to previous image (${TARGET_IMAGE})"
else
  TARGET_IMAGE="${IMAGE}:${ROLLBACK_TAG}"
  log "Rolling back to specific version: ${TARGET_IMAGE}"
fi

docker image inspect "$TARGET_IMAGE" &>/dev/null \
  || fail "Target image does not exist: $TARGET_IMAGE"

# ── Preserve current image, then swap tags ───────────────────────────
FAILED_TAG="failed-$(date -u +%Y%m%d_%H%M%S)"
log "Tagging current :latest as :${FAILED_TAG}"
docker tag "${IMAGE}:latest" "${IMAGE}:${FAILED_TAG}" 2>/dev/null || true

log "Tagging ${ROLLBACK_TAG} as :latest"
docker tag "$TARGET_IMAGE" "${IMAGE}:latest"

# ── Redeploy ─────────────────────────────────────────────────────────
log "Re-deploying with rolled-back image..."
cd "$APP_DIR"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --no-deps api

# ── Wait for health ──────────────────────────────────────────────────
log "Waiting up to 60s for health check to pass..."
for i in $(seq 1 60); do
  if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    log "Health check passed after ${i}s"
    log "Rollback completed successfully."
    exit 0
  fi
  sleep 1
done

# ── Health check failed — restore original ──────────────────────────
log "HEALTH CHECK FAILED after 60s! Restoring original image..."
docker tag "${IMAGE}:${FAILED_TAG}" "${IMAGE}:latest" 2>/dev/null || true
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --no-deps api

log "ORIGINAL IMAGE RESTORED. Rollback aborted."
log "Investigate the issue, then retry the rollback."
exit 1
