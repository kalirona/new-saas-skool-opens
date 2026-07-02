"""Operations dashboard router — aggregates system health, usage, and status
for the superadmin operations dashboard.

Prefix: /api/v1/operations/
"""

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.events.database import get_db_session
from src.core.redis import get_redis_client
from src.core.storage import get_storage_backend
from src.security.api_token_utils import get_authenticated_non_api_token_user
from src.services.health.health import check_all

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_authenticated_non_api_token_user)])


@router.get("/dashboard", summary="Full operations dashboard data")
async def get_operations_dashboard(db_session: AsyncSession = Depends(get_db_session)):
    """Aggregates system health, AI usage stats, billing failures, webhook
    failures, storage usage, and queue status into a single response."""
    import asyncio

    results = await asyncio.gather(
        _get_health_section(db_session),
        _get_ai_usage(),
        _get_billing_failures(),
        _get_failed_webhooks(db_session),
        _get_storage_usage(),
        _get_queue_status(),
        _get_background_job_status(),
        return_exceptions=True,
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "health": _unwrap(results[0]),
        "ai_usage": _unwrap(results[1]),
        "billing_failures": _unwrap(results[2]),
        "failed_webhooks": _unwrap(results[3]),
        "storage_usage": _unwrap(results[4]),
        "queue_status": _unwrap(results[5]),
        "background_jobs": _unwrap(results[6]),
    }


def _unwrap(result):
    if isinstance(result, Exception):
        return {"error": str(result)}
    return result


async def _get_health_section(db_session):
    report = await check_all(db_session)
    return {
        "status": report.status,
        "timestamp": report.timestamp,
        "dependencies": [
            {"name": d.name, "status": d.status, "latency_ms": d.latency_ms, "error": d.error}
            for d in report.dependencies
        ],
    }


async def _get_ai_usage():
    r = get_redis_client()
    try:
        recent = 0
        cfg_keys = r.keys("rate_limit:ai:*") if r else []
        recent = len(cfg_keys)
        return {
            "enabled": bool(os.environ.get("LEARNHOUSE_AI_PROVIDER")),
            "provider": os.environ.get("LEARNHOUSE_AI_PROVIDER", "not configured"),
            "recent_requests": recent,
        }
    except Exception as e:
        return {"enabled": False, "error": str(e)}


async def _get_billing_failures():
    r = get_redis_client()
    try:
        failures = []
        if r:
            keys = r.keys("billing:failure:*") or []
            for key in keys[-20:]:
                data = r.get(key)
                failures.append({
                    "key": key.decode() if isinstance(key, bytes) else key,
                    "data": data.decode()[:200] if isinstance(data, bytes) else str(data)[:200],
                })
        return {"total": len(failures), "recent": failures[-10:]}
    except Exception as e:
        return {"total": 0, "error": str(e)}


async def _get_failed_webhooks(db_session):
    try:
        from sqlmodel import select
        from src.db.webhooks import WebhookDeliveryLog

        stmt = (
            select(WebhookDeliveryLog)
            .where(WebhookDeliveryLog.status == "failed")
            .order_by(WebhookDeliveryLog.created_at.desc())
            .limit(20)
        )
        result = await db_session.execute(stmt)
        logs = result.scalars().all()
        return {
            "total_failed": len(logs),
            "recent": [
                {
                    "id": log.id,
                    "endpoint_id": log.webhook_endpoint_id,
                    "status_code": log.response_status_code,
                    "error": log.error_message,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
        }
    except Exception as e:
        return {"total_failed": 0, "error": str(e)}


async def _get_storage_usage():
    try:
        backend = get_storage_backend()
        backend_type = "s3" if "s3" in type(backend).__name__.lower() else "filesystem"
        return {"type": backend_type, "healthy": True}
    except Exception as e:
        return {"type": "unknown", "healthy": False, "error": str(e)}


async def _get_queue_status():
    r = get_redis_client()
    if r is None:
        return {"connected": False}
    try:
        info = r.info()
        return {
            "connected": True,
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def _get_background_job_status():
    r = get_redis_client()
    try:
        failed = 0
        queued = 0
        if r:
            job_keys = r.keys("bg:job:*") or []
            failed = len([k for k in job_keys if b":failed" in k])
            queued = len(job_keys)
        return {"workers": 1, "queued": queued, "recent_failures": failed}
    except Exception as e:
        return {"workers": 0, "queued": 0, "error": str(e)}
