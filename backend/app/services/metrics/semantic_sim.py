"""Semantic similarity metric: TF cosine similarity.

Pure-Python implementation — no ML or external dependencies — so it works fully offline.
Confidence is "low" because TF cosine is a rough approximation of semantic similarity.

Config key:
  threshold (float, default 0.0): informational only; stored in detail but does not gate the score.
"""

from __future__ import annotations

import math
from collections import Counter

from app.services.metrics.base import MetricInput, MetricScore


def _tf_vector(text: str) -> dict[str, float]:
    tokens = text.lower().split()
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    return {t: c / total for t, c in counts.items()}


def _cosine(v1: dict[str, float], v2: dict[str, float]) -> float:
    common = set(v1) & set(v2)
    dot = sum(v1[t] * v2[t] for t in common)
    norm1 = math.sqrt(sum(x * x for x in v1.values()))
    norm2 = math.sqrt(sum(x * x for x in v2.values()))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class SemanticSimilarityMetric:
    def score(self, inp: MetricInput) -> MetricScore:
        threshold: float = float(inp.config.get("threshold", 0.0))
        sim = _cosine(_tf_vector(inp.expected), _tf_vector(inp.actual))
        sim = round(sim, 4)
        return MetricScore(
            score=sim,
            confidence="low",
            detail={"cosine_similarity": sim, "threshold": threshold},
        )
