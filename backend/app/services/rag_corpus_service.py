"""RagCorpus service: create and read versioned knowledge bases."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.rag_corpus import RagCorpus
from app.services.versioning import create_version, get_latest, list_latest


def create_corpus(
    db: Session,
    *,
    name: str,
    description: str,
    embedding_model: str,
    chunk_size: int,
    chunk_overlap: int,
    actor: str,
) -> RagCorpus:
    return create_version(
        db,
        RagCorpus,
        fields={
            "name": name,
            "description": description,
            "embedding_model": embedding_model,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
        actor=actor,
        audit_payload={"name": name, "embedding_model": embedding_model},
    )


def get_corpus(db: Session, corpus_key: uuid.UUID) -> RagCorpus | None:
    return get_latest(db, RagCorpus, corpus_key)


def list_corpora(db: Session) -> list[RagCorpus]:
    return list_latest(db, RagCorpus)
