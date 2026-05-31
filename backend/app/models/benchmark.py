"""Benchmark domain entity (versioned).

Binds a set of Metrics to an optional Dataset. Lifecycle: draft → active →
deprecated → archived. Every governance transition creates a new immutable version.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import VersionedBase


class Benchmark(VersionedBase):
    __tablename__ = "benchmarks"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    domain: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    task_type: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    # JSON list of metric entity_key strings; Any avoids cascading generic errors.
    metric_keys: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    dataset_key: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    # Lifecycle: draft (default) → active → deprecated → archived
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
