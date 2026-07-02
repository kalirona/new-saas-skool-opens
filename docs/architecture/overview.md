# Architecture Overview

LearnHouse is a modern, open-source learning platform built with a service-
oriented architecture. This document describes the system architecture,
component relationships, and data flow.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Browser (Next.js SSR)                        │
│              apps/web — React, next, TailwindCSS, Radix             │
└──────────────────────┬──────────────────────────────────────────────┘
                       │ HTTPS / WSS
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Reverse Proxy (nginx / CloudPanel)                │
│              ┌─────────────────────────────────────────────────┐   │
│              │  /api/*  →  FastAPI backend (2 replicas)        │   │
│              │  /collab →  Hocuspocus WS collab server         │   │
│              │  /content/* →  S3 or local filesystem           │   │
│              └─────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────────┐
         ▼             ▼                   ▼
┌──────────────┐ ┌──────────┐ ┌──────────────────────┐
│  FastAPI API  │ │ Collab   │ │  Content Delivery    │
│  apps/api     │ │ Server   │ │  (S3 or local FS)    │
│  Python 3.14  │ │ Hocuspocus│ │                     │
│  2 replicas   │ │ TS/Node  │ │                     │
└──────┬───────┘ └──────────┘ └──────────────────────┘
       │
       ├──────────────────┬──────────────────┐
       ▼                  ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  PostgreSQL   │ │  Redis       │ │  Storage (S3/FS) │
│  Primary DB   │ │  Cache +     │ │  Uploaded files  │
│  + pgvector   │ │  Rate Limits │ │  + Media assets  │
│  + migrations │ │  + Sessions  │ │                  │
└──────────────┘ └──────────────┘ └──────────────────┘
```

## Component Breakdown

### 1. Frontend (`apps/web`)

- **Framework:** Next.js (React, Server Components, App Router)
- **Styling:** TailwindCSS + Radix UI primitives
- **State:** SWR for server state, local state for UI
- **Real-time:** Hocuspocus WebSocket for collaborative editing
- **AI:** Client-side AI features backed by server API
- **Build:** Outputs `standalone` Next.js build

### 2. API Server (`apps/api`)

- **Framework:** FastAPI (Python 3.14)
- **ORM:** SQLModel (SQLAlchemy + Pydantic)
- **Async:** asyncpg + aioredis
- **Auth:** JWT (access + refresh tokens), OAuth (Google), SSO (WorkOS)
- **AI:** Multi-provider support (Google, OpenAI, Anthropic, DeepSeek, Mistral, Ollama, Bedrock)
- **Payments:** Stripe + PayPal
- **Background:** Redis-based sessions, rate limiting, job monitoring
- **Migrations:** Alembic (50+ version files)

### 3. Collab Server (`apps/collab`)

- **Framework:** Hocuspocus (TypeScript)
- **Purpose:** Real-time collaborative document editing
- **Auth:** JWT validation via API
- **Rate Limit:** 30 connections / 60s per IP (in-memory)

### 4. Database (PostgreSQL)

- **Version:** 16+
- **Extension:** pgvector (for AI embeddings)
- **Pooling:** asyncpg connection pool (20 connections, 10 overflow)
- **Migrations:** Alembic (async)

### 5. Cache (Redis)

- **Version:** 7+
- **Uses:** Session store, rate limiting, lockout tracking, cache invalidation,
  job queues, pub/sub events

### 6. Storage

- **Local:** Filesystem (`/app/content` volume)
- **Remote:** S3-compatible (AWS, MinIO, Backblaze, etc.)
- **Access:** Signed URLs for private content

## Request Flow

```
User Request
    │
    ▼
nginx (SSL termination, static asset caching)
    │
    ├── /api/v1/* ──► FastAPI
    │                    │
    │                    ├── RequestIDMiddleware (X-Request-ID)
    │                    ├── StructuredLoggingMiddleware (JSON logs)
    │                    ├── RequestTimingMiddleware (duration tracking)
    │                    ├── CORS (origin allow-list)
    │                    ├── GZip (response compression)
    │                    ├── SecurityHeadersMiddleware (HSTS, XFO, CSP)
    │                    ├── CSRFProtectionMiddleware (origin validation)
    │                    │
    │                    ├── Rate Limiter (Redis-backed)
    │                    ├── JWT Auth (access/refresh tokens)
    │                    │
    │                    ├── Router (/api/v1/*)
    │                    │    ├── /auth/* — Login, OAuth, SSO
    │                    │    ├── /orgs/* — Organizations
    │                    │    ├── /courses/* — Courses
    │                    │    ├── /communities/* — Communities & Spaces
    │                    │    ├── /events/* — Events & RSVP
    │                    │    ├── /payments/* — Billing & Subscriptions
    │                    │    ├── /ai/* — AI Generation
    │                    │    ├── /health/* — Health Checks
    │                    │    └── /monitoring/* — Metrics & Debug
    │                    │
    │                    └── Database (SQLModel/asyncpg)
    │
    ├── /collab/* ──► Hocuspocus (WebSocket)
    │
    └── /content/* ──► Storage (S3/local)
```

## Security Model

| Layer | Mechanism | Details |
|-------|-----------|---------|
| Transport | TLS 1.2+ | Terminated at nginx |
| API | JWT (8h access, 30d refresh) | Bearer token + httponly cookies |
| API Tokens | `lh_*` prefixed | Organization-scoped, persistent |
| CSRF | Origin/Referer validation | Exempts API tokens + webhooks |
| CORS | Explicit allow-list | Regex fallback for dev |
| Rate Limiting | Redis-backed | Per-endpoint, per-IP, per-user |
| Account Lockout | Redis HyperLogLog | 10 failed attempts from 5+ IPs |
| CSP | Configurable (recommended for production) | Not set by default |
| Session Revocation | `jwt_revoked_before` Redis key | 30-day TTL |

## Observability

| Tool | Purpose | Configuration |
|------|---------|-------------|
| Sentry | Error tracking + performance | `LEARNHOUSE_SENTRY_DSN` |
| OpenTelemetry | Distributed tracing | `LEARNHOUSE_OTEL_ENABLED=true` |
| Structured JSON Logs | Log aggregation | `LEARNHOUSE_LOG_FORMAT=json` |
| Health Endpoints | Liveness + Readiness | `/live`, `/ready`, `/health` |
| Slow Query Logging | DB performance | `LEARNHOUSE_SLOW_QUERY_THRESHOLD_MS` |
| k6 Load Tests | Performance validation | `apps/api/tests/load/run.sh` |

## Data Flow for Key Features

### Course Creation
```
User → Frontend → POST /api/v1/courses/ → DB insert → Storage (thumbnails)
                                                         │
                                                    S3/local FS
                                                    ← signed URL
```

### AI Course Generation
```
User → Frontend → POST /api/v1/ai/generate-outline
                     → Rate Limit Check (Redis)
                     → AI Provider (Google/OpenAI/etc.)
                     → Response → Stream back to user
```

### Payment / Subscription
```
User → Frontend → POST /api/v1/offers/{plan}/checkout
                     → Stripe Checkout Session
                     → User completes on Stripe
                     → Stripe Webhook → POST /api/v1/payments/webhook
                     → Update subscription in DB
```

### Community + Spaces
```
User → Frontend → POST /api/v1/communities/ → DB insert
                     → POST /communities/{uuid}/spaces → Space created
                     → POST /communities/{uuid}/plans → Membership plan
                     → Users join → Access control (RBAC)
```

## Deployment Diagram

```
┌──────────────────────────────────────────────────────────┐
│  Docker Host (Ubuntu 24.04 LTS)                          │
│                                                          │
│  ┌──────────────────┐   ┌──────────────────┐            │
│  │  nginx:1.27      │   │  api:latest (×2) │            │
│  │  reverse proxy   │──▶│  FastAPI          │            │
│  │  SSL termination │   │  rolling updates  │            │
│  └──────────────────┘   └────────┬─────────┘            │
│                                  │                       │
│  ┌──────────────────┐   ┌───────┴─────────┐            │
│  │  PostgreSQL:16   │◀──│  Redis:7         │            │
│  │  pgdata volume   │   │  redisdata vol   │            │
│  └──────────────────┘   └──────────────────┘            │
│                                                          │
│  ┌──────────────────┐   ┌──────────────────┐            │
│  │  Content Volume  │   │  Backups Volume  │            │
│  │  (uploads)       │   │  (daily dumps)   │            │
│  └──────────────────┘   └──────────────────┘            │
└──────────────────────────────────────────────────────────┘
```

## Key Dependencies

| Component | Language | Key Libraries |
|-----------|----------|--------------|
| API | Python 3.14 | FastAPI, SQLModel, Pydantic, asyncpg, Redis, Stripe, Sentry, OpenTelemetry |
| Frontend | TypeScript | Next.js, React, SWR, TailwindCSS, Radix UI, Hocuspocus |
| Collab | TypeScript | Hocuspocus, Y.js |
| CLI | TypeScript | Typer, Docker Compose templates |
| Database | PostgreSQL 16 | pgvector, asyncpg |
| Cache | Redis 7 | — |
| Proxy | nginx 1.27 | — |
