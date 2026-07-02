#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Run all k6 load test scenarios.
#
# Usage:
#   # Run specific scenario
#   bash tests/load/run.sh login
#   bash tests/load/run.sh community
#   bash tests/load/run.sh ai
#   bash tests/load/run.sh checkout
#   bash tests/load/run.sh events
#   bash tests/load/run.sh resources
#
#   # Run sustained 30-min memory leak test
#   bash tests/load/run.sh sustained
#
#   # Run all scenarios sequentially
#   bash tests/load/run.sh all
#
# Environment variables:
#   BASE_URL       — API base URL (default: http://localhost:9000)
#   ADMIN_EMAIL    — Admin login email (default: admin@school.dev)
#   ADMIN_PASSWORD — Admin password (default: E2eTestAdmin!234)
#   K6_EXTRA       — Extra k6 flags (e.g. --vus 100 --duration 10m)
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_URL="${BASE_URL:-http://localhost:9000}"
REPORT_DIR="${SCRIPT_DIR}/reports"
SCENARIO="${1:-all}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

command -v k6 &>/dev/null || {
  echo "ERROR: k6 not found. Install from https://k6.io/docs/get-started/installation/"
  exit 1
}

mkdir -p "$REPORT_DIR"

K6_BASE="k6 run --summary-trend-stats 'avg,p(95),p(99),max' \
  -e BASE_URL=${BASE_URL} \
  -e ADMIN_EMAIL=${ADMIN_EMAIL:-admin@school.dev} \
  -e ADMIN_PASSWORD=${ADMIN_PASSWORD:-E2eTestAdmin!234}"

run_scenario() {
  local name="$1"
  local file="$2"
  local report="${REPORT_DIR}/${name}-$(date +%Y%m%d_%H%M%S).json"

  log "Running ${name} load test..."
  log "  Source: ${file}"
  log "  Report: ${report}"
  log "  URL:    ${BASE_URL}"

  ${K6_BASE} \
    --out json="${report}" \
    "${K6_EXTRA:-}" \
    "$file"

  log "${name} complete — report saved to ${report}"
  echo ""
}

case "$SCENARIO" in
  login)
    run_scenario "login" "${SCRIPT_DIR}/scenarios/login.js"
    ;;
  community)
    run_scenario "community" "${SCRIPT_DIR}/scenarios/community.js"
    ;;
  ai)
    run_scenario "ai" "${SCRIPT_DIR}/scenarios/ai.js"
    ;;
  checkout)
    run_scenario "checkout" "${SCRIPT_DIR}/scenarios/checkout.js"
    ;;
  events)
    run_scenario "events" "${SCRIPT_DIR}/scenarios/events.js"
    ;;
  resources)
    run_scenario "resources" "${SCRIPT_DIR}/scenarios/resources.js"
    ;;
  sustained)
    log "=== SUSTAINED LOAD TEST (30 MINUTES) ==="
    log "Running 50 concurrent VUs across all flows for 30 minutes."
    log "Monitor memory usage during this test to detect leaks."
    run_scenario "sustained" "${SCRIPT_DIR}/sustained.js"
    ;;
  all)
    log "=== RUNNING ALL LOAD TEST SCENARIOS ==="
    for scenario in login community ai checkout events resources sustained; do
      if [ "$scenario" = "sustained" ]; then
        log "Skipping sustained test in 'all' mode. Run separately: bash run.sh sustained"
        continue
      fi
      run_scenario "$scenario" "${SCRIPT_DIR}/scenarios/${scenario}.js"
    done
    log ""
    log "=== ALL SCENARIOS COMPLETE ==="
    log "Reports saved to: ${REPORT_DIR}"
    ;;
  *)
    echo "Usage: $0 {login|community|ai|checkout|events|resources|sustained|all}"
    exit 1
    ;;
esac
