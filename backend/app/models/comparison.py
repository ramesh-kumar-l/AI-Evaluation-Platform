"""Comparison: immutable record of a pairwise evaluation comparison.

Not versioned — comparisons are one-shot analysis events. Captures metric deltas,
regression flags, and thresholds at the time of creation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Comparison(Base):
    """Immutable record of a pairwise comparison between two evaluations."""

    __tablename__ = "comparisons"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")

    baseline_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)

    # "model" | "prompt" | "dataset" | "generic"
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="generic")

    # Must match between both evaluations
    dataset_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)

    # {metric_key: {metric_name, metric_kind, baseline_score, candidate_score,
    #               delta, relative_delta, regression, improvement, threshold}}
    metric_deltas: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Per-metric regression thresholds (absolute delta). Default applied in service.
    threshold_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    regressions_detected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    improvements_detected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # "regression" | "improvement" | "neutral"
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
