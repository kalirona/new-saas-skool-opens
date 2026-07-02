# Production Security Configuration

This document summarizes the production security defaults after review.

## Configuration Review Summary

### Rate Limits ✅

Redis-backed rate limiting is implemented and active for all critical endpoints:

| Endpoint | Limit | Window | Enforced |
|----------|-------|--------|----------|
| Login | 30 attempts | 5 min / IP | `rate_limiting.py` |
| Signup | 10 attempts | 1 hour / IP | `rate_limiting.py` |
| AI generation | 30 requests | 1 min / user | `rate_limiting.py` |
| AI generation (org) | 120 requests | 1 min / org | `rate_limiting.py` |
| Password reset | 5 attempts | 5 min / email | `rate_limiting.py` |
| API token creation | 10 attempts | 1 hour / IP | `rate_limiting.py` |
| Search | 60 requests | 1 min / user | `rate_limiting.py` |
| Collab WS | 30 connections | 60s / IP | `collab/src/index.ts` |

**Account lockout:** After 10 failed login attempts from 5+ distinct IPs, the account is locked for 5 minutes.

**Verdict: ✅ Production-ready**

### CSP (Content Security Policy) ⚠️

**Before:** Empty string by default — no CSP header sent.

**Recommended production CSP** (set via `LEARNHOUSE_CSP_HEADER`):
```
default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.umami.is; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; font-src 'self'; connect-src 'self' https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
```

**Delivered via:** `deploy/nginx-ssl.conf` now includes CSP in the HTTPS server block.

**Verdict: ✅ Configured in secure nginx template**

### CORS (Cross-Origin Resource Sharing) ✅

- Explicit allow-list from `LEARNHOUSE_ALLOWED_ORIGINS`
- Regex fallback for development (`^https?://localhost(:\d+)?$`)
- In single-tenancy mode, auto-adds `frontend_domain` and `domain`
- In dev mode, auto-adds localhost ports 3000 and 3001
- Methods: `GET, POST, PUT, PATCH, DELETE, OPTIONS`
- Credentials: allowed (cookies)
- Headers: `Authorization, Content-Type, X-Request-ID`

**Verdict: ✅ Production-ready**

### Cookies ✅

| Cookie | Type | HttpOnly | Secure | SameSite | Max-Age |
|--------|------|----------|--------|----------|---------|
| `LH_access` | Access token | Yes | Yes (if HTTPS) | Lax | 8 hours |
| `LH_refresh` | Refresh token | Yes | Yes (if HTTPS) | Lax | 30 days |

- **Domain:** Host-only in single mode; configurable in multi mode
- **Validation:** Single-label parents (`.com`) are refused; broad parents (`.example.com`) warn unless acknowledged

**Verdict: ✅ Production-ready**

### Session Expiry ✅

| Token | Expiry | Notes |
|-------|--------|-------|
| Access token (JWT) | 8 hours | `exp` + `iat` claims |
| Refresh token (JWT) | 30 days | `jti` for rotation/replay detection |
| Session revocation | 30 days | Redis `jwt_revoked_before` key |
| API tokens (`lh_*`) | No expiry | Organization-scoped; revocable via API |

**Verdict: ✅ Production-ready**

### HTTPS Enforcement ✅

- **Nginx level:** HTTP→HTTPS redirect configured in `deploy/nginx-ssl.conf`
- **Application level:** `is_request_secure()` checks `X-Forwarded-Proto` (only trusted from private proxies)
- **HSTS:** Set when `LEARNHOUSE_SSL=true` — `max-age=31536000; includeSubDomains`
- **Secure cookie flag:** Set when request is detected as HTTPS

**Verdict: ✅ Configured (requires LEARNHOUSE_SSL=true and nginx SSL setup)**

### Security Headers ✅

Sent by `SecurityHeadersMiddleware` on every response:

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (when SSL) |

**Verdict: ✅ Production-ready**

### CSRF Protection ✅

- Validates `Origin`/`Referer` headers on state-changing methods (POST, PUT, DELETE, PATCH)
- Exempts: API tokens (`Bearer lh_*`), Stripe webhooks, internal service calls
- Returns 403 with descriptive error message on failure

**Verdict: ✅ Production-ready**

## Recommended Production Defaults

```ini
# Must be explicitly set in .env for production:
LEARNHOUSE_SSL=true
LEARNHOUSE_AUTH_JWT_SECRET_KEY=<32+ char random string>
LEARNHOUSE_DOMAIN=learnhouse.example.com
LEARNHOUSE_ALLOWED_ORIGINS=https://learnhouse.example.com

# Recommended:
LEARNHOUSE_LOG_FORMAT=json
LEARNHOUSE_LOG_LEVEL=INFO
LEARNHOUSE_SLOW_QUERY_THRESHOLD_MS=500
LEARNHOUSE_CSP_HEADER=<see CSP section above>
LEARNHOUSE_TENANCY=single
```

## Production Hardening Checklist

- [ ] `LEARNHOUSE_AUTH_JWT_SECRET_KEY` is ≥32 chars, randomly generated
- [ ] `LEARNHOUSE_SSL=true` — HSTS and secure cookies enabled
- [ ] SSL certificate obtained and auto-renewal configured (Certbot)
- [ ] `LEARNHOUSE_ALLOWED_ORIGINS` set to the production domain only
- [ ] `LEARNHOUSE_COOKIE_DOMAIN` not set (host-only cookies in single mode)
- [ ] CSP header configured and tested
- [ ] Rate limits are active (verify with Redis: `KEYS rate_limit:*`)
- [ ] Database backups running (check `ls -la backups/`)
- [ ] Storage backups running (check for `storage_*.tar.zst`)
- [ ] Backup integrity verified (`bash verify-backup.sh`)
- [ ] Monitoring endpoints are secured behind nginx
- [ ] Sentry DSN configured for error tracking
- [ ] `LEARNHOUSE_DEVELOPMENT_MODE=false`
- [ ] API docs disabled (`/docs` and `/redoc` return 404)
- [ ] PostgreSQL: strong password, non-root user, network-bound to localhost
- [ ] Redis: password set (`REDIS_PASSWORD`), bound to localhost
- [ ] Firewall enabled (UFW): ports 22, 80, 443 only
- [ ] Log rotation configured (14-day retention)
- [ ] Docker images tagged with version (not just `:latest`)
