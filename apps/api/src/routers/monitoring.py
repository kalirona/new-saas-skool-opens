"""Monitoring endpoints — Sentry feedback relay, metrics, and OTel health."""

import os
from typing import Optional

import sentry_sdk
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

router = APIRouter()


_MAX_ATTACHMENTS = 3
_MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
_MAX_MESSAGE_LENGTH = 4096


@router.get(
    "/metrics",
    summary="OpenTelemetry metrics health",
    description="Returns the status of the OpenTelemetry exporter.",
)
async def get_metrics_health():
    otel_enabled = os.environ.get("LEARNHOUSE_OTEL_ENABLED", "").lower() in ("true", "1", "yes")
    return {
        "otel_enabled": otel_enabled,
        "otel_endpoint": os.environ.get("LEARNHOUSE_OTEL_EXPORTER_OTLP_ENDPOINT", "not set"),
        "log_format": os.environ.get("LEARNHOUSE_LOG_FORMAT", "json"),
    }


@router.get(
    "/debug",
    summary="Debug information (non-sensitive configuration dump)",
    include_in_schema=False,
)
async def get_debug_info(request: Request):
    """Return non-sensitive debug information for troubleshooting."""
    from src.services.health.health import check_all
    from src.core.events.database import get_db_session

    return {
        "request_id": getattr(request.state, "request_id", "unknown"),
        "otel_enabled": os.environ.get("LEARNHOUSE_OTEL_ENABLED", "false"),
        "log_format": os.environ.get("LEARNHOUSE_LOG_FORMAT", "json"),
        "slow_query_threshold_ms": os.environ.get("LEARNHOUSE_SLOW_QUERY_THRESHOLD_MS", "500"),
        "backup_retention_days": os.environ.get("LEARNHOUSE_BACKUP_RETENTION_DAYS", "30"),
    }


@router.post(
    "/feedback",
    summary="Submit user feedback",
    message: str = Form(""),
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    associated_event_id: Optional[str] = Form(None),
    attachments: list[UploadFile] = File(default=[]),
):
    message = (message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Feedback message is required")
    if len(message) > _MAX_MESSAGE_LENGTH:
        message = message[:_MAX_MESSAGE_LENGTH]

    if not sentry_sdk.get_client().is_active():
        return

    files = (attachments or [])[:_MAX_ATTACHMENTS]
    loaded: list[tuple[str, bytes, str]] = []
    for upload in files:
        if not upload or not upload.filename:
            continue
        data = await upload.read()
        if not data:
            continue
        if len(data) > _MAX_ATTACHMENT_BYTES:
            data = data[:_MAX_ATTACHMENT_BYTES]
        loaded.append((upload.filename, data, upload.content_type or "application/octet-stream"))

    # sentry-sdk 2.x has no capture_feedback; emit the JS SDK's envelope shape so it lands in User Feedback.
    feedback_context: dict[str, str] = {"message": message, "source": "api"}
    if name:
        feedback_context["name"] = name
    if email:
        feedback_context["contact_email"] = email
    if associated_event_id:
        feedback_context["associated_event_id"] = associated_event_id

    event = {
        "type": "feedback",
        "level": "info",
        "contexts": {"feedback": feedback_context},
    }

    with sentry_sdk.new_scope() as scope:
        for filename, data, content_type in loaded:
            scope.add_attachment(bytes=data, filename=filename, content_type=content_type)
        sentry_sdk.capture_event(event)
