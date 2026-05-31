"""EvaluationResult: immutable per-item score record for one evaluation execution."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, Float, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EvaluationResult(Base):
    """One metric score for one dataset item within an Evaluation."""

    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    item_index: Mapped[int] = mapped_column(Integer, nullable=False)

    expected_output: Mapped[str] = mapped_column(Text, nullable=False)

    # Metric provenance
    metric_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    metric_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    metric_kind: Mapped[str] = mapped_column(String(64), nullable=False)  # denormalized

    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # "high" | "medium" | "low"
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # "scored" | "failed"
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
