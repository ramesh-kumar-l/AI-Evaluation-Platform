"""EvalJob — immutable record of a single scheduled evaluation execution."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class EvalJob(Base):
    __tablename__ = "eval_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    schedule_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    eval_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    error_msg: Mapped[str] = mapped_column(Text, nullable=False, default="")
    triggered_by: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
