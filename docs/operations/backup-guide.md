# Backup Guide

LearnHouse provides automated backup scripts for both database and uploaded
content (storage files). Backups are compressed, retained for 30 days by
default, and optionally uploaded to S3.

## Backup Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  PostgreSQL DB   │────>│  backup-db.sh    │────>│ Local .sql.gz   │
│  (pg_dump)       │     │  Daily @ 3AM     │     │ or S3 bucket    │
└─────────────────┘     └──────────────────┘     └─────────────────┘

┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Content Storage │────>│ backup-storage.sh│────>│ Local .tar.zst  │
│  (filesystem)    │     │  Daily @ 4AM     │     │ or S3 bucket    │
└─────────────────┘     └──────────────────┘     └─────────────────┘

┌─────────────────┐     ┌──────────────────┐
│  Backup Archive  │────>│ verify-backup.sh │
│  (local/S3)      │     │  Weekly @ 5AM Sun│
└─────────────────┘     └──────────────────┘
```

## Quick Start

```bash
# Verify all backups are healthy
bash deploy/scripts/verify-backup.sh

# Check last backup time
ls -la /home/learnhouse/app/backups/
```

## Manual Backup

### Database

```bash
# Basic backup (uses env vars)
bash apps/api/scripts/backup-db.sh

# Custom destination
bash apps/api/scripts/backup-db.sh \
  "postgresql://user:pass@host:5432/db" \
  "s3://my-bucket/backups/"
```

### Storage (Uploaded Content)

```bash
# Backup local content
bash deploy/scripts/backup-storage.sh

# With custom paths
BACKUP_DIR=/mnt/backups \
STORAGE_DIR=/var/lib/learnhouse/content \
bash deploy/scripts/backup-storage.sh
```

## Automated Backups

When deployed via the provision script (`deploy/ubuntu/provision.sh`), the
following cron jobs are registered:

| Time | Script | Description |
|------|--------|-------------|
| Daily 3:00 AM | `backup-db.sh` | PostgreSQL dump (compressed) |
| Daily 4:00 AM | `backup-storage.sh` | Content files archive |
| Weekly Sun 5:00 AM | `verify-backup.sh` | Integrity check |

To add these manually on any server:

```bash
# Install cron jobs
sudo cp deploy/scripts/backup-db.sh /etc/cron.daily/learnhouse-db
sudo cp deploy/scripts/backup-storage.sh /etc/cron.daily/learnhouse-storage
sudo cp deploy/scripts/verify-backup.sh /etc/cron.weekly/learnhouse-verify
sudo chmod +x /etc/cron.daily/* /etc/cron.weekly/*
```

Or using systemd timers (preferred for Docker deployments):

```bash
# Example systemd timer for DB backup
cat > /etc/systemd/system/learnhouse-backup-db.service <<'EOF'
[Unit]
Description=LearnHouse Database Backup

[Service]
Type=oneshot
ExecStart=/usr/bin/docker exec $(docker ps -q -f name=api) bash /app/scripts/backup-db.sh
EOF

cat > /etc/systemd/system/learnhouse-backup-db.timer <<'EOF'
[Unit]
Description=Daily LearnHouse DB Backup

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now learnhouse-backup-db.timer
```

## S3 Backup Upload

Both backup scripts support optional S3 upload. Configure via `.env`:

```ini
LEARNHOUSE_BACKUP_S3_DEST=s3://my-bucket/learnhouse-backups/
```

Or pass at runtime:

```bash
BACKUP_S3_DEST=s3://my-bucket/learnhouse-backups/ bash deploy/scripts/backup-storage.sh
```

**Requirements:** AWS CLI installed and configured (`aws configure`).

## Retention Policy

- **Local backups:** 30 days (configurable via `LEARNHOUSE_BACKUP_RETENTION_DAYS`)
- **S3 backups:** Configure S3 lifecycle rules separately

## Backup Verification

Run the verification script to check integrity:

```bash
bash deploy/scripts/verify-backup.sh
```

This checks:

- ✅ Gzip/zstd integrity of each backup file
- ✅ Backup freshness (alerts if newest > 26 hours old)
- ✅ Disk usage report

Expected output:

```
========================================
  Backup Verification Report
  Directory: ./backups
========================================
── Database Backups ────────────────────
  OK: DB: db_20260702_030000.sql.gz (42M, 9h old)
  OK: DB: db_20260701_030000.sql.gz (41M, 33h old) — STALE
── Storage Backups ─────────────────────
  OK: Storage: storage_20260702_040000.tar.zst (156M, 8h old)
── Disk Usage ──────────────────────────
  Total backup size on disk: 273M

RESULT: ALL CHECKS PASSED
```
