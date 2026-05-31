"""AgentEval — immutable record of one agent evaluation run over a dataset."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AgentEval(Base):
    __tablename__ = "agent_evals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    dataset_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    query_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mean_tool_accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mean_trajectory_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mean_task_completion: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
