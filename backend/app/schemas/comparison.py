"""Pydantic schemas for Comparison."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class MetricDeltaOut(BaseModel):
    metric_name: str
    metric_kind: str
    baseline_score: float
    candidate_score: float
    delta: float
    relative_delta: float
    regression: bool
    improvement: bool
    threshold: float


class ComparisonCreate(BaseModel):
    name: str
    baseline_id: uuid.UUID
    candidate_id: uuid.UUID
    # "model" | "prompt" | "dataset" | "generic"
    kind: str = "generic"
    # Optional per-metric thresholds (absolute score drop). Default: 0.02
    threshold_config: dict[str, float] = {}
    notes: str | None = None

    @field_validator("kind")
    @classmethod
    def valid_kind(cls, v: str) -> str:
        allowed = {"model", "prompt", "dataset", "generic"}
        if v not in allowed:
            raise ValueError(f"kind must be one of {allowed}")
        return v


class ComparisonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    created_by: str
    baseline_id: uuid.UUID
    candidate_id: uuid.UUID
    kind: str
    dataset_key: uuid.UUID
    metric_deltas: dict[str, Any]
    threshold_config: dict[str, Any]
    regressions_detected: int
    improvements_detected: int
    status: str
    notes: str | None
