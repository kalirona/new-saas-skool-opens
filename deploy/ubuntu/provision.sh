#!/usr/bin/env bash
# LearnHouse Ubuntu VPS Provisioning Script
# Tested on: Ubuntu 24.04 LTS
# Usage: sudo bash provision.sh
#
# Sets up: Docker, nginx, Let's Encrypt, PostgreSQL, Redis, and the app.

set -euo pipefail

# ── Configuration (edit these!) ─────────────────────────────────────────
DOMAIN="${DOMAIN:-learnhouse.example.com}"
APP_USER="${APP_USER:-learnhouse}"
APP_DIR="/home/${APP_USER}/app"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 32)}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}"

LOG_FILE="/var/log/learnhouse-provision.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# ── System updates ──────────────────────────────────────────────────────
log "Updating system packages..."
apt-get update -qq && apt-get upgrade -y -qq

# ── Docker ──────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  log "Installing Docker..."
  curl -fsSL https://get.docker.com | bash
  usermod -aG docker "${SUDO_USER:-$APP_USER}"
fi

if ! command -v docker compose &>/dev/null; then
  log "Installing Docker Compose plugin..."
  apt-get install -y -qq docker-compose-plugin
fi

# ── Create app user ─────────────────────────────────────────────────────
if ! id -u "$APP_USER" &>/dev/null; then
  log "Creating app user: ${APP_USER}..."
  useradd -m -s /bin/bash "$APP_USER"
  usermod -aG docker "$APP_USER"
fi

# ── Prepare app directory ──────────────────────────────────────────────
mkdir -p "$APP_DIR"/{content,logs,backups,deploy}
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

# ── Deploy .env ─────────────────────────────────────────────────────────
if [ ! -f "$APP_DIR/.env" ]; then
  log "Creating .env file..."
  cat > "$APP_DIR/.env" <<EOF
# LearnHouse Production Environment
LEARNHOUSE_SQL_CONNECTION_STRING=postgresql+asyncpg://learnhouse:${POSTGRES_PASSWORD}@127.0.0.1:5432/learnhouse
LEARNHOUSE_REDIS_CONNECTION_STRING=redis://127.0.0.1:6379/learnhouse
LEARNHOUSE_AUTH_JWT_SECRET_KEY=${JWT_SECRET}
LEARNHOUSE_SITE_NAME=LearnHouse
LEARNHOUSE_DOMAIN=${DOMAIN}
LEARNHOUSE_FRONTEND_DOMAIN=${DOMAIN}
LEARNHOUSE_PORT=9000
LEARNHOUSE_TENANCY=single
LEARNHOUSE_SSL=true
LEARNHOUSE_ALLOWED_ORIGINS=https://${DOMAIN}
LEARNHOUSE_EMAIL_PROVIDER=resend
LEARNHOUSE_SYSTEM_EMAIL_ADDRESS=noreply@${DOMAIN}
LEARNHOUSE_RESEND_API_KEY=
LEARNHOUSE_CONTENT_DELIVERY_TYPE=filesystem
LEARNHOUSE_LOG_LEVEL=INFO
LEARNHOUSE_DEVELOPMENT_MODE=false
POSTGRES_USER=learnhouse
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=learnhouse
EOF
  chown "$APP_USER":"$APP_USER" "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
fi

# ── Deploy docker-compose ──────────────────────────────────────────────
log "Deploying docker-compose.yml..."
cp deploy/docker-compose.yml "$APP_DIR/docker-compose.yml"
cp deploy/nginx.conf "$APP_DIR/nginx.conf"
chown "$APP_USER":"$APP_USER" "$APP_DIR/docker-compose.yml" "$APP_DIR/nginx.conf"

# ── Start services ──────────────────────────────────────────────────────
log "Starting services with Docker Compose..."
cd "$APP_DIR"
docker compose --env-file .env -f docker-compose.yml up -d

# ── Set up systemd for automatic restarts ───────────────────────────────
cat > /etc/systemd/system/learnhouse.service <<EOF
[Unit]
Description=LearnHouse (Docker Compose)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/docker compose --env-file .env -f docker-compose.yml up -d
ExecStop=/usr/bin/docker compose --env-file .env -f docker-compose.yml down
StandardOutput=journal
User=${APP_USER}

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable learnhouse.service

# ── Set up log rotation ─────────────────────────────────────────────────
cat > /etc/logrotate.d/learnhouse <<EOF
${APP_DIR}/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

# ── Firewall ────────────────────────────────────────────────────────────
if command -v ufw &>/dev/null; then
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw allow 22/tcp
  ufw --force enable
fi

# ── Summary ─────────────────────────────────────────────────────────────
log ""
log "========================================"
log "  LearnHouse Provisioning Complete!"
log "========================================"
log "  Domain:       https://${DOMAIN}"
log "  API:          http://localhost:9000"
log "  App Dir:      ${APP_DIR}"
log "  Docker:       cd ${APP_DIR} && docker compose ps"
log "  Logs:         ${APP_DIR}/logs/"
log "  Backups:      ${APP_DIR}/backups/"
log ""
log "  ** IMPORTANT **"
log "  1. Set LEARNHOUSE_AUTH_JWT_SECRET_KEY and LEARNHOUSE_RESEND_API_KEY in .env"
log "  2. Configure DNS A record pointing ${DOMAIN} to this server's IP"
log "  3. Run: docker compose --env-file .env logs -f"
log "========================================"
