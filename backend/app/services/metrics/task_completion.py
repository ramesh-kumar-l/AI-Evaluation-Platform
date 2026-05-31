"""Task completion: TF-cosine similarity between expected and actual final answers."""

from __future__ import annotations

from app.services.metrics._utils import cosine, tf_vector


def score_task_completion(expected_answer: str, actual_answer: str) -> float:
    """TF-cosine similarity between expected and actual answer strings.

    Confidence: medium — offline, no LLM judge; captures token overlap.
    Returns 0.0 if either string is empty.
    """
    if not expected_answer.strip() or not actual_answer.strip():
        return 0.0
    return round(cosine(tf_vector(expected_answer), tf_vector(actual_answer)), 4)
