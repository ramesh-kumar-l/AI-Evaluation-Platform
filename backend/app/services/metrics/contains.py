"""Contains metric: checks whether the expected value appears in the model output.

Case-insensitive substring match after stripping whitespace.
Confidence is "medium" — the check is deterministic but imprecise.
"""

from __future__ import annotations

from app.services.metrics.base import MetricInput, MetricScore


class ContainsMetric:
    def score(self, inp: MetricInput) -> MetricScore:
        expected = inp.expected.strip().lower()
        actual = inp.actual.strip().lower()
        found = expected in actual
        return MetricScore(
            score=1.0 if found else 0.0,
            confidence="medium",
            detail={"expected": inp.expected.strip(), "found": found},
        )
