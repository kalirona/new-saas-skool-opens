"""Comprehensive health check service — database, Redis, storage, AI, billing."""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from config.config import get_learnhouse_config
from src.core.redis import get_redis_client
from src.core.storage import get_storage_backend

logger = logging.getLogger(__name__)


@dataclass
class DependencyStatus:
    name: str
    status: str  # "ok" | "degraded" | "down"
    latency_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class HealthReport:
    status: str  # "ok" | "degraded" | "down"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dependencies: list[DependencyStatus] = field(default_factory=list)

    def add(self, name: str, status: str, latency_ms: float = 0.0, error: Optional[str] = None) -> None:
        self.dependencies.append(DependencyStatus(name=name, status=status, latency_ms=latency_ms, error=error))
        if status == "down":
            self.status = "down"
        elif status == "degraded" and self.status != "down":
            self.status = "degraded"


async def check_database(db_session: AsyncSession) -> DependencyStatus:
    import time
    start = time.monotonic()
    try:
        result = await db_session.execute(text("SELECT 1"))
        scalar = result.scalar()
        latency = (time.monotonic() - start) * 1000
        if scalar == 1:
            return DependencyStatus(name="database", status="ok", latency_ms=round(latency, 1))
        return DependencyStatus(name="database", status="down", latency_ms=round(latency, 1), error="SELECT 1 returned unexpected value")
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return DependencyStatus(name="database", status="down", latency_ms=round(latency, 1), error=str(e))


async def check_redis() -> DependencyStatus:
    import time
    start = time.monotonic()
    try:
        r = get_redis_client()
        if r is None:
            latency = (time.monotonic() - start) * 1000
            return DependencyStatus(name="redis", status="down", latency_ms=round(latency, 1), error="Redis not configured or unavailable")
        r.ping()
        latency = (time.monotonic() - start) * 1000
        return DependencyStatus(name="redis", status="ok", latency_ms=round(latency, 1))
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return DependencyStatus(name="redis", status="down", latency_ms=round(latency, 1), error=str(e))


async def check_storage() -> DependencyStatus:
    import time
    start = time.monotonic()
    try:
        backend = get_storage_backend()
        test_key = ".health_check_test"
        await backend.write(test_key, b"ok", "text/plain")
        obj = await backend.read(test_key)
        await backend.delete(test_key)
        latency = (time.monotonic() - start) * 1000
        if obj and obj.data == b"ok":
            return DependencyStatus(name="storage", status="ok", latency_ms=round(latency, 1))
        return DependencyStatus(name="storage", status="degraded", latency_ms=round(latency, 1), error="Write/read verification failed")
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return DependencyStatus(name="storage", status="down", latency_ms=round(latency, 1), error=str(e))


async def check_ai() -> DependencyStatus:
    cfg = get_learnhouse_config()
    providers = []
    if cfg.openai_config and cfg.openai_config.api_key:
        providers.append("openai")
    if cfg.gemini_config and cfg.gemini_config.api_key:
        providers.append("gemini")
    if cfg.anthropic_config and cfg.anthropic_config.api_key:
        providers.append("anthropic")

    if not providers:
        return DependencyStatus(name="ai", status="degraded", error="No AI provider configured")

    return DependencyStatus(name="ai", status="ok", latency_ms=0.0, error=f"Configured providers: {', '.join(providers)}")


async def check_billing() -> DependencyStatus:
    cfg = get_learnhouse_config()
    billing = cfg.billing_config
    if billing is None:
        return DependencyStatus(name="billing", status="degraded", error="Billing not configured")

    providers = []
    if billing.stripe_config and billing.stripe_config.secret_key:
        providers.append("stripe")
    if billing.paypal_config and billing.paypal_config.client_id and billing.paypal_config.client_secret:
        providers.append("paypal")

    if not providers:
        return DependencyStatus(name="billing", status="degraded", error="No billing provider configured")

    return DependencyStatus(name="billing", status="ok", latency_ms=0.0, error=f"Configured: {', '.join(providers)}")


async def check_all(db_session: AsyncSession) -> HealthReport:
    import asyncio
    report = HealthReport(status="ok")

    results = await asyncio.gather(
        check_database(db_session),
        check_redis(),
        check_storage(),
        check_ai(),
        check_billing(),
        return_exceptions=True,
    )

    for r in results:
        if isinstance(r, DependencyStatus):
            report.add(r.name, r.status, r.latency_ms, r.error)
        elif isinstance(r, Exception):
            report.add("unknown", "down", error=str(r))

    return report


async def check_live() -> bool:
    return True
