# Restore Guide

This guide covers restoring LearnHouse from backups. Always test your backups
before you need them.

## Restore Testing (Recommended)

The `restore-test.sh` script validates that the latest backup can actually be
restored by booting a temporary PostgreSQL container:

```bash
# Test the most recent backup
bash deploy/scripts/restore-test.sh

# Test a specific backup file
bash deploy/scripts/restore-test.sh /path/to/backups/db_20260701_030000.sql.gz
```

This is safe — it never touches the production database. On success:

```
========================================
  Restore Test PASSED
========================================
  Backup:       db_20260701_030000.sql.gz (42M)
  Restore:      2340ms
  Verify:       512ms
  Tables:       87
========================================
```

## Database Restore

### From Latest Backup

```bash
# Find the newest backup
LATEST=$(ls -t /home/learnhouse/app/backups/db_*.sql.gz | head -1)

# Restore it
bash apps/api/scripts/restore-db.sh "$LATEST"
```

### From a Specific Backup

```bash
bash apps/api/scripts/restore-db.sh \
  /home/learnhouse/app/backups/db_20260701_030000.sql.gz \
  "postgresql+asyncpg://user:pass@host:5432/learnhouse"
```

### What the Restore Script Does

The script auto-detects the backup format:

| Extension | Command | Best For |
|-----------|---------|----------|
| `.sql.gz` | `zcat → psql` | Plain SQL, gzip-compressed |
| `.sql` | `psql -f` | Plain SQL, uncompressed |
| `.dump` / `.custom` | `pg_restore --clean` | Custom-format (parallel restore) |

### Migrations After Restore

After a restore, run any pending migrations:

```bash
# If using Alembic
alembic upgrade head
```

## Storage Restore

Uploaded content (files, images, videos) is backed up separately.

### From tar.zst (zstd compressed)

```bash
# Restore content to a temporary directory
zstd -d -c /home/learnhouse/app/backups/storage_20260701_040000.tar.zst | \
  tar -x -C /tmp/restore/

# Copy to content directory
cp -a /tmp/restore/content/* /home/learnhouse/app/content/

# Clean up
rm -rf /tmp/restore
```

### From tar.gz (gzip compressed)

```bash
tar -xzf /home/learnhouse/app/backups/storage_20260701_040000.tar.gz \
  -C /home/learnhouse/app/
```

## Full Disaster Recovery

Complete restore after total data loss:

```bash
# 1. Re-provision the server
sudo bash deploy/ubuntu/provision.sh

# 2. Restore database
bash apps/api/scripts/restore-db.sh /path/to/backups/db_latest.sql.gz

# 3. Restore storage
tar -xzf /path/to/backups/storage_latest.tar.gz -C /home/learnhouse/app/

# 4. Restart services
docker compose --env-file .env -f docker-compose.yml restart

# 5. Verify
curl -f http://localhost:9000/api/v1/health/ready
```

## Point-in-Time Recovery (PostgreSQL)

For PITR, you need WAL archiving. This is not set up by default. To enable:

```postgresql
-- In postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /mnt/backups/wal/%f'
```

Then restore with:

```bash
# Restore base backup, then apply WAL up to target time
pg_restore --clean -d learnhouse /mnt/backups/db_latest.dump
# Apply WAL files up to the desired point in time
```

## Troubleshooting Restores

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `role "learnhouse" does not exist` | Missing PostgreSQL role | Create role: `CREATE ROLE learnhouse LOGIN;` |
| `database "learnhouse" does not exist` | Missing database | Create database: `CREATE DATABASE learnhouse OWNER learnhouse;` |
| `pg_restore: error: could not execute query: ERROR: constraint` | Existing data conflicts | Add `--clean --if-exists` flags |
| Permission denied on backup file | File ownership | `chmod 644 /path/to/backup.sql.gz` |
| `connection refused` | DB not running | Check `docker ps` or `systemctl status postgresql` |
