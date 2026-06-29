import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

import httpx
from sqlmodel import select, col, delete

from src.core.events.database import _async_session_factory
from src.core.tasks.executor import get_executor
from src.db.webhooks import WebhookEndpoint, WebhookDeliveryLog
from src.services.utils.ssrf_guard import (
    SSRFBlockedError,
    assert_connected_peer_allowed,
    resolve_and_validate_url,
)
from src.services.webhooks.crypto import decrypt_secret, compute_signature
from src.services.webhooks.events import validate_event_data

logger = logging.getLogger(__name__)

_webhook_client: httpx.AsyncClient | None = None

LOG_RETENTION_PER_ENDPOINT = 200


def _get_webhook_client() -> httpx.AsyncClient:
    global _webhook_client
    if _webhook_client is None:
        _webhook_client = httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=False,
            headers={"User-Agent": "LearnHouse-Webhooks/1.0"},
        )
    return _webhook_client


async def close_webhook_client() -> None:
    global _webhook_client
    if _webhook_client is not None:
        await _webhook_client.aclose()
        _webhook_client = None


@dataclass
class _EndpointInfo:
    id: int
    webhook_uuid: str
    url: str
    secret_encrypted: str
    events: list


async def dispatch_webhooks(
    event_name: str,
    org_id: int,
    data: dict,
    webhook_ids: Optional[List[int]] = None,
) -> None:
    validate_event_data(event_name, data)
    executor = get_executor()
    await executor.run(
        lambda: _deliver_webhooks(event_name, org_id, data, webhook_ids),
        task_name=f"webhook_batch_{event_name}",
        idempotency_key=f"wh:{event_name}:{org_id}:{hash(str(data)[:200])}",
        dlq_payload={"event_name": event_name, "org_id": org_id, "webhook_ids": webhook_ids},
    )


async def _deliver_webhooks(
    event_name: str,
    org_id: int,
    data: dict,
    webhook_ids: Optional[List[int]],
) -> None:
    endpoints: list[_EndpointInfo] = []
    async with _async_session_factory() as db_session:
        if webhook_ids:
            statement = select(WebhookEndpoint).where(
                WebhookEndpoint.id.in_(webhook_ids),
                WebhookEndpoint.is_active == True,
            )
        else:
            statement = select(WebhookEndpoint).where(
                WebhookEndpoint.org_id == org_id,
                WebhookEndpoint.is_active == True,
            )
        for ep in (await db_session.execute(statement)).scalars().all():
            if webhook_ids or event_name in (ep.events or []):
                endpoints.append(_EndpointInfo(
                    id=ep.id,
                    webhook_uuid=ep.webhook_uuid,
                    url=ep.url,
                    secret_encrypted=ep.secret_encrypted,
                    events=ep.events or [],
                ))

    for ep_info in endpoints:
        try:
            await _deliver_to_endpoint(ep_info, event_name, org_id, data)
        except Exception:
            logger.error(
                "Webhook delivery failed for endpoint %s event %s org %s",
                ep_info.webhook_uuid, event_name, org_id, exc_info=True,
            )


async def _deliver_to_endpoint(
    ep: _EndpointInfo,
    event_name: str,
    org_id: int,
    data: dict,
) -> None:
    MAX_ATTEMPTS = 3
    BACKOFF_DELAYS = [1, 4, 16]

    delivery_uuid = f"dlv_{uuid4().hex[:16]}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "event": event_name,
        "delivery_id": delivery_uuid,
        "timestamp": timestamp,
        "org_id": org_id,
        "data": data,
    }

    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()

    try:
        secret = decrypt_secret(ep.secret_encrypted)
    except Exception:
        logger.warning("Failed to decrypt secret for webhook %s", ep.webhook_uuid)
        return

    signature = compute_signature(payload_bytes, secret)

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event_name,
        "X-Webhook-Delivery": delivery_uuid,
        "X-Webhook-Signature": signature,
    }

    client = _get_webhook_client()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        log_entry = WebhookDeliveryLog(
            webhook_id=ep.id,
            event_name=event_name,
            delivery_uuid=delivery_uuid,
            request_payload=payload,
            attempt=attempt,
            created_at=str(datetime.now()),
        )

        try:
            validated_ips = resolve_and_validate_url(ep.url)

            resp = await client.post(ep.url, content=payload_bytes, headers=headers)
            try:
                assert_connected_peer_allowed(resp, validated_ips)
            except SSRFBlockedError as ssrf_exc:
                log_entry.success = False
                log_entry.error_message = f"SSRF guard: {ssrf_exc}"[:1000]
            else:
                log_entry.response_status = resp.status_code
                log_entry.response_body = resp.text[:500] if resp.text else None
                log_entry.success = 200 <= resp.status_code < 300

        except SSRFBlockedError as e:
            log_entry.success = False
            log_entry.error_message = f"SSRF guard: {e}"[:1000]
        except Exception as e:
            log_entry.success = False
            log_entry.error_message = str(e)[:1000]

        async with _async_session_factory() as db_session:
            db_session.add(log_entry)
            await db_session.commit()
            success = bool(log_entry.success)

        if success:
            break

        if attempt < MAX_ATTEMPTS:
            delay = BACKOFF_DELAYS[attempt - 1] if attempt - 1 < len(BACKOFF_DELAYS) else BACKOFF_DELAYS[-1]
            await asyncio.sleep(delay)

    await _prune_delivery_logs(ep.id)


async def _prune_delivery_logs(webhook_id: int) -> None:
    try:
        async with _async_session_factory() as db_session:
            keep_ids = (
                select(WebhookDeliveryLog.id)
                .where(WebhookDeliveryLog.webhook_id == webhook_id)
                .order_by(col(WebhookDeliveryLog.id).desc())
                .limit(LOG_RETENTION_PER_ENDPOINT)
                .scalar_subquery()
            )
            await db_session.execute(
                delete(WebhookDeliveryLog).where(
                    WebhookDeliveryLog.webhook_id == webhook_id,
                    col(WebhookDeliveryLog.id).not_in(keep_ids),
                )
            )
            await db_session.commit()
    except Exception:
        logger.warning("Failed to prune webhook delivery logs for endpoint %s", webhook_id)
