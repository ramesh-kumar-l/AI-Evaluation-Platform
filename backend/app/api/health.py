"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import Settings, get_settings
from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    """Liveness: the process is up. Does not touch external dependencies."""
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": __version__,
        "env": settings.env,
        "offline_first": True,
    }


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, object]:
    """Readiness: the database is reachable."""
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
