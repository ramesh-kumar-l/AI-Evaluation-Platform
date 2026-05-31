"""Provider and Model schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import VersionedOut


class ProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(default="ollama", max_length=64)
    base_url: str = Field(default="", max_length=512)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class ProviderOut(VersionedOut):
    name: str
    kind: str
    base_url: str
    enabled: bool
    config: dict[str, Any]


class ModelCreate(BaseModel):
    provider_key: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ModelOut(VersionedOut):
    provider_key: uuid.UUID
    name: str
    parameters: dict[str, Any]
