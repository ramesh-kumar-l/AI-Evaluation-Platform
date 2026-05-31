"""GateDecision: immutable record of evaluating a ReleaseGate against a Comparison.

Status lifecycle:
  - "passed"            — all criteria met, no approval required
  - "failed"            — one or more criteria failed (or too many regressions)
  - "pending_approval"  — criteria met but gate.require_approval is True
  - "approved"          — pending_approval decision approved by a human
  - "rejected"          — pending_approval decision rejected by a human
  - "overridden"        — failed decision overridden with mandatory justification
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GateDecision(Base):
    __tablename__ = "gate_decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)

    # Stable identity — entity_key of the gate (not the version id)
    gate_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    # Specific gate version row that was active at evaluation time
    gate_version_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)

    comparison_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)

    # {metric_key: {metric_key, min_score, candidate_score, passed}}
    criteria_results: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    criteria_passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    criteria_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Denormalised from comparison at evaluation time
    regressions_detected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_regressions_allowed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # See module docstring for valid values
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_justification: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
