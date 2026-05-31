"""Audit event schema (read-only; the log is append-only)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq: int
    id: uuid.UUID
    occurred_at: datetime
    actor: str
    action: str
    entity_type: str
    entity_key: uuid.UUID
    entity_version_id: uuid.UUID | None
    payload: dict[str, Any]
    prev_hash: str | None
    hash: str
