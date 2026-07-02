# Environment Variable Reference

All LearnHouse configuration is through environment variables. There are no
config files in production — everything comes from `.env` or the environment.

## Quick Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_AUTH_JWT_SECRET_KEY` | **Yes** | — | JWT signing key (≥32 chars) |
| `LEARNHOUSE_SQL_CONNECTION_STRING` | **Yes** | — | PostgreSQL connection string |
| `LEARNHOUSE_REDIS_CONNECTION_STRING` | **Yes** | — | Redis connection string |
| `LEARNHOUSE_DOMAIN` | **Yes** | — | Public domain name |
| `LEARNHOUSE_SITE_NAME` | Yes | `LearnHouse` | Site display name |
| `LEARNHOUSE_TENANCY` | Yes | `single` | `single` or `multi` |
| `LEARNHOUSE_LOG_LEVEL` | No | `INFO` | Python log level |
| `LEARNHOUSE_LOG_FORMAT` | No | `json` | `json` or `text` |

---

## Security

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_AUTH_JWT_SECRET_KEY` | **Yes** | — | Min 32 chars. Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `LEARNHOUSE_COOKIE_DOMAIN` | No | `.localhost` | Cookie domain for shared subdomain auth |
| `LEARNHOUSE_COOKIE_DOMAIN_ALLOW_BROAD` | No | — | Set `true` to allow broad cookie domains |
| `LEARNHOUSE_SSL` | No | `false` | Enable HSTS and secure cookie flags |
| `LEARNHOUSE_CSP_HEADER` | No | — | Content-Security-Policy header value |
| `LEARNHOUSE_ALLOWED_ORIGINS` | No | `localhost:3000,3001` | Comma-separated CORS origins |
| `LEARNHOUSE_ALLOWED_REGEXP` | No | `^https?://localhost(:\d+)?$` | CORS origin regex fallback |
| `CLOUD_INTERNAL_KEY` | No | — | Internal service RPC key |
| `LEARNHOUSE_PLATFORM_API_KEY` | No | — | Platform control plane API key |

### Rate Limiting Defaults (hardcoded)

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 30 attempts | 5 min per IP |
| Signup | 10 attempts | 1 hour per IP |
| AI generation | 30 requests | 1 min per user |
| AI generation (org) | 120 requests | 1 min per org |
| API token creation | 10 attempts | 1 hour per IP |
| Password reset | 5 attempts | 5 min per email |
| Search | 60 requests | 1 min per user |

## Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_SQL_CONNECTION_STRING` | **Yes** | — | e.g. `postgresql+asyncpg://user:pass@host:5432/db` |
| `POSTGRES_USER` | Yes (Docker) | `learnhouse` | PostgreSQL user |
| `POSTGRES_PASSWORD` | Yes (Docker) | — | PostgreSQL password |
| `POSTGRES_DB` | Yes (Docker) | `learnhouse` | PostgreSQL database name |

## Redis

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_REDIS_CONNECTION_STRING` | **Yes** | — | e.g. `redis://host:6379/0` |

## Hosting

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_DOMAIN` | **Yes** | — | e.g. `learnhouse.example.com` |
| `LEARNHOUSE_FRONTEND_DOMAIN` | No | Same as DOMAIN | Frontend URL (if different) |
| `LEARNHOUSE_PORT` | No | `9000` | API listen port |
| `LEARNHOUSE_TENANCY` | No | `single` | `single` or `multi` (requires EE) |
| `LEARNHOUSE_SSL` | No | `false` | Enable HTTPS mode |
| `LEARNHOUSE_DEVELOPMENT_MODE` | No | `false` | Dev mode (docs, debug) |

## Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_CONTENT_DELIVERY_TYPE` | No | `filesystem` | `filesystem` or `s3api` |
| `LEARNHOUSE_S3_API_BUCKET_NAME` | For S3 | — | S3 bucket name |
| `LEARNHOUSE_S3_API_ENDPOINT_URL` | For S3 | — | S3 endpoint URL |
| `LEARNHOUSE_S3_API_REGION` | For S3 | — | AWS region |
| `LEARNHOUSE_S3_API_ACCESS_KEY_ID` | For S3 | — | AWS access key |
| `LEARNHOUSE_S3_API_SECRET_ACCESS_KEY` | For S3 | — | AWS secret key |

