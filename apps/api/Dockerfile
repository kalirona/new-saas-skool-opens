# ───────────────────────────────────────────────
# Stage 1: Builder — install deps & compile
# ───────────────────────────────────────────────
FROM python:3.14.3-slim-bookworm AS builder

# Install build dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /bin/

# Copy dependency files first for layer caching
WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install project dependencies (no dev deps)
RUN uv sync --frozen --no-dev

# Copy the rest of the source AFTER deps are installed
COPY . .

# Remove Enterprise Edition folder for public builds
ARG LEARNHOUSE_PUBLIC=false
RUN if [ "$LEARNHOUSE_PUBLIC" = "true" ]; then rm -rf /app/ee; fi

# ───────────────────────────────────────────────
# Stage 2: Runtime — minimal production image
# ───────────────────────────────────────────────
FROM python:3.14.3-slim-bookworm AS runner

# Runtime dependencies only (netcat for entrypoint wait, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copy uv binary for the entrypoint script (uses `uv run`)
COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /bin/

# Create a non-root user
RUN groupadd --system --gid 1001 learnhouse && \
    useradd --system --uid 1001 --gid learnhouse --home-dir /app --no-create-home learnhouse

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy only the runtime code and entrypoint
COPY --from=builder /app/src /app/src
COPY --from=builder /app/app.py /app/app.py
COPY --from=builder /app/cli.py /app/cli.py
COPY --from=builder /app/config /app/config
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/uv.lock /app/uv.lock
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh && chown -R learnhouse:learnhouse /app

WORKDIR /app

# Switch to non-root user
USER learnhouse

# Expose port
EXPOSE 9000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:9000/api/v1/health || exit 1

# Use entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]