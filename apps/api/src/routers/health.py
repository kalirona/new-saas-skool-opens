"""Health check endpoints — /health, /live, /ready, and per-dependency probes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.events.database import get_db_session
from src.services.health.health import (
    HealthReport,
    check_all,
    check_ai,
    check_billing,
    check_database,
    check_live,
    check_redis,
    check_storage,
)

router = APIRouter()


@router.get("/health", summary="Full health report")
async def get_health(db_session: AsyncSession = Depends(get_db_session)):
    report = await check_all(db_session)
    if report.status == "down":
        raise HTTPException(status_code=503, detail=report.__dict__)
    return report.__dict__


@router.get("/live", summary="Liveness probe — always returns 200 if the process is alive")
async def get_live():
    return {"status": "alive"}


@router.get("/ready", summary="Readiness probe — returns 200 only when dependencies are healthy")
async def get_ready(db_session: AsyncSession = Depends(get_db_session)):
    report = await check_all(db_session)
    if report.status == "down":
        raise HTTPException(status_code=503, detail=report.__dict__)
    report.status = "ready"
    return report.__dict__


@router.get("/database", summary="Database health check")
async def get_database_health(db_session: AsyncSession = Depends(get_db_session)):
    result = await check_database(db_session)
    if result.status == "down":
        raise HTTPException(status_code=503, detail=result.__dict__)
    return result.__dict__


@router.get("/redis", summary="Redis health check")
async def get_redis_health():
    result = await check_redis()
    if result.status == "down":
        raise HTTPException(status_code=503, detail=result.__dict__)
    return result.__dict__


@router.get("/storage", summary="Storage health check (local or S3)")
async def get_storage_health():
    result = await check_storage()
    if result.status == "down":
        raise HTTPException(status_code=503, detail=result.__dict__)
    return result.__dict__


@router.get("/ai", summary="AI provider health check")
async def get_ai_health():
    return (await check_ai()).__dict__


@router.get("/billing", summary="Billing provider health check (Stripe/PayPal)")
async def get_billing_health():
    return (await check_billing()).__dict__
