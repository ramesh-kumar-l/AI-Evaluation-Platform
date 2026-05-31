"""Audit endpoints (read-only): inspect the trail and verify chain integrity."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit_event import AuditEvent
from app.schemas.audit import AuditEventOut
from app.services import audit

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=list[AuditEventOut])
def list_events(
    db: Session = Depends(get_db),
    entity_key: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, le=1000),
) -> list[AuditEvent]:
    stmt = select(AuditEvent).order_by(AuditEvent.seq.desc()).limit(limit)
    if entity_key is not None:
        stmt = stmt.where(AuditEvent.entity_key == entity_key)
    return list(db.execute(stmt).scalars().all())


@router.get("/verify")
def verify(db: Session = Depends(get_db)) -> dict[str, bool]:
    """Recompute the hash chain; ``intact: false`` means the log was tampered with."""
    return {"intact": audit.verify_chain(db)}
