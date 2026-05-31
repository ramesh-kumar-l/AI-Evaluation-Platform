"""Pure-Python TF-IDF cosine retrieval — offline-first, no pgvector dependency.

In production with Postgres+pgvector, replace this with an ANN query while keeping
the same interface: retrieve(db, corpus_key, query, top_k) → list[(doc, score)].
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rag_document import RagDocument
from app.services.metrics._utils import cosine, tf_vector


def retrieve(
    db: Session,
    *,
    corpus_key: uuid.UUID,
    query: str,
    top_k: int,
) -> list[tuple[RagDocument, float]]:
    """Return the top-k documents ranked by TF-cosine(query, doc), highest score first."""
    stmt = select(RagDocument).where(RagDocument.corpus_key == corpus_key)
    docs = list(db.execute(stmt).scalars().all())
    if not docs:
        return []

    qv = tf_vector(query)
    scored: list[tuple[RagDocument, float]] = []
    for doc in docs:
        raw: dict[str, Any] = doc.embedding  # JSON → dict[str, Any] at runtime
        dv = {k: float(v) for k, v in raw.items()}
        sim = cosine(qv, dv)
        scored.append((doc, round(sim, 4)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
