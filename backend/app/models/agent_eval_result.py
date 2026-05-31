"""AgentEvalResult — immutable per-query result within an AgentEval."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AgentEvalResult(Base):
    __tablename__ = "agent_eval_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    agent_eval_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    actual_answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    expected_tools: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    actual_tools: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    tool_call_accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trajectory_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    task_completion_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
