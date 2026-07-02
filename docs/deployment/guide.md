# Deployment Guide

This guide covers all deployment methods for LearnHouse in production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start — Docker Compose](#quick-start--docker-compose)
3. [Ubuntu VPS (Automated)](#ubuntu-vps-automated)
4. [Ubuntu VPS (Manual)](#ubuntu-vps-manual)
5. [Coolify](#coolify)
6. [CloudPanel](#cloudpanel)
7. [Zero-Downtime Deployment](#zero-downtime-deployment)
8. [Rollback Procedure](#rollback-procedure)
9. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Prerequisites

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB (8 GB with AI) |
| Disk | 20 GB | 50 GB (SSD) |
| OS | Ubuntu 22.04+ | Ubuntu 24.04 LTS |
| Docker | 24+ | 27+ |
| PostgreSQL | 15+ | 16+ |
| Redis | 6+ | 7+ |

## Quick Start — Docker Compose

The fastest way to deploy:

```bash
# Clone the repo
git clone https://github.com/learnhouse/learnhouse.git
cd learnhouse

# Copy and edit environment
cp deploy/.env.example .env
# EDIT .env — fill in secrets, domain, API keys

# Start services
docker compose --env-file .env -f deploy/docker-compose.yml up -d

# Verify health
curl http://localhost:9000/api/v1/health/live
```

## Ubuntu VPS (Automated)

A provisioning script automates the entire setup:

```bash
# Run as root on a fresh Ubuntu 24.04 server
DOMAIN=learnhouse.example.com sudo bash deploy/ubuntu/provision.sh
```

This script:

- Installs Docker + Docker Compose
- Creates a `learnhouse` system user
- Generates secure secrets (JWT key, DB password)
- Sets up systemd service for auto-restart
- Configures log rotation (14-day retention)
- Enables UFW firewall (ports 22, 80, 443)
- Sets up cron jobs for daily database (3 AM) and storage (4 AM) backups
- Tags the initial Docker image as `:prev` for rollback support

### Post-Provision Steps

```bash
# 1. Edit the generated .env with your secrets
sudo nano /home/learnhouse/app/.env

# 2. Configure DNS → point A record to server IP

# 3. Get SSL certificate
sudo certbot --nginx -d learnhouse.example.com

# 4. Restart to pick up changes
sudo systemctl restart learnhouse

# 5. Verify
curl https://learnhouse.example.com/api/v1/health/live
```

## Ubuntu VPS (Manual)

```bash
# Install Docker
curl -fsSL https://get.docker.com | bash

# Clone and configure
git clone https://github.com/learnhouse/learnhouse.git /opt/learnhouse
cd /opt/learnhouse
cp deploy/.env.example .env

# Edit .env
nano .env

# Start
docker compose --env-file .env -f deploy/docker-compose.yml up -d
```

## Coolify

1. In Coolify, create a new **Docker Compose** resource
2. Copy the contents of `deploy/coolify/docker-compose.yml`
3. Set environment variables in Coolify's UI (see [Environment Variables](env-reference.md))
4. Deploy

## CloudPanel

1. Set up your CloudPanel server
2. Copy `deploy/cloudpanel/learnhouse.conf` to `/etc/nginx/sites-available/`
3. Enable the site:

   ```bash
   ln -s /etc/nginx/sites-available/learnhouse.conf /etc/nginx/sites-enabled/
   systemctl reload nginx
   ```

4. Run the API behind PM2 or Docker (see Docker Compose above)
5. CloudPanel manages SSL via Certbot automatically

## Zero-Downtime Deployment

The production Docker Compose (`deploy/docker-compose.yml`) supports zero-downtime
rolling updates:

```yaml
deploy:
  replicas: 2
  update_config:
    parallelism: 1    # Roll one container at a time
    delay: 10s        # Wait 10s between each
    order: start-first # Start new before stopping old
```

To deploy a new version:

```bash
# Pull latest image
docker compose --env-file .env -f deploy/docker-compose.yml pull api

# Rolling update (zero-downtime)
docker compose --env-file .env -f deploy/docker-compose.yml up -d --no-deps --scale api=2 api

# If using the deployment workflow
# Push to main → GitHub Actions builds and deploys automatically
```

## Rollback Procedure

If a deployment fails, roll back immediately:

```bash
# Automated rollback (restores :prev image)
sudo bash deploy/rollback.sh

# Roll back to a specific version
sudo bash deploy/rollback.sh v1.2.6
```

The rollback script:

1. Tags the current `:latest` as `:failed-<timestamp>`
2. Restores the previous `:prev` image as `:latest`
3. Redeploys with zero-downtime (rolling update)
4. Waits up to 60 seconds for the health check to pass
5. **If health check fails:** automatically restores the original image

## Post-Deployment Checklist

After deploying, verify every item:

```bash
# 1. Health endpoints
curl -f http://localhost:9000/api/v1/health/live      # → 200 alive
curl -f http://localhost:9000/api/v1/health/ready      # → 200 ready
curl http://localhost:9000/api/v1/health/database       # → 200 ok
curl http://localhost:9000/api/v1/health/redis          # → 200 ok
curl http://localhost:9000/api/v1/health/storage        # → 200 ok

# 2. API responds
curl http://localhost:9000/api/v1/health

# 3. Frontend loads (if deployed)
curl -I https://learnhouse.example.com | head -5

# 4. Logs look clean
docker compose --env-file .env logs --tail=100 api | grep ERROR

# 5. Monitoring endpoints
curl http://localhost:9000/api/v1/monitoring/metrics
curl http://localhost:9000/api/v1/monitoring/debug

# 6. Backup works
bash deploy/scripts/verify-backup.sh

# 7. Restore works (destructive — runs in temp container)
bash deploy/scripts/restore-test.sh
```
