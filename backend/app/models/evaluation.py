"""Evaluation: immutable record of a dataset-level evaluation execution.

Not versioned — evaluations are one-shot events. Full provenance captured via
exact version IDs for prompt, model, provider, dataset, and metrics.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Evaluation(Base):
    """Immutable record of one evaluation execution over a dataset."""

    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")

    # Stable entity keys (for cross-version analysis and grouping)
    prompt_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    model_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    provider_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    dataset_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)

    # Exact version row IDs — bit-perfect reproducibility
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    model_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    provider_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)

    # Metric entity keys and version IDs stored as JSON lists of UUID strings
    metric_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metric_version_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # "completed" | "partial" | "failed"
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scored_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # {metric_entity_key: {mean_score, count, metric_name, metric_kind, confidence_distribution}}
    aggregate_scores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
