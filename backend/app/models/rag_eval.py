"""RagEval — immutable record of one RAG evaluation run."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class RagEval(Base):
    __tablename__ = "rag_evals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    corpus_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    dataset_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    retrieval_method: Mapped[str] = mapped_column(String(128), nullable=False, default="tf-idf")
    top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    query_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mean_context_relevance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mean_faithfulness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mean_answer_relevance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
