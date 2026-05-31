"""Database engine + session management (SQLAlchemy 2.x).

Offline-first: resolves to a local SQLite file when no DATABASE_URL is set, otherwise the configured
Postgres URL. Sessions are provided via a FastAPI dependency; services own the transaction boundary.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


def _make_engine(settings: Settings) -> Engine:
    url = settings.resolved_database_url
    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        # Allow use across FastAPI's threadpool; SQLite is dev/test fallback only.
        connect_args["check_same_thread"] = False
    return create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)


_settings = get_settings()
engine: Engine = _make_engine(_settings)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a session; always closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
