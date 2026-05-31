"""FastAPI application entrypoint and composition root."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app import __version__
from app.api import (
    admin,
    agent,
    audit,
    benchmarks,
    comparisons,
    datasets,
    evaluations,
    gates,
    health,
    metrics,
    observability,
    prompts,
    providers,
    rag,
    runs,
)
from app.core.auth import get_current_key
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.core.scheduler import configure_scheduler, stop_scheduler
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.telemetry import configure_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    log = get_logger(__name__)
    configure_scheduler()
    log.info(
        "app.startup",
        version=__version__,
        env=settings.env,
        database=settings.resolved_database_url.split("://", 1)[0],
        telemetry=settings.telemetry_enabled,
    )
    yield
    stop_scheduler()
    log.info("app.shutdown")


def create_app() -> FastAPI:
    """Application factory — keeps wiring explicit and testable."""
    settings = get_settings()
    app = FastAPI(
        title="AI Evaluation Platform",
        version=__version__,
        summary="System of record for AI quality. Can we safely deploy?",
        lifespan=lifespan,
    )
    configure_telemetry(app, settings)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    _auth = [Depends(get_current_key)]
    app.include_router(health.router)  # health/ready never require auth
    app.include_router(providers.router, dependencies=_auth)
    app.include_router(prompts.router, dependencies=_auth)
    app.include_router(datasets.router, dependencies=_auth)
    app.include_router(audit.router, dependencies=_auth)
    app.include_router(runs.router, dependencies=_auth)
    app.include_router(metrics.router, dependencies=_auth)
    app.include_router(evaluations.router, dependencies=_auth)
    app.include_router(comparisons.router, dependencies=_auth)
    app.include_router(gates.router, dependencies=_auth)
    app.include_router(benchmarks.router, dependencies=_auth)
    app.include_router(rag.router, dependencies=_auth)
    app.include_router(agent.router, dependencies=_auth)
    app.include_router(observability.router, dependencies=_auth)
    app.include_router(admin.router)  # admin uses its own secret header
    return app


app = create_app()
