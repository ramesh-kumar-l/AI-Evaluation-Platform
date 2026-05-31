"""Pydantic schemas for Phase 10: Observability & Continuous Evaluation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator

# ---------- EvalSchedule ----------


class EvalScheduleCreate(BaseModel):
    name: str
    description: str = ""
    dataset_key: uuid.UUID
    model_key: uuid.UUID
    prompt_key: uuid.UUID
    metric_keys: list[str] = []
    cron_expr: str = "0 * * * *"


class EvalScheduleStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        if v not in {"active", "paused", "archived"}:
            raise ValueError(f"Invalid schedule status: {v!r}")
        return v


class EvalScheduleOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    entity_key: uuid.UUID
    version: int
    name: str
    description: str
    dataset_key: uuid.UUID
    model_key: uuid.UUID
    prompt_key: uuid.UUID
    metric_keys: list[Any]
    cron_expr: str
    status: str
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    created_by: str


# ---------- EvalJob ----------


class EvalJobOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    schedule_id: uuid.UUID
    status: str
    eval_id: uuid.UUID | None
    error_msg: str
    triggered_by: str
    started_at: datetime
    completed_at: datetime | None


# ---------- Experiment ----------


class ExperimentCreate(BaseModel):
    name: str
    description: str = ""
    evaluation_ids: list[str] = []
    hypothesis: str = ""


class ExperimentUpdate(BaseModel):
    evaluation_ids: list[str] | None = None
    status: str | None = None
    conclusion: str | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str | None) -> str | None:
        if v is not None and v not in {"active", "concluded", "archived"}:
            raise ValueError(f"Invalid experiment status: {v!r}")
        return v


class ExperimentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    entity_key: uuid.UUID
    version: int
    name: str
    description: str
    evaluation_ids: list[Any]
    status: str
    hypothesis: str
    conclusion: str
    created_at: datetime
    created_by: str


# ---------- Trend ----------


class TrendPoint(BaseModel):
    eval_id: str
    created_at: datetime
    mean_score: float
    status: str


class TrendOut(BaseModel):
    dataset_key: str
    metric_kind: str
    points: list[TrendPoint]
