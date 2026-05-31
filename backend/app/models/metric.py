"""Metric domain entity (versioned).

Each Metric defines how to score a model output against an expected value.
Supported kinds: exact_match, contains, semantic_similarity.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import VersionedBase


class Metric(VersionedBase):
    __tablename__ = "metrics"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    # "exact_match" | "contains" | "semantic_similarity"
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    # Scorer-specific settings, e.g. {"threshold": 0.7} for semantic_similarity
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
