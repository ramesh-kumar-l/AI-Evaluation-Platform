"""Base types for the metric scorer pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class MetricInput:
    expected: str
    actual: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricScore:
    score: float  # 0.0 – 1.0
    confidence: str  # "high" | "medium" | "low"
    detail: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class MetricFn(Protocol):
    """Structural interface every metric scorer must satisfy."""

    def score(self, inp: MetricInput) -> MetricScore: ...
