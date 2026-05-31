"""RagDocument — immutable chunk of text ingested into a RagCorpus."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class RagDocument(Base):
    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    # corpus_key is the entity_key of the owning RagCorpus (stable across versions).
    corpus_key: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    doc_source: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    # TF-frequency vector stored as JSON for SQLite compat; use pgvector in production.
    embedding: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
