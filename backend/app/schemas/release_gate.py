"""Pydantic schemas for ReleaseGate."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GateCriterionIn(BaseModel):
    metric_key: str
    min_score: float = Field(ge=0.0, le=1.0)


class ReleaseGateCreate(BaseModel):
    name: str
    description: str = ""
    criteria: list[GateCriterionIn] = []
    max_regressions_allowed: int = Field(default=0, ge=0)
    require_approval: bool = True
    notes: str | None = None


class ReleaseGateOut(BaseModel):
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
    criteria: list[Any]
    max_regressions_allowed: int
    require_approval: bool
    notes: str | None
