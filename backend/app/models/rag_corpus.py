"""RagCorpus — versioned knowledge base for RAG evaluation."""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import VersionedBase


class RagCorpus(VersionedBase):
    __tablename__ = "rag_corpora"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    # "tf-idf" = offline default; swap for a pgvector model in production.
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False, default="tf-idf")
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=512)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=64)
