"""RagDocument service: ingest and list document chunks within a corpus."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rag_corpus import RagCorpus
from app.models.rag_document import RagDocument
from app.services.metrics._utils import tf_vector
from app.services.versioning import get_latest


class RagError(Exception):
    """Raised when a RAG operation references a missing entity."""


def ingest_documents(
    db: Session,
    *,
    corpus_key: uuid.UUID,
    documents: list[dict[str, Any]],
    actor: str,
) -> list[RagDocument]:
    """Compute TF embeddings and persist document chunks under corpus_key."""
    corpus = get_latest(db, RagCorpus, corpus_key)
    if corpus is None:
        raise RagError(f"Corpus {corpus_key} not found")

    rows: list[RagDocument] = []
    for doc in documents:
        content = str(doc.get("content", ""))
        chunk_index = int(doc.get("chunk_index", 0))
        doc_source = str(doc.get("doc_source", ""))
        row = RagDocument(
            id=uuid.uuid4(),
            corpus_key=corpus.entity_key,
            content=content,
            chunk_index=chunk_index,
            doc_source=doc_source,
            embedding=tf_vector(content),
            created_by=actor,
        )
        db.add(row)
        rows.append(row)

    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def list_documents(db: Session, corpus_key: uuid.UUID) -> list[RagDocument]:
    stmt = (
        select(RagDocument)
        .where(RagDocument.corpus_key == corpus_key)
        .order_by(RagDocument.chunk_index)
    )
    return list(db.execute(stmt).scalars().all())
