"""Dataset schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import VersionedOut


class DatasetItem(BaseModel):
    input: Any
    expected: Any = None


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=1024)
    items: list[DatasetItem] = Field(default_factory=list)


class DatasetOut(VersionedOut):
    name: str
    description: str
    items: list[DatasetItem]
    item_count: int
