"""OpenTelemetry skeleton — active only when an OTLP endpoint is configured.

Offline-first: with no endpoint set this is a complete no-op and imports no OTel packages, so the
app runs fully offline without the optional `otel` extra installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import Settings
from app.core.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI

log = get_logger(__name__)


def configure_telemetry(app: FastAPI, settings: Settings) -> None:
    """Wire up tracing if (and only if) telemetry is enabled and deps are installed."""
    if not settings.telemetry_enabled:
        log.debug("telemetry.disabled", reason="no OTLP endpoint configured")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        log.warning("telemetry.skipped", reason="OTel packages not installed (extras: otel)")
        return

    resource = Resource.create({"service.name": settings.service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint))
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    log.info("telemetry.enabled", endpoint=settings.otel_exporter_otlp_endpoint)
