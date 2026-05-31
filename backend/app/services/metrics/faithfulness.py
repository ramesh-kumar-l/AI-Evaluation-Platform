"""Faithfulness: overlap coefficient between answer tokens and retrieved context tokens.

Measures whether the answer is grounded in the retrieved context. Confidence is "low"
because keyword overlap is a rough proxy — a better scorer would use NLI.
"""

from __future__ import annotations


def score_faithfulness(answer: str, retrieved_docs: list[str]) -> float:
    """Return fraction of answer tokens that appear in the retrieved context."""
    if not answer.strip() or not retrieved_docs:
        return 0.0
    answer_tokens = set(answer.lower().split())
    context_tokens: set[str] = set()
    for doc in retrieved_docs:
        context_tokens.update(doc.lower().split())
    if not answer_tokens:
        return 0.0
    return round(len(answer_tokens & context_tokens) / len(answer_tokens), 4)
