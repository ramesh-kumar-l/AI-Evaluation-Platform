"""AgentStep — immutable record of one step within an AgentRun trajectory."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # "thinking" | "tool_call" | "response"
    step_type: Mapped[str] = mapped_column(String(32), nullable=False, default="tool_call")
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    tool_input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    tool_output: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reasoning_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
