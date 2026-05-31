"""Run schemas (read-only — runs are immutable events)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class RunCreate(BaseModel):
    prompt_key: uuid.UUID
    prompt_version: int | None = None
    model_key: uuid.UUID
    model_version: int | None = None
    input_variables: dict[str, Any] = {}
    parameters: dict[str, Any] = {}


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    created_by: str

    prompt_key: uuid.UUID
    model_key: uuid.UUID
    provider_key: uuid.UUID

    prompt_version_id: uuid.UUID
    model_version_id: uuid.UUID
    provider_version_id: uuid.UUID

    rendered_prompt: str
    raw_output: str
    parameters: dict[str, Any]

    status: str
    started_at: datetime
    completed_at: datetime
    latency_ms: int
    error: str | None
