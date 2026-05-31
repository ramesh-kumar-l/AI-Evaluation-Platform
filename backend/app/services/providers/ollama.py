"""Ollama provider adapter — mandatory offline-first inference backend."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.services.providers.base import InferenceRequest, InferenceResponse, ProviderError


class OllamaError(ProviderError):
    """Raised when the Ollama API call fails."""


class OllamaAdapter:
    """HTTP adapter for a local Ollama instance.

    Uses Ollama's /api/generate endpoint with stream=False for deterministic,
    fully buffered responses.
    """

    def __init__(self, base_url: str, timeout: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        payload: dict[str, Any] = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
        }
        if request.parameters:
            payload["options"] = request.parameters

        t0 = time.monotonic()
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(f"{self._base_url}/api/generate", json=payload)
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise OllamaError(f"Ollama returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise OllamaError(f"Ollama unreachable: {exc}") from exc

        latency_ms = int((time.monotonic() - t0) * 1000)
        data: dict[str, Any] = resp.json()
        output: str = data.get("response", "")
        return InferenceResponse(output=output, raw=data, latency_ms=latency_ms)
