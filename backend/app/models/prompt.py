"""Prompt domain entity (versioned)."""

from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import VersionedBase


class Prompt(VersionedBase):
    __tablename__ = "prompts"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    template: Mapped[str] = mapped_column(Text, nullable=False)
    # Declared template variables, e.g. ["question", "context"].
    input_variables: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
