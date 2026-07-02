# Troubleshooting Guide

Common issues, their causes, and solutions.

## Table of Contents

1. [Application Won't Start](#application-wont-start)
2. [Database Issues](#database-issues)
3. [Redis Issues](#redis-issues)
4. [Performance Problems](#performance-problems)
5. [Monitoring & Logs](#monitoring--logs)
6. [Backup & Restore](#backup--restore)
7. [SSL / HTTPS](#ssl--https)
8. [Authentication Issues](#authentication-issues)
9. [Storage / File Upload Issues](#storage--file-upload-issues)
10. [AI Feature Issues](#ai-feature-issues)

---

## Application Won't Start

### Symptom: `docker compose up -d` exits immediately

```bash
# Check logs
docker compose logs api

# Common causes:
# - Database not ready (connection refused)
# - Redis not ready
# - Missing required env vars
```

**Fix:** Ensure `db` and `redis` services are healthy before the API starts:

```bash
docker compose ps
# Look for "healthy" status on db and redis
```

### Symptom: `LEARNHOUSE_AUTH_JWT_SECRET_KEY` error

```
ValueError: SECURITY ERROR: LEARNHOUSE_AUTH_JWT_SECRET_KEY must be set.
```

**Fix:** Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to `.env`:
```ini
LEARNHOUSE_AUTH_JWT_SECRET_KEY=<generated_key>
```

### Symptom: Port already in use

```bash
Error response from daemon: driver failed programming external connectivity
```

**Fix:** Check what's using port 9000 (or your configured port):

```bash
sudo lsof -i :9000
# Kill the process or change LEARNHOUSE_PORT in .env
```

---

## Database Issues

### Symptom: `connection refused` on startup

**Causes:**
- PostgreSQL not started yet
- Wrong connection string
- PostgreSQL running on a different port

**Fix:** Verify the connection string in `.env`:

```bash
# Test connection
psql "$LEARNHOUSE_SQL_CONNECTION_STRING" -c "SELECT 1"
```

### Symptom: `duplicate key value violates unique constraint`

**Cause:** Schema mismatch — migrations haven't been run, or data was partially
restored.

**Fix:** Run migrations:

```bash
alembic upgrade head
```

### Symptom: Database connection pool exhaustion

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 10 reached
```

**Causes:**
- Too many concurrent connections
- Connections not being returned to the pool
- Slow queries holding connections open

**Fixes:**
1. Check active connections: `SELECT count(*) FROM pg_stat_activity;`
2. Look for slow queries in logs
3. Restart the API to drain the pool

---

## Redis Issues

### Symptom: `Redis connection error`

```bash
redis.exceptions.ConnectionError: Error -2 connecting to redis:6379
```

**Fixes:**
- Verify Redis is running: `docker compose ps redis`
- Check connection string in `.env`
- Ensure network connectivity between containers

### Symptom: Rate limiting not working

Rate limits are stored in Redis. If Redis is down, rate limiting is bypassed.

**Check:**
```bash
redis-cli PING  # Should return PONG
redis-cli KEYS "rate_limit:*" | head -5  # Check active rate limit keys
```

---

## Performance Problems

### Symptom: API feels slow (p95 > 500ms)

**Diagnose:**

```bash
# 1. Check slow query logs
docker compose logs api | grep "Slow query"

# 2. Check request timing
docker compose logs api | grep "WARN.*ms"

# 3. Check database performance
docker compose exec db psql -U learnhouse -c "
  SELECT query, calls, total_time/calls AS avg_ms
  FROM pg_stat_statements
  ORDER BY total_time DESC LIMIT 10;
"

# 4. Run a load test
bash apps/api/tests/load/run.sh login
```

**Common fixes:**
- Add missing database indexes
- Increase API replicas in docker-compose.yml
- Increase `pool_size` in database.py
- Enable response caching for content endpoints

### Symptom: Memory usage grows over time (possible leak)

Run the sustained load test while monitoring memory:

```bash
# Terminal 1 — run load test
bash apps/api/tests/load/run.sh sustained

# Terminal 2 — monitor memory
docker stats --no-stream
```

**Check for:**
- SQLAlchemy session not being closed
- File handles not released after uploads
- Redis pub/sub subscriptions accumulating

---

## Monitoring & Logs

### Accessing Logs

```bash
# All services
docker compose logs --tail=100 -f

# API only
docker compose logs api --tail=100 -f

# Structured JSON logs (single line per request)
docker compose logs api | grep structured

# Errors only
docker compose logs api | grep -i error
```

### Log Format

In production, logs are JSON by default:

```json
{"timestamp": "2026-07-02T12:00:00.000Z", "level": "INFO",
 "request_id": "abc123def456", "method": "GET", "path": "/api/v1/health",
 "status": 200, "duration_ms": 12.5, "service": "api"}
```

### Metrics Endpoints

```bash
# Get monitoring debug info
curl http://localhost:9000/api/v1/monitoring/debug

# Get metrics status
curl http://localhost:9000/api/v1/monitoring/metrics
```

### Sentry

If `LEARNHOUSE_SENTRY_DSN` is configured, errors are automatically reported.

Check Sentry dashboard for:
- Error frequency and trends
- Performance traces (p50/p95/p99)
- User feedback submissions

---

## Backup & Restore

### Symptom: Backup script fails with `pg_dump: error: connection to server`

**Fix:** Ensure `LEARNHOUSE_SQL_CONNECTION_STRING` points to the correct database
URL. Use a direct connection (not through a pooler like PgBouncer) for backups.

### Symptom: `verify-backup.sh` shows `STALE`

A backup is "stale" if it's more than 26 hours old.

**Fixes:**
- Verify cron is running: `sudo systemctl status cron`
- Check cron logs: `sudo tail /var/log/syslog | grep backup`
- Run manually: `bash deploy/scripts/backup-db.sh`

### Symptom: S3 upload fails

```bash
upload failed: ... to s3://bucket/... An error occurred (AccessDenied)
```

**Fixes:**
- Verify AWS credentials are configured
- Check S3 bucket permissions
- Ensure IAM user has `s3:PutObject` permission

---

## SSL / HTTPS

### Symptom: Browser shows "Not Secure"

**Fixes:**
1. Get SSL certificate: `sudo certbot --nginx -d yourdomain.com`
2. Verify SSL is configured in nginx
3. Set `LEARNHOUSE_SSL=true` in .env

### Symptom: HSTS not being set

HSTS is only set when `LEARNHOUSE_SSL=true`. Verify:

```bash
# Check response headers
curl -I https://yourdomain.com | grep -i strict-transport
```

---

## Authentication Issues

### Symptom: Users can't log in

```bash
# Check rate limiting
redis-cli KEYS "rate_limit:login:*"

# Check account lockout
redis-cli KEYS "lockout:*"

# Verify JWT secret hasn't changed
# (Changing the secret invalidates all existing sessions)
```

### Symptom: CORS errors in browser

```bash
# Verify allowed origins
curl http://localhost:9000/api/v1/monitoring/debug

# Check .env value
grep LEARNHOUSE_ALLOWED_ORIGINS .env
```

---

## Storage / File Upload Issues

### Symptom: Upload fails with 413 Request Entity Too Large

**Fix:** Increase `client_max_body_size` in nginx config (default: 6G).

### Symptom: Uploaded files not accessible

**Fixes:**
- Check content delivery type in `.env`
- If using S3, verify bucket permissions
- If using filesystem, verify `/app/content` volume mount

---

## AI Feature Issues

### Symptom: AI features return 429 (rate limited)

**Check rate limit status:**
```bash
redis-cli KEYS "rate_limit:ai:*"
```

**Fix:** Wait for the rate limit window to reset (1 minute for user, 1 minute for org).

### Symptom: AI features return 503

**Causes:**
- AI provider API key not configured
- Provider outage
- Network connectivity issue

**Check:**
```bash
curl http://localhost:9000/api/v1/health/ai
```
