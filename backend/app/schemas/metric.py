"""Pydantic schemas for the Metric entity."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class MetricCreate(BaseModel):
    name: str
    description: str = ""
    kind: Literal["exact_match", "contains", "semantic_similarity"]
    config: dict[str, Any] = {}


class MetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_key: uuid.UUID
    version: int
    parent_id: uuid.UUID | None
    is_latest: bool
    created_at: datetime
    created_by: str
    name: str
    description: str
    kind: str
    config: dict[str, Any]
