"""RagEvalResult — immutable per-query result within a RagEval."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class RagEvalResult(Base):
    __tablename__ = "rag_eval_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    rag_eval_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_doc_ids: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    retrieved_content: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    context_relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    faithfulness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    answer_relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