## Mail

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_EMAIL_PROVIDER` | No | `resend` | `resend` or `smtp` |
| `LEARNHOUSE_SYSTEM_EMAIL_ADDRESS` | Yes | — | From address for system emails |
| `LEARNHOUSE_RESEND_API_KEY` | For Resend | — | Resend API key |
| `LEARNHOUSE_SMTP_HOST` | For SMTP | — | SMTP server host |
| `LEARNHOUSE_SMTP_PORT` | For SMTP | `587` | SMTP port |
| `LEARNHOUSE_SMTP_USERNAME` | For SMTP | — | SMTP username |
| `LEARNHOUSE_SMTP_PASSWORD` | For SMTP | — | SMTP password |
| `LEARNHOUSE_SMTP_USE_TLS` | For SMTP | `true` | SMTP TLS flag |

## Payments

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_STRIPE_SECRET_KEY` | For Stripe | — | Stripe secret key (sk_live_*) |
| `LEARNHOUSE_STRIPE_PUBLISHABLE_KEY` | For Stripe | — | Stripe publishable key (pk_live_*) |
| `LEARNHOUSE_STRIPE_WEBHOOK_STANDARD_SECRET` | For Stripe | — | Stripe webhook signing secret |
| `LEARNHOUSE_PAYPAL_CLIENT_ID` | For PayPal | — | PayPal client ID |
| `LEARNHOUSE_PAYPAL_CLIENT_SECRET` | For PayPal | — | PayPal client secret |

## AI

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_IS_AI_ENABLED` | No | `false` | Enable AI features |
| `LEARNHOUSE_AI_PROVIDER` | If AI enabled | — | `google`, `openai`, `anthropic`, etc. |
| `LEARNHOUSE_AI_API_KEY` | If AI enabled | — | Provider API key |
| `LEARNHOUSE_GEMINI_API_KEY` | If Gemini | — | Google Gemini API key |

## Observability

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LEARNHOUSE_LOG_FORMAT` | No | `json` | `json` (structured) or `text` (plain) |
| `LEARNHOUSE_SENTRY_DSN` | No | — | Sentry DSN for error tracking |
| `LEARNHOUSE_OTEL_ENABLED` | No | `false` | Enable OpenTelemetry |
| `LEARNHOUSE_OTEL_EXPORTER_OTLP_ENDPOINT` | If OTel | `http://localhost:4318` | OTLP HTTP endpoint |
| `LEARNHOUSE_OTEL_EXPORTER_OTLP_HEADERS` | If OTel | — | Comma-separated `key=value` headers |
| `LEARNHOUSE_SLOW_QUERY_THRESHOLD_MS` | No | `500` | SQLAlchemy slow query threshold |

## Backup

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LEARNHOUSE_BACKUP_DIR` | No | `./backups` | Backup storage directory |
| `LEARNHOUSE_BACKUP_RETENTION_DAYS` | No | `30` | Days to retain backups |
| `LEARNHOUSE_BACKUP_S3_DEST` | No | — | S3 destination for backup uploads |
| `BACKUP_DIR` | No | `./backups` | Script-level backup directory override |
| `BACKUP_S3_DEST` | No | — | Script-level S3 destination override |

## Full Example `.env`

```ini
# ── Required ─────────────────────────────────────────────────────────────
LEARNHOUSE_SQL_CONNECTION_STRING=postgresql+asyncpg://learnhouse:CHANGE_ME@db:5432/learnhouse
LEARNHOUSE_REDIS_CONNECTION_STRING=redis://redis:6379/0
LEARNHOUSE_AUTH_JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
LEARNHOUSE_DOMAIN=learnhouse.example.com

# ── Hosting ──────────────────────────────────────────────────────────────
LEARNHOUSE_SITE_NAME=LearnHouse
LEARNHOUSE_FRONTEND_DOMAIN=learnhouse.example.com
LEARNHOUSE_PORT=9000
LEARNHOUSE_TENANCY=single
LEARNHOUSE_SSL=true
LEARNHOUSE_ALLOWED_ORIGINS=https://learnhouse.example.com

# ── Mail ─────────────────────────────────────────────────────────────────
LEARNHOUSE_EMAIL_PROVIDER=resend
LEARNHOUSE_SYSTEM_EMAIL_ADDRESS=noreply@learnhouse.example.com
LEARNHOUSE_RESEND_API_KEY=re_...

# ── Storage (optional — omit for local filesystem) ──────────────────────
# LEARNHOUSE_CONTENT_DELIVERY_TYPE=s3api
# LEARNHOUSE_S3_API_BUCKET_NAME=learnhouse-media
# LEARNHOUSE_S3_API_ENDPOINT_URL=https://s3.eu-west-1.amazonaws.com
# LEARNHOUSE_S3_API_REGION=eu-west-1

# ── AI (optional) ───────────────────────────────────────────────────────
# LEARNHOUSE_IS_AI_ENABLED=true
# LEARNHOUSE_AI_PROVIDER=google
# LEARNHOUSE_GEMINI_API_KEY=AIza...

# ── Observability (optional) ────────────────────────────────────────────
# LEARNHOUSE_SENTRY_DSN=https://key@o123.ingest.sentry.io/123
# LEARNHOUSE_OTEL_ENABLED=true
# LEARNHOUSE_OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318

# ── Docker-only ─────────────────────────────────────────────────────────
POSTGRES_USER=learnhouse
POSTGRES_PASSWORD=CHANGE_ME
POSTGRES_DB=learnhouse
```
