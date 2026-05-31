"""Pydantic schemas for API key management."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

_VALID_ROLES = {"viewer", "evaluator", "approver", "admin"}

RoleType = Literal["viewer", "evaluator", "approver", "admin"]


class ApiKeyCreate(BaseModel):
    name: str
    role: RoleType = "evaluator"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class ApiKeyCreatedOut(BaseModel):
    """Returned once at creation — includes the raw key (never stored)."""

    id: uuid.UUID
    name: str
    role: str
    raw_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyOut(BaseModel):
    """Safe representation — last4 of hash only, no raw key."""

    id: uuid.UUID
    name: str
    role: str
    key_last4: str
    created_at: datetime
    revoked_at: datetime | None

    model_config = {"from_attributes": True}
