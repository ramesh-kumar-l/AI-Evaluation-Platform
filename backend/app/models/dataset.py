"""Dataset domain entity (versioned).

Items are stored inline as JSON for the MVP foundation; richer dataset governance (separate item
rows, ground-truth policy) arrives in Phase 7. Each item is ``{"input": ..., "expected": ...}``.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import VersionedBase


class Dataset(VersionedBase):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    items: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
