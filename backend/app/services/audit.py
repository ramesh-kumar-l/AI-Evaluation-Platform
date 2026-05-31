"""Append-only audit service with a tamper-evident hash chain. See ADR-0002.

Every mutation routes through :func:`record_event`, which links each event to the previous one via
``sha256(prev_hash + canonical(content))``. :func:`verify_chain` re-derives the chain to detect
tampering.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def _canonical(content: dict[str, Any]) -> str:
    """Deterministic JSON serialization so the same content always hashes identically."""
    return json.dumps(content, sort_keys=True, separators=(",", ":"), default=str)


def _hash(prev_hash: str | None, content: dict[str, Any]) -> str:
    return hashlib.sha256(f"{prev_hash or ''}{_canonical(content)}".encode()).hexdigest()


def _latest(db: Session) -> AuditEvent | None:
    return db.execute(
        select(AuditEvent).order_by(AuditEvent.seq.desc()).limit(1)
    ).scalar_one_or_none()


def record_event(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_key: uuid.UUID,
    entity_version_id: uuid.UUID | None,
    payload: dict[str, Any],
) -> AuditEvent:
    """Append one immutable, hash-chained audit event. Flushes but does not commit."""
    prev = _latest(db)
    prev_hash = prev.hash if prev else None
    content = {
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_key": str(entity_key),
        "entity_version_id": str(entity_version_id) if entity_version_id else None,
        "payload": payload,
    }
    event = AuditEvent(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_key=entity_key,
        entity_version_id=entity_version_id,
        payload=payload,
        prev_hash=prev_hash,
        hash=_hash(prev_hash, content),
    )
    db.add(event)
    db.flush()
    return event


def verify_chain(db: Session) -> bool:
    """Recompute the whole chain; return True iff every link is intact."""
    prev_hash: str | None = None
    events = db.execute(select(AuditEvent).order_by(AuditEvent.seq.asc())).scalars().all()
    for event in events:
        content = {
            "actor": event.actor,
            "action": event.action,
            "entity_type": event.entity_type,
            "entity_key": str(event.entity_key),
            "entity_version_id": str(event.entity_version_id) if event.entity_version_id else None,
            "payload": event.payload,
        }
        if event.prev_hash != prev_hash or event.hash != _hash(prev_hash, content):
            return False
        prev_hash = event.hash
    return True
