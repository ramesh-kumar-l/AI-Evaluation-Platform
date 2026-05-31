"""Provider adapter protocol and shared data classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class ProviderError(Exception):
    """Base exception for all provider adapter failures."""


@dataclass
class InferenceRequest:
    model: str
    prompt: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceResponse:
    output: str
    raw: dict[str, Any]
    latency_ms: int


class ProviderAdapter(Protocol):
    """Structural interface every provider adapter must satisfy."""

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        """Execute one inference and return the response."""
        ...
