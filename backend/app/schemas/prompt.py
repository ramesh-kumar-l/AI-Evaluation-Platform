"""Prompt schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import VersionedOut


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=1024)
    template: str = Field(min_length=1)
    input_variables: list[str] = Field(default_factory=list)


class PromptOut(VersionedOut):
    name: str
    description: str
    template: str
    input_variables: list[str]
