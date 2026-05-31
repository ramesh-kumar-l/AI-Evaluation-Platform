"""DatasetPolicy Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

_POLICY_STATUSES = {"active", "deprecated", "archived"}


class DatasetPolicyUpsert(BaseModel):
    owner: str = "system"
    status: str = "active"
    quality_rules: dict[str, Any] = {}
    ground_truth_policy: dict[str, Any] = {}
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        if v not in _POLICY_STATUSES:
            raise ValueError(f"status must be one of {_POLICY_STATUSES}")
        return v


class DatasetPolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_key: uuid.UUID
    owner: str
    status: str
    quality_rules: dict[str, Any]
    ground_truth_policy: dict[str, Any]
    notes: str | None
    created_at: datetime
    updated_at: datetime
    created_by: str
