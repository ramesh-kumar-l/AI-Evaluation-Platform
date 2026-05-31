"""InferenceRun: immutable record of a single model inference execution.

Not versioned (runs are never revised); each run is a unique event with full provenance.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InferenceRun(Base):
    """Immutable record of one inference call. Written once; never updated."""

    __tablename__ = "inference_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")

    # Stable entity keys (for grouping / cross-version analysis)
    prompt_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    model_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    provider_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)

    # Exact versioned row IDs for bit-perfect provenance (not FKs — stay table-agnostic)
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    model_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    provider_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)

    # What was sent and what came back
    rendered_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    raw_output: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Execution parameters snapshot (temperature, seed, max_tokens, …)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # "completed" | "failed"
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Populated when status == "failed"
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Full raw provider exchange; useful for debugging and tracing
    trace: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
