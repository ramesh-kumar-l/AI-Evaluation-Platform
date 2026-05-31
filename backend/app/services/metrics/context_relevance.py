"""Context relevance: mean TF-cosine(query, retrieved_doc) across all retrieved docs.

Confidence is "medium" — TF cosine is a reasonable lexical relevance proxy offline.
"""

from __future__ import annotations

from app.services.metrics._utils import cosine, tf_vector


def score_context_relevance(query: str, retrieved_docs: list[str]) -> float:
    """Return mean cosine similarity between query and each retrieved document."""
    if not retrieved_docs:
        return 0.0
    qv = tf_vector(query)
    scores = [cosine(qv, tf_vector(doc)) for doc in retrieved_docs]
    return round(sum(scores) / len(scores), 4)
