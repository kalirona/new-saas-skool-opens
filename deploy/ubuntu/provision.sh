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

# ── Set up backup cron job ──────────────────────────────────────────────
log "Setting up daily backup cron job..."
cat > /etc/cron.d/learnhouse-backup <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Daily database backup at 3:00 AM
0 3 * * * ${APP_USER} LEARNHOUSE_SQL_CONNECTION_STRING="${LEARNHOUSE_SQL_CONNECTION_STRING}" BACKUP_DIR="${APP_DIR}/backups" bash ${APP_DIR}/deploy/scripts/backup-db.sh >> ${APP_DIR}/logs/backup.log 2>&1

# Daily storage backup at 4:00 AM
0 4 * * * ${APP_USER} BACKUP_DIR="${APP_DIR}/backups" bash ${APP_DIR}/deploy/scripts/backup-storage.sh >> ${APP_DIR}/logs/backup.log 2>&1

# Weekly backup verification every Sunday at 5:00 AM
0 5 * * 0 ${APP_USER} BACKUP_DIR="${APP_DIR}/backups" bash ${APP_DIR}/deploy/scripts/verify-backup.sh >> ${APP_DIR}/logs/backup.log 2>&1
EOF
chmod 644 /etc/cron.d/learnhouse-backup

# ── Deploy backup scripts ──────────────────────────────────────────────
log "Deploying backup scripts..."
cp -r deploy/scripts "$APP_DIR/deploy/"
chmod +x "$APP_DIR"/deploy/scripts/*.sh
chown -R "$APP_USER":"$APP_USER" "$APP_DIR/deploy/scripts"

# ── Start services ──────────────────────────────────────────────────────
log "Starting services with Docker Compose..."
cd "$APP_DIR"
docker compose --env-file .env -f docker-compose.yml up -d

# ── Tag the initial image as :prev for rollback support ─────────────────
docker tag learnhouse/api:latest learnhouse/api:prev 2>/dev/null || true

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
ExecReload=/usr/bin/docker compose --env-file .env -f docker-compose.yml pull
ExecReload=/usr/bin/docker compose --env-file .env -f docker-compose.yml up -d --no-deps api
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
log "  Backups:      ${APP_DIR}/backups/ (daily at 3AM DB, 4AM storage)"
log "  Rollback:     sudo bash deploy/rollback.sh"
log ""
log "  ** POST-PROVISION STEPS **"
log "  1. Edit ${APP_DIR}/.env — fill in secrets, API keys, OTel endpoints"
log "  2. Configure DNS A record pointing ${DOMAIN} to this server's IP"
log "  3. Verify monitoring: curl http://localhost:9000/api/v1/health"
log "  4. Test backup:      sudo bash ${APP_DIR}/deploy/scripts/verify-backup.sh"
log "  5. Run:              docker compose --env-file .env logs -f"
log "========================================"
