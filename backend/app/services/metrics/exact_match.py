"""Exact-match metric: normalized string equality.

Strips whitespace and lowercases both strings before comparing.
Confidence is always "high" because the result is deterministic.
"""

from __future__ import annotations

from app.services.metrics.base import MetricInput, MetricScore


class ExactMatchMetric:
    def score(self, inp: MetricInput) -> MetricScore:
        expected = inp.expected.strip().lower()
        actual = inp.actual.strip().lower()
        match = expected == actual
        return MetricScore(
            score=1.0 if match else 0.0,
            confidence="high",
            detail={"expected_normalized": expected, "actual_normalized": actual},
        )
