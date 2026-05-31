"""Answer relevance: TF-cosine(question, answer).

Measures whether the answer is on-topic for the question. Confidence is "medium".
"""

from __future__ import annotations

from app.services.metrics._utils import cosine, tf_vector


def score_answer_relevance(question: str, answer: str) -> float:
    """Return TF-cosine similarity between question and answer."""
    return round(cosine(tf_vector(question), tf_vector(answer)), 4)
