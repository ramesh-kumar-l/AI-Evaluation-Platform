"""Benchmark Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

_SETTABLE_STATUSES = {"active", "deprecated", "archived"}


class BenchmarkCreate(BaseModel):
    name: str
    description: str = ""
    domain: str = ""
    task_type: str = ""
    metric_keys: list[str] = []
    dataset_key: uuid.UUID | None = None
    notes: str | None = None


class BenchmarkOut(BaseModel):
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
    domain: str
    task_type: str
    metric_keys: list[Any]
    dataset_key: uuid.UUID | None
    status: str
    notes: str | None


class BenchmarkStatusUpdate(BaseModel):
    status: str
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        if v not in _SETTABLE_STATUSES:
            raise ValueError(f"status must be one of {_SETTABLE_STATUSES}")
        return v
