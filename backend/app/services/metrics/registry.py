"""Metric scorer registry: maps metric kind → scorer instance."""

from __future__ import annotations

from app.services.metrics.base import MetricFn
from app.services.metrics.contains import ContainsMetric
from app.services.metrics.exact_match import ExactMatchMetric
from app.services.metrics.semantic_sim import SemanticSimilarityMetric

_REGISTRY: dict[str, MetricFn] = {
    "exact_match": ExactMatchMetric(),
    "contains": ContainsMetric(),
    "semantic_similarity": SemanticSimilarityMetric(),
}


def get_scorer(kind: str) -> MetricFn:
    scorer = _REGISTRY.get(kind)
    if scorer is None:
        raise ValueError(f"Unknown metric kind: {kind!r}. Supported: {sorted(_REGISTRY)}")
    return scorer
