"""Shared schema building blocks (version/lineage metadata exposed on every read)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VersionedOut(BaseModel):
    """Version + lineage fields surfaced for every versioned entity (trust-first)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_key: uuid.UUID
    version: int
    parent_id: uuid.UUID | None
    is_latest: bool
    created_at: datetime
    created_by: str
