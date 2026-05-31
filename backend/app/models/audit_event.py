"""Append-only, tamper-evident audit log (hash-chained). See ADR-0002.

Rows are only ever inserted — never updated or deleted. Each row's ``hash`` chains to the previous
row's hash, so any tampering breaks the chain and is detectable.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    # Monotonic global sequence — defines the chain order.
    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), default=uuid.uuid4, unique=True, nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "create", "new_version"

    # What this event is about.
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    entity_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)

    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Tamper-evidence chain.
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
