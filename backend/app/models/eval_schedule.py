"""EvalSchedule — versioned config for recurring automated evaluations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import VersionedBase


def _utcnow() -> datetime:
    return datetime.now(UTC)


class EvalSchedule(VersionedBase):
    __tablename__ = "eval_schedules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    dataset_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    model_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    prompt_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    metric_keys: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    cron_expr: Mapped[str] = mapped_column(String(100), nullable=False, default="0 * * * *")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
