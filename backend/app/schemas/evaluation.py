"""Pydantic schemas for Evaluation and EvaluationResult."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class EvaluationCreate(BaseModel):
    name: str
    prompt_key: uuid.UUID
    prompt_version: int | None = None
    model_key: uuid.UUID
    model_version: int | None = None
    dataset_key: uuid.UUID
    dataset_version: int | None = None
    metric_keys: list[uuid.UUID]
    parameters: dict[str, Any] = {}

    @field_validator("metric_keys")
    @classmethod
    def at_least_one_metric(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        if not v:
            raise ValueError("At least one metric_key is required")
        return v


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    created_by: str
    prompt_key: uuid.UUID
    model_key: uuid.UUID
    provider_key: uuid.UUID
    dataset_key: uuid.UUID
    prompt_version_id: uuid.UUID
    model_version_id: uuid.UUID
    provider_version_id: uuid.UUID
    dataset_version_id: uuid.UUID
    metric_keys: list[str]
    metric_version_ids: list[str]
    parameters: dict[str, Any]
    status: str
    started_at: datetime
    completed_at: datetime
    total_items: int
    scored_items: int
    error: str | None
    aggregate_scores: dict[str, Any]


class EvaluationResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evaluation_id: uuid.UUID
    run_id: uuid.UUID
    item_index: int
    expected_output: str
    metric_key: uuid.UUID
    metric_version_id: uuid.UUID
    metric_kind: str
    score: float
    confidence: str
    detail: dict[str, Any]
    status: str
    error: str | None
