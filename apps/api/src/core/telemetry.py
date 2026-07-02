"""OpenTelemetry instrumentation for the LearnHouse API.

Initialises OTel SDK with FastAPI, SQLAlchemy, Redis, and gRPC instrumentation
when LEARNHOUSE_OTEL_ENABLED=true. Traces are exported via OTLP HTTP.

Usage in app.py:
    from src.core.telemetry import setup_opentelemetry
    setup_opentelemetry(learnhouse_config)
"""

import logging
import os

logger = logging.getLogger(__name__)


def setup_opentelemetry(service_name: str = "learnhouse-api") -> bool:
    """Initialise OpenTelemetry SDK and instrument the app.

    Returns True if OTel was enabled and configured, False otherwise.
    """
    enabled = os.environ.get("LEARNHOUSE_OTEL_ENABLED", "").lower() in ("true", "1", "yes")
    if not enabled:
        logger.debug("OpenTelemetry disabled — set LEARNHOUSE_OTEL_ENABLED=true to enable")
        return False

    endpoint = os.environ.get(
        "LEARNHOUSE_OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4318",
    )
    headers = os.environ.get("LEARNHOUSE_OTEL_EXPORTER_OTLP_HEADERS", "")

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.2.7",
            "deployment.environment": os.environ.get("LEARNHOUSE_ENV", "dev"),
        })

        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(
            endpoint=f"{endpoint}/v1/traces",
            headers=dict(h.split("=", 1) for h in headers.split(",") if "=" in h) if headers else {},
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        logger.info("OpenTelemetry initialised — exporting to %s", endpoint)
        return True

    except ImportError as e:
        logger.warning(
            "OpenTelemetry packages not installed (%s). "
            "Install with: pip install opentelemetry-distro opentelemetry-exporter-otlp-proto-http",
            e,
        )
        return False
    except Exception as e:
        logger.error("Failed to initialise OpenTelemetry: %s", e)
        return False
