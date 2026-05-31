"""ReleaseGate domain entity (versioned).

A gate defines criteria that an evaluation (via a Comparison) must meet before a
model/prompt can be considered safe to deploy. Gates are versioned so criteria changes
are fully audited. Gate evaluations produce immutable GateDecision records.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import VersionedBase


class ReleaseGate(VersionedBase):
    __tablename__ = "release_gates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False, default="")

    # List of {metric_key: str, min_score: float}
    criteria: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)

    # Comparison.regressions_detected must be <= this to pass
    max_regressions_allowed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # If True, a passing gate still requires human approval before "approved"
    require_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
