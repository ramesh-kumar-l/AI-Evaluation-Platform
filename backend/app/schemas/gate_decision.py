"""Pydantic schemas for GateDecision and Approval."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GateEvaluateRequest(BaseModel):
    comparison_id: uuid.UUID


class GateDecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    gate_key: uuid.UUID
    gate_version_id: uuid.UUID
    comparison_id: uuid.UUID
    criteria_results: dict[str, Any]
    criteria_passed: int
    criteria_failed: int
    regressions_detected: int
    max_regressions_allowed: int
    status: str
    override: bool
    override_justification: str | None
    created_at: datetime
    created_by: str


class ApprovalCreate(BaseModel):
    # "approved" | "rejected" | "overridden"
    action: str
    justification: str = Field(min_length=10)

    @field_validator("action")
    @classmethod
    def valid_action(cls, v: str) -> str:
        allowed = {"approved", "rejected", "overridden"}
        if v not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return v


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    decision_id: uuid.UUID
    action: str
    justification: str
    created_at: datetime
    created_by: str
