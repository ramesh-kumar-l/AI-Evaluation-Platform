"""FastAPI application entrypoint and composition root."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api import audit, datasets, health, prompts, providers, runs
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.telemetry import configure_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    log = get_logger(__name__)
    log.info(
        "app.startup",
        version=__version__,
        env=settings.env,
        database=settings.resolved_database_url.split("://", 1)[0],
        telemetry=settings.telemetry_enabled,
    )
    yield
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
    app.include_router(health.router)
    app.include_router(providers.router)
    app.include_router(prompts.router)
    app.include_router(datasets.router)
    app.include_router(audit.router)
    app.include_router(runs.router)
    return app


app = create_app()
